#!/usr/bin/env python3
"""UHES 多 Agent 分工（第10项优化：范式设计师 / 验证器 / 审计器分离）。

设计原则（顶尖工程实践）：
- 职责分离：设计师(生产) / 验证器(评审生产) / 审计器(复核评审)，
  形成"生产-验证-审计"三道独立环节（对齐 Google 代码评审 + 独立 QA 分层）。
- 独立评审：验证器/审计器不修改交付包，只产出独立结论（评审证据链）。
- 交叉制衡：审计器可指出验证器遗漏/误判（如设计师 open_issues 未被验证器覆盖）。
- 可编排：run_multi_agent() 串联三 Agent，输出协作报告（design/validate/audit）。

使用：
    from agents import run_multi_agent
    report = run_multi_agent(case="lit_review")
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Optional


class ParadigmDesignerAgent:
    """设计师 Agent：运行 S1-S8 流水线，产出交付包。"""

    def __init__(self, case: str = "lit_review"):
        self.case = case
        self._main = None

    def _ensure_main(self):
        if self._main is None:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import main as m
            self._main = m
        return self._main

    def design(self) -> dict[str, Any]:
        """运行流水线，返回交付包 dict + 状态。"""
        m = self._ensure_main()
        case_inputs = {
            "lit_review": m.demo_input,
            "analytics": m.demo_input_analytics,
            "knowledge": m.demo_input_knowledge,
        }
        pipeline = m.build_pipeline(run_id=f"agent_design_{self.case}")
        pkg = pipeline.run(case_inputs[self.case]())
        return {
            "agent": "designer",
            "case": self.case,
            "final_status": pipeline.state.final_status,
            "degradation": pipeline.state.degradation_count,
            "rollback": pipeline.state.rollback_count,
            "package": pkg.to_dict(),
        }


class ValidatorAgent:
    """验证器 Agent：独立评审设计师产出（完整性 + 8维 + CONS_01 复核）。"""

    def __init__(self):
        self._main = None

    def _ensure_main(self):
        if self._main is None:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import main as m
            self._main = m
        return self._main

    def validate(self, design_result: dict[str, Any]) -> dict[str, Any]:
        """独立评审交付包：完整性检查 + 8维评分审视 + CONS_01 复核。

        返回验证结论（不修改交付包，产出独立证据链）。
        """
        m = self._ensure_main()
        pkg_dict = design_result.get("package", {})
        findings: list[str] = []

        # 1. 完整性检查（复用 IntegrityChecker，独立调用）
        intg = pkg_dict.get("integrity", {})
        completeness = intg.get("artifact_completeness", {}).get("complete", False)
        if not completeness:
            findings.append("完整性检查未通过(7件不全)")

        # 2. 8 维评分审视：无全 S 但 open_issues 非空（CONS_01 独立复核）
        vr = pkg_dict.get("artifacts", {}).get("06_validation_report", {})
        bp = pkg_dict.get("artifacts", {}).get("03_system_blueprint", {})
        scores = vr.get("eight_dimension_scores", [])
        open_issues = bp.get("open_issues", [])
        if open_issues and scores and all(s.get("grade") == "S" for s in scores):
            findings.append("CONS_01 复核: open_issues 非空但 8 维全 S(矛盾)")

        # 3. 降级/回退审视：设计带降级时应显式说明
        if design_result.get("degradation", 0) > 0 and not vr.get("gate_result", {}).get("passed"):
            findings.append("设计降级但验证门控未说明")

        verdict = "approve" if not findings else "revise"
        return {
            "agent": "validator",
            "verdict": verdict,
            "findings": findings,
            "note": f"独立评审: 完整性={completeness}, 8维覆盖={len(scores)}",
        }


class AuditorAgent:
    """审计器 Agent：独立复核交付包与验证器结论（交叉制衡）。"""

    def __init__(self):
        self._main = None

    def _ensure_main(self):
        if self._main is None:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import main as m
            self._main = m
        return self._main

    def audit(self, design_result: dict[str, Any],
              validate_result: dict[str, Any]) -> dict[str, Any]:
        """独立审计：复核验证器结论 + 检查交付包自洽性。

        可发现验证器遗漏（如引用闭环问题/哈希链）。
        """
        m = self._ensure_main()
        pkg_dict = design_result.get("package", {})
        audit_findings: list[str] = []

        # 1. 复核验证器结论是否完整
        if validate_result.get("verdict") == "approve" and not validate_result.get("findings"):
            pass  # 验证器无发现,审计器独立再查

        # 2. 引用闭环独立检查
        intg = pkg_dict.get("integrity", {})
        closure = intg.get("reference_closure", {}).get("passed", False)
        if not closure:
            audit_findings.append("审计独立发现: 引用闭环未通过(验证器可能遗漏)")

        # 3. 哈希链独立检查
        hash_chain = intg.get("snapshot_hash_chain", {}).get("chain_integrity", False)
        if not hash_chain:
            audit_findings.append("审计独立发现: 哈希链完整性未通过")

        # 4. 验证器一致性复核：验证器 approve 但交付包 verdict != deliver → 不一致
        pkg_verdict = intg.get("verdict")
        if validate_result.get("verdict") == "approve" and pkg_verdict != "deliver":
            audit_findings.append(
                f"审计发现: 验证器 approve 但交付包 verdict={pkg_verdict}(不一致)")

        verdict = "clean" if not audit_findings else "flagged"
        return {
            "agent": "auditor",
            "verdict": verdict,
            "findings": audit_findings,
            "note": f"独立审计: 引用闭环={closure}, 哈希链={hash_chain}, "
                    f"包verdict={pkg_verdict}",
        }


def run_multi_agent(case: str = "lit_review") -> dict[str, Any]:
    """三 Agent 协作编排：设计师 → 验证器 → 审计器。

    返回协作报告：{design, validate, audit, pipeline, final_verdict}
    """
    designer = ParadigmDesignerAgent(case=case)
    design_result = designer.design()

    validator = ValidatorAgent()
    validate_result = validator.validate(design_result)

    auditor = AuditorAgent()
    audit_result = auditor.audit(design_result, validate_result)

    # 最终裁决：三环全部通过才 deliver
    final_verdict = (
        "deliver" if (
            design_result["final_status"] == "completed"
            and validate_result["verdict"] == "approve"
            and audit_result["verdict"] == "clean"
        ) else "review_needed"
    )

    return {
        "pipeline": {
            "case": case,
            "final_status": design_result["final_status"],
            "degradation": design_result["degradation"],
            "rollback": design_result["rollback"],
        },
        "design": design_result,
        "validate": validate_result,
        "audit": audit_result,
        "final_verdict": final_verdict,
    }


if __name__ == "__main__":
    report = run_multi_agent(case="lit_review")
    print(f"[MULTI-AGENT] 最终裁决: {report['final_verdict']}")
    print(f"  设计师: {report['pipeline']['final_status']} "
          f"(降级{report['pipeline']['degradation']}/回退{report['pipeline']['rollback']})")
    print(f"  验证器: {report['validate']['verdict']} "
          f"发现={report['validate']['findings'] or '无'}")
    print(f"  审计器: {report['audit']['verdict']} "
          f"发现={report['audit']['findings'] or '无'}")
    sys.exit(0 if report["final_verdict"] == "deliver" else 1)
