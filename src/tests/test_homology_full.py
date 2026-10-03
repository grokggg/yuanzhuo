#!/usr/bin/env python3
"""同构全量落地测试（真实化清单第5步）。

锁契约：
- 全量生成 ≥150 对（种子 + 模板生成）
- 7 大机制类型全覆盖
- 检索/邻居/传递闭包可用
- 生成条目诚实标注（source 含"模板生成"）
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from homology import HomologyDB  # noqa: E402


class TestHomologyFull(unittest.TestCase):
    def setUp(self):
        self.db = HomologyDB()

    def test_full_generation_count(self):
        """全量同构 ≥150 对（15 种子 + 模板生成）。"""
        self.assertGreaterEqual(len(self.db._memory), 150)

    def test_seven_mechanism_types(self):
        """7 大机制类型全覆盖。"""
        types = {h["mechanism_type"] for h in self.db._memory}
        expected = {
            "information_flow", "feedback_loop", "state_transition",
            "constraint_optimization", "hierarchy_emergence",
            "selection_adaptation", "network_structure",
        }
        self.assertEqual(types, expected)

    def test_generated_entries_are_honest(self):
        """生成条目诚实标注（source 含"模板生成"）。"""
        gen = [h for h in self.db._memory if "模板生成" in h.get("source", "")]
        self.assertGreater(len(gen), 100, "模板生成条目应 >100")
        # 种子 15 对保留（非模板生成）
        seeds = [h for h in self.db._memory if "模板生成" not in h.get("source", "")]
        self.assertGreaterEqual(len(seeds), 15)

    def test_query_between_works(self):
        """两范式间检索（含种子与生成）。"""
        r = self.db.query_between("信息论", "语言学")
        self.assertIsNotNone(r)
        r2 = self.db.query_between("信息论", "认知科学")
        self.assertIsNotNone(r2)  # 生成条目可查

    def test_neighbors_works(self):
        """邻居发现。"""
        n = self.db.neighbors("信息论")
        self.assertGreater(len(n), 3)

    def test_sqlite_persist_full(self):
        """SQLite 落库全量 + 跨进程。"""
        tmp = tempfile.mktemp(suffix=".db")
        try:
            db = HomologyDB(tmp)
            import sqlite3
            conn = sqlite3.connect(tmp)
            count = conn.execute("SELECT COUNT(*) FROM homologies").fetchone()[0]
            conn.close()
            self.assertGreaterEqual(count, 150)
        finally:
            os.unlink(tmp)

    def test_transitive_closure_works(self):
        """传递闭包推理。"""
        reach = self.db.transitive_closure("信息论", depth=2)
        self.assertGreater(len(reach), 3)


if __name__ == "__main__":
    unittest.main()
