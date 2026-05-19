---
name: openclaw-fmea-cocreator
version: 0.3.0-m2
description: Co-create AFMEA, SFMEA, or DFMEA for OpenClaw from module inputs, existing tables, or historical quality materials, with traceable drafts and follow-up actions.
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

1. classify the task as `AFMEA`, `SFMEA`, or `DFMEA`
2. collect missing inputs in a structured way
3. retrieve similar historical failure cases
4. coordinate a small multi-specialist agent cluster when the scope needs multiple expert viewpoints
5. draft a normalized FMEA table
6. separate AI suggestions from human-confirmed judgments
7. output both the FMEA table and a follow-up action list

## Core workflow

新工作流由 6 个强制阶段构成,Claude 必须按顺序执行,不可跳步。

### 阶段 1: 结构化抽取 (P-Diagram + 模块层级树)

在生成任何 FMEA 行之前,先按 [references/p_diagram_template.md](references/p_diagram_template.md) 抽出 `structure.json`:

- `hierarchy` 模块层级树
- `p_diagrams[]` 每个子系统一份 P-Diagram

输出必须通过 schema 自检(详见 reference)。如果用户输入不足,列出缺失字段并要求补充,不要伪造。

### 阶段 2: 多专家失效模式生成 (6 个角色)

按 [references/specialist_role_prompts.md](references/specialist_role_prompts.md) 依次扮演 6 个专家角色:

1. 系统/接口工程师
2. 设计/模块工程师
3. 可靠性/试验工程师
4. 制造/工艺工程师
5. 安全/服务工程师
6. 软件/控制工程师 (条件触发)

每个角色独立,只看 `structure.json`,不看其他角色已产出。每个角色对 hierarchy 每个叶节点扫遍"必扫描轴对",输出 `candidates_{role}.json`。

**强制约束**: 不能静默跳过任何 (叶节点 × 必扫描轴对) 组合。不适用即给 `not_applicable_reason`。

### 阶段 3: 历史证据池

对 hierarchy 每个叶节点跑一次 `retrieve_cases.py`:

```bash
python3 openclaw-fmea-cocreator/scripts/retrieve_cases.py \
  --query "<leaf_name + 上下文关键词>" \
  --module "<module_root>" \
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

### 阶段 5: 工作簿渲染

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

### 阶段 6: 评审写回 (M3)

M1/M2 不实现。M3 落地 `confirmed_to_case_library.py` 实现案例库飞轮。

## OpenClaw delivery contract

When this skill is used as an OpenClaw workflow building block, the default output should be a compact package with these parts:

1. `Scope split`
2. `FMEA draft`
3. `Rows needing confirmation`
4. `Top risks`
5. `Suggested actions`
6. `Source trace`

Minimum delivery rules:

- generate the primary workbook from the bundled `template.xlsx`; repo-local development may use a root `template.xlsx` only as a fallback
- treat the sample workbook only as a format reference: preserve sheet names, column positions, formulas, merged cells, widths, row styles, and the scoring reference sheet, but not sample-specific content
- keep the workbook sheet set and visual style aligned with the standard template (`封面`, `FMEA主表`, `评分准则参考`)
- write all FMEA rows into `FMEA主表`; use `生命周期维度` to preserve scope/lifecycle grouping
- preserve the template `评分准则参考` worksheet exactly as the standard template provides it; use [references/scoring_guardrails.md](references/scoring_guardrails.md) for draft scoring rationale, not for rewriting that sheet
- when using lifecycle coverage, derive grouping and row count from the user's module/input; do not hardcode sample workbook dimensions or row distribution as template requirements
- for broad or OpenClaw-ready FMEA drafts, use a multi-specialist agent cluster when available; if subagents are unavailable, simulate the same role passes sequentially and label which professional viewpoint produced each cluster of risks
- label each row as `current module`, `direct family reference`, or `broader analogy`
- keep `O` and `D` in `draft` state unless the user or source gave enough enterprise evidence
- call out boundary rows whose scope ownership is ambiguous
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

If the user only asks for one of these, keep the response scoped.

If the user asks for an OpenClaw-ready result, follow the full delivery contract above and the field rules in [references/output_schema.md](references/output_schema.md).

If the task is about in-product review cards for `确认队列` or `Top风险`, see `references/openclaw_review_cards_schema.json` and `scripts/build_openclaw_review_cards.py` (M3).
If the task is about writing human review decisions back into the FMEA, see `references/openclaw_review_action_protocol.json`, `references/openclaw_review_action_examples.json`, and `scripts/apply_openclaw_review_actions.py` (M3).
If the task starts from an existing FMEA workbook instead of raw text, also use `scripts/import_existing_fmea_excel.py`.

Current script support:

```bash
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
python3 scripts/build_openclaw_review_cards.py --input-json /path/to/draft.json --output-json /path/to/cards.json
python3 scripts/apply_openclaw_review_actions.py --input-json /path/to/draft.json --actions-json /path/to/review_actions.json
python3 scripts/import_existing_fmea_excel.py --input-excel /path/to/existing.xlsx --excel-out /path/to/normalized.xlsx --json-out /path/to/normalized.json
```

## When to read which reference

- `references/p_diagram_template.md`: 每次生成 FMEA 前都要读,定义结构化抽取范式
- `references/specialist_role_prompts.md`: 阶段 2 多专家轮次的 prompt 卡
- `references/deduplication_protocol.md`: 跨 scope 与 scope 内去重协议
- `references/evidence_grading.md`: 证据等级与置信度公式
- `references/workflow.md`: when you need the full co-creation workflow
- `references/output_schema.md`: when generating or normalizing tables
- `references/openclaw_review_cards_schema.json` (M3): when rendering `确认队列` and `Top风险` as OpenClaw cards
- `references/openclaw_review_action_protocol.json` (M3): when frontend review actions need a writeback contract
- `references/openclaw_review_action_examples.json` (M3): when testing or mocking review writeback payloads
- `references/prompt_templates.md`: when constructing prompts or choosing AFMEA/SFMEA/DFMEA framing
- `references/scoring_guardrails.md`: whenever assigning or reviewing S/O/D

## Guardrails

- Do not pretend the AI knows enterprise-specific scoring rules if they were not provided.
- Do not hide uncertainty around `O` and `D`.
- Do not collapse customer impact and downstream-process impact into one vague sentence if the source separates them.
- Do not overwrite user-provided ratings without explaining why.
- Do not cite a historical case without naming the source workbook and sheet when practical.
- Do not let cross-module analogies dominate a scope that is already well covered by current-module cases.
- Do not merge boundary rows into one scope silently when ownership is debatable.

## Preferred style

- collaborative, not authoritative
- structured, not verbose
- explicit about assumptions
- easy to turn into an OpenClaw workflow or future structured tool
