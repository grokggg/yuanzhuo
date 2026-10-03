#!/usr/bin/env python3
"""UHES 真语义 Embedding 模块（真实化清单第 2 步）。

从 n-gram 字符近似升级为真语义 embedding：
- 有 ZHIPU_API_KEY：调智谱 embedding-2（1024 维真语义向量）→ 语义相似度
- 无 key：回退 n-gram 余弦（离线铁律，保持可跑）

设计原则：
1. 非侵入：不修改冻结核心，作为独立模块被 main.py 调用
2. 双模式：真语义优先，离线回退兜底（不阻塞主流程）
3. 缓存：同文本向量缓存，避免重复调用（省钱省时）
4. 诚实标注：返回 mode 字段（semantic/ngram），不假装

API：智谱 embedding-2
  URL: https://open.bigmodel.cn/api/paas/v4/embeddings
  模型: embedding-2（1024 维）
  价格: 0.5 元/百万 tokens
"""

import hashlib
import json
import math
import os
import time
import urllib.request
import urllib.error
from typing import Any

# ──────────────────────────────────────────────
# 常量
# ──────────────────────────────────────────────
EMBEDDING_URL = "https://open.bigmodel.cn/api/paas/v4/embeddings"
EMBEDDING_MODEL = "embedding-2"
EMBEDDING_DIM = 1024
_LLM_TIMEOUT = 30  # embedding 调用超时（秒）

# 缓存：text -> (vector, mode)
_VEC_CACHE: dict[str, tuple[list[float], str]] = {}
_CACHE_MAX = 500  # 上限，防内存膨胀


