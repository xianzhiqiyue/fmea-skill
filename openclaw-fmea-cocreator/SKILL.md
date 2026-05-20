---
name: openclaw-fmea-cocreator
version: 0.3.1
description: Co-create AFMEA, SFMEA, DFMEA, or PFMEA for OpenClaw from module inputs, existing tables, or historical quality materials, with traceable drafts and follow-up actions.
category: research
tags:
  - analysis
  - workflow
  - prompting
---

# OpenClaw FMEA Co-creator

Use this skill when the user wants to build, review, or refine FMEA collaboratively rather than just generate a one-off table.

This skill is designed around the materials in the current project:

- historical DFMEA examples under `excel_materials/workbooks/CAN400产品DFMEA/`
- AI-FMEA planning, prompt templates, and case templates under `excel_materials/workbooks/AI质量赋能/`

For OpenClaw delivery, prefer a reviewable Excel workbook over a raw spreadsheet dump.

## What this skill does

This skill helps Codex:

1. classify the task as `AFMEA`, `SFMEA`, `DFMEA`, or `PFMEA`
2. collect missing inputs in a structured way
3. retrieve similar historical failure cases
4. coordinate a small multi-specialist agent cluster when the scope needs multiple expert viewpoints
5. diagnose input quality before drafting so weak inputs do not produce false confidence
6. draft a normalized FMEA table
7. review lifecycle/interface/component coverage for likely gaps
8. run a quality gate for FMEA type boundaries, engineering self-consistency, Poka-Yoke actionability, and Excel formatting readiness
9. convert important uncertainty into plain-language validation questions for non-expert users
10. separate AI suggestions from human-confirmed judgments
11. output both the FMEA table and a follow-up action list

## Completeness floor

默认输出必须是**覆盖型草稿**,不是少量示例行。除非用户明确要求"只看 Top 风险"或"快速示例",否则:

- OpenClaw-ready 或 Excel 草稿不得少于 20 条 FMEA 行;DFMEA/PFMEA 宽范围草稿应优先达到脚本默认行数
- 每个 scope/lifecycle/process group 至少保留 4 条可审阅行;历史案例不足时,用覆盖补缺行补齐,并标为 `needs expert confirmation`
- 同一叶节点或同一工序不要只给 1 个泛化失效模式;应按 guidewords 展开不同机理: 功能丧失、功能退化、间歇性、非预期功能、错误输出/误判、接口失配、环境应力、老化/磨损、误操作、检验逃逸
- 允许低证据 AI 草稿存在,但必须显式标记证据等级、假设、待确认问题和专家复核焦点;不能因为证据少就少输出

## Core workflow

新工作流由 7 个强制阶段构成,Claude 必须按顺序执行,不可跳步。

### 阶段 1: 结构化抽取 (P-Diagram + 模块层级树)

在生成任何 FMEA 行之前,先按 [references/p_diagram_template.md](references/p_diagram_template.md) 抽出 `structure.json`:

- `hierarchy` 模块层级树
- `p_diagrams[]` 每个子系统一份 P-Diagram

输出必须通过 schema 自检(详见 reference)。如果用户输入不足,列出缺失字段并要求补充,不要伪造。

同时记录输入质量诊断,至少检查:

- 模块或分析对象
- 关键功能或要求
- 使用场景或生命周期阶段
- 环境和应用应力
- 结构、信号、能量、流体、运动、数据或控制接口
- BOM、关键件、材料或设计约束
- 现行预防控制、探测控制、测试、报警或联锁
- 历史故障、维修、投诉或相似 FMEA 行
- 客户影响或后工序影响
- `S/O/D` 评分证据

将输入质量标为 `strong`、`usable_with_assumptions` 或 `high_risk_missing_context`。缺口要转成具体、可回答的验证问题,不要只要求用户"补充更多信息"。

FMEA 类型边界必须保留:

- `AFMEA`: 应用生命周期、使用场景、运输、安装、操作、维护和现场控制点
- `SFMEA`: 系统、子系统、接口、功能链、能量/物料/信息流和系统状态
- `DFMEA`: 设计对象、零件、部件、材料、连接件、传感器/执行器、PCBA 和控制接口
- `PFMEA`: 制造、装配、测试、检验、包装、放行等过程步骤和控制计划

### 阶段 2: 多专家失效模式生成 (6 个角色)

按 [references/specialist_role_prompts.md](references/specialist_role_prompts.md) 依次扮演 6 个专家角色:

