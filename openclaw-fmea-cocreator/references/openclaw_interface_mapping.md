# OpenClaw Interface Mapping

Use this reference when turning the current skill into an OpenClaw workflow, form, or structured backend task.

The goal is to keep one clear contract between:

- OpenClaw input fields
- the skill's internal drafting steps
- the generated Excel workbook
- the optional JSON companion payload
- the optional imported existing FMEA workbook

Implementation artifacts in this directory:

- `openclaw_form_definition.json`: machine-readable field definition for the form
- `openclaw_submission_examples.json`: example payloads for auto-scope and manual-scope submission
- `openclaw_review_cards_schema.json`: machine-readable review card contract for OpenClaw front-end rendering
- `openclaw_review_action_protocol.json`: machine-readable mutation contract for writing review decisions back
- `openclaw_review_action_examples.json`: sample review writeback bundles for testing

## 1. Current delivery shape

The current skill is best understood as:

1. OpenClaw collects a task request
2. the skill normalizes the request and drafts FMEA content
3. the skill returns one `.xlsx` workbook as the primary artifact
4. Markdown is used as review preview
5. JSON is used as a structured companion payload for automation or downstream systems
6. review cards JSON can be used as the in-product card rendering payload for `确认队列` and `Top风险`
7. when an existing workbook is provided, the skill first normalizes that workbook into the same Excel/JSON/cards contract

Primary script:

```bash
python3 scripts/draft_fmea_from_cases.py --module "模块名" --input-file /path/to/input.txt --excel-out /path/to/output.xlsx
```

Current OpenClaw bridge:

```bash
python3 scripts/run_openclaw_submission.py --payload-file /path/to/payload.json
```

Current card builder:

```bash
python3 scripts/build_openclaw_review_cards.py --input-json /path/to/draft.json --output-json /path/to/cards.json
```

Current review writeback executor:

```bash
python3 scripts/apply_openclaw_review_actions.py --input-json /path/to/draft.json --actions-json /path/to/review_actions.json
```

Existing workbook import helper:

```bash
python3 scripts/import_existing_fmea_excel.py --input-excel /path/to/existing.xlsx --excel-out /path/to/normalized.xlsx --json-out /path/to/normalized.json
```

## 2. OpenClaw entry intents

OpenClaw should expose these entry intents:

| Intent id | User-facing meaning | Current support |
| --- | --- | --- |
| `new_fmea_draft` | 从模块描述共创首版 FMEA | yes |
| `review_existing_fmea` | 对已有 FMEA 做补全或审查 | yes, workbook import path now supported |
| `high_risk_review` | 聚焦高 RPN 和建议动作 | yes, can be driven from imported workbook or draft JSON |
| `case_library_extract` | 把确认后的条目沉淀为案例 | partial, workflow defined but artifact path still to be built |

For the current implementation, OpenClaw should default to `new_fmea_draft`.

## 3. Input contract

### 3.1 Top-level fields

These are the recommended OpenClaw input fields.

| Field id | Label | Type | Required | Notes |
| --- | --- | --- | --- | --- |
| `intent` | 任务类型 | enum | yes | `new_fmea_draft`, `review_existing_fmea`, `high_risk_review`, `case_library_extract` |
| `project_name` | 项目/产品名称 | string | recommended | goes to workbook overview |
| `module_name` | 模块/分析对象名称 | string | yes | maps to script `--module` |
| `fmea_type` | FMEA 类型 | enum | yes | `AFMEA`, `SFMEA`, `DFMEA`, `PFMEA` |
| `function_description` | 功能/要求描述 | long text | yes | core drafting input |
| `use_scenario` | 使用场景/任务场景 | long text | yes | required for AFMEA/SFMEA/DFMEA/PFMEA context |
| `scope_mode` | scope 方式 | enum | yes | `auto` or `manual` |
| `scope_notes` | scope 补充说明 | long text | optional | useful when the user knows boundaries but not exact scope keywords |
| `environment` | 环境与工况 | long text | optional | temperature, EMC, vibration, pressure, fluid, etc. |
| `interfaces` | 接口信息 | long text | optional | structure, signal, energy, fluid, motion |
| `design_constraints` | 设计约束 | long text | optional | weight, tolerance, safety, EMC, cost, material, regulation |
| `historical_issues` | 历史问题/投诉/维修 | long text | optional | strong retrieval signal |
| `current_controls` | 当前控制/检测/联锁 | long text | optional | used for `D` and action suggestions |
| `bom_or_key_parts` | BOM/关键部件 | long text | optional | especially useful for DFMEA |
| `customer_impact` | 客户或后工序影响 | long text | optional | helps severity drafting |
| `attachments_summary` | 附件摘要 | long text | optional | if OpenClaw later supports file upload, summarize extracted content here |
| `existing_fmea_text` | 已有 FMEA 内容 | long text | optional | for review mode |
| `existing_fmea_excel_path` | 已有 FMEA Excel 路径 | string | optional | local or mounted workbook path for import-first review mode |
| `requested_output_name` | 输出文件名 | string | optional | default can be auto-generated |

