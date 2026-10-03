#!/usr/bin/env python3
"""API 鉴权测试（真实化清单第3步）。

锁鉴权契约：
- 未配置 UHES_API_KEY → 放行（本地开发模式，兼容现有）
- 配置 key + 无/错 X-API-Key → 401
- 配置 key + 正确 X-API-Key → 放行
"""

import json
import os
import sys
import threading
import time
import unittest
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_server import UHESApiServer  # noqa: E402

PORT = 8877  # 测试专用端口


class TestApiAuth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._old_key = os.environ.get("UHES_API_KEY")
        os.environ.pop("UHES_API_KEY", None)
        cls.server = UHESApiServer(port=PORT)
        cls.server.start()
        time.sleep(0.5)  # 等服务起来

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()
        if cls._old_key:
            os.environ["UHES_API_KEY"] = cls._old_key
        else:
            os.environ.pop("UHES_API_KEY", None)

    def _req(self, method: str, path: str, api_key: str | None = None,
             body: dict | None = None) -> tuple[int, dict]:
        url = f"http://127.0.0.1:{PORT}{path}"
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, method=method)
        if api_key:
            req.add_header("X-API-Key", api_key)
        if body:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_no_key_mode_allows(self):
        """未配置 UHES_API_KEY → POST /jobs 放行（本地模式）。"""
        code, body = self._req("POST", "/jobs", body={"case": "lit_review"})
        self.assertEqual(code, 202)

    def test_get_job_allows(self):
        """未配置 key → GET 放行。"""
        code, body = self._req("GET", "/jobs/nonexistent")
        self.assertEqual(code, 404)  # 能到业务层（job_not_found），非 401

    def test_with_key_rejects_missing(self):
        """配置 key + 无 X-API-Key → 401。"""
        os.environ["UHES_API_KEY"] = "test-secret-key"
        try:
            code, body = self._req("POST", "/jobs", body={"case": "lit_review"})
            self.assertEqual(code, 401)
            self.assertIn("unauthorized", body.get("error", ""))
        finally:
            os.environ.pop("UHES_API_KEY", None)

    def test_with_key_rejects_wrong(self):
        """配置 key + 错误 X-API-Key → 401。"""
        os.environ["UHES_API_KEY"] = "test-secret-key"
        try:
            code, body = self._req("POST", "/jobs", api_key="wrong-key",
                                   body={"case": "lit_review"})
            self.assertEqual(code, 401)
        finally:
            os.environ.pop("UHES_API_KEY", None)

    def test_with_key_accepts_correct(self):
        """配置 key + 正确 X-API-Key → 放行。"""
        os.environ["UHES_API_KEY"] = "test-secret-key"
        try:
            code, body = self._req("POST", "/jobs", api_key="test-secret-key",
                                   body={"case": "lit_review"})
            self.assertEqual(code, 202)
        finally:
            os.environ.pop("UHES_API_KEY", None)


if __name__ == "__main__":
    unittest.main()