# ──────────────────────────────────────────────
# 1. 真语义 embedding（智谱 API）
# ──────────────────────────────────────────────
def _call_zhipu_embedding(text: str) -> list[float] | None:
    """调智谱 embedding-2 返回 1024 维向量；失败返回 None。"""
    key = os.environ.get("ZHIPU_API_KEY", "").strip()
    if not key:
        return None

    body = json.dumps({
        "model": EMBEDDING_MODEL,
        "input": text,
    }).encode("utf-8")

    req = urllib.request.Request(
        EMBEDDING_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=_LLM_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            # 响应结构: {"data": [{"embedding": [...]}], "model": ..., "usage": ...}
            emb = data["data"][0]["embedding"]
            return [float(x) for x in emb]
    except Exception:
        return None  # 任何失败 → 回退 n-gram（离线铁律）


def _cosine(a: list[float], b: list[float]) -> float:
    """两个稠密向量的余弦相似度。"""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def embed_text(text: str) -> tuple[list[float] | None, str]:
    """返回 (向量, mode)。mode ∈ {'semantic', 'ngram', 'none'}。

    semantic = 真语义 embedding（智谱 API）
    ngram    = 字符 n-gram 回退（离线）
    none     = 文本为空
    """
    text = (text or "").strip()
    if not text:
        return None, "none"

    # 缓存命中
    key = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if key in _VEC_CACHE:
        return _VEC_CACHE[key]

    # 真语义优先
    vec = _call_zhipu_embedding(text)
    if vec is not None:
        _cache_put(key, (vec, "semantic"))
        return vec, "semantic"

    # 回退：n-gram 稀疏向量（保持纯标准库离线可跑）
    vec_sparse = _ngram_vector(text)
    _cache_put(key, (vec_sparse, "ngram"))
    return vec_sparse, "ngram"


def _cache_put(key: str, val: tuple[list[float], str]) -> None:
    if len(_VEC_CACHE) >= _CACHE_MAX:
        _VEC_CACHE.clear()  # 简单淘汰：清空（概念引擎够用）
    _VEC_CACHE[key] = val


# ──────────────────────────────────────────────
# 2. n-gram 回退（原 main.py 的纯标准库实现，保持兼容）
# ──────────────────────────────────────────────
def _ngram_vector(text: str, n: int = 2) -> list[float]:
    """字符 n-gram 稀疏向量（回退模式）。

    返回稠密列表（长度 = 词表），与 semantic 向量接口统一。
    词表由常见范式关键词构成（从 PARADIGM 关键词聚合）。
    """
    # 统一接口：稀疏 dict 转稠密（用固定词表）
    vocab = _NGRAM_VOCAB
    counts: dict[str, float] = {}
    t = text.lower()
    for i in range(len(t) - n + 1):
        gram = t[i:i + n]
        counts[gram] = counts.get(gram, 0.0) + 1.0
    vec = [counts.get(g, 0.0) for g in vocab]
    # 归一化
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


# n-gram 回退的词表（覆盖 29 范式关键词，保证相似度有区分度）
_NGRAM_VOCAB = [
    "系统", "控制", "信息", "演化", "复杂", "反馈", "适应", "涌现",
    "熵", "自组织", "循环", "网络", "层次", "动态", "平衡", "结构",
    "机制", "生态", "进化", "选择", "竞争", "协同", "学习", "预测",
    "决策", "优化", "推理", "验证", "设计", "工程",
    "第一性", "原理", "热力", "量子", "拓扑", "神经", "认知",
    "社会", "经济", "政治", "心理", "语言", "教育", "法律",
]


# ──────────────────────────────────────────────
# 3. 语义相似度（统一入口）
# ──────────────────────────────────────────────
def semantic_similarity(a: str, b: str) -> dict[str, Any]:
    """计算两段文本的语义相似度。

    返回：
      {"similarity": float, "mode": "semantic"|"ngram",
       "vec_a_dim": int, "vec_b_dim": int}
    """
    va, ma = embed_text(a)
    vb, mb = embed_text(b)

    if ma == "semantic" and mb == "semantic":
        sim = _cosine(va, vb)  # type: ignore[arg-type]
        mode = "semantic"
    else:
        # 至少一边回退 n-gram：用 n-gram 余弦（稀疏 dict 兼容）
        sim = _ngram_cosine(a, b)
        mode = "ngram" if (ma == "ngram" or mb == "ngram") else "none"

    return {
        "similarity": round(sim, 4),
        "mode": mode,
        "vec_a_dim": len(va) if va else 0,
        "vec_b_dim": len(vb) if vb else 0,
    }


def _ngram_cosine(a: str, b: str) -> float:
    """n-gram 稀疏余弦（回退路径，兼容原 main.py 行为）。"""
    va = _ngram_dict(a)
    vb = _ngram_dict(b)
    common = set(va) & set(vb)
    dot = sum(va[g] * vb[g] for g in common)
    na = math.sqrt(sum(v * v for v in va.values())) or 1.0
    nb = math.sqrt(sum(v * v for v in vb.values())) or 1.0
    return dot / (na * nb)


def _ngram_dict(text: str, n: int = 2) -> dict[str, float]:
    t = text.lower()
    d: dict[str, float] = {}
    for i in range(len(t) - n + 1):
        g = t[i:i + n]
        d[g] = d.get(g, 0.0) + 1.0
    return d


# ──────────────────────────────────────────────
# 4. 主流程集成辅助：批量文本→向量（供 main.py 调用）
# ──────────────────────────────────────────────
def batch_embed(texts: list[str]) -> dict[str, Any]:
    """批量向量化（用于范式库全量向量化）。

    返回 {"vectors": {text: vec}, "mode": mode, "count": int, "failed": int}
    """
    result: dict[str, Any] = {}
    failed = 0
    mode_used = "none"
    for t in texts:
        vec, m = embed_text(t)
        if vec is None:
            failed += 1
        else:
            result[t] = vec
        if m != "none":
            mode_used = m
    return {"vectors": result, "mode": mode_used, "count": len(result), "failed": failed}


# ──────────────────────────────────────────────
# 5. 自测
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    print("=== 语义 embedding 自测 ===")
    print("环境 key:", "有" if os.environ.get("ZHIPU_API_KEY") else "无(回退 n-gram)")

    pairs = [
        ("控制系统", "反馈控制理论"),
        ("进化论", "自然选择"),
        ("量子力学", "叠加态"),
        ("系统论", "整体大于部分之和"),
        ("经济学", "供需关系"),
    ]
    for a, b in pairs:
        r = semantic_similarity(a, b)
        print(f"  {a} ~ {b}: {r['similarity']:.3f} [{r['mode']}]")

    print("batch_embed 自测:", batch_embed(["系统论", "控制论", "信息论"])["mode"])
    print("OK")
