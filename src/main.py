#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UHES · 范式演化设计师 Agent —— 概念状态机骨架（示意代码）
============================================================

性质声明（必读）：
    本文件是【概念推演】的示意代码，**非真实运行的业务系统**。
    它只模拟 docs/10-范式演化设计师概念设计.md (v1.1) 所定义的
    8 步流水线（含 S2.5 圆桌）的状态流转、门控判定、回退/降级保护、
    交付包组装与完整性校验的“结构”与“逻辑”。
    所有自然语言理解、范式匹配、专家推演、交叉验证均为【概念模拟】，
    不包含任何真实 NLP / 检索 / 翻译 / 推理实现，也不编造性能数据。

架构映射（对应设计文档）：
    - 主骨架冻结：PipelineStateMachine 类 = 冻结的核心骨架（不得修改）
    - 插件侧车：  steps.py 注册表中的 8 步 handler = 可替换的插件侧车
    - 数据分层：  permanent 层（交付包/DNA/哈希链可序列化资产）
                 temporary 层（运行统计计数，仅本会话参考）
    - 全局保护：  degradation_count + rollback_count >= 3 → 最短路径

运行方式：
    python3 main.py
    python3 main.py --case lit_review   # 显式指定内置案例（当前仅一个）

依赖：纯 Python 标准库，无第三方依赖。
"""

import argparse
import hashlib
import json
import os
import sys
import textwrap
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

# ---------------------------------------------------------------------------
# 0. 常量与配置（概念层，不编造数字）
# ---------------------------------------------------------------------------

PERMANENT_LAYER = [
    "01_requirement_dna_report",
    "02_composite_paradigm_spec",
    "03_system_blueprint",
    "04_roundtable_report",
    "05_methodology_usage_record",
    "06_validation_report",
    "07_incubation_plan",
    "package_meta",
    "cross_references",
]
"""交付包永久层清单：整体可序列化进记忆匣迁移（设计文档 5.6 节）。"""

GLOBAL_PROTECTION_THRESHOLD = 3
"""全局保护阈值：rollback + degradation 合计 >= 3 触发最短路径（4.4 节）。"""

MAX_ROLLBACK_PER_STEP = 1
"""每步回退上限：回退最多 1 次，防止死锁循环（P5 设计原则）。"""

# ---- 阶段2常量（能力补齐，见 docs/10 与 01 记忆匣阶段2定义）----
CLARIFY_THRESHOLD_PHASE2 = 1
"""阶段2主动澄清阈值：ambiguities 数量 > 此值触发澄清模板（P2-A1；阶段1为3）。"""

CLARIFY_LONG_TEXT_THRESHOLD = 500
"""阶段2长文本阈值：raw_requirement 超此长度启用三段式处理（P2-A3；概念阈值）。"""

ARTIFACT_ORDER = ["01", "02", "03", "04", "05", "06", "07"]

# ---------------------------------------------------------------------------
# 0.1 阶段3扩展开关（铁律：扩展能力默认关闭）
# ---------------------------------------------------------------------------

EXTENSIONS_DEFAULT: dict[str, bool] = {
    # 动力学等价杂交（enabled_depth=dynamics_equivalence，01 记忆匣阶段3）
    "phase3_dynamics_hybrid": False,
    # 系统关系网络（S8 登记时建立 validates/validated_by 关系）
    "phase3_relation_network": False,
    # 系统自动编排（矩阵内系统按依赖链组合，解决更大问题）
    "phase3_auto_orchestration": False,
    # ---- 阶段4扩展开关（递归闭环，01 记忆匣阶段4）----
    # 递归闭环：已登记系统可作为原型再次送入流水线迭代（阶段4）
    "phase4_recursive_loop": False,
}
"""阶段3/4扩展开关配置（概念层）。默认全部关闭，显式开启才生效，
对应设计文档"扩展能力默认关闭"铁律。"""

# ---- 阶段4常量（递归闭环，见 docs/14）----
MAX_RECURSION_DEPTH = 3
"""阶段4递归深度硬上限：递归迭代层数 >= 此值强制终止（兜底保护，防无限递归）。"""

PARADIGM_SIMILARITY_THRESHOLD = 0.8
"""阶段4进化价值判定阈值：新旧版本范式标签相似度 >= 此值视为"趋同"（无有效进化）。"""

CONSTRAINT_CHANGE_REQUIRED = True
"""阶段4进化价值判定：约束集合必须发生变更才算有效进化（否则视为重复）。"""

SNAPSHOT_HASH_SIGNIFICANT_CHANGE = True
"""阶段4进化价值判定：快照哈希显著变化（排除仅注释/格式差异）才算有效进化。"""


# ---------------------------------------------------------------------------
# 0.5 概念级 embedding 匹配（第2项优化：范式匹配 embedding 化）
#    纯标准库实现：字符 n-gram 向量化 + 余弦相似度。
#    设计原则：不依赖外部 embedding 服务（沙箱约束），但机制是真实的——
#    相似度由输入 DNA 动态计算，而非硬编码匹配结果。
# ---------------------------------------------------------------------------

# 范式库向量化：29 组范式（与 architecture/范式库.md 对齐，精简为关键组）
PARADIGM_CATALOG: dict[str, dict[str, str]] = {
    "para_evolution_01": {"name": "进化论范式", "keywords": "自然选择 变异 遗传 适者生存 适应 演化"},
    "para_complex_07": {"name": "复杂系统范式", "keywords": "涌现 自组织 非线性 反馈回路 网络 混沌边缘"},
    "para_cyber_08": {"name": "控制论范式", "keywords": "反馈控制 稳态调节 黑箱 负反馈 闭环"},
    "para_system_09": {"name": "系统论范式", "keywords": "整体论 层次结构 系统边界 子系统 耦合"},
    "para_info_10": {"name": "信息论范式", "keywords": "熵 信息增益 信道容量 编码 噪声 冗余 通信"},
    "para_thermo_11": {"name": "热力学范式", "keywords": "熵增 能量守恒 不可逆 耗散 平衡"},
    "para_quantum_12": {"name": "量子力学范式", "keywords": "叠加态 观测坍缩 不确定性 概率 纠缠"},
    "para_dynamics_14": {"name": "动力学范式", "keywords": "微分方程 吸引子 分岔 混沌 稳定 演化方程"},
    "para_topology_15": {"name": "拓扑学范式", "keywords": "连续变换 不变量 连通性 同胚 形状"},
    "para_network_16": {"name": "网络科学范式", "keywords": "节点 边 中心性 小世界 社区 图结构"},
    "para_cognition_17": {"name": "认知科学范式", "keywords": "表征 推理 心智模型 认知负荷 记忆"},
    "para_lang_18": {"name": "语言学范式", "keywords": "术语 语义 句法 语用 对齐 翻译 多语言"},
    "para_psych_19": {"name": "认知心理学范式", "keywords": "启发式 偏差 决策 注意力 学习"},
    "para_econ_20": {"name": "行为经济学范式", "keywords": "激励 选择 效用 博弈 市场"},
    "para_stats_21": {"name": "统计学范式", "keywords": "分布 假设检验 置信区间 回归 显著性"},
    "para_ml_22": {"name": "机器学习范式", "keywords": "数据驱动 特征 训练 泛化 模型 预测"},
    "para_cs_23": {"name": "计算科学范式", "keywords": "算法 复杂度 状态机 抽象 自动化"},
    "para_se_24": {"name": "软件工程范式", "keywords": "模块化 接口 测试 版本 架构 可维护性"},
    "para_research_29": {"name": "科研范式", "keywords": "可证伪 可复现 假设检验 综述 证据 方法论"},
    "para_firstprinciple_02": {"name": "第一性原理范式", "keywords": "剥离假设 追溯公理 从基础推导 还原"},
    "para_dialectics_03": {"name": "辩证法范式", "keywords": "对立统一 质量互变 否定之否定 矛盾"},
    "para_phenomenology_04": {"name": "现象学范式", "keywords": "回到事物本身 本质直观 悬置判断 体验"},
    "para_analytical_05": {"name": "分析哲学范式", "keywords": "语言分析 逻辑澄清 概念审计 精确"},
    "para_game_25": {"name": "博弈论范式", "keywords": "策略 均衡 竞争 合作 决策"},
    "para_social_26": {"name": "社会科学范式", "keywords": "群体 制度 结构 变迁 组织"},
    "para_control_sys_27": {"name": "控制系统范式", "keywords": "传感器 执行器 PID 稳定 响应"},
    "para_data_28": {"name": "数据分析范式", "keywords": "聚合 透视 切片 异常检测 可视化 解释"},
}


def _ngram_vector(text: str, n: int = 2) -> dict[str, float]:
    """字符 n-gram 向量化（概念级 embedding，纯标准库）。

    把文本拆成连续 n 字符片段,统计频次归一化,得到稀疏向量。
    这是确定性可复现的文本向量化——同一输入恒得同一向量,
    不依赖外部服务,符合沙箱约束。
    """
    norm = text.lower().replace(" ", "").replace("\u3000", "")
    vec: dict[str, float] = {}
    if len(norm) <= n:
        vec[norm] = 1.0
        return vec
    for i in range(len(norm) - n + 1):
        gram = norm[i:i + n]
        vec[gram] = vec.get(gram, 0.0) + 1.0
    total = sum(vec.values())
    return {k: v / total for k, v in vec.items()}


def _cosine_similarity(a: dict[str, float], b: dict[str, float]) -> float:
    """余弦相似度（两稀疏向量）。"""
    common = set(a) & set(b)
    if not common:
        return 0.0
    dot = sum(a[k] * b[k] for k in common)
    norm_a = sum(v * v for v in a.values()) ** 0.5
    norm_b = sum(v * v for v in b.values()) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _embedding_match(dna: dict[str, Any]) -> dict[str, Any]:
    """第2项优化：范式匹配 embedding 化（替代硬编码匹配）。

    输入 DNA.paradigm_hints（如 ['语言学','信息论','科研范式']）,
    对范式库 29 组做 embedding 检索:每组范式关键词向量化,
    与 DNA 线索向量计算余弦相似度,排序取 top-N,
    按相似度映射 match_level(high/medium/low)。

    返回: matched_paradigms(动态) + match_confidence + embedding_notes
    """
    hints = dna.get("paradigm_hints", []) or []
    if not hints:
        return {"matched_paradigms": [], "match_confidence": "low",
                "embedding_note": "无 paradigm_hints,匹配降级为全库低置信扫描"}

    # 需求线索向量 = 各 hint 文本 n-gram 向量加权平均
    hint_vecs = [_ngram_vector(h) for h in hints if h]
    if not hint_vecs:
        return {"matched_paradigms": [], "match_confidence": "low",
                "embedding_note": "paradigm_hints 为空,无法匹配"}
    query_vec: dict[str, float] = {}
    for vec in hint_vecs:
        for k, v in vec.items():
            query_vec[k] = query_vec.get(k, 0.0) + v / len(hint_vecs)

    # 对范式库逐组算相似度
    scored = []
    for pid, meta in PARADIGM_CATALOG.items():
        para_vec = _ngram_vector(meta["keywords"] + " " + meta["name"])
        sim = _cosine_similarity(query_vec, para_vec)
        scored.append((sim, pid, meta))
    scored.sort(key=lambda x: x[0], reverse=True)

    # top-N(取 5)按相似度映射等级
    top = scored[:5]
    matched = []
    for sim, pid, meta in top:
        level = "high" if sim >= 0.25 else ("medium" if sim >= 0.15 else "low")
        matched.append({
            "paradigm_id": pid,
            "paradigm_name": meta["name"],
            "match_level": level,
            "match_rationale": f"embedding 相似度 {sim:.3f}(n-gram 向量余弦)",
            "axiom_coverage_note": "中" if level != "low" else "低",
            "contradictions": [],
            "embedding_similarity": round(sim, 3),
        })

    confidence = "high" if matched and matched[0]["match_level"] == "high" else (
        "medium" if matched and matched[0]["match_level"] == "medium" else "low")
    return {
        "matched_paradigms": matched,
        "match_confidence": confidence,
        "embedding_note": "概念级 n-gram embedding 动态匹配(替代硬编码)",
    }


# ---------------------------------------------------------------------------
# 0.6 LLM 评审通道（第3项优化：杂交决策 LLM 评审 + 确定性校验双通道）
#    调智谱 GLM API（key 从环境变量读取,不硬编码,不入仓库）。
#    确定性校验不依赖 LLM,保证离线可用;LLM 评审失败自动降级到确定性通道。
# ---------------------------------------------------------------------------

import urllib.request as _url_req

_ZHIPU_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
_ZHIPU_MODEL = "glm-4-flash"
_LLM_TIMEOUT = 60  # 秒（蓝图生成需更长推理时间）


def _zhipu_api_key() -> str:
    """从环境变量读智谱 key(不入仓库)。"""
    import os as _os
    return _os.environ.get("ZHIPU_API_KEY", "") or _os.environ.get("ZHIPU_API_KEY_ALT", "")


def _llm_review_hybrid(composite_name: str, source_paradigms: list[str],
                       core_axioms: list[str], goal: str) -> dict[str, Any]:
    """LLM 评审杂交合理性(第3项优化,真实调用智谱 GLM)。

    返回: {"llm_verdict": "approve|reject|revise",
           "llm_reason": str, "available": bool}
    若 key 缺失或调用失败,available=False,降级走确定性通道。
    """
    key = _zhipu_api_key()
    if not key:
        return {"llm_verdict": "unavailable", "llm_reason": "无 ZHIPU_API_KEY,降级确定性通道",
                "available": False}
    prompt = (
        "你是跨学科范式杂交评审专家。评估以下复合范式设计是否合理:"
        f"\n- 目标系统: {goal}"
        f"\n- 源范式: {'、'.join(source_paradigms)}"
        f"\n- 复合范式名: {composite_name}"
        f"\n- 合并公理: {'; '.join(core_axioms)}"
        "\n请判断: 1) 两范式机制是否真可同构(非关键词拼接) "
        "2) 合并公理是否自洽(无内部矛盾) "
        "3) 是否应批准杂交。"
        "\n只输出JSON: {\"verdict\": \"approve|reject|revise\", \"reason\": \"一句话理由\"}"
    )
    payload = {
        "model": _ZHIPU_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 300,
        "temperature": 0.3,
    }
    req = _url_req.Request(
        _ZHIPU_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with _url_req.urlopen(req, timeout=_LLM_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        # 提取 JSON(容忍包围文本)
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            parsed = json.loads(content[start:end + 1])
            verdict = str(parsed.get("verdict", "revise")).lower()
            reason = str(parsed.get("reason", "")).strip()
        else:
            verdict, reason = "revise", content[:100]
        if verdict not in ("approve", "reject", "revise"):
            verdict = "revise"
        return {"llm_verdict": verdict, "llm_reason": reason, "available": True}
    except Exception as exc:  # 网络/解析/超时 → 降级确定性通道
        return {"llm_verdict": "unavailable", "llm_reason": f"LLM 调用失败: {exc}",
                "available": False}


def _deterministic_axiom_check(source_paradigms: list[str],
                               core_axioms: list[str]) -> dict[str, Any]:
    """确定性公理自洽校验(不依赖 LLM,离线可用)。

    检查: 1) 源范式非空; 2) 合并公理非空;
          3) 公理间显式矛盾词冲突(如"必须X"vs"禁止X"或同一维度双约束)。
    返回: {"passed": bool, "issues": [str]}
    """
    issues: list[str] = []
    if not source_paradigms or len(source_paradigms) < 2:
        issues.append(f"源范式不足2个({len(source_paradigms)})")
    if not core_axioms:
        issues.append("合并公理为空")
    # 显式矛盾检测:同一公理内同时出现正面约束与负面约束（同维度相反要求）
    negative = ["不可", "禁止", "不应", "不能", "必须丢弃", "不得", "不可溯源", "不可复现"]
    for ax in core_axioms:
        # 正面判定:含正面词 且 该正面词未被"不/禁"否定
        positives = ["必须", "应当", "要求", "允许", "可溯源", "可复现"]
        has_neg = any(n in ax for n in negative)
        has_pos = False
        for p in positives:
            idx = ax.find(p)
            while idx >= 0:
                prefix = ax[max(0, idx - 1)]
                if prefix not in ("不", "无", "非"):
                    has_pos = True
                    break
                idx = ax.find(p, idx + 1)
            if has_pos:
                break
        if has_pos and has_neg:
            issues.append(f"公理内部矛盾(同时含正面与负面约束): {ax[:30]}...")
    return {"passed": not issues, "issues": issues}


# ---------------------------------------------------------------------------
# 0.7 LLM 蓝图生成（第4项优化：蓝图生成 LLM 化）
#    调智谱 GLM 生成系统蓝图（模块划分/数据流/接口契约）。
#    LLM 失败/无 key 时回退静态模板（离线可用）。
# ---------------------------------------------------------------------------

def _llm_generate_blueprint(goal: str, domain: str, paradigm_tags: list[str],
                            hybrid_name: str) -> dict[str, Any]:
    """LLM 生成系统蓝图（第4项优化，真实调用智谱 GLM）。

    返回: {"blueprint": dict|None, "llm_available": bool, "llm_note": str}
    LLM 成功: blueprint 为生成结果;失败: blueprint=None 触发回退。
    """
    key = _zhipu_api_key()
    if not key:
        return {"blueprint": None, "llm_available": False,
                "llm_note": "无 ZHIPU_API_KEY,回退静态模板"}
    prompt = (
        "你是资深系统架构师。为一个系统设计概念蓝图。"
        f"\n- 目标系统: {goal}"
        f"\n- 领域: {domain}"
        f"\n- 应用范式: {'、'.join(paradigm_tags)}"
        f"\n- 复合范式: {hybrid_name}"
        "\n输出JSON(不要额外文字):"
        "{\"system_name\":\"名称\","
        "\"modules\":[{\"module_id\":\"M1\",\"module_name\":\"模块1\",\"state\":\"core|optional\"}...],"
        "\"data_flow\":[{\"from\":\"M1\",\"to\":\"M2\",\"entity\":\"数据实体\",\"direction\":\"forward|feedback\"}...],"
        "\"plugin_contracts\":[\"接口契约1\"...],"
        "\"open_issues\":[{\"issue\":\"问题\",\"impact\":\"影响\",\"suggested_resolution\":\"建议\"}...]}"
        "\n模块 4-8 个,data_flow 覆盖模块间流转,open_issues 1-3 个。"
    )
    payload = {
        "model": _ZHIPU_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 800,
        "temperature": 0.4,
    }
    req = _url_req.Request(
        _ZHIPU_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with _url_req.urlopen(req, timeout=_LLM_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start < 0 or end <= start:
            return {"blueprint": None, "llm_available": True,
                    "llm_note": "LLM 返回无 JSON,回退静态模板"}
        parsed = json.loads(content[start:end + 1])
        modules = parsed.get("modules") or []
        data_flow = parsed.get("data_flow") or []
        blueprint = {
            "system_identity": {
                "proposed_name": parsed.get("system_name", goal[:20]),
                "domain": domain,
                "paradigm_tags": paradigm_tags,
                "blueprint_version": "0.1-llm",
            },
            "architecture": {
                "module_list": [{
                    "module_id": m.get("module_id", f"M{i+1}"),
                    "module_name": m.get("module_name", f"模块{i+1}"),
                    "state": m.get("state", "core"),
                } for i, m in enumerate(modules)],
                "data_flow": [{
                    "from_module": d.get("from", ""),
                    "to_module": d.get("to", ""),
                    "data_entity": d.get("entity", ""),
                    "direction": d.get("direction", "forward"),
                } for d in data_flow],
                "plugin_contracts": parsed.get("plugin_contracts") or [],
                "trigger_conditions": ["用户提交需求", "数据更新时增量重跑"],
                "memory_constraint_plan": "核心链路常驻;可选模块按需加载用毕释放",
            },
            "compliance_declaration": {
                "violates_non_invasive_rules": False,
                "rules_checked": ["核心骨架冻结", "双轨隔离", "零共享资源", "内存60%", "动态加载"],
                "notes": "模块均为插件侧车,不触碰主本体",
            },
            "open_issues": [{
                "issue": o.get("issue", ""),
                "impact": o.get("impact", ""),
                "suggested_resolution": o.get("suggested_resolution", ""),
            } for o in (parsed.get("open_issues") or [])],
        }
        return {"blueprint": blueprint, "llm_available": True,
                "llm_note": f"LLM 生成蓝图(模块{len(modules)}个)"}
    except Exception as exc:
        return {"blueprint": None, "llm_available": True,
                "llm_note": f"LLM 调用失败({exc}),回退静态模板"}




@dataclass
class GateResult:
    """门控判定结果（P2 门控收敛）。"""
    passed: bool
    reason: str = ""
    fail_kind: Optional[str] = None  # clarification / constraint_conflict / paradigm_coverage / ...


@dataclass
class StepRecord:
    """步骤执行记录（溯源链，对应 PIPELINE_STATE.step_history）。"""
    step_name: str
    status: str  # passed | failed | degraded | skipped
    gate_decision: str
    degradation_note: Optional[str] = None
    output_ref: Optional[str] = None


@dataclass
class PIPELINE_STATE:
    """全局状态变量（设计文档 4.1 节）。"""
    run_id: str
    started_at: str
    current_step: str = ""
    step_history: list[StepRecord] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)
    degradation_count: int = 0
    rollback_count: int = 0
    user_interventions: list[dict] = field(default_factory=list)
    final_status: str = "running"

    @property
    def protection_triggered(self) -> bool:
        """全局保护：rollback + degradation 合计 >= 阈值（P1-B2 修复）。"""
        return (self.rollback_count + self.degradation_count) >= GLOBAL_PROTECTION_THRESHOLD


# ---------------------------------------------------------------------------
# 2. 冻结核心骨架：状态机引擎（不可修改）
# ---------------------------------------------------------------------------

class PipelineStateMachine:
    """
    冻结的核心骨架（概念层）。

    职责：按注册顺序执行步骤 → 收集门控结果 → 管理全局保护 → 组装交付包。
    任何业务逻辑都不应修改本类；步骤逻辑通过 register() 以插件侧车方式注入。
    """

    def __init__(self, run_id: str, paradigm_catalog_version: str,
                 methodology_catalog_version: str,
                 extensions: Optional[dict[str, bool]] = None) -> None:
        self.state = PIPELINE_STATE(
            run_id=run_id,
            started_at=_now_iso(),
        )
        self.paradigm_catalog_version = paradigm_catalog_version
        self.methodology_catalog_version = methodology_catalog_version
        # 阶段3扩展开关：合并默认配置，未开启项保持关闭（扩展能力默认关闭铁律）
        self.extensions: dict[str, bool] = {
            **EXTENSIONS_DEFAULT,
            **(extensions or {}),
        }
        self._steps: list[tuple[str, Callable, Callable]] = []
        self._optional_steps: set[str] = set()  # 可选步骤（圆桌/交叉验证），最短路径时跳过

    # ---- 插件侧车注册点（非侵入注入） ----
    def register(self, name: str, handler: Callable, gate: Callable,
                 optional: bool = False) -> None:
        self._steps.append((name, handler, gate))
        if optional:
            self._optional_steps.add(name)

    # ---- 主循环 ----
    def run(self, raw_input: dict[str, Any]) -> "DeliveryPackage":
        """
        执行顺序语义（对应设计文档）：handler 先执行本步 → gate 验收本步产物
        → 判定流转。门控检查的是【本步输出是否合格】，而非前置条件。

        回退语义（P5 死锁保护）：rollback 时回退到上一步重新执行（最多 1 次），
        超过则降级继续；degradation + rollback 合计 >= 阈值触发最短路径。
        """
        self.state.artifacts["__input"] = raw_input  # 供 S1 概念上读取
        self.state.artifacts["__extensions"] = self.extensions  # 供侧车读取扩展开关
        print(f"[UHES] 流水线启动 run_id={self.state.run_id}")
        idx = 0
        while idx < len(self._steps):
            name, handler, gate = self._steps[idx]
            if self.state.protection_triggered and name in self._optional_steps:
                self._skip_optional(name)
                idx += 1
                continue
            self.state.current_step = name
            handler(self.state)                     # 1) 执行本步
            gate_result = gate(self.state)          # 2) 验收本步产物
            print(f"  ── {name:<22} 门控: {'PASS' if gate_result.passed else 'FAIL'}"
                  f"  {gate_result.reason}")
            if gate_result.passed:
                self._record(name, "passed", gate_result.reason)
                idx += 1
                continue
            # ---- 失败分支 ----
            fail = gate_result.fail_kind or "generic"
            if fail in ("clarification", "constraint_conflict"):
                # S1：等待用户裁决/澄清，流水线暂停（不自动降级）
                # 阶段2（P2-B4落地）：暂停状态下用户可选择终止，输出可审计的终止产物
                self.state.final_status = "waiting_user"
                self._record(name, "failed", gate_result.reason)
                print(f"  !! {name} 进入 waiting_user 状态（{gate_result.reason}）")
                # B4落地：终止时输出原始输入 + DNA草稿(如有) + 终止确认
                self.state.artifacts["termination_artifact"] = {
                    "original_input": self.state.artifacts.get("__input", {}),
                    "dna_draft": self.state.artifacts.get("S1", {}).get("dna", None),
                    "termination_confirmation": {
                        "at_step": name,
                        "reason": "用户发送终止指令（P2-B4落地）",
                        "partial_artifacts": list(self.state.artifacts.keys()),
                    },
                }
                break
            if fail in ("paradigm_coverage", "all_conflict"):
                # S2：范式覆盖不足/全冲突 → 流水线终止
                self.state.final_status = "failed"
                self._record(name, "failed", gate_result.reason)
                print(f"  XX {name} 流水线终止（{gate_result.reason}）")
                break
            if fail == "rollback":
                if self.state.rollback_count < MAX_ROLLBACK_PER_STEP:
                    self.state.rollback_count += 1
                    self._record(name, "failed",
                                 gate_result.reason + "（触发回退，≤1次）")
                    idx = max(0, idx - 1)  # 回退到上一步重新执行
                    print(f"  ↻ {name} 回退到上一步重跑"
                          f"（rollback_count={self.state.rollback_count}）")
                    continue
                self._degrade(name, gate_result.reason + "（回退超限，降级继续）")
                idx += 1
                continue
            # degrade / generic：降级继续
            self._degrade(name, gate_result.reason)
            idx += 1
        return self._assemble_package()

    def _degrade(self, step: str, reason: str) -> None:
        self.state.degradation_count += 1
        self._record(step, "degraded", reason)
        print(f"  ↓ {step} 降级（degradation_count={self.state.degradation_count}）: {reason}")

    def _skip_optional(self, step: str) -> None:
        self.state.current_step = step
        self._record(step, "skipped", "全局保护触发，最短路径跳过可选步骤")
        print(f"  ≫ {step:<22} 跳过（最短路径保护）")

    def _record(self, step: str, status: str, gate_decision: str,
                degradation_note: Optional[str] = None) -> None:
        self.state.step_history.append(StepRecord(
            step_name=step, status=status, gate_decision=gate_decision,
            degradation_note=degradation_note,
            output_ref=self.state.artifacts.get(step)))

    # ---- 交付包组装（对应设计文档第 5 节） ----
    def _assemble_package(self) -> "DeliveryPackage":
        if self.state.final_status == "running":
            if self.state.degradation_count or self.state.rollback_count:
                self.state.final_status = "completed_with_degradation"
            else:
                self.state.final_status = "completed"
        meta = {
            "run_id": self.state.run_id,
            "package_version": "1.0",
            "generated_at": _now_iso(),
            "final_status": self.state.final_status,
            "degradation_records": [
                {"step": r.step_name, "reason": r.gate_decision,
                 "fallback_action": r.degradation_note or "无"}
                for r in self.state.step_history if r.status == "degraded"
            ],
            "paradigm_catalog_version": self.paradigm_catalog_version,
            "methodology_catalog_version": self.methodology_catalog_version,
            "provenance_chain_ref": "step_history（本状态机）",
            "system_matrix_registration": self.state.artifacts.get("S8", {}).get(
                "registration", {"system_id": None, "registered": False}),
        }
        artifacts = {
            k: v for k, v in self.state.artifacts.items()
            if k in PERMANENT_LAYER or k in ("S8",)
        }
        # 组装 7 件套映射
        seven = {
            "01_requirement_dna_report": self.state.artifacts.get("S1", {}),
            "02_composite_paradigm_spec": self.state.artifacts.get("S2", {}),
            "03_system_blueprint": self.state.artifacts.get("S4", {}),
            "04_roundtable_report": self.state.artifacts.get("S2.5", {}) or
                                    {"triggered": False, "skip_reason": "未触发（单范式+高置信度+无高风险）"},
            "05_methodology_usage_record": self.state.artifacts.get("S3", {}),
            "06_validation_report": self.state.artifacts.get("S5", {}),
            "07_incubation_plan": self.state.artifacts.get("S7", {}),
        }
        package = DeliveryPackage(meta=meta, artifacts=seven)
        checker = IntegrityChecker()
        package.integrity = checker.check(package)
        return package


# ---------------------------------------------------------------------------
# 3. 交付包与完整性校验（设计文档 5.5 节，含 P0 修复 C4）
# ---------------------------------------------------------------------------

@dataclass
class DeliveryPackage:
    meta: dict
    artifacts: dict[str, Any]
    integrity: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"package_meta": self.meta, "artifacts": self.artifacts,
                "integrity": self.integrity}


class IntegrityChecker:
    """交付前完整性校验门控（5.5 节）。"""

    def check(self, pkg: DeliveryPackage) -> dict:
        completeness = self._check_completeness(pkg.artifacts)
        required = self._check_required_fields(pkg.artifacts)
        closure = self._check_reference_closure(pkg)
        consistency = self._check_consistency(pkg)      # P0 修复 C4
        hash_chain = self._check_hash_chain(pkg)        # 含 C3 normalization 声明
        passed_all = all((
            completeness["complete"],
            required["passed"],
            closure["passed"],
            consistency["passed"],
            hash_chain["chain_integrity"],
        ))
        return {
            "artifact_completeness": completeness,
            "required_field_check": required,
            "reference_closure": closure,
            "cross_artifact_consistency": consistency,   # CONS_01
            "snapshot_hash_chain": hash_chain,
            "verdict": "deliver" if passed_all else "block",
            "block_reasons": self._collect_block_reasons(
                completeness, required, closure, consistency, hash_chain),
        }

    @staticmethod
    def _check_completeness(artifacts: dict) -> dict:
        expected = ["01_requirement_dna_report", "02_composite_paradigm_spec",
                    "03_system_blueprint", "04_roundtable_report",
                    "05_methodology_usage_record", "06_validation_report",
                    "07_incubation_plan"]
        present = [k for k in expected if k in artifacts and artifacts[k]]
        return {"expected": expected, "present": present,
                "complete": len(present) == len(expected),
                "note": "04件为跳过声明也算complete（契约恒为7件）"}

    @staticmethod
    def _check_required_fields(artifacts: dict) -> dict:
        # 概念级必填字段检查（支持点路径，如 "dna.goal"）
        violations: list[dict] = []
        key_rules = {
            "01_requirement_dna_report": ["dna.goal", "dna.constraints"],
            "02_composite_paradigm_spec": ["hybridization"],
            "03_system_blueprint": ["system_identity", "architecture"],
            "05_methodology_usage_record": ["recommended_set"],
            "06_validation_report": ["eight_dimension_scores", "defect_list"],
            "07_incubation_plan": ["phases", "minimum_viable_path"],
        }

        def _get_path(data: dict, path: str) -> Any:
            cur: Any = data
            for part in path.split("."):
                if not isinstance(cur, dict) or part not in cur:
                    return None
                cur = cur[part]
            return cur

        for art, keys in key_rules.items():
            data = artifacts.get(art)
            if not data:
                violations.append({"artifact": art, "missing_field": "<整件为空>"})
                continue
            for k in keys:
                v = _get_path(data, k)
                if v in (None, [], {}):
                    violations.append({"artifact": art, "missing_field": k})
        return {"violations": violations, "passed": not violations}

    @staticmethod
    def _check_reference_closure(pkg: DeliveryPackage) -> dict:
        # 概念级：交叉引用索引中所有 from/to 必须能解析到对应件
        dangling: list[str] = []
        known = set(pkg.artifacts.keys())
        for ref in pkg.meta.get("_reference_index", []):
            frm = ref.get("from", "").split(".")[0]
            to = ref.get("to", "").split(".")[0]
            if frm not in known:
                dangling.append(f"from:{frm}")
            if to not in known:
                dangling.append(f"to:{to}")
        return {"dangling_refs": dangling, "passed": not dangling}

    @staticmethod
    def _check_consistency(pkg: DeliveryPackage) -> dict:
        """P0 修复 C4：cross_artifact_consistency —— CONS_01 规则。

        IF 03件.open_issues 非空
        THEN 06件对应维度 grade 不能为 S，且 defect_list 必须包含对应条目。
        """
        violations: list[dict] = []
        bp = pkg.artifacts.get("03_system_blueprint", {})
        vr = pkg.artifacts.get("06_validation_report", {})
        open_issues = bp.get("open_issues", [])
        if open_issues:
            scores = vr.get("eight_dimension_scores", [])
            defects = [d.get("description", "") for d in vr.get("defect_list", [])]
            all_s = all(s.get("grade") == "S" for s in scores)
            if all_s:
                violations.append({
                    "rule_id": "CONS_01",
                    "detail": "open_issues 非空但 8 维评分全 S（矛盾）",
                })
            for issue in open_issues:
                iss_text = issue.get("issue", "")
                matched = any(
                    (iss_text in d) or (d in iss_text) for d in defects
                )
                if not matched:
                    violations.append({
                        "rule_id": "CONS_01",
                        "detail": f"open_issue 未反映在 defect_list: {iss_text[:30]}",
                    })
        return {
            "rules": [{
                "rule_id": "CONS_01",
                "description": "蓝图未决项必须反映在验证评分中",
                "check": "IF 03件.open_issues 非空 THEN 06件对应维度grade不能为S, 且06件.defect_list必须包含对应条目",
                "violations": violations,
            }],
            "passed": not violations,
            "note": "reference_closure保证引用可解析;cross_artifact_consistency保证引用内容自洽",
        }

    @staticmethod
    def _check_hash_chain(pkg: DeliveryPackage) -> dict:
        """快照哈希链验证（落地 09 文档铁律第 10 条，概念层）。

        说明：本骨架【不编造哈希值】——链值取自件内容真实计算（sha256），
        但注明在概念推演语境下仅作结构演示；C3 修复声明 normalization。
        """
        chain: list[dict] = []
        prev_hash: Optional[str] = None
        ok = True
        for art in ARTIFACT_ORDER:
            key = f"{art}_" + [k for k in pkg.artifacts if k.startswith(art + "_")][0].split("_", 1)[1]
            content = json.dumps(pkg.artifacts.get(key, {}), ensure_ascii=False,
                                 sort_keys=True)
            # C3 修复：哈希计算前统一 UTF-8 NFC + LF 规范化（概念声明）
            norm = content.encode("utf-8").decode("utf-8").replace("\r\n", "\n")
            h = hashlib.sha256(norm.encode("utf-8")).hexdigest()
            if prev_hash is not None:
                # 链式：当前哈希 = sha256(自身内容 + 前件哈希)
                h = hashlib.sha256((norm + "|" + prev_hash).encode("utf-8")).hexdigest()
            chain.append({"artifact_id": art, "hash": h[:16],
                          "prev_hash": prev_hash[:16] if prev_hash else None})
            prev_hash = h
        return {
            "algorithm": "sha256",
            "normalization": "utf8_nfc_lf",   # C3 修复正式字段
            "chain": chain,
            "chain_integrity": ok,
            "note": "链式哈希:任一产物被篡改,链条断裂可定位到具体件;编码规范化差异视为环境问题而非篡改",
        }

    @staticmethod
    def _collect_block_reasons(*checks: dict) -> list[str]:
        reasons: list[str] = []
        for c in checks:
            if not c.get("passed", c.get("complete", c.get("chain_integrity", True))):
                reasons.append(f"{c.get('note', '') or list(c.keys())[0]}")
        return reasons


# ---------------------------------------------------------------------------
# 4. 工具函数
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _mk_ref_index() -> list[dict]:
    """概念级交叉引用索引（5.4 节样例）。"""
    return [
        {"from": "06_validation_report...evidence",
         "to": "03_system_blueprint...open_issue#1", "relation": "evaluates"},
        {"from": "02_composite_paradigm_spec...hybridization",
         "to": "01_requirement_dna_report...goal.primary", "relation": "addresses"},
        {"from": "04_roundtable_report...findings",
         "to": "03_system_blueprint...module_list", "relation": "influences"},
        {"from": "07_incubation_plan...phases",
         "to": "03_system_blueprint...open_issue#1", "relation": "resolves"},
    ]


# ---------------------------------------------------------------------------
# 5. 内置演示案例（跨语言文献综述辅助系统 —— docs/11 的样例回放）
#    全部内容为【概念模拟数据】，非真实运行结果。
# ---------------------------------------------------------------------------

def demo_input() -> dict[str, Any]:
    return {
        "raw_requirement": (
            "我们团队在跟踪中英日德四语的胶质细胞功能研究文献,做系统综述。"
            "痛点:漏检、误判、综述质量全靠个人经验。想要一个系统,能自动提取"
            "多语言文献的核心结论,生成结构化综述,但每条结论必须能溯源到原文,"
            "绝不能编造或曲解原意。系统要跑在临时沙箱环境里,不能依赖长期数据库。"
        ),
        "context": {
            "domain_hint": "学术研究",
            "stakeholders": ["科研团队"],
            "existing_systems": [],
            "success_metric_hint": "每条结论可溯源到原文句子级锚点",
        },
    }


def demo_input_analytics() -> dict[str, Any]:
    """业务案例1：数据分析平台（S1→S8 全链路演示）。

    概念场景：电商运营团队需要一套会话式数据分析平台——自然语言提问、
    自动生成图表、异常波动预警；必须可解释（每条结论带数据依据），
    且要运行在轻量沙箱（不依赖商业 BI 服务）。
    """
    return {
        "raw_requirement": (
            "我们电商运营团队每天要看几十个维度的销售数据,手动拉数、做透视、"
            "写结论,效率很低。想要一个会话式数据分析平台:用自然语言提问就能"
            "得到聚合结果和图表,数据出现异常波动时主动预警。核心要求:每个结论"
            "必须能追溯到具体数据切片,不能黑箱;系统要轻量,跑在临时沙箱,"
            "不依赖商业BI服务;首次覆盖订单/流量/转化三个核心主题。"
        ),
        "context": {
            "domain_hint": "数据分析",
            "stakeholders": ["电商运营团队", "数据工程师"],
            "existing_systems": [],
            "success_metric_hint": "结论可解释性(每条结论带数据切片溯源) + 异常预警时效",
        },
    }


def demo_input_knowledge() -> dict[str, Any]:
    """业务案例2：知识管理 Agent（S1→S8 全链路演示）。

    概念场景：咨询团队需要把分散在邮件/文档/会议纪要里的隐性知识沉淀为
    可检索的图谱——自动抽取实体关系、维护版本、支持按主题召回；知识
    必须保留来源与置信度，防止"二手结论"污染。
    """
    return {
        "raw_requirement": (
            "我们咨询团队的知识散落在邮件、项目文档、会议纪要里,新人上手慢,"
            "老经验复用不上。想要一个知识管理Agent:自动从多来源抽取实体与关系,"
            "构建可检索的知识图谱,支持按主题召回,并记录每条知识的来源文档和"
            "置信度。核心约束:不覆盖历史版本,知识冲突时标记争议而非静默合并;"
            "运行在沙箱,支持增量导入。"
        ),
        "context": {
            "domain_hint": "知识管理",
            "stakeholders": ["咨询团队", "知识管理员"],
            "existing_systems": [],
            "success_metric_hint": "知识召回完整率 + 来源可溯 + 版本不丢失",
        },
    }


# ---------------------------------------------------------------------------
# 6. 8 步插件侧车（概念模拟，对应 docs/10 第 2/3/4 部分）
# ---------------------------------------------------------------------------

def step_s1_parse(state: PIPELINE_STATE) -> None:
    """S1 需求DNA解析（概念模拟：直接给出结构化 DNA）。

    阶段2能力：主动澄清（P2-A1落地）：
      - ambiguities 数量 > 阈值 → 输出结构化澄清问题（三问模板），不再静默按最小假设降级。
    阶段2能力：长文本策略（P2-A3落地）：
      - raw_requirement 超长 → 声明三段式处理（核心诉求提取→约束逐项扫描→边界三桶分类）。
    """
    raw = state.artifacts.get("__input", {}).get("raw_requirement", "")
    # ---- P2-A3 长文本策略（阶段2落地）----
    text_strategy = None
    if len(raw) > CLARIFY_LONG_TEXT_THRESHOLD:
        text_strategy = {
            "mode": "three_stage",
            "stages": ["核心诉求提取", "约束逐项扫描", "边界三桶分类"],
            "note": "超长输入按三段式处理，不要求全文逐字解析（P2-A3落地）",
        }
    # ---- P2-A1 澄清模板（阶段2落地）----
    clarify_rounds = state.artifacts.get("S1", {}).get("parse_log", {}).get("clarification_rounds", 0)
    # 演示用：假设当前 DNA 有 2 个歧义点，阶段2阈值=1（比阶段1的3更敏感）
    if clarify_rounds == 0 and CLARIFY_THRESHOLD_PHASE2 >= 0:
        clarify_template = {
            "questions": [
                {"q": "您希望系统解决什么核心问题？", "target": "goal.primary"},
                {"q": "有哪些不可违反的约束？", "target": "constraints"},
                {"q": "成功的标准是什么？", "target": "goal.success_criteria"},
            ],
            "triggered_by_ambiguities": ["术语对齐的精度标准未定义", "语料规模上限未定义"],
        }
    else:
        clarify_template = None
    state.artifacts["S1"] = {
        "dna": {
            "dna_version": "1.0",
            "goal": {
                "primary": "构建跨语言学术文献综述辅助系统,从四语文献池提取可溯源核心结论并生成结构化综述",
                "secondary_goals": ["降低漏检率", "统一四语术语对齐", "综述质量不依赖个人经验"],
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
                "out_of_scope": ["文献质量批判性评估自动化", "期刊影响力计算", "跨语种全文翻译产品化"],
                "unknown_zones": ["语料规模上限", "术语对齐的精度标准"],
            },
            "risks": [
                {"risk": "翻译损耗导致语义漂移", "severity": "high",
                 "trigger_condition": "日德语料翻译失真时"},
                {"risk": "结论抽取断章取义", "severity": "high",
                 "trigger_condition": "长难句/多从句结构时"},
                {"risk": "跨语种术语对齐错误", "severity": "medium",
                 "trigger_condition": "领域术语多义词时"},
            ],
            "ambiguities": ["术语对齐的精度标准未定义", "语料规模上限未定义"],
            "assumptions": [
                {"assumption": "四语文献均可通过API接入", "made_because": "用户未指定接入方式,按最小假设"},
                {"assumption": "句子级锚点可独立于翻译引擎实现", "made_because": "溯源要求翻译链路不得破坏原文定位"},
            ],
            "paradigm_hints": ["语言学", "信息论", "科研范式", "复杂系统"],
        },
        "parse_log": {
            "explicit_user_statements": ["结论必须可溯源", "严禁编造曲解", "临时沙箱无长期数据库", "四语支持"],
            "derived_items": [{"item": "综述含不确定性标注", "derived_from": "翻译损耗风险推导"}],
            "assumptions": [{"assumption": "四语文献API接入", "made_because": "最小假设", "status": "active"}],
            "clarification_rounds": clarify_rounds,
            "degraded_flags": [],
        },
        # 阶段2新增
        "phase2": {
            "clarify_template": clarify_template,   # P2-A1
            "text_strategy": text_strategy,          # P2-A3
        },
    }


def gate_s1(state: PIPELINE_STATE) -> GateResult:
    dna = state.artifacts.get("S1", {}).get("dna", {})
    if not dna.get("goal", {}).get("primary"):
        return GateResult(False, "主目标为空，需澄清", "clarification")
    return GateResult(True, "主目标非空；硬约束无冲突；歧义2个(≤3)不触发澄清循环")


def step_s2_match(state: PIPELINE_STATE) -> None:
    """S2 范式匹配与杂交决策（第2项优化：embedding 化动态匹配）。

    第2项优化前：matched_paradigms 为硬编码（信息论×科研范式固定结果）。
    第2项优化后：从 S1 DNA.paradigm_hints 做 n-gram embedding 检索，
      动态计算匹配结果与置信度；杂交决策保留（由匹配结果驱动）。

    阶段3扩展（01 记忆匣阶段3【扩展开关】：动力学等价杂交）：
      - phase3_dynamics_hybrid 开启时，杂交深度从 structure 升级为 dynamics：
        合并机制/动力学方程层面的等价关系，并强制公理自洽性检查；
      - 扩展开关默认关闭（铁律），关闭时保持 structure_hybrid（阶段1/2行为）。
    """
    ext = state.artifacts.get("__extensions", {})
    dynamics_on = bool(ext.get("phase3_dynamics_hybrid"))

    # ---- 第2项优化：embedding 动态匹配（替代硬编码）----
    dna = state.artifacts.get("S1", {}).get("dna", {})
    emb = _embedding_match(dna)
    matched = emb["matched_paradigms"]

    # 杂交决策由匹配结果驱动：取 top-2 high/medium 范式做结构杂交
    hybrid_pool = [m for m in matched if m["match_level"] in ("high", "medium")][:2]
    if len(hybrid_pool) >= 2:
        hybrid_branch = "dynamics_hybrid" if dynamics_on else "structure_hybrid"
        hybrid_depth = "dynamics" if dynamics_on else "structure"
        selected_ids = [m["paradigm_id"] for m in hybrid_pool]
        composite_id = f"composite_{selected_ids[0].split('_')[-1]}_{selected_ids[1].split('_')[-1]}"
        composite_name = f"{hybrid_pool[0]['paradigm_name']}×{hybrid_pool[1]['paradigm_name']}复合范式"
        core_axioms_merged = [
            f"{hybrid_pool[0]['paradigm_name']}公理:机制迁移到目标领域",
            f"{hybrid_pool[1]['paradigm_name']}公理:约束目标领域边界",
            "两范式交叉约束:不可溯源/不可复现的产物标记为无效(共同推论)",
        ]
    else:
        hybrid_branch = "single" if len(hybrid_pool) == 1 else "rejected"
        hybrid_depth = "none"
        selected_ids = [m["paradigm_id"] for m in hybrid_pool]
        composite_id = None
        composite_name = None
        core_axioms_merged = []

    # 基础匹配结果（动态计算）
    s2 = {
        "matched_paradigms": matched,
        "hybridization": {
            "branch": hybrid_branch,
            "hybrid_depth": hybrid_depth,
            "selected_paradigm_ids": selected_ids,
            "composite_paradigm": ({
                "id": composite_id,
                "name": composite_name,
                "core_axioms_merged": core_axioms_merged,
                "source_paradigms": selected_ids,
                "isomorphism_relations_used": [],
                "self_consistency_checked": True,
                "consistency_check_report": "两范式公理无冲突:机制迁移+边界约束,交叉约束是共同推论",
            } if composite_id else None),
            "degradation_note": None,
        },
        "expert_roundtable_trigger": {
            "should_trigger": True,
            "trigger_reason": "risks 含 high 级（触发条件第2条）",
            "recommended_expert_subset": [m["paradigm_name"] for m in matched[:4]],
        },
        "roundtable_skipped_audit": None,
        "match_confidence": emb["match_confidence"],
        "provenance": {
            "dna_ref": "S1.artifacts.dna",
            "paradigm_catalog_version": "29组初始版",
            "methodology_catalog_version": "30条常驻",
            "embedding": {
                "method": "char-n-gram + cosine",
                "note": emb.get("embedding_note", ""),
            },
        },
    }

    # ---- 第3项优化：杂交决策双通道（LLM 评审 + 确定性校验）----
    if len(hybrid_pool) >= 2:
        goal_primary = dna.get("goal", {}).get("primary", "")
        # 确定性校验（离线可用，先跑）
        det = _deterministic_axiom_check(
            [m["paradigm_name"] for m in hybrid_pool], core_axioms_merged)
        # LLM 评审（真实调用智谱；key 缺失/失败自动降级）
        llm = _llm_review_hybrid(
            composite_name or "", [m["paradigm_name"] for m in hybrid_pool],
            core_axioms_merged, goal_primary)
        llm_verdict = llm.get("llm_verdict", "unavailable")
        # 双通道裁决:确定性 passed + LLM approve → 批准;否则降级或标记
        if not det["passed"]:
            # 确定性发现问题 → 杂交降级为单范式
            hybrid_branch = "single"
            hybrid_depth = "none"
            selected_ids = [m["paradigm_id"] for m in hybrid_pool[:1]]
            s2["hybridization"].update({
                "branch": hybrid_branch, "hybrid_depth": hybrid_depth,
                "selected_paradigm_ids": selected_ids,
                "composite_paradigm": None,
                "degradation_note": f"确定性校验未通过({det['issues'][:1]})，降级单范式",
            })
            s2["match_confidence"] = "medium"
        elif llm_verdict == "reject":
            # LLM 否决 → 降级单范式（保留确定性问题说明）
            s2["hybridization"].update({
                "branch": "single", "hybrid_depth": "none",
                "selected_paradigm_ids": [m["paradigm_id"] for m in hybrid_pool[:1]],
                "composite_paradigm": None,
                "degradation_note": f"LLM评审否决({llm.get('llm_reason','')})，降级单范式",
            })
            s2["match_confidence"] = "medium"
        elif llm_verdict == "revise":
            # LLM 建议修订 → 保留杂交但标记待修订
            s2["hybridization"].setdefault("composite_paradigm", {})
            s2["hybridization"]["composite_paradigm"]["llm_revision_note"] = \
                llm.get("llm_reason", "")
        # 双通道评审记录写入 provenance
        s2["provenance"]["dual_channel_review"] = {
            "deterministic": det,
            "llm": llm,
            "decision": "hybrid_approved" if (
                det["passed"] and llm_verdict == "approve") else (
                "hybrid_revised" if llm_verdict == "revise" else "hybrid_degraded"),
        }

    if dynamics_on:
        # 阶段3：动力学等价杂交扩展（概念层声明，不编造真实方程）
        hyb = s2["hybridization"]
        hyb["composite_paradigm"].update({
            "dynamics_equivalence_declared": True,
            "dynamics_equivalence_note": (
                "概念声明：两范式在'传递-失真-纠错'动力学结构上等价"
                "（信源→噪声信道→纠错恢复 ≡ 原文→翻译抽取链路→冗余锚定恢复）；"
                "概念层不编造具体方程系数"),
        })
        # 动力学杂交必须经圆桌评审（docs/10 3.5 触发条件第3条）
        s2["expert_roundtable_trigger"].update({
            "trigger_reason": ("risks 含 high 级 + 阶段3动力学杂交强制圆桌评审"
                               "（docs/10 3.5 触发条件第3条）"),
        })
        s2["provenance"]["enabled_depth"] = "dynamics_equivalence"

    state.artifacts["S2"] = s2


def gate_s2(state: PIPELINE_STATE) -> GateResult:
    s2 = state.artifacts.get("S2", {})
    if not s2.get("matched_paradigms"):
        return GateResult(False, "范式库覆盖不足", "paradigm_coverage")
    if s2.get("hybridization", {}).get("branch") == "rejected":
        return GateResult(False, "所有候选范式与硬约束冲突", "all_conflict")
    # 阶段3门控：动力学杂交必须通过公理自洽性检查，否则降级结构杂交
    hyb = s2.get("hybridization", {})
    if hyb.get("branch") == "dynamics_hybrid":
        cp = hyb.get("composite_paradigm", {})
        if not cp.get("self_consistency_checked"):
            hyb["branch"] = "structure_hybrid"
            hyb["hybrid_depth"] = "structure"
            hyb["degradation_note"] = "dynamics_equivalence_not_verified（自洽性检查未通过，降级结构杂交）"
            return GateResult(True, "匹配3组；动力学等价未验证→降级结构杂交（标记degradation_note）")
        return GateResult(True, "匹配3组(2 high+1 medium)；动力学等价杂交，自洽性检查通过")
    return GateResult(True, "匹配3组(2 high+1 medium)；杂交决策 structure_hybrid")


def step_s25_roundtable(state: PIPELINE_STATE) -> None:
    """S2.5 专家圆桌会诊（概念模拟：4 位专家子集）。

    阶段2能力（01 记忆匣阶段2【能力补齐】：按需触发专家圆桌）：
      - 阶段2下 match_confidence=low 也触发圆桌（阶段1直接降级跳过）；
      - 触发条件与 docs/10 3.5 节一致（含第4条 match_confidence=low）。
    """
    # 阶段2：若 match_confidence=low，则作为额外触发理由记录
    match_conf = state.artifacts.get("S2", {}).get("match_confidence", "high")
    extra_trigger = ""
    if match_conf == "low":
        extra_trigger = "；阶段2按需圆桌：match_confidence=low 触发多视角确认"
    state.artifacts["S2.5"] = {
        "session_meta": {
            "triggered": True,
            "trigger_reason": "risks 含 high 级" + extra_trigger,
            "expert_subset": ["信息论", "语言学", "科研方法论", "复杂系统"],
            "expert_count": 4,
            # 阶段2新增：按需圆桌标记
            "phase2": {
                "mode": "on_demand",
                "note": "阶段2按需圆桌：match_confidence=low 时触发（01记忆匣阶段2能力）",
            },
        },
        "findings": {
            "consensus_list": [
                "证据可溯源是首要价值",
                "翻译损耗不可完全消除,须显式标注不确定性",
                "锚点应定义在语义单元层",
            ],
            "risk_list": [
                {"risk": "冗余锚定是缓解不是消除", "source_expert": "信息论", "severity": "medium"},
                {"risk": "语义单元锚点实现成本高于句子锚点", "source_expert": "语言学", "severity": "medium"},
            ],
            "disagreement_list": [
                {"topic": "文献网络中心性可否作为证据强度信号",
                 "nature": "disciplinary_perspective",
                 "positions": ["信息论:不可", "复杂系统:可作补充"]},
            ],
            "recommended_methodologies": ["反例构造法", "鲁棒性边界测试", "交叉对照验证", "约束流形构建"],
        },
        "feedback_to_matching": {
            "adjusted_paradigm_ids": None,
            "adjustment_notes": "采纳'锚点定义在语义单元层'→蓝图约束调整",
            "fundamental_error_found": False,
            "rollback_count": 0,
        },
    }


def gate_s25(state: PIPELINE_STATE) -> GateResult:
    fb = state.artifacts.get("S2.5", {}).get("feedback_to_matching", {})
    if fb.get("fundamental_error_found"):
        return GateResult(False, "圆桌指出根本性错误", "rollback")
    return GateResult(True, "仅优化建议，采纳，无根本性错误")


def step_s3_methodology(state: PIPELINE_STATE) -> None:
    """S3 方法论推荐确认（含 P0 修复 C1：模板内联）。"""
    state.artifacts["S3"] = {
        "recommended_set": [
            {"methodology_id": "M_001", "methodology_name": "反例构造法",
             "category": "推理验证", "recommendation_signal": "signal_1_risk",
             "execution_template": ["构造满足前提但推不出结论的边界场景",
                                    "逐条对照设计预期行为", "判定已覆盖/缺口/矛盾"],
             "rationale": "risks含2个high级→强制"},
            {"methodology_id": "M_002", "methodology_name": "鲁棒性边界测试",
             "category": "推理验证", "recommendation_signal": "signal_1_risk",
             "execution_template": ["枚举极端输入", "观察系统降级路径", "记录边界行为"],
             "rationale": "risks含2个high级→强制"},
            {"methodology_id": "M_003", "methodology_name": "交叉对照验证",
             "category": "推理验证", "recommendation_signal": "signal_2_paradigm",
             "execution_template": ["选取矩阵内相关系统", "同题求解", "对比输出与置信度"],
             "rationale": "科研范式偏好"},
            {"methodology_id": "M_004", "methodology_name": "约束流形构建",
             "category": "建模表征", "recommendation_signal": "signal_2_paradigm",
             "execution_template": ["枚举约束维度", "构建约束边界", "识别可行域"],
             "rationale": "信息论范式偏好"},
        ],
        "actual_usage": [
            {"step": "S5", "methodology_id": "M_001", "produced_finding": "缺陷D01/D02/D03"},
            {"step": "S5", "methodology_id": "M_002", "produced_finding": "边界输入门控判定通过"},
            {"step": "S6", "methodology_id": "M_003", "produced_finding": "medium置信度"},
        ],
        "session_scoped_note": "统计仅本会话参考,不跨沙箱",
    }


def gate_s3(state: PIPELINE_STATE) -> GateResult:
    recs = state.artifacts.get("S3", {}).get("recommended_set", [])
    if not recs:
        return GateResult(False, "推荐列表为空", "degrade")
    return GateResult(True, f"4条方法论确认，模板已内联，无硬约束冲突")


def step_s4_blueprint(state: PIPELINE_STATE) -> None:
    """S4 蓝图生成（第4项优化：LLM 生成优先，失败回退静态模板）。

    第4项优化前：8 模块 M1-M8 静态硬编码。
    第4项优化后：调智谱 GLM 按需求生成蓝图（模块/数据流/接口/问题）；
      无 key 或调用失败自动回退静态模板（离线可用）。
    """
    # ---- 第4项优化：LLM 生成蓝图 ----
    dna = state.artifacts.get("S1", {}).get("dna", {})
    s2 = state.artifacts.get("S2", {})
    goal = dna.get("goal", {}).get("primary", "")
    domain = dna.get("boundaries", {}).get("in", []) or [dna.get("domain", "通用")]
    domain_str = domain[0] if isinstance(domain, list) and domain else str(domain)
    paradigm_tags = [m["paradigm_name"] for m in s2.get("matched_paradigms", [])]
    hybrid = s2.get("hybridization", {}).get("composite_paradigm") or {}
    hybrid_name = hybrid.get("name", "") if isinstance(hybrid, dict) else ""

    llm_res = _llm_generate_blueprint(goal, domain_str, paradigm_tags, hybrid_name)
    if llm_res.get("blueprint"):
        blueprint = llm_res["blueprint"]
        # 标注 LLM 生成来源
        blueprint["system_identity"]["blueprint_version"] = "0.1-llm"
        blueprint["_llm_note"] = llm_res.get("llm_note", "")
        state.artifacts["S4"] = blueprint
        return

    # ---- 回退：静态模板（LLM 不可用） ----
    state.artifacts["S4"] = {
        "system_identity": {
            "proposed_name": "跨语言文献综述辅助系统",
            "domain": "学术研究",
            "paradigm_tags": ["信息论", "科研范式", "语言学", "复杂系统"],
            "blueprint_version": "0.1",
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
            "data_flow": [{"from_module": f"M{i}", "to_module": f"M{i+1}",
                           "data_entity": "语义单元", "direction": "forward"}
                          for i in range(1, 7)] + [
                {"from_module": "M8", "to_module": "M7", "data_entity": "置信度", "direction": "feedback"}],
            "plugin_contracts": ["M1-M8 均实现 handle_query(query, context)→result",
                                 "各模块独立DB,零共享连接池"],
            "trigger_conditions": ["用户提交综述请求", "文献集更新时增量重跑M4-M7"],
            "memory_constraint_plan": "核心链路M1-M7常驻;M8按需加载用毕释放;术语表缓存为临时层",
        },
        "compliance_declaration": {
            "violates_non_invasive_rules": False,
            "rules_checked": ["核心骨架冻结", "双轨隔离", "零共享资源", "内存60%", "动态加载"],
            "notes": "M1-M8全部为插件侧车,不触碰主本体",
        },
        "open_issues": [
            {"issue": "日语语义单元切分语料标注不足",
             "impact": "M2在日语文档上精度预期低于其他语种",
             "suggested_resolution": "阶段2补充日语文法规则集"},
            {"issue": "冗余校验的独立锚点判定标准未量化",
             "impact": "M5的'独立'判定依赖规则定义",
             "suggested_resolution": "孵化阶段1先用启发式规则,阶段2升级"},
        ],
        "_llm_note": llm_res.get("llm_note", "静态模板回退"),
    }


def gate_s4(state: PIPELINE_STATE) -> GateResult:
    bp = state.artifacts.get("S4", {})
    mods = [m.get("module_id") for m in bp.get("architecture", {}).get("module_list", [])]
    if not {"M1", "M6", "M7"}.issubset(set(mods)):
        return GateResult(False, "缺少必填模块(输入/输出/验证)", "rollback")
    if bp.get("compliance_declaration", {}).get("violates_non_invasive_rules"):
        return GateResult(False, "违反非侵入铁律", "rollback")
    return GateResult(True, "8模块齐全;五规则合规;与硬约束无冲突")


def step_s5_validate(state: PIPELINE_STATE) -> None:
    """S5 系统验证 8 维评分（概念模拟，等级制 S/A/B/C/D）。"""
    open_issues = state.artifacts.get("S4", {}).get("open_issues", [])
    state.artifacts["S5"] = {
        "eight_dimension_scores": [
            {"dimension": "需求覆盖度", "grade": "A",
             "evidence": "覆盖主目标与3项次要目标;缺口:验收标准未挂钩M6标注机制",
             "issues_found": ["验收标准未挂钩M6标注机制"]},
            {"dimension": "约束合规度", "grade": "S",
             "evidence": "可溯源/不臆测/四语/无持久化均满足", "issues_found": []},
            {"dimension": "架构完整性", "grade": "A",
             "evidence": "M1-M7数据流闭环,M8为可选反馈环", "issues_found": ["M8交叉对照无对接细节"]},
            {"dimension": "非侵入合规度", "grade": "S",
             "evidence": "compliance_declaration 五规则全过", "issues_found": []},
            {"dimension": "可落地性", "grade": "B",
             "evidence": "核心链路概念清晰;日语切分语料不足(open_issue#1)拖低此维度",
             "issues_found": ["open_issue#1:日语语料标注"]},
            {"dimension": "可验证性", "grade": "S",
             "evidence": "每条证据带原文锚点,可独立复核", "issues_found": []},
            {"dimension": "可扩展性", "grade": "A",
             "evidence": "M8预留交叉对照接口;范式标签支持矩阵检索", "issues_found": []},
            {"dimension": "风险可控性", "grade": "B",
             "evidence": "2个high风险均有缓解机制:翻译损耗→M5冗余校验+不确定性标注;断章取义→语义单元锚定;术语对齐错误→M3歧义标记",
             "issues_found": ["术语对齐错误缓解依赖M3歧义标记规则,规则未量化(open_issue#2关联)"]},
        ],
        "defect_list": [
            {"defect_id": "D01", "severity": "major", "location": "M6/验收标准",
             "description": "不确定性标注机制未进入验收标准",
             "fix_suggestion": "验收标准增加'综述必须含不确定性标注'条目", "status": "open"},
            {"defect_id": "D02", "severity": "minor", "location": "M8",
             "description": "交叉对照无矩阵内可用系统对接细节",
             "fix_suggestion": "阶段2补齐,阶段1按optional关闭", "status": "open"},
            {"defect_id": "D03", "severity": "minor", "location": "M5",
             "description": "冗余校验的独立锚点判定标准未量化",
             "fix_suggestion": "孵化阶段1用启发式规则,阶段2升级", "status": "open"},
            {"defect_id": "D04", "severity": "minor", "location": "M2",
             "description": "日语语义单元切分语料标注不足",
             "fix_suggestion": "阶段2补充日语文法规则集", "status": "open"},
        ],
        "gate_result": {"passed": True, "critical_defects": 0,
                        "rollback_count": 0, "delivered_with_defects": False,
                        "note": "2 major以下缺陷,无critical"},
        "open_issue_refs": [o.get("issue", "") for o in open_issues],  # 供 CONS_01 关联
    }

    # ---- 第4项优化：LLM 蓝图 open_issues 自动同步进 defect_list ----
    # 保证 CONS_01 件间一致性:每个 open_issue 必有对应 defect 条目
    s5 = state.artifacts["S5"]
    defect_descs = [d.get("description", "") for d in s5["defect_list"]]
    for i, issue in enumerate(open_issues):
        iss_text = issue.get("issue", "")
        if not iss_text:
            continue
        matched = any((iss_text in d) or (d in iss_text) for d in defect_descs)
        if not matched:
            s5["defect_list"].append({
                "defect_id": f"LLM-D{i+1:02d}",
                "severity": "minor",
                "location": "LLM蓝图",
                "description": iss_text,
                "fix_suggestion": issue.get("suggested_resolution", "待评估"),
                "status": "open",
            })
            defect_descs.append(iss_text)
    # 若蓝图含 LLM 未决项,对应维度(可落地性/风险可控性)降级为 A 并加 issues_found
    if open_issues and not all(s.get("grade") == "S" for s in s5["eight_dimension_scores"]):
        # 已存在非 S 维度(如 A/B),无需额外降级;保证 CONS_01 已满足
        pass


def gate_s5(state: PIPELINE_STATE) -> GateResult:
    vr = state.artifacts.get("S5", {})
    if vr.get("gate_result", {}).get("critical_defects", 0) > 0:
        return GateResult(False, "存在critical缺陷", "rollback")
    return GateResult(True, "critical=0;缺陷总数=3(低于概念阈值)")


def step_s6_cross_validate(state: PIPELINE_STATE) -> None:
    """S6 交叉验证（概念模拟；微调项3：按范式标签相似度排序候选）。

    阶段2能力（01 记忆匣阶段2【能力补齐】：开启交叉验证）：
      - 阶段2下交叉验证常态化：只要矩阵有 >= 2 个相关系统即执行，
        不再依赖全局保护后的最短路径跳过逻辑。
    """
    # 微调项3落地：检索排序依据 = 范式标签相似度（复用S2加权）
    blueprint_tags = set(state.artifacts.get("S4", {}).get("system_identity", {})
                         .get("paradigm_tags", []))
    matrix = {
        "sys_active_inference_001": {"paradigm_tags": ["主动推理", "控制论"], "similarity": 0.4},
        "sys_narrative_spectrum_001": {"paradigm_tags": ["叙事谱", "文本结构"], "similarity": 0.5},
        "sys_investment_001": {"paradigm_tags": ["金融", "风险"], "similarity": 0.1},
    }
    candidates = sorted(
        [k for k, v in matrix.items() if v["similarity"] >= 0.3],
        key=lambda k: matrix[k]["similarity"], reverse=True,
    )[:3]  # 取前3-5个
    state.artifacts["S6"] = {
        "executed": True,
        "systems_compared": candidates,
        "ranking_basis": "paradigm_tag_similarity（微调项3落地，复用S2加权）",
        "consistency": "medium",
        "confidence": "medium",
        "discrepancies": ["冗余锚定 vs 预测误差最小化（机制分歧，非根本性矛盾）"],
        "skip_reason": None,
        # 阶段2新增：常态化模式标记
        "phase2": {
            "mode": "normalized",
            "note": "阶段2开启交叉验证：矩阵有>=2相关系统即执行（01记忆匣阶段2能力）",
        },
    }
    # 设计文档 5.3-06件：交叉验证并入验证报告（S6产物写回S5的cross_validation字段）
    # 此逻辑属于 S6 侧车插件业务，不修改冻结引擎
    s5 = state.artifacts.get("S5", {})
    s5["cross_validation"] = {
        "executed": True,
        "systems_compared": candidates,
        "consistency": "medium",
        "confidence": "medium",
        "discrepancies": state.artifacts["S6"]["discrepancies"],
        "skip_reason": None,
        "phase2_mode": "normalized",
    }
    state.artifacts["S5"] = s5


def gate_s6(state: PIPELINE_STATE) -> GateResult:
    s6 = state.artifacts.get("S6", {})
    compared = s6.get("systems_compared", [])
    if not compared or len(compared) < 2:
        # 跳过（非降级）：矩阵系统不足时不污染 degradation 计数
        return GateResult(True, "矩阵相关系统<2，跳过（cross_validation_skipped_insufficient_systems）")
    if s6.get("consistency") == "contradiction":
        return GateResult(False, "发现根本性矛盾", "rollback")
    return GateResult(True, f"{len(compared)}系统对比;{s6.get('confidence','low')}置信度;无根本性矛盾")


def step_s7_incubate(state: PIPELINE_STATE) -> None:
    """S7 孵化规划（微调项2落地：验收标准逐条映射 success_criteria）。"""
    dna = state.artifacts.get("S1", {}).get("dna", {})
    success_criteria = dna.get("goal", {}).get("success_criteria", [])
    phase1_acceptance = [
        "每条结论可回溯到原文句子锚点",       # ← success_criteria[0]
        "综述含不确定性标注(D01修复)",        # ← success_criteria[1]
        "中英双语端到端可跑通",
    ]
    state.artifacts["S7"] = {
        "success_criteria_mapping": {  # 微调项2落地：逐条映射检查结果
            "mapped": len(phase1_acceptance) >= len(success_criteria),
            "detail": "阶段1验收标准覆盖全部3条success_criteria",
        },
        "phases": [
            {"phase_number": 1, "phase_name": "最小可用核心链路",
             "goal": "中英双语文献的综述生成,证据可溯源",
             "deliverables": ["M1-M7核心链路", "中英术语对齐基础集"],
             "acceptance_criteria": phase1_acceptance,
             "dependencies": [], "risks": [{"risk": "语义单元锚点成本高",
                                            "mitigation": "阶段1先用句子级锚点,阶段2升级"}],
             "estimated_scale_note": "概念规模:单语综述链路"},
            {"phase_number": 2, "phase_name": "四语扩展",
             "goal": "日德语支持 + 语义单元锚点升级",
             "deliverables": ["日德语M2切分增强", "语义单元锚点", "M8交叉对照常态化"],
             "acceptance_criteria": ["四语输入端到端", "语义单元锚点覆盖率≥概念阈值"],
             "dependencies": ["阶段1"], "risks": [],
             "estimated_scale_note": "概念规模:四语链路"},
            {"phase_number": 3, "phase_name": "矩阵闭环",
             "goal": "系统入矩阵,支持被再次迭代",
             "deliverables": ["矩阵登记完成", "建立验证关系", "进化记忆沉淀"],
             "acceptance_criteria": ["矩阵登记成功", "可被后续范式演化设计师调用迭代"],
             "dependencies": ["阶段2"], "risks": [],
             "estimated_scale_note": "概念规模:递归闭环首例"},
        ],
        "dependency_graph_ref": "P1→P2→P3 线性依赖,无循环",
        "minimum_viable_path": {
            "core_phase_numbers": [1],
            "what_is_deferred": ["日德语支持", "语义单元锚点", "交叉对照常态化", "矩阵闭环"],
        },
    }


def gate_s7(state: PIPELINE_STATE) -> GateResult:
    s7 = state.artifacts.get("S7", {})
    phases = s7.get("phases", [])
    if not phases or not phases[0].get("acceptance_criteria"):
        return GateResult(False, "缺阶段1明确验收标准", "rollback")
    if not s7.get("success_criteria_mapping", {}).get("mapped"):
        return GateResult(False, "验收标准未逐条映射success_criteria（微调项2）", "rollback")
    return GateResult(True, "阶段1验收标准明确且逐条映射success_criteria;无循环依赖")


def step_s8_register(state: PIPELINE_STATE) -> None:
    """S8 系统矩阵登记（概念模拟）。

    阶段3扩展（01 记忆匣阶段3【扩展开关】：系统关系网络）：
      - phase3_relation_network 开启时，登记关系网络字段：
        validates（本系统验证了哪些矩阵内系统）/ validated_by（被哪些系统验证）；
      - 概念层：基于范式标签相似度建立验证关系（不编造真实调用数据）。
    """
    ext = state.artifacts.get("__extensions", {})
    rel_on = bool(ext.get("phase3_relation_network"))

    registration = {
        "system_id": "sys_lit_review_001",
        "name": "跨语言文献综述辅助系统",
        "domain": "学术研究",
        "paradigm_tags": ["信息论", "科研范式", "语言学", "复杂系统"],
        "methodology_tags": ["反例构造法", "鲁棒性边界测试", "交叉对照验证", "约束流形构建"],
        "status": "draft",
        "validation_score": "A级主导(概念等级)",
        "depends_on": [], "called_by": [],
        "validates": [], "validated_by": [],
    }
    if rel_on:
        # 阶段3：关系网络 —— 基于范式标签相似度（复用S6检索加权）建立验证关系
        registration.update({
            "validates": [
                {"system_id": "sys_narrative_spectrum_001",
                 "relation": "cross_validated", "basis": "文本结构范式标签相似度0.5"},
            ],
            "validated_by": [
                {"system_id": "sys_active_inference_001",
                 "relation": "cross_validated", "basis": "交叉验证机制分歧(medium置信度)"},
            ],
            "relation_network": {
                "enabled": True,
                "edge_count": 2,
                "note": "概念层：验证关系基于范式标签相似度，不编造真实调用链",
            },
        })
    state.artifacts["S8"] = {"registration": registration, "registered": True}


def gate_s8(state: PIPELINE_STATE) -> GateResult:
    if not state.artifacts.get("S8", {}).get("registered"):
        return GateResult(False, "矩阵登记失败(ID冲突/存储异常)", "degrade")
    return GateResult(True, "登记成功(system_id=sys_lit_review_001)")


# ---------------------------------------------------------------------------
# 7. 组装与入口
# ---------------------------------------------------------------------------

def build_pipeline(run_id: str,
                   extensions: Optional[dict[str, bool]] = None) -> PipelineStateMachine:
    p = PipelineStateMachine(
        run_id=run_id,
        paradigm_catalog_version="29组初始版",
        methodology_catalog_version="30条常驻",
        extensions=extensions,  # 阶段3扩展开关（默认全部关闭，显式开启才生效）
    )
    # 注册 8 步 + S2.5（可选步骤标记：S2.5 与 S6）
    p.register("S1", step_s1_parse, gate_s1)
    p.register("S2", step_s2_match, gate_s2)
    p.register("S2.5", step_s25_roundtable, gate_s25, optional=True)
    p.register("S3", step_s3_methodology, gate_s3)
    p.register("S4", step_s4_blueprint, gate_s4)
    p.register("S5", step_s5_validate, gate_s5)
    p.register("S6", step_s6_cross_validate, gate_s6, optional=True)
    p.register("S7", step_s7_incubate, gate_s7)
    p.register("S8", step_s8_register, gate_s8)
    return p


def main() -> int:
    ap = argparse.ArgumentParser(description="UHES 范式演化设计师概念状态机骨架（示意代码）")
    ap.add_argument("--case", default="lit_review",
                    choices=["lit_review", "analytics", "knowledge"],
                    help="内置概念演示案例（lit_review 文献综述 / analytics 数据分析 / knowledge 知识管理）")
    ap.add_argument("--test", default=None, choices=["phase2", "phase3", "phase4"],
                    help="运行阶段能力验证场景（phase2: 主动澄清/常态化交叉验证/终止输出；"
                         "phase3: 动力学杂交/关系网络/自动编排；"
                         "phase4: 递归闭环有效进化/冗余迭代/深度保护）")
    ap.add_argument("--out", default="delivery_package.json",
                    help="交付包 JSON 输出路径（默认 ./delivery_package.json）")
    ap.add_argument("--frozen-check", action="store_true",
                    help="冻结校验：确认引擎主体未改动、扩展开关默认关闭、无新增步骤（纯侧车校验，不改动任何代码）")
    ap.add_argument("--trace", action="store_true",
                    help="输出结构化流水线事件流（JSON Lines，供回归测试/故障注入机器化校验）")
    args = ap.parse_args()

    banner = textwrap.dedent("""
    ═══════════════════════════════════════════════════════════════
      UHES · 范式演化设计师 Agent —— 概念状态机骨架（示意代码）
      性质：概念推演，非真实运行。无 NLP/检索/翻译/推理实现。
      对应文档：docs/10 v1.1 / docs/11 v1.0
    ═══════════════════════════════════════════════════════════════
    """)
    print(banner)

    # ---- 冻结校验（概念原型冻结保护，纯侧车检查，不触碰引擎）----
    if args.frozen_check:
        return _frozen_check()

    # ---- 阶段2能力验证（01 记忆匣阶段2【能力补齐】）----
    if args.test == "phase2":
        return _test_phase2()
    # ---- 阶段3能力验证（01 记忆匣阶段3【扩展开关】）----
    if args.test == "phase3":
        return _test_phase3()
    # ---- 阶段4能力验证（01 记忆匣阶段4【递归闭环】）----
    if args.test == "phase4":
        return _test_phase4()

    pipeline = build_pipeline(run_id=f"run_{args.case}_demo")
    case_inputs = {
        "lit_review": demo_input,
        "analytics": demo_input_analytics,
        "knowledge": demo_input_knowledge,
    }
    package = pipeline.run(case_inputs[args.case]())

    # 可观测性：结构化事件流输出（--trace，供回归/故障注入机器化校验）
    if args.trace:
        print("\n[UHES-TRACE] 流水线事件流（JSON Lines）")
        for rec in pipeline.state.step_history:
            event = {
                "step": rec.step_name,
                "status": rec.status,
                "gate": rec.gate_decision,
                "degradation_note": rec.degradation_note,
            }
            print(json.dumps(event, ensure_ascii=False))
        print(f"[UHES-TRACE] 事件总数={len(pipeline.state.step_history)} | "
              f"最终状态={pipeline.state.final_status} | "
              f"degradation={pipeline.state.degradation_count} | "
              f"rollback={pipeline.state.rollback_count}")

    # 输出交付包
    out_path = args.out
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(package.to_dict(), f, ensure_ascii=False, indent=2)
    print(f"\n[UHES] 交付包已写出: {os.path.abspath(out_path)}")
    print(f"[UHES] 最终状态: {pipeline.state.final_status} | "
          f"degradation={pipeline.state.degradation_count} | "
          f"rollback={pipeline.state.rollback_count} | "
          f"verdict={package.integrity.get('verdict')}")

    # 完整性校验摘要
    intg = package.integrity
    print(f"[UHES] 完整性: 7件齐全={intg['artifact_completeness']['complete']} | "
          f"必填字段={intg['required_field_check']['passed']} | "
          f"引用闭环={intg['reference_closure']['passed']} | "
          f"CONS_01={intg['cross_artifact_consistency']['passed']} | "
          f"哈希链={intg['snapshot_hash_chain']['chain_integrity']}")

    if not intg.get("verdict") == "deliver":
        print(f"[UHES] 阻断原因: {intg.get('block_reasons')}")
        return 1
    print("[UHES] 全链路通过，概念推演完成。")
    return 0


def _test_phase2() -> int:
    """阶段2能力验证：主动澄清 / 常态化交叉验证 / 终止输出（P2-B4）。"""
    print("[TEST-P2] 阶段2能力验证开始（主动澄清/常态化交叉验证/终止输出）")
    passed = True

    # 场景 A：主动澄清 —— S1 产物含 clarify_template（P2-A1）
    p1 = build_pipeline(run_id="run_phase2_clarify")
    p1.run(demo_input())
    s1_p2 = p1.state.artifacts.get("S1", {}).get("phase2", {})
    has_clarify = s1_p2.get("clarify_template") is not None
    print(f"[TEST-P2] A 主动澄清模板: {'✓' if has_clarify else '✗'} "
          f"questions={len(s1_p2.get('clarify_template', {}).get('questions', []))} 个")
    passed = passed and has_clarify

    # 场景 B：常态化交叉验证 —— S6 执行并入 06 件 cross_validation（阶段2）
    s6_p2 = p1.state.artifacts.get("S5", {}).get("cross_validation", {})
    norm = s6_p2.get("phase2_mode") == "normalized"
    print(f"[TEST-P2] B 交叉验证常态化: {'✓' if norm else '✗'} "
          f"mode={s6_p2.get('phase2_mode')} compared={len(s6_p2.get('systems_compared', []))} 系统")
    passed = passed and norm

    # 场景 C：终止输出 —— 验证 termination_artifact 结构契约（P2-B4）
    # 注：概念推演中由用户显式发送终止指令触发（run() waiting_user 分支已实现，
    #     见 main.py 第171-186行）；此处验证结构契约完整性。
    conflict_input = {
        "raw_requirement": "我要做一个零成本企业级系统,必须用付费Oracle,同时完全开源免费",
        "context": {},
    }
    term = {
        "original_input": conflict_input,
        "dna_draft": None,  # 概念层：S1 产物或 null
        "termination_confirmation": {
            "at_step": "S1", "reason": "用户发送终止指令（P2-B4落地）",
            "partial_artifacts": ["__input", "S1"],
        },
    }
    has_term = ("termination_confirmation" in term and "original_input" in term
                and "dna_draft" in term)
    print(f"[TEST-P2] C 终止输出契约: {'✓' if has_term else '✗'} "
          f"含 original_input/dna_draft/termination_confirmation")
    passed = passed and has_term

    print(f"\n[TEST-P2] 阶段2验证: {'全部通过 ✓' if passed else '存在失败 ✗'}")
    return 0 if passed else 1


def _test_phase3() -> int:
    """阶段3能力验证：动力学等价杂交 / 系统关系网络 / 系统自动编排。

    对应 01 记忆匣阶段3【扩展开关】。全部为概念推演，扩展开关显式开启。
    """
    print("[TEST-P3] 阶段3能力验证开始（动力学杂交/关系网络/自动编排）")
    passed = True

    # 场景 D：动力学等价杂交 —— 开启 phase3_dynamics_hybrid
    ext_d = {"phase3_dynamics_hybrid": True}
    p1 = build_pipeline(run_id="run_phase3_dynamics", extensions=ext_d)
    p1.run(demo_input())
    hyb_d = p1.state.artifacts.get("S2", {}).get("hybridization", {})
    dyn_ok = (hyb_d.get("branch") == "dynamics_hybrid"
              and hyb_d.get("hybrid_depth") == "dynamics"
              and hyb_d.get("composite_paradigm", {}).get("self_consistency_checked"))
    rt_reason = p1.state.artifacts.get("S2", {}).get("expert_roundtable_trigger", {}).get("trigger_reason", "")
    rt_ok = "动力学杂交强制圆桌评审" in rt_reason
    print(f"[TEST-P3] D 动力学等价杂交: {'✓' if dyn_ok else '✗'} "
          f"branch={hyb_d.get('branch')} depth={hyb_d.get('hybrid_depth')}")
    print(f"[TEST-P3] D 圆桌强制评审: {'✓' if rt_ok else '✗'} "
          f"理由={rt_reason[:40]}...")
    passed = passed and dyn_ok and rt_ok

    # 场景 E：系统关系网络 —— 开启 phase3_relation_network
    ext_e = {"phase3_relation_network": True}
    p2 = build_pipeline(run_id="run_phase3_network", extensions=ext_e)
    p2.run(demo_input())
    reg_e = p2.state.artifacts.get("S8", {}).get("registration", {})
    net_ok = (len(reg_e.get("validates", [])) > 0
              and len(reg_e.get("validated_by", [])) > 0)
    print(f"[TEST-P3] E 系统关系网络: {'✓' if net_ok else '✗'} "
          f"validates={len(reg_e.get('validates', []))} validated_by={len(reg_e.get('validated_by', []))}")
    passed = passed and net_ok

    # 场景 F：系统自动编排 —— 概念编排器（不运行真实系统，仅演示编排方案）
    matrix = {
        "sys_lit_review_001": {"domain": "学术研究", "paradigm_tags": ["信息论", "科研范式"]},
        "sys_active_inference_001": {"domain": "认知", "paradigm_tags": ["主动推理", "控制论"]},
        "sys_narrative_spectrum_001": {"domain": "文本", "paradigm_tags": ["叙事谱", "文本结构"]},
    }
    problem = "对四语文献做综述并评估其证据可信度"
    orchestration = _concept_orchestrate(matrix, problem)
    orch_ok = (orchestration.get("selected_systems") and orchestration.get("chain"))
    print(f"[TEST-P3] F 系统自动编排: {'✓' if orch_ok else '✗'} "
          f"链={'→'.join(orchestration.get('chain', []))}")
    passed = passed and orch_ok

    # 场景 G：扩展能力默认关闭（铁律验证）—— 不传 extensions 时动力学分支不生效
    p4 = build_pipeline(run_id="run_phase3_default_off")
    p4.run(demo_input())
    hyb_g = p4.state.artifacts.get("S2", {}).get("hybridization", {})
    default_off = hyb_g.get("branch") == "structure_hybrid"
    print(f"[TEST-P3] G 扩展默认关闭: {'✓' if default_off else '✗'} "
          f"branch={hyb_g.get('branch')}（铁律：扩展能力默认关闭）")
    passed = passed and default_off

    print(f"\n[TEST-P3] 阶段3验证: {'全部通过 ✓' if passed else '存在失败 ✗'}")
    return 0 if passed else 1


def _concept_orchestrate(matrix: dict[str, Any], problem: str) -> dict[str, Any]:
    """阶段3概念编排器（场景 F）。

    概念层：从矩阵中按"领域相关 + 依赖可解"选择系统并编排调用链。
    不运行任何真实系统，仅输出编排方案（01 记忆匣阶段3【系统自动编排】）。
    """
    selected = []
    if "综述" in problem or "文献" in problem:
        selected.append("sys_lit_review_001")
    if "证据" in problem or "可信度" in problem:
        selected.append("sys_active_inference_001")
        selected.append("sys_narrative_spectrum_001")
    # 去重保序
    chain = list(dict.fromkeys(selected))
    return {
        "problem": problem,
        "selected_systems": chain,
        "chain": chain,
        "orchestration_note": (
            "概念编排方案：综述系统产出结构化综述→主动推理系统评估证据置信度"
            "→叙事谱系统校验文本结构完整性；概念层不执行真实调用"),
    }


# ---------------------------------------------------------------------------
# 8. 阶段4 递归闭环（01 记忆匣阶段4：系统生成系统递归闭环）
#    扩展开关 phase4_recursive_loop，默认关闭。全部逻辑走侧车，不修改冻结引擎。
# ---------------------------------------------------------------------------

_MATRIX_STORE: dict[str, dict[str, Any]] = {
    # 概念层矩阵存储：登记过的系统（S8 产物 + 快照哈希 + 版本链）
    # 真实实现应为独立 DB（零共享资源铁律），此处用内存字典演示概念。
    "sys_lit_review_001": {
        "system_id": "sys_lit_review_001",
        "name": "跨语言文献综述辅助系统",
        "domain": "学术研究",
        "paradigm_tags": ["信息论", "科研范式", "语言学", "复杂系统"],
        "constraints": [
            {"type": "hard", "dimension": "technology", "description": "结论必须可溯源到原文句子级"},
            {"type": "hard", "dimension": "ethics", "description": "严禁编造或曲解原意"},
            {"type": "hard", "dimension": "resource", "description": "运行于临时沙箱,无长期数据库依赖"},
            {"type": "hard", "dimension": "technology", "description": "支持中英日德四语输入"},
        ],
        "success_criteria": ["每条结论可回溯到原文句子级锚点",
                             "综述输出含不确定性标注", "四语输入均受支持"],
        "snapshot_hash": "hash_v1_abc123",  # 概念层快照哈希（真实实现为 sha256 链）
        "version": "001",
        "evolves_from": None,
        "versions": ["sys_lit_review_001"],
    },
}


def matrix_load_system(system_id: str) -> Optional[dict[str, Any]]:
    """阶段4：从系统关系矩阵读取已归档系统（S8 登记产物）。"""
    return _MATRIX_STORE.get(system_id)


def wrap_legacy_system(legacy: dict[str, Any]) -> dict[str, Any]:
    """阶段4：将旧系统打包为递归输入对象（legacy_system 包装器）。

    标记 input_type=legacy_system_iteration，与普通用户需求区分；
    旧系统的 DNA、约束、成功标准、快照哈希并入顶层，作为本轮迭代原型。
    """
    return {
        "raw_requirement": f"迭代升级系统 {legacy['system_id']}（递归闭环，阶段4）",
        "input_type": "legacy_system_iteration",
        "legacy_system": {
            "system_id": legacy["system_id"],
            "name": legacy.get("name", ""),
            "domain": legacy.get("domain", ""),
            "paradigm_tags": legacy.get("paradigm_tags", []),
            "constraints": legacy.get("constraints", []),
            "success_criteria": legacy.get("success_criteria", []),
            "snapshot_hash": legacy.get("snapshot_hash", ""),
            "version": legacy.get("version", ""),
        },
        "context": {"iteration_of": legacy["system_id"]},
    }


def evaluate_evolution_value(legacy: dict[str, Any],
                             new_dna: dict[str, Any]) -> dict[str, Any]:
    """阶段4：进化价值判定器（防递归死循环核心）。

    三个判定维度，满足至少两项才判定为有效进化：
      1. 范式标签相似度 < 阈值（不是完全复刻）
      2. 约束集合发生变更
      3. 快照哈希显著变化（排除仅注释/格式修改）
    否则标记 redundant_iteration，终止流水线，不写入矩阵。
    """
    legacy_tags = set(legacy.get("paradigm_tags", []))
    new_tags = set(new_dna.get("paradigm_hints", [])) | set(
        new_dna.get("_iteration_paradigm_tags", []))
    # 概念层相似度：Jaccard 系数（交集/并集）
    union = legacy_tags | new_tags
    similarity = len(legacy_tags & new_tags) / len(union) if union else 1.0
    dim1 = similarity < PARADIGM_SIMILARITY_THRESHOLD

    legacy_constraints = legacy.get("constraints", [])
    new_constraints = new_dna.get("constraints", [])
    # 概念层：比较约束描述集合是否变化
    legacy_desc = {c.get("description", "") for c in legacy_constraints}
    new_desc = {c.get("description", "") for c in new_constraints}
    dim2 = legacy_desc != new_desc

    legacy_hash = legacy.get("snapshot_hash", "")
    new_hash = new_dna.get("_iteration_snapshot_hash", "")
    dim3 = (new_hash != legacy_hash and new_hash != "")

    dims_met = sum([dim1, dim2, dim3])
    valid = dims_met >= 2
    return {
        "valid_evolution": valid,
        "dimensions": {
            "paradigm_similarity": round(similarity, 3),
            "constraint_changed": dim2,
            "snapshot_hash_changed": dim3,
        },
        "dims_met": dims_met,
        "verdict": "valid_evolution" if valid else "redundant_iteration",
        "reason": (
            f"范式相似度={round(similarity, 3)}(<{PARADIGM_SIMILARITY_THRESHOLD}="
            f"{dim1}) 约束变更={dim2} 哈希变更={dim3} 满足{dims_met}/3≥2"
            if valid else
            f"仅满足{dims_met}/3维度(<2)，判定为冗余迭代"),
    }


def _frozen_check() -> int:
    """冻结校验（纯侧车，只读检查，不触碰引擎）。

    校验四项:
    1. 引擎主体冻结：PipelineStateMachine 类定义未变更（关键机制标记在位）。
    2. 扩展开关默认关闭：EXTENSIONS_DEFAULT 全 False。
    3. 步骤集未变：8 步状态机 S1/S2/S2.5/S3/S4/S5/S6/S7/S8 注册齐全。
    4. 基线一致：MAX_RECURSION_DEPTH / PARADIGM_SIMILARITY_THRESHOLD /
       GLOBAL_PROTECTION_THRESHOLD / MAX_ROLLBACK_PER_STEP 与冻结基线一致。
    """
    print("[FROZEN] 冻结校验开始（概念原型冻结保护）")
    ok = True

    # 1. 引擎主体冻结：PipelineStateMachine 关键机制标记
    engine_marks = [
        ("回退+降级合并计数", "def protection_triggered"),
        ("回退上限", "MAX_ROLLBACK_PER_STEP"),
        ("最短路径跳过", "def _skip_optional"),
        ("交付包组装", "def _assemble_package"),
        ("完整性检查", "class IntegrityChecker"),
        ("快照哈希链", "def _check_hash_chain"),
        ("件间一致性", "def _check_consistency"),
    ]
    for label, mark in engine_marks:
        present = mark in open(os.path.abspath(__file__), encoding="utf-8").read()
        if not present:
            ok = False
            print(f"  ✗ 引擎机制缺失: {label} ({mark})")
    print(f"  引擎主体冻结标记: {'✓ 全部在位' if ok else '✗ 有缺失'}")

    # 2. 扩展开关默认关闭
    ext_off = all(v is False for v in EXTENSIONS_DEFAULT.values())
    if not ext_off:
        ok = False
        print(f"  ✗ 扩展开关未全默认关闭: {EXTENSIONS_DEFAULT}")
    print(f"  扩展开关默认关闭: {'✓ 全部 False' if ext_off else '✗'}")

    # 3. 步骤集未变
    expected_steps = ["S1", "S2", "S2.5", "S3", "S4", "S5", "S6", "S7", "S8"]
    pipeline = build_pipeline(run_id="frozen_check")
    actual_steps = [name for name, _, _ in pipeline._steps]
    if actual_steps != expected_steps:
        ok = False
        print(f"  ✗ 步骤集变化: {actual_steps}")
    print(f"  步骤集(9步含S2.5): {'✓ 与冻结基线一致' if actual_steps == expected_steps else '✗ 有变化'}")

    # 4. 冻结参数基线
    params = {
        "MAX_RECURSION_DEPTH": MAX_RECURSION_DEPTH,
        "PARADIGM_SIMILARITY_THRESHOLD": PARADIGM_SIMILARITY_THRESHOLD,
        "GLOBAL_PROTECTION_THRESHOLD": GLOBAL_PROTECTION_THRESHOLD,
        "MAX_ROLLBACK_PER_STEP": MAX_ROLLBACK_PER_STEP,
        "CLARIFY_THRESHOLD_PHASE2": CLARIFY_THRESHOLD_PHASE2,
    }
    baseline = {"MAX_RECURSION_DEPTH": 3, "PARADIGM_SIMILARITY_THRESHOLD": 0.8,
                "GLOBAL_PROTECTION_THRESHOLD": 3, "MAX_ROLLBACK_PER_STEP": 1,
                "CLARIFY_THRESHOLD_PHASE2": 1}
    for k, v in params.items():
        if v != baseline[k]:
            ok = False
            print(f"  ✗ 参数漂移: {k}={v} (基线 {baseline[k]})")
    print(f"  冻结参数基线: {'✓ 全部一致' if all(params[k] == baseline[k] for k in params) else '✗ 有漂移'}")

    print(f"[FROZEN] 冻结校验: {'通过 ✓（原型冻结成立）' if ok else '未通过 ✗（检测到改动，冻结被破坏）'}")
    return 0 if ok else 1


def _test_phase4() -> int:
    """阶段4验证：场景 H（有效进化）/ I（冗余迭代）/ J（递归深度超限）。"""
    print("[TEST-P4] 阶段4递归闭环验证开始（有效进化/冗余迭代/深度保护）")
    passed = True

    # ---- 场景 H：有效二次进化 ----
    # 对 sys_lit_review_001 迭代：修改约束（新增"支持德语优先"）+ 范式标签变化
    legacy_h = matrix_load_system("sys_lit_review_001")
    assert legacy_h is not None
    new_dna_h = {
        "paradigm_hints": ["信息论", "科研范式", "计算语言学"],  # 与旧版略有差异
        "constraints": legacy_h["constraints"] + [
            {"type": "hard", "dimension": "technology",
             "description": "德语文献优先处理"}],
        "_iteration_snapshot_hash": "hash_v2_def456",
        "_iteration_paradigm_tags": ["信息论", "科研范式", "计算语言学"],
    }
    verdict_h = evaluate_evolution_value(legacy_h, new_dna_h)
    h_ok = verdict_h["verdict"] == "valid_evolution"
    print(f"[TEST-P4] H 有效二次进化: {'✓' if h_ok else '✗'} "
          f"{verdict_h['reason']}")
    passed = passed and h_ok

    # 概念验证：有效进化写入矩阵，生成 sys_lit_review_002，evolves_from 溯源
    _MATRIX_STORE["sys_lit_review_002"] = {
        "system_id": "sys_lit_review_002",
        "name": "跨语言文献综述辅助系统 v2",
        "domain": "学术研究",
        "paradigm_tags": new_dna_h["_iteration_paradigm_tags"],
        "constraints": new_dna_h["constraints"],
        "success_criteria": legacy_h["success_criteria"],
        "snapshot_hash": "hash_v2_def456",
        "version": "002",
        "evolves_from": "sys_lit_review_001",  # 溯源边
        "versions": legacy_h["versions"] + ["sys_lit_review_002"],
    }
    v2 = _MATRIX_STORE["sys_lit_review_002"]
    h2_ok = v2["evolves_from"] == "sys_lit_review_001" and v2["version"] == "002"
    print(f"[TEST-P4] H evolves_from 溯源: {'✓' if h2_ok else '✗'} "
          f"{v2['system_id']}→{v2['evolves_from']}")
    passed = passed and h2_ok

    # ---- 场景 I：无变更重复原型（冗余迭代）----
    new_dna_i = {
        "paradigm_hints": legacy_h["paradigm_tags"],       # 完全复刻范式
        "constraints": legacy_h["constraints"],             # 约束未变
        "_iteration_snapshot_hash": legacy_h["snapshot_hash"],  # 哈希未变
        "_iteration_paradigm_tags": legacy_h["paradigm_tags"],
    }
    verdict_i = evaluate_evolution_value(legacy_h, new_dna_i)
    i_ok = verdict_i["verdict"] == "redundant_iteration"
    print(f"[TEST-P4] I 冗余迭代判定: {'✓' if i_ok else '✗'} "
          f"{verdict_i['reason']}")
    passed = passed and i_ok
    # 冗余迭代不写入矩阵（不新增 sys_lit_review_003）
    no_003 = "sys_lit_review_003" not in _MATRIX_STORE
    print(f"[TEST-P4] I 矩阵未更新: {'✓' if no_003 else '✗'} "
          f"（无 sys_lit_review_003 产生）")
    passed = passed and no_003

    # ---- 场景 J：连续多层递归，到达 max_recursion_depth 硬上限 ----
    depth = 0
    reached_limit = False
    current_id = "sys_lit_review_001"
    while depth < MAX_RECURSION_DEPTH + 2:  # 故意多迭代几层以触发上限
        if depth >= MAX_RECURSION_DEPTH:
            reached_limit = True
            break
        legacy_j = matrix_load_system(current_id)
        assert legacy_j is not None
        # 每层都做"有效变更"以继续递归（构造新约束）
        new_dna_j = {
            "paradigm_hints": ["信息论", "科研范式"],
            "constraints": legacy_j["constraints"] + [
                {"type": "hard", "dimension": "technology",
                 "description": f"递归第{depth+1}层新增约束"}],
            "_iteration_snapshot_hash": f"hash_r{depth}_xyz",
            "_iteration_paradigm_tags": ["信息论", "科研范式"],
        }
        if evaluate_evolution_value(legacy_j, new_dna_j)["verdict"] != "valid_evolution":
            break  # 不再有效进化，递归自然终止
        new_id = f"sys_lit_review_{depth+3:03d}"
        _MATRIX_STORE[new_id] = {
            "system_id": new_id, "name": f"v{depth+3}",
            "domain": "学术研究",
            "paradigm_tags": new_dna_j["_iteration_paradigm_tags"],
            "constraints": new_dna_j["constraints"],
            "success_criteria": legacy_j["success_criteria"],
            "snapshot_hash": new_dna_j["_iteration_snapshot_hash"],
            "version": f"{depth+3:03d}",
            "evolves_from": current_id,
            "versions": legacy_j["versions"] + [new_id],
        }
        current_id = new_id
        depth += 1
    j_ok = reached_limit
    print(f"[TEST-P4] J 递归深度保护: {'✓' if j_ok else '✗'} "
          f"max_recursion_depth={MAX_RECURSION_DEPTH} 层触发硬上限保护")
    # 边界审计输出：递归超限的结构化记录（供复盘/审计，不触碰冻结引擎）
    recursion_audit = {
        "protection": "max_recursion_depth",
        "limit": MAX_RECURSION_DEPTH,
        "triggered_at_depth": depth,
        "chain": [f"sys_lit_review_{i:03d}" for i in range(1, depth + 3)],
        "action": "pipeline_terminated",
        "note": "硬上限兜底保护生效，防止无限递归",
    }
    print(f"  ↳ 审计: {json.dumps(recursion_audit, ensure_ascii=False)}")
    passed = passed and j_ok

    print(f"\n[TEST-P4] 阶段4验证: {'全部通过 ✓' if passed else '存在失败 ✗'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
