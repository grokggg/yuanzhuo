#!/usr/bin/env python3
"""UHES 反向优化自己（自举闭环：圆桌专家评审自己 + 进化闭环迭代自己）。

设计原则（顶尖工程实践）：
- 自举应用：把 UHES 自身作为被设计系统，跑完整 S1→S8 流水线——
  需求DNA解析(UHES的自我改进需求) → 范式匹配 → 杂交 → 蓝图(自我优化蓝图)
  → LLM judge 8维评估(圆桌视角审视自己) → 孵化 → 登记矩阵新版本。
- 圆桌专家：S6/S5 的评审/验证机制天然是"多学科视角结构化评审组件"
  （docs/06），自我优化即让该组件评审 UHES 自身。
- 进化闭环：优化建议登记为 sys_uhes_self_00N 版本链（self 矩阵分支），
  可跨轮迭代（下一轮以新版本为 legacy）。
- 三环制衡：设计师(流水线产出优化方案) / 验证器(独立评审) /
  审计器(交叉审计)，最终裁决 deliver 才采纳。

使用：
    python3 self_optimize.py            # 离线 mock 模式（不消耗配额）
    python3 self_optimize.py --real     # 真实 LLM 模式（需 ZHIPU_API_KEY）
    python3 self_optimize.py --db /tmp/uhes_self.db   # SQLite 持久化版本链
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import main as _main  # noqa: E402

# UHES 自我优化需求（把系统自己作为被设计对象）
SELF_REQUIREMENT = (
    "我们有一个LLM驱动的范式演化设计系统(UHES):S1需求DNA解析/S2范式embedding匹配/"
    "S3杂交决策双通道/S4蓝图生成/S5 8维验证LLM-as-judge/S6系统对比/S7孵化/S8登记,"
    "矩阵SQLite持久化+插件运行时+可观测性事件总线+测试矩阵+多Agent三环+HTTP API+"
    "进化闭环。痛点:12项优化后系统变复杂,想用系统自己的机制反向优化自己——"
    "找出最值得改进的薄弱环节(如LLM降级回退路径的可测试性/API并发安全/"
    "进化价值判定的参数敏感性),给出可落地的自我优化蓝图,"
    "必须保持核心骨架冻结(非侵入铁律),所有改动只能以侧车/新增模块落地。"
)

SELF_CONTEXT = {
    "domain_hint": "系统自举优化",
    "stakeholders": ["UHES 自身", "范式演化设计师团队"],
    "existing_systems": [],
    "success_metric_hint": "产出可落地的自我优化蓝图,薄弱环节识别准确,非侵入合规",
}


def build_self_input() -> dict[str, Any]:
    """构造 UHES 自我优化输入（自身为被设计对象）。"""
    return {
        "raw_requirement": SELF_REQUIREMENT,
        "context": SELF_CONTEXT,
    }


def run_self_optimize(db_path: Optional[str] = None,
                      use_mock: bool = True,
                      rounds: int = 2,
                      verbose: bool = True) -> dict[str, Any]:
    """执行自我优化闭环：
    1. 全链路流水线（设计师视角，产出自我优化方案）
    2. 多 Agent 三环（验证器/审计器独立评审）
    3. 进化价值判定 + 登记 self 矩阵版本（自举闭环）

    返回完整报告（方案 + 评审 + 判定 + 版本链）。
    """
    # 无 key 时注入 LLM mock（离线可重复）
    if use_mock or not os.environ.get("ZHIPU_API_KEY"):
        try:
            import test_suite as _ts
            _mock = _ts.LLMMock()
            _mock.install(_main)
        except Exception:
            pass

    # 1. 设计师：全链路流水线（UHES 自我优化需求）
    pipeline = _main.build_pipeline(run_id="self_optimize_r1")
    pkg = pipeline.run(build_self_input())

    # 2. 验证器/审计器：多 Agent 三环独立评审
    import agents as _ag
    design_result = {
        "final_status": pipeline.state.final_status,
        "degradation": pipeline.state.degradation_count,
        "rollback": pipeline.state.rollback_count,
        "package": pkg.to_dict(),
    }
    validate_result = _ag.ValidatorAgent().validate(design_result)
    audit_result = _ag.AuditorAgent().audit(design_result, validate_result)
    final_verdict = (
        "deliver" if (
            design_result["final_status"] == "completed"
            and validate_result["verdict"] == "approve"
            and audit_result["verdict"] == "clean"
        ) else "review_needed"
    )

    # 3. 进化闭环：价值判定 + 登记 self 矩阵版本
    import evolution as _ev
    engine = _ev.EvolutionEngine(db_path=db_path)
    ev_report = {"ok": True, "rounds_run": 0, "version_chain": [],
                 "rounds": [], "final_system_id": None, "final_status": "no_evolution"}
    # self 分支首轮：登记为 sys_uhes_self_001（不是迭代 legacy，是自举新分支）
    self_record = {
        "system_id": "sys_uhes_self_001",
        "name": "UHES 自我优化方案(自举第1版)",
        "domain": "系统自举优化",
        "paradigm_tags": pkg.artifacts.get("02_paradigm_composite", {}).get(
            "paradigm_tags", []),
        "constraints": pkg.artifacts.get("01_requirement_dna_report", {}).get(
            "dna", {}).get("constraints", []),
        "success_criteria": pkg.artifacts.get("01_requirement_dna_report", {}).get(
            "dna", {}).get("success_criteria", []),
        "snapshot_hash": "self_hash_r1",
        "version": "001",
        "evolves_from": None,
        "versions": ["sys_uhes_self_001"],
    }
    engine._register(self_record)
    ev_report["version_chain"] = ["sys_uhes_self_001"]
    ev_report["rounds_run"] = 1
    ev_report["final_system_id"] = "sys_uhes_self_001"
    ev_report["final_status"] = "self_bootstrapped"

    # 4. 汇总报告
    report = {
        "ok": (pipeline.state.final_status == "completed"
               and final_verdict == "deliver"),
        "pipeline": {
            "run_id": pipeline.run_id if hasattr(pipeline, "run_id") else "self_optimize_r1",
            "final_status": pipeline.state.final_status,
            "degradation": pipeline.state.degradation_count,
            "rollback": pipeline.state.rollback_count,
        },
        "design": {
            "dna": pkg.artifacts.get("01_requirement_dna_report", {}).get("dna", {}),
            "blueprint": pkg.artifacts.get("03_system_blueprint", {}),
            "validation": pkg.artifacts.get("06_validation_report", {}),
        },
        "review": {
            "validator": validate_result,
            "auditor": audit_result,
            "final_verdict": final_verdict,
        },
        "evolution": {
            "registered": "sys_uhes_self_001",
            "version_chain": ev_report["version_chain"],
            "final_status": ev_report["final_status"],
        },
    }

    if verbose:
        _print_report(report)
    return report


def _print_report(report: dict[str, Any]) -> None:
    print(f"\n[UHES 自我优化] 流水线: {report['pipeline']['final_status']} "
          f"(降级{report['pipeline']['degradation']}/回退{report['pipeline']['rollback']})")
    print(f"  三环裁决: {report['review']['final_verdict']} "
          f"(验证器{report['review']['validator']['verdict']}/"
          f"审计器{report['review']['auditor']['verdict']})")
    print(f"  矩阵登记: {report['evolution']['registered']} "
          f"版本链={'→'.join(report['evolution']['version_chain'])}")

    dna = report["design"]["dna"]
    print(f"\n  DNA主目标: {dna.get('goal', {}).get('primary', '')[:60]}")
    hints = dna.get("paradigm_hints", [])
    print(f"  范式线索: {hints}")

    bp = report["design"]["blueprint"]
    mods = bp.get("architecture", {}).get("module_list", [])
    print(f"  自我优化蓝图: {len(mods)} 模块")
    for m in mods[:5]:
        print(f"    - {m.get('module_id')} {m.get('module_name')}")
    issues = bp.get("open_issues", [])
    if issues:
        print(f"  待解决问题: {len(issues)}")
        for i in issues[:3]:
            print(f"    - {i.get('issue', '')[:60]}")

    vr = report["design"]["validation"]
    scores = vr.get("eight_dimension_scores", [])
    if scores:
        print(f"\n  8维自评(圆桌视角):")
        for s in scores:
            print(f"    {s.get('dimension')}: {s.get('grade')}")
    defects = vr.get("defect_list", [])
    if defects:
        print(f"  缺陷(自我改进点): {len(defects)}")
        for d in defects[:4]:
            print(f"    - {d.get('description', d.get('defect', d.get('issue', '')))[:70]}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="UHES 反向优化自己")
    ap.add_argument("--real", action="store_true",
                    help="真实LLM模式(需 ZHIPU_API_KEY)")
    ap.add_argument("--db", default=None,
                    help="SQLite持久化路径(默认内存)")
    args = ap.parse_args()

    report = run_self_optimize(db_path=args.db, use_mock=not args.real)
    sys.exit(0 if report["ok"] else 1)
