#!/usr/bin/env python3
"""UHES 同构关系数据化（第15项优化：581 对同构 → SQLite 可检索可推理）。

设计原则（顶尖工程实践）：
- 结构化落库：581 对同构关系从"文档登记"落地为 SQLite 数据（paradigm_a/
  paradigm_b/mechanism_type/depth/source/evidence）。
- 可检索：按范式、机制类型、深度查询（query_by_paradigm / query_by_type）。
- 可推理：传递闭包（A~B 且 B~C ⇒ A~C 弱同构）、邻居发现（某范式所有同构）。
- 渐进式：默认内置种子数据（概念层 581 对的可查询子集 + 生成器扩展），
  显式路径可持久化 SQLite。

使用：
    from homology import HomologyDB
    db = HomologyDB("/tmp/uhes_homology.db")   # 持久化
    db = HomologyDB()                          # 内存（概念行为）
    db.query_by_paradigm("信息论")
    db.transitive_closure("信息论", depth=2)
"""

from __future__ import annotations

import sqlite3
from typing import Any

# 机制类型枚举（同构关系的本质分类）
MECHANISM_TYPES = [
    "feedback_loop",      # 反馈回路同构（控制论×生态学等）
    "information_flow",   # 信息流同构（信息论×语言学等）
    "state_transition",   # 状态转移同构（动力学×量子力学等）
    "hierarchy_emergence",  # 层次涌现同构（复杂系统×社会学等）
    "constraint_optimization",  # 约束优化同构（经济学×热力学等）
    "selection_adaptation",     # 选择适应同构（进化论×经济学等）
    "network_structure",  # 网络结构同构（网络科学×神经科学等）
]

# 种子同构数据（29 组范式的代表性同构对，可扩展至 581）
SEED_HOMOLOGIES: list[dict[str, Any]] = [
    # 信息流类
    {"paradigm_a": "信息论", "paradigm_b": "语言学",
     "mechanism_type": "information_flow", "depth": "deep",
     "source": "证据传递=噪声信道→冗余锚定纠错",
     "evidence": "信道编码与语言冗余机制对应"},
    {"paradigm_a": "信息论", "paradigm_b": "科研范式",
     "mechanism_type": "information_flow", "depth": "deep",
     "source": "证据传递=噪声信道→可证伪性过滤",
     "evidence": "假设检验与信号检测对应"},
    # 反馈回路类
    {"paradigm_a": "控制论", "paradigm_b": "生态学",
     "mechanism_type": "feedback_loop", "depth": "deep",
     "source": "负反馈稳态=生态平衡机制",
     "evidence": "调节回路与种群动态对应"},
    {"paradigm_a": "控制论", "paradigm_b": "经济学",
     "mechanism_type": "feedback_loop", "depth": "medium",
     "source": "价格调节=负反馈稳态",
     "evidence": "市场均衡与稳态调节对应"},
    # 状态转移类
    {"paradigm_a": "动力学", "paradigm_b": "量子力学",
     "mechanism_type": "state_transition", "depth": "deep",
     "source": "演化算符=幺正演化",
     "evidence": "微分方程与薛定谔方程结构对应"},
    {"paradigm_a": "热力学", "paradigm_b": "经济学",
     "mechanism_type": "constraint_optimization", "depth": "deep",
     "source": "熵增=交易成本耗散",
     "evidence": "自由能最小化与效用最大化对应"},
    # 层次涌现类
    {"paradigm_a": "复杂系统", "paradigm_b": "社会学",
     "mechanism_type": "hierarchy_emergence", "depth": "deep",
     "source": "涌现秩序=社会结构自组织",
     "evidence": "微观互动→宏观结构对应"},
    {"paradigm_a": "复杂系统", "paradigm_b": "神经科学",
     "mechanism_type": "hierarchy_emergence", "depth": "deep",
     "source": "涌现认知=神经集群活动",
     "evidence": "局部神经元→整体认知对应"},
    # 选择适应类
    {"paradigm_a": "进化论", "paradigm_b": "经济学",
     "mechanism_type": "selection_adaptation", "depth": "medium",
     "source": "自然选择=市场竞争",
     "evidence": "适者生存与优胜劣汰对应"},
    {"paradigm_a": "进化论", "paradigm_b": "认知科学",
     "mechanism_type": "selection_adaptation", "depth": "medium",
     "source": "心智模块=适应器",
     "evidence": "进化心理学对应"},
    # 网络结构类
    {"paradigm_a": "网络科学", "paradigm_b": "神经科学",
     "mechanism_type": "network_structure", "depth": "deep",
     "source": "小世界网络=大脑连接组",
     "evidence": "拓扑属性对应"},
    {"paradigm_a": "网络科学", "paradigm_b": "社会学",
     "mechanism_type": "network_structure", "depth": "deep",
     "source": "社交网络=人际结构",
     "evidence": "中心性/社区结构对应"},
    # 跨类扩展
    {"paradigm_a": "信息论", "paradigm_b": "复杂系统",
     "mechanism_type": "information_flow", "depth": "medium",
     "source": "信息熵=系统复杂度",
     "evidence": "熵与涌现复杂度对应"},
    {"paradigm_a": "热力学", "paradigm_b": "信息论",
     "mechanism_type": "constraint_optimization", "depth": "deep",
     "source": "热熵=信息熵(麦克斯韦妖)",
     "evidence": "Landauer 原理对应"},
    {"paradigm_a": "系统论", "paradigm_b": "控制论",
     "mechanism_type": "feedback_loop", "depth": "deep",
     "source": "整体性=闭环调节",
     "evidence": "系统边界与反馈回路对应"},
]


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_xǁHomologyDBǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁHomologyDBǁ_init_schema__mutmut: MutantDict = {}  # type: ignore
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut: MutantDict = {}  # type: ignore
mutants_xǁHomologyDBǁ_load_seed_memory__mutmut: MutantDict = {}  # type: ignore
mutants_xǁHomologyDBǁ_rebuild_index__mutmut: MutantDict = {}  # type: ignore
mutants_xǁHomologyDBǁregister__mutmut: MutantDict = {}  # type: ignore
mutants_xǁHomologyDBǁquery_by_paradigm__mutmut: MutantDict = {}  # type: ignore
mutants_xǁHomologyDBǁquery_by_type__mutmut: MutantDict = {}  # type: ignore
mutants_xǁHomologyDBǁquery_between__mutmut: MutantDict = {}  # type: ignore
mutants_xǁHomologyDBǁtransitive_closure__mutmut: MutantDict = {}  # type: ignore
mutants_xǁHomologyDBǁneighbors__mutmut: MutantDict = {}  # type: ignore
mutants_xǁHomologyDBǁcount__mutmut: MutantDict = {}  # type: ignore
mutants_xǁHomologyDBǁclose__mutmut: MutantDict = {}  # type: ignore


