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

# 专家 LLM 推演提示词模板（固定三部分输出）
EXPERT_PROMPT_TEMPLATE = """你是{discipline}领域的专家「{name}」，正在参加跨学科系统设计圆桌会议。
请从你的学科视角，评审以下系统需求与初步设计：

【需求】
{requirement}

【范式线索】
{paradigm_hints}

【初步设计】
{design_summary}

请严格按三部分输出（JSON）：
1. strengths: 本学科视角下该设计的优势点（2-3条，每条一句话）
2. weaknesses: 本学科视角下发现的漏洞/矛盾/反例（2-3条，每条一句话）
3. methods: 你推荐的分析方法论（1-2个，从你的方法论偏好中选）

要求：只输出 JSON，不要多余文字。"""


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_xǁExpertPanelǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁExpertPanelǁselect_subset__mutmut: MutantDict = {}  # type: ignore
mutants_xǁExpertPanelǁexpert_deliberate__mutmut: MutantDict = {}  # type: ignore
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut: MutantDict = {}  # type: ignore


class ExpertPanel:
    """42 位专家圆桌（真实 LLM 独立推演 + 收敛）。"""

    @_mutmut_mutated(mutants_xǁExpertPanelǁ__init____mutmut)
    def __init__(self) -> None:
        self.experts = EXPERTS
        self.by_id = {e["id"]: e for e in EXPERTS}

    def xǁExpertPanelǁ__init____mutmut_orig(self) -> None:
        self.experts = EXPERTS
        self.by_id = {e["id"]: e for e in EXPERTS}

    def xǁExpertPanelǁ__init____mutmut_1(self) -> None:
        self.experts = None
        self.by_id = {e["id"]: e for e in EXPERTS}

    def xǁExpertPanelǁ__init____mutmut_2(self) -> None:
        self.experts = EXPERTS
        self.by_id = None

    def xǁExpertPanelǁ__init____mutmut_3(self) -> None:
        self.experts = EXPERTS
        self.by_id = {e["XXidXX"]: e for e in EXPERTS}

    def xǁExpertPanelǁ__init____mutmut_4(self) -> None:
        self.experts = EXPERTS
        self.by_id = {e["ID"]: e for e in EXPERTS}

    @_mutmut_mutated(mutants_xǁExpertPanelǁselect_subset__mutmut)
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

    def xǁExpertPanelǁselect_subset__mutmut_orig(self, paradigm_hints: list[str], max_n: int = 6) -> list[dict[str, Any]]:
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

    def xǁExpertPanelǁselect_subset__mutmut_1(self, paradigm_hints: list[str], max_n: int = 7) -> list[dict[str, Any]]:
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

    def xǁExpertPanelǁselect_subset__mutmut_2(self, paradigm_hints: list[str], max_n: int = 6) -> list[dict[str, Any]]:
        """按范式线索筛选专家子集（匹配范式 → 对应专家，最多 max_n 位）。"""
        selected_ids: list[str] = None
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

    def xǁExpertPanelǁselect_subset__mutmut_3(self, paradigm_hints: list[str], max_n: int = 6) -> list[dict[str, Any]]:
        """按范式线索筛选专家子集（匹配范式 → 对应专家，最多 max_n 位）。"""
        selected_ids: list[str] = []
        for hint in paradigm_hints:
            for eid in PARADIGM_EXPERT_MAP.get(None, []):
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

    def xǁExpertPanelǁselect_subset__mutmut_4(self, paradigm_hints: list[str], max_n: int = 6) -> list[dict[str, Any]]:
        """按范式线索筛选专家子集（匹配范式 → 对应专家，最多 max_n 位）。"""
        selected_ids: list[str] = []
        for hint in paradigm_hints:
            for eid in PARADIGM_EXPERT_MAP.get(hint, None):
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

    def xǁExpertPanelǁselect_subset__mutmut_5(self, paradigm_hints: list[str], max_n: int = 6) -> list[dict[str, Any]]:
        """按范式线索筛选专家子集（匹配范式 → 对应专家，最多 max_n 位）。"""
        selected_ids: list[str] = []
        for hint in paradigm_hints:
            for eid in PARADIGM_EXPERT_MAP.get([]):
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

    def xǁExpertPanelǁselect_subset__mutmut_6(self, paradigm_hints: list[str], max_n: int = 6) -> list[dict[str, Any]]:
        """按范式线索筛选专家子集（匹配范式 → 对应专家，最多 max_n 位）。"""
        selected_ids: list[str] = []
        for hint in paradigm_hints:
            for eid in PARADIGM_EXPERT_MAP.get(hint, ):
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

    def xǁExpertPanelǁselect_subset__mutmut_7(self, paradigm_hints: list[str], max_n: int = 6) -> list[dict[str, Any]]:
        """按范式线索筛选专家子集（匹配范式 → 对应专家，最多 max_n 位）。"""
        selected_ids: list[str] = []
        for hint in paradigm_hints:
            for eid in PARADIGM_EXPERT_MAP.get(hint, []):
                if eid in selected_ids:
                    selected_ids.append(eid)
            if len(selected_ids) >= max_n:
                break
        # 不足时补方法论管家 + 复杂系统（跨学科兜底）
        if len(selected_ids) < 3:
            for fallback in ["E29", "E30", "E39"]:
                if fallback not in selected_ids:
                    selected_ids.append(fallback)
        return [self.by_id[eid] for eid in selected_ids[:max_n]]

    def xǁExpertPanelǁselect_subset__mutmut_8(self, paradigm_hints: list[str], max_n: int = 6) -> list[dict[str, Any]]:
        """按范式线索筛选专家子集（匹配范式 → 对应专家，最多 max_n 位）。"""
        selected_ids: list[str] = []
        for hint in paradigm_hints:
            for eid in PARADIGM_EXPERT_MAP.get(hint, []):
                if eid not in selected_ids:
                    selected_ids.append(None)
            if len(selected_ids) >= max_n:
                break
        # 不足时补方法论管家 + 复杂系统（跨学科兜底）
        if len(selected_ids) < 3:
            for fallback in ["E29", "E30", "E39"]:
                if fallback not in selected_ids:
                    selected_ids.append(fallback)
        return [self.by_id[eid] for eid in selected_ids[:max_n]]

    def xǁExpertPanelǁselect_subset__mutmut_9(self, paradigm_hints: list[str], max_n: int = 6) -> list[dict[str, Any]]:
        """按范式线索筛选专家子集（匹配范式 → 对应专家，最多 max_n 位）。"""
        selected_ids: list[str] = []
        for hint in paradigm_hints:
            for eid in PARADIGM_EXPERT_MAP.get(hint, []):
                if eid not in selected_ids:
                    selected_ids.append(eid)
            if len(selected_ids) > max_n:
                break
        # 不足时补方法论管家 + 复杂系统（跨学科兜底）
        if len(selected_ids) < 3:
            for fallback in ["E29", "E30", "E39"]:
                if fallback not in selected_ids:
                    selected_ids.append(fallback)
        return [self.by_id[eid] for eid in selected_ids[:max_n]]

    def xǁExpertPanelǁselect_subset__mutmut_10(self, paradigm_hints: list[str], max_n: int = 6) -> list[dict[str, Any]]:
        """按范式线索筛选专家子集（匹配范式 → 对应专家，最多 max_n 位）。"""
        selected_ids: list[str] = []
        for hint in paradigm_hints:
            for eid in PARADIGM_EXPERT_MAP.get(hint, []):
                if eid not in selected_ids:
                    selected_ids.append(eid)
            if len(selected_ids) >= max_n:
                return
        # 不足时补方法论管家 + 复杂系统（跨学科兜底）
        if len(selected_ids) < 3:
            for fallback in ["E29", "E30", "E39"]:
                if fallback not in selected_ids:
                    selected_ids.append(fallback)
        return [self.by_id[eid] for eid in selected_ids[:max_n]]

    def xǁExpertPanelǁselect_subset__mutmut_11(self, paradigm_hints: list[str], max_n: int = 6) -> list[dict[str, Any]]:
        """按范式线索筛选专家子集（匹配范式 → 对应专家，最多 max_n 位）。"""
        selected_ids: list[str] = []
        for hint in paradigm_hints:
            for eid in PARADIGM_EXPERT_MAP.get(hint, []):
                if eid not in selected_ids:
                    selected_ids.append(eid)
            if len(selected_ids) >= max_n:
                break
        # 不足时补方法论管家 + 复杂系统（跨学科兜底）
        if len(selected_ids) <= 3:
            for fallback in ["E29", "E30", "E39"]:
                if fallback not in selected_ids:
                    selected_ids.append(fallback)
        return [self.by_id[eid] for eid in selected_ids[:max_n]]

    def xǁExpertPanelǁselect_subset__mutmut_12(self, paradigm_hints: list[str], max_n: int = 6) -> list[dict[str, Any]]:
        """按范式线索筛选专家子集（匹配范式 → 对应专家，最多 max_n 位）。"""
        selected_ids: list[str] = []
        for hint in paradigm_hints:
            for eid in PARADIGM_EXPERT_MAP.get(hint, []):
                if eid not in selected_ids:
                    selected_ids.append(eid)
            if len(selected_ids) >= max_n:
                break
        # 不足时补方法论管家 + 复杂系统（跨学科兜底）
        if len(selected_ids) < 4:
            for fallback in ["E29", "E30", "E39"]:
                if fallback not in selected_ids:
                    selected_ids.append(fallback)
        return [self.by_id[eid] for eid in selected_ids[:max_n]]

    def xǁExpertPanelǁselect_subset__mutmut_13(self, paradigm_hints: list[str], max_n: int = 6) -> list[dict[str, Any]]:
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
            for fallback in ["XXE29XX", "E30", "E39"]:
                if fallback not in selected_ids:
                    selected_ids.append(fallback)
        return [self.by_id[eid] for eid in selected_ids[:max_n]]

    def xǁExpertPanelǁselect_subset__mutmut_14(self, paradigm_hints: list[str], max_n: int = 6) -> list[dict[str, Any]]:
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
            for fallback in ["e29", "E30", "E39"]:
                if fallback not in selected_ids:
                    selected_ids.append(fallback)
        return [self.by_id[eid] for eid in selected_ids[:max_n]]

    def xǁExpertPanelǁselect_subset__mutmut_15(self, paradigm_hints: list[str], max_n: int = 6) -> list[dict[str, Any]]:
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
            for fallback in ["E29", "XXE30XX", "E39"]:
                if fallback not in selected_ids:
                    selected_ids.append(fallback)
        return [self.by_id[eid] for eid in selected_ids[:max_n]]

    def xǁExpertPanelǁselect_subset__mutmut_16(self, paradigm_hints: list[str], max_n: int = 6) -> list[dict[str, Any]]:
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
            for fallback in ["E29", "e30", "E39"]:
                if fallback not in selected_ids:
                    selected_ids.append(fallback)
        return [self.by_id[eid] for eid in selected_ids[:max_n]]

    def xǁExpertPanelǁselect_subset__mutmut_17(self, paradigm_hints: list[str], max_n: int = 6) -> list[dict[str, Any]]:
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
            for fallback in ["E29", "E30", "XXE39XX"]:
                if fallback not in selected_ids:
                    selected_ids.append(fallback)
        return [self.by_id[eid] for eid in selected_ids[:max_n]]

    def xǁExpertPanelǁselect_subset__mutmut_18(self, paradigm_hints: list[str], max_n: int = 6) -> list[dict[str, Any]]:
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
            for fallback in ["E29", "E30", "e39"]:
                if fallback not in selected_ids:
                    selected_ids.append(fallback)
        return [self.by_id[eid] for eid in selected_ids[:max_n]]

    def xǁExpertPanelǁselect_subset__mutmut_19(self, paradigm_hints: list[str], max_n: int = 6) -> list[dict[str, Any]]:
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
                if fallback in selected_ids:
                    selected_ids.append(fallback)
        return [self.by_id[eid] for eid in selected_ids[:max_n]]

    def xǁExpertPanelǁselect_subset__mutmut_20(self, paradigm_hints: list[str], max_n: int = 6) -> list[dict[str, Any]]:
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
                    selected_ids.append(None)
        return [self.by_id[eid] for eid in selected_ids[:max_n]]

    @_mutmut_mutated(mutants_xǁExpertPanelǁexpert_deliberate__mutmut)
    def expert_deliberate(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_orig(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_1(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = False) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_2(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock and not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_3(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_4(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get(None):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_5(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("XXZHIPU_API_KEYXX"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_6(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("zhipu_api_key"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_7(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(None, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_8(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, None)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_9(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_10(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, )
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_11(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = None
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_12(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=None, name=expert["name"],
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_13(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=None,
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_14(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=None,
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_15(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints=None,
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_16(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=None)
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_17(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            name=expert["name"],
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_18(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], requirement=requirement[:500],
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_19(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_20(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_21(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            )
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_22(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["XXdisciplineXX"], name=expert["name"],
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_23(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["DISCIPLINE"], name=expert["name"],
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_24(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["XXnameXX"],
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_25(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["NAME"],
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_26(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:501],
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_27(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(None),
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_28(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="XX、XX".join(hints),
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_29(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=design_summary[:501])
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_30(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=design_summary[:500])
        try:
            import main as m
            resp = None
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_31(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=design_summary[:500])
        try:
            import main as m
            resp = m._llm_chat_json(None, max_tokens=300)
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_32(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=design_summary[:500])
        try:
            import main as m
            resp = m._llm_chat_json(prompt, max_tokens=None)
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_33(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=design_summary[:500])
        try:
            import main as m
            resp = m._llm_chat_json(max_tokens=300)
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_34(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=design_summary[:500])
        try:
            import main as m
            resp = m._llm_chat_json(prompt, )
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_35(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=design_summary[:500])
        try:
            import main as m
            resp = m._llm_chat_json(prompt, max_tokens=301)
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

    def xǁExpertPanelǁexpert_deliberate__mutmut_36(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=design_summary[:500])
        try:
            import main as m
            resp = m._llm_chat_json(prompt, max_tokens=300)
            return {
                "XXexpert_idXX": expert["id"], "expert_name": expert["name"],
                "discipline": expert["discipline"],
                "strengths": resp.get("strengths", []),
                "weaknesses": resp.get("weaknesses", []),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_37(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=design_summary[:500])
        try:
            import main as m
            resp = m._llm_chat_json(prompt, max_tokens=300)
            return {
                "EXPERT_ID": expert["id"], "expert_name": expert["name"],
                "discipline": expert["discipline"],
                "strengths": resp.get("strengths", []),
                "weaknesses": resp.get("weaknesses", []),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_38(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=design_summary[:500])
        try:
            import main as m
            resp = m._llm_chat_json(prompt, max_tokens=300)
            return {
                "expert_id": expert["XXidXX"], "expert_name": expert["name"],
                "discipline": expert["discipline"],
                "strengths": resp.get("strengths", []),
                "weaknesses": resp.get("weaknesses", []),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_39(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=design_summary[:500])
        try:
            import main as m
            resp = m._llm_chat_json(prompt, max_tokens=300)
            return {
                "expert_id": expert["ID"], "expert_name": expert["name"],
                "discipline": expert["discipline"],
                "strengths": resp.get("strengths", []),
                "weaknesses": resp.get("weaknesses", []),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_40(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=design_summary[:500])
        try:
            import main as m
            resp = m._llm_chat_json(prompt, max_tokens=300)
            return {
                "expert_id": expert["id"], "XXexpert_nameXX": expert["name"],
                "discipline": expert["discipline"],
                "strengths": resp.get("strengths", []),
                "weaknesses": resp.get("weaknesses", []),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_41(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=design_summary[:500])
        try:
            import main as m
            resp = m._llm_chat_json(prompt, max_tokens=300)
            return {
                "expert_id": expert["id"], "EXPERT_NAME": expert["name"],
                "discipline": expert["discipline"],
                "strengths": resp.get("strengths", []),
                "weaknesses": resp.get("weaknesses", []),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_42(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=design_summary[:500])
        try:
            import main as m
            resp = m._llm_chat_json(prompt, max_tokens=300)
            return {
                "expert_id": expert["id"], "expert_name": expert["XXnameXX"],
                "discipline": expert["discipline"],
                "strengths": resp.get("strengths", []),
                "weaknesses": resp.get("weaknesses", []),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_43(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=design_summary[:500])
        try:
            import main as m
            resp = m._llm_chat_json(prompt, max_tokens=300)
            return {
                "expert_id": expert["id"], "expert_name": expert["NAME"],
                "discipline": expert["discipline"],
                "strengths": resp.get("strengths", []),
                "weaknesses": resp.get("weaknesses", []),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_44(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=design_summary[:500])
        try:
            import main as m
            resp = m._llm_chat_json(prompt, max_tokens=300)
            return {
                "expert_id": expert["id"], "expert_name": expert["name"],
                "XXdisciplineXX": expert["discipline"],
                "strengths": resp.get("strengths", []),
                "weaknesses": resp.get("weaknesses", []),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_45(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=design_summary[:500])
        try:
            import main as m
            resp = m._llm_chat_json(prompt, max_tokens=300)
            return {
                "expert_id": expert["id"], "expert_name": expert["name"],
                "DISCIPLINE": expert["discipline"],
                "strengths": resp.get("strengths", []),
                "weaknesses": resp.get("weaknesses", []),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_46(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=design_summary[:500])
        try:
            import main as m
            resp = m._llm_chat_json(prompt, max_tokens=300)
            return {
                "expert_id": expert["id"], "expert_name": expert["name"],
                "discipline": expert["XXdisciplineXX"],
                "strengths": resp.get("strengths", []),
                "weaknesses": resp.get("weaknesses", []),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_47(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=design_summary[:500])
        try:
            import main as m
            resp = m._llm_chat_json(prompt, max_tokens=300)
            return {
                "expert_id": expert["id"], "expert_name": expert["name"],
                "discipline": expert["DISCIPLINE"],
                "strengths": resp.get("strengths", []),
                "weaknesses": resp.get("weaknesses", []),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_48(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=design_summary[:500])
        try:
            import main as m
            resp = m._llm_chat_json(prompt, max_tokens=300)
            return {
                "expert_id": expert["id"], "expert_name": expert["name"],
                "discipline": expert["discipline"],
                "XXstrengthsXX": resp.get("strengths", []),
                "weaknesses": resp.get("weaknesses", []),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_49(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=design_summary[:500])
        try:
            import main as m
            resp = m._llm_chat_json(prompt, max_tokens=300)
            return {
                "expert_id": expert["id"], "expert_name": expert["name"],
                "discipline": expert["discipline"],
                "STRENGTHS": resp.get("strengths", []),
                "weaknesses": resp.get("weaknesses", []),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_50(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=design_summary[:500])
        try:
            import main as m
            resp = m._llm_chat_json(prompt, max_tokens=300)
            return {
                "expert_id": expert["id"], "expert_name": expert["name"],
                "discipline": expert["discipline"],
                "strengths": resp.get(None, []),
                "weaknesses": resp.get("weaknesses", []),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_51(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=design_summary[:500])
        try:
            import main as m
            resp = m._llm_chat_json(prompt, max_tokens=300)
            return {
                "expert_id": expert["id"], "expert_name": expert["name"],
                "discipline": expert["discipline"],
                "strengths": resp.get("strengths", None),
                "weaknesses": resp.get("weaknesses", []),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_52(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=design_summary[:500])
        try:
            import main as m
            resp = m._llm_chat_json(prompt, max_tokens=300)
            return {
                "expert_id": expert["id"], "expert_name": expert["name"],
                "discipline": expert["discipline"],
                "strengths": resp.get([]),
                "weaknesses": resp.get("weaknesses", []),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_53(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=design_summary[:500])
        try:
            import main as m
            resp = m._llm_chat_json(prompt, max_tokens=300)
            return {
                "expert_id": expert["id"], "expert_name": expert["name"],
                "discipline": expert["discipline"],
                "strengths": resp.get("strengths", ),
                "weaknesses": resp.get("weaknesses", []),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_54(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=design_summary[:500])
        try:
            import main as m
            resp = m._llm_chat_json(prompt, max_tokens=300)
            return {
                "expert_id": expert["id"], "expert_name": expert["name"],
                "discipline": expert["discipline"],
                "strengths": resp.get("XXstrengthsXX", []),
                "weaknesses": resp.get("weaknesses", []),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_55(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
            requirement=requirement[:500],
            paradigm_hints="、".join(hints),
            design_summary=design_summary[:500])
        try:
            import main as m
            resp = m._llm_chat_json(prompt, max_tokens=300)
            return {
                "expert_id": expert["id"], "expert_name": expert["name"],
                "discipline": expert["discipline"],
                "strengths": resp.get("STRENGTHS", []),
                "weaknesses": resp.get("weaknesses", []),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_56(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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
                "XXweaknessesXX": resp.get("weaknesses", []),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_57(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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
                "WEAKNESSES": resp.get("weaknesses", []),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_58(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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
                "weaknesses": resp.get(None, []),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_59(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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
                "weaknesses": resp.get("weaknesses", None),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_60(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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
                "weaknesses": resp.get([]),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_61(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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
                "weaknesses": resp.get("weaknesses", ),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_62(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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
                "weaknesses": resp.get("XXweaknessesXX", []),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_63(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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
                "weaknesses": resp.get("WEAKNESSES", []),
                "methods": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_64(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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
                "XXmethodsXX": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_65(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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
                "METHODS": resp.get("methods", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_66(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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
                "methods": resp.get(None, []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_67(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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
                "methods": resp.get("methods", None),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_68(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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
                "methods": resp.get([]),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_69(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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
                "methods": resp.get("methods", ),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_70(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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
                "methods": resp.get("XXmethodsXX", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_71(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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
                "methods": resp.get("METHODS", []),
                "llm_available": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_72(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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
                "XXllm_availableXX": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_73(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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
                "LLM_AVAILABLE": True,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_74(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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
                "llm_available": False,
            }
        except Exception:
            return self._mock_deliberate(expert, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_75(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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
            return self._mock_deliberate(None, design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_76(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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
            return self._mock_deliberate(expert, None)

    def xǁExpertPanelǁexpert_deliberate__mutmut_77(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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
            return self._mock_deliberate(design_summary)

    def xǁExpertPanelǁexpert_deliberate__mutmut_78(self, expert: dict[str, Any],
                          requirement: str, hints: list[str],
                          design_summary: str,
                          use_mock: bool = True) -> dict[str, Any]:
        """单个专家独立 LLM 推演（隔离调用，互不影响）。"""
        if use_mock or not os.environ.get("ZHIPU_API_KEY"):
            return self._mock_deliberate(expert, design_summary)
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=expert["discipline"], name=expert["name"],
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
            return self._mock_deliberate(expert, )

    @_mutmut_mutated(mutants_xǁExpertPanelǁ_mock_deliberate__mutmut)
    def _mock_deliberate(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "expert_id": expert["id"], "expert_name": expert["name"],
            "discipline": expert["discipline"],
            "strengths": [f"{expert['perspective']}视角:设计结构清晰"],
            "weaknesses": [f"{expert['perspective']}视角:需补充细节验证"],
            "methods": expert["methods"][:2],
            "llm_available": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_orig(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "expert_id": expert["id"], "expert_name": expert["name"],
            "discipline": expert["discipline"],
            "strengths": [f"{expert['perspective']}视角:设计结构清晰"],
            "weaknesses": [f"{expert['perspective']}视角:需补充细节验证"],
            "methods": expert["methods"][:2],
            "llm_available": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_1(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "XXexpert_idXX": expert["id"], "expert_name": expert["name"],
            "discipline": expert["discipline"],
            "strengths": [f"{expert['perspective']}视角:设计结构清晰"],
            "weaknesses": [f"{expert['perspective']}视角:需补充细节验证"],
            "methods": expert["methods"][:2],
            "llm_available": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_2(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "EXPERT_ID": expert["id"], "expert_name": expert["name"],
            "discipline": expert["discipline"],
            "strengths": [f"{expert['perspective']}视角:设计结构清晰"],
            "weaknesses": [f"{expert['perspective']}视角:需补充细节验证"],
            "methods": expert["methods"][:2],
            "llm_available": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_3(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "expert_id": expert["XXidXX"], "expert_name": expert["name"],
            "discipline": expert["discipline"],
            "strengths": [f"{expert['perspective']}视角:设计结构清晰"],
            "weaknesses": [f"{expert['perspective']}视角:需补充细节验证"],
            "methods": expert["methods"][:2],
            "llm_available": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_4(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "expert_id": expert["ID"], "expert_name": expert["name"],
            "discipline": expert["discipline"],
            "strengths": [f"{expert['perspective']}视角:设计结构清晰"],
            "weaknesses": [f"{expert['perspective']}视角:需补充细节验证"],
            "methods": expert["methods"][:2],
            "llm_available": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_5(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "expert_id": expert["id"], "XXexpert_nameXX": expert["name"],
            "discipline": expert["discipline"],
            "strengths": [f"{expert['perspective']}视角:设计结构清晰"],
            "weaknesses": [f"{expert['perspective']}视角:需补充细节验证"],
            "methods": expert["methods"][:2],
            "llm_available": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_6(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "expert_id": expert["id"], "EXPERT_NAME": expert["name"],
            "discipline": expert["discipline"],
            "strengths": [f"{expert['perspective']}视角:设计结构清晰"],
            "weaknesses": [f"{expert['perspective']}视角:需补充细节验证"],
            "methods": expert["methods"][:2],
            "llm_available": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_7(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "expert_id": expert["id"], "expert_name": expert["XXnameXX"],
            "discipline": expert["discipline"],
            "strengths": [f"{expert['perspective']}视角:设计结构清晰"],
            "weaknesses": [f"{expert['perspective']}视角:需补充细节验证"],
            "methods": expert["methods"][:2],
            "llm_available": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_8(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "expert_id": expert["id"], "expert_name": expert["NAME"],
            "discipline": expert["discipline"],
            "strengths": [f"{expert['perspective']}视角:设计结构清晰"],
            "weaknesses": [f"{expert['perspective']}视角:需补充细节验证"],
            "methods": expert["methods"][:2],
            "llm_available": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_9(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "expert_id": expert["id"], "expert_name": expert["name"],
            "XXdisciplineXX": expert["discipline"],
            "strengths": [f"{expert['perspective']}视角:设计结构清晰"],
            "weaknesses": [f"{expert['perspective']}视角:需补充细节验证"],
            "methods": expert["methods"][:2],
            "llm_available": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_10(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "expert_id": expert["id"], "expert_name": expert["name"],
            "DISCIPLINE": expert["discipline"],
            "strengths": [f"{expert['perspective']}视角:设计结构清晰"],
            "weaknesses": [f"{expert['perspective']}视角:需补充细节验证"],
            "methods": expert["methods"][:2],
            "llm_available": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_11(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "expert_id": expert["id"], "expert_name": expert["name"],
            "discipline": expert["XXdisciplineXX"],
            "strengths": [f"{expert['perspective']}视角:设计结构清晰"],
            "weaknesses": [f"{expert['perspective']}视角:需补充细节验证"],
            "methods": expert["methods"][:2],
            "llm_available": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_12(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "expert_id": expert["id"], "expert_name": expert["name"],
            "discipline": expert["DISCIPLINE"],
            "strengths": [f"{expert['perspective']}视角:设计结构清晰"],
            "weaknesses": [f"{expert['perspective']}视角:需补充细节验证"],
            "methods": expert["methods"][:2],
            "llm_available": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_13(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "expert_id": expert["id"], "expert_name": expert["name"],
            "discipline": expert["discipline"],
            "XXstrengthsXX": [f"{expert['perspective']}视角:设计结构清晰"],
            "weaknesses": [f"{expert['perspective']}视角:需补充细节验证"],
            "methods": expert["methods"][:2],
            "llm_available": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_14(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "expert_id": expert["id"], "expert_name": expert["name"],
            "discipline": expert["discipline"],
            "STRENGTHS": [f"{expert['perspective']}视角:设计结构清晰"],
            "weaknesses": [f"{expert['perspective']}视角:需补充细节验证"],
            "methods": expert["methods"][:2],
            "llm_available": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_15(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "expert_id": expert["id"], "expert_name": expert["name"],
            "discipline": expert["discipline"],
            "strengths": [f"{expert['XXperspectiveXX']}视角:设计结构清晰"],
            "weaknesses": [f"{expert['perspective']}视角:需补充细节验证"],
            "methods": expert["methods"][:2],
            "llm_available": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_16(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "expert_id": expert["id"], "expert_name": expert["name"],
            "discipline": expert["discipline"],
            "strengths": [f"{expert['PERSPECTIVE']}视角:设计结构清晰"],
            "weaknesses": [f"{expert['perspective']}视角:需补充细节验证"],
            "methods": expert["methods"][:2],
            "llm_available": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_17(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "expert_id": expert["id"], "expert_name": expert["name"],
            "discipline": expert["discipline"],
            "strengths": [f"{expert['perspective']}视角:设计结构清晰"],
            "XXweaknessesXX": [f"{expert['perspective']}视角:需补充细节验证"],
            "methods": expert["methods"][:2],
            "llm_available": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_18(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "expert_id": expert["id"], "expert_name": expert["name"],
            "discipline": expert["discipline"],
            "strengths": [f"{expert['perspective']}视角:设计结构清晰"],
            "WEAKNESSES": [f"{expert['perspective']}视角:需补充细节验证"],
            "methods": expert["methods"][:2],
            "llm_available": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_19(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "expert_id": expert["id"], "expert_name": expert["name"],
            "discipline": expert["discipline"],
            "strengths": [f"{expert['perspective']}视角:设计结构清晰"],
            "weaknesses": [f"{expert['XXperspectiveXX']}视角:需补充细节验证"],
            "methods": expert["methods"][:2],
            "llm_available": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_20(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "expert_id": expert["id"], "expert_name": expert["name"],
            "discipline": expert["discipline"],
            "strengths": [f"{expert['perspective']}视角:设计结构清晰"],
            "weaknesses": [f"{expert['PERSPECTIVE']}视角:需补充细节验证"],
            "methods": expert["methods"][:2],
            "llm_available": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_21(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "expert_id": expert["id"], "expert_name": expert["name"],
            "discipline": expert["discipline"],
            "strengths": [f"{expert['perspective']}视角:设计结构清晰"],
            "weaknesses": [f"{expert['perspective']}视角:需补充细节验证"],
            "XXmethodsXX": expert["methods"][:2],
            "llm_available": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_22(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "expert_id": expert["id"], "expert_name": expert["name"],
            "discipline": expert["discipline"],
            "strengths": [f"{expert['perspective']}视角:设计结构清晰"],
            "weaknesses": [f"{expert['perspective']}视角:需补充细节验证"],
            "METHODS": expert["methods"][:2],
            "llm_available": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_23(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "expert_id": expert["id"], "expert_name": expert["name"],
            "discipline": expert["discipline"],
            "strengths": [f"{expert['perspective']}视角:设计结构清晰"],
            "weaknesses": [f"{expert['perspective']}视角:需补充细节验证"],
            "methods": expert["XXmethodsXX"][:2],
            "llm_available": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_24(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "expert_id": expert["id"], "expert_name": expert["name"],
            "discipline": expert["discipline"],
            "strengths": [f"{expert['perspective']}视角:设计结构清晰"],
            "weaknesses": [f"{expert['perspective']}视角:需补充细节验证"],
            "methods": expert["METHODS"][:2],
            "llm_available": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_25(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "expert_id": expert["id"], "expert_name": expert["name"],
            "discipline": expert["discipline"],
            "strengths": [f"{expert['perspective']}视角:设计结构清晰"],
            "weaknesses": [f"{expert['perspective']}视角:需补充细节验证"],
            "methods": expert["methods"][:3],
            "llm_available": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_26(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "expert_id": expert["id"], "expert_name": expert["name"],
            "discipline": expert["discipline"],
            "strengths": [f"{expert['perspective']}视角:设计结构清晰"],
            "weaknesses": [f"{expert['perspective']}视角:需补充细节验证"],
            "methods": expert["methods"][:2],
            "XXllm_availableXX": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_27(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "expert_id": expert["id"], "expert_name": expert["name"],
            "discipline": expert["discipline"],
            "strengths": [f"{expert['perspective']}视角:设计结构清晰"],
            "weaknesses": [f"{expert['perspective']}视角:需补充细节验证"],
            "methods": expert["methods"][:2],
            "LLM_AVAILABLE": False,
        }

    def xǁExpertPanelǁ_mock_deliberate__mutmut_28(self, expert: dict[str, Any],
                         design_summary: str) -> dict[str, Any]:
        """离线降级：基于专家视角模板生成结构化输出（可重复）。"""
        return {
            "expert_id": expert["id"], "expert_name": expert["name"],
            "discipline": expert["discipline"],
            "strengths": [f"{expert['perspective']}视角:设计结构清晰"],
            "weaknesses": [f"{expert['perspective']}视角:需补充细节验证"],
            "methods": expert["methods"][:2],
            "llm_available": True,
        }

mutants_xǁExpertPanelǁ__init____mutmut['_mutmut_orig'] = ExpertPanel.xǁExpertPanelǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ__init____mutmut['xǁExpertPanelǁ__init____mutmut_1'] = ExpertPanel.xǁExpertPanelǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ__init____mutmut['xǁExpertPanelǁ__init____mutmut_2'] = ExpertPanel.xǁExpertPanelǁ__init____mutmut_2 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ__init____mutmut['xǁExpertPanelǁ__init____mutmut_3'] = ExpertPanel.xǁExpertPanelǁ__init____mutmut_3 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ__init____mutmut['xǁExpertPanelǁ__init____mutmut_4'] = ExpertPanel.xǁExpertPanelǁ__init____mutmut_4 # type: ignore # mutmut generated

mutants_xǁExpertPanelǁselect_subset__mutmut['_mutmut_orig'] = ExpertPanel.xǁExpertPanelǁselect_subset__mutmut_orig # type: ignore # mutmut generated
mutants_xǁExpertPanelǁselect_subset__mutmut['xǁExpertPanelǁselect_subset__mutmut_1'] = ExpertPanel.xǁExpertPanelǁselect_subset__mutmut_1 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁselect_subset__mutmut['xǁExpertPanelǁselect_subset__mutmut_2'] = ExpertPanel.xǁExpertPanelǁselect_subset__mutmut_2 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁselect_subset__mutmut['xǁExpertPanelǁselect_subset__mutmut_3'] = ExpertPanel.xǁExpertPanelǁselect_subset__mutmut_3 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁselect_subset__mutmut['xǁExpertPanelǁselect_subset__mutmut_4'] = ExpertPanel.xǁExpertPanelǁselect_subset__mutmut_4 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁselect_subset__mutmut['xǁExpertPanelǁselect_subset__mutmut_5'] = ExpertPanel.xǁExpertPanelǁselect_subset__mutmut_5 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁselect_subset__mutmut['xǁExpertPanelǁselect_subset__mutmut_6'] = ExpertPanel.xǁExpertPanelǁselect_subset__mutmut_6 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁselect_subset__mutmut['xǁExpertPanelǁselect_subset__mutmut_7'] = ExpertPanel.xǁExpertPanelǁselect_subset__mutmut_7 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁselect_subset__mutmut['xǁExpertPanelǁselect_subset__mutmut_8'] = ExpertPanel.xǁExpertPanelǁselect_subset__mutmut_8 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁselect_subset__mutmut['xǁExpertPanelǁselect_subset__mutmut_9'] = ExpertPanel.xǁExpertPanelǁselect_subset__mutmut_9 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁselect_subset__mutmut['xǁExpertPanelǁselect_subset__mutmut_10'] = ExpertPanel.xǁExpertPanelǁselect_subset__mutmut_10 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁselect_subset__mutmut['xǁExpertPanelǁselect_subset__mutmut_11'] = ExpertPanel.xǁExpertPanelǁselect_subset__mutmut_11 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁselect_subset__mutmut['xǁExpertPanelǁselect_subset__mutmut_12'] = ExpertPanel.xǁExpertPanelǁselect_subset__mutmut_12 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁselect_subset__mutmut['xǁExpertPanelǁselect_subset__mutmut_13'] = ExpertPanel.xǁExpertPanelǁselect_subset__mutmut_13 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁselect_subset__mutmut['xǁExpertPanelǁselect_subset__mutmut_14'] = ExpertPanel.xǁExpertPanelǁselect_subset__mutmut_14 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁselect_subset__mutmut['xǁExpertPanelǁselect_subset__mutmut_15'] = ExpertPanel.xǁExpertPanelǁselect_subset__mutmut_15 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁselect_subset__mutmut['xǁExpertPanelǁselect_subset__mutmut_16'] = ExpertPanel.xǁExpertPanelǁselect_subset__mutmut_16 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁselect_subset__mutmut['xǁExpertPanelǁselect_subset__mutmut_17'] = ExpertPanel.xǁExpertPanelǁselect_subset__mutmut_17 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁselect_subset__mutmut['xǁExpertPanelǁselect_subset__mutmut_18'] = ExpertPanel.xǁExpertPanelǁselect_subset__mutmut_18 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁselect_subset__mutmut['xǁExpertPanelǁselect_subset__mutmut_19'] = ExpertPanel.xǁExpertPanelǁselect_subset__mutmut_19 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁselect_subset__mutmut['xǁExpertPanelǁselect_subset__mutmut_20'] = ExpertPanel.xǁExpertPanelǁselect_subset__mutmut_20 # type: ignore # mutmut generated

mutants_xǁExpertPanelǁexpert_deliberate__mutmut['_mutmut_orig'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_orig # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_1'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_1 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_2'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_2 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_3'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_3 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_4'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_4 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_5'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_5 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_6'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_6 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_7'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_7 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_8'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_8 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_9'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_9 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_10'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_10 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_11'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_11 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_12'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_12 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_13'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_13 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_14'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_14 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_15'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_15 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_16'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_16 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_17'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_17 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_18'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_18 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_19'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_19 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_20'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_20 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_21'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_21 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_22'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_22 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_23'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_23 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_24'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_24 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_25'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_25 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_26'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_26 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_27'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_27 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_28'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_28 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_29'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_29 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_30'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_30 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_31'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_31 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_32'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_32 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_33'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_33 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_34'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_34 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_35'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_35 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_36'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_36 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_37'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_37 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_38'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_38 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_39'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_39 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_40'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_40 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_41'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_41 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_42'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_42 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_43'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_43 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_44'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_44 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_45'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_45 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_46'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_46 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_47'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_47 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_48'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_48 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_49'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_49 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_50'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_50 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_51'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_51 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_52'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_52 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_53'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_53 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_54'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_54 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_55'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_55 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_56'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_56 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_57'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_57 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_58'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_58 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_59'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_59 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_60'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_60 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_61'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_61 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_62'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_62 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_63'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_63 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_64'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_64 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_65'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_65 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_66'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_66 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_67'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_67 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_68'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_68 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_69'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_69 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_70'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_70 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_71'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_71 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_72'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_72 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_73'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_73 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_74'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_74 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_75'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_75 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_76'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_76 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_77'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_77 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁexpert_deliberate__mutmut['xǁExpertPanelǁexpert_deliberate__mutmut_78'] = ExpertPanel.xǁExpertPanelǁexpert_deliberate__mutmut_78 # type: ignore # mutmut generated

mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['_mutmut_orig'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_orig # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['xǁExpertPanelǁ_mock_deliberate__mutmut_1'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_1 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['xǁExpertPanelǁ_mock_deliberate__mutmut_2'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_2 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['xǁExpertPanelǁ_mock_deliberate__mutmut_3'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_3 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['xǁExpertPanelǁ_mock_deliberate__mutmut_4'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_4 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['xǁExpertPanelǁ_mock_deliberate__mutmut_5'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_5 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['xǁExpertPanelǁ_mock_deliberate__mutmut_6'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_6 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['xǁExpertPanelǁ_mock_deliberate__mutmut_7'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_7 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['xǁExpertPanelǁ_mock_deliberate__mutmut_8'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_8 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['xǁExpertPanelǁ_mock_deliberate__mutmut_9'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_9 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['xǁExpertPanelǁ_mock_deliberate__mutmut_10'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_10 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['xǁExpertPanelǁ_mock_deliberate__mutmut_11'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_11 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['xǁExpertPanelǁ_mock_deliberate__mutmut_12'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_12 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['xǁExpertPanelǁ_mock_deliberate__mutmut_13'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_13 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['xǁExpertPanelǁ_mock_deliberate__mutmut_14'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_14 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['xǁExpertPanelǁ_mock_deliberate__mutmut_15'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_15 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['xǁExpertPanelǁ_mock_deliberate__mutmut_16'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_16 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['xǁExpertPanelǁ_mock_deliberate__mutmut_17'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_17 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['xǁExpertPanelǁ_mock_deliberate__mutmut_18'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_18 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['xǁExpertPanelǁ_mock_deliberate__mutmut_19'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_19 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['xǁExpertPanelǁ_mock_deliberate__mutmut_20'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_20 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['xǁExpertPanelǁ_mock_deliberate__mutmut_21'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_21 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['xǁExpertPanelǁ_mock_deliberate__mutmut_22'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_22 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['xǁExpertPanelǁ_mock_deliberate__mutmut_23'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_23 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['xǁExpertPanelǁ_mock_deliberate__mutmut_24'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_24 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['xǁExpertPanelǁ_mock_deliberate__mutmut_25'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_25 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['xǁExpertPanelǁ_mock_deliberate__mutmut_26'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_26 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['xǁExpertPanelǁ_mock_deliberate__mutmut_27'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_27 # type: ignore # mutmut generated
mutants_xǁExpertPanelǁ_mock_deliberate__mutmut['xǁExpertPanelǁ_mock_deliberate__mutmut_28'] = ExpertPanel.xǁExpertPanelǁ_mock_deliberate__mutmut_28 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_run_roundtable__mutmut)
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


def x_run_roundtable__mutmut_orig(requirement: str,
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


def x_run_roundtable__mutmut_1(requirement: str,
                   paradigm_hints: list[str],
                   design_summary: str,
                   use_mock: bool = False,
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


def x_run_roundtable__mutmut_2(requirement: str,
                   paradigm_hints: list[str],
                   design_summary: str,
                   use_mock: bool = True,
                   max_experts: int = 7) -> dict[str, Any]:
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


def x_run_roundtable__mutmut_3(requirement: str,
                   paradigm_hints: list[str],
                   design_summary: str,
                   use_mock: bool = True,
                   max_experts: int = 6) -> dict[str, Any]:
    """完整圆桌：筛选 → 独立推演 → 收敛。

    返回收敛后的结构化报告（共识/分歧/风险/推荐方法论/专家明细）。
    """
    panel = None
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


def x_run_roundtable__mutmut_4(requirement: str,
                   paradigm_hints: list[str],
                   design_summary: str,
                   use_mock: bool = True,
                   max_experts: int = 6) -> dict[str, Any]:
    """完整圆桌：筛选 → 独立推演 → 收敛。

    返回收敛后的结构化报告（共识/分歧/风险/推荐方法论/专家明细）。
    """
    panel = ExpertPanel()
    subset = None

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


def x_run_roundtable__mutmut_5(requirement: str,
                   paradigm_hints: list[str],
                   design_summary: str,
                   use_mock: bool = True,
                   max_experts: int = 6) -> dict[str, Any]:
    """完整圆桌：筛选 → 独立推演 → 收敛。

    返回收敛后的结构化报告（共识/分歧/风险/推荐方法论/专家明细）。
    """
    panel = ExpertPanel()
    subset = panel.select_subset(None, max_n=max_experts)

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


def x_run_roundtable__mutmut_6(requirement: str,
                   paradigm_hints: list[str],
                   design_summary: str,
                   use_mock: bool = True,
                   max_experts: int = 6) -> dict[str, Any]:
    """完整圆桌：筛选 → 独立推演 → 收敛。

    返回收敛后的结构化报告（共识/分歧/风险/推荐方法论/专家明细）。
    """
    panel = ExpertPanel()
    subset = panel.select_subset(paradigm_hints, max_n=None)

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


def x_run_roundtable__mutmut_7(requirement: str,
                   paradigm_hints: list[str],
                   design_summary: str,
                   use_mock: bool = True,
                   max_experts: int = 6) -> dict[str, Any]:
    """完整圆桌：筛选 → 独立推演 → 收敛。

    返回收敛后的结构化报告（共识/分歧/风险/推荐方法论/专家明细）。
    """
    panel = ExpertPanel()
    subset = panel.select_subset(max_n=max_experts)

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


def x_run_roundtable__mutmut_8(requirement: str,
                   paradigm_hints: list[str],
                   design_summary: str,
                   use_mock: bool = True,
                   max_experts: int = 6) -> dict[str, Any]:
    """完整圆桌：筛选 → 独立推演 → 收敛。

    返回收敛后的结构化报告（共识/分歧/风险/推荐方法论/专家明细）。
    """
    panel = ExpertPanel()
    subset = panel.select_subset(paradigm_hints, )

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


def x_run_roundtable__mutmut_9(requirement: str,
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
    deliberations: list[dict[str, Any]] = None
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


def x_run_roundtable__mutmut_10(requirement: str,
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
    with ThreadPoolExecutor(max_workers=None) as pool:
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


def x_run_roundtable__mutmut_11(requirement: str,
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
    with ThreadPoolExecutor(max_workers=min(None, len(subset))) as pool:
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


def x_run_roundtable__mutmut_12(requirement: str,
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
    with ThreadPoolExecutor(max_workers=min(6, None)) as pool:
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


def x_run_roundtable__mutmut_13(requirement: str,
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
    with ThreadPoolExecutor(max_workers=min(len(subset))) as pool:
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


def x_run_roundtable__mutmut_14(requirement: str,
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
    with ThreadPoolExecutor(max_workers=min(6, )) as pool:
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


def x_run_roundtable__mutmut_15(requirement: str,
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
    with ThreadPoolExecutor(max_workers=min(7, len(subset))) as pool:
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


def x_run_roundtable__mutmut_16(requirement: str,
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
        futures = None
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


def x_run_roundtable__mutmut_17(requirement: str,
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
            pool.submit(None, e, requirement,
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


def x_run_roundtable__mutmut_18(requirement: str,
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
            pool.submit(panel.expert_deliberate, None, requirement,
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


def x_run_roundtable__mutmut_19(requirement: str,
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
            pool.submit(panel.expert_deliberate, e, None,
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


def x_run_roundtable__mutmut_20(requirement: str,
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
                        None, design_summary, use_mock)
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


def x_run_roundtable__mutmut_21(requirement: str,
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
                        paradigm_hints, None, use_mock)
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


def x_run_roundtable__mutmut_22(requirement: str,
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
                        paradigm_hints, design_summary, None)
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


def x_run_roundtable__mutmut_23(requirement: str,
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
            pool.submit(e, requirement,
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


def x_run_roundtable__mutmut_24(requirement: str,
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
            pool.submit(panel.expert_deliberate, requirement,
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


def x_run_roundtable__mutmut_25(requirement: str,
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
            pool.submit(panel.expert_deliberate, e, paradigm_hints, design_summary, use_mock)
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


def x_run_roundtable__mutmut_26(requirement: str,
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
                        design_summary, use_mock)
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


def x_run_roundtable__mutmut_27(requirement: str,
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
                        paradigm_hints, use_mock)
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


def x_run_roundtable__mutmut_28(requirement: str,
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
                        paradigm_hints, design_summary, )
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


def x_run_roundtable__mutmut_29(requirement: str,
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
        deliberations = None

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


def x_run_roundtable__mutmut_30(requirement: str,
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
    consensus: list[str] = None
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


def x_run_roundtable__mutmut_31(requirement: str,
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
    risks: list[dict[str, Any]] = None
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


def x_run_roundtable__mutmut_32(requirement: str,
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
    disagreements: list[dict[str, Any]] = None
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


def x_run_roundtable__mutmut_33(requirement: str,
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
    method_votes: dict[str, int] = None

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


def x_run_roundtable__mutmut_34(requirement: str,
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
        for s in d.get(None, []):
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


def x_run_roundtable__mutmut_35(requirement: str,
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
        for s in d.get("strengths", None):
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


def x_run_roundtable__mutmut_36(requirement: str,
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
        for s in d.get([]):
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


def x_run_roundtable__mutmut_37(requirement: str,
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
        for s in d.get("strengths", ):
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


def x_run_roundtable__mutmut_38(requirement: str,
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
        for s in d.get("XXstrengthsXX", []):
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


def x_run_roundtable__mutmut_39(requirement: str,
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
        for s in d.get("STRENGTHS", []):
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


def x_run_roundtable__mutmut_40(requirement: str,
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
            text = None
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


def x_run_roundtable__mutmut_41(requirement: str,
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
            text = s if (isinstance(s, str)) and False else str(s)
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


def x_run_roundtable__mutmut_42(requirement: str,
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
            text = s if (isinstance(s, str)) or True else str(s)
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


def x_run_roundtable__mutmut_43(requirement: str,
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
            text = s if isinstance(s, str) else str(None)
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


def x_run_roundtable__mutmut_44(requirement: str,
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
            if text in consensus:
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


def x_run_roundtable__mutmut_45(requirement: str,
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
                consensus.append(None)
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


def x_run_roundtable__mutmut_46(requirement: str,
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
        for w in d.get(None, []):
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


def x_run_roundtable__mutmut_47(requirement: str,
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
        for w in d.get("weaknesses", None):
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


def x_run_roundtable__mutmut_48(requirement: str,
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
        for w in d.get([]):
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


def x_run_roundtable__mutmut_49(requirement: str,
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
        for w in d.get("weaknesses", ):
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


def x_run_roundtable__mutmut_50(requirement: str,
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
        for w in d.get("XXweaknessesXX", []):
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


def x_run_roundtable__mutmut_51(requirement: str,
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
        for w in d.get("WEAKNESSES", []):
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


def x_run_roundtable__mutmut_52(requirement: str,
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
            text = None
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


def x_run_roundtable__mutmut_53(requirement: str,
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
            text = w if (isinstance(w, str)) and False else str(w)
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


def x_run_roundtable__mutmut_54(requirement: str,
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
            text = w if (isinstance(w, str)) or True else str(w)
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


def x_run_roundtable__mutmut_55(requirement: str,
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
            text = w if isinstance(w, str) else str(None)
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


def x_run_roundtable__mutmut_56(requirement: str,
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
            risks.append(None)
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


def x_run_roundtable__mutmut_57(requirement: str,
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
            risks.append({"XXriskXX": text, "source_expert": d["expert_name"],
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


def x_run_roundtable__mutmut_58(requirement: str,
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
            risks.append({"RISK": text, "source_expert": d["expert_name"],
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


def x_run_roundtable__mutmut_59(requirement: str,
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
            risks.append({"risk": text, "XXsource_expertXX": d["expert_name"],
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


def x_run_roundtable__mutmut_60(requirement: str,
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
            risks.append({"risk": text, "SOURCE_EXPERT": d["expert_name"],
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


def x_run_roundtable__mutmut_61(requirement: str,
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
            risks.append({"risk": text, "source_expert": d["XXexpert_nameXX"],
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


def x_run_roundtable__mutmut_62(requirement: str,
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
            risks.append({"risk": text, "source_expert": d["EXPERT_NAME"],
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


def x_run_roundtable__mutmut_63(requirement: str,
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
                          "XXseverityXX": "medium"})
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


def x_run_roundtable__mutmut_64(requirement: str,
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
                          "SEVERITY": "medium"})
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


def x_run_roundtable__mutmut_65(requirement: str,
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
                          "severity": "XXmediumXX"})
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


def x_run_roundtable__mutmut_66(requirement: str,
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
                          "severity": "MEDIUM"})
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


def x_run_roundtable__mutmut_67(requirement: str,
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
        for method in d.get(None, []):
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


def x_run_roundtable__mutmut_68(requirement: str,
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
        for method in d.get("methods", None):
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


def x_run_roundtable__mutmut_69(requirement: str,
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
        for method in d.get([]):
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


def x_run_roundtable__mutmut_70(requirement: str,
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
        for method in d.get("methods", ):
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


def x_run_roundtable__mutmut_71(requirement: str,
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
        for method in d.get("XXmethodsXX", []):
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


def x_run_roundtable__mutmut_72(requirement: str,
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
        for method in d.get("METHODS", []):
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


def x_run_roundtable__mutmut_73(requirement: str,
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
            method_votes[method] = None

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


def x_run_roundtable__mutmut_74(requirement: str,
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
            method_votes[method] = method_votes.get(method, 0) - 1

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


def x_run_roundtable__mutmut_75(requirement: str,
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
            method_votes[method] = method_votes.get(None, 0) + 1

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


def x_run_roundtable__mutmut_76(requirement: str,
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
            method_votes[method] = method_votes.get(method, None) + 1

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


def x_run_roundtable__mutmut_77(requirement: str,
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
            method_votes[method] = method_votes.get(0) + 1

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


def x_run_roundtable__mutmut_78(requirement: str,
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
            method_votes[method] = method_votes.get(method, ) + 1

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


def x_run_roundtable__mutmut_79(requirement: str,
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
            method_votes[method] = method_votes.get(method, 1) + 1

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


def x_run_roundtable__mutmut_80(requirement: str,
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
            method_votes[method] = method_votes.get(method, 0) + 2

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


def x_run_roundtable__mutmut_81(requirement: str,
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
    recommended_methods = None

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


def x_run_roundtable__mutmut_82(requirement: str,
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
    recommended_methods = sorted(None,
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


def x_run_roundtable__mutmut_83(requirement: str,
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
                                 key=None,
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


def x_run_roundtable__mutmut_84(requirement: str,
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
                                 reverse=None)[:5]

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


def x_run_roundtable__mutmut_85(requirement: str,
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
    recommended_methods = sorted(key=lambda k: method_votes[k],
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


def x_run_roundtable__mutmut_86(requirement: str,
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


def x_run_roundtable__mutmut_87(requirement: str,
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
                                 )[:5]

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


def x_run_roundtable__mutmut_88(requirement: str,
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
                                 key=lambda k: None,
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


def x_run_roundtable__mutmut_89(requirement: str,
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
                                 reverse=False)[:5]

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


def x_run_roundtable__mutmut_90(requirement: str,
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
                                 reverse=True)[:6]

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


def x_run_roundtable__mutmut_91(requirement: str,
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
    disagreement_list = None
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


def x_run_roundtable__mutmut_92(requirement: str,
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
    for i, d in enumerate(None):
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


def x_run_roundtable__mutmut_93(requirement: str,
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
        for j in range(None, len(deliberations)):
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


def x_run_roundtable__mutmut_94(requirement: str,
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
        for j in range(i + 1, None):
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


def x_run_roundtable__mutmut_95(requirement: str,
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
        for j in range(len(deliberations)):
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


def x_run_roundtable__mutmut_96(requirement: str,
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
        for j in range(i + 1, ):
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


def x_run_roundtable__mutmut_97(requirement: str,
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
        for j in range(i - 1, len(deliberations)):
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


def x_run_roundtable__mutmut_98(requirement: str,
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
        for j in range(i + 2, len(deliberations)):
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


def x_run_roundtable__mutmut_99(requirement: str,
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
            if d["XXdisciplineXX"] != deliberations[j]["discipline"]:
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


def x_run_roundtable__mutmut_100(requirement: str,
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
            if d["DISCIPLINE"] != deliberations[j]["discipline"]:
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


def x_run_roundtable__mutmut_101(requirement: str,
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
            if d["discipline"] == deliberations[j]["discipline"]:
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


def x_run_roundtable__mutmut_102(requirement: str,
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
            if d["discipline"] != deliberations[j]["XXdisciplineXX"]:
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


def x_run_roundtable__mutmut_103(requirement: str,
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
            if d["discipline"] != deliberations[j]["DISCIPLINE"]:
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


def x_run_roundtable__mutmut_104(requirement: str,
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
                disagreement_list.append(None)
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


def x_run_roundtable__mutmut_105(requirement: str,
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
                    "XXtopicXX": f"{d['expert_name']} vs {deliberations[j]['expert_name']} 视角差异",
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


def x_run_roundtable__mutmut_106(requirement: str,
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
                    "TOPIC": f"{d['expert_name']} vs {deliberations[j]['expert_name']} 视角差异",
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


def x_run_roundtable__mutmut_107(requirement: str,
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
                    "topic": f"{d['XXexpert_nameXX']} vs {deliberations[j]['expert_name']} 视角差异",
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


def x_run_roundtable__mutmut_108(requirement: str,
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
                    "topic": f"{d['EXPERT_NAME']} vs {deliberations[j]['expert_name']} 视角差异",
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


def x_run_roundtable__mutmut_109(requirement: str,
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
                    "topic": f"{d['expert_name']} vs {deliberations[j]['XXexpert_nameXX']} 视角差异",
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


def x_run_roundtable__mutmut_110(requirement: str,
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
                    "topic": f"{d['expert_name']} vs {deliberations[j]['EXPERT_NAME']} 视角差异",
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


def x_run_roundtable__mutmut_111(requirement: str,
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
                    "XXnatureXX": "disciplinary_perspective",
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


def x_run_roundtable__mutmut_112(requirement: str,
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
                    "NATURE": "disciplinary_perspective",
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


def x_run_roundtable__mutmut_113(requirement: str,
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
                    "nature": "XXdisciplinary_perspectiveXX",
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


def x_run_roundtable__mutmut_114(requirement: str,
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
                    "nature": "DISCIPLINARY_PERSPECTIVE",
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


def x_run_roundtable__mutmut_115(requirement: str,
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
                    "XXpositionsXX": [f"{d['expert_name']}:{d['strengths'][0][:20]}",
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


def x_run_roundtable__mutmut_116(requirement: str,
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
                    "POSITIONS": [f"{d['expert_name']}:{d['strengths'][0][:20]}",
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


def x_run_roundtable__mutmut_117(requirement: str,
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
                    "positions": [f"{d['XXexpert_nameXX']}:{d['strengths'][0][:20]}",
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


def x_run_roundtable__mutmut_118(requirement: str,
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
                    "positions": [f"{d['EXPERT_NAME']}:{d['strengths'][0][:20]}",
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


def x_run_roundtable__mutmut_119(requirement: str,
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
                    "positions": [f"{d['expert_name']}:{d['XXstrengthsXX'][0][:20]}",
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


def x_run_roundtable__mutmut_120(requirement: str,
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
                    "positions": [f"{d['expert_name']}:{d['STRENGTHS'][0][:20]}",
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


def x_run_roundtable__mutmut_121(requirement: str,
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
                    "positions": [f"{d['expert_name']}:{d['strengths'][1][:20]}",
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


def x_run_roundtable__mutmut_122(requirement: str,
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
                    "positions": [f"{d['expert_name']}:{d['strengths'][0][:21]}",
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


def x_run_roundtable__mutmut_123(requirement: str,
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
                                  f"{deliberations[j]['XXexpert_nameXX']}:{deliberations[j]['strengths'][0][:20]}"],
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


def x_run_roundtable__mutmut_124(requirement: str,
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
                                  f"{deliberations[j]['EXPERT_NAME']}:{deliberations[j]['strengths'][0][:20]}"],
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


def x_run_roundtable__mutmut_125(requirement: str,
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
                                  f"{deliberations[j]['expert_name']}:{deliberations[j]['XXstrengthsXX'][0][:20]}"],
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


def x_run_roundtable__mutmut_126(requirement: str,
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
                                  f"{deliberations[j]['expert_name']}:{deliberations[j]['STRENGTHS'][0][:20]}"],
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


def x_run_roundtable__mutmut_127(requirement: str,
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
                                  f"{deliberations[j]['expert_name']}:{deliberations[j]['strengths'][1][:20]}"],
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


def x_run_roundtable__mutmut_128(requirement: str,
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
                                  f"{deliberations[j]['expert_name']}:{deliberations[j]['strengths'][0][:21]}"],
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


def x_run_roundtable__mutmut_129(requirement: str,
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
                if len(disagreement_list) > 3:
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


def x_run_roundtable__mutmut_130(requirement: str,
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
                if len(disagreement_list) >= 4:
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


def x_run_roundtable__mutmut_131(requirement: str,
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
                    return
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


def x_run_roundtable__mutmut_132(requirement: str,
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
        if len(disagreement_list) > 3:
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


def x_run_roundtable__mutmut_133(requirement: str,
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
        if len(disagreement_list) >= 4:
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


def x_run_roundtable__mutmut_134(requirement: str,
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
            return

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


def x_run_roundtable__mutmut_135(requirement: str,
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
        "XXsession_metaXX": {
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


def x_run_roundtable__mutmut_136(requirement: str,
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
        "SESSION_META": {
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


def x_run_roundtable__mutmut_137(requirement: str,
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
            "XXtriggeredXX": True,
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


def x_run_roundtable__mutmut_138(requirement: str,
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
            "TRIGGERED": True,
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


def x_run_roundtable__mutmut_139(requirement: str,
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
            "triggered": False,
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


def x_run_roundtable__mutmut_140(requirement: str,
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
            "XXtrigger_reasonXX": "真实圆桌:范式线索触发专家子集",
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


def x_run_roundtable__mutmut_141(requirement: str,
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
            "TRIGGER_REASON": "真实圆桌:范式线索触发专家子集",
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


def x_run_roundtable__mutmut_142(requirement: str,
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
            "trigger_reason": "XX真实圆桌:范式线索触发专家子集XX",
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


def x_run_roundtable__mutmut_143(requirement: str,
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
            "XXexpert_subsetXX": [e["name"] for e in subset],
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


def x_run_roundtable__mutmut_144(requirement: str,
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
            "EXPERT_SUBSET": [e["name"] for e in subset],
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


def x_run_roundtable__mutmut_145(requirement: str,
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
            "expert_subset": [e["XXnameXX"] for e in subset],
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


def x_run_roundtable__mutmut_146(requirement: str,
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
            "expert_subset": [e["NAME"] for e in subset],
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


def x_run_roundtable__mutmut_147(requirement: str,
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
            "XXexpert_countXX": len(subset),
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


def x_run_roundtable__mutmut_148(requirement: str,
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
            "EXPERT_COUNT": len(subset),
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


def x_run_roundtable__mutmut_149(requirement: str,
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
            "XXllm_modeXX": "real_llm" if not use_mock and os.environ.get("ZHIPU_API_KEY") else ("mock" if use_mock else "fallback"),
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


def x_run_roundtable__mutmut_150(requirement: str,
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
            "LLM_MODE": "real_llm" if not use_mock and os.environ.get("ZHIPU_API_KEY") else ("mock" if use_mock else "fallback"),
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


def x_run_roundtable__mutmut_151(requirement: str,
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
            "llm_mode": "real_llm" if (not use_mock and os.environ.get("ZHIPU_API_KEY")) and False else ("mock" if use_mock else "fallback"),
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


def x_run_roundtable__mutmut_152(requirement: str,
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
            "llm_mode": "real_llm" if (not use_mock and os.environ.get("ZHIPU_API_KEY")) or True else ("mock" if use_mock else "fallback"),
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


def x_run_roundtable__mutmut_153(requirement: str,
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
            "llm_mode": "XXreal_llmXX" if not use_mock and os.environ.get("ZHIPU_API_KEY") else ("mock" if use_mock else "fallback"),
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


def x_run_roundtable__mutmut_154(requirement: str,
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
            "llm_mode": "REAL_LLM" if not use_mock and os.environ.get("ZHIPU_API_KEY") else ("mock" if use_mock else "fallback"),
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


def x_run_roundtable__mutmut_155(requirement: str,
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
            "llm_mode": "real_llm" if not use_mock or os.environ.get("ZHIPU_API_KEY") else ("mock" if use_mock else "fallback"),
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


def x_run_roundtable__mutmut_156(requirement: str,
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
            "llm_mode": "real_llm" if use_mock and os.environ.get("ZHIPU_API_KEY") else ("mock" if use_mock else "fallback"),
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


def x_run_roundtable__mutmut_157(requirement: str,
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
            "llm_mode": "real_llm" if not use_mock and os.environ.get(None) else ("mock" if use_mock else "fallback"),
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


def x_run_roundtable__mutmut_158(requirement: str,
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
            "llm_mode": "real_llm" if not use_mock and os.environ.get("XXZHIPU_API_KEYXX") else ("mock" if use_mock else "fallback"),
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


def x_run_roundtable__mutmut_159(requirement: str,
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
            "llm_mode": "real_llm" if not use_mock and os.environ.get("zhipu_api_key") else ("mock" if use_mock else "fallback"),
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


def x_run_roundtable__mutmut_160(requirement: str,
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
            "llm_mode": "real_llm" if not use_mock and os.environ.get("ZHIPU_API_KEY") else ("mock" if (use_mock) and False else "fallback"),
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


def x_run_roundtable__mutmut_161(requirement: str,
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
            "llm_mode": "real_llm" if not use_mock and os.environ.get("ZHIPU_API_KEY") else ("mock" if (use_mock) or True else "fallback"),
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


def x_run_roundtable__mutmut_162(requirement: str,
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
            "llm_mode": "real_llm" if not use_mock and os.environ.get("ZHIPU_API_KEY") else ("XXmockXX" if use_mock else "fallback"),
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


def x_run_roundtable__mutmut_163(requirement: str,
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
            "llm_mode": "real_llm" if not use_mock and os.environ.get("ZHIPU_API_KEY") else ("MOCK" if use_mock else "fallback"),
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


def x_run_roundtable__mutmut_164(requirement: str,
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
            "llm_mode": "real_llm" if not use_mock and os.environ.get("ZHIPU_API_KEY") else ("mock" if use_mock else "XXfallbackXX"),
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


def x_run_roundtable__mutmut_165(requirement: str,
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
            "llm_mode": "real_llm" if not use_mock and os.environ.get("ZHIPU_API_KEY") else ("mock" if use_mock else "FALLBACK"),
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


def x_run_roundtable__mutmut_166(requirement: str,
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
            "XXroundtable_versionXX": "2.0-real",
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


def x_run_roundtable__mutmut_167(requirement: str,
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
            "ROUNDTABLE_VERSION": "2.0-real",
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


def x_run_roundtable__mutmut_168(requirement: str,
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
            "roundtable_version": "XX2.0-realXX",
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


def x_run_roundtable__mutmut_169(requirement: str,
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
            "roundtable_version": "2.0-REAL",
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


def x_run_roundtable__mutmut_170(requirement: str,
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
        "XXfindingsXX": {
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


def x_run_roundtable__mutmut_171(requirement: str,
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
        "FINDINGS": {
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


def x_run_roundtable__mutmut_172(requirement: str,
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
            "XXconsensus_listXX": consensus[:5],
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


def x_run_roundtable__mutmut_173(requirement: str,
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
            "CONSENSUS_LIST": consensus[:5],
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


def x_run_roundtable__mutmut_174(requirement: str,
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
            "consensus_list": consensus[:6],
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


def x_run_roundtable__mutmut_175(requirement: str,
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
            "XXrisk_listXX": risks[:8],
            "disagreement_list": disagreement_list,
            "recommended_methodologies": recommended_methods,
        },
        "expert_deliberations": deliberations,
        "feedback_to_matching": {
            "adjusted_paradigm_ids": None,
            "adjustment_notes": "真实圆桌收敛,采纳跨学科共识",
        },
    }


def x_run_roundtable__mutmut_176(requirement: str,
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
            "RISK_LIST": risks[:8],
            "disagreement_list": disagreement_list,
            "recommended_methodologies": recommended_methods,
        },
        "expert_deliberations": deliberations,
        "feedback_to_matching": {
            "adjusted_paradigm_ids": None,
            "adjustment_notes": "真实圆桌收敛,采纳跨学科共识",
        },
    }


def x_run_roundtable__mutmut_177(requirement: str,
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
            "risk_list": risks[:9],
            "disagreement_list": disagreement_list,
            "recommended_methodologies": recommended_methods,
        },
        "expert_deliberations": deliberations,
        "feedback_to_matching": {
            "adjusted_paradigm_ids": None,
            "adjustment_notes": "真实圆桌收敛,采纳跨学科共识",
        },
    }


def x_run_roundtable__mutmut_178(requirement: str,
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
            "XXdisagreement_listXX": disagreement_list,
            "recommended_methodologies": recommended_methods,
        },
        "expert_deliberations": deliberations,
        "feedback_to_matching": {
            "adjusted_paradigm_ids": None,
            "adjustment_notes": "真实圆桌收敛,采纳跨学科共识",
        },
    }


def x_run_roundtable__mutmut_179(requirement: str,
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
            "DISAGREEMENT_LIST": disagreement_list,
            "recommended_methodologies": recommended_methods,
        },
        "expert_deliberations": deliberations,
        "feedback_to_matching": {
            "adjusted_paradigm_ids": None,
            "adjustment_notes": "真实圆桌收敛,采纳跨学科共识",
        },
    }


def x_run_roundtable__mutmut_180(requirement: str,
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
            "XXrecommended_methodologiesXX": recommended_methods,
        },
        "expert_deliberations": deliberations,
        "feedback_to_matching": {
            "adjusted_paradigm_ids": None,
            "adjustment_notes": "真实圆桌收敛,采纳跨学科共识",
        },
    }


def x_run_roundtable__mutmut_181(requirement: str,
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
            "RECOMMENDED_METHODOLOGIES": recommended_methods,
        },
        "expert_deliberations": deliberations,
        "feedback_to_matching": {
            "adjusted_paradigm_ids": None,
            "adjustment_notes": "真实圆桌收敛,采纳跨学科共识",
        },
    }


def x_run_roundtable__mutmut_182(requirement: str,
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
        "XXexpert_deliberationsXX": deliberations,
        "feedback_to_matching": {
            "adjusted_paradigm_ids": None,
            "adjustment_notes": "真实圆桌收敛,采纳跨学科共识",
        },
    }


def x_run_roundtable__mutmut_183(requirement: str,
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
        "EXPERT_DELIBERATIONS": deliberations,
        "feedback_to_matching": {
            "adjusted_paradigm_ids": None,
            "adjustment_notes": "真实圆桌收敛,采纳跨学科共识",
        },
    }


def x_run_roundtable__mutmut_184(requirement: str,
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
        "XXfeedback_to_matchingXX": {
            "adjusted_paradigm_ids": None,
            "adjustment_notes": "真实圆桌收敛,采纳跨学科共识",
        },
    }


def x_run_roundtable__mutmut_185(requirement: str,
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
        "FEEDBACK_TO_MATCHING": {
            "adjusted_paradigm_ids": None,
            "adjustment_notes": "真实圆桌收敛,采纳跨学科共识",
        },
    }


def x_run_roundtable__mutmut_186(requirement: str,
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
            "XXadjusted_paradigm_idsXX": None,
            "adjustment_notes": "真实圆桌收敛,采纳跨学科共识",
        },
    }


def x_run_roundtable__mutmut_187(requirement: str,
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
            "ADJUSTED_PARADIGM_IDS": None,
            "adjustment_notes": "真实圆桌收敛,采纳跨学科共识",
        },
    }


def x_run_roundtable__mutmut_188(requirement: str,
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
            "XXadjustment_notesXX": "真实圆桌收敛,采纳跨学科共识",
        },
    }


def x_run_roundtable__mutmut_189(requirement: str,
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
            "ADJUSTMENT_NOTES": "真实圆桌收敛,采纳跨学科共识",
        },
    }


def x_run_roundtable__mutmut_190(requirement: str,
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
            "adjustment_notes": "XX真实圆桌收敛,采纳跨学科共识XX",
        },
    }

mutants_x_run_roundtable__mutmut['_mutmut_orig'] = x_run_roundtable__mutmut_orig # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_1'] = x_run_roundtable__mutmut_1 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_2'] = x_run_roundtable__mutmut_2 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_3'] = x_run_roundtable__mutmut_3 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_4'] = x_run_roundtable__mutmut_4 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_5'] = x_run_roundtable__mutmut_5 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_6'] = x_run_roundtable__mutmut_6 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_7'] = x_run_roundtable__mutmut_7 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_8'] = x_run_roundtable__mutmut_8 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_9'] = x_run_roundtable__mutmut_9 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_10'] = x_run_roundtable__mutmut_10 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_11'] = x_run_roundtable__mutmut_11 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_12'] = x_run_roundtable__mutmut_12 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_13'] = x_run_roundtable__mutmut_13 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_14'] = x_run_roundtable__mutmut_14 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_15'] = x_run_roundtable__mutmut_15 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_16'] = x_run_roundtable__mutmut_16 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_17'] = x_run_roundtable__mutmut_17 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_18'] = x_run_roundtable__mutmut_18 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_19'] = x_run_roundtable__mutmut_19 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_20'] = x_run_roundtable__mutmut_20 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_21'] = x_run_roundtable__mutmut_21 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_22'] = x_run_roundtable__mutmut_22 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_23'] = x_run_roundtable__mutmut_23 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_24'] = x_run_roundtable__mutmut_24 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_25'] = x_run_roundtable__mutmut_25 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_26'] = x_run_roundtable__mutmut_26 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_27'] = x_run_roundtable__mutmut_27 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_28'] = x_run_roundtable__mutmut_28 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_29'] = x_run_roundtable__mutmut_29 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_30'] = x_run_roundtable__mutmut_30 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_31'] = x_run_roundtable__mutmut_31 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_32'] = x_run_roundtable__mutmut_32 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_33'] = x_run_roundtable__mutmut_33 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_34'] = x_run_roundtable__mutmut_34 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_35'] = x_run_roundtable__mutmut_35 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_36'] = x_run_roundtable__mutmut_36 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_37'] = x_run_roundtable__mutmut_37 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_38'] = x_run_roundtable__mutmut_38 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_39'] = x_run_roundtable__mutmut_39 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_40'] = x_run_roundtable__mutmut_40 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_41'] = x_run_roundtable__mutmut_41 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_42'] = x_run_roundtable__mutmut_42 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_43'] = x_run_roundtable__mutmut_43 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_44'] = x_run_roundtable__mutmut_44 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_45'] = x_run_roundtable__mutmut_45 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_46'] = x_run_roundtable__mutmut_46 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_47'] = x_run_roundtable__mutmut_47 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_48'] = x_run_roundtable__mutmut_48 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_49'] = x_run_roundtable__mutmut_49 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_50'] = x_run_roundtable__mutmut_50 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_51'] = x_run_roundtable__mutmut_51 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_52'] = x_run_roundtable__mutmut_52 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_53'] = x_run_roundtable__mutmut_53 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_54'] = x_run_roundtable__mutmut_54 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_55'] = x_run_roundtable__mutmut_55 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_56'] = x_run_roundtable__mutmut_56 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_57'] = x_run_roundtable__mutmut_57 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_58'] = x_run_roundtable__mutmut_58 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_59'] = x_run_roundtable__mutmut_59 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_60'] = x_run_roundtable__mutmut_60 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_61'] = x_run_roundtable__mutmut_61 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_62'] = x_run_roundtable__mutmut_62 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_63'] = x_run_roundtable__mutmut_63 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_64'] = x_run_roundtable__mutmut_64 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_65'] = x_run_roundtable__mutmut_65 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_66'] = x_run_roundtable__mutmut_66 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_67'] = x_run_roundtable__mutmut_67 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_68'] = x_run_roundtable__mutmut_68 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_69'] = x_run_roundtable__mutmut_69 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_70'] = x_run_roundtable__mutmut_70 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_71'] = x_run_roundtable__mutmut_71 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_72'] = x_run_roundtable__mutmut_72 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_73'] = x_run_roundtable__mutmut_73 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_74'] = x_run_roundtable__mutmut_74 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_75'] = x_run_roundtable__mutmut_75 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_76'] = x_run_roundtable__mutmut_76 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_77'] = x_run_roundtable__mutmut_77 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_78'] = x_run_roundtable__mutmut_78 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_79'] = x_run_roundtable__mutmut_79 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_80'] = x_run_roundtable__mutmut_80 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_81'] = x_run_roundtable__mutmut_81 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_82'] = x_run_roundtable__mutmut_82 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_83'] = x_run_roundtable__mutmut_83 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_84'] = x_run_roundtable__mutmut_84 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_85'] = x_run_roundtable__mutmut_85 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_86'] = x_run_roundtable__mutmut_86 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_87'] = x_run_roundtable__mutmut_87 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_88'] = x_run_roundtable__mutmut_88 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_89'] = x_run_roundtable__mutmut_89 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_90'] = x_run_roundtable__mutmut_90 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_91'] = x_run_roundtable__mutmut_91 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_92'] = x_run_roundtable__mutmut_92 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_93'] = x_run_roundtable__mutmut_93 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_94'] = x_run_roundtable__mutmut_94 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_95'] = x_run_roundtable__mutmut_95 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_96'] = x_run_roundtable__mutmut_96 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_97'] = x_run_roundtable__mutmut_97 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_98'] = x_run_roundtable__mutmut_98 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_99'] = x_run_roundtable__mutmut_99 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_100'] = x_run_roundtable__mutmut_100 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_101'] = x_run_roundtable__mutmut_101 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_102'] = x_run_roundtable__mutmut_102 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_103'] = x_run_roundtable__mutmut_103 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_104'] = x_run_roundtable__mutmut_104 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_105'] = x_run_roundtable__mutmut_105 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_106'] = x_run_roundtable__mutmut_106 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_107'] = x_run_roundtable__mutmut_107 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_108'] = x_run_roundtable__mutmut_108 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_109'] = x_run_roundtable__mutmut_109 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_110'] = x_run_roundtable__mutmut_110 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_111'] = x_run_roundtable__mutmut_111 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_112'] = x_run_roundtable__mutmut_112 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_113'] = x_run_roundtable__mutmut_113 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_114'] = x_run_roundtable__mutmut_114 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_115'] = x_run_roundtable__mutmut_115 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_116'] = x_run_roundtable__mutmut_116 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_117'] = x_run_roundtable__mutmut_117 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_118'] = x_run_roundtable__mutmut_118 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_119'] = x_run_roundtable__mutmut_119 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_120'] = x_run_roundtable__mutmut_120 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_121'] = x_run_roundtable__mutmut_121 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_122'] = x_run_roundtable__mutmut_122 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_123'] = x_run_roundtable__mutmut_123 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_124'] = x_run_roundtable__mutmut_124 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_125'] = x_run_roundtable__mutmut_125 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_126'] = x_run_roundtable__mutmut_126 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_127'] = x_run_roundtable__mutmut_127 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_128'] = x_run_roundtable__mutmut_128 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_129'] = x_run_roundtable__mutmut_129 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_130'] = x_run_roundtable__mutmut_130 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_131'] = x_run_roundtable__mutmut_131 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_132'] = x_run_roundtable__mutmut_132 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_133'] = x_run_roundtable__mutmut_133 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_134'] = x_run_roundtable__mutmut_134 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_135'] = x_run_roundtable__mutmut_135 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_136'] = x_run_roundtable__mutmut_136 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_137'] = x_run_roundtable__mutmut_137 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_138'] = x_run_roundtable__mutmut_138 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_139'] = x_run_roundtable__mutmut_139 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_140'] = x_run_roundtable__mutmut_140 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_141'] = x_run_roundtable__mutmut_141 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_142'] = x_run_roundtable__mutmut_142 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_143'] = x_run_roundtable__mutmut_143 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_144'] = x_run_roundtable__mutmut_144 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_145'] = x_run_roundtable__mutmut_145 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_146'] = x_run_roundtable__mutmut_146 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_147'] = x_run_roundtable__mutmut_147 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_148'] = x_run_roundtable__mutmut_148 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_149'] = x_run_roundtable__mutmut_149 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_150'] = x_run_roundtable__mutmut_150 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_151'] = x_run_roundtable__mutmut_151 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_152'] = x_run_roundtable__mutmut_152 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_153'] = x_run_roundtable__mutmut_153 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_154'] = x_run_roundtable__mutmut_154 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_155'] = x_run_roundtable__mutmut_155 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_156'] = x_run_roundtable__mutmut_156 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_157'] = x_run_roundtable__mutmut_157 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_158'] = x_run_roundtable__mutmut_158 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_159'] = x_run_roundtable__mutmut_159 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_160'] = x_run_roundtable__mutmut_160 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_161'] = x_run_roundtable__mutmut_161 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_162'] = x_run_roundtable__mutmut_162 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_163'] = x_run_roundtable__mutmut_163 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_164'] = x_run_roundtable__mutmut_164 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_165'] = x_run_roundtable__mutmut_165 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_166'] = x_run_roundtable__mutmut_166 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_167'] = x_run_roundtable__mutmut_167 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_168'] = x_run_roundtable__mutmut_168 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_169'] = x_run_roundtable__mutmut_169 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_170'] = x_run_roundtable__mutmut_170 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_171'] = x_run_roundtable__mutmut_171 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_172'] = x_run_roundtable__mutmut_172 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_173'] = x_run_roundtable__mutmut_173 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_174'] = x_run_roundtable__mutmut_174 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_175'] = x_run_roundtable__mutmut_175 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_176'] = x_run_roundtable__mutmut_176 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_177'] = x_run_roundtable__mutmut_177 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_178'] = x_run_roundtable__mutmut_178 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_179'] = x_run_roundtable__mutmut_179 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_180'] = x_run_roundtable__mutmut_180 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_181'] = x_run_roundtable__mutmut_181 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_182'] = x_run_roundtable__mutmut_182 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_183'] = x_run_roundtable__mutmut_183 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_184'] = x_run_roundtable__mutmut_184 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_185'] = x_run_roundtable__mutmut_185 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_186'] = x_run_roundtable__mutmut_186 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_187'] = x_run_roundtable__mutmut_187 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_188'] = x_run_roundtable__mutmut_188 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_189'] = x_run_roundtable__mutmut_189 # type: ignore # mutmut generated
mutants_x_run_roundtable__mutmut['x_run_roundtable__mutmut_190'] = x_run_roundtable__mutmut_190 # type: ignore # mutmut generated


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
