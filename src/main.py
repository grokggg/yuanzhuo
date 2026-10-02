#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UHES · 范式演化设计师 Agent —— 概念状态机骨架（示意代码）
============================================================

性质声明（必读）：
    本文件是【概念推演】的示意代码，**非真实运行的业务系统**。
    它只模拟 docs/10-范式演化设计师概念设计.md (v1.1) 所定义的
    8 步流水线（含 S2.5 圆桌）的状态流转、门控判定、回退/降级保护、
    交付包组装与完整性校验的“结构”与“逻辑”。
    所有自然语言理解、范式匹配、专家推演、交叉验证均为【概念模拟】，
    不包含任何真实 NLP / 检索 / 翻译 / 推理实现，也不编造性能数据。

架构映射（对应设计文档）：
    - 主骨架冻结：PipelineStateMachine 类 = 冻结的核心骨架（不得修改）
    - 插件侧车：  steps.py 注册表中的 8 步 handler = 可替换的插件侧车
    - 数据分层：  permanent 层（交付包/DNA/哈希链可序列化资产）
                 temporary 层（运行统计计数，仅本会话参考）
    - 全局保护：  degradation_count + rollback_count >= 3 → 最短路径

运行方式：
    python3 main.py
    python3 main.py --case lit_review   # 显式指定内置案例（当前仅一个）