### 3.2 Manual scope fields

If `scope_mode = manual`, OpenClaw should allow repeated child items:

| Field id | Label | Type | Required | Notes |
| --- | --- | --- | --- | --- |
| `scopes[].name` | scope 名称 | string | yes | becomes sheet grouping basis |
| `scopes[].keywords` | scope 关键词 | string list or long text | yes | used to build `--scope "名称::关键词..."` |
| `scopes[].notes` | scope 说明 | long text | optional | not currently consumed by script, but useful for UI and future logic |

### 3.3 Minimum viable input

If the user only gives a minimal package, OpenClaw should still allow the run when these are present:

- `module_name`
- `fmea_type`
- `function_description`
- `use_scenario`
- at least one of:
  - `environment`
  - `interfaces`
  - `design_constraints`
  - `historical_issues`
  - `bom_or_key_parts`

If these are not met, OpenClaw should not block forever. It should ask for missing critical fields first, then allow the skill to continue with explicit assumptions.

For `review_existing_fmea` or `high_risk_review`, OpenClaw may also allow a lighter package:

- `existing_fmea_excel_path`
- optional `module_name`
- optional `fmea_type`

If `module_name` or `fmea_type` is omitted, the importer will try to recover them from the workbook `封面` sheet first, then from the legacy `概览` sheet.

## 4. Interaction contract

The current skill should interact in these rounds.

### Round 1: task framing

OpenClaw sends the collected fields to the skill.

The skill should:

- identify `AFMEA`, `SFMEA`, `DFMEA`, or `PFMEA`
- decide whether the request is a new draft or a review-like task
- detect whether scope split is needed

### Round 2: scope decision

If `scope_mode = auto`, the skill:

- suggests scopes from module profile and input text
- records them in the workbook `FMEA主表` column `生命周期维度`

If `scope_mode = manual`, the skill:

- uses the provided child scopes directly
- still flags weak or boundary rows later if scope ownership is ambiguous

### Round 3: drafting

The skill:

- normalizes module names
- retrieves historical cases
- drafts per-scope FMEA rows
- marks `Reference type`
- marks `Confirmation status`
- builds confirmation queue and suggested actions

If `existing_fmea_excel_path` is present instead of a raw-description path, this round becomes:

- import the workbook
- detect `FMEA主表` or legacy scope sheets and normalized headers
- preserve existing review/trace details when available
- rebuild the standard Excel/JSON/cards contract

### Round 4: delivery

The skill returns:

- one Excel workbook
- optional Markdown preview
- optional JSON payload

### Round 5: human confirmation

OpenClaw should allow the user to:

- review the JSON/card-based confirmation queue
- adjust scope ownership
- confirm or overwrite `S/O/D`
- fill `Owner` and `Target date`
- decide which rows should enter a case library later

### Round 6: review writeback

Once OpenClaw collects the clicked review actions, it should:

- assemble them with the `openclaw_review_action_protocol.json` contract
- execute `scripts/apply_openclaw_review_actions.py`
- replace or version the workbook with the reviewed `.xlsx`
- refresh the review cards from the reviewed `.json`

## 5. Input-to-workbook mapping

### 5.1 Workbook `封面`

