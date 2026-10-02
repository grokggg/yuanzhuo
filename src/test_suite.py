#!/usr/bin/env python3
"""UHES 集成测试套件（第9项优化：测试体系升级）。

设计原则（顶尖工程实践）：
- LLM mock 层：模拟智谱 API 响应（固定结构化输出），测试不依赖真实网络/配额，
  可离线/可重复。
- 测试矩阵：三案例 × 全链路 × 关键保护（降级/回退/递归/契约），每用例独立断言。
- 一键运行：run_suite() 返回 {total, passed, failed, results[]}，可机器消费。
- 与现有 --test phase2/3/4 互补：phase 场景验证具体能力，suite 验证整体回归。

使用：
    from test_suite import run_suite
    result = run_suite(use_mock=True)   # LLM mock 模式（默认）
    # 或 run_suite(use_mock=False) 真实 LLM（需 ZHIPU_API_KEY）

    CLI: python3 main.py --test suite          # mock 模式
         python3 main.py --test suite-real     # 真实 LLM（需 key）
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Callable, Optional

# ---------------------------------------------------------------------------
# LLM mock 层：模拟 _llm_parse_dna / _llm_review_hybrid / _llm_generate_blueprint /
# _llm_judge_validation 的响应（固定结构化输出，可重复）
# ---------------------------------------------------------------------------

_MOCK_DNA = {
    "dna_version": "1.0-mock",
    "goal": {
        "primary": "构建跨语言学术文献综述辅助系统,提取可溯源核心结论并生成结构化综述",
        "secondary_goals": ["降低漏检率", "统一四语术语对齐"],
        "success_criteria": ["每条结论可回溯到原文句子级锚点",
                             "综述输出含不确定性标注", "四语输入均受支持"],
        "goal_source": "user_stated",
    },
    "constraints": [
        {"type": "hard", "dimension": "technology",
         "description": "结论必须可溯源到原文句子级", "source": "user_stated"},
        {"type": "hard", "dimension": "ethics",
         "description": "严禁编造或曲解原意", "source": "user_stated"},
        {"type": "hard", "dimension": "resource",
         "description": "运行于临时沙箱,无长期数据库依赖", "source": "user_stated"},
        {"type": "hard", "dimension": "technology",
         "description": "支持中英日德四语输入", "source": "user_stated"},
    ],
    "boundaries": {
        "in_scope": ["文献检索接入", "语言对齐", "结论抽取", "综述组装", "溯源校验"],
        "out_of_scope": ["期刊影响力计算", "跨语种全文翻译产品化"],
        "unknown_zones": ["语料规模上限", "术语对齐的精度标准"],
    },
    "risks": [
        {"risk": "翻译损耗导致语义漂移", "severity": "high",
         "trigger_condition": "日德语料翻译失真时"},
        {"risk": "结论抽取断章取义", "severity": "high",
         "trigger_condition": "长句多子句结构时"},
    ],
    "ambiguities": ["术语对齐的精度标准未定义"],
    "assumptions": ["术语表可从开源词典构建"],
    "paradigm_hints": ["语言学", "信息论", "科研范式", "复杂系统"],
}

_MOCK_REVIEW = {"llm_verdict": "approve", "llm_reason": "mock: 机制可同构,公理自洽",
                "available": True}

_MOCK_BLUEPRINT = {
    "system_identity": {
        "proposed_name": "跨语言文献综述辅助系统(mock)", "domain": "学术研究",
        "paradigm_tags": ["语言学", "信息论", "科研范式", "复杂系统"],
        "blueprint_version": "0.1-mock",
    },
    "architecture": {
        "module_list": [
            {"module_id": "M1", "module_name": "文献接入", "state": "core"},
            {"module_id": "M2", "module_name": "语义单元切分", "state": "core"},
            {"module_id": "M3", "module_name": "术语对齐", "state": "core"},
            {"module_id": "M4", "module_name": "证据抽取", "state": "core"},
            {"module_id": "M5", "module_name": "证据冗余校验", "state": "core"},
            {"module_id": "M6", "module_name": "综述组装", "state": "core"},
            {"module_id": "M7", "module_name": "验证门控", "state": "core"},
            {"module_id": "M8", "module_name": "交叉对照", "state": "optional"},
        ],
        "data_flow": [
            {"from_module": f"M{i}", "to_module": f"M{i+1}",
             "data_entity": "语义单元", "direction": "forward"} for i in range(1, 7)
        ] + [{"from_module": "M8", "to_module": "M7", "data_entity": "置信度",
              "direction": "feedback"}],
        "plugin_contracts": ["M1-M8 均实现 handle_query(query, context)→result"],
        "trigger_conditions": ["用户提交综述请求"],
        "memory_constraint_plan": "核心链路常驻;M8按需加载",
    },
    "compliance_declaration": {
        "violates_non_invasive_rules": False,
        "rules_checked": ["核心骨架冻结", "双轨隔离", "零共享资源", "内存60%", "动态加载"],
        "notes": "模块均为插件侧车,不触碰主本体",
    },
    "open_issues": [
        {"issue": "日语语义单元切分语料标注不足", "impact": "M2日语文档精度低",
         "suggested_resolution": "阶段2补充日语文法规则集"},
        {"issue": "冗余校验的独立锚点判定标准未量化", "impact": "M5判定依赖规则",
         "suggested_resolution": "孵化阶段1启发式规则"},
    ],
}

_MOCK_JUDGE = {
    "scores": {
        "需求覆盖度": {"grade": "A", "evidence": "mock覆盖主目标",
                     "issues": []},
        "约束合规度": {"grade": "S", "evidence": "mock约束满足", "issues": []},
        "架构完整性": {"grade": "A", "evidence": "mock架构完整", "issues": []},
        "非侵入合规度": {"grade": "S", "evidence": "mock非侵入", "issues": []},
        "可落地性": {"grade": "B", "evidence": "mock日语语料不足",
                    "issues": ["日语语料标注不足"]},
        "可验证性": {"grade": "S", "evidence": "mock可验证", "issues": []},
        "可扩展性": {"grade": "A", "evidence": "mock可扩展", "issues": []},
        "风险可控性": {"grade": "B", "evidence": "mock风险有缓解",
                      "issues": ["冗余校验标准未量化"]},
    },
    "llm_available": True,
    "llm_note": "mock judge",
}


class LLMMock:
    """LLM mock：替换 main 的 4 个 LLM 函数为固定响应（可重复、离线）。"""

    def install(self, main_mod) -> None:
        """把 main_mod 的 LLM 函数替换为 mock 版（可恢复）。"""
        self._originals = {
            "_llm_parse_dna": main_mod._llm_parse_dna,
            "_llm_review_hybrid": main_mod._llm_review_hybrid,
            "_llm_generate_blueprint": main_mod._llm_generate_blueprint,
            "_llm_judge_validation": main_mod._llm_judge_validation,
        }
        main_mod._llm_parse_dna = self._mock_parse
        main_mod._llm_review_hybrid = self._mock_review
        main_mod._llm_generate_blueprint = self._mock_blueprint
        main_mod._llm_judge_validation = self._mock_judge

    def restore(self, main_mod) -> None:
        """恢复原始 LLM 函数。"""
        for name, fn in getattr(self, "_originals", {}).items():
            setattr(main_mod, name, fn)

    def _mock_parse(self, raw, context):
        # mock 解析：主目标取自 raw（自定义需求也能离线解析出真实目标）
        dna = json.loads(json.dumps(_MOCK_DNA))
        if raw:
            # 从 raw 提取主目标（首句截断）+ 领域线索
            first_line = raw.strip().split("\n")[0][:40]
            dna["goal"]["primary"] = first_line
            hint = context.get("domain_hint", "") if isinstance(context, dict) else ""
            if hint:
                dna["paradigm_hints"] = [hint, "信息论", "系统论", "数据驱动"]
        return {"dna": dna, "llm_available": True,
                "llm_note": "mock 解析(raw 驱动)"}

    def _mock_review(self, composite_name, sources, axioms, goal):
        return dict(_MOCK_REVIEW)

    def _mock_blueprint(self, goal, domain, tags, hybrid_name):
        return {"blueprint": json.loads(json.dumps(_MOCK_BLUEPRINT)),
                "llm_available": True, "llm_note": "mock 蓝图"}

    def _mock_judge(self, goal, blueprint):
        return {"scores": json.loads(json.dumps(_MOCK_JUDGE["scores"])),
                "llm_available": True, "llm_note": "mock judge"}


# ---------------------------------------------------------------------------
# 测试矩阵：三案例 × 全链路 × 关键保护
# ---------------------------------------------------------------------------

def run_suite(use_mock: bool = True) -> dict[str, Any]:
    """运行集成测试矩阵。

    用例：
      1. 三案例全链路 deliver（lit_review/analytics/knowledge）
      2. 完整性检查全 True（7件/必填/引用闭环/CONS_01/哈希链）
      3. 保护机制：phase4 递归深度保护（H/I/J）
      4. 插件契约：PluginRuntime 加载合规插件 + 拒绝不合规
      5. 持久化：MatrixStore 写读/版本链
      6. 可观测性：ObservabilityBus 事件/span/指标
    """
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import main as _main

    mock = LLMMock()
    if use_mock:
        mock.install(_main)

    results: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: str = "") -> None:
        results.append({"name": name, "passed": bool(passed), "detail": detail})
        print(f"  {'✓' if passed else '✗'} {name}" + (f" | {detail}" if detail else ""))

    try:
        # 1. 三案例全链路
        for case in ["lit_review", "analytics", "knowledge"]:
            pipeline = _main.build_pipeline(run_id=f"suite_{case}")
            pkg = pipeline.run(_main.demo_input() if case == "lit_review"
                               else _main.demo_input_analytics() if case == "analytics"
                               else _main.demo_input_knowledge())
            check(f"{case} 全链路 deliver",
                  pkg.integrity.get("verdict") == "deliver",
                  f"状态={pipeline.state.final_status}")
            check(f"{case} 完整性全True",
                  all((
                      pkg.integrity["artifact_completeness"]["complete"],
                      pkg.integrity["required_field_check"]["passed"],
                      pkg.integrity["reference_closure"]["passed"],
                      pkg.integrity["cross_artifact_consistency"]["passed"],
                      pkg.integrity["snapshot_hash_chain"]["chain_integrity"],
                  )))

        # 2. 保护机制：phase4 递归深度（mock 下应仍触发 H/I/J）
        rc = _main._test_phase4()
        check("phase4 递归保护(H/I/J)", rc == 0)

        # 3. 插件契约
        import plugin_runtime as _pr
        rt = _pr.PluginRuntime(plugin_dir=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "plugins"))
        loaded = rt.load_dir()
        check("插件运行时加载", "step_s1_llm" in loaded,
              f"加载={loaded}")
        try:
            rt.load("__nope__")
            contract_rejected = False
        except _pr.PluginContractError:
            contract_rejected = True
        check("插件契约拒绝不合规", contract_rejected)

        # 4. 持久化：MatrixStore 写读/版本链
        import tempfile
        import matrix_store as _ms
        db = os.path.join(tempfile.mkdtemp(), "suite_matrix.db")
        store = _ms.MatrixStore(db)
        store.register({"system_id": "sys_suite_001", "name": "suite系统",
                        "version": "001", "evolves_from": None,
                        "versions": ["sys_suite_001"]})
        rec = store.load("sys_suite_001")
        check("矩阵持久化写读", rec is not None and rec["system_id"] == "sys_suite_001")
        os.unlink(db)

        # 5. 可观测性
        import observability as _ob
        bus = _ob.ObservabilityBus(run_id="suite_obs")
        with bus.span("root"):
            bus.record_event("custom", {"x": 1})
        metrics = bus.export_metrics()
        check("可观测性事件总线",
              metrics["total_steps"] == 1 and len(bus.export_jsonl().splitlines()) >= 3)
    finally:
        mock.restore(_main)

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    return {"total": total, "passed": passed, "failed": total - passed,
            "results": results}


if __name__ == "__main__":
    res = run_suite(use_mock=True)
    print(f"\n[TEST-SUITE] 结果: {res['passed']}/{res['total']} 通过")
    sys.exit(0 if res["failed"] == 0 else 1)
