#!/usr/bin/env python3
"""示例插件：step_s1_llm —— 需求DNA解析（LLM 版）。

演示第7项优化（插件运行时真实化）：
- 独立模块，暴露 PLUGIN_META（契约）+ handle(state)（执行接口）。
- 加载器动态 import + 契约校验 + 资源预算。
- handle 在隔离命名空间执行，不触碰引擎主体（非侵入铁律）。

契约：
    PLUGIN_META = {name, step, resource_budget, description}
    handle(state) -> None   # 修改 state.artifacts[step]，与内置侧车同接口
"""

PLUGIN_META = {
    "name": "step_s1_llm",
    "step": "S1",
    "resource_budget": 10,  # 概念资源预算（≤100 契约上限）
    "description": "LLM 需求DNA解析（智谱GLM，key 从环境变量读取）",
}


def handle(state) -> None:
    """LLM 版 S1 解析：调用智谱 GLM 解析需求为 REQUIREMENT_DNA。

    与内置 step_s1_parse 同接口（state.artifacts["S1"]），
    隔离命名空间内执行，仅依赖标准库 + 环境变量 key。
    """
    import json
    import os
    import urllib.request

    raw = state.artifacts.get("__input", {}).get("raw_requirement", "")
    key = os.environ.get("ZHIPU_API_KEY", "")
    if not key:
        # 无 key：降级为简单占位解析（插件自身处理，不抛错）
        state.artifacts["S1"] = {
            "dna": {
                "dna_version": "1.0-plugin-no-key",
                "goal": {"primary": raw[:30], "secondary_goals": [],
                         "success_criteria": [], "goal_source": "user_stated"},
                "constraints": [], "boundaries": {"in_scope": [], "out_of_scope": [],
                                                  "unknown_zones": []},
                "risks": [], "ambiguities": [], "assumptions": [],
                "paradigm_hints": [],
            },
            "parse_log": {"parse_note": "插件降级(无key)", "clarification_rounds": 0,
                          "text_strategy": None, "clarify_template": None},
        }
        return

    prompt = (
        "你是需求分析专家。把需求解析为REQUIREMENT_DNA JSON:"
        "{\"goal\":{\"primary\":\"主目标\",\"secondary_goals\":[\"次目标\"],\"success_criteria\":[\"成功标准\"]},"
        "\"constraints\":[{\"type\":\"hard|soft\",\"dimension\":\"technology\",\"description\":\"约束\"}],"
        "\"boundaries\":{\"in_scope\":[\"范围内\"],\"out_of_scope\":[\"范围外\"],\"unknown_zones\":[\"未知\"]},"
        "\"risks\":[{\"risk\":\"风险\",\"severity\":\"high|medium|low\",\"trigger_condition\":\"条件\"}],"
        "\"ambiguities\":[\"歧义\"],\"assumptions\":[\"假设\"],\"paradigm_hints\":[\"简短范式名(如:信息论,系统论,数据驱动,网络科学,统计学,控制论,不要用长句描述)\"]}"
        f"\n需求: {raw}"
    )
    payload = {
        "model": "glm-4-flash",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 600,
    }
    req = urllib.request.Request(
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        parsed = json.loads(content[start:end + 1]) if end > start else {}
        goal = parsed.get("goal", {})
        dna = {
            "dna_version": "1.0-plugin-llm",
            "goal": {
                "primary": goal.get("primary", raw[:30]),
                "secondary_goals": [str(g).strip() for g in goal.get("secondary_goals", [])],
                "success_criteria": [str(c).strip() for c in goal.get("success_criteria", [])],
                "goal_source": "user_stated",
            },
            "constraints": [{
                "type": c.get("type", "soft"),
                "dimension": c.get("dimension", "technology"),
                "description": c.get("description", ""),
                "source": "user_stated",
            } for c in parsed.get("constraints", [])],
            "boundaries": {
                "in_scope": [str(b).strip() for b in (parsed.get("boundaries") or {}).get("in_scope", [])],
                "out_of_scope": [str(b).strip() for b in (parsed.get("boundaries") or {}).get("out_of_scope", [])],
                "unknown_zones": [str(b).strip() for b in (parsed.get("boundaries") or {}).get("unknown_zones", [])],
            },
            "risks": [{
                "risk": str(r.get("risk", "")).strip(),
                "severity": str(r.get("severity", "medium")).lower(),
                "trigger_condition": str(r.get("trigger_condition", "")).strip(),
            } for r in parsed.get("risks", [])],
            "ambiguities": [str(a).strip() for a in parsed.get("ambiguities", [])],
            "assumptions": [str(a).strip() for a in parsed.get("assumptions", [])],
            "paradigm_hints": [str(p).strip() for p in parsed.get("paradigm_hints", [])],
        }
        state.artifacts["S1"] = {
            "dna": dna,
            "parse_log": {"parse_note": "插件LLM解析(真实)", "clarification_rounds": 0,
                          "text_strategy": None, "clarify_template": None},
        }
    except Exception:
        # 插件自身兜底：不抛错，回退占位
        state.artifacts["S1"] = {
            "dna": {
                "dna_version": "1.0-plugin-fallback",
                "goal": {"primary": raw[:30], "secondary_goals": [],
                         "success_criteria": [], "goal_source": "user_stated"},
                "constraints": [], "boundaries": {"in_scope": [], "out_of_scope": [],
                                                  "unknown_zones": []},
                "risks": [], "ambiguities": [], "assumptions": [],
                "paradigm_hints": [],
            },
            "parse_log": {"parse_note": "插件LLM失败回退", "clarification_rounds": 0,
                          "text_strategy": None, "clarify_template": None},
        }
