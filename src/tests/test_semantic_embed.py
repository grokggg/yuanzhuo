#!/usr/bin/env python3
"""semantic_embed 模块单元测试（真实化清单第2步）。

锁双模式契约：
- 无 key → n-gram 回退（mode='ngram'），不抛异常
- 有 key → 真语义（mode='semantic'），需 mock 智谱 API
- 空文本 → none
- 缓存生效（同文本不重复调用）
"""

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import semantic_embed as se


class TestSemanticEmbed(unittest.TestCase):
    def setUp(self):
        se._VEC_CACHE.clear()
        # 确保无 key（隔离测试）
        self._old_key = os.environ.get("ZHIPU_API_KEY")
        os.environ.pop("ZHIPU_API_KEY", None)

    def tearDown(self):
        if self._old_key:
            os.environ["ZHIPU_API_KEY"] = self._old_key
        else:
            os.environ.pop("ZHIPU_API_KEY", None)

    def test_no_key_returns_ngram(self):
        """无 key → n-gram 回退,不抛异常。"""
        vec, mode = se.embed_text("控制系统")
        self.assertEqual(mode, "ngram")
        self.assertIsNotNone(vec)
        self.assertGreater(len(vec), 0)

    def test_empty_text_returns_none(self):
        """空文本 → (None, 'none')。"""
        vec, mode = se.embed_text("   ")
        self.assertIsNone(vec)
        self.assertEqual(mode, "none")

    def test_similarity_ngram_mode(self):
        """无 key 相似度走 n-gram。"""
        r = se.semantic_similarity("系统论", "控制论")
        self.assertEqual(r["mode"], "ngram")
        self.assertGreaterEqual(r["similarity"], 0.0)
        self.assertLessEqual(r["similarity"], 1.0)

    def test_cache_used(self):
        """同文本二次调用走缓存（不重复 API）。"""
        se.embed_text("控制系统")
        cached = se._VEC_CACHE
        self.assertEqual(len(cached), 1)
        # 再调同文本,命中
        vec2, mode2 = se.embed_text("控制系统")
        self.assertEqual(len(cached), 1)
        self.assertEqual(mode2, "ngram")

    @patch.object(se, "_call_zhipu_embedding", return_value=[0.1] * 1024)
    def test_with_key_uses_semantic(self, mock_call):
        """有 key + API 成功 → 真语义 mode。"""
        os.environ["ZHIPU_API_KEY"] = "test-key"
        vec, mode = se.embed_text("控制系统")
        self.assertEqual(mode, "semantic")
        self.assertEqual(len(vec), 1024)
        mock_call.assert_called_once()

    @patch.object(se, "_call_zhipu_embedding", return_value=None)
    def test_api_failure_falls_back(self, mock_call):
        """有 key 但 API 失败 → 回退 n-gram（离线铁律）。"""
        os.environ["ZHIPU_API_KEY"] = "test-key"
        vec, mode = se.embed_text("控制系统")
        self.assertEqual(mode, "ngram")
        self.assertIsNotNone(vec)

    def test_batch_embed(self):
        """批量向量化契约。"""
        r = se.batch_embed(["系统论", "控制论", ""])
        self.assertEqual(r["count"], 2)
        self.assertEqual(r["failed"], 1)
        self.assertIn("mode", r)


if __name__ == "__main__":
    unittest.main()