1. 系统/接口工程师
2. 设计/模块工程师
3. 可靠性/试验工程师
4. 制造/工艺工程师
5. 安全/服务工程师
6. 软件/控制工程师 (条件触发)

每个角色独立,只看 `structure.json`,不看其他角色已产出。每个角色对 hierarchy 每个叶节点扫遍"必扫描轴对",输出 `candidates_{role}.json`。

**强制约束**: 不能静默跳过任何 (叶节点 × 必扫描轴对) 组合。不适用即给 `not_applicable_reason`。适用组合不能只产出一个笼统风险;应至少尝试从 2 个不同失效类别展开候选行,直到该叶节点已覆盖主要功能、接口、控制、环境、寿命和误用风险。

### 阶段 3: 历史证据池

对 hierarchy 每个叶节点跑一次 `retrieve_cases.py`:

```bash
python3 openclaw-fmea-cocreator/scripts/retrieve_cases.py \
  --query "<leaf_name + 上下文关键词>" \
  --module "<module_root>" \
  --case-library-root case_library/ \
  --json-out evidence_pool/<leaf_id>.json
```

输出 `evidence_pool/<leaf_id>.json` 固定 schema,M2 起由 `merge_and_score.py` 直接消费。

### 阶段 4: 合并、去重、评级、置信度

按 [references/deduplication_protocol.md](references/deduplication_protocol.md) 与 [references/evidence_grading.md](references/evidence_grading.md):

1. 跨 scope 机械去重 (主键 = `leaf_id` × `failure_mode_canonical`)
2. scope 内语义去重 (LLM 仲裁,触发条件: 同 leaf 下 candidate ≥ 2)
3. 合并候选行 (S/O/D 取最大值,rationale 全留)
4. 与历史证据对齐,判定 5 状态 `evidence_grade`
5. 计算 4 分量 `confidence`
6. 覆盖率检查,输出 `coverage_gaps.json`

由 `merge_and_score.py` 脚本承担,Claude 只做最后审阅。

审阅时把低证据、低置信度、覆盖缺口、输入质量缺口和 `O/D` 不确定项显式送入确认队列。确认项应包含普通用户能回答的问题、默认 AI 假设、答案错误时的影响,以及专家评审焦点。

### 阶段 5: 硬核质量门禁

按 [references/fmea_quality_gate.md](references/fmea_quality_gate.md) 审查草稿,至少覆盖:

- 四类 FMEA 防串台: AFMEA 看操作流,SFMEA 看接口/边界,DFMEA 看设计物理极限,PFMEA 看工序/工装/检验/放行
- 工程物理自洽: 对象、功能、失效模式、影响、原因、现行控制、建议措施必须能闭环
- 现场痛点与防呆: 建议措施必须能落到 BOM、图纸、工装、SOP、控制计划、测试或 OpenClaw 评审动作,不得只写"加强培训/检查/优化设计"
- Excel 输出格式: 表头、序号列、文本列、评分列和多级编号必须满足门禁

质量门禁发现必须进入 JSON/Markdown companion 的 `quality_gate_findings`; 对影响 FMEA 类型归属、物理机理或措施可执行性的发现,同步转入确认队列。

### 阶段 6: 工作簿渲染

```bash
python3 openclaw-fmea-cocreator/scripts/build_workbook.py \
  --normalized fmea_normalized.json \
  --structure structure.json \
  --output 输出.xlsx
```

输出工作簿包含 5 个 sheet:

- `封面` (含证据等级分布、置信度分布、覆盖摘要)
- `FMEA主表` (31 列,含 P-Diagram 锚点、证据等级、置信度等新列)
- `评分准则参考`
- `覆盖盲区与待确认队列`
- `结构与P-Diagram`

### 阶段 7: 评审写回与案例库飞轮 (M3)

完成 `fmea_normalized.json` 与工作簿后,把人工评审与回流闭环:

1. 用 `scripts/build_openclaw_review_cards.py` 从 `fmea_normalized.json` 生成 OpenClaw 评审卡
   ```bash
   python3 scripts/build_openclaw_review_cards.py \
     --input-json /path/to/fmea_normalized.json \
     --output-json /path/to/cards.json
   ```
