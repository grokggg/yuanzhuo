#!/usr/bin/env python3
"""UHES 范式库模块（第16项优化：拆单体——范式数据与向量函数独立）。

设计原则（顶尖工程实践）：
- 范式库数据独立：PARADIGM_CATALOG(29 组范式) 从 main.py 拆出，单一数据源。
- 向量函数独立：n-gram 向量化 + 余弦相似度，供 embedding 匹配复用。
- 可扩展：范式库以数据驱动，新增范式不改逻辑。

使用：
    from paradigms import PARADIGM_CATALOG, ngram_vector, cosine_similarity
"""

from __future__ import annotations

from typing import Any

# 29 组范式目录（六大类，对应 architecture/范式库.md）
PARADIGM_CATALOG: dict[str, dict[str, str]] = {
    # 一、哲学与思维（5）
    "易经演化": {"name": "易经演化范式", "keywords": "阴阳 变易 卦象 辩证"},
    "第一性原理": {"name": "第一性原理范式", "keywords": "公理 假设剥离 基础推导"},
    "辩证法": {"name": "辩证法范式", "keywords": "对立统一 质量互变 否定之否定"},
    "现象学": {"name": "现象学范式", "keywords": "本质直观 悬置判断 回到事物本身"},
    "分析哲学": {"name": "分析哲学范式", "keywords": "语言分析 逻辑澄清 概念审计"},
    # 二、复杂系统与演化（5）
    "进化论": {"name": "进化论范式", "keywords": "自然选择 变异 适者生存"},
    "复杂系统": {"name": "复杂系统范式", "keywords": "涌现 自组织 非线性 反馈"},
    "控制论": {"name": "控制论范式", "keywords": "反馈控制 稳态 黑箱"},
    "系统论": {"name": "系统论范式", "keywords": "整体论 层次 系统边界"},
    "信息论": {"name": "信息论范式", "keywords": "熵 信息增益 信道 编码"},
    # 三、物理与数学（5）
    "热力学": {"name": "热力学范式", "keywords": "熵增 能量守恒 不可逆"},
    "量子力学": {"name": "量子力学范式", "keywords": "叠加 观测坍缩 不确定性"},
    "凝聚态物理": {"name": "凝聚态物理范式", "keywords": "相变 序参量 对称性破缺"},
    "动力学": {"name": "动力学范式", "keywords": "微分方程 吸引子 混沌"},
    "拓扑学": {"name": "拓扑学范式", "keywords": "连续变换 不变量 连通性"},
    # 四、生物与认知（4）
    "神经科学": {"name": "神经科学范式", "keywords": "神经元 突触可塑性 大脑分区"},
    "认知科学": {"name": "认知科学范式", "keywords": "信息处理 心智表征 有限理性"},
    "生态学": {"name": "生态学范式", "keywords": "生态位 食物链 共生竞争"},
    "胚胎发育": {"name": "胚胎发育范式", "keywords": "细胞分化 形态发生 基因调控"},
    # 五、社会科学（5）
    "社会学": {"name": "社会学范式", "keywords": "社会结构 角色 社会网络"},
    "经济学": {"name": "经济学范式", "keywords": "供需 理性选择 交易成本 博弈"},
    "政治学": {"name": "政治学范式", "keywords": "权力 制度变迁 集体行动"},
    "心理学": {"name": "心理学范式", "keywords": "动机 认知偏差 行为强化"},
    "人类学": {"name": "人类学范式", "keywords": "文化相对主义 符号互动 田野"},
    # 六、工程与应用（5）
    "软件工程": {"name": "软件工程范式", "keywords": "模块化 接口 版本控制 测试"},
    "系统工程": {"name": "系统工程范式", "keywords": "需求 架构 验证 生命周期"},
    "法律": {"name": "法律范式", "keywords": "规则 先例 权利义务 程序"},
    "教育": {"name": "教育范式", "keywords": "建构主义 最近发展区 反馈评估"},
    "科研范式": {"name": "科研范式", "keywords": "假设检验 可证伪 同行评议 复现"},
}

# 网络科学(补充：docs 案例用到,不在 29 组清单但案例引用)
PARADIGM_CATALOG["网络科学"] = {"name": "网络科学范式", "keywords": "节点 边 中心性 小世界 社区"}


def ngram_vector(text: str, n: int = 2) -> dict[str, float]:
    """n-gram 词频向量（中文按字 n-gram + 词混合）。"""
    vec: dict[str, float] = {}
    # 字 n-gram
    for i in range(len(text) - n + 1):
        gram = text[i:i + n]
        vec[gram] = vec.get(gram, 0.0) + 1.0
    # 词（简单 2-4 字词频）
    for w in _tokenize_cn(text):
        if len(w) >= 2:
            vec[w] = vec.get(w, 0.0) + 1.0
    return vec


def _tokenize_cn(text: str) -> list[str]:
    """极简中文分词（2-4 字滑动窗口,概念级）。"""
    tokens: list[str] = []
    for n in (2, 3, 4):
        for i in range(len(text) - n + 1):
            tokens.append(text[i:i + n])
    return tokens


def cosine_similarity(a: dict[str, float], b: dict[str, float]) -> float:
    """余弦相似度。"""
    if not a or not b:
        return 0.0
    dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in set(a) | set(b))
    na = sum(v * v for v in a.values()) ** 0.5
    nb = sum(v * v for v in b.values()) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def embedding_match(dna: dict[str, Any],
                    threshold: float = 0.08) -> dict[str, Any]:
    """范式 embedding 匹配（第2项优化：向量化语义检索）。

    对需求 DNA 的 paradigm_hints + goal 做 n-gram 向量化,与 29 组范式
    关键词向量求余弦相似度,按相似度排序返回匹配范式。
    """
    hints = " ".join([str(h) for h in dna.get("paradigm_hints", [])])
    goal = str(dna.get("goal", {}).get("primary", ""))
    query_vec = ngram_vector(hints + " " + goal)
    scored: list[dict[str, Any]] = []
    for name, meta in PARADIGM_CATALOG.items():
        kw_vec = ngram_vector(meta["keywords"])
        sim = cosine_similarity(query_vec, kw_vec)
        if sim >= threshold:
            scored.append({
                "paradigm_name": name,
                "paradigm_label": meta["name"],
                "similarity": round(sim, 4),
                "match_level": "high" if sim >= 0.15 else "medium",
            })
    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return {
        "matched_paradigms": scored[:5],
        "match_confidence": (
            "high" if scored and scored[0]["similarity"] >= 0.15
            else "medium" if scored else "low"),
        "embedding_version": "2.0-paradigms-module",
    }


if __name__ == "__main__":
    print(f"[PARADIGMS] 范式库: {len(PARADIGM_CATALOG)} 组")
    dna = {"paradigm_hints": ["信息论", "系统论", "数据驱动"],
           "goal": {"primary": "构建数据分析系统,结论可溯源"}}
    r = embedding_match(dna)
    print(f"匹配: {[(m['paradigm_name'], m['similarity']) for m in r['matched_paradigms'][:5]]}")
    print(f"置信度: {r['match_confidence']}")