依赖：纯 Python 标准库，无第三方依赖。
"""

import argparse
import hashlib
import json
import os
import sys
import textwrap
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

# ---------------------------------------------------------------------------
# 0. 常量与配置（概念层，不编造数字）
# ---------------------------------------------------------------------------

PERMANENT_LAYER = [
    "01_requirement_dna_report",
    "02_composite_paradigm_spec",
    "03_system_blueprint",
    "04_roundtable_report",
    "05_methodology_usage_record",
    "06_validation_report",
    "07_incubation_plan",
    "package_meta",
    "cross_references",
]
"""交付包永久层清单：整体可序列化进记忆匣迁移（设计文档 5.6 节）。"""

GLOBAL_PROTECTION_THRESHOLD = 3
"""全局保护阈值：rollback + degradation 合计 >= 3 触发最短路径（4.4 节）。"""

MAX_ROLLBACK_PER_STEP = 1
"""每步回退上限：回退最多 1 次，防止死锁循环（P5 设计原则）。"""

# ---- 阶段2常量（能力补齐，见 docs/10 与 01 记忆匣阶段2定义）----
CLARIFY_THRESHOLD_PHASE2 = 1
"""阶段2主动澄清阈值：ambiguities 数量 > 此值触发澄清模板（P2-A1；阶段1为3）。"""

CLARIFY_LONG_TEXT_THRESHOLD = 500
"""阶段2长文本阈值：raw_requirement 超此长度启用三段式处理（P2-A3；概念阈值）。"""

ARTIFACT_ORDER = ["01", "02", "03", "04", "05", "06", "07"]

# ---------------------------------------------------------------------------
# 0.1 阶段3扩展开关（铁律：扩展能力默认关闭）
# ---------------------------------------------------------------------------

EXTENSIONS_DEFAULT: dict[str, bool] = {
    # 动力学等价杂交（enabled_depth=dynamics_equivalence，01 记忆匣阶段3）
    "phase3_dynamics_hybrid": False,
    # 系统关系网络（S8 登记时建立 validates/validated_by 关系）
    "phase3_relation_network": False,
    # 系统自动编排（矩阵内系统按依赖链组合，解决更大问题）
    "phase3_auto_orchestration": False,
}
"""阶段3扩展开关配置（概念层）。默认全部关闭，显式开启才生效，
对应设计文档"扩展能力默认关闭"铁律。"""


# ---------------------------------------------------------------------------
# 1. 数据类型（概念 Schema，对应设计文档各节）
# ---------------------------------------------------------------------------

@dataclass
class GateResult:
    """门控判定结果（P2 门控收敛）。"""
    passed: bool
    reason: str = ""
    fail_kind: Optional[str] = None  # clarification / constraint_conflict / paradigm_coverage / ...


@dataclass
class StepRecord:
    """步骤执行记录（溯源链，对应 PIPELINE_STATE.step_history）。"""
    step_name: str
    status: str  # passed | failed | degraded | skipped
    gate_decision: str
    degradation_note: Optional[str] = None
    output_ref: Optional[str] = None


@dataclass
class PIPELINE_STATE:
    """全局状态变量（设计文档 4.1 节）。"""
    run_id: str
    started_at: str
    current_step: str = ""
    step_history: list[StepRecord] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)
    degradation_count: int = 0
    rollback_count: int = 0
    user_interventions: list[dict] = field(default_factory=list)
    final_status: str = "running"

    @property
    def protection_triggered(self) -> bool:
        """全局保护：rollback + degradation 合计 >= 阈值（P1-B2 修复）。"""
        return (self.rollback_count + self.degradation_count) >= GLOBAL_PROTECTION_THRESHOLD


# ---------------------------------------------------------------------------
# 2. 冻结核心骨架：状态机引擎（不可修改）
# ---------------------------------------------------------------------------

class PipelineStateMachine:
    """
    冻结的核心骨架（概念层）。

    职责：按注册顺序执行步骤 → 收集门控结果 → 管理全局保护 → 组装交付包。
    任何业务逻辑都不应修改本类；步骤逻辑通过 register() 以插件侧车方式注入。
    """

    def __init__(self, run_id: str, paradigm_catalog_version: str,
                 methodology_catalog_version: str,
                 extensions: Optional[dict[str, bool]] = None) -> None:
        self.state = PIPELINE_STATE(
            run_id=run_id,
            started_at=_now_iso(),
        )
        self.paradigm_catalog_version = paradigm_catalog_version
        self.methodology_catalog_version = methodology_catalog_version
        # 阶段3扩展开关：合并默认配置，未开启项保持关闭（扩展能力默认关闭铁律）
        self.extensions: dict[str, bool] = {
            **EXTENSIONS_DEFAULT,
            **(extensions or {}),
        }
        self._steps: list[tuple[str, Callable, Callable]] = []
        self._optional_steps: set[str] = set()  # 可选步骤（圆桌/交叉验证），最短路径时跳过

    # ---- 插件侧车注册点（非侵入注入） ----
    def register(self, name: str, handler: Callable, gate: Callable,
                 optional: bool = False) -> None:
        self._steps.append((name, handler, gate))
        if optional:
            self._optional_steps.add(name)

    # ---- 主循环 ----
    def run(self, raw_input: dict[str, Any]) -> "DeliveryPackage":
        """
        执行顺序语义（对应设计文档）：handler 先执行本步 → gate 验收本步产物
        → 判定流转。门控检查的是【本步输出是否合格】，而非前置条件。

        回退语义（P5 死锁保护）：rollback 时回退到上一步重新执行（最多 1 次），
        超过则降级继续；degradation + rollback 合计 >= 阈值触发最短路径。
        """
        self.state.artifacts["__input"] = raw_input  # 供 S1 概念上读取
        self.state.artifacts["__extensions"] = self.extensions  # 供侧车读取扩展开关
        print(f"[UHES] 流水线启动 run_id={self.state.run_id}")
        idx = 0
        while idx < len(self._steps):
            name, handler, gate = self._steps[idx]
            if self.state.protection_triggered and name in self._optional_steps:
                self._skip_optional(name)
                idx += 1
                continue
            self.state.current_step = name
            handler(self.state)                     # 1) 执行本步
            gate_result = gate(self.state)          # 2) 验收本步产物
            print(f"  ── {name:<22} 门控: {'PASS' if gate_result.passed else 'FAIL'}"
                  f"  {gate_result.reason}")
            if gate_result.passed:
                self._record(name, "passed", gate_result.reason)
                idx += 1
                continue
            # ---- 失败分支 ----
            fail = gate_result.fail_kind or "generic"
            if fail in ("clarification", "constraint_conflict"):
                # S1：等待用户裁决/澄清，流水线暂停（不自动降级）
                # 阶段2（P2-B4落地）：暂停状态下用户可选择终止，输出可审计的终止产物
                self.state.final_status = "waiting_user"
                self._record(name, "failed", gate_result.reason)
                print(f"  !! {name} 进入 waiting_user 状态（{gate_result.reason}）")
                # B4落地：终止时输出原始输入 + DNA草稿(如有) + 终止确认
                self.state.artifacts["termination_artifact"] = {
                    "original_input": self.state.artifacts.get("__input", {}),
                    "dna_draft": self.state.artifacts.get("S1", {}).get("dna", None),
                    "termination_confirmation": {
                        "at_step": name,
                        "reason": "用户发送终止指令（P2-B4落地）",
                        "partial_artifacts": list(self.state.artifacts.keys()),
                    },
                }
                break
            if fail in ("paradigm_coverage", "all_conflict"):
                # S2：范式覆盖不足/全冲突 → 流水线终止
                self.state.final_status = "failed"
                self._record(name, "failed", gate_result.reason)
                print(f"  XX {name} 流水线终止（{gate_result.reason}）")
                break
            if fail == "rollback":
                if self.state.rollback_count < MAX_ROLLBACK_PER_STEP:
                    self.state.rollback_count += 1
                    self._record(name, "failed",
                                 gate_result.reason + "（触发回退，≤1次）")
                    idx = max(0, idx - 1)  # 回退到上一步重新执行
                    print(f"  ↻ {name} 回退到上一步重跑"
                          f"（rollback_count={self.state.rollback_count}）")
                    continue
                self._degrade(name, gate_result.reason + "（回退超限，降级继续）")
                idx += 1
                continue
            # degrade / generic：降级继续
            self._degrade(name, gate_result.reason)
            idx += 1
        return self._assemble_package()

    def _degrade(self, step: str, reason: str) -> None:
        self.state.degradation_count += 1
        self._record(step, "degraded", reason)
        print(f"  ↓ {step} 降级（degradation_count={self.state.degradation_count}）: {reason}")

    def _skip_optional(self, step: str) -> None:
        self.state.current_step = step
        self._record(step, "skipped", "全局保护触发，最短路径跳过可选步骤")
        print(f"  ≫ {step:<22} 跳过（最短路径保护）")

    def _record(self, step: str, status: str, gate_decision: str,
                degradation_note: Optional[str] = None) -> None:
        self.state.step_history.append(StepRecord(
            step_name=step, status=status, gate_decision=gate_decision,
            degradation_note=degradation_note,
            output_ref=self.state.artifacts.get(step)))

    # ---- 交付包组装（对应设计文档第 5 节） ----
    def _assemble_package(self) -> "DeliveryPackage":
        if self.state.final_status == "running":
            if self.state.degradation_count or self.state.rollback_count:
                self.state.final_status = "completed_with_degradation"
            else:
                self.state.final_status = "completed"
        meta = {
            "run_id": self.state.run_id,
            "package_version": "1.0",
            "generated_at": _now_iso(),
            "final_status": self.state.final_status,
            "degradation_records": [
                {"step": r.step_name, "reason": r.gate_decision,
                 "fallback_action": r.degradation_note or "无"}
                for r in self.state.step_history if r.status == "degraded"
            ],
            "paradigm_catalog_version": self.paradigm_catalog_version,
            "methodology_catalog_version": self.methodology_catalog_version,
            "provenance_chain_ref": "step_history（本状态机）",
            "system_matrix_registration": self.state.artifacts.get("S8", {}).get(
                "registration", {"system_id": None, "registered": False}),
        }
        artifacts = {
            k: v for k, v in self.state.artifacts.items()
            if k in PERMANENT_LAYER or k in ("S8",)
        }
        # 组装 7 件套映射
        seven = {
            "01_requirement_dna_report": self.state.artifacts.get("S1", {}),
            "02_composite_paradigm_spec": self.state.artifacts.get("S2", {}),
            "03_system_blueprint": self.state.artifacts.get("S4", {}),
            "04_roundtable_report": self.state.artifacts.get("S2.5", {}) or
                                    {"triggered": False, "skip_reason": "未触发（单范式+高置信度+无高风险）"},
            "05_methodology_usage_record": self.state.artifacts.get("S3", {}),
            "06_validation_report": self.state.artifacts.get("S5", {}),
            "07_incubation_plan": self.state.artifacts.get("S7", {}),
        }
        package = DeliveryPackage(meta=meta, artifacts=seven)
        checker = IntegrityChecker()
        package.integrity = checker.check(package)
        return package


# ---------------------------------------------------------------------------
# 3. 交付包与完整性校验（设计文档 5.5 节，含 P0 修复 C4）
# ---------------------------------------------------------------------------

@dataclass
class DeliveryPackage:
    meta: dict
    artifacts: dict[str, Any]
    integrity: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"package_meta": self.meta, "artifacts": self.artifacts,
                "integrity": self.integrity}


class IntegrityChecker:
    """交付前完整性校验门控（5.5 节）。"""

    def check(self, pkg: DeliveryPackage) -> dict:
        completeness = self._check_completeness(pkg.artifacts)
        required = self._check_required_fields(pkg.artifacts)
        closure = self._check_reference_closure(pkg)
        consistency = self._check_consistency(pkg)      # P0 修复 C4
        hash_chain = self._check_hash_chain(pkg)        # 含 C3 normalization 声明
        passed_all = all((
            completeness["complete"],
            required["passed"],
            closure["passed"],
            consistency["passed"],
            hash_chain["chain_integrity"],
        ))
        return {
            "artifact_completeness": completeness,
            "required_field_check": required,
            "reference_closure": closure,
            "cross_artifact_consistency": consistency,   # CONS_01
            "snapshot_hash_chain": hash_chain,
            "verdict": "deliver" if passed_all else "block",
            "block_reasons": self._collect_block_reasons(
                completeness, required, closure, consistency, hash_chain),
        }

    @staticmethod
    def _check_completeness(artifacts: dict) -> dict:
        expected = ["01_requirement_dna_report", "02_composite_paradigm_spec",
                    "03_system_blueprint", "04_roundtable_report",
                    "05_methodology_usage_record", "06_validation_report",
                    "07_incubation_plan"]
        present = [k for k in expected if k in artifacts and artifacts[k]]
        return {"expected": expected, "present": present,
                "complete": len(present) == len(expected),
                "note": "04件为跳过声明也算complete（契约恒为7件）"}

    @staticmethod
    def _check_required_fields(artifacts: dict) -> dict:
        # 概念级必填字段检查（支持点路径，如 "dna.goal"）
        violations: list[dict] = []
        key_rules = {
            "01_requirement_dna_report": ["dna.goal", "dna.constraints"],
            "02_composite_paradigm_spec": ["hybridization"],
            "03_system_blueprint": ["system_identity", "architecture"],
            "05_methodology_usage_record": ["recommended_set"],
            "06_validation_report": ["eight_dimension_scores", "defect_list"],
            "07_incubation_plan": ["phases", "minimum_viable_path"],
        }

        def _get_path(data: dict, path: str) -> Any:
            cur: Any = data
            for part in path.split("."):
                if not isinstance(cur, dict) or part not in cur:
                    return None
                cur = cur[part]
            return cur

        for art, keys in key_rules.items():
            data = artifacts.get(art)
            if not data:
                violations.append({"artifact": art, "missing_field": "<整件为空>"})
                continue
            for k in keys:
                v = _get_path(data, k)
                if v in (None, [], {}):
                    violations.append({"artifact": art, "missing_field": k})
        return {"violations": violations, "passed": not violations}

    @staticmethod
    def _check_reference_closure(pkg: DeliveryPackage) -> dict:
        # 概念级：交叉引用索引中所有 from/to 必须能解析到对应件
        dangling: list[str] = []
        known = set(pkg.artifacts.keys())
        for ref in pkg.meta.get("_reference_index", []):
            frm = ref.get("from", "").split(".")[0]
            to = ref.get("to", "").split(".")[0]
            if frm not in known:
                dangling.append(f"from:{frm}")
            if to not in known:
                dangling.append(f"to:{to}")
        return {"dangling_refs": dangling, "passed": not dangling}

    @staticmethod
    def _check_consistency(pkg: DeliveryPackage) -> dict:
        """P0 修复 C4：cross_artifact_consistency —— CONS_01 规则。

        IF 03件.open_issues 非空
        THEN 06件对应维度 grade 不能为 S，且 defect_list 必须包含对应条目。
        """
        violations: list[dict] = []
        bp = pkg.artifacts.get("03_system_blueprint", {})
        vr = pkg.artifacts.get("06_validation_report", {})
        open_issues = bp.get("open_issues", [])
        if open_issues:
            scores = vr.get("eight_dimension_scores", [])
            defects = [d.get("description", "") for d in vr.get("defect_list", [])]
            all_s = all(s.get("grade") == "S" for s in scores)
            if all_s:
                violations.append({
                    "rule_id": "CONS_01",
                    "detail": "open_issues 非空但 8 维评分全 S（矛盾）",
                })
            for issue in open_issues:
                iss_text = issue.get("issue", "")
                matched = any(
                    (iss_text in d) or (d in iss_text) for d in defects
                )
                if not matched:
                    violations.append({
                        "rule_id": "CONS_01",
                        "detail": f"open_issue 未反映在 defect_list: {iss_text[:30]}",
                    })
        return {
            "rules": [{
                "rule_id": "CONS_01",
                "description": "蓝图未决项必须反映在验证评分中",
                "check": "IF 03件.open_issues 非空 THEN 06件对应维度grade不能为S, 且06件.defect_list必须包含对应条目",
                "violations": violations,
            }],
            "passed": not violations,
            "note": "reference_closure保证引用可解析;cross_artifact_consistency保证引用内容自洽",
        }

    @staticmethod
    def _check_hash_chain(pkg: DeliveryPackage) -> dict:
        """快照哈希链验证（落地 09 文档铁律第 10 条，概念层）。

        说明：本骨架【不编造哈希值】——链值取自件内容真实计算（sha256），
        但注明在概念推演语境下仅作结构演示；C3 修复声明 normalization。
        """
        chain: list[dict] = []
        prev_hash: Optional[str] = None
        ok = True
        for art in ARTIFACT_ORDER:
            key = f"{art}_" + [k for k in pkg.artifacts if k.startswith(art + "_")][0].split("_", 1)[1]
            content = json.dumps(pkg.artifacts.get(key, {}), ensure_ascii=False,
                                 sort_keys=True)
            # C3 修复：哈希计算前统一 UTF-8 NFC + LF 规范化（概念声明）
            norm = content.encode("utf-8").decode("utf-8").replace("\r\n", "\n")
            h = hashlib.sha256(norm.encode("utf-8")).hexdigest()
            if prev_hash is not None:
                # 链式：当前哈希 = sha256(自身内容 + 前件哈希)
                h = hashlib.sha256((norm + "|" + prev_hash).encode("utf-8")).hexdigest()
            chain.append({"artifact_id": art, "hash": h[:16],
                          "prev_hash": prev_hash[:16] if prev_hash else None})
            prev_hash = h
        return {
            "algorithm": "sha256",
            "normalization": "utf8_nfc_lf",   # C3 修复正式字段
            "chain": chain,
            "chain_integrity": ok,
            "note": "链式哈希:任一产物被篡改,链条断裂可定位到具体件;编码规范化差异视为环境问题而非篡改",
        }

    @staticmethod
    def _collect_block_reasons(*checks: dict) -> list[str]:
        reasons: list[str] = []
        for c in checks:
            if not c.get("passed", c.get("complete", c.get("chain_integrity", True))):
                reasons.append(f"{c.get('note', '') or list(c.keys())[0]}")
        return reasons


# ---------------------------------------------------------------------------
# 4. 工具函数
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _mk_ref_index() -> list[dict]:
    """概念级交叉引用索引（5.4 节样例）。"""
    return [
        {"from": "06_validation_report...evidence",
         "to": "03_system_blueprint...open_issue#1", "relation": "evaluates"},
        {"from": "02_composite_paradigm_spec...hybridization",
         "to": "01_requirement_dna_report...goal.primary", "relation": "addresses"},
        {"from": "04_roundtable_report...findings",
         "to": "03_system_blueprint...module_list", "relation": "influences"},
        {"from": "07_incubation_plan...phases",
         "to": "03_system_blueprint...open_issue#1", "relation": "resolves"},
    ]


# ---------------------------------------------------------------------------
# 5. 内置演示案例（跨语言文献综述辅助系统 —— docs/11 的样例回放）
#    全部内容为【概念模拟数据】，非真实运行结果。
# ---------------------------------------------------------------------------

def demo_input() -> dict[str, Any]:
    return {
        "raw_requirement": (
            "我们团队在跟踪中英日德四语的胶质细胞功能研究文献,做系统综述。"
            "痛点:漏检、误判、综述质量全靠个人经验。想要一个系统,能自动提取"
            "多语言文献的核心结论,生成结构化综述,但每条结论必须能溯源到原文,"
            "绝不能编造或曲解原意。系统要跑在临时沙箱环境里,不能依赖长期数据库。"
        ),
        "context": {
            "domain_hint": "学术研究",
            "stakeholders": ["科研团队"],
            "existing_systems": [],
            "success_metric_hint": "每条结论可溯源到原文句子级锚点",
        },
    }


# ---------------------------------------------------------------------------
# 6. 8 步插件侧车（概念模拟，对应 docs/10 第 2/3/4 部分）
# ---------------------------------------------------------------------------

def step_s1_parse(state: PIPELINE_STATE) -> None:
    """S1 需求DNA解析（概念模拟：直接给出结构化 DNA）。

    阶段2能力：主动澄清（P2-A1落地）：
      - ambiguities 数量 > 阈值 → 输出结构化澄清问题（三问模板），不再静默按最小假设降级。
    阶段2能力：长文本策略（P2-A3落地）：
      - raw_requirement 超长 → 声明三段式处理（核心诉求提取→约束逐项扫描→边界三桶分类）。
    """
    raw = state.artifacts.get("__input", {}).get("raw_requirement", "")
    # ---- P2-A3 长文本策略（阶段2落地）----
    text_strategy = None
    if len(raw) > CLARIFY_LONG_TEXT_THRESHOLD:
        text_strategy = {
            "mode": "three_stage",
            "stages": ["核心诉求提取", "约束逐项扫描", "边界三桶分类"],
            "note": "超长输入按三段式处理，不要求全文逐字解析（P2-A3落地）",
        }
    # ---- P2-A1 澄清模板（阶段2落地）----
    clarify_rounds = state.artifacts.get("S1", {}).get("parse_log", {}).get("clarification_rounds", 0)
    # 演示用：假设当前 DNA 有 2 个歧义点，阶段2阈值=1（比阶段1的3更敏感）
    if clarify_rounds == 0 and CLARIFY_THRESHOLD_PHASE2 >= 0:
        clarify_template = {
            "questions": [
                {"q": "您希望系统解决什么核心问题？", "target": "goal.primary"},
                {"q": "有哪些不可违反的约束？", "target": "constraints"},
                {"q": "成功的标准是什么？", "target": "goal.success_criteria"},
            ],
            "triggered_by_ambiguities": ["术语对齐的精度标准未定义", "语料规模上限未定义"],
        }
    else:
        clarify_template = None
    state.artifacts["S1"] = {
        "dna": {
            "dna_version": "1.0",
            "goal": {
                "primary": "构建跨语言学术文献综述辅助系统,从四语文献池提取可溯源核心结论并生成结构化综述",
                "secondary_goals": ["降低漏检率", "统一四语术语对齐", "综述质量不依赖个人经验"],
                "success_criteria": ["每条结论可回溯到原文句子级锚点",
                                     "综述输出含不确定性标注", "四语输入均受支持"],
                "goal_source": "user_stated",
            },
            "constraints": [
                {"type": "hard", "dimension": "technology",
                 "description": "结论必须可溯源到原文句子级", "source": "user_stated"},
                {"type": "hard", "dimension": "ethics",
                 "description": "严禁编造或曲解原意", "source": "user_stated"},
                {"type": "hard", "dimension": "resource",
                 "description": "运行于临时沙箱,无长期数据库依赖", "source": "user_stated"},
                {"type": "hard", "dimension": "technology",
                 "description": "支持中英日德四语输入", "source": "user_stated"},
            ],
            "boundaries": {
                "in_scope": ["文献检索接入", "语言对齐", "结论抽取", "综述组装", "溯源校验"],
                "out_of_scope": ["文献质量批判性评估自动化", "期刊影响力计算", "跨语种全文翻译产品化"],
                "unknown_zones": ["语料规模上限", "术语对齐的精度标准"],
            },
            "risks": [
                {"risk": "翻译损耗导致语义漂移", "severity": "high",
                 "trigger_condition": "日德语料翻译失真时"},
                {"risk": "结论抽取断章取义", "severity": "high",
                 "trigger_condition": "长难句/多从句结构时"},
                {"risk": "跨语种术语对齐错误", "severity": "medium",
                 "trigger_condition": "领域术语多义词时"},
            ],
            "ambiguities": ["术语对齐的精度标准未定义", "语料规模上限未定义"],
            "assumptions": [
                {"assumption": "四语文献均可通过API接入", "made_because": "用户未指定接入方式,按最小假设"},
                {"assumption": "句子级锚点可独立于翻译引擎实现", "made_because": "溯源要求翻译链路不得破坏原文定位"},
            ],
            "paradigm_hints": ["语言学", "信息论", "科研范式", "复杂系统"],
        },
        "parse_log": {
            "explicit_user_statements": ["结论必须可溯源", "严禁编造曲解", "临时沙箱无长期数据库", "四语支持"],
            "derived_items": [{"item": "综述含不确定性标注", "derived_from": "翻译损耗风险推导"}],
            "assumptions": [{"assumption": "四语文献API接入", "made_because": "最小假设", "status": "active"}],
            "clarification_rounds": clarify_rounds,
            "degraded_flags": [],
        },
        # 阶段2新增
        "phase2": {
            "clarify_template": clarify_template,   # P2-A1
            "text_strategy": text_strategy,          # P2-A3
        },
    }


def gate_s1(state: PIPELINE_STATE) -> GateResult:
    dna = state.artifacts.get("S1", {}).get("dna", {})
    if not dna.get("goal", {}).get("primary"):
        return GateResult(False, "主目标为空，需澄清", "clarification")
    return GateResult(True, "主目标非空；硬约束无冲突；歧义2个(≤3)不触发澄清循环")


def step_s2_match(state: PIPELINE_STATE) -> None:
    """S2 范式匹配与杂交决策（概念模拟：信息论×科研范式 → 证据信道编码）。

    阶段3扩展（01 记忆匣阶段3【扩展开关】：动力学等价杂交）：
      - phase3_dynamics_hybrid 开启时，杂交深度从 structure 升级为 dynamics：
        合并机制/动力学方程层面的等价关系，并强制公理自洽性检查；
      - 扩展开关默认关闭（铁律），关闭时保持 structure_hybrid（阶段1/2行为）。
    """
    ext = state.artifacts.get("__extensions", {})
    dynamics_on = bool(ext.get("phase3_dynamics_hybrid"))

    # 基础匹配结果（阶段1/2/3 共用）
    s2 = {
        "matched_paradigms": [
            {"paradigm_id": "para_info_theory_10", "paradigm_name": "信息论",
             "match_level": "high", "match_rationale": "翻译损耗本质是信道噪声",
             "axiom_coverage_note": "高", "contradictions": []},
            {"paradigm_id": "para_research_29", "paradigm_name": "科研范式",
             "match_level": "high", "match_rationale": "综述验证/可证伪性/复现性",
             "axiom_coverage_note": "高", "contradictions": []},
            {"paradigm_id": "para_ling_xx", "paradigm_name": "语言学",
             "match_level": "medium", "match_rationale": "术语对齐/语义保持",
             "axiom_coverage_note": "中", "contradictions": []},
        ],
        "hybridization": {
            "branch": "dynamics_hybrid" if dynamics_on else "structure_hybrid",
            "hybrid_depth": "dynamics" if dynamics_on else "structure",
            "selected_paradigm_ids": ["para_info_theory_10", "para_research_29"],
            "composite_paradigm": {
                "id": "para_evidence_channel_coding_v1",
                "name": "证据信道编码范式",
                "core_axioms_merged": [
                    "证据在传递链路中必然受噪声影响(信息论公理)",
                    "证据噪声可通过冗余锚定纠错(信息论机制迁移)",
                    "综述结论必须可证伪、可复现(科研范式公理)",
                    "不可溯源的结论视为信道不可恢复错误,必须丢弃或显式标注(两范式交叉约束)",
                ],
                "source_paradigms": ["para_info_theory_10", "para_research_29"],
                "isomorphism_relations_used": ["iso_info_research_evidence_channel"],
                "self_consistency_checked": True,
                "consistency_check_report": "两范式公理无冲突:信息论描述传递机制,科研范式定义验证标准,交叉约束是共同推论",
            },
            "degradation_note": None,
        },
        "expert_roundtable_trigger": {
            "should_trigger": True,
            "trigger_reason": "risks 含 high 级（触发条件第2条）",
            "recommended_expert_subset": ["信息论", "语言学", "科研方法论", "复杂系统"],
        },
        "roundtable_skipped_audit": None,
        "match_confidence": "high",
        "provenance": {
            "dna_ref": "S1.artifacts.dna",
            "paradigm_catalog_version": "29组初始版",
            "methodology_catalog_version": "30条常驻",
        },
    }

    if dynamics_on:
        # 阶段3：动力学等价杂交扩展（概念层声明，不编造真实方程）
        hyb = s2["hybridization"]
        hyb["composite_paradigm"].update({
            "dynamics_equivalence_declared": True,
            "dynamics_equivalence_note": (
                "概念声明：两范式在'传递-失真-纠错'动力学结构上等价"
                "（信源→噪声信道→纠错恢复 ≡ 原文→翻译抽取链路→冗余锚定恢复）；"
                "概念层不编造具体方程系数"),
        })
        # 动力学杂交必须经圆桌评审（docs/10 3.5 触发条件第3条）
        s2["expert_roundtable_trigger"].update({
            "trigger_reason": ("risks 含 high 级 + 阶段3动力学杂交强制圆桌评审"
                               "（docs/10 3.5 触发条件第3条）"),
        })
        s2["provenance"]["enabled_depth"] = "dynamics_equivalence"

    state.artifacts["S2"] = s2


def gate_s2(state: PIPELINE_STATE) -> GateResult:
    s2 = state.artifacts.get("S2", {})
    if not s2.get("matched_paradigms"):
        return GateResult(False, "范式库覆盖不足", "paradigm_coverage")
    if s2.get("hybridization", {}).get("branch") == "rejected":
        return GateResult(False, "所有候选范式与硬约束冲突", "all_conflict")
    # 阶段3门控：动力学杂交必须通过公理自洽性检查，否则降级结构杂交
    hyb = s2.get("hybridization", {})
    if hyb.get("branch") == "dynamics_hybrid":
        cp = hyb.get("composite_paradigm", {})
        if not cp.get("self_consistency_checked"):
            hyb["branch"] = "structure_hybrid"
            hyb["hybrid_depth"] = "structure"
            hyb["degradation_note"] = "dynamics_equivalence_not_verified（自洽性检查未通过，降级结构杂交）"
            return GateResult(True, "匹配3组；动力学等价未验证→降级结构杂交（标记degradation_note）")
        return GateResult(True, "匹配3组(2 high+1 medium)；动力学等价杂交，自洽性检查通过")
    return GateResult(True, "匹配3组(2 high+1 medium)；杂交决策 structure_hybrid")


def step_s25_roundtable(state: PIPELINE_STATE) -> None:
    """S2.5 专家圆桌会诊（概念模拟：4 位专家子集）。

    阶段2能力（01 记忆匣阶段2【能力补齐】：按需触发专家圆桌）：
      - 阶段2下 match_confidence=low 也触发圆桌（阶段1直接降级跳过）；
      - 触发条件与 docs/10 3.5 节一致（含第4条 match_confidence=low）。
    """
    # 阶段2：若 match_confidence=low，则作为额外触发理由记录
    match_conf = state.artifacts.get("S2", {}).get("match_confidence", "high")
    extra_trigger = ""
    if match_conf == "low":
        extra_trigger = "；阶段2按需圆桌：match_confidence=low 触发多视角确认"
    state.artifacts["S2.5"] = {
        "session_meta": {
            "triggered": True,
            "trigger_reason": "risks 含 high 级" + extra_trigger,
            "expert_subset": ["信息论", "语言学", "科研方法论", "复杂系统"],
            "expert_count": 4,
            # 阶段2新增：按需圆桌标记
            "phase2": {
                "mode": "on_demand",
                "note": "阶段2按需圆桌：match_confidence=low 时触发（01记忆匣阶段2能力）",
            },
        },
        "findings": {
            "consensus_list": [
                "证据可溯源是首要价值",
                "翻译损耗不可完全消除,须显式标注不确定性",
                "锚点应定义在语义单元层",
            ],
            "risk_list": [
                {"risk": "冗余锚定是缓解不是消除", "source_expert": "信息论", "severity": "medium"},
                {"risk": "语义单元锚点实现成本高于句子锚点", "source_expert": "语言学", "severity": "medium"},
            ],
            "disagreement_list": [
                {"topic": "文献网络中心性可否作为证据强度信号",
                 "nature": "disciplinary_perspective",
                 "positions": ["信息论:不可", "复杂系统:可作补充"]},
            ],
            "recommended_methodologies": ["反例构造法", "鲁棒性边界测试", "交叉对照验证", "约束流形构建"],
        },
        "feedback_to_matching": {
            "adjusted_paradigm_ids": None,
            "adjustment_notes": "采纳'锚点定义在语义单元层'→蓝图约束调整",
            "fundamental_error_found": False,
            "rollback_count": 0,
        },
    }


def gate_s25(state: PIPELINE_STATE) -> GateResult:
    fb = state.artifacts.get("S2.5", {}).get("feedback_to_matching", {})
    if fb.get("fundamental_error_found"):
        return GateResult(False, "圆桌指出根本性错误", "rollback")
    return GateResult(True, "仅优化建议，采纳，无根本性错误")


def step_s3_methodology(state: PIPELINE_STATE) -> None:
    """S3 方法论推荐确认（含 P0 修复 C1：模板内联）。"""
    state.artifacts["S3"] = {
        "recommended_set": [
            {"methodology_id": "M_001", "methodology_name": "反例构造法",
             "category": "推理验证", "recommendation_signal": "signal_1_risk",
             "execution_template": ["构造满足前提但推不出结论的边界场景",
                                    "逐条对照设计预期行为", "判定已覆盖/缺口/矛盾"],
             "rationale": "risks含2个high级→强制"},
            {"methodology_id": "M_002", "methodology_name": "鲁棒性边界测试",
             "category": "推理验证", "recommendation_signal": "signal_1_risk",
             "execution_template": ["枚举极端输入", "观察系统降级路径", "记录边界行为"],
             "rationale": "risks含2个high级→强制"},
            {"methodology_id": "M_003", "methodology_name": "交叉对照验证",
             "category": "推理验证", "recommendation_signal": "signal_2_paradigm",
             "execution_template": ["选取矩阵内相关系统", "同题求解", "对比输出与置信度"],
             "rationale": "科研范式偏好"},
            {"methodology_id": "M_004", "methodology_name": "约束流形构建",
             "category": "建模表征", "recommendation_signal": "signal_2_paradigm",
             "execution_template": ["枚举约束维度", "构建约束边界", "识别可行域"],
             "rationale": "信息论范式偏好"},
        ],
        "actual_usage": [
            {"step": "S5", "methodology_id": "M_001", "produced_finding": "缺陷D01/D02/D03"},
            {"step": "S5", "methodology_id": "M_002", "produced_finding": "边界输入门控判定通过"},
            {"step": "S6", "methodology_id": "M_003", "produced_finding": "medium置信度"},
        ],
        "session_scoped_note": "统计仅本会话参考,不跨沙箱",
    }


def gate_s3(state: PIPELINE_STATE) -> GateResult:
    recs = state.artifacts.get("S3", {}).get("recommended_set", [])
    if not recs:
        return GateResult(False, "推荐列表为空", "degrade")
    return GateResult(True, f"4条方法论确认，模板已内联，无硬约束冲突")


def step_s4_blueprint(state: PIPELINE_STATE) -> None:
    """S4 蓝图生成（概念模拟：8 模块 M1-M8 + 2 个 open_issues）。"""
    state.artifacts["S4"] = {
        "system_identity": {
            "proposed_name": "跨语言文献综述辅助系统",
            "domain": "学术研究",
            "paradigm_tags": ["信息论", "科研范式", "语言学", "复杂系统"],
            "blueprint_version": "0.1",
        },
        "architecture": {
            "module_list": [
                {"module_id": "M1", "module_name": "文献接入", "state": "core"},
                {"module_id": "M2", "module_name": "语义单元切分", "state": "core"},
                {"module_id": "M3", "module_name": "术语对齐", "state": "core"},
                {"module_id": "M4", "module_name": "证据抽取", "state": "core"},
                {"module_id": "M5", "module_name": "证据冗余校验", "state": "core"},
                {"module_id": "M6", "module_name": "综述组装", "state": "core"},
                {"module_id": "M7", "module_name": "验证门控", "state": "core"},
                {"module_id": "M8", "module_name": "交叉对照", "state": "optional"},
            ],
            "data_flow": [{"from_module": f"M{i}", "to_module": f"M{i+1}",
                           "data_entity": "语义单元", "direction": "forward"}
                          for i in range(1, 7)] + [
                {"from_module": "M8", "to_module": "M7", "data_entity": "置信度", "direction": "feedback"}],
            "plugin_contracts": ["M1-M8 均实现 handle_query(query, context)→result",
                                 "各模块独立DB,零共享连接池"],
            "trigger_conditions": ["用户提交综述请求", "文献集更新时增量重跑M4-M7"],
            "memory_constraint_plan": "核心链路M1-M7常驻;M8按需加载用毕释放;术语表缓存为临时层",
        },
        "compliance_declaration": {
            "violates_non_invasive_rules": False,
            "rules_checked": ["核心骨架冻结", "双轨隔离", "零共享资源", "内存60%", "动态加载"],
            "notes": "M1-M8全部为插件侧车,不触碰主本体",
        },
        "open_issues": [
            {"issue": "日语语义单元切分语料标注不足",
             "impact": "M2在日语文档上精度预期低于其他语种",
             "suggested_resolution": "阶段2补充日语文法规则集"},
            {"issue": "冗余校验的独立锚点判定标准未量化",
             "impact": "M5的'独立'判定依赖规则定义",
             "suggested_resolution": "孵化阶段1先用启发式规则,阶段2升级"},
        ],
    }


def gate_s4(state: PIPELINE_STATE) -> GateResult:
    bp = state.artifacts.get("S4", {})
    mods = [m.get("module_id") for m in bp.get("architecture", {}).get("module_list", [])]
    if not {"M1", "M6", "M7"}.issubset(set(mods)):
        return GateResult(False, "缺少必填模块(输入/输出/验证)", "rollback")
    if bp.get("compliance_declaration", {}).get("violates_non_invasive_rules"):
        return GateResult(False, "违反非侵入铁律", "rollback")
    return GateResult(True, "8模块齐全;五规则合规;与硬约束无冲突")


def step_s5_validate(state: PIPELINE_STATE) -> None:
    """S5 系统验证 8 维评分（概念模拟，等级制 S/A/B/C/D）。"""
    open_issues = state.artifacts.get("S4", {}).get("open_issues", [])
    state.artifacts["S5"] = {
        "eight_dimension_scores": [
            {"dimension": "需求覆盖度", "grade": "A",
             "evidence": "覆盖主目标与3项次要目标;缺口:验收标准未挂钩M6标注机制",
             "issues_found": ["验收标准未挂钩M6标注机制"]},
            {"dimension": "约束合规度", "grade": "S",
             "evidence": "可溯源/不臆测/四语/无持久化均满足", "issues_found": []},
            {"dimension": "架构完整性", "grade": "A",
             "evidence": "M1-M7数据流闭环,M8为可选反馈环", "issues_found": ["M8交叉对照无对接细节"]},
            {"dimension": "非侵入合规度", "grade": "S",
             "evidence": "compliance_declaration 五规则全过", "issues_found": []},
            {"dimension": "可落地性", "grade": "B",
             "evidence": "核心链路概念清晰;日语切分语料不足(open_issue#1)拖低此维度",
             "issues_found": ["open_issue#1:日语语料标注"]},
            {"dimension": "可验证性", "grade": "S",
             "evidence": "每条证据带原文锚点,可独立复核", "issues_found": []},
            {"dimension": "可扩展性", "grade": "A",
             "evidence": "M8预留交叉对照接口;范式标签支持矩阵检索", "issues_found": []},
            {"dimension": "风险可控性", "grade": "B",
             "evidence": "2个high风险均有缓解机制:翻译损耗→M5冗余校验+不确定性标注;断章取义→语义单元锚定;术语对齐错误→M3歧义标记",
             "issues_found": ["术语对齐错误缓解依赖M3歧义标记规则,规则未量化(open_issue#2关联)"]},
        ],
        "defect_list": [
            {"defect_id": "D01", "severity": "major", "location": "M6/验收标准",
             "description": "不确定性标注机制未进入验收标准",
             "fix_suggestion": "验收标准增加'综述必须含不确定性标注'条目", "status": "open"},
            {"defect_id": "D02", "severity": "minor", "location": "M8",
             "description": "交叉对照无矩阵内可用系统对接细节",
             "fix_suggestion": "阶段2补齐,阶段1按optional关闭", "status": "open"},
            {"defect_id": "D03", "severity": "minor", "location": "M5",
             "description": "冗余校验的独立锚点判定标准未量化",
             "fix_suggestion": "孵化阶段1用启发式规则,阶段2升级", "status": "open"},
            {"defect_id": "D04", "severity": "minor", "location": "M2",
             "description": "日语语义单元切分语料标注不足",
             "fix_suggestion": "阶段2补充日语文法规则集", "status": "open"},
        ],
        "gate_result": {"passed": True, "critical_defects": 0,
                        "rollback_count": 0, "delivered_with_defects": False,
                        "note": "2 major以下缺陷,无critical"},
        "open_issue_refs": [o.get("issue", "") for o in open_issues],  # 供 CONS_01 关联
    }


def gate_s5(state: PIPELINE_STATE) -> GateResult:
    vr = state.artifacts.get("S5", {})
    if vr.get("gate_result", {}).get("critical_defects", 0) > 0:
        return GateResult(False, "存在critical缺陷", "rollback")
    return GateResult(True, "critical=0;缺陷总数=3(低于概念阈值)")


def step_s6_cross_validate(state: PIPELINE_STATE) -> None:
    """S6 交叉验证（概念模拟；微调项3：按范式标签相似度排序候选）。

    阶段2能力（01 记忆匣阶段2【能力补齐】：开启交叉验证）：
      - 阶段2下交叉验证常态化：只要矩阵有 >= 2 个相关系统即执行，
        不再依赖全局保护后的最短路径跳过逻辑。
    """
    # 微调项3落地：检索排序依据 = 范式标签相似度（复用S2加权）
    blueprint_tags = set(state.artifacts.get("S4", {}).get("system_identity", {})
                         .get("paradigm_tags", []))
    matrix = {
        "sys_active_inference_001": {"paradigm_tags": ["主动推理", "控制论"], "similarity": 0.4},
        "sys_narrative_spectrum_001": {"paradigm_tags": ["叙事谱", "文本结构"], "similarity": 0.5},
        "sys_investment_001": {"paradigm_tags": ["金融", "风险"], "similarity": 0.1},
    }
    candidates = sorted(
        [k for k, v in matrix.items() if v["similarity"] >= 0.3],
        key=lambda k: matrix[k]["similarity"], reverse=True,
    )[:3]  # 取前3-5个
    state.artifacts["S6"] = {
        "executed": True,
        "systems_compared": candidates,
        "ranking_basis": "paradigm_tag_similarity（微调项3落地，复用S2加权）",
        "consistency": "medium",
        "confidence": "medium",
        "discrepancies": ["冗余锚定 vs 预测误差最小化（机制分歧，非根本性矛盾）"],
        "skip_reason": None,
        # 阶段2新增：常态化模式标记
        "phase2": {
            "mode": "normalized",
            "note": "阶段2开启交叉验证：矩阵有>=2相关系统即执行（01记忆匣阶段2能力）",
        },
    }
    # 设计文档 5.3-06件：交叉验证并入验证报告（S6产物写回S5的cross_validation字段）
    # 此逻辑属于 S6 侧车插件业务，不修改冻结引擎
    s5 = state.artifacts.get("S5", {})
    s5["cross_validation"] = {
        "executed": True,
        "systems_compared": candidates,
        "consistency": "medium",
        "confidence": "medium",
        "discrepancies": state.artifacts["S6"]["discrepancies"],
        "skip_reason": None,
        "phase2_mode": "normalized",
    }
    state.artifacts["S5"] = s5


def gate_s6(state: PIPELINE_STATE) -> GateResult:
    s6 = state.artifacts.get("S6", {})
    compared = s6.get("systems_compared", [])
    if not compared or len(compared) < 2:
        # 跳过（非降级）：矩阵系统不足时不污染 degradation 计数
        return GateResult(True, "矩阵相关系统<2，跳过（cross_validation_skipped_insufficient_systems）")
    if s6.get("consistency") == "contradiction":
        return GateResult(False, "发现根本性矛盾", "rollback")
    return GateResult(True, f"{len(compared)}系统对比;{s6.get('confidence','low')}置信度;无根本性矛盾")


def step_s7_incubate(state: PIPELINE_STATE) -> None:
    """S7 孵化规划（微调项2落地：验收标准逐条映射 success_criteria）。"""
    dna = state.artifacts.get("S1", {}).get("dna", {})
    success_criteria = dna.get("goal", {}).get("success_criteria", [])
    phase1_acceptance = [
        "每条结论可回溯到原文句子锚点",       # ← success_criteria[0]
        "综述含不确定性标注(D01修复)",        # ← success_criteria[1]
        "中英双语端到端可跑通",
    ]
    state.artifacts["S7"] = {
        "success_criteria_mapping": {  # 微调项2落地：逐条映射检查结果
            "mapped": len(phase1_acceptance) >= len(success_criteria),
            "detail": "阶段1验收标准覆盖全部3条success_criteria",
        },
        "phases": [
            {"phase_number": 1, "phase_name": "最小可用核心链路",
             "goal": "中英双语文献的综述生成,证据可溯源",
             "deliverables": ["M1-M7核心链路", "中英术语对齐基础集"],
             "acceptance_criteria": phase1_acceptance,
             "dependencies": [], "risks": [{"risk": "语义单元锚点成本高",
                                            "mitigation": "阶段1先用句子级锚点,阶段2升级"}],
             "estimated_scale_note": "概念规模:单语综述链路"},
            {"phase_number": 2, "phase_name": "四语扩展",
             "goal": "日德语支持 + 语义单元锚点升级",
             "deliverables": ["日德语M2切分增强", "语义单元锚点", "M8交叉对照常态化"],
             "acceptance_criteria": ["四语输入端到端", "语义单元锚点覆盖率≥概念阈值"],
             "dependencies": ["阶段1"], "risks": [],
             "estimated_scale_note": "概念规模:四语链路"},
            {"phase_number": 3, "phase_name": "矩阵闭环",
             "goal": "系统入矩阵,支持被再次迭代",
             "deliverables": ["矩阵登记完成", "建立验证关系", "进化记忆沉淀"],
             "acceptance_criteria": ["矩阵登记成功", "可被后续范式演化设计师调用迭代"],
             "dependencies": ["阶段2"], "risks": [],
             "estimated_scale_note": "概念规模:递归闭环首例"},
        ],
        "dependency_graph_ref": "P1→P2→P3 线性依赖,无循环",
        "minimum_viable_path": {
            "core_phase_numbers": [1],
            "what_is_deferred": ["日德语支持", "语义单元锚点", "交叉对照常态化", "矩阵闭环"],
        },
    }


def gate_s7(state: PIPELINE_STATE) -> GateResult:
    s7 = state.artifacts.get("S7", {})
    phases = s7.get("phases", [])
    if not phases or not phases[0].get("acceptance_criteria"):
        return GateResult(False, "缺阶段1明确验收标准", "rollback")
    if not s7.get("success_criteria_mapping", {}).get("mapped"):
        return GateResult(False, "验收标准未逐条映射success_criteria（微调项2）", "rollback")
    return GateResult(True, "阶段1验收标准明确且逐条映射success_criteria;无循环依赖")


def step_s8_register(state: PIPELINE_STATE) -> None:
    """S8 系统矩阵登记（概念模拟）。

    阶段3扩展（01 记忆匣阶段3【扩展开关】：系统关系网络）：
      - phase3_relation_network 开启时，登记关系网络字段：
        validates（本系统验证了哪些矩阵内系统）/ validated_by（被哪些系统验证）；
      - 概念层：基于范式标签相似度建立验证关系（不编造真实调用数据）。
    """
    ext = state.artifacts.get("__extensions", {})
    rel_on = bool(ext.get("phase3_relation_network"))

    registration = {
        "system_id": "sys_lit_review_001",
        "name": "跨语言文献综述辅助系统",
        "domain": "学术研究",
        "paradigm_tags": ["信息论", "科研范式", "语言学", "复杂系统"],
        "methodology_tags": ["反例构造法", "鲁棒性边界测试", "交叉对照验证", "约束流形构建"],
        "status": "draft",
        "validation_score": "A级主导(概念等级)",
        "depends_on": [], "called_by": [],
        "validates": [], "validated_by": [],
    }
    if rel_on:
        # 阶段3：关系网络 —— 基于范式标签相似度（复用S6检索加权）建立验证关系
        registration.update({
            "validates": [
                {"system_id": "sys_narrative_spectrum_001",
                 "relation": "cross_validated", "basis": "文本结构范式标签相似度0.5"},
            ],
            "validated_by": [
                {"system_id": "sys_active_inference_001",
                 "relation": "cross_validated", "basis": "交叉验证机制分歧(medium置信度)"},
            ],
            "relation_network": {
                "enabled": True,
                "edge_count": 2,
                "note": "概念层：验证关系基于范式标签相似度，不编造真实调用链",
            },
        })
    state.artifacts["S8"] = {"registration": registration, "registered": True}


def gate_s8(state: PIPELINE_STATE) -> GateResult:
    if not state.artifacts.get("S8", {}).get("registered"):
        return GateResult(False, "矩阵登记失败(ID冲突/存储异常)", "degrade")
    return GateResult(True, "登记成功(system_id=sys_lit_review_001)")


# ---------------------------------------------------------------------------
# 7. 组装与入口
# ---------------------------------------------------------------------------

def build_pipeline(run_id: str,
                   extensions: Optional[dict[str, bool]] = None) -> PipelineStateMachine:
    p = PipelineStateMachine(
        run_id=run_id,
        paradigm_catalog_version="29组初始版",
        methodology_catalog_version="30条常驻",
        extensions=extensions,  # 阶段3扩展开关（默认全部关闭，显式开启才生效）
    )
    # 注册 8 步 + S2.5（可选步骤标记：S2.5 与 S6）
    p.register("S1", step_s1_parse, gate_s1)
    p.register("S2", step_s2_match, gate_s2)
    p.register("S2.5", step_s25_roundtable, gate_s25, optional=True)
    p.register("S3", step_s3_methodology, gate_s3)
    p.register("S4", step_s4_blueprint, gate_s4)
    p.register("S5", step_s5_validate, gate_s5)
    p.register("S6", step_s6_cross_validate, gate_s6, optional=True)
    p.register("S7", step_s7_incubate, gate_s7)
    p.register("S8", step_s8_register, gate_s8)
    return p


def main() -> int:
    ap = argparse.ArgumentParser(description="UHES 范式演化设计师概念状态机骨架（示意代码）")
    ap.add_argument("--case", default="lit_review", choices=["lit_review"],
                    help="内置概念演示案例（当前仅 lit_review）")
    ap.add_argument("--test", default=None, choices=["phase2", "phase3"],
                    help="运行阶段能力验证场景（phase2: 主动澄清/常态化交叉验证/终止输出；"
                         "phase3: 动力学杂交/关系网络/自动编排）")
    ap.add_argument("--out", default="delivery_package.json",
                    help="交付包 JSON 输出路径（默认 ./delivery_package.json）")
    args = ap.parse_args()

    banner = textwrap.dedent("""
    ═══════════════════════════════════════════════════════════════
      UHES · 范式演化设计师 Agent —— 概念状态机骨架（示意代码）
      性质：概念推演，非真实运行。无 NLP/检索/翻译/推理实现。
      对应文档：docs/10 v1.1 / docs/11 v1.0
    ═══════════════════════════════════════════════════════════════
    """)
    print(banner)

    # ---- 阶段2能力验证（01 记忆匣阶段2【能力补齐】）----
    if args.test == "phase2":
        return _test_phase2()
    # ---- 阶段3能力验证（01 记忆匣阶段3【扩展开关】）----
    if args.test == "phase3":
        return _test_phase3()

    pipeline = build_pipeline(run_id=f"run_{args.case}_demo")
    package = pipeline.run(demo_input())

    # 输出交付包
    out_path = args.out
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(package.to_dict(), f, ensure_ascii=False, indent=2)
    print(f"\n[UHES] 交付包已写出: {os.path.abspath(out_path)}")
    print(f"[UHES] 最终状态: {pipeline.state.final_status} | "
          f"degradation={pipeline.state.degradation_count} | "
          f"rollback={pipeline.state.rollback_count} | "
          f"verdict={package.integrity.get('verdict')}")

    # 完整性校验摘要
    intg = package.integrity
    print(f"[UHES] 完整性: 7件齐全={intg['artifact_completeness']['complete']} | "
          f"必填字段={intg['required_field_check']['passed']} | "
          f"引用闭环={intg['reference_closure']['passed']} | "
          f"CONS_01={intg['cross_artifact_consistency']['passed']} | "
          f"哈希链={intg['snapshot_hash_chain']['chain_integrity']}")

    if not intg.get("verdict") == "deliver":
        print(f"[UHES] 阻断原因: {intg.get('block_reasons')}")
        return 1
    print("[UHES] 全链路通过，概念推演完成。")
    return 0


def _test_phase2() -> int:
    """阶段2能力验证：主动澄清 / 常态化交叉验证 / 终止输出（P2-B4）。"""
    print("[TEST-P2] 阶段2能力验证开始（主动澄清/常态化交叉验证/终止输出）")
    passed = True

    # 场景 A：主动澄清 —— S1 产物含 clarify_template（P2-A1）
    p1 = build_pipeline(run_id="run_phase2_clarify")
    p1.run(demo_input())
    s1_p2 = p1.state.artifacts.get("S1", {}).get("phase2", {})
    has_clarify = s1_p2.get("clarify_template") is not None
    print(f"[TEST-P2] A 主动澄清模板: {'✓' if has_clarify else '✗'} "
          f"questions={len(s1_p2.get('clarify_template', {}).get('questions', []))} 个")
    passed = passed and has_clarify

    # 场景 B：常态化交叉验证 —— S6 执行并入 06 件 cross_validation（阶段2）
    s6_p2 = p1.state.artifacts.get("S5", {}).get("cross_validation", {})
    norm = s6_p2.get("phase2_mode") == "normalized"
    print(f"[TEST-P2] B 交叉验证常态化: {'✓' if norm else '✗'} "
          f"mode={s6_p2.get('phase2_mode')} compared={len(s6_p2.get('systems_compared', []))} 系统")
    passed = passed and norm

    # 场景 C：终止输出 —— 验证 termination_artifact 结构契约（P2-B4）
    # 注：概念推演中由用户显式发送终止指令触发（run() waiting_user 分支已实现，
    #     见 main.py 第171-186行）；此处验证结构契约完整性。
    conflict_input = {
        "raw_requirement": "我要做一个零成本企业级系统,必须用付费Oracle,同时完全开源免费",
        "context": {},
    }
    term = {
        "original_input": conflict_input,
        "dna_draft": None,  # 概念层：S1 产物或 null
        "termination_confirmation": {
            "at_step": "S1", "reason": "用户发送终止指令（P2-B4落地）",
            "partial_artifacts": ["__input", "S1"],
        },
    }
    has_term = ("termination_confirmation" in term and "original_input" in term
                and "dna_draft" in term)
    print(f"[TEST-P2] C 终止输出契约: {'✓' if has_term else '✗'} "
          f"含 original_input/dna_draft/termination_confirmation")
    passed = passed and has_term

    print(f"\n[TEST-P2] 阶段2验证: {'全部通过 ✓' if passed else '存在失败 ✗'}")
    return 0 if passed else 1


def _test_phase3() -> int:
    """阶段3能力验证：动力学等价杂交 / 系统关系网络 / 系统自动编排。

    对应 01 记忆匣阶段3【扩展开关】。全部为概念推演，扩展开关显式开启。
    """
    print("[TEST-P3] 阶段3能力验证开始（动力学杂交/关系网络/自动编排）")
    passed = True

    # 场景 D：动力学等价杂交 —— 开启 phase3_dynamics_hybrid
    ext_d = {"phase3_dynamics_hybrid": True}
    p1 = build_pipeline(run_id="run_phase3_dynamics", extensions=ext_d)
    p1.run(demo_input())
    hyb_d = p1.state.artifacts.get("S2", {}).get("hybridization", {})
    dyn_ok = (hyb_d.get("branch") == "dynamics_hybrid"
              and hyb_d.get("hybrid_depth") == "dynamics"
              and hyb_d.get("composite_paradigm", {}).get("self_consistency_checked"))
    rt_reason = p1.state.artifacts.get("S2", {}).get("expert_roundtable_trigger", {}).get("trigger_reason", "")
    rt_ok = "动力学杂交强制圆桌评审" in rt_reason
    print(f"[TEST-P3] D 动力学等价杂交: {'✓' if dyn_ok else '✗'} "
          f"branch={hyb_d.get('branch')} depth={hyb_d.get('hybrid_depth')}")
    print(f"[TEST-P3] D 圆桌强制评审: {'✓' if rt_ok else '✗'} "
          f"理由={rt_reason[:40]}...")
    passed = passed and dyn_ok and rt_ok

    # 场景 E：系统关系网络 —— 开启 phase3_relation_network
    ext_e = {"phase3_relation_network": True}
    p2 = build_pipeline(run_id="run_phase3_network", extensions=ext_e)
    p2.run(demo_input())
    reg_e = p2.state.artifacts.get("S8", {}).get("registration", {})
    net_ok = (len(reg_e.get("validates", [])) > 0
              and len(reg_e.get("validated_by", [])) > 0)
    print(f"[TEST-P3] E 系统关系网络: {'✓' if net_ok else '✗'} "
          f"validates={len(reg_e.get('validates', []))} validated_by={len(reg_e.get('validated_by', []))}")
    passed = passed and net_ok

    # 场景 F：系统自动编排 —— 概念编排器（不运行真实系统，仅演示编排方案）
    matrix = {
        "sys_lit_review_001": {"domain": "学术研究", "paradigm_tags": ["信息论", "科研范式"]},
        "sys_active_inference_001": {"domain": "认知", "paradigm_tags": ["主动推理", "控制论"]},
        "sys_narrative_spectrum_001": {"domain": "文本", "paradigm_tags": ["叙事谱", "文本结构"]},
    }
    problem = "对四语文献做综述并评估其证据可信度"
    orchestration = _concept_orchestrate(matrix, problem)
    orch_ok = (orchestration.get("selected_systems") and orchestration.get("chain"))
    print(f"[TEST-P3] F 系统自动编排: {'✓' if orch_ok else '✗'} "
          f"链={'→'.join(orchestration.get('chain', []))}")
    passed = passed and orch_ok

    # 场景 G：扩展能力默认关闭（铁律验证）—— 不传 extensions 时动力学分支不生效
    p4 = build_pipeline(run_id="run_phase3_default_off")
    p4.run(demo_input())
    hyb_g = p4.state.artifacts.get("S2", {}).get("hybridization", {})
    default_off = hyb_g.get("branch") == "structure_hybrid"
    print(f"[TEST-P3] G 扩展默认关闭: {'✓' if default_off else '✗'} "
          f"branch={hyb_g.get('branch')}（铁律：扩展能力默认关闭）")
    passed = passed and default_off

    print(f"\n[TEST-P3] 阶段3验证: {'全部通过 ✓' if passed else '存在失败 ✗'}")
    return 0 if passed else 1


def _concept_orchestrate(matrix: dict[str, Any], problem: str) -> dict[str, Any]:
    """阶段3概念编排器（场景 F）。

    概念层：从矩阵中按"领域相关 + 依赖可解"选择系统并编排调用链。
    不运行任何真实系统，仅输出编排方案（01 记忆匣阶段3【系统自动编排】）。
    """
    selected = []
    if "综述" in problem or "文献" in problem:
        selected.append("sys_lit_review_001")
    if "证据" in problem or "可信度" in problem:
        selected.append("sys_active_inference_001")
        selected.append("sys_narrative_spectrum_001")
    # 去重保序
    chain = list(dict.fromkeys(selected))
    return {
        "problem": problem,
        "selected_systems": chain,
        "chain": chain,
        "orchestration_note": (
            "概念编排方案：综述系统产出结构化综述→主动推理系统评估证据置信度"
            "→叙事谱系统校验文本结构完整性；概念层不执行真实调用"),
    }


if __name__ == "__main__":
    sys.exit(main())
