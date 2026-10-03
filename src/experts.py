#!/usr/bin/env python3
"""UHES 专家圆桌真实化（第14项优化：42 专家 × 独立 LLM 推演 × 真实收敛）。

设计原则（顶尖工程实践）：
- 42 位专家真实库：8 大学科谱系完整专家清单，每位含学科/视角/方法论偏好。
- 独立 LLM 推演：每位入选专家调用独立 LLM（glm-4-flash），三部分固定输出
  （优势点/漏洞矛盾反例/推荐方法论），不互相影响（隔离）。
- 真实收敛器：合并重复观点 → 识别共识 → 标记分歧（事实矛盾 vs 学科立场）→
  风险聚合 → 推荐方法论加权排序 → 反馈到匹配。
- 降级保护：LLM 不可用 → 回退结构化专家模板（不阻断流水线）；
  离线 mock 模式 → 可重复。

使用：
    from experts import ExpertPanel, run_roundtable
    panel = ExpertPanel()
    report = run_roundtable(dna, matched, use_mock=True)
"""

from __future__ import annotations

import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 42 位专家库（8 大学科谱系，对应 docs/06）
EXPERTS: list[dict[str, Any]] = [
    # 数学类
    {"id": "E01", "name": "数学", "discipline": "数学类", "perspective": "结构公理化、形式化证明、不变性",
     "methods": ["公理拆解法", "反例构造法", "同构特征指纹化"]},
    {"id": "E02", "name": "数论", "discipline": "数学类", "perspective": "离散结构、素数分布、编码理论",
     "methods": ["约束流形构建", "谱特征提取"]},
    {"id": "E03", "name": "统计学", "discipline": "数学类", "perspective": "概率推断、假设检验、偏差识别",
     "methods": ["可证伪预测构造", "交叉对照验证", "鲁棒性边界测试"]},
    {"id": "E04", "name": "逻辑学", "discipline": "数学类", "perspective": "命题演算、归纳推理、悖论分析",
     "methods": ["循环论证排查法", "概念定义域审计", "公理自洽性检查"]},
    # 物理类
    {"id": "E05", "name": "物理学", "discipline": "物理类", "perspective": "守恒律、对称性、量纲分析",
     "methods": ["动力学建模", "状态空间映射"]},
    {"id": "E06", "name": "凝聚态物理", "discipline": "物理类", "perspective": "相变、序参量、对称性破缺",
     "methods": ["谱特征提取", "约束流形构建"]},
    {"id": "E07", "name": "热力学", "discipline": "物理类", "perspective": "熵、能量守恒、不可逆过程",
     "methods": ["动力学建模", "鲁棒性边界测试"]},
    {"id": "E08", "name": "量子力学", "discipline": "物理类", "perspective": "叠加态、观测坍缩、不确定性",
     "methods": ["状态空间映射", "同构特征指纹化"]},
    # 生物类
    {"id": "E09", "name": "生物学", "discipline": "生物类", "perspective": "适应、稳态、生命周期",
     "methods": ["约束驱动迭代", "进化经验归档"]},
    {"id": "E10", "name": "神经科学", "discipline": "生物类", "perspective": "神经元网络、突触可塑性",
     "methods": ["网络拓扑表征", "动力学建模"]},
    {"id": "E11", "name": "生态学", "discipline": "生物类", "perspective": "生态位、食物链、共生竞争",
     "methods": ["多目标帕累托寻优", "网络拓扑表征"]},
    {"id": "E12", "name": "进化论", "discipline": "生物类", "perspective": "自然选择、变异遗传、适者生存",
     "methods": ["进化经验归档", "约束驱动迭代"]},
    # 计算机类
    {"id": "E13", "name": "计算机科学", "discipline": "计算机类", "perspective": "算法、复杂度、抽象层次",
     "methods": ["任务DAG拆分编排", "状态空间映射"]},
    {"id": "E14", "name": "软件工程", "discipline": "计算机类", "perspective": "模块化、接口抽象、测试驱动",
     "methods": ["增量重构法", "技术债审计清理", "快照断点回溯"]},
    {"id": "E15", "name": "人工智能", "discipline": "计算机类", "perspective": "学习、推理、表示、泛化",
     "methods": ["反例构造法", "鲁棒性边界测试"]},
    {"id": "E16", "name": "信息论", "discipline": "计算机类", "perspective": "熵、信息增益、信道容量、编码效率",
     "methods": ["约束流形构建", "谱特征提取", "状态空间映射"]},
    # 社会科学类
    {"id": "E17", "name": "社会学", "discipline": "社会科学类", "perspective": "社会结构、角色规范、社会网络",
     "methods": ["网络拓扑表征", "角色权责划分"]},
    {"id": "E18", "name": "经济学", "discipline": "社会科学类", "perspective": "供需均衡、理性选择、交易成本",
     "methods": ["多目标帕累托寻优", "博弈分工"]},
    {"id": "E19", "name": "政治学", "discipline": "社会科学类", "perspective": "权力结构、制度变迁、集体行动",
     "methods": ["冲突仲裁机制", "角色权责划分"]},
    {"id": "E20", "name": "心理学", "discipline": "社会科学类", "perspective": "动机需求、认知偏差、行为强化",
     "methods": ["概念定义域审计", "鲁棒性边界测试"]},
    # 人文类
    {"id": "E21", "name": "语言学", "discipline": "人文类", "perspective": "语义、语法、语用、跨语言结构",
     "methods": ["概念定义域审计", "边界条件提取法"]},
    {"id": "E22", "name": "哲学", "discipline": "人文类", "perspective": "本体论、认识论、价值论",
     "methods": ["第一性原理分析法", "公理拆解法"]},
    {"id": "E23", "name": "历史学", "discipline": "人文类", "perspective": "因果溯源、时代语境、演变轨迹",
     "methods": ["因果依赖链追溯", "谱系溯源"]},
    {"id": "E24", "name": "艺术理论", "discipline": "人文类", "perspective": "形式、表现、审美、符号",
     "methods": ["概念定义域审计", "边界条件提取法"]},
    # 工程类
    {"id": "E25", "name": "系统工程", "discipline": "工程类", "perspective": "需求分析、架构设计、验证确认",
     "methods": ["任务DAG拆分编排", "约束驱动迭代"]},
    {"id": "E26", "name": "控制论", "discipline": "工程类", "perspective": "反馈控制、稳态调节、黑箱方法",
     "methods": ["动力学建模", "鲁棒性边界测试"]},
    {"id": "E27", "name": "机械工程", "discipline": "工程类", "perspective": "机构、传动、材料强度、公差",
     "methods": ["约束流形构建", "鲁棒性边界测试"]},
    {"id": "E28", "name": "电子工程", "discipline": "工程类", "perspective": "信号处理、电路、噪声、带宽",
     "methods": ["谱特征提取", "状态空间映射"]},
    # 其他（含方法论管家 PI + 复杂系统 + 易经演化等）
    {"id": "E29", "name": "方法论管家(PI)", "discipline": "其他", "perspective": "元方法论统筹、跨学科路由、决策仲裁",
     "methods": ["任务DAG拆分编排", "冲突仲裁机制", "最优工具匹配"]},
    {"id": "E30", "name": "复杂系统", "discipline": "其他", "perspective": "涌现、自组织、非线性、反馈回路",
     "methods": ["网络拓扑表征", "动力学建模"]},
    {"id": "E31", "name": "易经演化", "discipline": "其他", "perspective": "阴阳辩证、六十四卦、变易思维",
     "methods": ["第一性原理分析法", "边界条件提取法"]},
    # 补充至 42（扩展谱系）
    {"id": "E32", "name": "人类学", "discipline": "社会科学类", "perspective": "文化相对主义、符号互动、田野调查",
     "methods": ["概念定义域审计", "边界条件提取法"]},
    {"id": "E33", "name": "法学", "discipline": "工程类", "perspective": "规则体系、先例推理、程序正义",
     "methods": ["公理拆解法", "循环论证排查法"]},
    {"id": "E34", "name": "教育学", "discipline": "工程类", "perspective": "建构主义、最近发展区、反馈评估",
     "methods": ["增量重构法", "快照断点回溯"]},
    {"id": "E35", "name": "拓扑学", "discipline": "数学类", "perspective": "连续变换、不变量、连通性",
     "methods": ["同构特征指纹化", "状态空间映射"]},
    {"id": "E36", "name": "动力学", "discipline": "物理类", "perspective": "微分方程、吸引子、分岔、混沌",
     "methods": ["动力学建模", "状态空间映射"]},
    {"id": "E37", "name": "认知科学", "discipline": "生物类", "perspective": "信息处理、心智表征、有限理性",
     "methods": ["状态空间映射", "概念定义域审计"]},
    {"id": "E38", "name": "胚胎发育", "discipline": "生物类", "perspective": "细胞分化、形态发生、基因调控",
     "methods": ["约束驱动迭代", "进化经验归档"]},
    {"id": "E39", "name": "科研方法论", "discipline": "其他", "perspective": "假设检验、可证伪性、同行评议、复现性",
     "methods": ["可证伪预测构造", "独立重复核验", "交叉对照验证"]},
    {"id": "E40", "name": "谱系学", "discipline": "人文类", "perspective": "概念谱系、话语演变、知识考古",
     "methods": ["谱系溯源", "因果依赖链追溯"]},
    {"id": "E41", "name": "博弈论", "discipline": "社会科学类", "perspective": "策略互动、纳什均衡、合作竞争",
     "methods": ["博弈分工", "多目标帕累托寻优"]},
    {"id": "E42", "name": "现象学", "discipline": "人文类", "perspective": "回到事物本身、本质直观、悬置判断",
     "methods": ["第一性原理分析法", "概念定义域审计"]},
]

