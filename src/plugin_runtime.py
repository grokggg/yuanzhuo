#!/usr/bin/env python3
"""UHES 插件运行时（第7项优化：插件加载真实化）。

设计原则（对应 09 铁律 + 非侵入铁律）：
- 动态 import：插件是独立 Python 模块，importlib 按名加载（替代硬编码函数引用）。
- 隔离命名空间：每个插件在独立模块命名空间执行，不污染引擎主体。
- 契约校验：加载时校验插件暴露 PLUGIN_META（name/step/接口）+ handle()，
  不符合契约拒绝加载并报告。
- 资源上限：PLUGIN_META.resource_budget 声明概念资源预算，超限拒绝（概念层）。

使用：
    runtime = PluginRuntime(plugin_dir="src/plugins")
    plugin = runtime.load("step_s1_llm")     # 加载插件模块
    plugin.handle(state)                      # 执行（隔离命名空间）
    runtime.list_loaded()                     # 已加载列表
"""

from __future__ import annotations

import importlib.util
import os
import sys
from typing import Any, Callable, Optional

# 契约：插件必须暴露的键
_REQUIRED_META_KEYS = {"name", "step"}
_REQUIRED_ATTRS = {"PLUGIN_META", "handle"}
_MAX_RESOURCE_BUDGET = 100  # 概念层资源预算上限（单位：概念点数）


class PluginContractError(RuntimeError):
    """插件不符合加载契约。"""


class PluginRuntime:
    """动态插件加载器（隔离命名空间 + 契约校验 + 资源上限）。"""

    def __init__(self, plugin_dir: str = ""):
        self.plugin_dir = plugin_dir
        self._loaded: dict[str, dict[str, Any]] = {}  # name -> {meta, module, handle}

    def load(self, plugin_name: str) -> dict[str, Any]:
        """按名加载插件模块（动态 import + 契约校验 + 资源预算检查）。

        返回: {"name", "step", "handle", "resource_budget", "loaded_from"}
        失败: 抛 PluginContractError（契约不符/资源超限/不存在）。
        """
        if plugin_name in self._loaded:
            return self._loaded[plugin_name]

        # 1) 定位模块文件（plugin_dir/<name>.py）
        module_path = os.path.join(self.plugin_dir, f"{plugin_name}.py")
        if not os.path.isfile(module_path):
            raise PluginContractError(f"插件模块不存在: {module_path}")

        # 2) 动态 import（importlib，独立模块命名空间）
        spec = importlib.util.spec_from_file_location(
            f"uhes_plugin_{plugin_name}", module_path)
        if spec is None or spec.loader is None:
            raise PluginContractError(f"插件模块无法加载: {module_path}")
        module = importlib.util.module_from_spec(spec)
        # 隔离命名空间：注入独立全局（复制最小环境，不暴露引擎内部）
        module.__dict__.setdefault("__builtins__", __builtins__)
        try:
            spec.loader.exec_module(module)
        except Exception as exc:
            raise PluginContractError(f"插件模块执行失败: {plugin_name} ({exc})") from exc

        # 3) 契约校验：必须暴露 PLUGIN_META + handle
        missing = [attr for attr in _REQUIRED_ATTRS if not hasattr(module, attr)]
        if missing:
            raise PluginContractError(
                f"插件 {plugin_name} 缺契约属性: {missing}（需要 PLUGIN_META + handle）")
        meta = module.PLUGIN_META
        missing_meta = [k for k in _REQUIRED_META_KEYS if k not in meta]
        if missing_meta:
            raise PluginContractError(
                f"插件 {plugin_name} 的 PLUGIN_META 缺字段: {missing_meta}（需要 name+step）")
        if not callable(module.handle):
            raise PluginContractError(f"插件 {plugin_name} 的 handle 不可调用")

        # 4) 资源预算检查（概念层）
        budget = int(meta.get("resource_budget", 1) or 1)
        if budget > _MAX_RESOURCE_BUDGET:
            raise PluginContractError(
                f"插件 {plugin_name} 资源预算超限: {budget} > {_MAX_RESOURCE_BUDGET}")

        record = {
            "name": meta["name"],
            "step": meta["step"],
            "handle": module.handle,
            "resource_budget": budget,
            "loaded_from": module_path,
            "module": module,
        }
        self._loaded[plugin_name] = record
        return record

    def unload(self, plugin_name: str) -> None:
        """卸载插件（从加载表移除；模块对象交 GC，不污染引擎命名空间）。"""
        self._loaded.pop(plugin_name, None)

    def list_loaded(self) -> list[str]:
        """已加载插件名列表。"""
        return list(self._loaded.keys())

    def load_dir(self) -> list[str]:
        """加载插件目录下全部 *.py（排除 __init__），返回成功加载名。"""
        loaded = []
        if not self.plugin_dir or not os.path.isdir(self.plugin_dir):
            return loaded
        for fn in sorted(os.listdir(self.plugin_dir)):
            if not fn.endswith(".py") or fn.startswith("__"):
                continue
            name = fn[:-3]
            try:
                self.load(name)
                loaded.append(name)
            except PluginContractError:
                continue  # 契约不符的插件跳过（不阻断其他）
        return loaded