| Workbook cell group | Source |
| --- | --- |
| report title | `module_name` + `fmea_type` |
| `产品型号` | `module_name` |
| `核心指标` | merged input summary from function, scenario, environment, interfaces, constraints, historical issues, BOM |
| `分析维度` | auto/manual scope names |
| `分析日期` | generation date |

### 5.2 Workbook `FMEA主表`

All scopes are written into one template-styled worksheet. Scope ownership is preserved in `生命周期维度` rather than separate worksheets.
The standard workbook format uses worksheet `FMEA主表`, headers in `B2:W2`, data rows from row `3`, current `RPN` formula in column `O`, and post-action `改进后RPN` formula in column `W`.

| Worksheet column | Source |
| --- | --- |
| `序号` | generated row number |
| `生命周期维度` | derived scope name |
| `模块/零件` | drafted or retrieved analysis object |
| `功能及要求` | drafted or retrieved function / requirement |
| `参数指标性能` | blank unless a concrete parameter is available |
| `失效影响（后果）` | drafted or retrieved failure effect |
| `严重度 S` | drafted or inherited |
| `潜在失效模式` | drafted or retrieved failure mode |
| `失效原因` | drafted or retrieved cause / mechanism |
| `现行预防措施` | drafted or retrieved current controls |
| `频度 O` | drafted or inherited |
| `现行探测控制` | drafted or retrieved current controls when prevention/detection are not separated |
| `探测度 D` | drafted or inherited |
| `RPN` | inherited or computed |
| `AI打分推导依据` | generated S/O/D basis plus confirmation status, reference type, review comments, and source trace |
| `建议措施` | drafted or inherited recommended actions |
| `措施负责人` | current owner or blank |
| `完成时间` | current target date or blank |
| `改进后S/O/D/RPN` | blank unless reassessment values are provided |

When imported from an existing workbook, the source trace should prepend:

- `{imported_workbook_name} / {sheet_name} / row {row_number}`

### 5.3 Workbook `评分准则参考`

This sheet is copied from the standard template unchanged and should remain available for expert scoring review.

## 6. OpenClaw field-to-script mapping

For the current implementation, OpenClaw can map its fields to the script like this:

| OpenClaw field | Script mapping |
| --- | --- |
| `module_name` | `--module` when drafting, optional `--module` override when importing |
| merged long-text fields | merged into one `--input-file` or `--input-text` body |
| `existing_fmea_excel_path` | `--input-excel` |
| `scope_mode = auto` | omit `--scope` |
| `scope_mode = manual` | repeat `--scope "名称::关键词..."` |
| output path | `--excel-out` |
| optional preview path | `--markdown-out` |
| optional machine payload path | `--json-out` |

Recommended merged input body order:

1. project and module
2. function description
3. use scenario
4. environment
5. interfaces
6. design constraints
7. historical issues
8. current controls
9. BOM or key parts
10. customer impact
11. attachments summary

## 7. Enum contract

### 7.1 `fmea_type`

- `AFMEA`
- `SFMEA`
- `DFMEA`
- `PFMEA`

### 7.2 `scope_mode`

- `auto`
- `manual`

### 7.3 `confirmation_status`

- `draft`
- `needs expert confirmation`
- `confirmed`

### 7.4 `reference_type`

- `current module`
- `direct family reference`
- `broader analogy`

## 8. Current implementation limits

OpenClaw should know these current limits:

1. primary supported paths are `new_fmea_draft` and workbook-based `review_existing_fmea`
2. existing FMEA import currently expects one workbook path, not a raw uploaded binary stream in memory
3. `Owner` and `Target date` are structurally supported, but usually remain blank until human review
4. `O` and `D` must not be treated as enterprise-final unless the user explicitly confirms them
5. current workbook column names are mostly English normalized labels

If enterprise delivery later requires a Chinese workbook template, add a display-layer column alias map rather than changing the underlying contract first.

## 9. Recommended next implementation step

The next OpenClaw development step should be:

1. build a form using the top-level fields above
2. merge them into one drafting payload
3. run the current script to generate the workbook
4. return the `.xlsx` as the primary artifact
5. optionally render `确认队列` and `Top风险` as OpenClaw cards for in-product review
