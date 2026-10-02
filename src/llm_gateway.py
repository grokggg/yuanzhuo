#!/usr/bin/env python3
"""UHES LLM 网关（第16项优化：拆单体 + 多通道冗余）。

设计原则（顶尖工程实践）：
- 独立模块：LLM 调用从 main.py 拆出，单一职责，可独立测试。
- 多通道冗余：主模型 glm-4-flash + 备选模型（glm-4-plus / glm-4），
  主通道失败自动切换备选（网络/限流/超时容错）。
- 统一超时/重试：单次超时 _LLM_TIMEOUT，切换通道重试（最多 2 次）。
- 密钥安全：仅从环境变量读取（ZHIPU_API_KEY / ZHIPU_API_KEY_ALT），不入库。

使用：
    from llm_gateway import LLMGateway
    gw = LLMGateway()
    gw.chat_json(prompt, max_tokens=300)   # 自动多通道
"""

from __future__ import annotations

import json
import os
import urllib.request as _url_req
from typing import Any, Optional

# 智谱 API 配置（多通道）
_ZHIPU_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
# 主通道 + 备选通道（模型列表，按序尝试）
_MODEL_CHANNELS = [
    {"model": "glm-4-flash", "key_env": "ZHIPU_API_KEY"},
    {"model": "glm-4-plus", "key_env": "ZHIPU_API_KEY_ALT"},
    {"model": "glm-4-flash", "key_env": "ZHIPU_API_KEY_ALT"},
]
_LLM_TIMEOUT = 60


class LLMGateway:
    """多通道 LLM 网关（失败自动切换备选模型/密钥）。"""

    def __init__(self, timeout: int = _LLM_TIMEOUT):
        self.timeout = timeout
        self.channels = [dict(c) for c in _MODEL_CHANNELS]

    def _available_channels(self) -> list[dict[str, str]]:
        """可用通道：模型 + 对应密钥（环境变量存在才可用）。"""
        return [c for c in self.channels if os.environ.get(c["key_env"], "")]

    def chat_json(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        """
        last_err: Optional[Exception] = None
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        for ch in channels:
            try:
                return self._call_once(
                    ch["model"], os.environ.get(ch["key_env"], ""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
                continue
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def _call_once(self, model: str, key: str, prompt: str,
                   max_tokens: int, temperature: float) -> dict[str, Any]:
        """单通道调用（失败抛异常，由 chat_json 切换）。"""
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        req = _url_req.Request(
            _ZHIPU_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
            method="POST",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def chat_text(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Optional[Exception] = None
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        for ch in channels:
            try:
                return self._call_text_once(
                    ch["model"], os.environ.get(ch["key_env"], ""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def _call_text_once(self, model: str, key: str, prompt: str,
                        max_tokens: int, temperature: float) -> str:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        req = _url_req.Request(
            _ZHIPU_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
            method="POST",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def available(self) -> bool:
        """是否有可用通道。"""
        return bool(self._available_channels())

    def channel_summary(self) -> str:
        """通道摘要（不含密钥）。"""
        return " | ".join(f"{c['model']}({'✓' if os.environ.get(c['key_env'],'') else '✗'})"
                          for c in self.channels)


if __name__ == "__main__":
    gw = LLMGateway()
    print(f"[LLM-GATEWAY] 通道: {gw.channel_summary()}")
    print(f"可用: {gw.available()}")
    if gw.available():
        resp = gw.chat_json("只输出JSON: {\"status\": \"ok\"}", max_tokens=50)
        print(f"实测: {resp}")