class HomologyDB:
    """同构关系数据库（SQLite 持久化 + 内存兜底）。"""

    @_mutmut_mutated(mutants_xǁHomologyDBǁ__init____mutmut)
    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None
        if db_path:
            self._conn = sqlite3.connect(db_path)
            self._init_schema()
            self._seed_if_empty()
        self._memory: list[dict[str, Any]] = []
        self._memory_index: dict[str, list[dict[str, Any]]] = {}
        if not db_path:
            self._load_seed_memory()

    def xǁHomologyDBǁ__init____mutmut_orig(self, db_path: str | None = None) -> None:
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None
        if db_path:
            self._conn = sqlite3.connect(db_path)
            self._init_schema()
            self._seed_if_empty()
        self._memory: list[dict[str, Any]] = []
        self._memory_index: dict[str, list[dict[str, Any]]] = {}
        if not db_path:
            self._load_seed_memory()

    def xǁHomologyDBǁ__init____mutmut_1(self, db_path: str | None = None) -> None:
        self.db_path = None
        self._conn: sqlite3.Connection | None = None
        if db_path:
            self._conn = sqlite3.connect(db_path)
            self._init_schema()
            self._seed_if_empty()
        self._memory: list[dict[str, Any]] = []
        self._memory_index: dict[str, list[dict[str, Any]]] = {}
        if not db_path:
            self._load_seed_memory()

    def xǁHomologyDBǁ__init____mutmut_2(self, db_path: str | None = None) -> None:
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = ""
        if db_path:
            self._conn = sqlite3.connect(db_path)
            self._init_schema()
            self._seed_if_empty()
        self._memory: list[dict[str, Any]] = []
        self._memory_index: dict[str, list[dict[str, Any]]] = {}
        if not db_path:
            self._load_seed_memory()

    def xǁHomologyDBǁ__init____mutmut_3(self, db_path: str | None = None) -> None:
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None
        if db_path:
            self._conn = None
            self._init_schema()
            self._seed_if_empty()
        self._memory: list[dict[str, Any]] = []
        self._memory_index: dict[str, list[dict[str, Any]]] = {}
        if not db_path:
            self._load_seed_memory()

    def xǁHomologyDBǁ__init____mutmut_4(self, db_path: str | None = None) -> None:
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None
        if db_path:
            self._conn = sqlite3.connect(None)
            self._init_schema()
            self._seed_if_empty()
        self._memory: list[dict[str, Any]] = []
        self._memory_index: dict[str, list[dict[str, Any]]] = {}
        if not db_path:
            self._load_seed_memory()

    def xǁHomologyDBǁ__init____mutmut_5(self, db_path: str | None = None) -> None:
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None
        if db_path:
            self._conn = sqlite3.connect(db_path)
            self._init_schema()
            self._seed_if_empty()
        self._memory: list[dict[str, Any]] = None
        self._memory_index: dict[str, list[dict[str, Any]]] = {}
        if not db_path:
            self._load_seed_memory()

    def xǁHomologyDBǁ__init____mutmut_6(self, db_path: str | None = None) -> None:
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None
        if db_path:
            self._conn = sqlite3.connect(db_path)
            self._init_schema()
            self._seed_if_empty()
        self._memory: list[dict[str, Any]] = []
        self._memory_index: dict[str, list[dict[str, Any]]] = None
        if not db_path:
            self._load_seed_memory()

    def xǁHomologyDBǁ__init____mutmut_7(self, db_path: str | None = None) -> None:
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None
        if db_path:
            self._conn = sqlite3.connect(db_path)
            self._init_schema()
            self._seed_if_empty()
        self._memory: list[dict[str, Any]] = []
        self._memory_index: dict[str, list[dict[str, Any]]] = {}
        if db_path:
            self._load_seed_memory()

    @_mutmut_mutated(mutants_xǁHomologyDBǁ_init_schema__mutmut)
    def _init_schema(self) -> None:
        assert self._conn is not None
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS homologies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paradigm_a TEXT NOT NULL,
                paradigm_b TEXT NOT NULL,
                mechanism_type TEXT NOT NULL,
                depth TEXT NOT NULL,
                source TEXT,
                evidence TEXT,
                UNIQUE(paradigm_a, paradigm_b, mechanism_type)
            )
        """)
        self._conn.commit()

    def xǁHomologyDBǁ_init_schema__mutmut_orig(self) -> None:
        assert self._conn is not None
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS homologies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paradigm_a TEXT NOT NULL,
                paradigm_b TEXT NOT NULL,
                mechanism_type TEXT NOT NULL,
                depth TEXT NOT NULL,
                source TEXT,
                evidence TEXT,
                UNIQUE(paradigm_a, paradigm_b, mechanism_type)
            )
        """)
        self._conn.commit()

    def xǁHomologyDBǁ_init_schema__mutmut_1(self) -> None:
        assert self._conn is None
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS homologies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paradigm_a TEXT NOT NULL,
                paradigm_b TEXT NOT NULL,
                mechanism_type TEXT NOT NULL,
                depth TEXT NOT NULL,
                source TEXT,
                evidence TEXT,
                UNIQUE(paradigm_a, paradigm_b, mechanism_type)
            )
        """)
        self._conn.commit()

    def xǁHomologyDBǁ_init_schema__mutmut_2(self) -> None:
        assert self._conn is not None
        self._conn.execute(None)
        self._conn.commit()

    @_mutmut_mutated(mutants_xǁHomologyDBǁ_seed_if_empty__mutmut)
    def _seed_if_empty(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "VALUES (?,?,?,?,?,?)",
                    (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                     h["depth"], h["source"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_orig(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "VALUES (?,?,?,?,?,?)",
                    (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                     h["depth"], h["source"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_1(self) -> None:
        assert self._conn is None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "VALUES (?,?,?,?,?,?)",
                    (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                     h["depth"], h["source"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_2(self) -> None:
        assert self._conn is not None
        count = None
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "VALUES (?,?,?,?,?,?)",
                    (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                     h["depth"], h["source"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_3(self) -> None:
        assert self._conn is not None
        count = self._conn.execute(None).fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "VALUES (?,?,?,?,?,?)",
                    (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                     h["depth"], h["source"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_4(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("XXSELECT COUNT(*) FROM homologiesXX").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "VALUES (?,?,?,?,?,?)",
                    (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                     h["depth"], h["source"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_5(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("select count(*) from homologies").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "VALUES (?,?,?,?,?,?)",
                    (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                     h["depth"], h["source"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_6(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM HOMOLOGIES").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "VALUES (?,?,?,?,?,?)",
                    (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                     h["depth"], h["source"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_7(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[1]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "VALUES (?,?,?,?,?,?)",
                    (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                     h["depth"], h["source"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_8(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        if count != 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "VALUES (?,?,?,?,?,?)",
                    (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                     h["depth"], h["source"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_9(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        if count == 1:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "VALUES (?,?,?,?,?,?)",
                    (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                     h["depth"], h["source"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_10(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    None,
                    (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                     h["depth"], h["source"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_11(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "VALUES (?,?,?,?,?,?)",
                    None)
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_12(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                     h["depth"], h["source"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_13(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "VALUES (?,?,?,?,?,?)",
                    )
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_14(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "XXINSERT OR IGNORE INTO homologies XX"
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "VALUES (?,?,?,?,?,?)",
                    (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                     h["depth"], h["source"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_15(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "insert or ignore into homologies "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "VALUES (?,?,?,?,?,?)",
                    (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                     h["depth"], h["source"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_16(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO HOMOLOGIES "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "VALUES (?,?,?,?,?,?)",
                    (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                     h["depth"], h["source"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_17(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "XX(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) XX"
                    "VALUES (?,?,?,?,?,?)",
                    (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                     h["depth"], h["source"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_18(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "(PARADIGM_A, PARADIGM_B, MECHANISM_TYPE, DEPTH, SOURCE, EVIDENCE) "
                    "VALUES (?,?,?,?,?,?)",
                    (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                     h["depth"], h["source"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_19(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "XXVALUES (?,?,?,?,?,?)XX",
                    (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                     h["depth"], h["source"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_20(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "values (?,?,?,?,?,?)",
                    (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                     h["depth"], h["source"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_21(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "VALUES (?,?,?,?,?,?)",
                    (h["XXparadigm_aXX"], h["paradigm_b"], h["mechanism_type"],
                     h["depth"], h["source"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_22(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "VALUES (?,?,?,?,?,?)",
                    (h["PARADIGM_A"], h["paradigm_b"], h["mechanism_type"],
                     h["depth"], h["source"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_23(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "VALUES (?,?,?,?,?,?)",
                    (h["paradigm_a"], h["XXparadigm_bXX"], h["mechanism_type"],
                     h["depth"], h["source"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_24(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "VALUES (?,?,?,?,?,?)",
                    (h["paradigm_a"], h["PARADIGM_B"], h["mechanism_type"],
                     h["depth"], h["source"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_25(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "VALUES (?,?,?,?,?,?)",
                    (h["paradigm_a"], h["paradigm_b"], h["XXmechanism_typeXX"],
                     h["depth"], h["source"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_26(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "VALUES (?,?,?,?,?,?)",
                    (h["paradigm_a"], h["paradigm_b"], h["MECHANISM_TYPE"],
                     h["depth"], h["source"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_27(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "VALUES (?,?,?,?,?,?)",
                    (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                     h["XXdepthXX"], h["source"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_28(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "VALUES (?,?,?,?,?,?)",
                    (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                     h["DEPTH"], h["source"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_29(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "VALUES (?,?,?,?,?,?)",
                    (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                     h["depth"], h["XXsourceXX"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_30(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "VALUES (?,?,?,?,?,?)",
                    (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                     h["depth"], h["SOURCE"], h["evidence"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_31(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "VALUES (?,?,?,?,?,?)",
                    (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                     h["depth"], h["source"], h["XXevidenceXX"]))
            self._conn.commit()

    def xǁHomologyDBǁ_seed_if_empty__mutmut_32(self) -> None:
        assert self._conn is not None
        count = self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        if count == 0:
            for h in SEED_HOMOLOGIES:
                self._conn.execute(
                    "INSERT OR IGNORE INTO homologies "
                    "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                    "VALUES (?,?,?,?,?,?)",
                    (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                     h["depth"], h["source"], h["EVIDENCE"]))
            self._conn.commit()

    @_mutmut_mutated(mutants_xǁHomologyDBǁ_load_seed_memory__mutmut)
    def _load_seed_memory(self) -> None:
        self._memory = [dict(h) for h in SEED_HOMOLOGIES]
        self._rebuild_index()

    def xǁHomologyDBǁ_load_seed_memory__mutmut_orig(self) -> None:
        self._memory = [dict(h) for h in SEED_HOMOLOGIES]
        self._rebuild_index()

    def xǁHomologyDBǁ_load_seed_memory__mutmut_1(self) -> None:
        self._memory = None
        self._rebuild_index()

    def xǁHomologyDBǁ_load_seed_memory__mutmut_2(self) -> None:
        self._memory = [dict(None) for h in SEED_HOMOLOGIES]
        self._rebuild_index()

    @_mutmut_mutated(mutants_xǁHomologyDBǁ_rebuild_index__mutmut)
    def _rebuild_index(self) -> None:
        self._memory_index = {}
        for h in self._memory:
            for p in (h["paradigm_a"], h["paradigm_b"]):
                self._memory_index.setdefault(p, []).append(h)

    def xǁHomologyDBǁ_rebuild_index__mutmut_orig(self) -> None:
        self._memory_index = {}
        for h in self._memory:
            for p in (h["paradigm_a"], h["paradigm_b"]):
                self._memory_index.setdefault(p, []).append(h)

    def xǁHomologyDBǁ_rebuild_index__mutmut_1(self) -> None:
        self._memory_index = None
        for h in self._memory:
            for p in (h["paradigm_a"], h["paradigm_b"]):
                self._memory_index.setdefault(p, []).append(h)

    def xǁHomologyDBǁ_rebuild_index__mutmut_2(self) -> None:
        self._memory_index = {}
        for h in self._memory:
            for p in (h["XXparadigm_aXX"], h["paradigm_b"]):
                self._memory_index.setdefault(p, []).append(h)

    def xǁHomologyDBǁ_rebuild_index__mutmut_3(self) -> None:
        self._memory_index = {}
        for h in self._memory:
            for p in (h["PARADIGM_A"], h["paradigm_b"]):
                self._memory_index.setdefault(p, []).append(h)

    def xǁHomologyDBǁ_rebuild_index__mutmut_4(self) -> None:
        self._memory_index = {}
        for h in self._memory:
            for p in (h["paradigm_a"], h["XXparadigm_bXX"]):
                self._memory_index.setdefault(p, []).append(h)

    def xǁHomologyDBǁ_rebuild_index__mutmut_5(self) -> None:
        self._memory_index = {}
        for h in self._memory:
            for p in (h["paradigm_a"], h["PARADIGM_B"]):
                self._memory_index.setdefault(p, []).append(h)

    def xǁHomologyDBǁ_rebuild_index__mutmut_6(self) -> None:
        self._memory_index = {}
        for h in self._memory:
            for p in (h["paradigm_a"], h["paradigm_b"]):
                self._memory_index.setdefault(p, []).append(None)

    def xǁHomologyDBǁ_rebuild_index__mutmut_7(self) -> None:
        self._memory_index = {}
        for h in self._memory:
            for p in (h["paradigm_a"], h["paradigm_b"]):
                self._memory_index.setdefault(None, []).append(h)

    def xǁHomologyDBǁ_rebuild_index__mutmut_8(self) -> None:
        self._memory_index = {}
        for h in self._memory:
            for p in (h["paradigm_a"], h["paradigm_b"]):
                self._memory_index.setdefault(p, None).append(h)

    def xǁHomologyDBǁ_rebuild_index__mutmut_9(self) -> None:
        self._memory_index = {}
        for h in self._memory:
            for p in (h["paradigm_a"], h["paradigm_b"]):
                self._memory_index.setdefault([]).append(h)

    def xǁHomologyDBǁ_rebuild_index__mutmut_10(self) -> None:
        self._memory_index = {}
        for h in self._memory:
            for p in (h["paradigm_a"], h["paradigm_b"]):
                self._memory_index.setdefault(p, ).append(h)

    # ---- 写 ----
    @_mutmut_mutated(mutants_xǁHomologyDBǁregister__mutmut)
    def register(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_orig(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_1(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_2(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                None,
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_3(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                None)
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_4(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_5(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                )
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_6(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "XXINSERT OR IGNORE INTO homologies XX"
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_7(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "insert or ignore into homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_8(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO HOMOLOGIES "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_9(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "XX(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) XX"
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_10(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(PARADIGM_A, PARADIGM_B, MECHANISM_TYPE, DEPTH, SOURCE, EVIDENCE) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_11(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "XXVALUES (?,?,?,?,?,?)XX",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_12(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "values (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_13(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["XXparadigm_aXX"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_14(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["PARADIGM_A"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_15(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["XXparadigm_bXX"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_16(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["PARADIGM_B"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_17(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["XXmechanism_typeXX"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_18(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["MECHANISM_TYPE"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_19(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["XXdepthXX"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_20(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["DEPTH"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_21(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["XXsourceXX"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_22(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["SOURCE"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_23(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["XXevidenceXX"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_24(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["EVIDENCE"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_25(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_26(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(None):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_27(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"] or x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_28(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"] or x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_29(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["XXparadigm_aXX"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_30(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["PARADIGM_A"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_31(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] != h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_32(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["XXparadigm_aXX"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_33(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["PARADIGM_A"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_34(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["XXparadigm_bXX"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_35(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["PARADIGM_B"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_36(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] != h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_37(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["XXparadigm_bXX"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_38(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["PARADIGM_B"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_39(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["XXmechanism_typeXX"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_40(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["MECHANISM_TYPE"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_41(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] != h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_42(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["XXmechanism_typeXX"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_43(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["MECHANISM_TYPE"]
                   for x in self._memory):
            self._memory.append(dict(h))
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_44(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(None)
            self._rebuild_index()

    # ---- 写 ----
    def xǁHomologyDBǁregister__mutmut_45(self, h: dict[str, Any]) -> None:
        """登记一条同构关系（幂等：同范式对+机制类型不重复）。"""
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR IGNORE INTO homologies "
                "(paradigm_a, paradigm_b, mechanism_type, depth, source, evidence) "
                "VALUES (?,?,?,?,?,?)",
                (h["paradigm_a"], h["paradigm_b"], h["mechanism_type"],
                 h["depth"], h["source"], h["evidence"]))
            self._conn.commit()
        if not any(x["paradigm_a"] == h["paradigm_a"]
                   and x["paradigm_b"] == h["paradigm_b"]
                   and x["mechanism_type"] == h["mechanism_type"]
                   for x in self._memory):
            self._memory.append(dict(None))
            self._rebuild_index()

    # ---- 检索 ----
    @_mutmut_mutated(mutants_xǁHomologyDBǁquery_by_paradigm__mutmut)
    def query_by_paradigm(self, paradigm: str) -> list[dict[str, Any]]:
        """查某范式的全部同构关系（邻居发现）。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE paradigm_a=? OR paradigm_b=?",
                (paradigm, paradigm)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory_index.get(paradigm, [])]

    # ---- 检索 ----
    def xǁHomologyDBǁquery_by_paradigm__mutmut_orig(self, paradigm: str) -> list[dict[str, Any]]:
        """查某范式的全部同构关系（邻居发现）。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE paradigm_a=? OR paradigm_b=?",
                (paradigm, paradigm)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory_index.get(paradigm, [])]

    # ---- 检索 ----
    def xǁHomologyDBǁquery_by_paradigm__mutmut_1(self, paradigm: str) -> list[dict[str, Any]]:
        """查某范式的全部同构关系（邻居发现）。"""
        if self._conn is None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE paradigm_a=? OR paradigm_b=?",
                (paradigm, paradigm)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory_index.get(paradigm, [])]

    # ---- 检索 ----
    def xǁHomologyDBǁquery_by_paradigm__mutmut_2(self, paradigm: str) -> list[dict[str, Any]]:
        """查某范式的全部同构关系（邻居发现）。"""
        if self._conn is not None:
            rows = None
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory_index.get(paradigm, [])]

    # ---- 检索 ----
    def xǁHomologyDBǁquery_by_paradigm__mutmut_3(self, paradigm: str) -> list[dict[str, Any]]:
        """查某范式的全部同构关系（邻居发现）。"""
        if self._conn is not None:
            rows = self._conn.execute(
                None,
                (paradigm, paradigm)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory_index.get(paradigm, [])]

    # ---- 检索 ----
    def xǁHomologyDBǁquery_by_paradigm__mutmut_4(self, paradigm: str) -> list[dict[str, Any]]:
        """查某范式的全部同构关系（邻居发现）。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE paradigm_a=? OR paradigm_b=?",
                None).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory_index.get(paradigm, [])]

    # ---- 检索 ----
    def xǁHomologyDBǁquery_by_paradigm__mutmut_5(self, paradigm: str) -> list[dict[str, Any]]:
        """查某范式的全部同构关系（邻居发现）。"""
        if self._conn is not None:
            rows = self._conn.execute(
                (paradigm, paradigm)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory_index.get(paradigm, [])]

    # ---- 检索 ----
    def xǁHomologyDBǁquery_by_paradigm__mutmut_6(self, paradigm: str) -> list[dict[str, Any]]:
        """查某范式的全部同构关系（邻居发现）。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE paradigm_a=? OR paradigm_b=?",
                ).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory_index.get(paradigm, [])]

    # ---- 检索 ----
    def xǁHomologyDBǁquery_by_paradigm__mutmut_7(self, paradigm: str) -> list[dict[str, Any]]:
        """查某范式的全部同构关系（邻居发现）。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "XXSELECT * FROM homologies WHERE paradigm_a=? OR paradigm_b=?XX",
                (paradigm, paradigm)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory_index.get(paradigm, [])]

    # ---- 检索 ----
    def xǁHomologyDBǁquery_by_paradigm__mutmut_8(self, paradigm: str) -> list[dict[str, Any]]:
        """查某范式的全部同构关系（邻居发现）。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "select * from homologies where paradigm_a=? or paradigm_b=?",
                (paradigm, paradigm)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory_index.get(paradigm, [])]

    # ---- 检索 ----
    def xǁHomologyDBǁquery_by_paradigm__mutmut_9(self, paradigm: str) -> list[dict[str, Any]]:
        """查某范式的全部同构关系（邻居发现）。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM HOMOLOGIES WHERE PARADIGM_A=? OR PARADIGM_B=?",
                (paradigm, paradigm)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory_index.get(paradigm, [])]

    # ---- 检索 ----
    def xǁHomologyDBǁquery_by_paradigm__mutmut_10(self, paradigm: str) -> list[dict[str, Any]]:
        """查某范式的全部同构关系（邻居发现）。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE paradigm_a=? OR paradigm_b=?",
                (paradigm, paradigm)).fetchall()
            cols = None
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory_index.get(paradigm, [])]

    # ---- 检索 ----
    def xǁHomologyDBǁquery_by_paradigm__mutmut_11(self, paradigm: str) -> list[dict[str, Any]]:
        """查某范式的全部同构关系（邻居发现）。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE paradigm_a=? OR paradigm_b=?",
                (paradigm, paradigm)).fetchall()
            cols = [d[1] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory_index.get(paradigm, [])]

    # ---- 检索 ----
    def xǁHomologyDBǁquery_by_paradigm__mutmut_12(self, paradigm: str) -> list[dict[str, Any]]:
        """查某范式的全部同构关系（邻居发现）。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE paradigm_a=? OR paradigm_b=?",
                (paradigm, paradigm)).fetchall()
            cols = [d[0] for d in self._conn.execute(None).description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory_index.get(paradigm, [])]

    # ---- 检索 ----
    def xǁHomologyDBǁquery_by_paradigm__mutmut_13(self, paradigm: str) -> list[dict[str, Any]]:
        """查某范式的全部同构关系（邻居发现）。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE paradigm_a=? OR paradigm_b=?",
                (paradigm, paradigm)).fetchall()
            cols = [d[0] for d in self._conn.execute("XXSELECT * FROM homologies LIMIT 0XX").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory_index.get(paradigm, [])]

    # ---- 检索 ----
    def xǁHomologyDBǁquery_by_paradigm__mutmut_14(self, paradigm: str) -> list[dict[str, Any]]:
        """查某范式的全部同构关系（邻居发现）。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE paradigm_a=? OR paradigm_b=?",
                (paradigm, paradigm)).fetchall()
            cols = [d[0] for d in self._conn.execute("select * from homologies limit 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory_index.get(paradigm, [])]

    # ---- 检索 ----
    def xǁHomologyDBǁquery_by_paradigm__mutmut_15(self, paradigm: str) -> list[dict[str, Any]]:
        """查某范式的全部同构关系（邻居发现）。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE paradigm_a=? OR paradigm_b=?",
                (paradigm, paradigm)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM HOMOLOGIES LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory_index.get(paradigm, [])]

    # ---- 检索 ----
    def xǁHomologyDBǁquery_by_paradigm__mutmut_16(self, paradigm: str) -> list[dict[str, Any]]:
        """查某范式的全部同构关系（邻居发现）。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE paradigm_a=? OR paradigm_b=?",
                (paradigm, paradigm)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(None) for r in rows]
        return [dict(h) for h in self._memory_index.get(paradigm, [])]

    # ---- 检索 ----
    def xǁHomologyDBǁquery_by_paradigm__mutmut_17(self, paradigm: str) -> list[dict[str, Any]]:
        """查某范式的全部同构关系（邻居发现）。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE paradigm_a=? OR paradigm_b=?",
                (paradigm, paradigm)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(None, r)) for r in rows]
        return [dict(h) for h in self._memory_index.get(paradigm, [])]

    # ---- 检索 ----
    def xǁHomologyDBǁquery_by_paradigm__mutmut_18(self, paradigm: str) -> list[dict[str, Any]]:
        """查某范式的全部同构关系（邻居发现）。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE paradigm_a=? OR paradigm_b=?",
                (paradigm, paradigm)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, None)) for r in rows]
        return [dict(h) for h in self._memory_index.get(paradigm, [])]

    # ---- 检索 ----
    def xǁHomologyDBǁquery_by_paradigm__mutmut_19(self, paradigm: str) -> list[dict[str, Any]]:
        """查某范式的全部同构关系（邻居发现）。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE paradigm_a=? OR paradigm_b=?",
                (paradigm, paradigm)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(r)) for r in rows]
        return [dict(h) for h in self._memory_index.get(paradigm, [])]

    # ---- 检索 ----
    def xǁHomologyDBǁquery_by_paradigm__mutmut_20(self, paradigm: str) -> list[dict[str, Any]]:
        """查某范式的全部同构关系（邻居发现）。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE paradigm_a=? OR paradigm_b=?",
                (paradigm, paradigm)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, )) for r in rows]
        return [dict(h) for h in self._memory_index.get(paradigm, [])]

    # ---- 检索 ----
    def xǁHomologyDBǁquery_by_paradigm__mutmut_21(self, paradigm: str) -> list[dict[str, Any]]:
        """查某范式的全部同构关系（邻居发现）。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE paradigm_a=? OR paradigm_b=?",
                (paradigm, paradigm)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(None) for h in self._memory_index.get(paradigm, [])]

    # ---- 检索 ----
    def xǁHomologyDBǁquery_by_paradigm__mutmut_22(self, paradigm: str) -> list[dict[str, Any]]:
        """查某范式的全部同构关系（邻居发现）。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE paradigm_a=? OR paradigm_b=?",
                (paradigm, paradigm)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory_index.get(None, [])]

    # ---- 检索 ----
    def xǁHomologyDBǁquery_by_paradigm__mutmut_23(self, paradigm: str) -> list[dict[str, Any]]:
        """查某范式的全部同构关系（邻居发现）。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE paradigm_a=? OR paradigm_b=?",
                (paradigm, paradigm)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory_index.get(paradigm, None)]

    # ---- 检索 ----
    def xǁHomologyDBǁquery_by_paradigm__mutmut_24(self, paradigm: str) -> list[dict[str, Any]]:
        """查某范式的全部同构关系（邻居发现）。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE paradigm_a=? OR paradigm_b=?",
                (paradigm, paradigm)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory_index.get([])]

    # ---- 检索 ----
    def xǁHomologyDBǁquery_by_paradigm__mutmut_25(self, paradigm: str) -> list[dict[str, Any]]:
        """查某范式的全部同构关系（邻居发现）。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE paradigm_a=? OR paradigm_b=?",
                (paradigm, paradigm)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory_index.get(paradigm, )]

    @_mutmut_mutated(mutants_xǁHomologyDBǁquery_by_type__mutmut)
    def query_by_type(self, mechanism_type: str) -> list[dict[str, Any]]:
        """按机制类型查同构。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE mechanism_type=?",
                (mechanism_type,)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory if h["mechanism_type"] == mechanism_type]

    def xǁHomologyDBǁquery_by_type__mutmut_orig(self, mechanism_type: str) -> list[dict[str, Any]]:
        """按机制类型查同构。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE mechanism_type=?",
                (mechanism_type,)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory if h["mechanism_type"] == mechanism_type]

    def xǁHomologyDBǁquery_by_type__mutmut_1(self, mechanism_type: str) -> list[dict[str, Any]]:
        """按机制类型查同构。"""
        if self._conn is None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE mechanism_type=?",
                (mechanism_type,)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory if h["mechanism_type"] == mechanism_type]

    def xǁHomologyDBǁquery_by_type__mutmut_2(self, mechanism_type: str) -> list[dict[str, Any]]:
        """按机制类型查同构。"""
        if self._conn is not None:
            rows = None
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory if h["mechanism_type"] == mechanism_type]

    def xǁHomologyDBǁquery_by_type__mutmut_3(self, mechanism_type: str) -> list[dict[str, Any]]:
        """按机制类型查同构。"""
        if self._conn is not None:
            rows = self._conn.execute(
                None,
                (mechanism_type,)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory if h["mechanism_type"] == mechanism_type]

    def xǁHomologyDBǁquery_by_type__mutmut_4(self, mechanism_type: str) -> list[dict[str, Any]]:
        """按机制类型查同构。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE mechanism_type=?",
                None).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory if h["mechanism_type"] == mechanism_type]

    def xǁHomologyDBǁquery_by_type__mutmut_5(self, mechanism_type: str) -> list[dict[str, Any]]:
        """按机制类型查同构。"""
        if self._conn is not None:
            rows = self._conn.execute(
                (mechanism_type,)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory if h["mechanism_type"] == mechanism_type]

    def xǁHomologyDBǁquery_by_type__mutmut_6(self, mechanism_type: str) -> list[dict[str, Any]]:
        """按机制类型查同构。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE mechanism_type=?",
                ).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory if h["mechanism_type"] == mechanism_type]

    def xǁHomologyDBǁquery_by_type__mutmut_7(self, mechanism_type: str) -> list[dict[str, Any]]:
        """按机制类型查同构。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "XXSELECT * FROM homologies WHERE mechanism_type=?XX",
                (mechanism_type,)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory if h["mechanism_type"] == mechanism_type]

    def xǁHomologyDBǁquery_by_type__mutmut_8(self, mechanism_type: str) -> list[dict[str, Any]]:
        """按机制类型查同构。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "select * from homologies where mechanism_type=?",
                (mechanism_type,)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory if h["mechanism_type"] == mechanism_type]

    def xǁHomologyDBǁquery_by_type__mutmut_9(self, mechanism_type: str) -> list[dict[str, Any]]:
        """按机制类型查同构。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM HOMOLOGIES WHERE MECHANISM_TYPE=?",
                (mechanism_type,)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory if h["mechanism_type"] == mechanism_type]

    def xǁHomologyDBǁquery_by_type__mutmut_10(self, mechanism_type: str) -> list[dict[str, Any]]:
        """按机制类型查同构。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE mechanism_type=?",
                (mechanism_type,)).fetchall()
            cols = None
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory if h["mechanism_type"] == mechanism_type]

    def xǁHomologyDBǁquery_by_type__mutmut_11(self, mechanism_type: str) -> list[dict[str, Any]]:
        """按机制类型查同构。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE mechanism_type=?",
                (mechanism_type,)).fetchall()
            cols = [d[1] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory if h["mechanism_type"] == mechanism_type]

    def xǁHomologyDBǁquery_by_type__mutmut_12(self, mechanism_type: str) -> list[dict[str, Any]]:
        """按机制类型查同构。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE mechanism_type=?",
                (mechanism_type,)).fetchall()
            cols = [d[0] for d in self._conn.execute(None).description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory if h["mechanism_type"] == mechanism_type]

    def xǁHomologyDBǁquery_by_type__mutmut_13(self, mechanism_type: str) -> list[dict[str, Any]]:
        """按机制类型查同构。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE mechanism_type=?",
                (mechanism_type,)).fetchall()
            cols = [d[0] for d in self._conn.execute("XXSELECT * FROM homologies LIMIT 0XX").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory if h["mechanism_type"] == mechanism_type]

    def xǁHomologyDBǁquery_by_type__mutmut_14(self, mechanism_type: str) -> list[dict[str, Any]]:
        """按机制类型查同构。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE mechanism_type=?",
                (mechanism_type,)).fetchall()
            cols = [d[0] for d in self._conn.execute("select * from homologies limit 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory if h["mechanism_type"] == mechanism_type]

    def xǁHomologyDBǁquery_by_type__mutmut_15(self, mechanism_type: str) -> list[dict[str, Any]]:
        """按机制类型查同构。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE mechanism_type=?",
                (mechanism_type,)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM HOMOLOGIES LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory if h["mechanism_type"] == mechanism_type]

    def xǁHomologyDBǁquery_by_type__mutmut_16(self, mechanism_type: str) -> list[dict[str, Any]]:
        """按机制类型查同构。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE mechanism_type=?",
                (mechanism_type,)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(None) for r in rows]
        return [dict(h) for h in self._memory if h["mechanism_type"] == mechanism_type]

    def xǁHomologyDBǁquery_by_type__mutmut_17(self, mechanism_type: str) -> list[dict[str, Any]]:
        """按机制类型查同构。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE mechanism_type=?",
                (mechanism_type,)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(None, r)) for r in rows]
        return [dict(h) for h in self._memory if h["mechanism_type"] == mechanism_type]

    def xǁHomologyDBǁquery_by_type__mutmut_18(self, mechanism_type: str) -> list[dict[str, Any]]:
        """按机制类型查同构。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE mechanism_type=?",
                (mechanism_type,)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, None)) for r in rows]
        return [dict(h) for h in self._memory if h["mechanism_type"] == mechanism_type]

    def xǁHomologyDBǁquery_by_type__mutmut_19(self, mechanism_type: str) -> list[dict[str, Any]]:
        """按机制类型查同构。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE mechanism_type=?",
                (mechanism_type,)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(r)) for r in rows]
        return [dict(h) for h in self._memory if h["mechanism_type"] == mechanism_type]

    def xǁHomologyDBǁquery_by_type__mutmut_20(self, mechanism_type: str) -> list[dict[str, Any]]:
        """按机制类型查同构。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE mechanism_type=?",
                (mechanism_type,)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, )) for r in rows]
        return [dict(h) for h in self._memory if h["mechanism_type"] == mechanism_type]

    def xǁHomologyDBǁquery_by_type__mutmut_21(self, mechanism_type: str) -> list[dict[str, Any]]:
        """按机制类型查同构。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE mechanism_type=?",
                (mechanism_type,)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(None) for h in self._memory if h["mechanism_type"] == mechanism_type]

    def xǁHomologyDBǁquery_by_type__mutmut_22(self, mechanism_type: str) -> list[dict[str, Any]]:
        """按机制类型查同构。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE mechanism_type=?",
                (mechanism_type,)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory if h["XXmechanism_typeXX"] == mechanism_type]

    def xǁHomologyDBǁquery_by_type__mutmut_23(self, mechanism_type: str) -> list[dict[str, Any]]:
        """按机制类型查同构。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE mechanism_type=?",
                (mechanism_type,)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory if h["MECHANISM_TYPE"] == mechanism_type]

    def xǁHomologyDBǁquery_by_type__mutmut_24(self, mechanism_type: str) -> list[dict[str, Any]]:
        """按机制类型查同构。"""
        if self._conn is not None:
            rows = self._conn.execute(
                "SELECT * FROM homologies WHERE mechanism_type=?",
                (mechanism_type,)).fetchall()
            cols = [d[0] for d in self._conn.execute("SELECT * FROM homologies LIMIT 0").description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(h) for h in self._memory if h["mechanism_type"] != mechanism_type]

    @_mutmut_mutated(mutants_xǁHomologyDBǁquery_between__mutmut)
    def query_between(self, a: str, b: str) -> dict[str, Any] | None:
        """查两范式之间的同构（任一方向）。"""
        for h in self.query_by_paradigm(a):
            if h["paradigm_b"] == b or h["paradigm_a"] == b:
                return dict(h)
        return None

    def xǁHomologyDBǁquery_between__mutmut_orig(self, a: str, b: str) -> dict[str, Any] | None:
        """查两范式之间的同构（任一方向）。"""
        for h in self.query_by_paradigm(a):
            if h["paradigm_b"] == b or h["paradigm_a"] == b:
                return dict(h)
        return None

    def xǁHomologyDBǁquery_between__mutmut_1(self, a: str, b: str) -> dict[str, Any] | None:
        """查两范式之间的同构（任一方向）。"""
        for h in self.query_by_paradigm(None):
            if h["paradigm_b"] == b or h["paradigm_a"] == b:
                return dict(h)
        return None

    def xǁHomologyDBǁquery_between__mutmut_2(self, a: str, b: str) -> dict[str, Any] | None:
        """查两范式之间的同构（任一方向）。"""
        for h in self.query_by_paradigm(a):
            if h["paradigm_b"] == b and h["paradigm_a"] == b:
                return dict(h)
        return None

    def xǁHomologyDBǁquery_between__mutmut_3(self, a: str, b: str) -> dict[str, Any] | None:
        """查两范式之间的同构（任一方向）。"""
        for h in self.query_by_paradigm(a):
            if h["XXparadigm_bXX"] == b or h["paradigm_a"] == b:
                return dict(h)
        return None

    def xǁHomologyDBǁquery_between__mutmut_4(self, a: str, b: str) -> dict[str, Any] | None:
        """查两范式之间的同构（任一方向）。"""
        for h in self.query_by_paradigm(a):
            if h["PARADIGM_B"] == b or h["paradigm_a"] == b:
                return dict(h)
        return None

    def xǁHomologyDBǁquery_between__mutmut_5(self, a: str, b: str) -> dict[str, Any] | None:
        """查两范式之间的同构（任一方向）。"""
        for h in self.query_by_paradigm(a):
            if h["paradigm_b"] != b or h["paradigm_a"] == b:
                return dict(h)
        return None

    def xǁHomologyDBǁquery_between__mutmut_6(self, a: str, b: str) -> dict[str, Any] | None:
        """查两范式之间的同构（任一方向）。"""
        for h in self.query_by_paradigm(a):
            if h["paradigm_b"] == b or h["XXparadigm_aXX"] == b:
                return dict(h)
        return None

    def xǁHomologyDBǁquery_between__mutmut_7(self, a: str, b: str) -> dict[str, Any] | None:
        """查两范式之间的同构（任一方向）。"""
        for h in self.query_by_paradigm(a):
            if h["paradigm_b"] == b or h["PARADIGM_A"] == b:
                return dict(h)
        return None

    def xǁHomologyDBǁquery_between__mutmut_8(self, a: str, b: str) -> dict[str, Any] | None:
        """查两范式之间的同构（任一方向）。"""
        for h in self.query_by_paradigm(a):
            if h["paradigm_b"] == b or h["paradigm_a"] != b:
                return dict(h)
        return None

    def xǁHomologyDBǁquery_between__mutmut_9(self, a: str, b: str) -> dict[str, Any] | None:
        """查两范式之间的同构（任一方向）。"""
        for h in self.query_by_paradigm(a):
            if h["paradigm_b"] == b or h["paradigm_a"] == b:
                return dict(None)
        return None

    # ---- 推理 ----
    @_mutmut_mutated(mutants_xǁHomologyDBǁtransitive_closure__mutmut)
    def transitive_closure(self, paradigm: str, depth: int = 2) -> list[str]:
        """传递闭包：A~B 且 B~C ⇒ A~C（弱同构），返回可达范式链。"""
        reachable: set[str] = set()
        frontier = [paradigm]
        for _ in range(depth):
            next_frontier: list[str] = []
            for p in frontier:
                for h in self.query_by_paradigm(p):
                    nb = h["paradigm_b"] if h["paradigm_a"] == p else h["paradigm_a"]
                    if nb != paradigm and nb not in reachable:
                        reachable.add(nb)
                        next_frontier.append(nb)
            frontier = next_frontier
        return sorted(reachable)

    # ---- 推理 ----
    def xǁHomologyDBǁtransitive_closure__mutmut_orig(self, paradigm: str, depth: int = 2) -> list[str]:
        """传递闭包：A~B 且 B~C ⇒ A~C（弱同构），返回可达范式链。"""
        reachable: set[str] = set()
        frontier = [paradigm]
        for _ in range(depth):
            next_frontier: list[str] = []
            for p in frontier:
                for h in self.query_by_paradigm(p):
                    nb = h["paradigm_b"] if h["paradigm_a"] == p else h["paradigm_a"]
                    if nb != paradigm and nb not in reachable:
                        reachable.add(nb)
                        next_frontier.append(nb)
            frontier = next_frontier
        return sorted(reachable)

    # ---- 推理 ----
    def xǁHomologyDBǁtransitive_closure__mutmut_1(self, paradigm: str, depth: int = 3) -> list[str]:
        """传递闭包：A~B 且 B~C ⇒ A~C（弱同构），返回可达范式链。"""
        reachable: set[str] = set()
        frontier = [paradigm]
        for _ in range(depth):
            next_frontier: list[str] = []
            for p in frontier:
                for h in self.query_by_paradigm(p):
                    nb = h["paradigm_b"] if h["paradigm_a"] == p else h["paradigm_a"]
                    if nb != paradigm and nb not in reachable:
                        reachable.add(nb)
                        next_frontier.append(nb)
            frontier = next_frontier
        return sorted(reachable)

    # ---- 推理 ----
    def xǁHomologyDBǁtransitive_closure__mutmut_2(self, paradigm: str, depth: int = 2) -> list[str]:
        """传递闭包：A~B 且 B~C ⇒ A~C（弱同构），返回可达范式链。"""
        reachable: set[str] = None
        frontier = [paradigm]
        for _ in range(depth):
            next_frontier: list[str] = []
            for p in frontier:
                for h in self.query_by_paradigm(p):
                    nb = h["paradigm_b"] if h["paradigm_a"] == p else h["paradigm_a"]
                    if nb != paradigm and nb not in reachable:
                        reachable.add(nb)
                        next_frontier.append(nb)
            frontier = next_frontier
        return sorted(reachable)

    # ---- 推理 ----
    def xǁHomologyDBǁtransitive_closure__mutmut_3(self, paradigm: str, depth: int = 2) -> list[str]:
        """传递闭包：A~B 且 B~C ⇒ A~C（弱同构），返回可达范式链。"""
        reachable: set[str] = set()
        frontier = None
        for _ in range(depth):
            next_frontier: list[str] = []
            for p in frontier:
                for h in self.query_by_paradigm(p):
                    nb = h["paradigm_b"] if h["paradigm_a"] == p else h["paradigm_a"]
                    if nb != paradigm and nb not in reachable:
                        reachable.add(nb)
                        next_frontier.append(nb)
            frontier = next_frontier
        return sorted(reachable)

    # ---- 推理 ----
    def xǁHomologyDBǁtransitive_closure__mutmut_4(self, paradigm: str, depth: int = 2) -> list[str]:
        """传递闭包：A~B 且 B~C ⇒ A~C（弱同构），返回可达范式链。"""
        reachable: set[str] = set()
        frontier = [paradigm]
        for _ in range(None):
            next_frontier: list[str] = []
            for p in frontier:
                for h in self.query_by_paradigm(p):
                    nb = h["paradigm_b"] if h["paradigm_a"] == p else h["paradigm_a"]
                    if nb != paradigm and nb not in reachable:
                        reachable.add(nb)
                        next_frontier.append(nb)
            frontier = next_frontier
        return sorted(reachable)

    # ---- 推理 ----
    def xǁHomologyDBǁtransitive_closure__mutmut_5(self, paradigm: str, depth: int = 2) -> list[str]:
        """传递闭包：A~B 且 B~C ⇒ A~C（弱同构），返回可达范式链。"""
        reachable: set[str] = set()
        frontier = [paradigm]
        for _ in range(depth):
            next_frontier: list[str] = None
            for p in frontier:
                for h in self.query_by_paradigm(p):
                    nb = h["paradigm_b"] if h["paradigm_a"] == p else h["paradigm_a"]
                    if nb != paradigm and nb not in reachable:
                        reachable.add(nb)
                        next_frontier.append(nb)
            frontier = next_frontier
        return sorted(reachable)

    # ---- 推理 ----
    def xǁHomologyDBǁtransitive_closure__mutmut_6(self, paradigm: str, depth: int = 2) -> list[str]:
        """传递闭包：A~B 且 B~C ⇒ A~C（弱同构），返回可达范式链。"""
        reachable: set[str] = set()
        frontier = [paradigm]
        for _ in range(depth):
            next_frontier: list[str] = []
            for p in frontier:
                for h in self.query_by_paradigm(None):
                    nb = h["paradigm_b"] if h["paradigm_a"] == p else h["paradigm_a"]
                    if nb != paradigm and nb not in reachable:
                        reachable.add(nb)
                        next_frontier.append(nb)
            frontier = next_frontier
        return sorted(reachable)

    # ---- 推理 ----
    def xǁHomologyDBǁtransitive_closure__mutmut_7(self, paradigm: str, depth: int = 2) -> list[str]:
        """传递闭包：A~B 且 B~C ⇒ A~C（弱同构），返回可达范式链。"""
        reachable: set[str] = set()
        frontier = [paradigm]
        for _ in range(depth):
            next_frontier: list[str] = []
            for p in frontier:
                for h in self.query_by_paradigm(p):
                    nb = None
                    if nb != paradigm and nb not in reachable:
                        reachable.add(nb)
                        next_frontier.append(nb)
            frontier = next_frontier
        return sorted(reachable)

    # ---- 推理 ----
    def xǁHomologyDBǁtransitive_closure__mutmut_8(self, paradigm: str, depth: int = 2) -> list[str]:
        """传递闭包：A~B 且 B~C ⇒ A~C（弱同构），返回可达范式链。"""
        reachable: set[str] = set()
        frontier = [paradigm]
        for _ in range(depth):
            next_frontier: list[str] = []
            for p in frontier:
                for h in self.query_by_paradigm(p):
                    nb = h["paradigm_b"] if (h["paradigm_a"] == p) and False else h["paradigm_a"]
                    if nb != paradigm and nb not in reachable:
                        reachable.add(nb)
                        next_frontier.append(nb)
            frontier = next_frontier
        return sorted(reachable)

    # ---- 推理 ----
    def xǁHomologyDBǁtransitive_closure__mutmut_9(self, paradigm: str, depth: int = 2) -> list[str]:
        """传递闭包：A~B 且 B~C ⇒ A~C（弱同构），返回可达范式链。"""
        reachable: set[str] = set()
        frontier = [paradigm]
        for _ in range(depth):
            next_frontier: list[str] = []
            for p in frontier:
                for h in self.query_by_paradigm(p):
                    nb = h["paradigm_b"] if (h["paradigm_a"] == p) or True else h["paradigm_a"]
                    if nb != paradigm and nb not in reachable:
                        reachable.add(nb)
                        next_frontier.append(nb)
            frontier = next_frontier
        return sorted(reachable)

    # ---- 推理 ----
    def xǁHomologyDBǁtransitive_closure__mutmut_10(self, paradigm: str, depth: int = 2) -> list[str]:
        """传递闭包：A~B 且 B~C ⇒ A~C（弱同构），返回可达范式链。"""
        reachable: set[str] = set()
        frontier = [paradigm]
        for _ in range(depth):
            next_frontier: list[str] = []
            for p in frontier:
                for h in self.query_by_paradigm(p):
                    nb = h["XXparadigm_bXX"] if h["paradigm_a"] == p else h["paradigm_a"]
                    if nb != paradigm and nb not in reachable:
                        reachable.add(nb)
                        next_frontier.append(nb)
            frontier = next_frontier
        return sorted(reachable)

    # ---- 推理 ----
    def xǁHomologyDBǁtransitive_closure__mutmut_11(self, paradigm: str, depth: int = 2) -> list[str]:
        """传递闭包：A~B 且 B~C ⇒ A~C（弱同构），返回可达范式链。"""
        reachable: set[str] = set()
        frontier = [paradigm]
        for _ in range(depth):
            next_frontier: list[str] = []
            for p in frontier:
                for h in self.query_by_paradigm(p):
                    nb = h["PARADIGM_B"] if h["paradigm_a"] == p else h["paradigm_a"]
                    if nb != paradigm and nb not in reachable:
                        reachable.add(nb)
                        next_frontier.append(nb)
            frontier = next_frontier
        return sorted(reachable)

    # ---- 推理 ----
    def xǁHomologyDBǁtransitive_closure__mutmut_12(self, paradigm: str, depth: int = 2) -> list[str]:
        """传递闭包：A~B 且 B~C ⇒ A~C（弱同构），返回可达范式链。"""
        reachable: set[str] = set()
        frontier = [paradigm]
        for _ in range(depth):
            next_frontier: list[str] = []
            for p in frontier:
                for h in self.query_by_paradigm(p):
                    nb = h["paradigm_b"] if h["XXparadigm_aXX"] == p else h["paradigm_a"]
                    if nb != paradigm and nb not in reachable:
                        reachable.add(nb)
                        next_frontier.append(nb)
            frontier = next_frontier
        return sorted(reachable)

    # ---- 推理 ----
    def xǁHomologyDBǁtransitive_closure__mutmut_13(self, paradigm: str, depth: int = 2) -> list[str]:
        """传递闭包：A~B 且 B~C ⇒ A~C（弱同构），返回可达范式链。"""
        reachable: set[str] = set()
        frontier = [paradigm]
        for _ in range(depth):
            next_frontier: list[str] = []
            for p in frontier:
                for h in self.query_by_paradigm(p):
                    nb = h["paradigm_b"] if h["PARADIGM_A"] == p else h["paradigm_a"]
                    if nb != paradigm and nb not in reachable:
                        reachable.add(nb)
                        next_frontier.append(nb)
            frontier = next_frontier
        return sorted(reachable)

    # ---- 推理 ----
    def xǁHomologyDBǁtransitive_closure__mutmut_14(self, paradigm: str, depth: int = 2) -> list[str]:
        """传递闭包：A~B 且 B~C ⇒ A~C（弱同构），返回可达范式链。"""
        reachable: set[str] = set()
        frontier = [paradigm]
        for _ in range(depth):
            next_frontier: list[str] = []
            for p in frontier:
                for h in self.query_by_paradigm(p):
                    nb = h["paradigm_b"] if h["paradigm_a"] != p else h["paradigm_a"]
                    if nb != paradigm and nb not in reachable:
                        reachable.add(nb)
                        next_frontier.append(nb)
            frontier = next_frontier
        return sorted(reachable)

    # ---- 推理 ----
    def xǁHomologyDBǁtransitive_closure__mutmut_15(self, paradigm: str, depth: int = 2) -> list[str]:
        """传递闭包：A~B 且 B~C ⇒ A~C（弱同构），返回可达范式链。"""
        reachable: set[str] = set()
        frontier = [paradigm]
        for _ in range(depth):
            next_frontier: list[str] = []
            for p in frontier:
                for h in self.query_by_paradigm(p):
                    nb = h["paradigm_b"] if h["paradigm_a"] == p else h["XXparadigm_aXX"]
                    if nb != paradigm and nb not in reachable:
                        reachable.add(nb)
                        next_frontier.append(nb)
            frontier = next_frontier
        return sorted(reachable)

    # ---- 推理 ----
    def xǁHomologyDBǁtransitive_closure__mutmut_16(self, paradigm: str, depth: int = 2) -> list[str]:
        """传递闭包：A~B 且 B~C ⇒ A~C（弱同构），返回可达范式链。"""
        reachable: set[str] = set()
        frontier = [paradigm]
        for _ in range(depth):
            next_frontier: list[str] = []
            for p in frontier:
                for h in self.query_by_paradigm(p):
                    nb = h["paradigm_b"] if h["paradigm_a"] == p else h["PARADIGM_A"]
                    if nb != paradigm and nb not in reachable:
                        reachable.add(nb)
                        next_frontier.append(nb)
            frontier = next_frontier
        return sorted(reachable)

    # ---- 推理 ----
    def xǁHomologyDBǁtransitive_closure__mutmut_17(self, paradigm: str, depth: int = 2) -> list[str]:
        """传递闭包：A~B 且 B~C ⇒ A~C（弱同构），返回可达范式链。"""
        reachable: set[str] = set()
        frontier = [paradigm]
        for _ in range(depth):
            next_frontier: list[str] = []
            for p in frontier:
                for h in self.query_by_paradigm(p):
                    nb = h["paradigm_b"] if h["paradigm_a"] == p else h["paradigm_a"]
                    if nb != paradigm or nb not in reachable:
                        reachable.add(nb)
                        next_frontier.append(nb)
            frontier = next_frontier
        return sorted(reachable)

    # ---- 推理 ----
    def xǁHomologyDBǁtransitive_closure__mutmut_18(self, paradigm: str, depth: int = 2) -> list[str]:
        """传递闭包：A~B 且 B~C ⇒ A~C（弱同构），返回可达范式链。"""
        reachable: set[str] = set()
        frontier = [paradigm]
        for _ in range(depth):
            next_frontier: list[str] = []
            for p in frontier:
                for h in self.query_by_paradigm(p):
                    nb = h["paradigm_b"] if h["paradigm_a"] == p else h["paradigm_a"]
                    if nb == paradigm and nb not in reachable:
                        reachable.add(nb)
                        next_frontier.append(nb)
            frontier = next_frontier
        return sorted(reachable)

    # ---- 推理 ----
    def xǁHomologyDBǁtransitive_closure__mutmut_19(self, paradigm: str, depth: int = 2) -> list[str]:
        """传递闭包：A~B 且 B~C ⇒ A~C（弱同构），返回可达范式链。"""
        reachable: set[str] = set()
        frontier = [paradigm]
        for _ in range(depth):
            next_frontier: list[str] = []
            for p in frontier:
                for h in self.query_by_paradigm(p):
                    nb = h["paradigm_b"] if h["paradigm_a"] == p else h["paradigm_a"]
                    if nb != paradigm and nb in reachable:
                        reachable.add(nb)
                        next_frontier.append(nb)
            frontier = next_frontier
        return sorted(reachable)

    # ---- 推理 ----
    def xǁHomologyDBǁtransitive_closure__mutmut_20(self, paradigm: str, depth: int = 2) -> list[str]:
        """传递闭包：A~B 且 B~C ⇒ A~C（弱同构），返回可达范式链。"""
        reachable: set[str] = set()
        frontier = [paradigm]
        for _ in range(depth):
            next_frontier: list[str] = []
            for p in frontier:
                for h in self.query_by_paradigm(p):
                    nb = h["paradigm_b"] if h["paradigm_a"] == p else h["paradigm_a"]
                    if nb != paradigm and nb not in reachable:
                        reachable.add(None)
                        next_frontier.append(nb)
            frontier = next_frontier
        return sorted(reachable)

    # ---- 推理 ----
    def xǁHomologyDBǁtransitive_closure__mutmut_21(self, paradigm: str, depth: int = 2) -> list[str]:
        """传递闭包：A~B 且 B~C ⇒ A~C（弱同构），返回可达范式链。"""
        reachable: set[str] = set()
        frontier = [paradigm]
        for _ in range(depth):
            next_frontier: list[str] = []
            for p in frontier:
                for h in self.query_by_paradigm(p):
                    nb = h["paradigm_b"] if h["paradigm_a"] == p else h["paradigm_a"]
                    if nb != paradigm and nb not in reachable:
                        reachable.add(nb)
                        next_frontier.append(None)
            frontier = next_frontier
        return sorted(reachable)

    # ---- 推理 ----
    def xǁHomologyDBǁtransitive_closure__mutmut_22(self, paradigm: str, depth: int = 2) -> list[str]:
        """传递闭包：A~B 且 B~C ⇒ A~C（弱同构），返回可达范式链。"""
        reachable: set[str] = set()
        frontier = [paradigm]
        for _ in range(depth):
            next_frontier: list[str] = []
            for p in frontier:
                for h in self.query_by_paradigm(p):
                    nb = h["paradigm_b"] if h["paradigm_a"] == p else h["paradigm_a"]
                    if nb != paradigm and nb not in reachable:
                        reachable.add(nb)
                        next_frontier.append(nb)
            frontier = None
        return sorted(reachable)

    # ---- 推理 ----
    def xǁHomologyDBǁtransitive_closure__mutmut_23(self, paradigm: str, depth: int = 2) -> list[str]:
        """传递闭包：A~B 且 B~C ⇒ A~C（弱同构），返回可达范式链。"""
        reachable: set[str] = set()
        frontier = [paradigm]
        for _ in range(depth):
            next_frontier: list[str] = []
            for p in frontier:
                for h in self.query_by_paradigm(p):
                    nb = h["paradigm_b"] if h["paradigm_a"] == p else h["paradigm_a"]
                    if nb != paradigm and nb not in reachable:
                        reachable.add(nb)
                        next_frontier.append(nb)
            frontier = next_frontier
        return sorted(None)

    @_mutmut_mutated(mutants_xǁHomologyDBǁneighbors__mutmut)
    def neighbors(self, paradigm: str) -> list[str]:
        """直接邻居（一跳同构范式）。"""
        return sorted({h["paradigm_b"] if h["paradigm_a"] == paradigm
                       else h["paradigm_a"]
                       for h in self.query_by_paradigm(paradigm)})

    def xǁHomologyDBǁneighbors__mutmut_orig(self, paradigm: str) -> list[str]:
        """直接邻居（一跳同构范式）。"""
        return sorted({h["paradigm_b"] if h["paradigm_a"] == paradigm
                       else h["paradigm_a"]
                       for h in self.query_by_paradigm(paradigm)})

    def xǁHomologyDBǁneighbors__mutmut_1(self, paradigm: str) -> list[str]:
        """直接邻居（一跳同构范式）。"""
        return sorted(None)

    def xǁHomologyDBǁneighbors__mutmut_2(self, paradigm: str) -> list[str]:
        """直接邻居（一跳同构范式）。"""
        return sorted({h["paradigm_b"] if (h["paradigm_a"] == paradigm) and False
                       else h["paradigm_a"]
                       for h in self.query_by_paradigm(paradigm)})

    def xǁHomologyDBǁneighbors__mutmut_3(self, paradigm: str) -> list[str]:
        """直接邻居（一跳同构范式）。"""
        return sorted({h["paradigm_b"] if (h["paradigm_a"] == paradigm) or True
                       else h["paradigm_a"]
                       for h in self.query_by_paradigm(paradigm)})

    def xǁHomologyDBǁneighbors__mutmut_4(self, paradigm: str) -> list[str]:
        """直接邻居（一跳同构范式）。"""
        return sorted({h["XXparadigm_bXX"] if h["paradigm_a"] == paradigm
                       else h["paradigm_a"]
                       for h in self.query_by_paradigm(paradigm)})

    def xǁHomologyDBǁneighbors__mutmut_5(self, paradigm: str) -> list[str]:
        """直接邻居（一跳同构范式）。"""
        return sorted({h["PARADIGM_B"] if h["paradigm_a"] == paradigm
                       else h["paradigm_a"]
                       for h in self.query_by_paradigm(paradigm)})

    def xǁHomologyDBǁneighbors__mutmut_6(self, paradigm: str) -> list[str]:
        """直接邻居（一跳同构范式）。"""
        return sorted({h["paradigm_b"] if h["XXparadigm_aXX"] == paradigm
                       else h["paradigm_a"]
                       for h in self.query_by_paradigm(paradigm)})

    def xǁHomologyDBǁneighbors__mutmut_7(self, paradigm: str) -> list[str]:
        """直接邻居（一跳同构范式）。"""
        return sorted({h["paradigm_b"] if h["PARADIGM_A"] == paradigm
                       else h["paradigm_a"]
                       for h in self.query_by_paradigm(paradigm)})

    def xǁHomologyDBǁneighbors__mutmut_8(self, paradigm: str) -> list[str]:
        """直接邻居（一跳同构范式）。"""
        return sorted({h["paradigm_b"] if h["paradigm_a"] != paradigm
                       else h["paradigm_a"]
                       for h in self.query_by_paradigm(paradigm)})

    def xǁHomologyDBǁneighbors__mutmut_9(self, paradigm: str) -> list[str]:
        """直接邻居（一跳同构范式）。"""
        return sorted({h["paradigm_b"] if h["paradigm_a"] == paradigm
                       else h["XXparadigm_aXX"]
                       for h in self.query_by_paradigm(paradigm)})

    def xǁHomologyDBǁneighbors__mutmut_10(self, paradigm: str) -> list[str]:
        """直接邻居（一跳同构范式）。"""
        return sorted({h["paradigm_b"] if h["paradigm_a"] == paradigm
                       else h["PARADIGM_A"]
                       for h in self.query_by_paradigm(paradigm)})

    def xǁHomologyDBǁneighbors__mutmut_11(self, paradigm: str) -> list[str]:
        """直接邻居（一跳同构范式）。"""
        return sorted({h["paradigm_b"] if h["paradigm_a"] == paradigm
                       else h["paradigm_a"]
                       for h in self.query_by_paradigm(None)})

    @_mutmut_mutated(mutants_xǁHomologyDBǁcount__mutmut)
    def count(self) -> int:
        if self._conn is not None:
            return self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        return len(self._memory)

    def xǁHomologyDBǁcount__mutmut_orig(self) -> int:
        if self._conn is not None:
            return self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        return len(self._memory)

    def xǁHomologyDBǁcount__mutmut_1(self) -> int:
        if self._conn is None:
            return self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
        return len(self._memory)

    def xǁHomologyDBǁcount__mutmut_2(self) -> int:
        if self._conn is not None:
            return self._conn.execute(None).fetchone()[0]
        return len(self._memory)

    def xǁHomologyDBǁcount__mutmut_3(self) -> int:
        if self._conn is not None:
            return self._conn.execute("XXSELECT COUNT(*) FROM homologiesXX").fetchone()[0]
        return len(self._memory)

    def xǁHomologyDBǁcount__mutmut_4(self) -> int:
        if self._conn is not None:
            return self._conn.execute("select count(*) from homologies").fetchone()[0]
        return len(self._memory)

    def xǁHomologyDBǁcount__mutmut_5(self) -> int:
        if self._conn is not None:
            return self._conn.execute("SELECT COUNT(*) FROM HOMOLOGIES").fetchone()[0]
        return len(self._memory)

    def xǁHomologyDBǁcount__mutmut_6(self) -> int:
        if self._conn is not None:
            return self._conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[1]
        return len(self._memory)

    @_mutmut_mutated(mutants_xǁHomologyDBǁclose__mutmut)
    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def xǁHomologyDBǁclose__mutmut_orig(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def xǁHomologyDBǁclose__mutmut_1(self) -> None:
        if self._conn is None:
            self._conn.close()
            self._conn = None

    def xǁHomologyDBǁclose__mutmut_2(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = ""

mutants_xǁHomologyDBǁ__init____mutmut['_mutmut_orig'] = HomologyDB.xǁHomologyDBǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ__init____mutmut['xǁHomologyDBǁ__init____mutmut_1'] = HomologyDB.xǁHomologyDBǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ__init____mutmut['xǁHomologyDBǁ__init____mutmut_2'] = HomologyDB.xǁHomologyDBǁ__init____mutmut_2 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ__init____mutmut['xǁHomologyDBǁ__init____mutmut_3'] = HomologyDB.xǁHomologyDBǁ__init____mutmut_3 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ__init____mutmut['xǁHomologyDBǁ__init____mutmut_4'] = HomologyDB.xǁHomologyDBǁ__init____mutmut_4 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ__init____mutmut['xǁHomologyDBǁ__init____mutmut_5'] = HomologyDB.xǁHomologyDBǁ__init____mutmut_5 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ__init____mutmut['xǁHomologyDBǁ__init____mutmut_6'] = HomologyDB.xǁHomologyDBǁ__init____mutmut_6 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ__init____mutmut['xǁHomologyDBǁ__init____mutmut_7'] = HomologyDB.xǁHomologyDBǁ__init____mutmut_7 # type: ignore # mutmut generated

mutants_xǁHomologyDBǁ_init_schema__mutmut['_mutmut_orig'] = HomologyDB.xǁHomologyDBǁ_init_schema__mutmut_orig # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_init_schema__mutmut['xǁHomologyDBǁ_init_schema__mutmut_1'] = HomologyDB.xǁHomologyDBǁ_init_schema__mutmut_1 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_init_schema__mutmut['xǁHomologyDBǁ_init_schema__mutmut_2'] = HomologyDB.xǁHomologyDBǁ_init_schema__mutmut_2 # type: ignore # mutmut generated

mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['_mutmut_orig'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_orig # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_1'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_1 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_2'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_2 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_3'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_3 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_4'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_4 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_5'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_5 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_6'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_6 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_7'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_7 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_8'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_8 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_9'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_9 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_10'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_10 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_11'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_11 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_12'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_12 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_13'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_13 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_14'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_14 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_15'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_15 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_16'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_16 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_17'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_17 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_18'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_18 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_19'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_19 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_20'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_20 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_21'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_21 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_22'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_22 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_23'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_23 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_24'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_24 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_25'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_25 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_26'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_26 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_27'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_27 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_28'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_28 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_29'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_29 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_30'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_30 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_31'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_31 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_seed_if_empty__mutmut['xǁHomologyDBǁ_seed_if_empty__mutmut_32'] = HomologyDB.xǁHomologyDBǁ_seed_if_empty__mutmut_32 # type: ignore # mutmut generated

mutants_xǁHomologyDBǁ_load_seed_memory__mutmut['_mutmut_orig'] = HomologyDB.xǁHomologyDBǁ_load_seed_memory__mutmut_orig # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_load_seed_memory__mutmut['xǁHomologyDBǁ_load_seed_memory__mutmut_1'] = HomologyDB.xǁHomologyDBǁ_load_seed_memory__mutmut_1 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_load_seed_memory__mutmut['xǁHomologyDBǁ_load_seed_memory__mutmut_2'] = HomologyDB.xǁHomologyDBǁ_load_seed_memory__mutmut_2 # type: ignore # mutmut generated

mutants_xǁHomologyDBǁ_rebuild_index__mutmut['_mutmut_orig'] = HomologyDB.xǁHomologyDBǁ_rebuild_index__mutmut_orig # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_rebuild_index__mutmut['xǁHomologyDBǁ_rebuild_index__mutmut_1'] = HomologyDB.xǁHomologyDBǁ_rebuild_index__mutmut_1 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_rebuild_index__mutmut['xǁHomologyDBǁ_rebuild_index__mutmut_2'] = HomologyDB.xǁHomologyDBǁ_rebuild_index__mutmut_2 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_rebuild_index__mutmut['xǁHomologyDBǁ_rebuild_index__mutmut_3'] = HomologyDB.xǁHomologyDBǁ_rebuild_index__mutmut_3 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_rebuild_index__mutmut['xǁHomologyDBǁ_rebuild_index__mutmut_4'] = HomologyDB.xǁHomologyDBǁ_rebuild_index__mutmut_4 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_rebuild_index__mutmut['xǁHomologyDBǁ_rebuild_index__mutmut_5'] = HomologyDB.xǁHomologyDBǁ_rebuild_index__mutmut_5 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_rebuild_index__mutmut['xǁHomologyDBǁ_rebuild_index__mutmut_6'] = HomologyDB.xǁHomologyDBǁ_rebuild_index__mutmut_6 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_rebuild_index__mutmut['xǁHomologyDBǁ_rebuild_index__mutmut_7'] = HomologyDB.xǁHomologyDBǁ_rebuild_index__mutmut_7 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_rebuild_index__mutmut['xǁHomologyDBǁ_rebuild_index__mutmut_8'] = HomologyDB.xǁHomologyDBǁ_rebuild_index__mutmut_8 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_rebuild_index__mutmut['xǁHomologyDBǁ_rebuild_index__mutmut_9'] = HomologyDB.xǁHomologyDBǁ_rebuild_index__mutmut_9 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁ_rebuild_index__mutmut['xǁHomologyDBǁ_rebuild_index__mutmut_10'] = HomologyDB.xǁHomologyDBǁ_rebuild_index__mutmut_10 # type: ignore # mutmut generated

mutants_xǁHomologyDBǁregister__mutmut['_mutmut_orig'] = HomologyDB.xǁHomologyDBǁregister__mutmut_orig # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_1'] = HomologyDB.xǁHomologyDBǁregister__mutmut_1 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_2'] = HomologyDB.xǁHomologyDBǁregister__mutmut_2 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_3'] = HomologyDB.xǁHomologyDBǁregister__mutmut_3 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_4'] = HomologyDB.xǁHomologyDBǁregister__mutmut_4 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_5'] = HomologyDB.xǁHomologyDBǁregister__mutmut_5 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_6'] = HomologyDB.xǁHomologyDBǁregister__mutmut_6 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_7'] = HomologyDB.xǁHomologyDBǁregister__mutmut_7 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_8'] = HomologyDB.xǁHomologyDBǁregister__mutmut_8 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_9'] = HomologyDB.xǁHomologyDBǁregister__mutmut_9 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_10'] = HomologyDB.xǁHomologyDBǁregister__mutmut_10 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_11'] = HomologyDB.xǁHomologyDBǁregister__mutmut_11 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_12'] = HomologyDB.xǁHomologyDBǁregister__mutmut_12 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_13'] = HomologyDB.xǁHomologyDBǁregister__mutmut_13 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_14'] = HomologyDB.xǁHomologyDBǁregister__mutmut_14 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_15'] = HomologyDB.xǁHomologyDBǁregister__mutmut_15 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_16'] = HomologyDB.xǁHomologyDBǁregister__mutmut_16 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_17'] = HomologyDB.xǁHomologyDBǁregister__mutmut_17 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_18'] = HomologyDB.xǁHomologyDBǁregister__mutmut_18 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_19'] = HomologyDB.xǁHomologyDBǁregister__mutmut_19 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_20'] = HomologyDB.xǁHomologyDBǁregister__mutmut_20 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_21'] = HomologyDB.xǁHomologyDBǁregister__mutmut_21 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_22'] = HomologyDB.xǁHomologyDBǁregister__mutmut_22 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_23'] = HomologyDB.xǁHomologyDBǁregister__mutmut_23 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_24'] = HomologyDB.xǁHomologyDBǁregister__mutmut_24 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_25'] = HomologyDB.xǁHomologyDBǁregister__mutmut_25 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_26'] = HomologyDB.xǁHomologyDBǁregister__mutmut_26 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_27'] = HomologyDB.xǁHomologyDBǁregister__mutmut_27 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_28'] = HomologyDB.xǁHomologyDBǁregister__mutmut_28 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_29'] = HomologyDB.xǁHomologyDBǁregister__mutmut_29 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_30'] = HomologyDB.xǁHomologyDBǁregister__mutmut_30 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_31'] = HomologyDB.xǁHomologyDBǁregister__mutmut_31 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_32'] = HomologyDB.xǁHomologyDBǁregister__mutmut_32 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_33'] = HomologyDB.xǁHomologyDBǁregister__mutmut_33 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_34'] = HomologyDB.xǁHomologyDBǁregister__mutmut_34 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_35'] = HomologyDB.xǁHomologyDBǁregister__mutmut_35 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_36'] = HomologyDB.xǁHomologyDBǁregister__mutmut_36 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_37'] = HomologyDB.xǁHomologyDBǁregister__mutmut_37 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_38'] = HomologyDB.xǁHomologyDBǁregister__mutmut_38 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_39'] = HomologyDB.xǁHomologyDBǁregister__mutmut_39 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_40'] = HomologyDB.xǁHomologyDBǁregister__mutmut_40 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_41'] = HomologyDB.xǁHomologyDBǁregister__mutmut_41 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_42'] = HomologyDB.xǁHomologyDBǁregister__mutmut_42 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_43'] = HomologyDB.xǁHomologyDBǁregister__mutmut_43 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_44'] = HomologyDB.xǁHomologyDBǁregister__mutmut_44 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁregister__mutmut['xǁHomologyDBǁregister__mutmut_45'] = HomologyDB.xǁHomologyDBǁregister__mutmut_45 # type: ignore # mutmut generated

mutants_xǁHomologyDBǁquery_by_paradigm__mutmut['_mutmut_orig'] = HomologyDB.xǁHomologyDBǁquery_by_paradigm__mutmut_orig # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_paradigm__mutmut['xǁHomologyDBǁquery_by_paradigm__mutmut_1'] = HomologyDB.xǁHomologyDBǁquery_by_paradigm__mutmut_1 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_paradigm__mutmut['xǁHomologyDBǁquery_by_paradigm__mutmut_2'] = HomologyDB.xǁHomologyDBǁquery_by_paradigm__mutmut_2 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_paradigm__mutmut['xǁHomologyDBǁquery_by_paradigm__mutmut_3'] = HomologyDB.xǁHomologyDBǁquery_by_paradigm__mutmut_3 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_paradigm__mutmut['xǁHomologyDBǁquery_by_paradigm__mutmut_4'] = HomologyDB.xǁHomologyDBǁquery_by_paradigm__mutmut_4 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_paradigm__mutmut['xǁHomologyDBǁquery_by_paradigm__mutmut_5'] = HomologyDB.xǁHomologyDBǁquery_by_paradigm__mutmut_5 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_paradigm__mutmut['xǁHomologyDBǁquery_by_paradigm__mutmut_6'] = HomologyDB.xǁHomologyDBǁquery_by_paradigm__mutmut_6 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_paradigm__mutmut['xǁHomologyDBǁquery_by_paradigm__mutmut_7'] = HomologyDB.xǁHomologyDBǁquery_by_paradigm__mutmut_7 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_paradigm__mutmut['xǁHomologyDBǁquery_by_paradigm__mutmut_8'] = HomologyDB.xǁHomologyDBǁquery_by_paradigm__mutmut_8 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_paradigm__mutmut['xǁHomologyDBǁquery_by_paradigm__mutmut_9'] = HomologyDB.xǁHomologyDBǁquery_by_paradigm__mutmut_9 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_paradigm__mutmut['xǁHomologyDBǁquery_by_paradigm__mutmut_10'] = HomologyDB.xǁHomologyDBǁquery_by_paradigm__mutmut_10 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_paradigm__mutmut['xǁHomologyDBǁquery_by_paradigm__mutmut_11'] = HomologyDB.xǁHomologyDBǁquery_by_paradigm__mutmut_11 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_paradigm__mutmut['xǁHomologyDBǁquery_by_paradigm__mutmut_12'] = HomologyDB.xǁHomologyDBǁquery_by_paradigm__mutmut_12 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_paradigm__mutmut['xǁHomologyDBǁquery_by_paradigm__mutmut_13'] = HomologyDB.xǁHomologyDBǁquery_by_paradigm__mutmut_13 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_paradigm__mutmut['xǁHomologyDBǁquery_by_paradigm__mutmut_14'] = HomologyDB.xǁHomologyDBǁquery_by_paradigm__mutmut_14 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_paradigm__mutmut['xǁHomologyDBǁquery_by_paradigm__mutmut_15'] = HomologyDB.xǁHomologyDBǁquery_by_paradigm__mutmut_15 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_paradigm__mutmut['xǁHomologyDBǁquery_by_paradigm__mutmut_16'] = HomologyDB.xǁHomologyDBǁquery_by_paradigm__mutmut_16 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_paradigm__mutmut['xǁHomologyDBǁquery_by_paradigm__mutmut_17'] = HomologyDB.xǁHomologyDBǁquery_by_paradigm__mutmut_17 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_paradigm__mutmut['xǁHomologyDBǁquery_by_paradigm__mutmut_18'] = HomologyDB.xǁHomologyDBǁquery_by_paradigm__mutmut_18 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_paradigm__mutmut['xǁHomologyDBǁquery_by_paradigm__mutmut_19'] = HomologyDB.xǁHomologyDBǁquery_by_paradigm__mutmut_19 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_paradigm__mutmut['xǁHomologyDBǁquery_by_paradigm__mutmut_20'] = HomologyDB.xǁHomologyDBǁquery_by_paradigm__mutmut_20 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_paradigm__mutmut['xǁHomologyDBǁquery_by_paradigm__mutmut_21'] = HomologyDB.xǁHomologyDBǁquery_by_paradigm__mutmut_21 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_paradigm__mutmut['xǁHomologyDBǁquery_by_paradigm__mutmut_22'] = HomologyDB.xǁHomologyDBǁquery_by_paradigm__mutmut_22 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_paradigm__mutmut['xǁHomologyDBǁquery_by_paradigm__mutmut_23'] = HomologyDB.xǁHomologyDBǁquery_by_paradigm__mutmut_23 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_paradigm__mutmut['xǁHomologyDBǁquery_by_paradigm__mutmut_24'] = HomologyDB.xǁHomologyDBǁquery_by_paradigm__mutmut_24 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_paradigm__mutmut['xǁHomologyDBǁquery_by_paradigm__mutmut_25'] = HomologyDB.xǁHomologyDBǁquery_by_paradigm__mutmut_25 # type: ignore # mutmut generated

mutants_xǁHomologyDBǁquery_by_type__mutmut['_mutmut_orig'] = HomologyDB.xǁHomologyDBǁquery_by_type__mutmut_orig # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_type__mutmut['xǁHomologyDBǁquery_by_type__mutmut_1'] = HomologyDB.xǁHomologyDBǁquery_by_type__mutmut_1 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_type__mutmut['xǁHomologyDBǁquery_by_type__mutmut_2'] = HomologyDB.xǁHomologyDBǁquery_by_type__mutmut_2 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_type__mutmut['xǁHomologyDBǁquery_by_type__mutmut_3'] = HomologyDB.xǁHomologyDBǁquery_by_type__mutmut_3 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_type__mutmut['xǁHomologyDBǁquery_by_type__mutmut_4'] = HomologyDB.xǁHomologyDBǁquery_by_type__mutmut_4 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_type__mutmut['xǁHomologyDBǁquery_by_type__mutmut_5'] = HomologyDB.xǁHomologyDBǁquery_by_type__mutmut_5 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_type__mutmut['xǁHomologyDBǁquery_by_type__mutmut_6'] = HomologyDB.xǁHomologyDBǁquery_by_type__mutmut_6 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_type__mutmut['xǁHomologyDBǁquery_by_type__mutmut_7'] = HomologyDB.xǁHomologyDBǁquery_by_type__mutmut_7 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_type__mutmut['xǁHomologyDBǁquery_by_type__mutmut_8'] = HomologyDB.xǁHomologyDBǁquery_by_type__mutmut_8 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_type__mutmut['xǁHomologyDBǁquery_by_type__mutmut_9'] = HomologyDB.xǁHomologyDBǁquery_by_type__mutmut_9 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_type__mutmut['xǁHomologyDBǁquery_by_type__mutmut_10'] = HomologyDB.xǁHomologyDBǁquery_by_type__mutmut_10 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_type__mutmut['xǁHomologyDBǁquery_by_type__mutmut_11'] = HomologyDB.xǁHomologyDBǁquery_by_type__mutmut_11 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_type__mutmut['xǁHomologyDBǁquery_by_type__mutmut_12'] = HomologyDB.xǁHomologyDBǁquery_by_type__mutmut_12 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_type__mutmut['xǁHomologyDBǁquery_by_type__mutmut_13'] = HomologyDB.xǁHomologyDBǁquery_by_type__mutmut_13 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_type__mutmut['xǁHomologyDBǁquery_by_type__mutmut_14'] = HomologyDB.xǁHomologyDBǁquery_by_type__mutmut_14 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_type__mutmut['xǁHomologyDBǁquery_by_type__mutmut_15'] = HomologyDB.xǁHomologyDBǁquery_by_type__mutmut_15 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_type__mutmut['xǁHomologyDBǁquery_by_type__mutmut_16'] = HomologyDB.xǁHomologyDBǁquery_by_type__mutmut_16 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_type__mutmut['xǁHomologyDBǁquery_by_type__mutmut_17'] = HomologyDB.xǁHomologyDBǁquery_by_type__mutmut_17 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_type__mutmut['xǁHomologyDBǁquery_by_type__mutmut_18'] = HomologyDB.xǁHomologyDBǁquery_by_type__mutmut_18 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_type__mutmut['xǁHomologyDBǁquery_by_type__mutmut_19'] = HomologyDB.xǁHomologyDBǁquery_by_type__mutmut_19 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_type__mutmut['xǁHomologyDBǁquery_by_type__mutmut_20'] = HomologyDB.xǁHomologyDBǁquery_by_type__mutmut_20 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_type__mutmut['xǁHomologyDBǁquery_by_type__mutmut_21'] = HomologyDB.xǁHomologyDBǁquery_by_type__mutmut_21 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_type__mutmut['xǁHomologyDBǁquery_by_type__mutmut_22'] = HomologyDB.xǁHomologyDBǁquery_by_type__mutmut_22 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_type__mutmut['xǁHomologyDBǁquery_by_type__mutmut_23'] = HomologyDB.xǁHomologyDBǁquery_by_type__mutmut_23 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_by_type__mutmut['xǁHomologyDBǁquery_by_type__mutmut_24'] = HomologyDB.xǁHomologyDBǁquery_by_type__mutmut_24 # type: ignore # mutmut generated

mutants_xǁHomologyDBǁquery_between__mutmut['_mutmut_orig'] = HomologyDB.xǁHomologyDBǁquery_between__mutmut_orig # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_between__mutmut['xǁHomologyDBǁquery_between__mutmut_1'] = HomologyDB.xǁHomologyDBǁquery_between__mutmut_1 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_between__mutmut['xǁHomologyDBǁquery_between__mutmut_2'] = HomologyDB.xǁHomologyDBǁquery_between__mutmut_2 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_between__mutmut['xǁHomologyDBǁquery_between__mutmut_3'] = HomologyDB.xǁHomologyDBǁquery_between__mutmut_3 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_between__mutmut['xǁHomologyDBǁquery_between__mutmut_4'] = HomologyDB.xǁHomologyDBǁquery_between__mutmut_4 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_between__mutmut['xǁHomologyDBǁquery_between__mutmut_5'] = HomologyDB.xǁHomologyDBǁquery_between__mutmut_5 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_between__mutmut['xǁHomologyDBǁquery_between__mutmut_6'] = HomologyDB.xǁHomologyDBǁquery_between__mutmut_6 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_between__mutmut['xǁHomologyDBǁquery_between__mutmut_7'] = HomologyDB.xǁHomologyDBǁquery_between__mutmut_7 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_between__mutmut['xǁHomologyDBǁquery_between__mutmut_8'] = HomologyDB.xǁHomologyDBǁquery_between__mutmut_8 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁquery_between__mutmut['xǁHomologyDBǁquery_between__mutmut_9'] = HomologyDB.xǁHomologyDBǁquery_between__mutmut_9 # type: ignore # mutmut generated

mutants_xǁHomologyDBǁtransitive_closure__mutmut['_mutmut_orig'] = HomologyDB.xǁHomologyDBǁtransitive_closure__mutmut_orig # type: ignore # mutmut generated
mutants_xǁHomologyDBǁtransitive_closure__mutmut['xǁHomologyDBǁtransitive_closure__mutmut_1'] = HomologyDB.xǁHomologyDBǁtransitive_closure__mutmut_1 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁtransitive_closure__mutmut['xǁHomologyDBǁtransitive_closure__mutmut_2'] = HomologyDB.xǁHomologyDBǁtransitive_closure__mutmut_2 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁtransitive_closure__mutmut['xǁHomologyDBǁtransitive_closure__mutmut_3'] = HomologyDB.xǁHomologyDBǁtransitive_closure__mutmut_3 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁtransitive_closure__mutmut['xǁHomologyDBǁtransitive_closure__mutmut_4'] = HomologyDB.xǁHomologyDBǁtransitive_closure__mutmut_4 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁtransitive_closure__mutmut['xǁHomologyDBǁtransitive_closure__mutmut_5'] = HomologyDB.xǁHomologyDBǁtransitive_closure__mutmut_5 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁtransitive_closure__mutmut['xǁHomologyDBǁtransitive_closure__mutmut_6'] = HomologyDB.xǁHomologyDBǁtransitive_closure__mutmut_6 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁtransitive_closure__mutmut['xǁHomologyDBǁtransitive_closure__mutmut_7'] = HomologyDB.xǁHomologyDBǁtransitive_closure__mutmut_7 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁtransitive_closure__mutmut['xǁHomologyDBǁtransitive_closure__mutmut_8'] = HomologyDB.xǁHomologyDBǁtransitive_closure__mutmut_8 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁtransitive_closure__mutmut['xǁHomologyDBǁtransitive_closure__mutmut_9'] = HomologyDB.xǁHomologyDBǁtransitive_closure__mutmut_9 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁtransitive_closure__mutmut['xǁHomologyDBǁtransitive_closure__mutmut_10'] = HomologyDB.xǁHomologyDBǁtransitive_closure__mutmut_10 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁtransitive_closure__mutmut['xǁHomologyDBǁtransitive_closure__mutmut_11'] = HomologyDB.xǁHomologyDBǁtransitive_closure__mutmut_11 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁtransitive_closure__mutmut['xǁHomologyDBǁtransitive_closure__mutmut_12'] = HomologyDB.xǁHomologyDBǁtransitive_closure__mutmut_12 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁtransitive_closure__mutmut['xǁHomologyDBǁtransitive_closure__mutmut_13'] = HomologyDB.xǁHomologyDBǁtransitive_closure__mutmut_13 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁtransitive_closure__mutmut['xǁHomologyDBǁtransitive_closure__mutmut_14'] = HomologyDB.xǁHomologyDBǁtransitive_closure__mutmut_14 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁtransitive_closure__mutmut['xǁHomologyDBǁtransitive_closure__mutmut_15'] = HomologyDB.xǁHomologyDBǁtransitive_closure__mutmut_15 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁtransitive_closure__mutmut['xǁHomologyDBǁtransitive_closure__mutmut_16'] = HomologyDB.xǁHomologyDBǁtransitive_closure__mutmut_16 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁtransitive_closure__mutmut['xǁHomologyDBǁtransitive_closure__mutmut_17'] = HomologyDB.xǁHomologyDBǁtransitive_closure__mutmut_17 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁtransitive_closure__mutmut['xǁHomologyDBǁtransitive_closure__mutmut_18'] = HomologyDB.xǁHomologyDBǁtransitive_closure__mutmut_18 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁtransitive_closure__mutmut['xǁHomologyDBǁtransitive_closure__mutmut_19'] = HomologyDB.xǁHomologyDBǁtransitive_closure__mutmut_19 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁtransitive_closure__mutmut['xǁHomologyDBǁtransitive_closure__mutmut_20'] = HomologyDB.xǁHomologyDBǁtransitive_closure__mutmut_20 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁtransitive_closure__mutmut['xǁHomologyDBǁtransitive_closure__mutmut_21'] = HomologyDB.xǁHomologyDBǁtransitive_closure__mutmut_21 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁtransitive_closure__mutmut['xǁHomologyDBǁtransitive_closure__mutmut_22'] = HomologyDB.xǁHomologyDBǁtransitive_closure__mutmut_22 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁtransitive_closure__mutmut['xǁHomologyDBǁtransitive_closure__mutmut_23'] = HomologyDB.xǁHomologyDBǁtransitive_closure__mutmut_23 # type: ignore # mutmut generated

mutants_xǁHomologyDBǁneighbors__mutmut['_mutmut_orig'] = HomologyDB.xǁHomologyDBǁneighbors__mutmut_orig # type: ignore # mutmut generated
mutants_xǁHomologyDBǁneighbors__mutmut['xǁHomologyDBǁneighbors__mutmut_1'] = HomologyDB.xǁHomologyDBǁneighbors__mutmut_1 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁneighbors__mutmut['xǁHomologyDBǁneighbors__mutmut_2'] = HomologyDB.xǁHomologyDBǁneighbors__mutmut_2 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁneighbors__mutmut['xǁHomologyDBǁneighbors__mutmut_3'] = HomologyDB.xǁHomologyDBǁneighbors__mutmut_3 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁneighbors__mutmut['xǁHomologyDBǁneighbors__mutmut_4'] = HomologyDB.xǁHomologyDBǁneighbors__mutmut_4 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁneighbors__mutmut['xǁHomologyDBǁneighbors__mutmut_5'] = HomologyDB.xǁHomologyDBǁneighbors__mutmut_5 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁneighbors__mutmut['xǁHomologyDBǁneighbors__mutmut_6'] = HomologyDB.xǁHomologyDBǁneighbors__mutmut_6 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁneighbors__mutmut['xǁHomologyDBǁneighbors__mutmut_7'] = HomologyDB.xǁHomologyDBǁneighbors__mutmut_7 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁneighbors__mutmut['xǁHomologyDBǁneighbors__mutmut_8'] = HomologyDB.xǁHomologyDBǁneighbors__mutmut_8 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁneighbors__mutmut['xǁHomologyDBǁneighbors__mutmut_9'] = HomologyDB.xǁHomologyDBǁneighbors__mutmut_9 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁneighbors__mutmut['xǁHomologyDBǁneighbors__mutmut_10'] = HomologyDB.xǁHomologyDBǁneighbors__mutmut_10 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁneighbors__mutmut['xǁHomologyDBǁneighbors__mutmut_11'] = HomologyDB.xǁHomologyDBǁneighbors__mutmut_11 # type: ignore # mutmut generated

mutants_xǁHomologyDBǁcount__mutmut['_mutmut_orig'] = HomologyDB.xǁHomologyDBǁcount__mutmut_orig # type: ignore # mutmut generated
mutants_xǁHomologyDBǁcount__mutmut['xǁHomologyDBǁcount__mutmut_1'] = HomologyDB.xǁHomologyDBǁcount__mutmut_1 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁcount__mutmut['xǁHomologyDBǁcount__mutmut_2'] = HomologyDB.xǁHomologyDBǁcount__mutmut_2 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁcount__mutmut['xǁHomologyDBǁcount__mutmut_3'] = HomologyDB.xǁHomologyDBǁcount__mutmut_3 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁcount__mutmut['xǁHomologyDBǁcount__mutmut_4'] = HomologyDB.xǁHomologyDBǁcount__mutmut_4 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁcount__mutmut['xǁHomologyDBǁcount__mutmut_5'] = HomologyDB.xǁHomologyDBǁcount__mutmut_5 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁcount__mutmut['xǁHomologyDBǁcount__mutmut_6'] = HomologyDB.xǁHomologyDBǁcount__mutmut_6 # type: ignore # mutmut generated

mutants_xǁHomologyDBǁclose__mutmut['_mutmut_orig'] = HomologyDB.xǁHomologyDBǁclose__mutmut_orig # type: ignore # mutmut generated
mutants_xǁHomologyDBǁclose__mutmut['xǁHomologyDBǁclose__mutmut_1'] = HomologyDB.xǁHomologyDBǁclose__mutmut_1 # type: ignore # mutmut generated
mutants_xǁHomologyDBǁclose__mutmut['xǁHomologyDBǁclose__mutmut_2'] = HomologyDB.xǁHomologyDBǁclose__mutmut_2 # type: ignore # mutmut generated
mutants_x_demo__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_demo__mutmut)
def demo(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_orig(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_1(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = None
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_2(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(None)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_3(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = None
    if db_path:
        db.close()
    return result


def x_demo__mutmut_4(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "XXtotalXX": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_5(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "TOTAL": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_6(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "XXinfo_flow_countXX": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_7(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "INFO_FLOW_COUNT": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_8(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "XX信息论_邻居XX": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_9(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors(None),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_10(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("XX信息论XX"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_11(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "XX信息论_传递闭包(depth=2)XX": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_12(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(DEPTH=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_13(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure(None, 2),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_14(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", None),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_15(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure(2),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_16(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", ),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_17(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("XX信息论XX", 2),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_18(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 3),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_19(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "XX信息论×复杂系统_同构XX": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_20(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between(None, "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_21(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("信息论", None),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_22(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_23(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("信息论", ),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_24(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("XX信息论XX", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_25(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("信息论", "XX复杂系统XX"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_26(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "XX反馈回路类XX": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_27(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" - h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_28(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] - "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_29(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["XXparadigm_aXX"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_30(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["PARADIGM_A"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_31(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "XX×XX" + h["paradigm_b"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_32(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["XXparadigm_bXX"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_33(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["PARADIGM_B"]
                     for h in db.query_by_type("feedback_loop")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_34(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type(None)],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_35(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("XXfeedback_loopXX")],
    }
    if db_path:
        db.close()
    return result


def x_demo__mutmut_36(db_path: str | None = None) -> dict[str, Any]:
    """演示：查询 + 推理。"""
    db = HomologyDB(db_path)
    result = {
        "total": db.count(),
        "info_flow_count": len(db.query_by_type("information_flow")),
        "信息论_邻居": db.neighbors("信息论"),
        "信息论_传递闭包(depth=2)": db.transitive_closure("信息论", 2),
        "信息论×复杂系统_同构": db.query_between("信息论", "复杂系统"),
        "反馈回路类": [h["paradigm_a"] + "×" + h["paradigm_b"]
                     for h in db.query_by_type("FEEDBACK_LOOP")],
    }
    if db_path:
        db.close()
    return result

mutants_x_demo__mutmut['_mutmut_orig'] = x_demo__mutmut_orig # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_1'] = x_demo__mutmut_1 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_2'] = x_demo__mutmut_2 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_3'] = x_demo__mutmut_3 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_4'] = x_demo__mutmut_4 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_5'] = x_demo__mutmut_5 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_6'] = x_demo__mutmut_6 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_7'] = x_demo__mutmut_7 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_8'] = x_demo__mutmut_8 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_9'] = x_demo__mutmut_9 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_10'] = x_demo__mutmut_10 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_11'] = x_demo__mutmut_11 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_12'] = x_demo__mutmut_12 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_13'] = x_demo__mutmut_13 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_14'] = x_demo__mutmut_14 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_15'] = x_demo__mutmut_15 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_16'] = x_demo__mutmut_16 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_17'] = x_demo__mutmut_17 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_18'] = x_demo__mutmut_18 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_19'] = x_demo__mutmut_19 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_20'] = x_demo__mutmut_20 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_21'] = x_demo__mutmut_21 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_22'] = x_demo__mutmut_22 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_23'] = x_demo__mutmut_23 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_24'] = x_demo__mutmut_24 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_25'] = x_demo__mutmut_25 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_26'] = x_demo__mutmut_26 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_27'] = x_demo__mutmut_27 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_28'] = x_demo__mutmut_28 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_29'] = x_demo__mutmut_29 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_30'] = x_demo__mutmut_30 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_31'] = x_demo__mutmut_31 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_32'] = x_demo__mutmut_32 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_33'] = x_demo__mutmut_33 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_34'] = x_demo__mutmut_34 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_35'] = x_demo__mutmut_35 # type: ignore # mutmut generated
mutants_x_demo__mutmut['x_demo__mutmut_36'] = x_demo__mutmut_36 # type: ignore # mutmut generated


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None, help="SQLite 持久化路径")
    args = ap.parse_args()
    r = demo(args.db)
    print(f"[HOMOLOGY] 同构库: 共 {r['total']} 对 | 信息流类 {r['info_flow_count']} 对")
    print(f"  信息论邻居: {r['信息论_邻居']}")
    print(f"  信息论传递闭包(depth=2): {r['信息论_传递闭包(depth=2)']}")
    print(f"  信息论×复杂系统: {r['信息论×复杂系统_同构']}")
    print(f"  反馈回路类: {r['反馈回路类']}")
