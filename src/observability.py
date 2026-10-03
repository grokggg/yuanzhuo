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


class ObservabilityBus:
    """结构化事件总线（span 生命周期 + 指标聚合 + 事件订阅 + 导出）。"""

    def __init__(self, run_id: str = ""):
        self.run_id = run_id or "run_unknown"
        self._events: list[dict[str, Any]] = []
        self._spans: list[dict[str, Any]] = []
        self._span_stack: list[str] = []  # 当前 span id 栈（支持嵌套）
        self._observers: list[Callable[[str, dict[str, Any]], None]] = []
        self._started_at = time.time()
        self._span_seq = 0

    # ---- 订阅 ----
    def subscribe(self, observer: Callable[[str, dict[str, Any]], None]) -> None:
        """订阅事件（observer(event_type, payload)）。"""
        self._observers.append(observer)

    # ---- 事件 ----
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

    # ---- Span 生命周期（上下文管理器）----
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

    # ---- 指标聚合 ----
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

    # ---- 导出 ----
    def export_jsonl(self) -> str:
        """导出结构化事件流（JSON Lines，含 span 层级与耗时）。"""
        lines = [json.dumps(e, ensure_ascii=False) for e in self._events]
        lines.append(json.dumps({
            "event": "metrics_snapshot", "run_id": self.run_id,
            "metrics": self.export_metrics(),
        }, ensure_ascii=False))
        return "\n".join(lines)

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


class _SpanCtx:
    """span 上下文管理器。"""

    def __init__(self, bus: ObservabilityBus, span_id: str):
        self._bus = bus
        self._span_id = span_id

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        status = "error" if exc_type is not None else "ok"
        self._bus._end_span(self._span_id, status)
        return False  # 不吞异常
