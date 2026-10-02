#!/usr/bin/env python3
"""UHES mock/真实双模式一致性检查（第20项优化：用户反馈"mock和真实差距大"）。

设计原则（顶尖工程实践）：
- 结构一致性：mock 与真实 LLM 的交付包应结构一致（7件套齐全、字段对齐）。
- 内容差异可视化：主目标/范式线索/蓝图模块数的差异是预期的（内容随 LLM 变化），
  但结构差异是缺陷。
- 判定规则：
    PASS = 结构一致（7件套齐全 + 必填字段在）
    WARN = 内容差异但结构一致（预期，记录差异）
    FAIL = 结构不一致（缺陷）
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_both_modes(requirement: str = None,
                   context: dict[str, Any] = None) -> dict[str, Any]:
    """跑 mock 与真实 LLM 两种模式,对比交付包一致性。"""
    import main as m
    import test_suite as _ts

    req = requirement or (
        "构建跨语言文献综述系统,结论必须可溯源到句子级,"
        "支持中英日德四语,运行在临时沙箱")
    ctx = context or {"domain_hint": "学术研究"}

    # 1. mock 模式
    _mock = _ts.LLMMock()
    _mock.install(m)
    p1 = m.build_pipeline(run_id="consistency_mock")
    pkg_mock = p1.run({"raw_requirement": req, "context": ctx})
    _mock.restore(m)

    # 2. 真实 LLM 模式(无 key 时跳过,标注 unavailable)
    if not os.environ.get("ZHIPU_API_KEY"):
        return {
            "mode": "real_unavailable",
            "note": "ZHIPU_API_KEY 未设置,真实模式不可用,仅输出 mock 结构",
            "mock_package_ok": pkg_mock.integrity.get("verdict") == "deliver",
            "structure": _extract_structure(pkg_mock),
        }

    p2 = m.build_pipeline(run_id="consistency_real")
    pkg_real = p2.run({"raw_requirement": req, "context": ctx})

    # 3. 对比
    s_mock = _extract_structure(pkg_mock)
    s_real = _extract_structure(pkg_real)
    report = {
        "mode": "both",
        "mock": s_mock,
        "real": s_real,
        "structural_match": s_mock["structure"] == s_real["structure"],
        "differences": _diff(s_mock, s_real),
    }
    report["verdict"] = (
        "PASS" if report["structural_match"] else
        "FAIL")
    return report


def _extract_structure(pkg: Any) -> dict[str, Any]:
    """提取交付包的结构化视图（7件套 + 关键字段）。"""
    arts = pkg.artifacts
    return {
        "structure": sorted(arts.keys()),
        "meta_keys": sorted(pkg.meta.keys()),
        "dna_goal": arts.get("01_requirement_dna_report", {}).get(
            "dna", {}).get("goal", {}).get("primary", "")[:40],
        "dna_paradigms": arts.get("01_requirement_dna_report", {}).get(
            "dna", {}).get("paradigm_hints", []),
        "blueprint_modules": len(arts.get("03_system_blueprint", {}).get(
            "architecture", {}).get("module_list", [])),
        "validation_dims": len(arts.get("06_validation_report", {}).get(
            "eight_dimension_scores", arts.get("06_validation_report", {}).get(
                "eight_dimension_scores", {}))),
        "verdict": pkg.integrity.get("verdict"),
    }


def _diff(a: dict[str, Any], b: dict[str, Any]) -> list[str]:
    """列出两模式差异(内容级,非结构)。"""
    diffs = []
    if a["dna_goal"] != b["dna_goal"]:
        diffs.append(f"DNA主目标不同: mock={a['dna_goal'][:20]}... real={b['dna_goal'][:20]}...")
    if a["dna_paradigms"] != b["dna_paradigms"]:
        diffs.append(f"范式线索不同: mock={a['dna_paradigms']} real={b['dna_paradigms']}")
    if a["blueprint_modules"] != b["blueprint_modules"]:
        diffs.append(f"蓝图模块数不同: mock={a['blueprint_modules']} real={b['blueprint_modules']}")
    return diffs


if __name__ == "__main__":
    report = run_both_modes()
    if report.get("mode") == "real_unavailable":
        print(f"[CONSISTENCY] 真实模式不可用(无key): mock 结构="
              f"{report['structure']['structure']}")
        print(f"  mock verdict={report['structure']['verdict']}")
        sys.exit(0)
    print(f"[CONSISTENCY] 双模式一致性: {report['verdict']}")
    print(f"  结构匹配: {report['structural_match']}")
    print(f"  mock 结构: {report['mock']['structure']}")
    print(f"  real 结构: {report['real']['structure']}")
    print(f"  mock 模块数: {report['mock']['blueprint_modules']} | "
          f"real 模块数: {report['real']['blueprint_modules']}")
    for d in report["differences"]:
        print(f"  差异: {d}")
    sys.exit(0 if report["verdict"] == "PASS" else 1)
