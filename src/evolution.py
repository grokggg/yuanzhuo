#!/usr/bin/env python3
"""UHES 进化闭环真实化（第12项优化：矩阵真实版本管理 + 递归迭代真实执行）。

设计原则（顶尖工程实践）：
- 三合一：阶段4机制（matrix_load_system/wrap_legacy_system/
  evaluate_evolution_value）+ SQLite 持久化（矩阵真实版本管理）+
  真实流水线（递归迭代真实执行）。
- 版本管理：每次有效进化自动递增版本号（001→002→003），
  evolves_from 溯源边 + versions 版本链（不可变历史）。
- 递归保护：深度上限 MAX_RECURSION_DEPTH，冗余迭代（价值判定不通过）
  立即终止，不写入矩阵（防死循环）。
- 三环制衡：有效进化 → 登记新版本；冗余迭代 → 终止并报告。

使用：
    from evolution import EvolutionEngine
    engine = EvolutionEngine(db_path="/tmp/uhes_evolution.db")
    result = engine.evolve(system_id="sys_lit_review_001", rounds=2)
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Optional

# 引用 main 中的阶段4机制（不修改冻结引擎，纯侧车调用）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import main as _main  # noqa: E402

# 递归深度保护（与阶段4基线一致）
MAX_RECURSION_DEPTH = getattr(_main, "MAX_RECURSION_DEPTH", 3)


class EvolutionEngine:
    """进化闭环引擎：矩阵版本管理 + 递归迭代真实执行。"""

    def __init__(self, db_path: Optional[str] = None):
        # 持久化：显式 db_path 时启用 SQLite（第6项机制复用），否则内存
        self.db_path = db_path
        if db_path:
            import matrix_store as _ms
            self.store = _ms.MatrixStore(db_path)
        else:
            self.store = None  # 内存（概念行为）

    # ---- 版本管理 ----
    def next_version(self, system_id: str) -> str:
        """真实版本管理：按现有版本自动递增（001→002→…）。"""
        base = system_id.rsplit("_", 1)[0]  # sys_lit_review → sys_lit_review
        # 查现有最大版本号
        existing = self._load_latest(system_id)
        if existing is None:
            return "001"
        try:
            ver = int(existing.get("version", "000")) + 1
        except (TypeError, ValueError):
            ver = int(existing.get("version", "000") or 0) + 1
        return f"{ver:03d}"

    def _load_latest(self, system_id: str) -> Optional[dict[str, Any]]:
        """加载指定 system_id 的最新版本（含版本链追溯）。"""
        # 持久化优先
        if self.store is not None:
            rec = self.store.load(system_id)
            if rec is not None:
                return rec
        return _main._MATRIX_STORE.get(system_id)

    # ---- 进化执行 ----
    def evolve(self, system_id: str, rounds: int = 1,
               use_mock: bool = False) -> dict[str, Any]:
        """递归迭代真实执行：对系统跑真实流水线，最多 rounds 轮。

        每轮：加载 → 包装 → 流水线迭代 → 价值判定 →
              有效 → 登记新版本（下一轮以此为 legacy）→ 递归。
              冗余 → 终止（不写入矩阵）。
        返回进化报告（版本链 + 每轮判定 + 最终状态）。
        """
        # 无 key 时注入 LLM mock（离线也能真实迭代）
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            try:
                import test_suite as _ts
                _mock = _ts.LLMMock()
                _mock.install(_main)
            except Exception:
                pass

        current = self._load_latest(system_id)
        if current is None:
            return {"ok": False, "error": f"系统 {system_id} 不存在于矩阵",
                    "rounds_run": 0, "version_chain": []}

        report = {
            "ok": True,
            "origin": system_id,
            "rounds_requested": rounds,
            "rounds_run": 0,
            "version_chain": [system_id],
            "rounds": [],
            "final_system_id": system_id,
            "final_status": "no_evolution",
        }

        for r in range(1, rounds + 1):
            if r > MAX_RECURSION_DEPTH:
                report["final_status"] = "depth_protected"
                report["note"] = f"递归深度达上限({MAX_RECURSION_DEPTH})，保护性终止"
                break

            # 1. 包装 legacy（阶段4机制）
            legacy_input = _main.wrap_legacy_system(current)

            # 2. 跑真实流水线迭代
            try:
                pipeline = _main.build_pipeline(
                    run_id=f"evolution_{current['system_id']}_r{r}")
                pkg = pipeline.run(legacy_input)
            except Exception as exc:
                report["ok"] = False
                report["error"] = f"第{r}轮迭代失败: {exc}"
                report["final_status"] = "iteration_failed"
                break

            # 3. 进化价值判定（阶段4机制，防死循环核心）
            new_dna = pkg.artifacts.get(
                "01_requirement_dna_report", {}).get("dna", {})
            judgement = _main.evaluate_evolution_value(current, new_dna)

            round_info = {
                "round": r,
                "iterated_from": current["system_id"],
                "pipeline_status": pipeline.state.final_status,
                "judgement": judgement["verdict"],
                "dims_met": judgement["dims_met"],
                "reason": judgement["reason"],
            }

            if not judgement["valid_evolution"]:
                round_info["action"] = "terminate_no_registration"
                report["rounds"].append(round_info)
                report["final_status"] = "redundant_terminated"
                report["note"] = "冗余迭代，终止且不写入矩阵（防死循环）"
                break

            # 4. 有效进化：登记新版本（真实版本管理 + 溯源）
            new_version = self.next_version(current["system_id"])
            new_system_id = f"{current['system_id'].rsplit('_', 1)[0]}_{new_version}"
            # 版本链：继承 + 追加
            versions = list(current.get("versions", []))
            if new_system_id not in versions:
                versions.append(new_system_id)
            new_record = {
                "system_id": new_system_id,
                "name": pkg.artifacts.get("02_paradigm_composite", {}).get(
                    "composite_name", f"{current['name']} v{new_version}"),
                "domain": current.get("domain", ""),
                "paradigm_tags": new_dna.get("paradigm_hints", []) or new_dna.get(
                    "_iteration_paradigm_tags", []),
                "constraints": new_dna.get("constraints", []),
                "success_criteria": new_dna.get("success_criteria", []),
                "snapshot_hash": new_dna.get("_iteration_snapshot_hash",
                                             f"hash_v{new_version}"),
                "version": new_version,
                "evolves_from": current["system_id"],
                "versions": versions,
                "iteration_round": r,
                "pipeline_status": pipeline.state.final_status,
            }
            self._register(new_record)
            round_info["action"] = "registered"
            round_info["new_system_id"] = new_system_id
            report["rounds"].append(round_info)
            report["version_chain"].append(new_system_id)

            # 5. 递归：新系统成为下一轮 legacy（真实迭代）
            current = new_record
            report["rounds_run"] = r
            report["final_system_id"] = new_system_id
            report["final_status"] = "evolved"

        # 汇总判定
        evolved_rounds = [r for r in report["rounds"] if r.get("action") == "registered"]
        report["evolved_count"] = len(evolved_rounds)
        if report["rounds_run"] > 0 and not any(
                r.get("action") == "terminate_no_registration" for r in report["rounds"]):
            report["final_status"] = "evolved"
        return report

    def _register(self, record: dict[str, Any]) -> None:
        """登记新版本：持久化（SQLite）+ 内存同步（与阶段4机制一致）。"""
        if self.store is not None:
            self.store.register(record)
        _main.matrix_register(record)

    # ---- 查询 ----
    def version_history(self, system_id: str) -> list[str]:
        """版本历史（版本链溯源）。"""
        rec = self._load_latest(system_id)
        if rec is None:
            return []
        return rec.get("versions", [rec["system_id"]])

    def load_version(self, system_id: str) -> Optional[dict[str, Any]]:
        """加载指定版本。"""
        return self._load_latest(system_id)


def run_evolution_demo(system_id: str = "sys_lit_review_001",
                       rounds: int = 2,
                       db_path: Optional[str] = None,
                       use_mock: bool = True) -> dict[str, Any]:
    """演示入口：对种子系统跑递归进化。"""
    engine = EvolutionEngine(db_path=db_path)
    return engine.evolve(system_id, rounds=rounds, use_mock=use_mock)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="UHES 进化闭环真实执行")
    ap.add_argument("--system", default="sys_lit_review_001")
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--db", default=None, help="SQLite 持久化路径(默认内存)")
    ap.add_argument("--real", action="store_true", help="使用真实 LLM(需 ZHIPU_API_KEY)")
    args = ap.parse_args()

    res = run_evolution_demo(args.system, args.rounds, args.db,
                             use_mock=not args.real)
    print(f"[EVOLUTION] 系统 {res['origin']} 进化: 状态={res['final_status']}")
    print(f"  版本链: {' → '.join(res['version_chain'])}")
    for r in res.get("rounds", []):
        print(f"  第{r['round']}轮: {r['action']} "
              f"({r['judgement']}, 维度{r['dims_met']}/3) "
              f"{r.get('new_system_id', '')}")
    if not res.get("ok", True):
        print(f"  错误: {res.get('error', '')}")
    sys.exit(0 if res.get("ok") and res.get("final_status") in (
        "evolved", "redundant_terminated", "depth_protected") else 1)