2. 评审者通过 OpenClaw 产生 `review_actions.json` (5 种动作: confirm/edit/reject/defer/promote_to_case),协议见 [`references/openclaw_review_action_protocol.json`](references/openclaw_review_action_protocol.json)。
3. 用 `scripts/apply_openclaw_review_actions.py` 把动作应用到 normalized JSON
   ```bash
   python3 scripts/apply_openclaw_review_actions.py \
     --input-json /path/to/fmea_normalized.json \
     --actions-json /path/to/review_actions.json \
     --output-json /path/to/fmea_normalized.review_applied.json
   ```
4. 用 `scripts/confirmed_to_case_library.py` 把"已确认 + 高证据等级"或"`promote_to_case`"的行回流到 `case_library/<module>/<YYYY-Q*>.json`
   ```bash
   python3 scripts/confirmed_to_case_library.py \
     --input-json /path/to/fmea_normalized.review_applied.json \
     --case-library-root case_library/ \
     --source-fmea-path /path/to/fmea_normalized.json
   ```
5. 下一次跑 `retrieve_cases.py` 时加 `--case-library-root case_library/`,本企业历史案例命中权重自动 × 1.5,优先级高于通用历史案例。

**回流条件 (避免 echo chamber)**:

- `review_status == "promoted"` (`promote_to_case` 动作) - 无条件回流
- `review_status == "confirmed"` 且 `evidence_grade ∈ {evidence-backed, historical-supported}` - 回流
- 其他情况 (`confirmed + ai-inferred` / `rejected` / `deferred`) - 不回流

## OpenClaw delivery contract

When this skill is used as an OpenClaw workflow building block, the default output should be a compact package with these parts:

1. `Scope split`
2. `Input quality diagnosis`
3. `Coverage matrix review`
4. `Quality gate findings`
5. `FMEA draft`
6. `Rows needing confirmation`
7. `Top risks`
8. `Suggested actions`
9. `Source trace`

Minimum delivery rules:

- generate the primary workbook from the bundled `template.xlsx`; repo-local development may use a root `template.xlsx` only as a fallback
- treat the sample workbook only as a format reference: preserve sheet names, column positions, formulas, merged cells, widths, row styles, and the scoring reference sheet, but not sample-specific content
- keep the workbook sheet set and visual style aligned with the standard template (`封面`, `FMEA主表`, `评分准则参考`)
- write all FMEA rows into `FMEA主表`; use `生命周期维度` to preserve scope/lifecycle grouping
- preserve the template `评分准则参考` worksheet exactly as the standard template provides it; use [references/scoring_guardrails.md](references/scoring_guardrails.md) for draft scoring rationale, not for rewriting that sheet
- when using lifecycle coverage, derive grouping and row count from the user's module/input; do not hardcode sample workbook dimensions or row distribution as template requirements
- keep draft volume reviewable but complete: default workbook drafts should normally exceed 20 rows, and broad DFMEA/PFMEA drafts should not collapse to only a few rows just because historical cases are sparse
- for broad or OpenClaw-ready FMEA drafts, use a multi-specialist agent cluster when available; if subagents are unavailable, simulate the same role passes sequentially and label which professional viewpoint produced each cluster of risks
- label each row as `current module`, `direct family reference`, or `broader analogy`
- keep `O` and `D` in `draft` state unless the user or source gave enough enterprise evidence
- call out boundary rows whose scope ownership is ambiguous
- include input quality and coverage review in JSON/Markdown companions so weak inputs do not look complete
- include quality gate findings for type-boundary, physics/self-consistency, actionability, and formatting issues before final signoff
- write plain-language validation prompts for non-expert users whenever assumptions materially affect scope, `O/D`, controls, or action priority
- preserve historical traceability in the `AI打分推导依据` cell whenever a historical row influenced the draft
- keep Markdown or JSON only as preview or system interface companions when useful

### M1 新增交付规则

- 每行必须有 `evidence_grade ∈ {evidence-backed, historical-supported, multi-role-inferred, ai-inferred, contradicted}`,见 [references/evidence_grading.md](references/evidence_grading.md)
- 每行必须有 `confidence ∈ [0,1]`,以及 4 分量明细
- 每行必须有 `p_diagram_anchor` 字符串,指明该行来自 P-Diagram 哪个组合
- `top_risks` 按 `confidence × rpn` 排序,不再按纯 rpn
- `confirmation_queue` 自动包含 `evidence_grade ∈ {contradicted, ai-inferred}` 或 `confidence < 0.5` 的行

## Output expectations

For most requests, return these sections when useful:

1. `FMEA draft`
2. `Rows needing confirmation`
3. `Top risks`
4. `Suggested actions`
5. `Quality gate findings`