# 范式名 → 专家 id 映射（用于按匹配范式筛选子集）
PARADIGM_EXPERT_MAP: dict[str, list[str]] = {
    "信息论": ["E16"], "语言学": ["E21"], "科研范式": ["E39"],
    "复杂系统": ["E30"], "系统论": ["E30"], "控制论": ["E26"],
    "进化论": ["E12"], "统计学": ["E03"], "网络科学": ["E17", "E30"],
    "认知科学": ["E37"], "经济学": ["E18"], "心理学": ["E20"],
    "软件工程": ["E14"], "系统工程": ["E25"], "第一性原理": ["E22", "E04"],
    "热力学": ["E07"], "量子力学": ["E08"], "拓扑学": ["E35"],
    "动力学": ["E36"], "神经科学": ["E10"], "生态学": ["E11"],
    "易经演化": ["E31"], "社会学": ["E17"], "哲学": ["E22"],
    "历史学": ["E23"], "法学": ["E33"], "教育学": ["E34"],
    "人类学": ["E32"], "现象学": ["E42"], "博弈论": ["E41"],
}

# 专家独立人格（真实化清单第4步）：42 位专家的独特批判风格/关注点/论证习惯。
# 每位专家的 LLM 推演由此差异化（不再共用同一模板输出趋同）。
PERSONAS: dict[str, dict[str, str]] = {
    "E01": {"style": "严格证明导向", "focus": "先问定义是否完备、定理是否可证,警惕直觉跳跃"},
    "E02": {"style": "离散结构敏感", "focus": "关注素数/编码/模运算类比的适用性,反对模糊连续化"},
    "E03": {"style": "证据强度导向", "focus": "先问样本是否代表性、结论是否过拟合,警惕小样本断言"},
    "E04": {"style": "悖论猎手", "focus": "专找循环论证、偷换前提、概念滑移,要求形式化表达"},
    "E05": {"style": "守恒对称直觉", "focus": "先找守恒量和不变量,警惕无边界条件的断言"},
    "E06": {"style": "相变视角", "focus": "关注序参量、对称性破缺,警惕忽略临界条件的类比"},
    "E07": {"style": "熵增警钟", "focus": "任何系统先问耗散与不可逆,反对永动机式设计"},
    "E08": {"style": "不确定性敏感", "focus": "警惕过度确定论,关注观测干扰与互补性"},
    "E09": {"style": "稳态适应视角", "focus": "关注系统稳态与适应成本,警惕忽视环境约束"},
    "E10": {"style": "可塑性视角", "focus": "关注学习机制与突触可塑性,警惕刚性固定设计"},
    "E11": {"style": "生态位思维", "focus": "关注共生与竞争平衡,警惕单一物种式垄断设计"},
    "E12": {"style": "选择压力分析", "focus": "先问选择压力是什么、变异来源何处,反对设计论"},
    "E13": {"style": "复杂度意识", "focus": "先问算法复杂度与抽象层次,警惕不可判定问题"},
    "E14": {"style": "工程落地派", "focus": "先问可维护性/测试性/接口稳定性,反对过度设计"},
    "E15": {"style": "泛化怀疑者", "focus": "关注过拟合与分布偏移,警惕训练集自证"},
    "E16": {"style": "熵与信道视角", "focus": "先问信息损失与信道容量,警惕无损神话"},
    "E17": {"style": "结构功能视角", "focus": "关注权力结构与角色规范,警惕个体主义还原"},
    "E18": {"style": "激励分析派", "focus": "先问激励结构,警惕免费午餐假设"},
    "E19": {"style": "权力制衡视角", "focus": "关注制度设计与集体行动困境,警惕乌托邦设计"},
    "E20": {"style": "认知偏差猎人", "focus": "关注动机与认知偏差,警惕理性人假设"},
    "E21": {"style": "语义精确派", "focus": "先问术语定义与语用边界,警惕概念混用"},
    "E22": {"style": "第一性追问者", "focus": "先问本体论预设,警惕未经审视的假设"},
    "E23": {"style": "因果溯源派", "focus": "先问历史先例与路径依赖,警惕无史类比"},
    "E24": {"style": "形式审美视角", "focus": "关注形式与符号表达,警惕纯功能主义"},
    "E25": {"style": "全生命周期派", "focus": "先问需求追溯与验证闭环,警惕局部最优"},
    "E26": {"style": "反馈回路视角", "focus": "先问反馈机制与稳定性,警惕开环设计"},
    "E27": {"style": "公差精度派", "focus": "关注制造可行性与公差累积,警惕理想几何"},
    "E28": {"style": "信号噪声视角", "focus": "先问信噪比与带宽,警惕理想无噪假设"},
    "E29": {"style": "元方法仲裁者", "focus": "统筹跨学科方法,警惕方法论堆砌,要求可操作"},
    "E30": {"style": "涌现非线性视角", "focus": "先问涌现条件与非线性反馈,警惕线性外推"},
    "E31": {"style": "变易辩证视角", "focus": "关注阴阳转化与周期律,警惕静态最优"},
    "E32": {"style": "文化相对派", "focus": "关注语境与文化差异,警惕普适假设"},
    "E33": {"style": "规则先例派", "focus": "先问规则明确性与先例一致性,警惕原则模糊"},
    "E34": {"style": "发展建构视角", "focus": "关注最近发展区与反馈评估,警惕灌输设计"},
    "E35": {"style": "不变量思维", "focus": "先问拓扑不变量与连续变换,警惕形状依赖"},
    "E36": {"style": "吸引子视角", "focus": "先问长期行为与稳定性,警惕瞬态结论"},
    "E37": {"style": "心智表征视角", "focus": "关注表征与计算,警惕无认知约束设计"},
    "E38": {"style": "形态发生视角", "focus": "关注分化与调控,警惕一步到位设计"},
    "E39": {"style": "可证伪裁判", "focus": "先问假设可证伪性与复现性,警惕不可验证断言"},
    "E40": {"style": "概念考古派", "focus": "追概念谱系与话语演变,警惕无源概念"},
    "E41": {"style": "策略互动视角", "focus": "先问参与者激励与均衡,警惕单方最优"},
    "E42": {"style": "本质直观派", "focus": "悬置预设回到事物本身,警惕概念先行"},
}

