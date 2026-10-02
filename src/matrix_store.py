#!/usr/bin/env python3
"""UHES 系统矩阵持久化存储（第6项优化：矩阵持久化）。

设计原则（对应 09 铁律 + 零共享资源）：
- 独立 SQLite DB（.uhes_matrix.db），零共享连接池——符合"各插件独立DB"铁律。
- 表 schema 落地 evolves_from / versions 版本链（阶段4递归闭环真实化）。
- 纯标准库 sqlite3，无第三方依赖。
- 对外接口：register / load / list_all / close，与内存 _MATRIX_STORE 兼容。

使用：
    store = MatrixStore("path/to/matrix.db")
    store.register(record)      # 写入/更新系统记录（含版本链）
    rec = store.load("sys_xxx") # 读取
    all_rec = store.list_all()  # 全部
"""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Any, Optional


class MatrixStore:
    """SQLite 持久化的系统矩阵存储。"""

    def __init__(self, db_path: str = ".uhes_matrix.db"):
        self.db_path = db_path
        # 零共享资源：每次操作独立连接，用毕关闭（避免跨线程共享连接池）
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        conn = self._connect()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS systems (
                    system_id      TEXT PRIMARY KEY,
                    name           TEXT NOT NULL,
                    domain         TEXT,
                    paradigm_tags  TEXT,          -- JSON array
                    constraints    TEXT,          -- JSON array
                    success_criteria TEXT,        -- JSON array
                    snapshot_hash  TEXT,
                    version        TEXT,
                    evolves_from   TEXT,          -- 溯源边（阶段4）
                    versions       TEXT,          -- JSON array 版本链
                    payload        TEXT           -- 完整记录 JSON（保真）
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def register(self, record: dict[str, Any]) -> None:
        """写入/更新系统记录（含版本链字段）。"""
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO systems
                (system_id, name, domain, paradigm_tags, constraints,
                 success_criteria, snapshot_hash, version, evolves_from,
                 versions, payload)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    record.get("system_id", ""),
                    record.get("name", ""),
                    record.get("domain", ""),
                    json.dumps(record.get("paradigm_tags", []), ensure_ascii=False),
                    json.dumps(record.get("constraints", []), ensure_ascii=False),
                    json.dumps(record.get("success_criteria", []), ensure_ascii=False),
                    record.get("snapshot_hash", ""),
                    record.get("version", ""),
                    record.get("evolves_from"),
                    json.dumps(record.get("versions", []), ensure_ascii=False),
                    json.dumps(record, ensure_ascii=False),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def load(self, system_id: str) -> Optional[dict[str, Any]]:
        """按 system_id 读取记录（优先返回完整 payload 反序列化）。"""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT payload FROM systems WHERE system_id = ?", (system_id,)
            ).fetchone()
            if row is None:
                return None
            return json.loads(row["payload"])
        finally:
            conn.close()

    def list_all(self) -> list[dict[str, Any]]:
        """返回全部系统记录（反序列化）。"""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT payload FROM systems ORDER BY system_id"
            ).fetchall()
            return [json.loads(r["payload"]) for r in rows]
        finally:
            conn.close()

    def close(self) -> None:
        """关闭（SQLite 每次连接即关，此处保留接口兼容）。"""
        pass
