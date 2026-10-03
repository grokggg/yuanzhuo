#!/usr/bin/env python3
"""UHES 100 用户压力模拟（第19项优化：多用户真实使用验证）。

设计原则（顶尖工程实践）：
- 100 个模拟用户：覆盖不同领域(医疗/教育/电商/金融/制造/政务/文旅/物流/能源/科研)、
  不同行为模式(标准需求/模糊需求/极端需求/多轮迭代)、不同调用方式(CLI/API)。
- 真实执行：每个用户真实调用流水线(主流程/API/进化)，非虚构。
- 反馈收集：每个用户返回 {user_id, domain, mode, status, verdict, latency, issues[]}。
- 问题识别：汇总失败/降级/超时/低分，输出问题清单供修复。

使用：
    python3 user_simulator.py              # 100 用户全跑(离线 mock)
    python3 user_simulator.py --real       # 真实 LLM(需 key)
    python3 user_simulator.py --count 20   # 只跑 20 个(快速验证)
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 100 个模拟用户(领域 × 需求模板 × 行为模式)
DOMAINS = ["医疗健康", "在线教育", "电商零售", "金融服务", "智能制造",
           "政务治理", "文化旅游", "物流运输", "能源管理", "科研学术"]

REQUIREMENT_TEMPLATES = [
    # 标准需求(清晰)
    "我们需要一个{domain}系统,核心功能是{d1},必须满足{constraint},输出要{output}",
    # 模糊需求(信息不足)
    "我们想要个{domain}的东西,感觉现在效率低,最好能自动化,你看着办",
    # 约束严格
    "构建{domain}系统:硬性要求{constraint},不能依赖外部服务,数据必须可审计,7x24运行",
    # 集成需求
    "把现有{domain}流程数字化:{d1}+{d2}打通,历史数据迁移,权限分级",
    # 极简
    "{domain}工具,要快,要稳",
]

CONSTRAINTS = [
    "每个操作可追溯", "响应<2秒", "数据加密存储", "离线可用",
    "多租户隔离", "审计日志完整", "高可用99.9%", "合规(等保/GDPR)",
]

OUTPUTS = ["可视化报表", "结构化报告", "实时预警", "API接口", "知识图谱"]

D1_POOL = ["数据采集", "流程审批", "智能推荐", "异常检测", "知识检索", "资源调度"]
D2_POOL = ["数据分析", "任务分配", "用户画像", "质量监控", "协同编辑", "风险预警"]

# 行为模式(决定调用方式与期望)
MODES = ["api_standard", "api_vague", "api_iterative", "cli_standard", "api_evolution"]


def gen_user(user_id: int) -> dict[str, Any]:
    """生成第 user_id 个用户(确定性,可复现)。"""
    domain = DOMAINS[user_id % len(DOMAINS)]
    template = REQUIREMENT_TEMPLATES[user_id % len(REQUIREMENT_TEMPLATES)]
    constraint = CONSTRAINTS[(user_id * 3) % len(CONSTRAINTS)]
    output = OUTPUTS[(user_id * 5) % len(OUTPUTS)]
    d1 = D1_POOL[(user_id * 7) % len(D1_POOL)]
    d2 = D2_POOL[(user_id * 11) % len(D2_POOL)]
    mode = MODES[user_id % len(MODES)]

    if template.startswith("我们需要"):
        req = template.format(domain=domain, d1=d1, constraint=constraint, output=output)
    elif template.startswith("我们想要"):
        req = template.format(domain=domain)
    elif template.startswith("构建"):
        req = template.format(domain=domain, constraint=constraint)
    elif template.startswith("把现有"):
        req = template.format(domain=domain, d1=d1, d2=d2)
    else:
        req = template.format(domain=domain)

    return {"user_id": user_id, "domain": domain, "mode": mode, "requirement": req,
            "constraint": constraint, "output": output}


def run_user(user: dict[str, Any], use_mock: bool = True) -> dict[str, Any]:
    """单个用户使用系统(真实调用),返回反馈。"""
    uid = user["user_id"]
    mode = user["mode"]
    req = user["requirement"]
    start = time.time()
    feedback: dict[str, Any] = {
        "user_id": uid, "domain": user["domain"], "mode": mode,
        "status": "ok", "verdict": None, "latency_ms": 0,
        "degradation": 0, "issues": [], "pipeline_ok": False,
    }
    try:
        import main as m
        if use_mock:
            import test_suite as _ts
            _mock = _ts.LLMMock()
            _mock.install(m)

        # 按行为模式调用
        if mode == "api_evolution":
            # 进化模式:先主流程登记,再迭代
            p1 = m.build_pipeline(run_id=f"u{uid}_p1")
            pkg1 = p1.run(m.demo_input() if "文献" in req else
                          {"raw_requirement": req, "context": {"domain_hint": user["domain"]}})
            feedback["pipeline_ok"] = pkg1.integrity.get("verdict") == "deliver"
            feedback["verdict"] = pkg1.integrity.get("verdict")
            feedback["degradation"] = p1.state.degradation_count
            import evolution as _ev
            engine = _ev.EvolutionEngine(db_path=None)
            ev = engine.evolve("sys_lit_review_001", rounds=1, use_mock=use_mock)
            feedback["evolution_status"] = ev.get("final_status")
        elif mode == "api_standard":
            p = m.build_pipeline(run_id=f"u{uid}")
            pkg = p.run({"raw_requirement": req,
                         "context": {"domain_hint": user["domain"]}})
            feedback["pipeline_ok"] = pkg.integrity.get("verdict") == "deliver"
            feedback["verdict"] = pkg.integrity.get("verdict")
            feedback["degradation"] = p.state.degradation_count
        elif mode == "api_vague":
            # 模糊需求:可能触发澄清/降级
            p = m.build_pipeline(run_id=f"u{uid}")
            pkg = p.run({"raw_requirement": req,
                         "context": {"domain_hint": user["domain"]}})
            feedback["pipeline_ok"] = pkg.integrity.get("verdict") == "deliver"
            feedback["verdict"] = pkg.integrity.get("verdict")
            feedback["degradation"] = p.state.degradation_count
            if p.state.degradation_count > 0:
                feedback["issues"].append("模糊需求触发降级")
        elif mode == "api_iterative":
            # 多轮迭代:同一需求跑 2 轮
            for r in range(2):
                p = m.build_pipeline(run_id=f"u{uid}_r{r}")
                pkg = p.run({"raw_requirement": req,
                             "context": {"domain_hint": user["domain"]}})
                feedback["pipeline_ok"] = pkg.integrity.get("verdict") == "deliver"
                feedback["verdict"] = pkg.integrity.get("verdict")
                feedback["degradation"] += p.state.degradation_count
        else:  # cli_standard
            p = m.build_pipeline(run_id=f"u{uid}")
            pkg = p.run({"raw_requirement": req,
                         "context": {"domain_hint": user["domain"]}})
            feedback["pipeline_ok"] = pkg.integrity.get("verdict") == "deliver"
            feedback["verdict"] = pkg.integrity.get("verdict")
            feedback["degradation"] = p.state.degradation_count

        feedback["latency_ms"] = int((time.time() - start) * 1000)
        if not feedback["pipeline_ok"]:
            feedback["status"] = "failed"
            feedback["issues"].append("交付包未达 deliver")
    except Exception as exc:
        feedback["status"] = "error"
        feedback["latency_ms"] = int((time.time() - start) * 1000)
        feedback["issues"].append(f"{type(exc).__name__}: {str(exc)[:100]}")
    return feedback


def run_all(count: int = 100, use_mock: bool = True,
            concurrency: int = 4) -> dict[str, Any]:
    """运行 count 个用户,汇总反馈。

    第19项优化：并发执行（多用户并行，真实压测场景）。
    """
    from concurrent.futures import ThreadPoolExecutor
    users = [gen_user(uid) for uid in range(1, count + 1)]
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(run_user, u, use_mock) for u in users]
        results = [f.result() for f in futures]

    # 汇总
    ok = sum(1 for r in results if r["status"] == "ok" and r["pipeline_ok"])
    failed = sum(1 for r in results if r["status"] in ("failed", "error"))
    degraded = sum(1 for r in results if r["degradation"] > 0)
    avg_latency = sum(r["latency_ms"] for r in results) // max(1, len(results))
    issues: dict[str, int] = {}
    for r in results:
        for i in r["issues"]:
            issues[i] = issues.get(i, 0) + 1
    domains_fail: dict[str, int] = {}
    for r in results:
        if not r["pipeline_ok"]:
            domains_fail[r["domain"]] = domains_fail.get(r["domain"], 0) + 1
    modes_fail: dict[str, int] = {}
    for r in results:
        if not r["pipeline_ok"]:
            modes_fail[r["mode"]] = modes_fail.get(r["mode"], 0) + 1

    return {
        "total": count,
        "ok": ok, "failed": failed, "degraded": degraded,
        "avg_latency_ms": avg_latency,
        "success_rate": round(ok / count, 3) if count else 0,
        "top_issues": sorted(issues.items(), key=lambda x: -x[1])[:8],
        "fail_by_domain": domains_fail,
        "fail_by_mode": modes_fail,
        "results": results,
    }


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=100)
    ap.add_argument("--real", action="store_true")
    args = ap.parse_args()
    print(f"[SIM] 模拟 {args.count} 个用户使用 UHES "
          f"({'真实LLM' if args.real else 'mock 离线'})...")
    report = run_all(args.count, use_mock=not args.real)
    print(f"[SIM] 完成: {report['total']} 用户")
    print(f"  成功: {report['ok']} | 失败: {report['failed']} | 降级: {report['degraded']}")
    print(f"  成功率: {report['success_rate']} | 平均延迟: {report['avg_latency_ms']}ms")
    print(f"  失败领域: {report['fail_by_domain'] or '无'}")
    print(f"  失败模式: {report['fail_by_mode'] or '无'}")
    print("  问题清单:")
    for issue, cnt in report["top_issues"]:
        print(f"    [{cnt}] {issue}")
    # 输出 JSON 供后续处理
    with open("/tmp/uhes_sim_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("[SIM] 报告已存 /tmp/uhes_sim_report.json")