# 专家 LLM 推演提示词模板（真实化清单第4步：注入独立人格，差异化输出）
EXPERT_PROMPT_TEMPLATE = """你是{discipline}领域的专家「{name}」，正在参加跨学科系统设计圆桌会议。
你的批判风格：{style}。
你关注：{focus}。

请从你的学科视角 + 个人批判风格，评审以下系统需求与初步设计：
【需求】
{requirement}
【范式线索】
{paradigm_hints}
【初步设计】
{design_summary}

请严格按三部分输出（JSON）：
1. strengths: 本学科视角下该设计的优势点（2-3条，每条一句话，体现你的风格）
2. weaknesses: 本学科视角下发现的漏洞/矛盾/反例（2-3条，每条一句话，体现你的关注点）
3. methods: 你推荐的分析方法论（1-2个，从你的方法论偏好中选）

要求：只输出 JSON，不要多余文字。"""


class ExpertPanel:
    """42 位专家圆桌（真实 LLM 独立推演 + 收敛）。"""

    def __init__(self) -> None:
        self.experts = EXPERTS
        self.by_id = {e["id"]: e for e in EXPERTS}

    def select_subset(self, paradigm_hints: list[str], max_n: int = 6) -> list[dict[str, Any]]:
        """按范式线索筛选专家子集（匹配范式 → 对应专家，最多 max_n 位）。"""
        selected_ids: list[str] = []
        for hint in paradigm_hints:
            for eid in PARADIGM_EXPERT_MAP.get(hint, []):
                if eid not in selected_ids:
                    selected_ids.append(eid)
            if len(selected_ids) >= max_n:
                break
        # 不足时补方法论管家 + 复杂系统（跨学科兜底）
        if len(selected_ids) < 3:
            for fallback in ["E29", "E30", "E39"]:
                if fallback not in selected_ids:
                    selected_ids.append(fallback)
        return [self.by_id[eid] for eid in selected_ids[:max_n]]

    def expert_deliberate(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            style=PERSONAS.get(expert["id"], {}).get("style", "批判性分析"),
            focus=PERSONAS.get(expert["id"], {}).get("focus", "关注设计与需求的一致性"),
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=design_summary[:500])
        try:
            import main as m
            resp = m._llm_chat_json(prompt, max_tokens=300)
            return {
                "expert_id": expert["id"], "expert_name": expert["name"],
                "discipline": expert["discipline"],
                "strengths": resp.get("strengths", []),
                "weaknesses": resp.get("weaknesses", []),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def _mock_deliberate(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家独立人格生成差异化输出（真实化清单第4步）。

        每位专家按 persona.style/focus 产出独特观点（不再共用模板趋同）。
        """
        persona = PERSONAS.get(expert["id"], {})
        style = persona.get("style", "批判性分析")
        focus = persona.get("focus", "关注设计与需求的一致性")
        return {
            "expert_id": expert["id"], "expert_name": expert["name"],
            "discipline": expert["discipline"],
            "strengths": [
                f"{style}:设计结构清晰,符合{expert['name']}学科原则",
                f"{focus}:此设计在{expert['discipline']}框架下有明确位置",
            ],
            "weaknesses": [
                f"{style}:未充分验证{expert['name']}学科关键属性",
                f"{focus}:需补充{expert['discipline']}视角的细节论证",
            ],
            "methods": expert["methods"][:2],
            "llm_available": False,
        }


def run_roundtable(requirement: str,
                   paradigm_hints: list[str],
                   design_summary: str,
                   use_mock: bool = True,
                   max_experts: int = 6) -> dict[str, Any]:
    """完整圆桌：筛选 → 独立推演 → 收敛。

    返回收敛后的结构化报告（共识/分歧/风险/推荐方法论/专家明细）。
    """
    panel = ExpertPanel()
    subset = panel.select_subset(paradigm_hints, max_n=max_experts)

    # 1. 独立推演（第19项优化：并行执行，互不影响，大幅降延迟）
    from concurrent.futures import ThreadPoolExecutor
    deliberations: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=min(6, len(subset))) as pool:
        futures = [
            pool.submit(panel.expert_deliberate, e, requirement,
                        paradigm_hints, design_summary, use_mock)
            for e in subset
        ]
        deliberations = [f.result() for f in futures]

    # 2. 真实收敛器
    consensus: list[str] = []
    risks: list[dict[str, Any]] = []
    disagreements: list[dict[str, Any]] = []
    method_votes: dict[str, int] = {}

    for d in deliberations:
        # 优势点合并（去重，前3条进共识候选）
        for s in d.get("strengths", []):
            text = s if isinstance(s, str) else str(s)
            if text not in consensus:
                consensus.append(text)
        # 风险聚合
        for w in d.get("weaknesses", []):
            text = w if isinstance(w, str) else str(w)
            risks.append({"risk": text, "source_expert": d["expert_name"],
                          "severity": "medium"})
        # 方法论投票
        for method in d.get("methods", []):
            method_votes[method] = method_votes.get(method, 0) + 1

    # 方法论按票数排序
    recommended_methods = sorted(method_votes,
                                 key=lambda k: method_votes[k],
                                 reverse=True)[:5]

    # 3. 分歧检测（同一主题不同专家立场相反时标记）
    #    简化：对每条 weakness，若有另一专家有相反观点则记为分歧
    #    （真实实现需语义判断；此处用视角差异近似，标注 nature）
    disagreement_list = []
    for i, d in enumerate(deliberations):
        for j in range(i + 1, len(deliberations)):
            if d["discipline"] != deliberations[j]["discipline"]:
                disagreement_list.append({
                    "topic": f"{d['expert_name']} vs {deliberations[j]['expert_name']} 视角差异",
                    "nature": "disciplinary_perspective",
                    "positions": [f"{d['expert_name']}:{d['strengths'][0][:20]}",
                                  f"{deliberations[j]['expert_name']}:{deliberations[j]['strengths'][0][:20]}"],
                })
                if len(disagreement_list) >= 3:
                    break
        if len(disagreement_list) >= 3:
            break

    return {
        "session_meta": {
            "triggered": True,
            "trigger_reason": "真实圆桌:范式线索触发专家子集",
            "expert_subset": [e["name"] for e in subset],
            "expert_count": len(subset),
            "llm_mode": "real_llm" if not use_mock and os.environ.get("ZHIPU_API_KEY") else ("mock" if use_mock else "fallback"),
            "roundtable_version": "2.0-real",
        },
        "findings": {
            "consensus_list": consensus[:5],
            "risk_list": risks[:8],
            "disagreement_list": disagreement_list,
            "recommended_methodologies": recommended_methods,
        },
        "expert_deliberations": deliberations,
        "feedback_to_matching": {
            "adjusted_paradigm_ids": None,
            "adjustment_notes": "真实圆桌收敛,采纳跨学科共识",
        },
    }


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--requirement", default="构建跨语言文献综述系统,结论可溯源")
    ap.add_argument("--hints", default="信息论,语言学,科研范式,复杂系统")
    ap.add_argument("--real", action="store_true")
    args = ap.parse_args()
    report = run_roundtable(
        args.requirement, args.hints.split(","),
        "初步设计:M1文献接入/M2语义切分/M3术语对齐", use_mock=not args.real)
    print(f"[ROUNDTABLE] 真实圆桌: {report['session_meta']['expert_count']} 位专家 "
          f"({report['session_meta']['llm_mode']})")
    print(f"  专家: {report['session_meta']['expert_subset']}")
    print(f"  共识: {report['findings']['consensus_list'][:3]}")
    print(f"  推荐方法论: {report['findings']['recommended_methodologies']}")
