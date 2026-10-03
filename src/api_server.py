#!/usr/bin/env python3
"""UHES API 服务（第11项优化：流水线 HTTP 服务化）。

设计原则（顶尖工程实践）：
- 纯标准库 http.server（零第三方依赖，与项目一致）。
- 异步任务：POST 提交 → 后台线程执行 → GET 轮询/取包（不阻塞请求）。
- REST 语义：
    POST /jobs           提交需求 {case | raw, context} → {job_id, status}
    GET  /jobs/{job_id}  轮询状态 {job_id, status, final_verdict}
    GET  /jobs/{job_id}/package  取交付包 {package: {...}}
- 状态机在后台线程运行，交付包存内存（概念层）。

使用：
    from api_server import UHESApiServer
    server = UHESApiServer(port=8765)
    server.start()          # 后台启动
    # 客户端: POST /jobs → GET /jobs/{id} → GET /jobs/{id}/package
"""

from __future__ import annotations

import json
import os
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

# 状态常量
ST_QUEUED = "queued"
ST_RUNNING = "running"
ST_COMPLETED = "completed"
ST_FAILED = "failed"


class UHESApiServer:
    """HTTP API 服务（异步任务 + 状态轮询 + 交付包获取）。

    第17项优化（工程加固）：
      - 任务上限 MAX_JOBS（防无界提交）；
      - 并发限制 MAX_CONCURRENT（Semaphore 控并发执行线程）；
      - 任务超时 JOB_TIMEOUT（超时标记 failed，不悬挂）。
    """

    # 工程加固参数
    MAX_JOBS = 200            # 任务上限（防无界）
    MAX_CONCURRENT = 4        # 最大并发执行
    JOB_TIMEOUT = 600         # 单任务超时（秒）

    def __init__(self, port: int = 8765, host: str = "127.0.0.1"):
        self.port = port
        self.host = host
        self._jobs: dict[str, dict[str, Any]] = {}  # job_id -> job
        self._lock = threading.Lock()
        self._sem = threading.Semaphore(self.MAX_CONCURRENT)
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    # ---- 任务管理 ----
    def submit(self, case: str = "lit_review",
               raw: str | None = None,
               context: dict[str, Any] | None = None,
               iteration_of: str | None = None) -> dict[str, Any]:
        """提交一个流水线任务，返回 job_id + 初始状态。

        第12项优化：iteration_of 非空时 = 进化任务（进化闭环真实执行）。
        """
        job_id = uuid.uuid4().hex[:12]
        job = {
            "job_id": job_id,
            "status": ST_QUEUED,
            "case": case,
            "raw": raw,
            "context": context or {},
            "iteration_of": iteration_of,
            "package": None,
            "error": None,
        }
        with self._lock:
            # 第17项优化：任务上限（防无界提交）
            if len(self._jobs) >= self.MAX_JOBS:
                return {"job_id": None, "status": "rejected",
                        "error": f"任务队列已满(>{self.MAX_JOBS})"}
            self._jobs[job_id] = job
        # 后台执行（不阻塞提交，并发信号量限制）
        threading.Thread(target=self._run_job, args=(job_id,),
                         daemon=True).start()
        return {"job_id": job_id, "status": ST_QUEUED}

    def _run_job(self, job_id: str) -> None:
        """后台执行流水线（设计师 Agent 运行 + 交付包产出）。

        第17项优化：并发信号量限制 + 任务超时保护。
        """
        acquired = self._sem.acquire(timeout=5)
        if not acquired:
            with self._lock:
                self._jobs[job_id]["status"] = ST_FAILED
                self._jobs[job_id]["error"] = "并发繁忙,获取执行许可超时"
            return
        try:
            self._execute_job(job_id)
        finally:
            self._sem.release()

    def _execute_job(self, job_id: str) -> None:
        """执行流水线（超时保护）。"""
        import threading as _th
        result_holder: dict[str, Any] = {}
        worker = _th.Thread(target=self._run_job_worker,
                            args=(job_id, result_holder), daemon=True)
        worker.start()
        worker.join(timeout=self.JOB_TIMEOUT)
        if worker.is_alive():
            with self._lock:
                self._jobs[job_id]["status"] = ST_FAILED
                self._jobs[job_id]["error"] = f"任务超时(>{self.JOB_TIMEOUT}s)"

    def _run_job_worker(self, job_id: str, result_holder: dict[str, Any]) -> None:
        """实际流水线执行（超时保护的 worker）。"""
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import main as m
        # 无 ZHIPU_API_KEY 时注入 LLM mock（离线也能真实解析自定义需求）
        if not os.environ.get("ZHIPU_API_KEY"):
            try:
                import test_suite as _ts
                _mock = _ts.LLMMock()
                _mock.install(m)
            except Exception:
                pass
        job = self._jobs[job_id]
        with self._lock:
            job["status"] = ST_RUNNING
        try:
            # 第12项优化：进化任务（进化闭环真实执行）
            if job.get("iteration_of"):
                import evolution as _ev
                engine = _ev.EvolutionEngine(
                    db_path=os.environ.get("UHES_MATRIX_DB") or None)
                result = engine.evolve(
                    job["iteration_of"],
                    rounds=job.get("context", {}).get("rounds", 2),
                    use_mock=not os.environ.get("ZHIPU_API_KEY"))
                with self._lock:
                    job["package"] = {"evolution": result}
                    job["status"] = ST_COMPLETED
                return
            case_inputs = {
                "lit_review": m.demo_input,
                "analytics": m.demo_input_analytics,
                "knowledge": m.demo_input_knowledge,
            }
            if job["raw"]:
                # 自定义需求：构造输入
                inp = {"raw_requirement": job["raw"],
                       "context": job["context"] or {}}
            else:
                inp = case_inputs[job["case"]]()
            pipeline = m.build_pipeline(run_id=f"api_{job_id}")
            pkg = pipeline.run(inp)
            with self._lock:
                job["package"] = pkg.to_dict()
                job["status"] = ST_COMPLETED
        except Exception as exc:
            with self._lock:
                job["error"] = str(exc)
                job["status"] = ST_FAILED

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        """查询任务状态（不含完整包）。"""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            return {
                "job_id": job["job_id"],
                "status": job["status"],
                "case": job["case"],
                "iteration_of": job.get("iteration_of"),
                "final_verdict": (job.get("package", {}) or {}).get(
                    "integrity", {}).get("verdict") if job["status"] == ST_COMPLETED else None,
                "evolution_status": (job.get("package", {}) or {}).get(
                    "evolution", {}).get("final_status") if job["status"] == ST_COMPLETED else None,
                "error": job["error"],
            }

    def get_package(self, job_id: str) -> dict[str, Any] | None:
        """取交付包（仅 completed 时返回）。"""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or job["status"] != ST_COMPLETED or job["package"] is None:
                return None
            return {"job_id": job_id, "package": job["package"]}

    # ---- HTTP 服务 ----
    def start(self) -> None:
        """后台启动 HTTP 服务。"""
        handler = self._make_handler()
        self._httpd = ThreadingHTTPServer((self.host, self.port), handler)
        self._httpd.server = self  # 注入 server 引用
        self._thread = threading.Thread(target=self._httpd.serve_forever,
                                        daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """停止服务。"""
        if self._httpd:
            self._httpd.shutdown()

    def _make_handler(self):
        server_ref = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):
                pass  # 静默（避免刷屏）

            def _check_auth(self) -> bool:
                """鉴权校验：若配置了 UHES_API_KEY 则要求 X-API-Key 匹配。

                未配置 key = 本地开发模式，放行（兼容现有行为）。
                配置 key = 必须带正确 X-API-Key，否则 401。
                """
                expected = os.environ.get("UHES_API_KEY", "").strip()
                if not expected:
                    return True  # 未启用鉴权（本地模式）
                provided = self.headers.get("X-API-Key", "")
                return provided == expected

            def _send(self, code: int, obj: dict[str, Any]) -> None:
                body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                if not self._check_auth():
                    self._send(401, {"error": "unauthorized", "hint": "需 X-API-Key 请求头（配置 UHES_API_KEY 后生效）"})
                    return
                if self.path != "/jobs":
                    self._send(404, {"error": "not_found"})
                    return
                try:
                    length = int(self.headers.get("Content-Length", 0))
                    body = json.loads(self.rfile.read(length).decode("utf-8"))
                except Exception:
                    self._send(400, {"error": "bad_request"})
                    return
                case = body.get("case", "lit_review")
                if case not in ("lit_review", "analytics", "knowledge") and not body.get("raw") and not body.get("iteration_of"):
                    self._send(400, {"error": "unsupported_case", "case": case})
                    return
                result = server_ref.submit(
                    case=case, raw=body.get("raw"), context=body.get("context"),
                    iteration_of=body.get("iteration_of"))
                self._send(202, result)

            def do_GET(self):
                if not self._check_auth():
                    self._send(401, {"error": "unauthorized", "hint": "需 X-API-Key 请求头（配置 UHES_API_KEY 后生效）"})
                    return
                # /jobs/{id} 或 /jobs/{id}/package
                parts = self.path.strip("/").split("/")
                if len(parts) == 2 and parts[0] == "jobs":
                    job = server_ref.get_job(parts[1])
                    if job is None:
                        self._send(404, {"error": "job_not_found"})
                        return
                    self._send(200, job)
                    return
                if len(parts) == 3 and parts[0] == "jobs" and parts[2] == "package":
                    pkg = server_ref.get_package(parts[1])
                    if pkg is None:
                        self._send(404, {"error": "package_not_ready"})
                        return
                    self._send(200, pkg)
                    return
                self._send(404, {"error": "not_found"})

        return Handler


def run_server(port: int = 8765, host: str = "127.0.0.1") -> UHESApiServer:
    """启动 API 服务（阻塞主线程，Ctrl-C 停止）。"""
    server = UHESApiServer(port=port, host=host)
    server.start()
    print(f"[UHES-API] 服务已启动: http://{host}:{port}/jobs")
    print("[UHES-API] POST /jobs 提交 | GET /jobs/{id} 轮询 | "
          "GET /jobs/{id}/package 取包")
    try:
        while True:
            import time
            time.sleep(3600)
    except KeyboardInterrupt:
        server.stop()
    return server


if __name__ == "__main__":
    run_server(port=int(sys.argv[1]) if len(sys.argv) > 1 else 8765)
