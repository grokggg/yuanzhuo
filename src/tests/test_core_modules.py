#!/usr/bin/env python3
"""UHES 核心模块单元测试（第22项优化：测试金字塔底座）。

覆盖 6 个核心模块 × 3-5 用例 = 边界 / 降级 / 异常，测真实行为。

运行：cd src && python3 -m pytest tests/ -v
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


# ---------------------------------------------------------------------------
# 1. llm_gateway：多通道 + 缓存 + 降级
# ---------------------------------------------------------------------------

class TestLLMGateway:
    def test_no_key_raises(self):
        """无 key 时 chat_json 应抛异常(不可静默失败)。"""
        import llm_gateway as lg
        gw = lg.LLMGateway()
        old = os.environ.get("ZHIPU_API_KEY")
        os.environ.pop("ZHIPU_API_KEY", None)
        try:
            with pytest.raises(RuntimeError):
                gw.chat_json("test")
        finally:
            if old:
                os.environ["ZHIPU_API_KEY"] = old

    def test_available_false_no_key(self):
        """无 key 时 available() 应为 False。"""
        import llm_gateway as lg
        gw = lg.LLMGateway()
        old = os.environ.get("ZHIPU_API_KEY")
        os.environ.pop("ZHIPU_API_KEY", None)
        try:
            assert gw.available() is False
        finally:
            if old:
                os.environ["ZHIPU_API_KEY"] = old

    def test_cache_key_deterministic(self):
        """同 prompt 的缓存键应确定且唯一。"""
        import llm_gateway as lg
        gw = lg.LLMGateway()
        k1 = gw._cache_key("m", "hello", 100)
        k2 = gw._cache_key("m", "hello", 100)
        k3 = gw._cache_key("m", "hello", 200)
        assert k1 == k2
        assert k1 != k3

    def test_cache_bounded(self):
        """缓存应有界: 超过200条时 _cached_or 应淘汰最旧。"""
        import llm_gateway as lg
        gw = lg.LLMGateway(use_cache=True)
        # 直接塞 250 条(模拟大量调用)
        for i in range(250):
            gw._cache[f"key{i}"] = {"v": i}
        # 再调用 _cached_or 触发淘汰检查
        gw._cached_or("new_key", lambda: {"ok": True})
        assert len(gw._cache) <= 200


# ---------------------------------------------------------------------------
# 2. homology：同构库 检索/推理/持久化
# ---------------------------------------------------------------------------

class TestHomology:
    def test_seed_count(self):
        """种子同构对应存在。"""
        import homology as h
        db = h.HomologyDB()
        assert db.count() >= 10
        db.close() if db._conn else None

    def test_query_by_paradigm(self):
        """按范式查邻居应返回相关同构。"""
        import homology as h
        db = h.HomologyDB()
        neighbors = db.neighbors("信息论")
        assert "语言学" in neighbors  # 种子: 信息论×语言学
        db.close() if db._conn else None

    def test_transitive_closure(self):
        """传递闭包应返回可达范式(非空)。"""
        import homology as h
        db = h.HomologyDB()
        closure = db.transitive_closure("信息论", depth=2)
        assert len(closure) >= 3
        db.close() if db._conn else None

    def test_sqlite_persist(self):
        """SQLite 持久化: 写入后跨实例可读。"""
        import homology as h
        tmp = os.path.join(tempfile.mkdtemp(), "hom.db")
        db = h.HomologyDB(tmp)
        db.register({"paradigm_a": "测试A", "paradigm_b": "测试B",
                     "mechanism_type": "feedback_loop", "depth": "deep",
                     "source": "测试", "evidence": "测试"})
        db.close()
        db2 = h.HomologyDB(tmp)
        found = db2.query_between("测试A", "测试B")
        assert found is not None
        db2.close()


# ---------------------------------------------------------------------------
# 3. experts：专家库 筛选/降级
# ---------------------------------------------------------------------------

class TestExperts:
    def test_panel_42_experts(self):
        """专家库应有 42 位。"""
        import experts as e
        panel = e.ExpertPanel()
        assert len(panel.experts) == 42

    def test_select_subset(self):
        """按范式线索筛选子集应非空且含匹配专家。"""
        import experts as e
        panel = e.ExpertPanel()
        subset = panel.select_subset(["信息论", "语言学"], max_n=4)
        assert len(subset) >= 2
        names = [x["name"] for x in subset]
        assert "信息论" in names or "语言学" in names

    def test_mock_deliberate_fallback(self):
        """无 key 时专家推演应降级 mock(不抛异常)。"""
        import experts as e
        panel = e.ExpertPanel()
        expert = panel.by_id["E16"]  # 信息论
        result = panel.expert_deliberate(expert, "测试需求", ["信息论"],
                                         "设计摘要", use_mock=True)
        assert result["expert_id"] == "E16"
        assert result["llm_available"] is False  # mock 降级


# ---------------------------------------------------------------------------
# 4. matrix_store：持久化 写读/版本链
# ---------------------------------------------------------------------------

class TestMatrixStore:
    def test_register_load(self):
        """登记后应能读回(含 payload)。"""
        import matrix_store as ms
        tmp = os.path.join(tempfile.mkdtemp(), "mat.db")
        store = ms.MatrixStore(tmp)
        store.register({"system_id": "sys_test_001", "name": "测试系统",
                        "version": "001", "evolves_from": None,
                        "versions": ["sys_test_001"]})
        rec = store.load("sys_test_001")
        assert rec is not None
        assert rec["system_id"] == "sys_test_001"
        store.close()

    def test_version_chain(self):
        """版本链字段应保留。"""
        import matrix_store as ms
        tmp = os.path.join(tempfile.mkdtemp(), "mat2.db")
        store = ms.MatrixStore(tmp)
        store.register({"system_id": "sys_v_002", "name": "V2",
                        "version": "002", "evolves_from": "sys_v_001",
                        "versions": ["sys_v_001", "sys_v_002"]})
        rec = store.load("sys_v_002")
        assert rec["evolves_from"] == "sys_v_001"
        assert "sys_v_002" in rec["versions"]
        store.close()

    def test_load_missing(self):
        """读不存在的系统应返回 None(不抛异常)。"""
        import matrix_store as ms
        tmp = os.path.join(tempfile.mkdtemp(), "mat3.db")
        store = ms.MatrixStore(tmp)
        assert store.load("sys_nonexistent") is None
        store.close()


# ---------------------------------------------------------------------------
# 5. paradigms：范式库 embedding 匹配
# ---------------------------------------------------------------------------

class TestParadigms:
    def test_catalog_size(self):
        """范式库应有 29+ 组(含网络科学补充)。"""
        import paradigms as p
        assert len(p.PARADIGM_CATALOG) >= 29

    def test_embedding_match(self):
        """embedding 匹配应返回结果(非空或 low 置信)。"""
        import paradigms as p
        r = p.embedding_match({"paradigm_hints": ["信息论"],
                               "goal": {"primary": "数据编码系统"}})
        assert "matched_paradigms" in r
        assert r["match_confidence"] in ("high", "medium", "low")

    def test_cosine_similarity(self):
        """余弦相似度边界: 相同≈1, 正交=0。"""
        import paradigms as p
        v = {"a": 1.0, "b": 2.0}
        assert abs(p.cosine_similarity(v, v) - 1.0) < 1e-9  # 浮点容差
        assert p.cosine_similarity({"x": 1.0}, {"y": 1.0}) == 0.0


# ---------------------------------------------------------------------------
# 6. observability：事件总线 span/指标
# ---------------------------------------------------------------------------

class TestObservability:
    def test_span_tree(self):
        """span 嵌套应生成树。"""
        import observability as ob
        bus = ob.ObservabilityBus(run_id="ut")
        with bus.span("root"):
            with bus.span("child"):
                pass
        tree = bus.export_span_tree()
        assert "root" in tree
        assert "child" in tree

    def test_metrics(self):
        """指标应含总步数与事件数。"""
        import observability as ob
        bus = ob.ObservabilityBus(run_id="ut2")
        with bus.span("s1"):
            bus.record_event(ob.EVENT_DEGRADE, {"step": "S1"})
        m = bus.export_metrics()
        assert m["total_steps"] == 1
        assert m["degradation_count"] >= 1

    def test_jsonl_export(self):
        """JSONL 导出应含事件行。"""
        import observability as ob
        bus = ob.ObservabilityBus(run_id="ut3")
        bus.record_event("custom", {"x": 1})
        lines = bus.export_jsonl().splitlines()
        assert len(lines) >= 2  # span 开始+事件


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
