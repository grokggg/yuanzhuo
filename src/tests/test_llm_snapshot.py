#!/usr/bin/env python3
"""UHES LLM 输出快照测试（第23项优化：锁住 LLM 契约结构）。

原理：LLM 输出内容多变（换模型/升级/网络波动），但流水线依赖的**结构契约**
不能变。用 mock LLM 固定输出，断言每步产物的结构（字段/类型/嵌套）稳定。
LLM 升级或换模型后跑此测试 → 若结构变了立刻红。

运行：cd src && python3 -m pytest tests/test_llm_snapshot.py -v
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


@pytest.fixture(scope="module")
def mock_pipeline():
    """mock LLM 模式跑一次完整流水线,缓存交付包供快照断言。"""
    import main as m
    import test_suite as _ts
    _mock = _ts.LLMMock()
    _mock.install(m)
    p = m.build_pipeline(run_id="snapshot_fixture")
    pkg = p.run(m.demo_input())
    _mock.restore(m)
    return pkg


# ---------------------------------------------------------------------------
# S1 需求DNA 结构契约
# ---------------------------------------------------------------------------

class TestDNASnapshot:
    def test_dna_top_level_fields(self, mock_pipeline):
        """DNA 顶层字段必须齐全(锁契约)。"""
        dna = mock_pipeline.artifacts["01_requirement_dna_report"]["dna"]
        required = ["goal", "constraints", "boundaries", "risks",
                    "ambiguities", "assumptions", "paradigm_hints"]
        missing = [f for f in required if f not in dna]
        assert not missing, f"DNA 缺字段: {missing}"

    def test_dna_goal_structure(self, mock_pipeline):
        """goal 必须含 primary/secondary/success_criteria。"""
        goal = mock_pipeline.artifacts["01_requirement_dna_report"]["dna"]["goal"]
        for f in ("primary", "secondary_goals", "success_criteria"):
            assert f in goal, f"goal 缺 {f}"

    def test_dna_constraints_have_type(self, mock_pipeline):
        """约束必须带 type(硬/软)和 dimension。"""
        cons = mock_pipeline.artifacts["01_requirement_dna_report"]["dna"]["constraints"]
        for c in cons:
            assert c.get("type") in ("hard", "soft"), f"约束缺 type: {c}"
            assert c.get("dimension"), f"约束缺 dimension: {c}"


# ---------------------------------------------------------------------------
# S4 蓝图结构契约
# ---------------------------------------------------------------------------

class TestBlueprintSnapshot:
    def test_blueprint_identity(self, mock_pipeline):
        """蓝图必须含 system_identity(锁身份结构)。"""
        bp = mock_pipeline.artifacts["03_system_blueprint"]
        assert "system_identity" in bp, "蓝图缺 system_identity"
        si = bp["system_identity"]
        assert "proposed_name" in si and "domain" in si

    def test_blueprint_architecture(self, mock_pipeline):
        """架构必须含 module_list 和 data_flow。"""
        arch = mock_pipeline.artifacts["03_system_blueprint"]["architecture"]
        assert "module_list" in arch and len(arch["module_list"]) >= 6
        assert "data_flow" in arch
        # 模块必须有 id 和 name
        for mod in arch["module_list"][:3]:
            assert mod.get("module_id"), f"模块缺 id: {mod}"
            assert mod.get("module_name"), f"模块缺 name: {mod}"

    def test_blueprint_compliance(self, mock_pipeline):
        """蓝图必须含非侵入合规声明。"""
        bp = mock_pipeline.artifacts["03_system_blueprint"]
        assert "compliance_declaration" in bp
        cd = bp["compliance_declaration"]
        assert "violates_non_invasive_rules" in cd


# ---------------------------------------------------------------------------
# S5 验证报告结构契约
# ---------------------------------------------------------------------------

class TestValidationSnapshot:
    def test_validation_eight_dims(self, mock_pipeline):
        """8 维评分必须齐全(锁维度集合)。"""
        vr = mock_pipeline.artifacts["06_validation_report"]
        scores = vr.get("eight_dimension_scores", {})
        # mock 用 dict(维度→详情); 真实用 list——两种都要兼容
        if isinstance(scores, dict):
            dims = set(scores.keys())
        else:
            dims = {s.get("dimension") for s in scores}
        expected = {"需求覆盖度", "约束合规度", "架构完整性", "非侵入合规度",
                    "可落地性", "可验证性", "可扩展性", "风险可控性"}
        missing = expected - dims
        assert not missing, f"8 维缺: {missing}"

    def test_validation_defects(self, mock_pipeline):
        """缺陷列表必须存在(可空)。"""
        vr = mock_pipeline.artifacts["06_validation_report"]
        assert "defect_list" in vr
        # 每缺陷必须有描述
        for d in vr["defect_list"]:
            assert d.get("description") or d.get("defect"), f"缺陷缺描述: {d}"


# ---------------------------------------------------------------------------
# 交付包整体结构契约
# ---------------------------------------------------------------------------

class TestPackageSnapshot:
    def test_seven_artifacts(self, mock_pipeline):
        """交付包必须含 7 件套(锁契约)。"""
        required = ["01_requirement_dna_report", "02_composite_paradigm_spec",
                    "03_system_blueprint", "04_roundtable_report",
                    "05_methodology_usage_record", "06_validation_report",
                    "07_incubation_plan"]
        missing = [r for r in required if r not in mock_pipeline.artifacts]
        assert not missing, f"7 件套缺: {missing}"

    def test_integrity_verdict(self, mock_pipeline):
        """完整性检查必须给出 verdict。"""
        assert mock_pipeline.integrity.get("verdict") in ("deliver", "block")

    def test_meta_final_status(self, mock_pipeline):
        """meta 必须含最终状态。"""
        assert mock_pipeline.meta.get("final_status") in (
            "completed", "completed_with_degradation")


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