If the user only asks for one of these, keep the response scoped.

If the user asks for an OpenClaw-ready result, follow the full delivery contract above and the field rules in [references/output_schema.md](references/output_schema.md).

If the task is about in-product review cards for `确认队列` or `Top风险`, see `references/openclaw_review_cards_schema.json` and `scripts/build_openclaw_review_cards.py` (M3).
If the task is about writing human review decisions back into the FMEA, see `references/openclaw_review_action_protocol.json`, `references/openclaw_review_action_examples.json`, and `scripts/apply_openclaw_review_actions.py` (M3).
If the task starts from an existing FMEA workbook instead of raw text, also use `scripts/import_existing_fmea_excel.py`.

Current script support:

```bash
python3 openclaw-fmea-cocreator/scripts/draft_fmea_from_cases.py \
  --module "模块名" \
  --fmea-type PFMEA \
  --input-file /path/to/input.txt \
  --excel-out /path/to/output.xlsx

python3 openclaw-fmea-cocreator/scripts/merge_and_score.py \
  --structure structure.json \
  --candidates-dir <dir> \
  --evidence-pool-dir <dir>/evidence_pool \
  --output fmea_normalized.json

python3 openclaw-fmea-cocreator/scripts/build_workbook.py \
  --normalized fmea_normalized.json \
  --structure structure.json \
  --output 输出.xlsx
```

OpenClaw bridge support:

```bash
python3 scripts/run_openclaw_submission.py --payload-file /path/to/payload.json
python3 scripts/run_openclaw_submission.py --example-name auto_scope_pfmea_module_assembly --dry-run --print-input
python3 scripts/build_openclaw_review_cards.py --input-json /path/to/draft.json --output-json /path/to/cards.json
python3 scripts/apply_openclaw_review_actions.py --input-json /path/to/draft.json --actions-json /path/to/review_actions.json
python3 scripts/import_existing_fmea_excel.py --input-excel /path/to/existing.xlsx --excel-out /path/to/normalized.xlsx --json-out /path/to/normalized.json
```

## When to read which reference

- `references/p_diagram_template.md`: 每次生成 FMEA 前都要读,定义结构化抽取范式
- `references/specialist_role_prompts.md`: 阶段 2 多专家轮次的 prompt 卡
- `references/deduplication_protocol.md`: 跨 scope 与 scope 内去重协议
- `references/evidence_grading.md`: 证据等级与置信度公式
- `references/fmea_quality_gate.md`: 每次交付前读取,用于防串台、工程物理自洽、防呆措施和 Excel 格式门禁
- `references/workflow.md`: when you need the full co-creation workflow
- `references/output_schema.md`: when generating or normalizing tables
- `references/openclaw_review_cards_schema.json` (M3): when rendering `确认队列` and `Top风险` as OpenClaw cards
- `references/openclaw_review_action_protocol.json` (M3): when frontend review actions need a writeback contract
- `references/openclaw_review_action_examples.json` (M3): when testing or mocking review writeback payloads
- `references/prompt_templates.md`: when constructing prompts or choosing AFMEA/SFMEA/DFMEA/PFMEA framing
- `references/openclaw_form_definition.json`: when building the actual OpenClaw form config
- `references/openclaw_interface_mapping.md`: when mapping OpenClaw fields to script inputs, workbook sheets, or structured payloads
- `references/openclaw_submission_examples.json`: when preparing request payloads or testing submission shape
- `references/openclaw_submission_assembly.md`: when wiring backend payload assembly or executing the bridge script
- `references/scoring_guardrails.md`: whenever assigning or reviewing S/O/D

## Guardrails

- Do not pretend the AI knows enterprise-specific scoring rules if they were not provided.
- Do not hide uncertainty around `O` and `D`.
- Do not collapse customer impact and downstream-process impact into one vague sentence if the source separates them.
- Do not overwrite user-provided ratings without explaining why.
- Do not cite a historical case without naming the source workbook and sheet when practical.
- Do not let cross-module analogies dominate a scope that is already well covered by current-module cases.
- Do not merge boundary rows into one scope silently when ownership is debatable.
- Do not mix PFMEA process-step causes into DFMEA design rows, or DFMEA design mechanisms into PFMEA rows; move cross-type risks into confirmation/follow-up instead.

## Preferred style

- collaborative, not authoritative
- structured, not verbose
- explicit about assumptions
- easy to turn into an OpenClaw workflow or future structured tool
