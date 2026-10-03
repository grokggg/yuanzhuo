#!/usr/bin/env python3
"""UHES 可观测性事件总线（第8项优化：--trace JSONL → 结构化事件总线）。

设计原则（顶尖工程实践）：
- Span 生命周期：每步执行 = 一个 span（开始/结束/耗时），可嵌套（流水线根 span → 各步子 span）。
- 指标聚合：各步耗时 / 降级率 / 回退率 / 门控通过率，可导出为 JSON。
- 事件订阅：observers 可订阅事件（event: step_started/step_finished/metrics_updated），
  支持未来接 OpenTelemetry/日志收集器。
- 导出：export_jsonl() 输出结构化事件流（含 span 层级与耗时），
  export_metrics() 输出聚合指标（可机器消费）。

使用：
    bus = ObservabilityBus(run_id="run_x")
    with bus.span("S1", {"step": "S1"}):
        ...  # 步骤执行
    bus.record_event("step_finished", {...})
    jsonl = bus.export_jsonl()     # 结构化事件流
    metrics = bus.export_metrics()  # 聚合指标
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import Any

# 事件类型
EVENT_PIPELINE_START = "pipeline_started"
EVENT_PIPELINE_END = "pipeline_finished"
EVENT_STEP_START = "step_started"
EVENT_STEP_END = "step_finished"
EVENT_STEP_SKIP = "step_skipped"
EVENT_DEGRADE = "step_degraded"
EVENT_ROLLBACK = "step_rolled_back"


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_xǁObservabilityBusǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁObservabilityBusǁsubscribe__mutmut: MutantDict = {}  # type: ignore
mutants_xǁObservabilityBusǁrecord_event__mutmut: MutantDict = {}  # type: ignore
mutants_xǁObservabilityBusǁspan__mutmut: MutantDict = {}  # type: ignore
mutants_xǁObservabilityBusǁ_end_span__mutmut: MutantDict = {}  # type: ignore
mutants_xǁObservabilityBusǁexport_metrics__mutmut: MutantDict = {}  # type: ignore
mutants_xǁObservabilityBusǁexport_jsonl__mutmut: MutantDict = {}  # type: ignore
mutants_xǁObservabilityBusǁexport_span_tree__mutmut: MutantDict = {}  # type: ignore


class ObservabilityBus:
    """结构化事件总线（span 生命周期 + 指标聚合 + 事件订阅 + 导出）。"""

    @_mutmut_mutated(mutants_xǁObservabilityBusǁ__init____mutmut)
    def __init__(self, run_id: str = ""):
        self.run_id = run_id or "run_unknown"
        self._events: list[dict[str, Any]] = []
        self._spans: list[dict[str, Any]] = []
        self._span_stack: list[str] = []  # 当前 span id 栈（支持嵌套）
        self._observers: list[Callable[[str, dict[str, Any]], None]] = []
        self._started_at = time.time()
        self._span_seq = 0

    def xǁObservabilityBusǁ__init____mutmut_orig(self, run_id: str = ""):
        self.run_id = run_id or "run_unknown"
        self._events: list[dict[str, Any]] = []
        self._spans: list[dict[str, Any]] = []
        self._span_stack: list[str] = []  # 当前 span id 栈（支持嵌套）
        self._observers: list[Callable[[str, dict[str, Any]], None]] = []
        self._started_at = time.time()
        self._span_seq = 0

    def xǁObservabilityBusǁ__init____mutmut_1(self, run_id: str = "XXXX"):
        self.run_id = run_id or "run_unknown"
        self._events: list[dict[str, Any]] = []
        self._spans: list[dict[str, Any]] = []
        self._span_stack: list[str] = []  # 当前 span id 栈（支持嵌套）
        self._observers: list[Callable[[str, dict[str, Any]], None]] = []
        self._started_at = time.time()
        self._span_seq = 0

    def xǁObservabilityBusǁ__init____mutmut_2(self, run_id: str = ""):
        self.run_id = None
        self._events: list[dict[str, Any]] = []
        self._spans: list[dict[str, Any]] = []
        self._span_stack: list[str] = []  # 当前 span id 栈（支持嵌套）
        self._observers: list[Callable[[str, dict[str, Any]], None]] = []
        self._started_at = time.time()
        self._span_seq = 0

    def xǁObservabilityBusǁ__init____mutmut_3(self, run_id: str = ""):
        self.run_id = run_id and "run_unknown"
        self._events: list[dict[str, Any]] = []
        self._spans: list[dict[str, Any]] = []
        self._span_stack: list[str] = []  # 当前 span id 栈（支持嵌套）
        self._observers: list[Callable[[str, dict[str, Any]], None]] = []
        self._started_at = time.time()
        self._span_seq = 0

    def xǁObservabilityBusǁ__init____mutmut_4(self, run_id: str = ""):
        self.run_id = run_id or "XXrun_unknownXX"
        self._events: list[dict[str, Any]] = []
        self._spans: list[dict[str, Any]] = []
        self._span_stack: list[str] = []  # 当前 span id 栈（支持嵌套）
        self._observers: list[Callable[[str, dict[str, Any]], None]] = []
        self._started_at = time.time()
        self._span_seq = 0

    def xǁObservabilityBusǁ__init____mutmut_5(self, run_id: str = ""):
        self.run_id = run_id or "RUN_UNKNOWN"
        self._events: list[dict[str, Any]] = []
        self._spans: list[dict[str, Any]] = []
        self._span_stack: list[str] = []  # 当前 span id 栈（支持嵌套）
        self._observers: list[Callable[[str, dict[str, Any]], None]] = []
        self._started_at = time.time()
        self._span_seq = 0

    def xǁObservabilityBusǁ__init____mutmut_6(self, run_id: str = ""):
        self.run_id = run_id or "run_unknown"
        self._events: list[dict[str, Any]] = None
        self._spans: list[dict[str, Any]] = []
        self._span_stack: list[str] = []  # 当前 span id 栈（支持嵌套）
        self._observers: list[Callable[[str, dict[str, Any]], None]] = []
        self._started_at = time.time()
        self._span_seq = 0

    def xǁObservabilityBusǁ__init____mutmut_7(self, run_id: str = ""):
        self.run_id = run_id or "run_unknown"
        self._events: list[dict[str, Any]] = []
        self._spans: list[dict[str, Any]] = None
        self._span_stack: list[str] = []  # 当前 span id 栈（支持嵌套）
        self._observers: list[Callable[[str, dict[str, Any]], None]] = []
        self._started_at = time.time()
        self._span_seq = 0

    def xǁObservabilityBusǁ__init____mutmut_8(self, run_id: str = ""):
        self.run_id = run_id or "run_unknown"
        self._events: list[dict[str, Any]] = []
        self._spans: list[dict[str, Any]] = []
        self._span_stack: list[str] = None  # 当前 span id 栈（支持嵌套）
        self._observers: list[Callable[[str, dict[str, Any]], None]] = []
        self._started_at = time.time()
        self._span_seq = 0

    def xǁObservabilityBusǁ__init____mutmut_9(self, run_id: str = ""):
        self.run_id = run_id or "run_unknown"
        self._events: list[dict[str, Any]] = []
        self._spans: list[dict[str, Any]] = []
        self._span_stack: list[str] = []  # 当前 span id 栈（支持嵌套）
        self._observers: list[Callable[[str, dict[str, Any]], None]] = None
        self._started_at = time.time()
        self._span_seq = 0

    def xǁObservabilityBusǁ__init____mutmut_10(self, run_id: str = ""):
        self.run_id = run_id or "run_unknown"
        self._events: list[dict[str, Any]] = []
        self._spans: list[dict[str, Any]] = []
        self._span_stack: list[str] = []  # 当前 span id 栈（支持嵌套）
        self._observers: list[Callable[[str, dict[str, Any]], None]] = []
        self._started_at = None
        self._span_seq = 0

    def xǁObservabilityBusǁ__init____mutmut_11(self, run_id: str = ""):
        self.run_id = run_id or "run_unknown"
        self._events: list[dict[str, Any]] = []
        self._spans: list[dict[str, Any]] = []
        self._span_stack: list[str] = []  # 当前 span id 栈（支持嵌套）
        self._observers: list[Callable[[str, dict[str, Any]], None]] = []
        self._started_at = time.time()
        self._span_seq = None

    def xǁObservabilityBusǁ__init____mutmut_12(self, run_id: str = ""):
        self.run_id = run_id or "run_unknown"
        self._events: list[dict[str, Any]] = []
        self._spans: list[dict[str, Any]] = []
        self._span_stack: list[str] = []  # 当前 span id 栈（支持嵌套）
        self._observers: list[Callable[[str, dict[str, Any]], None]] = []
        self._started_at = time.time()
        self._span_seq = 1

    # ---- 订阅 ----
    @_mutmut_mutated(mutants_xǁObservabilityBusǁsubscribe__mutmut)
    def subscribe(self, observer: Callable[[str, dict[str, Any]], None]) -> None:
        """订阅事件（observer(event_type, payload)）。"""
        self._observers.append(observer)

    # ---- 订阅 ----
    def xǁObservabilityBusǁsubscribe__mutmut_orig(self, observer: Callable[[str, dict[str, Any]], None]) -> None:
        """订阅事件（observer(event_type, payload)）。"""
        self._observers.append(observer)

    # ---- 订阅 ----
    def xǁObservabilityBusǁsubscribe__mutmut_1(self, observer: Callable[[str, dict[str, Any]], None]) -> None:
        """订阅事件（observer(event_type, payload)）。"""
        self._observers.append(None)

    # ---- 事件 ----
    @_mutmut_mutated(mutants_xǁObservabilityBusǁrecord_event__mutmut)
    def record_event(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """记录一个事件（带时间戳与当前 span 上下文）。"""
        ev = {
            "event": event_type,
            "ts": round(time.time() - self._started_at, 4),
            "run_id": self.run_id,
            "current_span": self._span_stack[-1] if self._span_stack else None,
            **(payload or {}),
        }
        self._events.append(ev)
        for obs in self._observers:
            try:
                obs(event_type, ev)
            except Exception:
                pass  # 观察者异常不阻断主线

    # ---- 事件 ----
    def xǁObservabilityBusǁrecord_event__mutmut_orig(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """记录一个事件（带时间戳与当前 span 上下文）。"""
        ev = {
            "event": event_type,
            "ts": round(time.time() - self._started_at, 4),
            "run_id": self.run_id,
            "current_span": self._span_stack[-1] if self._span_stack else None,
            **(payload or {}),
        }
        self._events.append(ev)
        for obs in self._observers:
            try:
                obs(event_type, ev)
            except Exception:
                pass  # 观察者异常不阻断主线

    # ---- 事件 ----
    def xǁObservabilityBusǁrecord_event__mutmut_1(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """记录一个事件（带时间戳与当前 span 上下文）。"""
        ev = None
        self._events.append(ev)
        for obs in self._observers:
            try:
                obs(event_type, ev)
            except Exception:
                pass  # 观察者异常不阻断主线

    # ---- 事件 ----
    def xǁObservabilityBusǁrecord_event__mutmut_2(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """记录一个事件（带时间戳与当前 span 上下文）。"""
        ev = {
            "XXeventXX": event_type,
            "ts": round(time.time() - self._started_at, 4),
            "run_id": self.run_id,
            "current_span": self._span_stack[-1] if self._span_stack else None,
            **(payload or {}),
        }
        self._events.append(ev)
        for obs in self._observers:
            try:
                obs(event_type, ev)
            except Exception:
                pass  # 观察者异常不阻断主线

    # ---- 事件 ----
    def xǁObservabilityBusǁrecord_event__mutmut_3(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """记录一个事件（带时间戳与当前 span 上下文）。"""
        ev = {
            "EVENT": event_type,
            "ts": round(time.time() - self._started_at, 4),
            "run_id": self.run_id,
            "current_span": self._span_stack[-1] if self._span_stack else None,
            **(payload or {}),
        }
        self._events.append(ev)
        for obs in self._observers:
            try:
                obs(event_type, ev)
            except Exception:
                pass  # 观察者异常不阻断主线

    # ---- 事件 ----
    def xǁObservabilityBusǁrecord_event__mutmut_4(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """记录一个事件（带时间戳与当前 span 上下文）。"""
        ev = {
            "event": event_type,
            "XXtsXX": round(time.time() - self._started_at, 4),
            "run_id": self.run_id,
            "current_span": self._span_stack[-1] if self._span_stack else None,
            **(payload or {}),
        }
        self._events.append(ev)
        for obs in self._observers:
            try:
                obs(event_type, ev)
            except Exception:
                pass  # 观察者异常不阻断主线

    # ---- 事件 ----
    def xǁObservabilityBusǁrecord_event__mutmut_5(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """记录一个事件（带时间戳与当前 span 上下文）。"""
        ev = {
            "event": event_type,
            "TS": round(time.time() - self._started_at, 4),
            "run_id": self.run_id,
            "current_span": self._span_stack[-1] if self._span_stack else None,
            **(payload or {}),
        }
        self._events.append(ev)
        for obs in self._observers:
            try:
                obs(event_type, ev)
            except Exception:
                pass  # 观察者异常不阻断主线

    # ---- 事件 ----
    def xǁObservabilityBusǁrecord_event__mutmut_6(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """记录一个事件（带时间戳与当前 span 上下文）。"""
        ev = {
            "event": event_type,
            "ts": round(None, 4),
            "run_id": self.run_id,
            "current_span": self._span_stack[-1] if self._span_stack else None,
            **(payload or {}),
        }
        self._events.append(ev)
        for obs in self._observers:
            try:
                obs(event_type, ev)
            except Exception:
                pass  # 观察者异常不阻断主线

    # ---- 事件 ----
    def xǁObservabilityBusǁrecord_event__mutmut_7(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """记录一个事件（带时间戳与当前 span 上下文）。"""
        ev = {
            "event": event_type,
            "ts": round(time.time() - self._started_at, None),
            "run_id": self.run_id,
            "current_span": self._span_stack[-1] if self._span_stack else None,
            **(payload or {}),
        }
        self._events.append(ev)
        for obs in self._observers:
            try:
                obs(event_type, ev)
            except Exception:
                pass  # 观察者异常不阻断主线

    # ---- 事件 ----
    def xǁObservabilityBusǁrecord_event__mutmut_8(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """记录一个事件（带时间戳与当前 span 上下文）。"""
        ev = {
            "event": event_type,
            "ts": round(4),
            "run_id": self.run_id,
            "current_span": self._span_stack[-1] if self._span_stack else None,
            **(payload or {}),
        }
        self._events.append(ev)
        for obs in self._observers:
            try:
                obs(event_type, ev)
            except Exception:
                pass  # 观察者异常不阻断主线

    # ---- 事件 ----
    def xǁObservabilityBusǁrecord_event__mutmut_9(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """记录一个事件（带时间戳与当前 span 上下文）。"""
        ev = {
            "event": event_type,
            "ts": round(time.time() - self._started_at, ),
            "run_id": self.run_id,
            "current_span": self._span_stack[-1] if self._span_stack else None,
            **(payload or {}),
        }
        self._events.append(ev)
        for obs in self._observers:
            try:
                obs(event_type, ev)
            except Exception:
                pass  # 观察者异常不阻断主线

    # ---- 事件 ----
    def xǁObservabilityBusǁrecord_event__mutmut_10(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """记录一个事件（带时间戳与当前 span 上下文）。"""
        ev = {
            "event": event_type,
            "ts": round(time.time() + self._started_at, 4),
            "run_id": self.run_id,
            "current_span": self._span_stack[-1] if self._span_stack else None,
            **(payload or {}),
        }
        self._events.append(ev)
        for obs in self._observers:
            try:
                obs(event_type, ev)
            except Exception:
                pass  # 观察者异常不阻断主线

    # ---- 事件 ----
    def xǁObservabilityBusǁrecord_event__mutmut_11(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """记录一个事件（带时间戳与当前 span 上下文）。"""
        ev = {
            "event": event_type,
            "ts": round(time.time() - self._started_at, 5),
            "run_id": self.run_id,
            "current_span": self._span_stack[-1] if self._span_stack else None,
            **(payload or {}),
        }
        self._events.append(ev)
        for obs in self._observers:
            try:
                obs(event_type, ev)
            except Exception:
                pass  # 观察者异常不阻断主线

    # ---- 事件 ----
    def xǁObservabilityBusǁrecord_event__mutmut_12(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """记录一个事件（带时间戳与当前 span 上下文）。"""
        ev = {
            "event": event_type,
            "ts": round(time.time() - self._started_at, 4),
            "XXrun_idXX": self.run_id,
            "current_span": self._span_stack[-1] if self._span_stack else None,
            **(payload or {}),
        }
        self._events.append(ev)
        for obs in self._observers:
            try:
                obs(event_type, ev)
            except Exception:
                pass  # 观察者异常不阻断主线

    # ---- 事件 ----
    def xǁObservabilityBusǁrecord_event__mutmut_13(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """记录一个事件（带时间戳与当前 span 上下文）。"""
        ev = {
            "event": event_type,
            "ts": round(time.time() - self._started_at, 4),
            "RUN_ID": self.run_id,
            "current_span": self._span_stack[-1] if self._span_stack else None,
            **(payload or {}),
        }
        self._events.append(ev)
        for obs in self._observers:
            try:
                obs(event_type, ev)
            except Exception:
                pass  # 观察者异常不阻断主线

    # ---- 事件 ----
    def xǁObservabilityBusǁrecord_event__mutmut_14(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """记录一个事件（带时间戳与当前 span 上下文）。"""
        ev = {
            "event": event_type,
            "ts": round(time.time() - self._started_at, 4),
            "run_id": self.run_id,
            "XXcurrent_spanXX": self._span_stack[-1] if self._span_stack else None,
            **(payload or {}),
        }
        self._events.append(ev)
        for obs in self._observers:
            try:
                obs(event_type, ev)
            except Exception:
                pass  # 观察者异常不阻断主线

    # ---- 事件 ----
    def xǁObservabilityBusǁrecord_event__mutmut_15(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """记录一个事件（带时间戳与当前 span 上下文）。"""
        ev = {
            "event": event_type,
            "ts": round(time.time() - self._started_at, 4),
            "run_id": self.run_id,
            "CURRENT_SPAN": self._span_stack[-1] if self._span_stack else None,
            **(payload or {}),
        }
        self._events.append(ev)
        for obs in self._observers:
            try:
                obs(event_type, ev)
            except Exception:
                pass  # 观察者异常不阻断主线

    # ---- 事件 ----
    def xǁObservabilityBusǁrecord_event__mutmut_16(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """记录一个事件（带时间戳与当前 span 上下文）。"""
        ev = {
            "event": event_type,
            "ts": round(time.time() - self._started_at, 4),
            "run_id": self.run_id,
            "current_span": self._span_stack[-1] if (self._span_stack) and False else None,
            **(payload or {}),
        }
        self._events.append(ev)
        for obs in self._observers:
            try:
                obs(event_type, ev)
            except Exception:
                pass  # 观察者异常不阻断主线

    # ---- 事件 ----
    def xǁObservabilityBusǁrecord_event__mutmut_17(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """记录一个事件（带时间戳与当前 span 上下文）。"""
        ev = {
            "event": event_type,
            "ts": round(time.time() - self._started_at, 4),
            "run_id": self.run_id,
            "current_span": self._span_stack[-1] if (self._span_stack) or True else None,
            **(payload or {}),
        }
        self._events.append(ev)
        for obs in self._observers:
            try:
                obs(event_type, ev)
            except Exception:
                pass  # 观察者异常不阻断主线

    # ---- 事件 ----
    def xǁObservabilityBusǁrecord_event__mutmut_18(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """记录一个事件（带时间戳与当前 span 上下文）。"""
        ev = {
            "event": event_type,
            "ts": round(time.time() - self._started_at, 4),
            "run_id": self.run_id,
            "current_span": self._span_stack[+1] if self._span_stack else None,
            **(payload or {}),
        }
        self._events.append(ev)
        for obs in self._observers:
            try:
                obs(event_type, ev)
            except Exception:
                pass  # 观察者异常不阻断主线

    # ---- 事件 ----
    def xǁObservabilityBusǁrecord_event__mutmut_19(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """记录一个事件（带时间戳与当前 span 上下文）。"""
        ev = {
            "event": event_type,
            "ts": round(time.time() - self._started_at, 4),
            "run_id": self.run_id,
            "current_span": self._span_stack[-2] if self._span_stack else None,
            **(payload or {}),
        }
        self._events.append(ev)
        for obs in self._observers:
            try:
                obs(event_type, ev)
            except Exception:
                pass  # 观察者异常不阻断主线

    # ---- 事件 ----
    def xǁObservabilityBusǁrecord_event__mutmut_20(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """记录一个事件（带时间戳与当前 span 上下文）。"""
        ev = {
            "event": event_type,
            "ts": round(time.time() - self._started_at, 4),
            "run_id": self.run_id,
            "current_span": self._span_stack[-1] if self._span_stack else None,
            **(payload and {}),
        }
        self._events.append(ev)
        for obs in self._observers:
            try:
                obs(event_type, ev)
            except Exception:
                pass  # 观察者异常不阻断主线

    # ---- 事件 ----
    def xǁObservabilityBusǁrecord_event__mutmut_21(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """记录一个事件（带时间戳与当前 span 上下文）。"""
        ev = {
            "event": event_type,
            "ts": round(time.time() - self._started_at, 4),
            "run_id": self.run_id,
            "current_span": self._span_stack[-1] if self._span_stack else None,
            **(payload or {}),
        }
        self._events.append(None)
        for obs in self._observers:
            try:
                obs(event_type, ev)
            except Exception:
                pass  # 观察者异常不阻断主线

    # ---- 事件 ----
    def xǁObservabilityBusǁrecord_event__mutmut_22(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """记录一个事件（带时间戳与当前 span 上下文）。"""
        ev = {
            "event": event_type,
            "ts": round(time.time() - self._started_at, 4),
            "run_id": self.run_id,
            "current_span": self._span_stack[-1] if self._span_stack else None,
            **(payload or {}),
        }
        self._events.append(ev)
        for obs in self._observers:
            try:
                obs(None, ev)
            except Exception:
                pass  # 观察者异常不阻断主线

    # ---- 事件 ----
    def xǁObservabilityBusǁrecord_event__mutmut_23(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """记录一个事件（带时间戳与当前 span 上下文）。"""
        ev = {
            "event": event_type,
            "ts": round(time.time() - self._started_at, 4),
            "run_id": self.run_id,
            "current_span": self._span_stack[-1] if self._span_stack else None,
            **(payload or {}),
        }
        self._events.append(ev)
        for obs in self._observers:
            try:
                obs(event_type, None)
            except Exception:
                pass  # 观察者异常不阻断主线

    # ---- 事件 ----
    def xǁObservabilityBusǁrecord_event__mutmut_24(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """记录一个事件（带时间戳与当前 span 上下文）。"""
        ev = {
            "event": event_type,
            "ts": round(time.time() - self._started_at, 4),
            "run_id": self.run_id,
            "current_span": self._span_stack[-1] if self._span_stack else None,
            **(payload or {}),
        }
        self._events.append(ev)
        for obs in self._observers:
            try:
                obs(ev)
            except Exception:
                pass  # 观察者异常不阻断主线

    # ---- 事件 ----
    def xǁObservabilityBusǁrecord_event__mutmut_25(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """记录一个事件（带时间戳与当前 span 上下文）。"""
        ev = {
            "event": event_type,
            "ts": round(time.time() - self._started_at, 4),
            "run_id": self.run_id,
            "current_span": self._span_stack[-1] if self._span_stack else None,
            **(payload or {}),
        }
        self._events.append(ev)
        for obs in self._observers:
            try:
                obs(event_type, )
            except Exception:
                pass  # 观察者异常不阻断主线

    # ---- Span 生命周期（上下文管理器）----
    @_mutmut_mutated(mutants_xǁObservabilityBusǁspan__mutmut)
    def span(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_orig(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_1(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq = 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_2(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq -= 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_3(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 2
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_4(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = None
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_5(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_6(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if (self._span_stack) and False else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_7(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if (self._span_stack) or True else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_8(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[+1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_9(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-2] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_10(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = None
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_11(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "XXspan_idXX": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_12(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "SPAN_ID": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_13(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "XXnameXX": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_14(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "NAME": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_15(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "XXparentXX": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_16(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "PARENT": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_17(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "XXattrsXX": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_18(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "ATTRS": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_19(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs and {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_20(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "XXstart_tsXX": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_21(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "START_TS": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_22(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(None, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_23(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, None),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_24(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_25(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, ),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_26(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() + self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_27(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 5),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_28(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "XXduration_msXX": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_29(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "DURATION_MS": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_30(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "XXstatusXX": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_31(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "STATUS": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_32(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "XXopenXX",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_33(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "OPEN",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_34(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(None)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_35(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(None)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_36(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(None, {"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_37(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, None)
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_38(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event({"span": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_39(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, )
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_40(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"XXspanXX": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_41(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"SPAN": name, "span_id": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_42(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "XXspan_idXX": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_43(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "SPAN_ID": span_id})
        return _SpanCtx(self, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_44(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(None, span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_45(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, None)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_46(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(span_id)

    # ---- Span 生命周期（上下文管理器）----
    def xǁObservabilityBusǁspan__mutmut_47(self, name: str, attrs: dict[str, Any] | None = None) -> _SpanCtx:
        """开启一个 span（支持 with 语法），自动记录开始/结束/耗时。"""
        self._span_seq += 1
        span_id = f"span_{self._span_seq}"
        parent = self._span_stack[-1] if self._span_stack else None
        span = {
            "span_id": span_id,
            "name": name,
            "parent": parent,
            "attrs": attrs or {},
            "start_ts": round(time.time() - self._started_at, 4),
            "duration_ms": None,
            "status": "open",
        }
        self._spans.append(span)
        self._span_stack.append(span_id)
        self.record_event(EVENT_STEP_START, {"span": name, "span_id": span_id})
        return _SpanCtx(self, )

    @_mutmut_mutated(mutants_xǁObservabilityBusǁ_end_span__mutmut)
    def _end_span(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1000, 2)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_orig(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1000, 2)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_1(self, span_id: str, status: str = "XXokXX") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1000, 2)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_2(self, span_id: str, status: str = "OK") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1000, 2)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_3(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["XXspan_idXX"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1000, 2)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_4(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["SPAN_ID"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1000, 2)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_5(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] != span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1000, 2)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_6(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = None
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_7(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["XXduration_msXX"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1000, 2)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_8(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["DURATION_MS"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1000, 2)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_9(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    None, 2)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_10(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1000, None)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_11(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    2)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_12(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1000, )
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_13(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["start_ts"]) / 1000, 2)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_14(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at + s["start_ts"]) * 1000, 2)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_15(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() + self._started_at - s["start_ts"]) * 1000, 2)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_16(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["XXstart_tsXX"]) * 1000, 2)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_17(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["START_TS"]) * 1000, 2)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_18(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1001, 2)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_19(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1000, 3)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_20(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1000, 2)
                s["status"] = None
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_21(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1000, 2)
                s["XXstatusXX"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_22(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1000, 2)
                s["STATUS"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_23(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1000, 2)
                s["status"] = status
                return
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_24(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1000, 2)
                s["status"] = status
                break
        if self._span_stack or self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_25(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1000, 2)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[+1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_26(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1000, 2)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-2] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_27(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1000, 2)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] != span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_28(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1000, 2)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(None, {"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_29(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1000, 2)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, None)

    def xǁObservabilityBusǁ_end_span__mutmut_30(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1000, 2)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event({"span": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_31(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1000, 2)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, )

    def xǁObservabilityBusǁ_end_span__mutmut_32(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1000, 2)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"XXspanXX": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_33(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1000, 2)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"SPAN": span_id, "status": status})

    def xǁObservabilityBusǁ_end_span__mutmut_34(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1000, 2)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "XXstatusXX": status})

    def xǁObservabilityBusǁ_end_span__mutmut_35(self, span_id: str, status: str = "ok") -> None:
        for s in self._spans:
            if s["span_id"] == span_id:
                s["duration_ms"] = round(
                    (time.time() - self._started_at - s["start_ts"]) * 1000, 2)
                s["status"] = status
                break
        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()
        self.record_event(EVENT_STEP_END, {"span": span_id, "STATUS": status})

    # ---- 指标聚合 ----
    @_mutmut_mutated(mutants_xǁObservabilityBusǁexport_metrics__mutmut)
    def export_metrics(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_orig(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_1(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = None
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_2(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = None
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_3(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = None
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_4(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(None)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_5(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(2 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_6(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["XXeventXX"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_7(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["EVENT"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_8(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] != EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_9(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = None
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_10(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(None)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_11(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(2 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_12(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["XXeventXX"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_13(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["EVENT"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_14(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] != EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_15(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = None
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_16(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = None
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_17(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["XXnameXX"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_18(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["NAME"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_19(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = None
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_20(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(None, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_21(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, None)
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_22(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault({"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_23(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, )
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_24(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"XXcountXX": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_25(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"COUNT": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_26(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 1, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_27(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "XXtotal_msXX": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_28(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "TOTAL_MS": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_29(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 1.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_30(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "XXmin_msXX": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_31(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "MIN_MS": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_32(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "XXmax_msXX": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_33(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "MAX_MS": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_34(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 1.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_35(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] = 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_36(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] -= 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_37(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["XXcountXX"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_38(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["COUNT"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_39(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 2
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_40(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] = s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_41(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] -= s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_42(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["XXtotal_msXX"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_43(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["TOTAL_MS"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_44(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] and 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_45(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["XXduration_msXX"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_46(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["DURATION_MS"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_47(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 1.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_48(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None and s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_49(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["XXmin_msXX"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_50(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["MIN_MS"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_51(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is not None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_52(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["XXduration_msXX"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_53(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["DURATION_MS"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_54(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] <= d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_55(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["XXmin_msXX"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_56(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["MIN_MS"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_57(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = None
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_58(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["XXmin_msXX"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_59(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["MIN_MS"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_60(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["XXduration_msXX"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_61(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["DURATION_MS"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_62(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = None
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_63(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["XXmax_msXX"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_64(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["MAX_MS"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_65(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(None, s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_66(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], None)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_67(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_68(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], )
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_69(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["XXmax_msXX"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_70(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["MAX_MS"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_71(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] and 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_72(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["XXduration_msXX"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_73(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["DURATION_MS"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_74(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 1.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_75(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = None
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_76(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["XXavg_msXX"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_77(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["AVG_MS"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_78(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if (d["count"]) and False else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_79(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if (d["count"]) or True else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_80(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(None, 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_81(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], None) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_82(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_83(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], ) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_84(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] * d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_85(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["XXtotal_msXX"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_86(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["TOTAL_MS"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_87(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["XXcountXX"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_88(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["COUNT"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_89(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 3) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_90(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["XXcountXX"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_91(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["COUNT"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_92(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 1.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_93(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "XXrun_idXX": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_94(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "RUN_ID": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_95(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "XXtotal_stepsXX": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_96(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "TOTAL_STEPS": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_97(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "XXdegradation_countXX": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_98(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "DEGRADATION_COUNT": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_99(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "XXrollback_countXX": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_100(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "ROLLBACK_COUNT": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_101(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "XXdegradation_rateXX": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_102(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "DEGRADATION_RATE": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_103(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if (total) and False else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_104(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if (total) or True else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_105(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(None, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_106(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, None) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_107(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_108(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, ) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_109(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded * total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_110(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 4) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_111(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 1.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_112(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "XXrollback_rateXX": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_113(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "ROLLBACK_RATE": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_114(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if (total) and False else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_115(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if (total) or True else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_116(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(None, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_117(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, None) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_118(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_119(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, ) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_120(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back * total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_121(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 4) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_122(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 1.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_123(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "XXstep_statsXX": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_124(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "STEP_STATS": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_125(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "XXtotal_duration_msXX": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_126(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "TOTAL_DURATION_MS": round((time.time() - self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_127(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round(None, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_128(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, None),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_129(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round(2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_130(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, ),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_131(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) / 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_132(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() + self._started_at) * 1000, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_133(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1001, 2),
        }

    # ---- 指标聚合 ----
    def xǁObservabilityBusǁexport_metrics__mutmut_134(self) -> dict[str, Any]:
        """聚合指标：各步耗时 / 降级率 / 回退率 / 门控通过率。"""
        steps = [s for s in self._spans]
        total = len(steps)
        degraded = sum(1 for e in self._events if e["event"] == EVENT_DEGRADE)
        rolled_back = sum(1 for e in self._events if e["event"] == EVENT_ROLLBACK)
        step_stats: dict[str, dict[str, float]] = {}
        for s in steps:
            name = s["name"]
            d = step_stats.setdefault(name, {"count": 0, "total_ms": 0.0,
                                             "min_ms": None, "max_ms": 0.0})
            d["count"] += 1
            d["total_ms"] += s["duration_ms"] or 0.0
            if d["min_ms"] is None or s["duration_ms"] < d["min_ms"]:
                d["min_ms"] = s["duration_ms"]
            d["max_ms"] = max(d["max_ms"], s["duration_ms"] or 0.0)
        for d in step_stats.values():
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2) if d["count"] else 0.0
        return {
            "run_id": self.run_id,
            "total_steps": total,
            "degradation_count": degraded,
            "rollback_count": rolled_back,
            "degradation_rate": round(degraded / total, 3) if total else 0.0,
            "rollback_rate": round(rolled_back / total, 3) if total else 0.0,
            "step_stats": step_stats,
            "total_duration_ms": round((time.time() - self._started_at) * 1000, 3),
        }

    # ---- 导出 ----
    @_mutmut_mutated(mutants_xǁObservabilityBusǁexport_jsonl__mutmut)
    def export_jsonl(self) -> str:
        """导出结构化事件流（JSON Lines，含 span 层级与耗时）。"""
        lines = [json.dumps(e, ensure_ascii=False) for e in self._events]
        lines.append(json.dumps({
            "event": "metrics_snapshot", "run_id": self.run_id,
            "metrics": self.export_metrics(),
        }, ensure_ascii=False))
        return "\n".join(lines)

    # ---- 导出 ----
    def xǁObservabilityBusǁexport_jsonl__mutmut_orig(self) -> str:
        """导出结构化事件流（JSON Lines，含 span 层级与耗时）。"""
        lines = [json.dumps(e, ensure_ascii=False) for e in self._events]
        lines.append(json.dumps({
            "event": "metrics_snapshot", "run_id": self.run_id,
            "metrics": self.export_metrics(),
        }, ensure_ascii=False))
        return "\n".join(lines)

    # ---- 导出 ----
    def xǁObservabilityBusǁexport_jsonl__mutmut_1(self) -> str:
        """导出结构化事件流（JSON Lines，含 span 层级与耗时）。"""
        lines = None
        lines.append(json.dumps({
            "event": "metrics_snapshot", "run_id": self.run_id,
            "metrics": self.export_metrics(),
        }, ensure_ascii=False))
        return "\n".join(lines)

    # ---- 导出 ----
    def xǁObservabilityBusǁexport_jsonl__mutmut_2(self) -> str:
        """导出结构化事件流（JSON Lines，含 span 层级与耗时）。"""
        lines = [json.dumps(None, ensure_ascii=False) for e in self._events]
        lines.append(json.dumps({
            "event": "metrics_snapshot", "run_id": self.run_id,
            "metrics": self.export_metrics(),
        }, ensure_ascii=False))
        return "\n".join(lines)

    # ---- 导出 ----
    def xǁObservabilityBusǁexport_jsonl__mutmut_3(self) -> str:
        """导出结构化事件流（JSON Lines，含 span 层级与耗时）。"""
        lines = [json.dumps(e, ensure_ascii=None) for e in self._events]
        lines.append(json.dumps({
            "event": "metrics_snapshot", "run_id": self.run_id,
            "metrics": self.export_metrics(),
        }, ensure_ascii=False))
        return "\n".join(lines)

    # ---- 导出 ----
    def xǁObservabilityBusǁexport_jsonl__mutmut_4(self) -> str:
        """导出结构化事件流（JSON Lines，含 span 层级与耗时）。"""
        lines = [json.dumps(ensure_ascii=False) for e in self._events]
        lines.append(json.dumps({
            "event": "metrics_snapshot", "run_id": self.run_id,
            "metrics": self.export_metrics(),
        }, ensure_ascii=False))
        return "\n".join(lines)

    # ---- 导出 ----
    def xǁObservabilityBusǁexport_jsonl__mutmut_5(self) -> str:
        """导出结构化事件流（JSON Lines，含 span 层级与耗时）。"""
        lines = [json.dumps(e, ) for e in self._events]
        lines.append(json.dumps({
            "event": "metrics_snapshot", "run_id": self.run_id,
            "metrics": self.export_metrics(),
        }, ensure_ascii=False))
        return "\n".join(lines)

    # ---- 导出 ----
    def xǁObservabilityBusǁexport_jsonl__mutmut_6(self) -> str:
        """导出结构化事件流（JSON Lines，含 span 层级与耗时）。"""
        lines = [json.dumps(e, ensure_ascii=True) for e in self._events]
        lines.append(json.dumps({
            "event": "metrics_snapshot", "run_id": self.run_id,
            "metrics": self.export_metrics(),
        }, ensure_ascii=False))
        return "\n".join(lines)

    # ---- 导出 ----
    def xǁObservabilityBusǁexport_jsonl__mutmut_7(self) -> str:
        """导出结构化事件流（JSON Lines，含 span 层级与耗时）。"""
        lines = [json.dumps(e, ensure_ascii=False) for e in self._events]
        lines.append(None)
        return "\n".join(lines)

    # ---- 导出 ----
    def xǁObservabilityBusǁexport_jsonl__mutmut_8(self) -> str:
        """导出结构化事件流（JSON Lines，含 span 层级与耗时）。"""
        lines = [json.dumps(e, ensure_ascii=False) for e in self._events]
        lines.append(json.dumps(None, ensure_ascii=False))
        return "\n".join(lines)

    # ---- 导出 ----
    def xǁObservabilityBusǁexport_jsonl__mutmut_9(self) -> str:
        """导出结构化事件流（JSON Lines，含 span 层级与耗时）。"""
        lines = [json.dumps(e, ensure_ascii=False) for e in self._events]
        lines.append(json.dumps({
            "event": "metrics_snapshot", "run_id": self.run_id,
            "metrics": self.export_metrics(),
        }, ensure_ascii=None))
        return "\n".join(lines)

    # ---- 导出 ----
    def xǁObservabilityBusǁexport_jsonl__mutmut_10(self) -> str:
        """导出结构化事件流（JSON Lines，含 span 层级与耗时）。"""
        lines = [json.dumps(e, ensure_ascii=False) for e in self._events]
        lines.append(json.dumps(ensure_ascii=False))
        return "\n".join(lines)

    # ---- 导出 ----
    def xǁObservabilityBusǁexport_jsonl__mutmut_11(self) -> str:
        """导出结构化事件流（JSON Lines，含 span 层级与耗时）。"""
        lines = [json.dumps(e, ensure_ascii=False) for e in self._events]
        lines.append(json.dumps({
            "event": "metrics_snapshot", "run_id": self.run_id,
            "metrics": self.export_metrics(),
        }, ))
        return "\n".join(lines)

    # ---- 导出 ----
    def xǁObservabilityBusǁexport_jsonl__mutmut_12(self) -> str:
        """导出结构化事件流（JSON Lines，含 span 层级与耗时）。"""
        lines = [json.dumps(e, ensure_ascii=False) for e in self._events]
        lines.append(json.dumps({
            "XXeventXX": "metrics_snapshot", "run_id": self.run_id,
            "metrics": self.export_metrics(),
        }, ensure_ascii=False))
        return "\n".join(lines)

    # ---- 导出 ----
    def xǁObservabilityBusǁexport_jsonl__mutmut_13(self) -> str:
        """导出结构化事件流（JSON Lines，含 span 层级与耗时）。"""
        lines = [json.dumps(e, ensure_ascii=False) for e in self._events]
        lines.append(json.dumps({
            "EVENT": "metrics_snapshot", "run_id": self.run_id,
            "metrics": self.export_metrics(),
        }, ensure_ascii=False))
        return "\n".join(lines)

    # ---- 导出 ----
    def xǁObservabilityBusǁexport_jsonl__mutmut_14(self) -> str:
        """导出结构化事件流（JSON Lines，含 span 层级与耗时）。"""
        lines = [json.dumps(e, ensure_ascii=False) for e in self._events]
        lines.append(json.dumps({
            "event": "XXmetrics_snapshotXX", "run_id": self.run_id,
            "metrics": self.export_metrics(),
        }, ensure_ascii=False))
        return "\n".join(lines)

    # ---- 导出 ----
    def xǁObservabilityBusǁexport_jsonl__mutmut_15(self) -> str:
        """导出结构化事件流（JSON Lines，含 span 层级与耗时）。"""
        lines = [json.dumps(e, ensure_ascii=False) for e in self._events]
        lines.append(json.dumps({
            "event": "METRICS_SNAPSHOT", "run_id": self.run_id,
            "metrics": self.export_metrics(),
        }, ensure_ascii=False))
        return "\n".join(lines)

    # ---- 导出 ----
    def xǁObservabilityBusǁexport_jsonl__mutmut_16(self) -> str:
        """导出结构化事件流（JSON Lines，含 span 层级与耗时）。"""
        lines = [json.dumps(e, ensure_ascii=False) for e in self._events]
        lines.append(json.dumps({
            "event": "metrics_snapshot", "XXrun_idXX": self.run_id,
            "metrics": self.export_metrics(),
        }, ensure_ascii=False))
        return "\n".join(lines)

    # ---- 导出 ----
    def xǁObservabilityBusǁexport_jsonl__mutmut_17(self) -> str:
        """导出结构化事件流（JSON Lines，含 span 层级与耗时）。"""
        lines = [json.dumps(e, ensure_ascii=False) for e in self._events]
        lines.append(json.dumps({
            "event": "metrics_snapshot", "RUN_ID": self.run_id,
            "metrics": self.export_metrics(),
        }, ensure_ascii=False))
        return "\n".join(lines)

    # ---- 导出 ----
    def xǁObservabilityBusǁexport_jsonl__mutmut_18(self) -> str:
        """导出结构化事件流（JSON Lines，含 span 层级与耗时）。"""
        lines = [json.dumps(e, ensure_ascii=False) for e in self._events]
        lines.append(json.dumps({
            "event": "metrics_snapshot", "run_id": self.run_id,
            "XXmetricsXX": self.export_metrics(),
        }, ensure_ascii=False))
        return "\n".join(lines)

    # ---- 导出 ----
    def xǁObservabilityBusǁexport_jsonl__mutmut_19(self) -> str:
        """导出结构化事件流（JSON Lines，含 span 层级与耗时）。"""
        lines = [json.dumps(e, ensure_ascii=False) for e in self._events]
        lines.append(json.dumps({
            "event": "metrics_snapshot", "run_id": self.run_id,
            "METRICS": self.export_metrics(),
        }, ensure_ascii=False))
        return "\n".join(lines)

    # ---- 导出 ----
    def xǁObservabilityBusǁexport_jsonl__mutmut_20(self) -> str:
        """导出结构化事件流（JSON Lines，含 span 层级与耗时）。"""
        lines = [json.dumps(e, ensure_ascii=False) for e in self._events]
        lines.append(json.dumps({
            "event": "metrics_snapshot", "run_id": self.run_id,
            "metrics": self.export_metrics(),
        }, ensure_ascii=True))
        return "\n".join(lines)

    # ---- 导出 ----
    def xǁObservabilityBusǁexport_jsonl__mutmut_21(self) -> str:
        """导出结构化事件流（JSON Lines，含 span 层级与耗时）。"""
        lines = [json.dumps(e, ensure_ascii=False) for e in self._events]
        lines.append(json.dumps({
            "event": "metrics_snapshot", "run_id": self.run_id,
            "metrics": self.export_metrics(),
        }, ensure_ascii=False))
        return "\n".join(None)

    # ---- 导出 ----
    def xǁObservabilityBusǁexport_jsonl__mutmut_22(self) -> str:
        """导出结构化事件流（JSON Lines，含 span 层级与耗时）。"""
        lines = [json.dumps(e, ensure_ascii=False) for e in self._events]
        lines.append(json.dumps({
            "event": "metrics_snapshot", "run_id": self.run_id,
            "metrics": self.export_metrics(),
        }, ensure_ascii=False))
        return "XX\nXX".join(lines)

    @_mutmut_mutated(mutants_xǁObservabilityBusǁexport_span_tree__mutmut)
    def export_span_tree(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_orig(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_1(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = None
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_2(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["XXparentXX"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_3(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["PARENT"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_4(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is not None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_5(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = None

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_6(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = None
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_7(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " / depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_8(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "XX  XX" * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_9(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = None
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_10(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if (span["duration_ms"] is not None) and False else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_11(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if (span["duration_ms"] is not None) or True else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_12(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['XXduration_msXX']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_13(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['DURATION_MS']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_14(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["XXduration_msXX"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_15(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["DURATION_MS"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_16(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_17(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "XXopenXX"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_18(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "OPEN"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_19(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(None)
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_20(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['XXnameXX']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_21(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['NAME']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_22(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['XXspan_idXX']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_23(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['SPAN_ID']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_24(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['XXstatusXX']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_25(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['STATUS']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_26(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["XXparentXX"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_27(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["PARENT"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_28(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] != span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_29(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["XXspan_idXX"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_30(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["SPAN_ID"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_31(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(None, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_32(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, None)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_33(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_34(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, )

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_35(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth - 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_36(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 2)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_37(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(None, 0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_38(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, None)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_39(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(0)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_40(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, )
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_41(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 1)
        return "\n".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_42(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) and "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_43(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(None) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_44(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "XX\nXX".join(out) or "(no spans)"

    def xǁObservabilityBusǁexport_span_tree__mutmut_45(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "XX(no spans)XX"

    def xǁObservabilityBusǁexport_span_tree__mutmut_46(self) -> str:
        """导出 span 树（人类可读，含缩进层级与耗时）。"""
        roots = [s for s in self._spans if s["parent"] is None]
        out = []

        def walk(span, depth: int):
            pad = "  " * depth
            dur = f"{span['duration_ms']}ms" if span["duration_ms"] is not None else "open"
            out.append(f"{pad}├─ {span['name']} [{span['span_id']}] ({dur}) {span['status']}")
            for child in self._spans:
                if child["parent"] == span["span_id"]:
                    walk(child, depth + 1)

        for root in roots:
            walk(root, 0)
        return "\n".join(out) or "(NO SPANS)"

mutants_xǁObservabilityBusǁ__init____mutmut['_mutmut_orig'] = ObservabilityBus.xǁObservabilityBusǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ__init____mutmut['xǁObservabilityBusǁ__init____mutmut_1'] = ObservabilityBus.xǁObservabilityBusǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ__init____mutmut['xǁObservabilityBusǁ__init____mutmut_2'] = ObservabilityBus.xǁObservabilityBusǁ__init____mutmut_2 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ__init____mutmut['xǁObservabilityBusǁ__init____mutmut_3'] = ObservabilityBus.xǁObservabilityBusǁ__init____mutmut_3 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ__init____mutmut['xǁObservabilityBusǁ__init____mutmut_4'] = ObservabilityBus.xǁObservabilityBusǁ__init____mutmut_4 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ__init____mutmut['xǁObservabilityBusǁ__init____mutmut_5'] = ObservabilityBus.xǁObservabilityBusǁ__init____mutmut_5 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ__init____mutmut['xǁObservabilityBusǁ__init____mutmut_6'] = ObservabilityBus.xǁObservabilityBusǁ__init____mutmut_6 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ__init____mutmut['xǁObservabilityBusǁ__init____mutmut_7'] = ObservabilityBus.xǁObservabilityBusǁ__init____mutmut_7 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ__init____mutmut['xǁObservabilityBusǁ__init____mutmut_8'] = ObservabilityBus.xǁObservabilityBusǁ__init____mutmut_8 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ__init____mutmut['xǁObservabilityBusǁ__init____mutmut_9'] = ObservabilityBus.xǁObservabilityBusǁ__init____mutmut_9 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ__init____mutmut['xǁObservabilityBusǁ__init____mutmut_10'] = ObservabilityBus.xǁObservabilityBusǁ__init____mutmut_10 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ__init____mutmut['xǁObservabilityBusǁ__init____mutmut_11'] = ObservabilityBus.xǁObservabilityBusǁ__init____mutmut_11 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ__init____mutmut['xǁObservabilityBusǁ__init____mutmut_12'] = ObservabilityBus.xǁObservabilityBusǁ__init____mutmut_12 # type: ignore # mutmut generated

mutants_xǁObservabilityBusǁsubscribe__mutmut['_mutmut_orig'] = ObservabilityBus.xǁObservabilityBusǁsubscribe__mutmut_orig # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁsubscribe__mutmut['xǁObservabilityBusǁsubscribe__mutmut_1'] = ObservabilityBus.xǁObservabilityBusǁsubscribe__mutmut_1 # type: ignore # mutmut generated

mutants_xǁObservabilityBusǁrecord_event__mutmut['_mutmut_orig'] = ObservabilityBus.xǁObservabilityBusǁrecord_event__mutmut_orig # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁrecord_event__mutmut['xǁObservabilityBusǁrecord_event__mutmut_1'] = ObservabilityBus.xǁObservabilityBusǁrecord_event__mutmut_1 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁrecord_event__mutmut['xǁObservabilityBusǁrecord_event__mutmut_2'] = ObservabilityBus.xǁObservabilityBusǁrecord_event__mutmut_2 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁrecord_event__mutmut['xǁObservabilityBusǁrecord_event__mutmut_3'] = ObservabilityBus.xǁObservabilityBusǁrecord_event__mutmut_3 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁrecord_event__mutmut['xǁObservabilityBusǁrecord_event__mutmut_4'] = ObservabilityBus.xǁObservabilityBusǁrecord_event__mutmut_4 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁrecord_event__mutmut['xǁObservabilityBusǁrecord_event__mutmut_5'] = ObservabilityBus.xǁObservabilityBusǁrecord_event__mutmut_5 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁrecord_event__mutmut['xǁObservabilityBusǁrecord_event__mutmut_6'] = ObservabilityBus.xǁObservabilityBusǁrecord_event__mutmut_6 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁrecord_event__mutmut['xǁObservabilityBusǁrecord_event__mutmut_7'] = ObservabilityBus.xǁObservabilityBusǁrecord_event__mutmut_7 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁrecord_event__mutmut['xǁObservabilityBusǁrecord_event__mutmut_8'] = ObservabilityBus.xǁObservabilityBusǁrecord_event__mutmut_8 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁrecord_event__mutmut['xǁObservabilityBusǁrecord_event__mutmut_9'] = ObservabilityBus.xǁObservabilityBusǁrecord_event__mutmut_9 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁrecord_event__mutmut['xǁObservabilityBusǁrecord_event__mutmut_10'] = ObservabilityBus.xǁObservabilityBusǁrecord_event__mutmut_10 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁrecord_event__mutmut['xǁObservabilityBusǁrecord_event__mutmut_11'] = ObservabilityBus.xǁObservabilityBusǁrecord_event__mutmut_11 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁrecord_event__mutmut['xǁObservabilityBusǁrecord_event__mutmut_12'] = ObservabilityBus.xǁObservabilityBusǁrecord_event__mutmut_12 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁrecord_event__mutmut['xǁObservabilityBusǁrecord_event__mutmut_13'] = ObservabilityBus.xǁObservabilityBusǁrecord_event__mutmut_13 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁrecord_event__mutmut['xǁObservabilityBusǁrecord_event__mutmut_14'] = ObservabilityBus.xǁObservabilityBusǁrecord_event__mutmut_14 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁrecord_event__mutmut['xǁObservabilityBusǁrecord_event__mutmut_15'] = ObservabilityBus.xǁObservabilityBusǁrecord_event__mutmut_15 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁrecord_event__mutmut['xǁObservabilityBusǁrecord_event__mutmut_16'] = ObservabilityBus.xǁObservabilityBusǁrecord_event__mutmut_16 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁrecord_event__mutmut['xǁObservabilityBusǁrecord_event__mutmut_17'] = ObservabilityBus.xǁObservabilityBusǁrecord_event__mutmut_17 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁrecord_event__mutmut['xǁObservabilityBusǁrecord_event__mutmut_18'] = ObservabilityBus.xǁObservabilityBusǁrecord_event__mutmut_18 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁrecord_event__mutmut['xǁObservabilityBusǁrecord_event__mutmut_19'] = ObservabilityBus.xǁObservabilityBusǁrecord_event__mutmut_19 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁrecord_event__mutmut['xǁObservabilityBusǁrecord_event__mutmut_20'] = ObservabilityBus.xǁObservabilityBusǁrecord_event__mutmut_20 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁrecord_event__mutmut['xǁObservabilityBusǁrecord_event__mutmut_21'] = ObservabilityBus.xǁObservabilityBusǁrecord_event__mutmut_21 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁrecord_event__mutmut['xǁObservabilityBusǁrecord_event__mutmut_22'] = ObservabilityBus.xǁObservabilityBusǁrecord_event__mutmut_22 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁrecord_event__mutmut['xǁObservabilityBusǁrecord_event__mutmut_23'] = ObservabilityBus.xǁObservabilityBusǁrecord_event__mutmut_23 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁrecord_event__mutmut['xǁObservabilityBusǁrecord_event__mutmut_24'] = ObservabilityBus.xǁObservabilityBusǁrecord_event__mutmut_24 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁrecord_event__mutmut['xǁObservabilityBusǁrecord_event__mutmut_25'] = ObservabilityBus.xǁObservabilityBusǁrecord_event__mutmut_25 # type: ignore # mutmut generated

mutants_xǁObservabilityBusǁspan__mutmut['_mutmut_orig'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_orig # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_1'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_1 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_2'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_2 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_3'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_3 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_4'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_4 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_5'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_5 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_6'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_6 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_7'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_7 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_8'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_8 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_9'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_9 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_10'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_10 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_11'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_11 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_12'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_12 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_13'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_13 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_14'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_14 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_15'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_15 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_16'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_16 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_17'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_17 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_18'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_18 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_19'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_19 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_20'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_20 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_21'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_21 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_22'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_22 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_23'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_23 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_24'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_24 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_25'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_25 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_26'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_26 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_27'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_27 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_28'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_28 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_29'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_29 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_30'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_30 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_31'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_31 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_32'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_32 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_33'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_33 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_34'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_34 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_35'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_35 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_36'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_36 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_37'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_37 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_38'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_38 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_39'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_39 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_40'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_40 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_41'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_41 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_42'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_42 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_43'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_43 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_44'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_44 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_45'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_45 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_46'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_46 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁspan__mutmut['xǁObservabilityBusǁspan__mutmut_47'] = ObservabilityBus.xǁObservabilityBusǁspan__mutmut_47 # type: ignore # mutmut generated

mutants_xǁObservabilityBusǁ_end_span__mutmut['_mutmut_orig'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_orig # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_1'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_1 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_2'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_2 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_3'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_3 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_4'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_4 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_5'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_5 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_6'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_6 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_7'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_7 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_8'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_8 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_9'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_9 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_10'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_10 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_11'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_11 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_12'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_12 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_13'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_13 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_14'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_14 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_15'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_15 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_16'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_16 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_17'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_17 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_18'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_18 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_19'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_19 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_20'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_20 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_21'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_21 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_22'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_22 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_23'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_23 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_24'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_24 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_25'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_25 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_26'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_26 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_27'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_27 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_28'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_28 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_29'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_29 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_30'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_30 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_31'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_31 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_32'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_32 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_33'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_33 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_34'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_34 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁ_end_span__mutmut['xǁObservabilityBusǁ_end_span__mutmut_35'] = ObservabilityBus.xǁObservabilityBusǁ_end_span__mutmut_35 # type: ignore # mutmut generated

mutants_xǁObservabilityBusǁexport_metrics__mutmut['_mutmut_orig'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_orig # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_1'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_1 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_2'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_2 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_3'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_3 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_4'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_4 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_5'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_5 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_6'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_6 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_7'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_7 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_8'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_8 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_9'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_9 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_10'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_10 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_11'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_11 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_12'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_12 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_13'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_13 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_14'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_14 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_15'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_15 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_16'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_16 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_17'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_17 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_18'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_18 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_19'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_19 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_20'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_20 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_21'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_21 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_22'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_22 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_23'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_23 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_24'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_24 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_25'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_25 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_26'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_26 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_27'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_27 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_28'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_28 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_29'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_29 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_30'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_30 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_31'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_31 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_32'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_32 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_33'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_33 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_34'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_34 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_35'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_35 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_36'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_36 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_37'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_37 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_38'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_38 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_39'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_39 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_40'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_40 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_41'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_41 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_42'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_42 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_43'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_43 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_44'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_44 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_45'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_45 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_46'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_46 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_47'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_47 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_48'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_48 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_49'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_49 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_50'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_50 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_51'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_51 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_52'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_52 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_53'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_53 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_54'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_54 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_55'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_55 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_56'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_56 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_57'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_57 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_58'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_58 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_59'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_59 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_60'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_60 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_61'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_61 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_62'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_62 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_63'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_63 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_64'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_64 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_65'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_65 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_66'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_66 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_67'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_67 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_68'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_68 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_69'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_69 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_70'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_70 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_71'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_71 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_72'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_72 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_73'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_73 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_74'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_74 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_75'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_75 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_76'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_76 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_77'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_77 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_78'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_78 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_79'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_79 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_80'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_80 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_81'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_81 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_82'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_82 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_83'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_83 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_84'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_84 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_85'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_85 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_86'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_86 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_87'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_87 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_88'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_88 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_89'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_89 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_90'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_90 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_91'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_91 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_92'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_92 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_93'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_93 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_94'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_94 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_95'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_95 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_96'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_96 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_97'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_97 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_98'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_98 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_99'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_99 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_100'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_100 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_101'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_101 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_102'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_102 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_103'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_103 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_104'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_104 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_105'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_105 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_106'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_106 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_107'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_107 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_108'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_108 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_109'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_109 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_110'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_110 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_111'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_111 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_112'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_112 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_113'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_113 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_114'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_114 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_115'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_115 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_116'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_116 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_117'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_117 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_118'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_118 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_119'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_119 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_120'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_120 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_121'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_121 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_122'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_122 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_123'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_123 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_124'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_124 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_125'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_125 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_126'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_126 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_127'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_127 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_128'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_128 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_129'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_129 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_130'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_130 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_131'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_131 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_132'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_132 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_133'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_133 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_metrics__mutmut['xǁObservabilityBusǁexport_metrics__mutmut_134'] = ObservabilityBus.xǁObservabilityBusǁexport_metrics__mutmut_134 # type: ignore # mutmut generated

mutants_xǁObservabilityBusǁexport_jsonl__mutmut['_mutmut_orig'] = ObservabilityBus.xǁObservabilityBusǁexport_jsonl__mutmut_orig # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_jsonl__mutmut['xǁObservabilityBusǁexport_jsonl__mutmut_1'] = ObservabilityBus.xǁObservabilityBusǁexport_jsonl__mutmut_1 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_jsonl__mutmut['xǁObservabilityBusǁexport_jsonl__mutmut_2'] = ObservabilityBus.xǁObservabilityBusǁexport_jsonl__mutmut_2 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_jsonl__mutmut['xǁObservabilityBusǁexport_jsonl__mutmut_3'] = ObservabilityBus.xǁObservabilityBusǁexport_jsonl__mutmut_3 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_jsonl__mutmut['xǁObservabilityBusǁexport_jsonl__mutmut_4'] = ObservabilityBus.xǁObservabilityBusǁexport_jsonl__mutmut_4 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_jsonl__mutmut['xǁObservabilityBusǁexport_jsonl__mutmut_5'] = ObservabilityBus.xǁObservabilityBusǁexport_jsonl__mutmut_5 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_jsonl__mutmut['xǁObservabilityBusǁexport_jsonl__mutmut_6'] = ObservabilityBus.xǁObservabilityBusǁexport_jsonl__mutmut_6 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_jsonl__mutmut['xǁObservabilityBusǁexport_jsonl__mutmut_7'] = ObservabilityBus.xǁObservabilityBusǁexport_jsonl__mutmut_7 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_jsonl__mutmut['xǁObservabilityBusǁexport_jsonl__mutmut_8'] = ObservabilityBus.xǁObservabilityBusǁexport_jsonl__mutmut_8 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_jsonl__mutmut['xǁObservabilityBusǁexport_jsonl__mutmut_9'] = ObservabilityBus.xǁObservabilityBusǁexport_jsonl__mutmut_9 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_jsonl__mutmut['xǁObservabilityBusǁexport_jsonl__mutmut_10'] = ObservabilityBus.xǁObservabilityBusǁexport_jsonl__mutmut_10 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_jsonl__mutmut['xǁObservabilityBusǁexport_jsonl__mutmut_11'] = ObservabilityBus.xǁObservabilityBusǁexport_jsonl__mutmut_11 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_jsonl__mutmut['xǁObservabilityBusǁexport_jsonl__mutmut_12'] = ObservabilityBus.xǁObservabilityBusǁexport_jsonl__mutmut_12 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_jsonl__mutmut['xǁObservabilityBusǁexport_jsonl__mutmut_13'] = ObservabilityBus.xǁObservabilityBusǁexport_jsonl__mutmut_13 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_jsonl__mutmut['xǁObservabilityBusǁexport_jsonl__mutmut_14'] = ObservabilityBus.xǁObservabilityBusǁexport_jsonl__mutmut_14 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_jsonl__mutmut['xǁObservabilityBusǁexport_jsonl__mutmut_15'] = ObservabilityBus.xǁObservabilityBusǁexport_jsonl__mutmut_15 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_jsonl__mutmut['xǁObservabilityBusǁexport_jsonl__mutmut_16'] = ObservabilityBus.xǁObservabilityBusǁexport_jsonl__mutmut_16 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_jsonl__mutmut['xǁObservabilityBusǁexport_jsonl__mutmut_17'] = ObservabilityBus.xǁObservabilityBusǁexport_jsonl__mutmut_17 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_jsonl__mutmut['xǁObservabilityBusǁexport_jsonl__mutmut_18'] = ObservabilityBus.xǁObservabilityBusǁexport_jsonl__mutmut_18 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_jsonl__mutmut['xǁObservabilityBusǁexport_jsonl__mutmut_19'] = ObservabilityBus.xǁObservabilityBusǁexport_jsonl__mutmut_19 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_jsonl__mutmut['xǁObservabilityBusǁexport_jsonl__mutmut_20'] = ObservabilityBus.xǁObservabilityBusǁexport_jsonl__mutmut_20 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_jsonl__mutmut['xǁObservabilityBusǁexport_jsonl__mutmut_21'] = ObservabilityBus.xǁObservabilityBusǁexport_jsonl__mutmut_21 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_jsonl__mutmut['xǁObservabilityBusǁexport_jsonl__mutmut_22'] = ObservabilityBus.xǁObservabilityBusǁexport_jsonl__mutmut_22 # type: ignore # mutmut generated

mutants_xǁObservabilityBusǁexport_span_tree__mutmut['_mutmut_orig'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_orig # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_1'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_1 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_2'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_2 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_3'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_3 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_4'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_4 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_5'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_5 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_6'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_6 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_7'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_7 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_8'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_8 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_9'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_9 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_10'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_10 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_11'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_11 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_12'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_12 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_13'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_13 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_14'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_14 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_15'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_15 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_16'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_16 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_17'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_17 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_18'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_18 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_19'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_19 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_20'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_20 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_21'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_21 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_22'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_22 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_23'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_23 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_24'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_24 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_25'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_25 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_26'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_26 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_27'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_27 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_28'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_28 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_29'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_29 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_30'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_30 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_31'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_31 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_32'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_32 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_33'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_33 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_34'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_34 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_35'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_35 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_36'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_36 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_37'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_37 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_38'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_38 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_39'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_39 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_40'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_40 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_41'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_41 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_42'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_42 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_43'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_43 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_44'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_44 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_45'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_45 # type: ignore # mutmut generated
mutants_xǁObservabilityBusǁexport_span_tree__mutmut['xǁObservabilityBusǁexport_span_tree__mutmut_46'] = ObservabilityBus.xǁObservabilityBusǁexport_span_tree__mutmut_46 # type: ignore # mutmut generated
mutants_xǁ_SpanCtxǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁ_SpanCtxǁ__exit____mutmut: MutantDict = {}  # type: ignore


class _SpanCtx:
    """span 上下文管理器。"""

    @_mutmut_mutated(mutants_xǁ_SpanCtxǁ__init____mutmut)
    def __init__(self, bus: ObservabilityBus, span_id: str):
        self._bus = bus
        self._span_id = span_id

    def xǁ_SpanCtxǁ__init____mutmut_orig(self, bus: ObservabilityBus, span_id: str):
        self._bus = bus
        self._span_id = span_id

    def xǁ_SpanCtxǁ__init____mutmut_1(self, bus: ObservabilityBus, span_id: str):
        self._bus = None
        self._span_id = span_id

    def xǁ_SpanCtxǁ__init____mutmut_2(self, bus: ObservabilityBus, span_id: str):
        self._bus = bus
        self._span_id = None

    def __enter__(self):
        return self

    @_mutmut_mutated(mutants_xǁ_SpanCtxǁ__exit____mutmut)
    def __exit__(self, exc_type, exc_val, exc_tb):
        status = "error" if exc_type is not None else "ok"
        self._bus._end_span(self._span_id, status)
        return False  # 不吞异常

    def xǁ_SpanCtxǁ__exit____mutmut_orig(self, exc_type, exc_val, exc_tb):
        status = "error" if exc_type is not None else "ok"
        self._bus._end_span(self._span_id, status)
        return False  # 不吞异常

    def xǁ_SpanCtxǁ__exit____mutmut_1(self, exc_type, exc_val, exc_tb):
        status = None
        self._bus._end_span(self._span_id, status)
        return False  # 不吞异常

    def xǁ_SpanCtxǁ__exit____mutmut_2(self, exc_type, exc_val, exc_tb):
        status = "error" if (exc_type is not None) and False else "ok"
        self._bus._end_span(self._span_id, status)
        return False  # 不吞异常

    def xǁ_SpanCtxǁ__exit____mutmut_3(self, exc_type, exc_val, exc_tb):
        status = "error" if (exc_type is not None) or True else "ok"
        self._bus._end_span(self._span_id, status)
        return False  # 不吞异常

    def xǁ_SpanCtxǁ__exit____mutmut_4(self, exc_type, exc_val, exc_tb):
        status = "XXerrorXX" if exc_type is not None else "ok"
        self._bus._end_span(self._span_id, status)
        return False  # 不吞异常

    def xǁ_SpanCtxǁ__exit____mutmut_5(self, exc_type, exc_val, exc_tb):
        status = "ERROR" if exc_type is not None else "ok"
        self._bus._end_span(self._span_id, status)
        return False  # 不吞异常

    def xǁ_SpanCtxǁ__exit____mutmut_6(self, exc_type, exc_val, exc_tb):
        status = "error" if exc_type is None else "ok"
        self._bus._end_span(self._span_id, status)
        return False  # 不吞异常

    def xǁ_SpanCtxǁ__exit____mutmut_7(self, exc_type, exc_val, exc_tb):
        status = "error" if exc_type is not None else "XXokXX"
        self._bus._end_span(self._span_id, status)
        return False  # 不吞异常

    def xǁ_SpanCtxǁ__exit____mutmut_8(self, exc_type, exc_val, exc_tb):
        status = "error" if exc_type is not None else "OK"
        self._bus._end_span(self._span_id, status)
        return False  # 不吞异常

    def xǁ_SpanCtxǁ__exit____mutmut_9(self, exc_type, exc_val, exc_tb):
        status = "error" if exc_type is not None else "ok"
        self._bus._end_span(None, status)
        return False  # 不吞异常

    def xǁ_SpanCtxǁ__exit____mutmut_10(self, exc_type, exc_val, exc_tb):
        status = "error" if exc_type is not None else "ok"
        self._bus._end_span(self._span_id, None)
        return False  # 不吞异常

    def xǁ_SpanCtxǁ__exit____mutmut_11(self, exc_type, exc_val, exc_tb):
        status = "error" if exc_type is not None else "ok"
        self._bus._end_span(status)
        return False  # 不吞异常

    def xǁ_SpanCtxǁ__exit____mutmut_12(self, exc_type, exc_val, exc_tb):
        status = "error" if exc_type is not None else "ok"
        self._bus._end_span(self._span_id, )
        return False  # 不吞异常

    def xǁ_SpanCtxǁ__exit____mutmut_13(self, exc_type, exc_val, exc_tb):
        status = "error" if exc_type is not None else "ok"
        self._bus._end_span(self._span_id, status)
        return True  # 不吞异常

mutants_xǁ_SpanCtxǁ__init____mutmut['_mutmut_orig'] = _SpanCtx.xǁ_SpanCtxǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁ_SpanCtxǁ__init____mutmut['xǁ_SpanCtxǁ__init____mutmut_1'] = _SpanCtx.xǁ_SpanCtxǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁ_SpanCtxǁ__init____mutmut['xǁ_SpanCtxǁ__init____mutmut_2'] = _SpanCtx.xǁ_SpanCtxǁ__init____mutmut_2 # type: ignore # mutmut generated

mutants_xǁ_SpanCtxǁ__exit____mutmut['_mutmut_orig'] = _SpanCtx.xǁ_SpanCtxǁ__exit____mutmut_orig # type: ignore # mutmut generated
mutants_xǁ_SpanCtxǁ__exit____mutmut['xǁ_SpanCtxǁ__exit____mutmut_1'] = _SpanCtx.xǁ_SpanCtxǁ__exit____mutmut_1 # type: ignore # mutmut generated
mutants_xǁ_SpanCtxǁ__exit____mutmut['xǁ_SpanCtxǁ__exit____mutmut_2'] = _SpanCtx.xǁ_SpanCtxǁ__exit____mutmut_2 # type: ignore # mutmut generated
mutants_xǁ_SpanCtxǁ__exit____mutmut['xǁ_SpanCtxǁ__exit____mutmut_3'] = _SpanCtx.xǁ_SpanCtxǁ__exit____mutmut_3 # type: ignore # mutmut generated
mutants_xǁ_SpanCtxǁ__exit____mutmut['xǁ_SpanCtxǁ__exit____mutmut_4'] = _SpanCtx.xǁ_SpanCtxǁ__exit____mutmut_4 # type: ignore # mutmut generated
mutants_xǁ_SpanCtxǁ__exit____mutmut['xǁ_SpanCtxǁ__exit____mutmut_5'] = _SpanCtx.xǁ_SpanCtxǁ__exit____mutmut_5 # type: ignore # mutmut generated
mutants_xǁ_SpanCtxǁ__exit____mutmut['xǁ_SpanCtxǁ__exit____mutmut_6'] = _SpanCtx.xǁ_SpanCtxǁ__exit____mutmut_6 # type: ignore # mutmut generated
mutants_xǁ_SpanCtxǁ__exit____mutmut['xǁ_SpanCtxǁ__exit____mutmut_7'] = _SpanCtx.xǁ_SpanCtxǁ__exit____mutmut_7 # type: ignore # mutmut generated
mutants_xǁ_SpanCtxǁ__exit____mutmut['xǁ_SpanCtxǁ__exit____mutmut_8'] = _SpanCtx.xǁ_SpanCtxǁ__exit____mutmut_8 # type: ignore # mutmut generated
mutants_xǁ_SpanCtxǁ__exit____mutmut['xǁ_SpanCtxǁ__exit____mutmut_9'] = _SpanCtx.xǁ_SpanCtxǁ__exit____mutmut_9 # type: ignore # mutmut generated
mutants_xǁ_SpanCtxǁ__exit____mutmut['xǁ_SpanCtxǁ__exit____mutmut_10'] = _SpanCtx.xǁ_SpanCtxǁ__exit____mutmut_10 # type: ignore # mutmut generated
mutants_xǁ_SpanCtxǁ__exit____mutmut['xǁ_SpanCtxǁ__exit____mutmut_11'] = _SpanCtx.xǁ_SpanCtxǁ__exit____mutmut_11 # type: ignore # mutmut generated
mutants_xǁ_SpanCtxǁ__exit____mutmut['xǁ_SpanCtxǁ__exit____mutmut_12'] = _SpanCtx.xǁ_SpanCtxǁ__exit____mutmut_12 # type: ignore # mutmut generated
mutants_xǁ_SpanCtxǁ__exit____mutmut['xǁ_SpanCtxǁ__exit____mutmut_13'] = _SpanCtx.xǁ_SpanCtxǁ__exit____mutmut_13 # type: ignore # mutmut generated
