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

import hashlib
import json
import os
import urllib.request as _url_req
from typing import Any

# 智谱 API 配置（多通道）
_ZHIPU_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
# 主通道 + 备选通道（模型列表，按序尝试）
_MODEL_CHANNELS = [
    {"model": "glm-4-flash", "key_env": "ZHIPU_API_KEY"},
    {"model": "glm-4-plus", "key_env": "ZHIPU_API_KEY_ALT"},
    {"model": "glm-4-flash", "key_env": "ZHIPU_API_KEY_ALT"},
]
_LLM_TIMEOUT = 60
_CACHE_MAX = 200  # LLM 结果缓存上限(第20项优化) 


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_xǁLLMGatewayǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁLLMGatewayǁ_cache_key__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLLMGatewayǁ_cached_or__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLLMGatewayǁ_available_channels__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLLMGatewayǁchat_json__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLLMGatewayǁ_chat_json_uncached__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLLMGatewayǁ_call_once__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLLMGatewayǁchat_text__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLLMGatewayǁ_call_text_once__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLLMGatewayǁavailable__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLLMGatewayǁchannel_summary__mutmut: MutantDict = {}  # type: ignore


class LLMGateway:
    """多通道 LLM 网关（失败自动切换备选模型/密钥）。

    第20项优化：结果缓存（同 prompt 命中免重复调用,降延迟省配额）。
    """

    @_mutmut_mutated(mutants_xǁLLMGatewayǁ__init____mutmut)
    def __init__(self, timeout: int = _LLM_TIMEOUT, use_cache: bool = True) -> None:
        self.timeout = timeout
        self.channels = [dict(c) for c in _MODEL_CHANNELS]
        self.use_cache = use_cache
        self._cache: dict[str, dict[str, Any]] = {}

    def xǁLLMGatewayǁ__init____mutmut_orig(self, timeout: int = _LLM_TIMEOUT, use_cache: bool = True) -> None:
        self.timeout = timeout
        self.channels = [dict(c) for c in _MODEL_CHANNELS]
        self.use_cache = use_cache
        self._cache: dict[str, dict[str, Any]] = {}

    def xǁLLMGatewayǁ__init____mutmut_1(self, timeout: int = _LLM_TIMEOUT, use_cache: bool = False) -> None:
        self.timeout = timeout
        self.channels = [dict(c) for c in _MODEL_CHANNELS]
        self.use_cache = use_cache
        self._cache: dict[str, dict[str, Any]] = {}

    def xǁLLMGatewayǁ__init____mutmut_2(self, timeout: int = _LLM_TIMEOUT, use_cache: bool = True) -> None:
        self.timeout = None
        self.channels = [dict(c) for c in _MODEL_CHANNELS]
        self.use_cache = use_cache
        self._cache: dict[str, dict[str, Any]] = {}

    def xǁLLMGatewayǁ__init____mutmut_3(self, timeout: int = _LLM_TIMEOUT, use_cache: bool = True) -> None:
        self.timeout = timeout
        self.channels = None
        self.use_cache = use_cache
        self._cache: dict[str, dict[str, Any]] = {}

    def xǁLLMGatewayǁ__init____mutmut_4(self, timeout: int = _LLM_TIMEOUT, use_cache: bool = True) -> None:
        self.timeout = timeout
        self.channels = [dict(None) for c in _MODEL_CHANNELS]
        self.use_cache = use_cache
        self._cache: dict[str, dict[str, Any]] = {}

    def xǁLLMGatewayǁ__init____mutmut_5(self, timeout: int = _LLM_TIMEOUT, use_cache: bool = True) -> None:
        self.timeout = timeout
        self.channels = [dict(c) for c in _MODEL_CHANNELS]
        self.use_cache = None
        self._cache: dict[str, dict[str, Any]] = {}

    def xǁLLMGatewayǁ__init____mutmut_6(self, timeout: int = _LLM_TIMEOUT, use_cache: bool = True) -> None:
        self.timeout = timeout
        self.channels = [dict(c) for c in _MODEL_CHANNELS]
        self.use_cache = use_cache
        self._cache: dict[str, dict[str, Any]] = None

    @_mutmut_mutated(mutants_xǁLLMGatewayǁ_cache_key__mutmut)
    def _cache_key(self, model: str, prompt: str, max_tokens: int) -> str:
        return f"{model}:{max_tokens}:{hashlib.sha256(prompt.encode('utf-8')).hexdigest()}"

    def xǁLLMGatewayǁ_cache_key__mutmut_orig(self, model: str, prompt: str, max_tokens: int) -> str:
        return f"{model}:{max_tokens}:{hashlib.sha256(prompt.encode('utf-8')).hexdigest()}"

    def xǁLLMGatewayǁ_cache_key__mutmut_1(self, model: str, prompt: str, max_tokens: int) -> str:
        return f"{model}:{max_tokens}:{hashlib.sha256(None).hexdigest()}"

    def xǁLLMGatewayǁ_cache_key__mutmut_2(self, model: str, prompt: str, max_tokens: int) -> str:
        return f"{model}:{max_tokens}:{hashlib.sha256(prompt.encode(None)).hexdigest()}"

    def xǁLLMGatewayǁ_cache_key__mutmut_3(self, model: str, prompt: str, max_tokens: int) -> str:
        return f"{model}:{max_tokens}:{hashlib.sha256(prompt.encode('XXutf-8XX')).hexdigest()}"

    def xǁLLMGatewayǁ_cache_key__mutmut_4(self, model: str, prompt: str, max_tokens: int) -> str:
        return f"{model}:{max_tokens}:{hashlib.sha256(prompt.encode('UTF-8')).hexdigest()}"

    @_mutmut_mutated(mutants_xǁLLMGatewayǁ_cached_or__mutmut)
    def _cached_or(self, key: str, fn) -> dict[str, Any]:
        """缓存命中返回,未命中调用并缓存。"""
        if self.use_cache and key in self._cache:
            return dict(self._cache[key])
        result = fn()
        if self.use_cache and result:
            # 缓存有界:超过上限时淘汰最旧,直到回到上限内
            while len(self._cache) >= _CACHE_MAX:
                self._cache.pop(next(iter(self._cache)))
            self._cache[key] = dict(result)
        return result

    def xǁLLMGatewayǁ_cached_or__mutmut_orig(self, key: str, fn) -> dict[str, Any]:
        """缓存命中返回,未命中调用并缓存。"""
        if self.use_cache and key in self._cache:
            return dict(self._cache[key])
        result = fn()
        if self.use_cache and result:
            # 缓存有界:超过上限时淘汰最旧,直到回到上限内
            while len(self._cache) >= _CACHE_MAX:
                self._cache.pop(next(iter(self._cache)))
            self._cache[key] = dict(result)
        return result

    def xǁLLMGatewayǁ_cached_or__mutmut_1(self, key: str, fn) -> dict[str, Any]:
        """缓存命中返回,未命中调用并缓存。"""
        if self.use_cache or key in self._cache:
            return dict(self._cache[key])
        result = fn()
        if self.use_cache and result:
            # 缓存有界:超过上限时淘汰最旧,直到回到上限内
            while len(self._cache) >= _CACHE_MAX:
                self._cache.pop(next(iter(self._cache)))
            self._cache[key] = dict(result)
        return result

    def xǁLLMGatewayǁ_cached_or__mutmut_2(self, key: str, fn) -> dict[str, Any]:
        """缓存命中返回,未命中调用并缓存。"""
        if self.use_cache and key not in self._cache:
            return dict(self._cache[key])
        result = fn()
        if self.use_cache and result:
            # 缓存有界:超过上限时淘汰最旧,直到回到上限内
            while len(self._cache) >= _CACHE_MAX:
                self._cache.pop(next(iter(self._cache)))
            self._cache[key] = dict(result)
        return result

    def xǁLLMGatewayǁ_cached_or__mutmut_3(self, key: str, fn) -> dict[str, Any]:
        """缓存命中返回,未命中调用并缓存。"""
        if self.use_cache and key in self._cache:
            return dict(None)
        result = fn()
        if self.use_cache and result:
            # 缓存有界:超过上限时淘汰最旧,直到回到上限内
            while len(self._cache) >= _CACHE_MAX:
                self._cache.pop(next(iter(self._cache)))
            self._cache[key] = dict(result)
        return result

    def xǁLLMGatewayǁ_cached_or__mutmut_4(self, key: str, fn) -> dict[str, Any]:
        """缓存命中返回,未命中调用并缓存。"""
        if self.use_cache and key in self._cache:
            return dict(self._cache[key])
        result = None
        if self.use_cache and result:
            # 缓存有界:超过上限时淘汰最旧,直到回到上限内
            while len(self._cache) >= _CACHE_MAX:
                self._cache.pop(next(iter(self._cache)))
            self._cache[key] = dict(result)
        return result

    def xǁLLMGatewayǁ_cached_or__mutmut_5(self, key: str, fn) -> dict[str, Any]:
        """缓存命中返回,未命中调用并缓存。"""
        if self.use_cache and key in self._cache:
            return dict(self._cache[key])
        result = fn()
        if self.use_cache or result:
            # 缓存有界:超过上限时淘汰最旧,直到回到上限内
            while len(self._cache) >= _CACHE_MAX:
                self._cache.pop(next(iter(self._cache)))
            self._cache[key] = dict(result)
        return result

    def xǁLLMGatewayǁ_cached_or__mutmut_6(self, key: str, fn) -> dict[str, Any]:
        """缓存命中返回,未命中调用并缓存。"""
        if self.use_cache and key in self._cache:
            return dict(self._cache[key])
        result = fn()
        if self.use_cache and result:
            # 缓存有界:超过上限时淘汰最旧,直到回到上限内
            while len(self._cache) > _CACHE_MAX:
                self._cache.pop(next(iter(self._cache)))
            self._cache[key] = dict(result)
        return result

    def xǁLLMGatewayǁ_cached_or__mutmut_7(self, key: str, fn) -> dict[str, Any]:
        """缓存命中返回,未命中调用并缓存。"""
        if self.use_cache and key in self._cache:
            return dict(self._cache[key])
        result = fn()
        if self.use_cache and result:
            # 缓存有界:超过上限时淘汰最旧,直到回到上限内
            while len(self._cache) >= _CACHE_MAX:
                self._cache.pop(None)
            self._cache[key] = dict(result)
        return result

    def xǁLLMGatewayǁ_cached_or__mutmut_8(self, key: str, fn) -> dict[str, Any]:
        """缓存命中返回,未命中调用并缓存。"""
        if self.use_cache and key in self._cache:
            return dict(self._cache[key])
        result = fn()
        if self.use_cache and result:
            # 缓存有界:超过上限时淘汰最旧,直到回到上限内
            while len(self._cache) >= _CACHE_MAX:
                self._cache.pop(next(None))
            self._cache[key] = dict(result)
        return result

    def xǁLLMGatewayǁ_cached_or__mutmut_9(self, key: str, fn) -> dict[str, Any]:
        """缓存命中返回,未命中调用并缓存。"""
        if self.use_cache and key in self._cache:
            return dict(self._cache[key])
        result = fn()
        if self.use_cache and result:
            # 缓存有界:超过上限时淘汰最旧,直到回到上限内
            while len(self._cache) >= _CACHE_MAX:
                self._cache.pop(next(iter(None)))
            self._cache[key] = dict(result)
        return result

    def xǁLLMGatewayǁ_cached_or__mutmut_10(self, key: str, fn) -> dict[str, Any]:
        """缓存命中返回,未命中调用并缓存。"""
        if self.use_cache and key in self._cache:
            return dict(self._cache[key])
        result = fn()
        if self.use_cache and result:
            # 缓存有界:超过上限时淘汰最旧,直到回到上限内
            while len(self._cache) >= _CACHE_MAX:
                self._cache.pop(next(iter(self._cache)))
            self._cache[key] = None
        return result

    def xǁLLMGatewayǁ_cached_or__mutmut_11(self, key: str, fn) -> dict[str, Any]:
        """缓存命中返回,未命中调用并缓存。"""
        if self.use_cache and key in self._cache:
            return dict(self._cache[key])
        result = fn()
        if self.use_cache and result:
            # 缓存有界:超过上限时淘汰最旧,直到回到上限内
            while len(self._cache) >= _CACHE_MAX:
                self._cache.pop(next(iter(self._cache)))
            self._cache[key] = dict(None)
        return result

    @_mutmut_mutated(mutants_xǁLLMGatewayǁ_available_channels__mutmut)
    def _available_channels(self) -> list[dict[str, str]]:
        """可用通道：模型 + 对应密钥（环境变量存在才可用）。"""
        return [c for c in self.channels if os.environ.get(c["key_env"], "")]

    def xǁLLMGatewayǁ_available_channels__mutmut_orig(self) -> list[dict[str, str]]:
        """可用通道：模型 + 对应密钥（环境变量存在才可用）。"""
        return [c for c in self.channels if os.environ.get(c["key_env"], "")]

    def xǁLLMGatewayǁ_available_channels__mutmut_1(self) -> list[dict[str, str]]:
        """可用通道：模型 + 对应密钥（环境变量存在才可用）。"""
        return [c for c in self.channels if os.environ.get(None, "")]

    def xǁLLMGatewayǁ_available_channels__mutmut_2(self) -> list[dict[str, str]]:
        """可用通道：模型 + 对应密钥（环境变量存在才可用）。"""
        return [c for c in self.channels if os.environ.get(c["key_env"], None)]

    def xǁLLMGatewayǁ_available_channels__mutmut_3(self) -> list[dict[str, str]]:
        """可用通道：模型 + 对应密钥（环境变量存在才可用）。"""
        return [c for c in self.channels if os.environ.get("")]

    def xǁLLMGatewayǁ_available_channels__mutmut_4(self) -> list[dict[str, str]]:
        """可用通道：模型 + 对应密钥（环境变量存在才可用）。"""
        return [c for c in self.channels if os.environ.get(c["key_env"], )]

    def xǁLLMGatewayǁ_available_channels__mutmut_5(self) -> list[dict[str, str]]:
        """可用通道：模型 + 对应密钥（环境变量存在才可用）。"""
        return [c for c in self.channels if os.environ.get(c["XXkey_envXX"], "")]

    def xǁLLMGatewayǁ_available_channels__mutmut_6(self) -> list[dict[str, str]]:
        """可用通道：模型 + 对应密钥（环境变量存在才可用）。"""
        return [c for c in self.channels if os.environ.get(c["KEY_ENV"], "")]

    def xǁLLMGatewayǁ_available_channels__mutmut_7(self) -> list[dict[str, str]]:
        """可用通道：模型 + 对应密钥（环境变量存在才可用）。"""
        return [c for c in self.channels if os.environ.get(c["key_env"], "XXXX")]

    @_mutmut_mutated(mutants_xǁLLMGatewayǁchat_json__mutmut)
    def chat_json(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(channels[0]["model"], prompt, max_tokens)
        return self._cached_or(cache_key, lambda: self._chat_json_uncached(
            prompt, max_tokens, temperature))

    def xǁLLMGatewayǁchat_json__mutmut_orig(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(channels[0]["model"], prompt, max_tokens)
        return self._cached_or(cache_key, lambda: self._chat_json_uncached(
            prompt, max_tokens, temperature))

    def xǁLLMGatewayǁchat_json__mutmut_1(self, prompt: str, max_tokens: int = 301,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(channels[0]["model"], prompt, max_tokens)
        return self._cached_or(cache_key, lambda: self._chat_json_uncached(
            prompt, max_tokens, temperature))

    def xǁLLMGatewayǁchat_json__mutmut_2(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 1.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(channels[0]["model"], prompt, max_tokens)
        return self._cached_or(cache_key, lambda: self._chat_json_uncached(
            prompt, max_tokens, temperature))

    def xǁLLMGatewayǁchat_json__mutmut_3(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = None
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(channels[0]["model"], prompt, max_tokens)
        return self._cached_or(cache_key, lambda: self._chat_json_uncached(
            prompt, max_tokens, temperature))

    def xǁLLMGatewayǁchat_json__mutmut_4(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(channels[0]["model"], prompt, max_tokens)
        return self._cached_or(cache_key, lambda: self._chat_json_uncached(
            prompt, max_tokens, temperature))

    def xǁLLMGatewayǁchat_json__mutmut_5(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if not channels:
            raise RuntimeError(None)
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(channels[0]["model"], prompt, max_tokens)
        return self._cached_or(cache_key, lambda: self._chat_json_uncached(
            prompt, max_tokens, temperature))

    def xǁLLMGatewayǁchat_json__mutmut_6(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("XX无可用 LLM 通道（ZHIPU_API_KEY 未设置）XX")
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(channels[0]["model"], prompt, max_tokens)
        return self._cached_or(cache_key, lambda: self._chat_json_uncached(
            prompt, max_tokens, temperature))

    def xǁLLMGatewayǁchat_json__mutmut_7(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 llm 通道（zhipu_api_key 未设置）")
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(channels[0]["model"], prompt, max_tokens)
        return self._cached_or(cache_key, lambda: self._chat_json_uncached(
            prompt, max_tokens, temperature))

    def xǁLLMGatewayǁchat_json__mutmut_8(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        # 缓存键基于主通道(首个可用)
        cache_key = None
        return self._cached_or(cache_key, lambda: self._chat_json_uncached(
            prompt, max_tokens, temperature))

    def xǁLLMGatewayǁchat_json__mutmut_9(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(None, prompt, max_tokens)
        return self._cached_or(cache_key, lambda: self._chat_json_uncached(
            prompt, max_tokens, temperature))

    def xǁLLMGatewayǁchat_json__mutmut_10(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(channels[0]["model"], None, max_tokens)
        return self._cached_or(cache_key, lambda: self._chat_json_uncached(
            prompt, max_tokens, temperature))

    def xǁLLMGatewayǁchat_json__mutmut_11(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(channels[0]["model"], prompt, None)
        return self._cached_or(cache_key, lambda: self._chat_json_uncached(
            prompt, max_tokens, temperature))

    def xǁLLMGatewayǁchat_json__mutmut_12(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(prompt, max_tokens)
        return self._cached_or(cache_key, lambda: self._chat_json_uncached(
            prompt, max_tokens, temperature))

    def xǁLLMGatewayǁchat_json__mutmut_13(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(channels[0]["model"], max_tokens)
        return self._cached_or(cache_key, lambda: self._chat_json_uncached(
            prompt, max_tokens, temperature))

    def xǁLLMGatewayǁchat_json__mutmut_14(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(channels[0]["model"], prompt, )
        return self._cached_or(cache_key, lambda: self._chat_json_uncached(
            prompt, max_tokens, temperature))

    def xǁLLMGatewayǁchat_json__mutmut_15(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(channels[1]["model"], prompt, max_tokens)
        return self._cached_or(cache_key, lambda: self._chat_json_uncached(
            prompt, max_tokens, temperature))

    def xǁLLMGatewayǁchat_json__mutmut_16(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(channels[0]["XXmodelXX"], prompt, max_tokens)
        return self._cached_or(cache_key, lambda: self._chat_json_uncached(
            prompt, max_tokens, temperature))

    def xǁLLMGatewayǁchat_json__mutmut_17(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(channels[0]["MODEL"], prompt, max_tokens)
        return self._cached_or(cache_key, lambda: self._chat_json_uncached(
            prompt, max_tokens, temperature))

    def xǁLLMGatewayǁchat_json__mutmut_18(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(channels[0]["model"], prompt, max_tokens)
        return self._cached_or(None, lambda: self._chat_json_uncached(
            prompt, max_tokens, temperature))

    def xǁLLMGatewayǁchat_json__mutmut_19(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(channels[0]["model"], prompt, max_tokens)
        return self._cached_or(cache_key, None)

    def xǁLLMGatewayǁchat_json__mutmut_20(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(channels[0]["model"], prompt, max_tokens)
        return self._cached_or(lambda: self._chat_json_uncached(
            prompt, max_tokens, temperature))

    def xǁLLMGatewayǁchat_json__mutmut_21(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(channels[0]["model"], prompt, max_tokens)
        return self._cached_or(cache_key, )

    def xǁLLMGatewayǁchat_json__mutmut_22(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(channels[0]["model"], prompt, max_tokens)
        return self._cached_or(cache_key, lambda: None)

    def xǁLLMGatewayǁchat_json__mutmut_23(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(channels[0]["model"], prompt, max_tokens)
        return self._cached_or(cache_key, lambda: self._chat_json_uncached(
            None, max_tokens, temperature))

    def xǁLLMGatewayǁchat_json__mutmut_24(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(channels[0]["model"], prompt, max_tokens)
        return self._cached_or(cache_key, lambda: self._chat_json_uncached(
            prompt, None, temperature))

    def xǁLLMGatewayǁchat_json__mutmut_25(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(channels[0]["model"], prompt, max_tokens)
        return self._cached_or(cache_key, lambda: self._chat_json_uncached(
            prompt, max_tokens, None))

    def xǁLLMGatewayǁchat_json__mutmut_26(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(channels[0]["model"], prompt, max_tokens)
        return self._cached_or(cache_key, lambda: self._chat_json_uncached(
            max_tokens, temperature))

    def xǁLLMGatewayǁchat_json__mutmut_27(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(channels[0]["model"], prompt, max_tokens)
        return self._cached_or(cache_key, lambda: self._chat_json_uncached(
            prompt, temperature))

    def xǁLLMGatewayǁchat_json__mutmut_28(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> dict[str, Any]:
        """调用 LLM 返回 JSON（多通道容错 + 第20项缓存）。

        按通道序尝试：主通道失败 → 备选通道；全部失败抛异常。
        同 prompt 命中缓存直接返回（降延迟省配额）。
        """
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        # 缓存键基于主通道(首个可用)
        cache_key = self._cache_key(channels[0]["model"], prompt, max_tokens)
        return self._cached_or(cache_key, lambda: self._chat_json_uncached(
            prompt, max_tokens, ))

    @_mutmut_mutated(mutants_xǁLLMGatewayǁ_chat_json_uncached__mutmut)
    def _chat_json_uncached(self, prompt: str, max_tokens: int,
                            temperature: float) -> dict[str, Any]:
        """未命中缓存的 JSON 调用（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        for ch in channels:
            try:
                return self._call_once(
                    ch["model"], os.environ.get(ch["key_env"], ""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
                continue
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁ_chat_json_uncached__mutmut_orig(self, prompt: str, max_tokens: int,
                            temperature: float) -> dict[str, Any]:
        """未命中缓存的 JSON 调用（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        for ch in channels:
            try:
                return self._call_once(
                    ch["model"], os.environ.get(ch["key_env"], ""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
                continue
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁ_chat_json_uncached__mutmut_1(self, prompt: str, max_tokens: int,
                            temperature: float) -> dict[str, Any]:
        """未命中缓存的 JSON 调用（多通道容错）。"""
        last_err: Exception | None = ""
        channels = self._available_channels()
        for ch in channels:
            try:
                return self._call_once(
                    ch["model"], os.environ.get(ch["key_env"], ""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
                continue
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁ_chat_json_uncached__mutmut_2(self, prompt: str, max_tokens: int,
                            temperature: float) -> dict[str, Any]:
        """未命中缓存的 JSON 调用（多通道容错）。"""
        last_err: Exception | None = None
        channels = None
        for ch in channels:
            try:
                return self._call_once(
                    ch["model"], os.environ.get(ch["key_env"], ""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
                continue
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁ_chat_json_uncached__mutmut_3(self, prompt: str, max_tokens: int,
                            temperature: float) -> dict[str, Any]:
        """未命中缓存的 JSON 调用（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        for ch in channels:
            try:
                return self._call_once(
                    None, os.environ.get(ch["key_env"], ""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
                continue
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁ_chat_json_uncached__mutmut_4(self, prompt: str, max_tokens: int,
                            temperature: float) -> dict[str, Any]:
        """未命中缓存的 JSON 调用（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        for ch in channels:
            try:
                return self._call_once(
                    ch["model"], None,
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
                continue
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁ_chat_json_uncached__mutmut_5(self, prompt: str, max_tokens: int,
                            temperature: float) -> dict[str, Any]:
        """未命中缓存的 JSON 调用（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        for ch in channels:
            try:
                return self._call_once(
                    ch["model"], os.environ.get(ch["key_env"], ""),
                    None, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
                continue
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁ_chat_json_uncached__mutmut_6(self, prompt: str, max_tokens: int,
                            temperature: float) -> dict[str, Any]:
        """未命中缓存的 JSON 调用（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        for ch in channels:
            try:
                return self._call_once(
                    ch["model"], os.environ.get(ch["key_env"], ""),
                    prompt, None, temperature)
            except Exception as exc:
                last_err = exc
                continue
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁ_chat_json_uncached__mutmut_7(self, prompt: str, max_tokens: int,
                            temperature: float) -> dict[str, Any]:
        """未命中缓存的 JSON 调用（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        for ch in channels:
            try:
                return self._call_once(
                    ch["model"], os.environ.get(ch["key_env"], ""),
                    prompt, max_tokens, None)
            except Exception as exc:
                last_err = exc
                continue
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁ_chat_json_uncached__mutmut_8(self, prompt: str, max_tokens: int,
                            temperature: float) -> dict[str, Any]:
        """未命中缓存的 JSON 调用（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        for ch in channels:
            try:
                return self._call_once(
                    os.environ.get(ch["key_env"], ""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
                continue
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁ_chat_json_uncached__mutmut_9(self, prompt: str, max_tokens: int,
                            temperature: float) -> dict[str, Any]:
        """未命中缓存的 JSON 调用（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        for ch in channels:
            try:
                return self._call_once(
                    ch["model"], prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
                continue
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁ_chat_json_uncached__mutmut_10(self, prompt: str, max_tokens: int,
                            temperature: float) -> dict[str, Any]:
        """未命中缓存的 JSON 调用（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        for ch in channels:
            try:
                return self._call_once(
                    ch["model"], os.environ.get(ch["key_env"], ""),
                    max_tokens, temperature)
            except Exception as exc:
                last_err = exc
                continue
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁ_chat_json_uncached__mutmut_11(self, prompt: str, max_tokens: int,
                            temperature: float) -> dict[str, Any]:
        """未命中缓存的 JSON 调用（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        for ch in channels:
            try:
                return self._call_once(
                    ch["model"], os.environ.get(ch["key_env"], ""),
                    prompt, temperature)
            except Exception as exc:
                last_err = exc
                continue
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁ_chat_json_uncached__mutmut_12(self, prompt: str, max_tokens: int,
                            temperature: float) -> dict[str, Any]:
        """未命中缓存的 JSON 调用（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        for ch in channels:
            try:
                return self._call_once(
                    ch["model"], os.environ.get(ch["key_env"], ""),
                    prompt, max_tokens, )
            except Exception as exc:
                last_err = exc
                continue
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁ_chat_json_uncached__mutmut_13(self, prompt: str, max_tokens: int,
                            temperature: float) -> dict[str, Any]:
        """未命中缓存的 JSON 调用（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        for ch in channels:
            try:
                return self._call_once(
                    ch["XXmodelXX"], os.environ.get(ch["key_env"], ""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
                continue
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁ_chat_json_uncached__mutmut_14(self, prompt: str, max_tokens: int,
                            temperature: float) -> dict[str, Any]:
        """未命中缓存的 JSON 调用（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        for ch in channels:
            try:
                return self._call_once(
                    ch["MODEL"], os.environ.get(ch["key_env"], ""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
                continue
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁ_chat_json_uncached__mutmut_15(self, prompt: str, max_tokens: int,
                            temperature: float) -> dict[str, Any]:
        """未命中缓存的 JSON 调用（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        for ch in channels:
            try:
                return self._call_once(
                    ch["model"], os.environ.get(None, ""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
                continue
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁ_chat_json_uncached__mutmut_16(self, prompt: str, max_tokens: int,
                            temperature: float) -> dict[str, Any]:
        """未命中缓存的 JSON 调用（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        for ch in channels:
            try:
                return self._call_once(
                    ch["model"], os.environ.get(ch["key_env"], None),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
                continue
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁ_chat_json_uncached__mutmut_17(self, prompt: str, max_tokens: int,
                            temperature: float) -> dict[str, Any]:
        """未命中缓存的 JSON 调用（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        for ch in channels:
            try:
                return self._call_once(
                    ch["model"], os.environ.get(""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
                continue
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁ_chat_json_uncached__mutmut_18(self, prompt: str, max_tokens: int,
                            temperature: float) -> dict[str, Any]:
        """未命中缓存的 JSON 调用（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        for ch in channels:
            try:
                return self._call_once(
                    ch["model"], os.environ.get(ch["key_env"], ),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
                continue
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁ_chat_json_uncached__mutmut_19(self, prompt: str, max_tokens: int,
                            temperature: float) -> dict[str, Any]:
        """未命中缓存的 JSON 调用（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        for ch in channels:
            try:
                return self._call_once(
                    ch["model"], os.environ.get(ch["XXkey_envXX"], ""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
                continue
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁ_chat_json_uncached__mutmut_20(self, prompt: str, max_tokens: int,
                            temperature: float) -> dict[str, Any]:
        """未命中缓存的 JSON 调用（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        for ch in channels:
            try:
                return self._call_once(
                    ch["model"], os.environ.get(ch["KEY_ENV"], ""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
                continue
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁ_chat_json_uncached__mutmut_21(self, prompt: str, max_tokens: int,
                            temperature: float) -> dict[str, Any]:
        """未命中缓存的 JSON 调用（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        for ch in channels:
            try:
                return self._call_once(
                    ch["model"], os.environ.get(ch["key_env"], "XXXX"),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
                continue
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁ_chat_json_uncached__mutmut_22(self, prompt: str, max_tokens: int,
                            temperature: float) -> dict[str, Any]:
        """未命中缓存的 JSON 调用（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        for ch in channels:
            try:
                return self._call_once(
                    ch["model"], os.environ.get(ch["key_env"], ""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = None
                continue
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁ_chat_json_uncached__mutmut_23(self, prompt: str, max_tokens: int,
                            temperature: float) -> dict[str, Any]:
        """未命中缓存的 JSON 调用（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        for ch in channels:
            try:
                return self._call_once(
                    ch["model"], os.environ.get(ch["key_env"], ""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
                break
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁ_chat_json_uncached__mutmut_24(self, prompt: str, max_tokens: int,
                            temperature: float) -> dict[str, Any]:
        """未命中缓存的 JSON 调用（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        for ch in channels:
            try:
                return self._call_once(
                    ch["model"], os.environ.get(ch["key_env"], ""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
                continue
        raise RuntimeError(None)

    @_mutmut_mutated(mutants_xǁLLMGatewayǁ_call_once__mutmut)
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

    def xǁLLMGatewayǁ_call_once__mutmut_orig(self, model: str, key: str, prompt: str,
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

    def xǁLLMGatewayǁ_call_once__mutmut_1(self, model: str, key: str, prompt: str,
                   max_tokens: int, temperature: float) -> dict[str, Any]:
        """单通道调用（失败抛异常，由 chat_json 切换）。"""
        payload = None
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

    def xǁLLMGatewayǁ_call_once__mutmut_2(self, model: str, key: str, prompt: str,
                   max_tokens: int, temperature: float) -> dict[str, Any]:
        """单通道调用（失败抛异常，由 chat_json 切换）。"""
        payload = {
            "XXmodelXX": model,
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

    def xǁLLMGatewayǁ_call_once__mutmut_3(self, model: str, key: str, prompt: str,
                   max_tokens: int, temperature: float) -> dict[str, Any]:
        """单通道调用（失败抛异常，由 chat_json 切换）。"""
        payload = {
            "MODEL": model,
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

    def xǁLLMGatewayǁ_call_once__mutmut_4(self, model: str, key: str, prompt: str,
                   max_tokens: int, temperature: float) -> dict[str, Any]:
        """单通道调用（失败抛异常，由 chat_json 切换）。"""
        payload = {
            "model": model,
            "XXmessagesXX": [{"role": "user", "content": prompt}],
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

    def xǁLLMGatewayǁ_call_once__mutmut_5(self, model: str, key: str, prompt: str,
                   max_tokens: int, temperature: float) -> dict[str, Any]:
        """单通道调用（失败抛异常，由 chat_json 切换）。"""
        payload = {
            "model": model,
            "MESSAGES": [{"role": "user", "content": prompt}],
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

    def xǁLLMGatewayǁ_call_once__mutmut_6(self, model: str, key: str, prompt: str,
                   max_tokens: int, temperature: float) -> dict[str, Any]:
        """单通道调用（失败抛异常，由 chat_json 切换）。"""
        payload = {
            "model": model,
            "messages": [{"XXroleXX": "user", "content": prompt}],
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

    def xǁLLMGatewayǁ_call_once__mutmut_7(self, model: str, key: str, prompt: str,
                   max_tokens: int, temperature: float) -> dict[str, Any]:
        """单通道调用（失败抛异常，由 chat_json 切换）。"""
        payload = {
            "model": model,
            "messages": [{"ROLE": "user", "content": prompt}],
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

    def xǁLLMGatewayǁ_call_once__mutmut_8(self, model: str, key: str, prompt: str,
                   max_tokens: int, temperature: float) -> dict[str, Any]:
        """单通道调用（失败抛异常，由 chat_json 切换）。"""
        payload = {
            "model": model,
            "messages": [{"role": "XXuserXX", "content": prompt}],
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

    def xǁLLMGatewayǁ_call_once__mutmut_9(self, model: str, key: str, prompt: str,
                   max_tokens: int, temperature: float) -> dict[str, Any]:
        """单通道调用（失败抛异常，由 chat_json 切换）。"""
        payload = {
            "model": model,
            "messages": [{"role": "USER", "content": prompt}],
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

    def xǁLLMGatewayǁ_call_once__mutmut_10(self, model: str, key: str, prompt: str,
                   max_tokens: int, temperature: float) -> dict[str, Any]:
        """单通道调用（失败抛异常，由 chat_json 切换）。"""
        payload = {
            "model": model,
            "messages": [{"role": "user", "XXcontentXX": prompt}],
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

    def xǁLLMGatewayǁ_call_once__mutmut_11(self, model: str, key: str, prompt: str,
                   max_tokens: int, temperature: float) -> dict[str, Any]:
        """单通道调用（失败抛异常，由 chat_json 切换）。"""
        payload = {
            "model": model,
            "messages": [{"role": "user", "CONTENT": prompt}],
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

    def xǁLLMGatewayǁ_call_once__mutmut_12(self, model: str, key: str, prompt: str,
                   max_tokens: int, temperature: float) -> dict[str, Any]:
        """单通道调用（失败抛异常，由 chat_json 切换）。"""
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "XXmax_tokensXX": max_tokens,
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

    def xǁLLMGatewayǁ_call_once__mutmut_13(self, model: str, key: str, prompt: str,
                   max_tokens: int, temperature: float) -> dict[str, Any]:
        """单通道调用（失败抛异常，由 chat_json 切换）。"""
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "MAX_TOKENS": max_tokens,
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

    def xǁLLMGatewayǁ_call_once__mutmut_14(self, model: str, key: str, prompt: str,
                   max_tokens: int, temperature: float) -> dict[str, Any]:
        """单通道调用（失败抛异常，由 chat_json 切换）。"""
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "XXtemperatureXX": temperature,
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

    def xǁLLMGatewayǁ_call_once__mutmut_15(self, model: str, key: str, prompt: str,
                   max_tokens: int, temperature: float) -> dict[str, Any]:
        """单通道调用（失败抛异常，由 chat_json 切换）。"""
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "TEMPERATURE": temperature,
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

    def xǁLLMGatewayǁ_call_once__mutmut_16(self, model: str, key: str, prompt: str,
                   max_tokens: int, temperature: float) -> dict[str, Any]:
        """单通道调用（失败抛异常，由 chat_json 切换）。"""
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        req = None
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_17(self, model: str, key: str, prompt: str,
                   max_tokens: int, temperature: float) -> dict[str, Any]:
        """单通道调用（失败抛异常，由 chat_json 切换）。"""
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        req = _url_req.Request(
            None,
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

    def xǁLLMGatewayǁ_call_once__mutmut_18(self, model: str, key: str, prompt: str,
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
            data=None,
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

    def xǁLLMGatewayǁ_call_once__mutmut_19(self, model: str, key: str, prompt: str,
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
            headers=None,
            method="POST",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_20(self, model: str, key: str, prompt: str,
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
            method=None,
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_21(self, model: str, key: str, prompt: str,
                   max_tokens: int, temperature: float) -> dict[str, Any]:
        """单通道调用（失败抛异常，由 chat_json 切换）。"""
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        req = _url_req.Request(
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

    def xǁLLMGatewayǁ_call_once__mutmut_22(self, model: str, key: str, prompt: str,
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

    def xǁLLMGatewayǁ_call_once__mutmut_23(self, model: str, key: str, prompt: str,
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
            method="POST",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_24(self, model: str, key: str, prompt: str,
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
            )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_25(self, model: str, key: str, prompt: str,
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
            data=json.dumps(payload).encode(None),
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

    def xǁLLMGatewayǁ_call_once__mutmut_26(self, model: str, key: str, prompt: str,
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
            data=json.dumps(None).encode("utf-8"),
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

    def xǁLLMGatewayǁ_call_once__mutmut_27(self, model: str, key: str, prompt: str,
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
            data=json.dumps(payload).encode("XXutf-8XX"),
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

    def xǁLLMGatewayǁ_call_once__mutmut_28(self, model: str, key: str, prompt: str,
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
            data=json.dumps(payload).encode("UTF-8"),
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

    def xǁLLMGatewayǁ_call_once__mutmut_29(self, model: str, key: str, prompt: str,
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
            headers={"XXAuthorizationXX": f"Bearer {key}",
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

    def xǁLLMGatewayǁ_call_once__mutmut_30(self, model: str, key: str, prompt: str,
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
            headers={"authorization": f"Bearer {key}",
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

    def xǁLLMGatewayǁ_call_once__mutmut_31(self, model: str, key: str, prompt: str,
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
            headers={"AUTHORIZATION": f"Bearer {key}",
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

    def xǁLLMGatewayǁ_call_once__mutmut_32(self, model: str, key: str, prompt: str,
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
                     "XXContent-TypeXX": "application/json"},
            method="POST",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_33(self, model: str, key: str, prompt: str,
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
                     "content-type": "application/json"},
            method="POST",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_34(self, model: str, key: str, prompt: str,
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
                     "CONTENT-TYPE": "application/json"},
            method="POST",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_35(self, model: str, key: str, prompt: str,
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
                     "Content-Type": "XXapplication/jsonXX"},
            method="POST",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_36(self, model: str, key: str, prompt: str,
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
                     "Content-Type": "APPLICATION/JSON"},
            method="POST",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_37(self, model: str, key: str, prompt: str,
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
            method="XXPOSTXX",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_38(self, model: str, key: str, prompt: str,
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
            method="post",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_39(self, model: str, key: str, prompt: str,
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
        with _url_req.urlopen(None, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_40(self, model: str, key: str, prompt: str,
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
        with _url_req.urlopen(req, timeout=None) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_41(self, model: str, key: str, prompt: str,
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
        with _url_req.urlopen(timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_42(self, model: str, key: str, prompt: str,
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
        with _url_req.urlopen(req, ) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_43(self, model: str, key: str, prompt: str,
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
            data = None
        content = data["choices"][0]["message"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_44(self, model: str, key: str, prompt: str,
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
            data = json.loads(None)
        content = data["choices"][0]["message"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_45(self, model: str, key: str, prompt: str,
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
            data = json.loads(resp.read().decode(None))
        content = data["choices"][0]["message"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_46(self, model: str, key: str, prompt: str,
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
            data = json.loads(resp.read().decode("XXutf-8XX"))
        content = data["choices"][0]["message"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_47(self, model: str, key: str, prompt: str,
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
            data = json.loads(resp.read().decode("UTF-8"))
        content = data["choices"][0]["message"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_48(self, model: str, key: str, prompt: str,
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
        content = None
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_49(self, model: str, key: str, prompt: str,
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
        content = data["XXchoicesXX"][0]["message"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_50(self, model: str, key: str, prompt: str,
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
        content = data["CHOICES"][0]["message"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_51(self, model: str, key: str, prompt: str,
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
        content = data["choices"][1]["message"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_52(self, model: str, key: str, prompt: str,
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
        content = data["choices"][0]["XXmessageXX"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_53(self, model: str, key: str, prompt: str,
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
        content = data["choices"][0]["MESSAGE"]["content"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_54(self, model: str, key: str, prompt: str,
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
        content = data["choices"][0]["message"]["XXcontentXX"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_55(self, model: str, key: str, prompt: str,
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
        content = data["choices"][0]["message"]["CONTENT"].strip()
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_56(self, model: str, key: str, prompt: str,
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
        start, end = None
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_57(self, model: str, key: str, prompt: str,
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
        start, end = content.find(None), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_58(self, model: str, key: str, prompt: str,
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
        start, end = content.rfind("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_59(self, model: str, key: str, prompt: str,
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
        start, end = content.find("XX{XX"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_60(self, model: str, key: str, prompt: str,
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
        start, end = content.find("{"), content.rfind(None)
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_61(self, model: str, key: str, prompt: str,
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
        start, end = content.find("{"), content.find("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_62(self, model: str, key: str, prompt: str,
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
        start, end = content.find("{"), content.rfind("XX}XX")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_63(self, model: str, key: str, prompt: str,
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
        if start >= 0 or end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_64(self, model: str, key: str, prompt: str,
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
        if start > 0 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_65(self, model: str, key: str, prompt: str,
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
        if start >= 1 and end > start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_66(self, model: str, key: str, prompt: str,
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
        if start >= 0 and end >= start:
            return json.loads(content[start:end + 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_67(self, model: str, key: str, prompt: str,
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
            return json.loads(None)
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_68(self, model: str, key: str, prompt: str,
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
            return json.loads(content[start:end - 1])
        return {}

    def xǁLLMGatewayǁ_call_once__mutmut_69(self, model: str, key: str, prompt: str,
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
            return json.loads(content[start:end + 2])
        return {}

    @_mutmut_mutated(mutants_xǁLLMGatewayǁchat_text__mutmut)
    def chat_text(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
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

    def xǁLLMGatewayǁchat_text__mutmut_orig(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
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

    def xǁLLMGatewayǁchat_text__mutmut_1(self, prompt: str, max_tokens: int = 301,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
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

    def xǁLLMGatewayǁchat_text__mutmut_2(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 1.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
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

    def xǁLLMGatewayǁchat_text__mutmut_3(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = ""
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

    def xǁLLMGatewayǁchat_text__mutmut_4(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
        channels = None
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

    def xǁLLMGatewayǁchat_text__mutmut_5(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        if channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        for ch in channels:
            try:
                return self._call_text_once(
                    ch["model"], os.environ.get(ch["key_env"], ""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁchat_text__mutmut_6(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        if not channels:
            raise RuntimeError(None)
        for ch in channels:
            try:
                return self._call_text_once(
                    ch["model"], os.environ.get(ch["key_env"], ""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁchat_text__mutmut_7(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("XX无可用 LLM 通道（ZHIPU_API_KEY 未设置）XX")
        for ch in channels:
            try:
                return self._call_text_once(
                    ch["model"], os.environ.get(ch["key_env"], ""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁchat_text__mutmut_8(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 llm 通道（zhipu_api_key 未设置）")
        for ch in channels:
            try:
                return self._call_text_once(
                    ch["model"], os.environ.get(ch["key_env"], ""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁchat_text__mutmut_9(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        for ch in channels:
            try:
                return self._call_text_once(
                    None, os.environ.get(ch["key_env"], ""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁchat_text__mutmut_10(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        for ch in channels:
            try:
                return self._call_text_once(
                    ch["model"], None,
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁchat_text__mutmut_11(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        for ch in channels:
            try:
                return self._call_text_once(
                    ch["model"], os.environ.get(ch["key_env"], ""),
                    None, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁchat_text__mutmut_12(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        for ch in channels:
            try:
                return self._call_text_once(
                    ch["model"], os.environ.get(ch["key_env"], ""),
                    prompt, None, temperature)
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁchat_text__mutmut_13(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        for ch in channels:
            try:
                return self._call_text_once(
                    ch["model"], os.environ.get(ch["key_env"], ""),
                    prompt, max_tokens, None)
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁchat_text__mutmut_14(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        for ch in channels:
            try:
                return self._call_text_once(
                    os.environ.get(ch["key_env"], ""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁchat_text__mutmut_15(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        for ch in channels:
            try:
                return self._call_text_once(
                    ch["model"], prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁchat_text__mutmut_16(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        for ch in channels:
            try:
                return self._call_text_once(
                    ch["model"], os.environ.get(ch["key_env"], ""),
                    max_tokens, temperature)
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁchat_text__mutmut_17(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        for ch in channels:
            try:
                return self._call_text_once(
                    ch["model"], os.environ.get(ch["key_env"], ""),
                    prompt, temperature)
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁchat_text__mutmut_18(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        for ch in channels:
            try:
                return self._call_text_once(
                    ch["model"], os.environ.get(ch["key_env"], ""),
                    prompt, max_tokens, )
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁchat_text__mutmut_19(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        for ch in channels:
            try:
                return self._call_text_once(
                    ch["XXmodelXX"], os.environ.get(ch["key_env"], ""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁchat_text__mutmut_20(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        for ch in channels:
            try:
                return self._call_text_once(
                    ch["MODEL"], os.environ.get(ch["key_env"], ""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁchat_text__mutmut_21(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        for ch in channels:
            try:
                return self._call_text_once(
                    ch["model"], os.environ.get(None, ""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁchat_text__mutmut_22(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        for ch in channels:
            try:
                return self._call_text_once(
                    ch["model"], os.environ.get(ch["key_env"], None),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁchat_text__mutmut_23(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        for ch in channels:
            try:
                return self._call_text_once(
                    ch["model"], os.environ.get(""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁchat_text__mutmut_24(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        for ch in channels:
            try:
                return self._call_text_once(
                    ch["model"], os.environ.get(ch["key_env"], ),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁchat_text__mutmut_25(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        for ch in channels:
            try:
                return self._call_text_once(
                    ch["model"], os.environ.get(ch["XXkey_envXX"], ""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁchat_text__mutmut_26(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        for ch in channels:
            try:
                return self._call_text_once(
                    ch["model"], os.environ.get(ch["KEY_ENV"], ""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁchat_text__mutmut_27(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        for ch in channels:
            try:
                return self._call_text_once(
                    ch["model"], os.environ.get(ch["key_env"], "XXXX"),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁchat_text__mutmut_28(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
        channels = self._available_channels()
        if not channels:
            raise RuntimeError("无可用 LLM 通道（ZHIPU_API_KEY 未设置）")
        for ch in channels:
            try:
                return self._call_text_once(
                    ch["model"], os.environ.get(ch["key_env"], ""),
                    prompt, max_tokens, temperature)
            except Exception as exc:
                last_err = None
        raise RuntimeError(f"全部 LLM 通道失败: {last_err}")

    def xǁLLMGatewayǁchat_text__mutmut_29(self, prompt: str, max_tokens: int = 300,
                  temperature: float = 0.3) -> str:
        """调用 LLM 返回原始文本（多通道容错）。"""
        last_err: Exception | None = None
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
        raise RuntimeError(None)

    @_mutmut_mutated(mutants_xǁLLMGatewayǁ_call_text_once__mutmut)
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

    def xǁLLMGatewayǁ_call_text_once__mutmut_orig(self, model: str, key: str, prompt: str,
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

    def xǁLLMGatewayǁ_call_text_once__mutmut_1(self, model: str, key: str, prompt: str,
                        max_tokens: int, temperature: float) -> str:
        payload = None
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

    def xǁLLMGatewayǁ_call_text_once__mutmut_2(self, model: str, key: str, prompt: str,
                        max_tokens: int, temperature: float) -> str:
        payload = {
            "XXmodelXX": model,
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

    def xǁLLMGatewayǁ_call_text_once__mutmut_3(self, model: str, key: str, prompt: str,
                        max_tokens: int, temperature: float) -> str:
        payload = {
            "MODEL": model,
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

    def xǁLLMGatewayǁ_call_text_once__mutmut_4(self, model: str, key: str, prompt: str,
                        max_tokens: int, temperature: float) -> str:
        payload = {
            "model": model,
            "XXmessagesXX": [{"role": "user", "content": prompt}],
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

    def xǁLLMGatewayǁ_call_text_once__mutmut_5(self, model: str, key: str, prompt: str,
                        max_tokens: int, temperature: float) -> str:
        payload = {
            "model": model,
            "MESSAGES": [{"role": "user", "content": prompt}],
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

    def xǁLLMGatewayǁ_call_text_once__mutmut_6(self, model: str, key: str, prompt: str,
                        max_tokens: int, temperature: float) -> str:
        payload = {
            "model": model,
            "messages": [{"XXroleXX": "user", "content": prompt}],
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

    def xǁLLMGatewayǁ_call_text_once__mutmut_7(self, model: str, key: str, prompt: str,
                        max_tokens: int, temperature: float) -> str:
        payload = {
            "model": model,
            "messages": [{"ROLE": "user", "content": prompt}],
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

    def xǁLLMGatewayǁ_call_text_once__mutmut_8(self, model: str, key: str, prompt: str,
                        max_tokens: int, temperature: float) -> str:
        payload = {
            "model": model,
            "messages": [{"role": "XXuserXX", "content": prompt}],
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

    def xǁLLMGatewayǁ_call_text_once__mutmut_9(self, model: str, key: str, prompt: str,
                        max_tokens: int, temperature: float) -> str:
        payload = {
            "model": model,
            "messages": [{"role": "USER", "content": prompt}],
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

    def xǁLLMGatewayǁ_call_text_once__mutmut_10(self, model: str, key: str, prompt: str,
                        max_tokens: int, temperature: float) -> str:
        payload = {
            "model": model,
            "messages": [{"role": "user", "XXcontentXX": prompt}],
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

    def xǁLLMGatewayǁ_call_text_once__mutmut_11(self, model: str, key: str, prompt: str,
                        max_tokens: int, temperature: float) -> str:
        payload = {
            "model": model,
            "messages": [{"role": "user", "CONTENT": prompt}],
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

    def xǁLLMGatewayǁ_call_text_once__mutmut_12(self, model: str, key: str, prompt: str,
                        max_tokens: int, temperature: float) -> str:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "XXmax_tokensXX": max_tokens,
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

    def xǁLLMGatewayǁ_call_text_once__mutmut_13(self, model: str, key: str, prompt: str,
                        max_tokens: int, temperature: float) -> str:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "MAX_TOKENS": max_tokens,
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

    def xǁLLMGatewayǁ_call_text_once__mutmut_14(self, model: str, key: str, prompt: str,
                        max_tokens: int, temperature: float) -> str:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "XXtemperatureXX": temperature,
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

    def xǁLLMGatewayǁ_call_text_once__mutmut_15(self, model: str, key: str, prompt: str,
                        max_tokens: int, temperature: float) -> str:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "TEMPERATURE": temperature,
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

    def xǁLLMGatewayǁ_call_text_once__mutmut_16(self, model: str, key: str, prompt: str,
                        max_tokens: int, temperature: float) -> str:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        req = None
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_17(self, model: str, key: str, prompt: str,
                        max_tokens: int, temperature: float) -> str:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        req = _url_req.Request(
            None,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
            method="POST",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_18(self, model: str, key: str, prompt: str,
                        max_tokens: int, temperature: float) -> str:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        req = _url_req.Request(
            _ZHIPU_API_URL,
            data=None,
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
            method="POST",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_19(self, model: str, key: str, prompt: str,
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
            headers=None,
            method="POST",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_20(self, model: str, key: str, prompt: str,
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
            method=None,
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_21(self, model: str, key: str, prompt: str,
                        max_tokens: int, temperature: float) -> str:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        req = _url_req.Request(
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
            method="POST",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_22(self, model: str, key: str, prompt: str,
                        max_tokens: int, temperature: float) -> str:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        req = _url_req.Request(
            _ZHIPU_API_URL,
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
            method="POST",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_23(self, model: str, key: str, prompt: str,
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
            method="POST",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_24(self, model: str, key: str, prompt: str,
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
            )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_25(self, model: str, key: str, prompt: str,
                        max_tokens: int, temperature: float) -> str:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        req = _url_req.Request(
            _ZHIPU_API_URL,
            data=json.dumps(payload).encode(None),
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
            method="POST",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_26(self, model: str, key: str, prompt: str,
                        max_tokens: int, temperature: float) -> str:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        req = _url_req.Request(
            _ZHIPU_API_URL,
            data=json.dumps(None).encode("utf-8"),
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
            method="POST",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_27(self, model: str, key: str, prompt: str,
                        max_tokens: int, temperature: float) -> str:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        req = _url_req.Request(
            _ZHIPU_API_URL,
            data=json.dumps(payload).encode("XXutf-8XX"),
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
            method="POST",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_28(self, model: str, key: str, prompt: str,
                        max_tokens: int, temperature: float) -> str:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        req = _url_req.Request(
            _ZHIPU_API_URL,
            data=json.dumps(payload).encode("UTF-8"),
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
            method="POST",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_29(self, model: str, key: str, prompt: str,
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
            headers={"XXAuthorizationXX": f"Bearer {key}",
                     "Content-Type": "application/json"},
            method="POST",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_30(self, model: str, key: str, prompt: str,
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
            headers={"authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
            method="POST",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_31(self, model: str, key: str, prompt: str,
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
            headers={"AUTHORIZATION": f"Bearer {key}",
                     "Content-Type": "application/json"},
            method="POST",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_32(self, model: str, key: str, prompt: str,
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
                     "XXContent-TypeXX": "application/json"},
            method="POST",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_33(self, model: str, key: str, prompt: str,
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
                     "content-type": "application/json"},
            method="POST",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_34(self, model: str, key: str, prompt: str,
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
                     "CONTENT-TYPE": "application/json"},
            method="POST",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_35(self, model: str, key: str, prompt: str,
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
                     "Content-Type": "XXapplication/jsonXX"},
            method="POST",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_36(self, model: str, key: str, prompt: str,
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
                     "Content-Type": "APPLICATION/JSON"},
            method="POST",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_37(self, model: str, key: str, prompt: str,
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
            method="XXPOSTXX",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_38(self, model: str, key: str, prompt: str,
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
            method="post",
        )
        with _url_req.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_39(self, model: str, key: str, prompt: str,
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
        with _url_req.urlopen(None, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_40(self, model: str, key: str, prompt: str,
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
        with _url_req.urlopen(req, timeout=None) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_41(self, model: str, key: str, prompt: str,
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
        with _url_req.urlopen(timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_42(self, model: str, key: str, prompt: str,
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
        with _url_req.urlopen(req, ) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_43(self, model: str, key: str, prompt: str,
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
            data = None
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_44(self, model: str, key: str, prompt: str,
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
            data = json.loads(None)
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_45(self, model: str, key: str, prompt: str,
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
            data = json.loads(resp.read().decode(None))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_46(self, model: str, key: str, prompt: str,
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
            data = json.loads(resp.read().decode("XXutf-8XX"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_47(self, model: str, key: str, prompt: str,
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
            data = json.loads(resp.read().decode("UTF-8"))
        return data["choices"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_48(self, model: str, key: str, prompt: str,
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
        return data["XXchoicesXX"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_49(self, model: str, key: str, prompt: str,
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
        return data["CHOICES"][0]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_50(self, model: str, key: str, prompt: str,
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
        return data["choices"][1]["message"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_51(self, model: str, key: str, prompt: str,
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
        return data["choices"][0]["XXmessageXX"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_52(self, model: str, key: str, prompt: str,
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
        return data["choices"][0]["MESSAGE"]["content"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_53(self, model: str, key: str, prompt: str,
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
        return data["choices"][0]["message"]["XXcontentXX"].strip()

    def xǁLLMGatewayǁ_call_text_once__mutmut_54(self, model: str, key: str, prompt: str,
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
        return data["choices"][0]["message"]["CONTENT"].strip()

    @_mutmut_mutated(mutants_xǁLLMGatewayǁavailable__mutmut)
    def available(self) -> bool:
        """是否有可用通道。"""
        return bool(self._available_channels())

    def xǁLLMGatewayǁavailable__mutmut_orig(self) -> bool:
        """是否有可用通道。"""
        return bool(self._available_channels())

    def xǁLLMGatewayǁavailable__mutmut_1(self) -> bool:
        """是否有可用通道。"""
        return bool(None)

    @_mutmut_mutated(mutants_xǁLLMGatewayǁchannel_summary__mutmut)
    def channel_summary(self) -> str:
        """通道摘要（不含密钥）。"""
        return " | ".join(f"{c['model']}({'✓' if os.environ.get(c['key_env'],'') else '✗'})"
                          for c in self.channels)

    def xǁLLMGatewayǁchannel_summary__mutmut_orig(self) -> str:
        """通道摘要（不含密钥）。"""
        return " | ".join(f"{c['model']}({'✓' if os.environ.get(c['key_env'],'') else '✗'})"
                          for c in self.channels)

    def xǁLLMGatewayǁchannel_summary__mutmut_1(self) -> str:
        """通道摘要（不含密钥）。"""
        return " | ".join(None)

    def xǁLLMGatewayǁchannel_summary__mutmut_2(self) -> str:
        """通道摘要（不含密钥）。"""
        return "XX | XX".join(f"{c['model']}({'✓' if os.environ.get(c['key_env'],'') else '✗'})"
                          for c in self.channels)

    def xǁLLMGatewayǁchannel_summary__mutmut_3(self) -> str:
        """通道摘要（不含密钥）。"""
        return " | ".join(f"{c['XXmodelXX']}({'✓' if os.environ.get(c['key_env'],'') else '✗'})"
                          for c in self.channels)

    def xǁLLMGatewayǁchannel_summary__mutmut_4(self) -> str:
        """通道摘要（不含密钥）。"""
        return " | ".join(f"{c['MODEL']}({'✓' if os.environ.get(c['key_env'],'') else '✗'})"
                          for c in self.channels)

    def xǁLLMGatewayǁchannel_summary__mutmut_5(self) -> str:
        """通道摘要（不含密钥）。"""
        return " | ".join(f"{c['model']}({'✓' if (os.environ.get(c['key_env'],'')) and False else '✗'})"
                          for c in self.channels)

    def xǁLLMGatewayǁchannel_summary__mutmut_6(self) -> str:
        """通道摘要（不含密钥）。"""
        return " | ".join(f"{c['model']}({'✓' if (os.environ.get(c['key_env'],'')) or True else '✗'})"
                          for c in self.channels)

    def xǁLLMGatewayǁchannel_summary__mutmut_7(self) -> str:
        """通道摘要（不含密钥）。"""
        return " | ".join(f"{c['model']}({'XX✓XX' if os.environ.get(c['key_env'],'') else '✗'})"
                          for c in self.channels)

    def xǁLLMGatewayǁchannel_summary__mutmut_8(self) -> str:
        """通道摘要（不含密钥）。"""
        return " | ".join(f"{c['model']}({'✓' if os.environ.get(None,'') else '✗'})"
                          for c in self.channels)

    def xǁLLMGatewayǁchannel_summary__mutmut_9(self) -> str:
        """通道摘要（不含密钥）。"""
        return " | ".join(f"{c['model']}({'✓' if os.environ.get(c['key_env'],None) else '✗'})"
                          for c in self.channels)

    def xǁLLMGatewayǁchannel_summary__mutmut_10(self) -> str:
        """通道摘要（不含密钥）。"""
        return " | ".join(f"{c['model']}({'✓' if os.environ.get('') else '✗'})"
                          for c in self.channels)

    def xǁLLMGatewayǁchannel_summary__mutmut_11(self) -> str:
        """通道摘要（不含密钥）。"""
        return " | ".join(f"{c['model']}({'✓' if os.environ.get(c['key_env'],) else '✗'})"
                          for c in self.channels)

    def xǁLLMGatewayǁchannel_summary__mutmut_12(self) -> str:
        """通道摘要（不含密钥）。"""
        return " | ".join(f"{c['model']}({'✓' if os.environ.get(c['XXkey_envXX'],'') else '✗'})"
                          for c in self.channels)

    def xǁLLMGatewayǁchannel_summary__mutmut_13(self) -> str:
        """通道摘要（不含密钥）。"""
        return " | ".join(f"{c['model']}({'✓' if os.environ.get(c['KEY_ENV'],'') else '✗'})"
                          for c in self.channels)

    def xǁLLMGatewayǁchannel_summary__mutmut_14(self) -> str:
        """通道摘要（不含密钥）。"""
        return " | ".join(f"{c['model']}({'✓' if os.environ.get(c['key_env'],'XXXX') else '✗'})"
                          for c in self.channels)

    def xǁLLMGatewayǁchannel_summary__mutmut_15(self) -> str:
        """通道摘要（不含密钥）。"""
        return " | ".join(f"{c['model']}({'✓' if os.environ.get(c['key_env'],'') else 'XX✗XX'})"
                          for c in self.channels)

mutants_xǁLLMGatewayǁ__init____mutmut['_mutmut_orig'] = LLMGateway.xǁLLMGatewayǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ__init____mutmut['xǁLLMGatewayǁ__init____mutmut_1'] = LLMGateway.xǁLLMGatewayǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ__init____mutmut['xǁLLMGatewayǁ__init____mutmut_2'] = LLMGateway.xǁLLMGatewayǁ__init____mutmut_2 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ__init____mutmut['xǁLLMGatewayǁ__init____mutmut_3'] = LLMGateway.xǁLLMGatewayǁ__init____mutmut_3 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ__init____mutmut['xǁLLMGatewayǁ__init____mutmut_4'] = LLMGateway.xǁLLMGatewayǁ__init____mutmut_4 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ__init____mutmut['xǁLLMGatewayǁ__init____mutmut_5'] = LLMGateway.xǁLLMGatewayǁ__init____mutmut_5 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ__init____mutmut['xǁLLMGatewayǁ__init____mutmut_6'] = LLMGateway.xǁLLMGatewayǁ__init____mutmut_6 # type: ignore # mutmut generated

mutants_xǁLLMGatewayǁ_cache_key__mutmut['_mutmut_orig'] = LLMGateway.xǁLLMGatewayǁ_cache_key__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_cache_key__mutmut['xǁLLMGatewayǁ_cache_key__mutmut_1'] = LLMGateway.xǁLLMGatewayǁ_cache_key__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_cache_key__mutmut['xǁLLMGatewayǁ_cache_key__mutmut_2'] = LLMGateway.xǁLLMGatewayǁ_cache_key__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_cache_key__mutmut['xǁLLMGatewayǁ_cache_key__mutmut_3'] = LLMGateway.xǁLLMGatewayǁ_cache_key__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_cache_key__mutmut['xǁLLMGatewayǁ_cache_key__mutmut_4'] = LLMGateway.xǁLLMGatewayǁ_cache_key__mutmut_4 # type: ignore # mutmut generated

mutants_xǁLLMGatewayǁ_cached_or__mutmut['_mutmut_orig'] = LLMGateway.xǁLLMGatewayǁ_cached_or__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_cached_or__mutmut['xǁLLMGatewayǁ_cached_or__mutmut_1'] = LLMGateway.xǁLLMGatewayǁ_cached_or__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_cached_or__mutmut['xǁLLMGatewayǁ_cached_or__mutmut_2'] = LLMGateway.xǁLLMGatewayǁ_cached_or__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_cached_or__mutmut['xǁLLMGatewayǁ_cached_or__mutmut_3'] = LLMGateway.xǁLLMGatewayǁ_cached_or__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_cached_or__mutmut['xǁLLMGatewayǁ_cached_or__mutmut_4'] = LLMGateway.xǁLLMGatewayǁ_cached_or__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_cached_or__mutmut['xǁLLMGatewayǁ_cached_or__mutmut_5'] = LLMGateway.xǁLLMGatewayǁ_cached_or__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_cached_or__mutmut['xǁLLMGatewayǁ_cached_or__mutmut_6'] = LLMGateway.xǁLLMGatewayǁ_cached_or__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_cached_or__mutmut['xǁLLMGatewayǁ_cached_or__mutmut_7'] = LLMGateway.xǁLLMGatewayǁ_cached_or__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_cached_or__mutmut['xǁLLMGatewayǁ_cached_or__mutmut_8'] = LLMGateway.xǁLLMGatewayǁ_cached_or__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_cached_or__mutmut['xǁLLMGatewayǁ_cached_or__mutmut_9'] = LLMGateway.xǁLLMGatewayǁ_cached_or__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_cached_or__mutmut['xǁLLMGatewayǁ_cached_or__mutmut_10'] = LLMGateway.xǁLLMGatewayǁ_cached_or__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_cached_or__mutmut['xǁLLMGatewayǁ_cached_or__mutmut_11'] = LLMGateway.xǁLLMGatewayǁ_cached_or__mutmut_11 # type: ignore # mutmut generated

mutants_xǁLLMGatewayǁ_available_channels__mutmut['_mutmut_orig'] = LLMGateway.xǁLLMGatewayǁ_available_channels__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_available_channels__mutmut['xǁLLMGatewayǁ_available_channels__mutmut_1'] = LLMGateway.xǁLLMGatewayǁ_available_channels__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_available_channels__mutmut['xǁLLMGatewayǁ_available_channels__mutmut_2'] = LLMGateway.xǁLLMGatewayǁ_available_channels__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_available_channels__mutmut['xǁLLMGatewayǁ_available_channels__mutmut_3'] = LLMGateway.xǁLLMGatewayǁ_available_channels__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_available_channels__mutmut['xǁLLMGatewayǁ_available_channels__mutmut_4'] = LLMGateway.xǁLLMGatewayǁ_available_channels__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_available_channels__mutmut['xǁLLMGatewayǁ_available_channels__mutmut_5'] = LLMGateway.xǁLLMGatewayǁ_available_channels__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_available_channels__mutmut['xǁLLMGatewayǁ_available_channels__mutmut_6'] = LLMGateway.xǁLLMGatewayǁ_available_channels__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_available_channels__mutmut['xǁLLMGatewayǁ_available_channels__mutmut_7'] = LLMGateway.xǁLLMGatewayǁ_available_channels__mutmut_7 # type: ignore # mutmut generated

mutants_xǁLLMGatewayǁchat_json__mutmut['_mutmut_orig'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_json__mutmut['xǁLLMGatewayǁchat_json__mutmut_1'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_json__mutmut['xǁLLMGatewayǁchat_json__mutmut_2'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_json__mutmut['xǁLLMGatewayǁchat_json__mutmut_3'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_json__mutmut['xǁLLMGatewayǁchat_json__mutmut_4'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_json__mutmut['xǁLLMGatewayǁchat_json__mutmut_5'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_json__mutmut['xǁLLMGatewayǁchat_json__mutmut_6'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_json__mutmut['xǁLLMGatewayǁchat_json__mutmut_7'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_json__mutmut['xǁLLMGatewayǁchat_json__mutmut_8'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_json__mutmut['xǁLLMGatewayǁchat_json__mutmut_9'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_json__mutmut['xǁLLMGatewayǁchat_json__mutmut_10'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_json__mutmut['xǁLLMGatewayǁchat_json__mutmut_11'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_11 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_json__mutmut['xǁLLMGatewayǁchat_json__mutmut_12'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_12 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_json__mutmut['xǁLLMGatewayǁchat_json__mutmut_13'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_13 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_json__mutmut['xǁLLMGatewayǁchat_json__mutmut_14'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_14 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_json__mutmut['xǁLLMGatewayǁchat_json__mutmut_15'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_15 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_json__mutmut['xǁLLMGatewayǁchat_json__mutmut_16'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_16 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_json__mutmut['xǁLLMGatewayǁchat_json__mutmut_17'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_17 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_json__mutmut['xǁLLMGatewayǁchat_json__mutmut_18'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_18 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_json__mutmut['xǁLLMGatewayǁchat_json__mutmut_19'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_19 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_json__mutmut['xǁLLMGatewayǁchat_json__mutmut_20'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_20 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_json__mutmut['xǁLLMGatewayǁchat_json__mutmut_21'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_21 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_json__mutmut['xǁLLMGatewayǁchat_json__mutmut_22'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_22 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_json__mutmut['xǁLLMGatewayǁchat_json__mutmut_23'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_23 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_json__mutmut['xǁLLMGatewayǁchat_json__mutmut_24'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_24 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_json__mutmut['xǁLLMGatewayǁchat_json__mutmut_25'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_25 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_json__mutmut['xǁLLMGatewayǁchat_json__mutmut_26'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_26 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_json__mutmut['xǁLLMGatewayǁchat_json__mutmut_27'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_27 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_json__mutmut['xǁLLMGatewayǁchat_json__mutmut_28'] = LLMGateway.xǁLLMGatewayǁchat_json__mutmut_28 # type: ignore # mutmut generated

mutants_xǁLLMGatewayǁ_chat_json_uncached__mutmut['_mutmut_orig'] = LLMGateway.xǁLLMGatewayǁ_chat_json_uncached__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_chat_json_uncached__mutmut['xǁLLMGatewayǁ_chat_json_uncached__mutmut_1'] = LLMGateway.xǁLLMGatewayǁ_chat_json_uncached__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_chat_json_uncached__mutmut['xǁLLMGatewayǁ_chat_json_uncached__mutmut_2'] = LLMGateway.xǁLLMGatewayǁ_chat_json_uncached__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_chat_json_uncached__mutmut['xǁLLMGatewayǁ_chat_json_uncached__mutmut_3'] = LLMGateway.xǁLLMGatewayǁ_chat_json_uncached__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_chat_json_uncached__mutmut['xǁLLMGatewayǁ_chat_json_uncached__mutmut_4'] = LLMGateway.xǁLLMGatewayǁ_chat_json_uncached__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_chat_json_uncached__mutmut['xǁLLMGatewayǁ_chat_json_uncached__mutmut_5'] = LLMGateway.xǁLLMGatewayǁ_chat_json_uncached__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_chat_json_uncached__mutmut['xǁLLMGatewayǁ_chat_json_uncached__mutmut_6'] = LLMGateway.xǁLLMGatewayǁ_chat_json_uncached__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_chat_json_uncached__mutmut['xǁLLMGatewayǁ_chat_json_uncached__mutmut_7'] = LLMGateway.xǁLLMGatewayǁ_chat_json_uncached__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_chat_json_uncached__mutmut['xǁLLMGatewayǁ_chat_json_uncached__mutmut_8'] = LLMGateway.xǁLLMGatewayǁ_chat_json_uncached__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_chat_json_uncached__mutmut['xǁLLMGatewayǁ_chat_json_uncached__mutmut_9'] = LLMGateway.xǁLLMGatewayǁ_chat_json_uncached__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_chat_json_uncached__mutmut['xǁLLMGatewayǁ_chat_json_uncached__mutmut_10'] = LLMGateway.xǁLLMGatewayǁ_chat_json_uncached__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_chat_json_uncached__mutmut['xǁLLMGatewayǁ_chat_json_uncached__mutmut_11'] = LLMGateway.xǁLLMGatewayǁ_chat_json_uncached__mutmut_11 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_chat_json_uncached__mutmut['xǁLLMGatewayǁ_chat_json_uncached__mutmut_12'] = LLMGateway.xǁLLMGatewayǁ_chat_json_uncached__mutmut_12 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_chat_json_uncached__mutmut['xǁLLMGatewayǁ_chat_json_uncached__mutmut_13'] = LLMGateway.xǁLLMGatewayǁ_chat_json_uncached__mutmut_13 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_chat_json_uncached__mutmut['xǁLLMGatewayǁ_chat_json_uncached__mutmut_14'] = LLMGateway.xǁLLMGatewayǁ_chat_json_uncached__mutmut_14 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_chat_json_uncached__mutmut['xǁLLMGatewayǁ_chat_json_uncached__mutmut_15'] = LLMGateway.xǁLLMGatewayǁ_chat_json_uncached__mutmut_15 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_chat_json_uncached__mutmut['xǁLLMGatewayǁ_chat_json_uncached__mutmut_16'] = LLMGateway.xǁLLMGatewayǁ_chat_json_uncached__mutmut_16 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_chat_json_uncached__mutmut['xǁLLMGatewayǁ_chat_json_uncached__mutmut_17'] = LLMGateway.xǁLLMGatewayǁ_chat_json_uncached__mutmut_17 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_chat_json_uncached__mutmut['xǁLLMGatewayǁ_chat_json_uncached__mutmut_18'] = LLMGateway.xǁLLMGatewayǁ_chat_json_uncached__mutmut_18 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_chat_json_uncached__mutmut['xǁLLMGatewayǁ_chat_json_uncached__mutmut_19'] = LLMGateway.xǁLLMGatewayǁ_chat_json_uncached__mutmut_19 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_chat_json_uncached__mutmut['xǁLLMGatewayǁ_chat_json_uncached__mutmut_20'] = LLMGateway.xǁLLMGatewayǁ_chat_json_uncached__mutmut_20 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_chat_json_uncached__mutmut['xǁLLMGatewayǁ_chat_json_uncached__mutmut_21'] = LLMGateway.xǁLLMGatewayǁ_chat_json_uncached__mutmut_21 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_chat_json_uncached__mutmut['xǁLLMGatewayǁ_chat_json_uncached__mutmut_22'] = LLMGateway.xǁLLMGatewayǁ_chat_json_uncached__mutmut_22 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_chat_json_uncached__mutmut['xǁLLMGatewayǁ_chat_json_uncached__mutmut_23'] = LLMGateway.xǁLLMGatewayǁ_chat_json_uncached__mutmut_23 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_chat_json_uncached__mutmut['xǁLLMGatewayǁ_chat_json_uncached__mutmut_24'] = LLMGateway.xǁLLMGatewayǁ_chat_json_uncached__mutmut_24 # type: ignore # mutmut generated

mutants_xǁLLMGatewayǁ_call_once__mutmut['_mutmut_orig'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_1'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_2'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_3'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_4'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_5'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_6'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_7'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_8'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_9'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_10'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_11'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_11 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_12'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_12 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_13'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_13 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_14'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_14 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_15'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_15 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_16'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_16 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_17'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_17 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_18'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_18 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_19'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_19 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_20'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_20 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_21'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_21 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_22'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_22 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_23'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_23 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_24'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_24 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_25'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_25 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_26'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_26 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_27'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_27 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_28'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_28 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_29'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_29 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_30'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_30 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_31'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_31 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_32'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_32 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_33'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_33 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_34'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_34 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_35'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_35 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_36'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_36 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_37'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_37 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_38'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_38 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_39'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_39 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_40'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_40 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_41'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_41 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_42'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_42 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_43'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_43 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_44'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_44 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_45'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_45 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_46'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_46 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_47'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_47 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_48'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_48 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_49'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_49 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_50'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_50 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_51'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_51 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_52'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_52 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_53'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_53 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_54'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_54 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_55'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_55 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_56'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_56 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_57'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_57 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_58'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_58 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_59'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_59 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_60'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_60 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_61'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_61 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_62'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_62 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_63'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_63 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_64'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_64 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_65'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_65 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_66'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_66 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_67'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_67 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_68'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_68 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_once__mutmut['xǁLLMGatewayǁ_call_once__mutmut_69'] = LLMGateway.xǁLLMGatewayǁ_call_once__mutmut_69 # type: ignore # mutmut generated

mutants_xǁLLMGatewayǁchat_text__mutmut['_mutmut_orig'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_1'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_2'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_3'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_4'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_5'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_6'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_7'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_8'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_9'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_10'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_11'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_11 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_12'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_12 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_13'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_13 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_14'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_14 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_15'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_15 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_16'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_16 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_17'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_17 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_18'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_18 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_19'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_19 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_20'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_20 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_21'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_21 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_22'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_22 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_23'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_23 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_24'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_24 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_25'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_25 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_26'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_26 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_27'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_27 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_28'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_28 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchat_text__mutmut['xǁLLMGatewayǁchat_text__mutmut_29'] = LLMGateway.xǁLLMGatewayǁchat_text__mutmut_29 # type: ignore # mutmut generated

mutants_xǁLLMGatewayǁ_call_text_once__mutmut['_mutmut_orig'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_1'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_2'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_3'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_4'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_5'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_6'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_7'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_8'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_9'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_10'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_11'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_11 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_12'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_12 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_13'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_13 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_14'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_14 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_15'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_15 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_16'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_16 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_17'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_17 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_18'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_18 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_19'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_19 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_20'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_20 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_21'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_21 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_22'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_22 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_23'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_23 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_24'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_24 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_25'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_25 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_26'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_26 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_27'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_27 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_28'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_28 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_29'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_29 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_30'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_30 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_31'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_31 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_32'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_32 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_33'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_33 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_34'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_34 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_35'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_35 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_36'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_36 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_37'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_37 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_38'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_38 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_39'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_39 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_40'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_40 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_41'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_41 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_42'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_42 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_43'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_43 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_44'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_44 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_45'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_45 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_46'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_46 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_47'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_47 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_48'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_48 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_49'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_49 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_50'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_50 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_51'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_51 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_52'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_52 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_53'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_53 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁ_call_text_once__mutmut['xǁLLMGatewayǁ_call_text_once__mutmut_54'] = LLMGateway.xǁLLMGatewayǁ_call_text_once__mutmut_54 # type: ignore # mutmut generated

mutants_xǁLLMGatewayǁavailable__mutmut['_mutmut_orig'] = LLMGateway.xǁLLMGatewayǁavailable__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁavailable__mutmut['xǁLLMGatewayǁavailable__mutmut_1'] = LLMGateway.xǁLLMGatewayǁavailable__mutmut_1 # type: ignore # mutmut generated

mutants_xǁLLMGatewayǁchannel_summary__mutmut['_mutmut_orig'] = LLMGateway.xǁLLMGatewayǁchannel_summary__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchannel_summary__mutmut['xǁLLMGatewayǁchannel_summary__mutmut_1'] = LLMGateway.xǁLLMGatewayǁchannel_summary__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchannel_summary__mutmut['xǁLLMGatewayǁchannel_summary__mutmut_2'] = LLMGateway.xǁLLMGatewayǁchannel_summary__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchannel_summary__mutmut['xǁLLMGatewayǁchannel_summary__mutmut_3'] = LLMGateway.xǁLLMGatewayǁchannel_summary__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchannel_summary__mutmut['xǁLLMGatewayǁchannel_summary__mutmut_4'] = LLMGateway.xǁLLMGatewayǁchannel_summary__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchannel_summary__mutmut['xǁLLMGatewayǁchannel_summary__mutmut_5'] = LLMGateway.xǁLLMGatewayǁchannel_summary__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchannel_summary__mutmut['xǁLLMGatewayǁchannel_summary__mutmut_6'] = LLMGateway.xǁLLMGatewayǁchannel_summary__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchannel_summary__mutmut['xǁLLMGatewayǁchannel_summary__mutmut_7'] = LLMGateway.xǁLLMGatewayǁchannel_summary__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchannel_summary__mutmut['xǁLLMGatewayǁchannel_summary__mutmut_8'] = LLMGateway.xǁLLMGatewayǁchannel_summary__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchannel_summary__mutmut['xǁLLMGatewayǁchannel_summary__mutmut_9'] = LLMGateway.xǁLLMGatewayǁchannel_summary__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchannel_summary__mutmut['xǁLLMGatewayǁchannel_summary__mutmut_10'] = LLMGateway.xǁLLMGatewayǁchannel_summary__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchannel_summary__mutmut['xǁLLMGatewayǁchannel_summary__mutmut_11'] = LLMGateway.xǁLLMGatewayǁchannel_summary__mutmut_11 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchannel_summary__mutmut['xǁLLMGatewayǁchannel_summary__mutmut_12'] = LLMGateway.xǁLLMGatewayǁchannel_summary__mutmut_12 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchannel_summary__mutmut['xǁLLMGatewayǁchannel_summary__mutmut_13'] = LLMGateway.xǁLLMGatewayǁchannel_summary__mutmut_13 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchannel_summary__mutmut['xǁLLMGatewayǁchannel_summary__mutmut_14'] = LLMGateway.xǁLLMGatewayǁchannel_summary__mutmut_14 # type: ignore # mutmut generated
mutants_xǁLLMGatewayǁchannel_summary__mutmut['xǁLLMGatewayǁchannel_summary__mutmut_15'] = LLMGateway.xǁLLMGatewayǁchannel_summary__mutmut_15 # type: ignore # mutmut generated


if __name__ == "__main__":
    gw = LLMGateway()
    print(f"[LLM-GATEWAY] 通道: {gw.channel_summary()}")
    print(f"可用: {gw.available()}")
    if gw.available():
        resp = gw.chat_json("只输出JSON: {\"status\": \"ok\"}", max_tokens=50)
        print(f"实测: {resp}")
