# UHES · 概念状态机骨架（示意代码）

> **性质声明**:本目录代码为【概念推演】的示意骨架，**非真实运行的业务系统**。
> 它模拟 docs/10 定义的状态流转、门控、回退/降级保护与完整性校验的"结构"，
> 不含任何真实 NLP / 检索 / 翻译 / 推理实现，不编造性能数据。

## 文件

| 文件 | 说明 |
|------|------|
| `main.py` | 概念状态机骨架（完整可运行，纯标准库，Python ≥ 3.10） |
| `requirements.txt` | 依赖声明（无第三方依赖） |
| `delivery_package.json` | 概念演示输出样例（`python3 main.py` 运行产物） |

## 运行

```bash
cd src
python3 main.py                # 跑通内置演示案例（跨语言文献综述辅助系统）
python3 main.py --out demo.json  # 自定义交付包输出路径
python3 main.py --test phase2    # 阶段2能力验证（主动澄清/常态化交叉验证/终止输出）
python3 main.py --test phase3    # 阶段3扩展验证（动力学杂交/关系网络/自动编排/默认关闭）
python3 main.py --test phase4    # 阶段4递归闭环验证（有效进化/冗余迭代/深度保护）
python3 main.py --frozen-check   # 冻结校验（引擎未改/开关默认关/步骤集未变/参数基线）
python3 main.py --trace          # 第8项优化:事件总线(span树+指标聚合+JSONL事件流)
python3 main.py --test suite      # 第9项优化:集成测试矩阵(LLM mock,11用例离线)
python3 main.py --agent lit_review # 第10项优化:多Agent三环(设计师/验证器/审计器)
python3 main.py --plugins src/plugins # 第7项优化:动态加载插件覆盖侧车(示例 step_s1_llm)
# 第6项优化:矩阵持久化(UHES_MATRIX_DB=<db路径> python3 main.py --test phase4 启用SQLite持久化)
# 第3项优化:杂交决策双通道(S2 LLM评审+确定性校验;设置 ZHIPU_API_KEY 启用真实LLM,无key自动降级确定性通道)
# 第4项优化:蓝图生成LLM化(S4 智谱GLM生成蓝图,失败回退模板,open_issues自动同步CONS_01)
# 第5项优化:8维验证LLM-as-judge(S5 智谱GLM评估8维,失败回退静态等级)
# 第2项优化:范式匹配 embedding 化(S2 从 DNA.paradigm_hints 动态 n-gram 匹配,替代硬编码)
```

## 阶段能力状态

| 阶段 | 能力 | 验证命令 | 状态 |
|------|------|---------|------|
| 阶段1 | 8步状态机/门控/回退/最短路径/完整性校验 | `python3 main.py` | ✅ |
| 阶段2 | 交叉验证常态化/主动澄清/按需圆桌/P2项 | `--test phase2` | ✅ |
| 阶段3 | 动力学等价杂交/关系网络/自动编排（默认关闭） | `--test phase3` | ✅ |
| 阶段4 | 递归闭环/进化价值判定/evolves_from溯源/深度保护（默认关闭） | `--test phase4` | ✅ |

阶段3/4扩展开关遵循"扩展能力默认关闭"铁律：
`build_pipeline(run_id, extensions={...})` 显式开启才生效（见 `EXTENSIONS_DEFAULT`）。

## 骨架验证了什么（概念层）

1. **8步状态机流转**：S1→S2→S2.5→S3→S4→S5→S6→S7→S8，每步 handler 先执行、gate 后验收。
2. **门控收敛**：每步有明确通过/失败分支，无静默失败。
3. **回退死锁保护**：S2.5 根本性错误→回退 S2 重跑（≤1次）；S5 critical→回退 S4（≤1次）。
4. **全局最短路径**：degradation + rollback 合计 ≥3 → 跳过可选步骤（圆桌/交叉验证）。
5. **交付包完整性**：7件齐全 / 必填字段（点路径）/ 引用闭环 / CONS_01 件间一致性 / sha256 快照哈希链（UTF-8 NFC+LF 规范化）。
6. **非侵入概念映射**：状态机引擎为"冻结骨架"，8 步 handler 经 `register()` 以插件侧车注入。
7. **阶段2能力（01 记忆匣阶段2【能力补齐】）**：
   - 主动澄清（P2-A1）：S1 歧义超阈值输出三问澄清模板，不再静默降级。
   - 交叉验证常态化：矩阵有 ≥2 相关系统即执行 S6，并入 06 件 cross_validation。
   - 按需圆桌：match_confidence=low 时也触发 S2.5。
   - 长文本策略（P2-A3）：超长输入声明三段式处理。
   - 终止输出（P2-B4）：waiting_user 状态输出 原始输入+DNA草稿+终止确认。
8. **阶段3能力（01 记忆匣阶段3【扩展开关】）**：
   - 动力学等价杂交：`phase3_dynamics_hybrid` 开启时 hybrid_depth=dynamics，强制公理自洽检查+圆桌评审；未通过自动降级结构杂交。
   - 系统关系网络：`phase3_relation_network` 开启时 S8 登记 validates/validated_by。
   - 系统自动编排：`_concept_orchestrate()` 概念编排器输出调用链方案。
   - 默认关闭铁律：`EXTENSIONS_DEFAULT` 全 False，`--test phase3` 场景 G 验证。
9. **阶段4能力（01 记忆匣阶段4【递归闭环】）**：
   - 矩阵读取：`matrix_load_system()` 从系统矩阵加载已归档系统作为迭代原型。
   - 递归输入包装：`wrap_legacy_system()` 标记 `input_type: legacy_system_iteration`。
   - 进化价值判定：`evaluate_evolution_value()` 三维度（范式相似度/约束变更/哈希变更）≥2 判定有效进化，否则 redundant_iteration 终止。
   - 版本溯源：有效进化写入新版本，`evolves_from` 溯源边，旧版本保留不覆盖。
   - 深度保护：`MAX_RECURSION_DEPTH=3` 硬上限，防无限递归。
   - 默认关闭铁律：`phase4_recursive_loop` 默认 False。

## 与设计文档的对应

| 骨架元素 | 设计文档 |
|----------|---------|
| `PipelineStateMachine` | docs/10 第 4 部分（八步状态机 + 全局保护） |
| `PIPELINE_STATE` | docs/10 4.1 节 |
| `IntegrityChecker` | docs/10 5.5 节（含 P0 修复 C4、P1 修复 C3） |
| `demo_input()` 案例 | docs/11（跨语言文献综述辅助系统） |
| `_test_phase2()` | docs/10 阶段2定义 + docs/11（阶段2能力推演） |
