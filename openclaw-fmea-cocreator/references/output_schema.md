# Output Schema

Use this normalized schema for most FMEA drafts and reviews.

For OpenClaw delivery, the primary artifact is a stable Excel workbook generated from the bundled `template.xlsx`.
The repository sample workbook is a format reference only; its product-specific content is not part of the template contract.
The generated workbook should preserve the standard template's sheet names, column positions, row styling, merged cells, column widths, formulas, and scoring reference sheet.
Companion Markdown/JSON artifacts can still carry review queues and machine-readable details when requested.

The companion payload should still be made of:

1. `Scope split`
2. `Input quality diagnosis`
3. `Coverage matrix review`
4. `FMEA draft`
5. `Rows needing confirmation`
6. `Top risks`
7. `Suggested actions`
8. `Source trace`

## Workbook layout

The default deliverable should be one `.xlsx` workbook with the exact standard-template worksheets:

1. `封面`
2. `FMEA主表`
3. `评分准则参考`

All generated FMEA rows go into `FMEA主表`; use `生命周期维度` for scope/lifecycle grouping instead of creating one worksheet per scope.
`FMEA主表` must keep the standard table position: headers in `B2:W2`, data rows beginning at row `3`, and formulas in `RPN` / `改进后RPN`.
`评分准则参考` must be copied from the standard template without content rewrites so the workbook keeps the template reference structure exactly.

Default rich drafts may use lifecycle-style grouping when the input scope calls for it, but lifecycle names, row counts, module names, product metrics, and risk examples are generated content, not template content.
Rows expanded from lifecycle context should stay traceable and remain `needs expert confirmation`.

## Companion JSON quality fields

The JSON payload may include quality metadata that is not written as separate workbook sheets:

| Field | Required | Notes |
| --- | --- | --- |
| `input_quality_diagnosis.level` | recommended | `strong`, `usable_with_assumptions`, or `high_risk_missing_context` |
| `input_quality_diagnosis.summary` | recommended | short explanation of why the level was assigned |
| `input_quality_diagnosis.signals` | recommended | per-signal status for function, scenario, environment, interfaces, controls, history, and scoring evidence |
| `input_quality_diagnosis.missing_critical_inputs` | recommended | highest-value inputs needed before expert signoff |
| `coverage_matrix` | recommended | list of coverage dimensions with `covered`, `weak`, or `missing` status |
| `coverage_matrix[].review_prompt` | recommended | what reviewers should confirm or supplement |

These fields are review scaffolding. They should not be presented as proof that the FMEA is complete.

## Recommended columns

| Field | Required | Notes |
| --- | --- | --- |
| Scope | yes | required when the parent module is split into multiple subsystems |
| Analysis object | yes | system, subsystem, module, component, or part |
| Function or requirement | yes | what it must do |
| Failure mode | yes | one logical failure mode per row |
| Failure effect | yes | separate customer and downstream impact when possible |
| S | yes | severity |
| Cause or mechanism | yes | why the failure happens |
| O | yes | occurrence |
| Current controls | yes | prevention and detection can be combined if source uses one field |
| D | yes | detection |
| RPN | yes | `S * O * D` |
| Recommended actions | recommended | actions to reduce occurrence or improve detection |
| Post-action S | optional | only when reassessment is requested |
| Post-action O | optional | only when reassessment is requested |
| Post-action D | optional | only when reassessment is requested |
| Post-action RPN | optional | only when reassessment is requested |
| Owner | optional | useful for action tracking |
| Target date | optional | useful for action tracking |
| Confirmation status | recommended | `draft`, `needs expert confirmation`, or `confirmed` |
| Review comment | recommended | short human review notes appended during writeback |
| Rating basis | recommended | short basis text for `S`, `O`, and `D` |
| Reference type | recommended | `current module`, `direct family reference`, or `broader analogy` |
| Source case | recommended | workbook, sheet, and row id when derived from historical examples or imported from an existing workbook |

## Template column mapping

| Normalized field | standard-template column |
| --- | --- |
| Row number | `序号` |
| Scope | `生命周期维度` |
| Analysis object | `模块/零件` |
| Function or requirement | `功能及要求` |
| Parameter indicators | `参数指标性能` |
| Failure effect | `失效影响（后果）` |
| S | `严重度 S` |
| Failure mode | `潜在失效模式` |
| Cause or mechanism | `失效原因` |
| Current controls | `现行预防措施` and `现行探测控制` when source data is combined |
| O | `频度 O` |
| D | `探测度 D` |
| RPN | `RPN` |
| Rating basis / status / reference / source trace | `AI打分推导依据` |
| Recommended actions | `建议措施` |
| Owner | `措施负责人` |
| Target date | `完成时间` |
| Post-action S/O/D/RPN | `改进后S` / `改进后O` / `改进后D` / `改进后RPN` |

## Preferred row pattern

Use this logic:

`object -> function -> failure mode -> effect -> cause -> current control -> score -> action`

For Markdown preview, the minimum useful column set is:

| Scope | Analysis object | Function or requirement | Failure mode | Failure effect | S | Cause or mechanism | O | Current controls | D | RPN | Recommended actions | Confirmation status | Review comment | Reference type | Source case |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Rules

- one failure mode per row
- do not combine unrelated causes in one vague blob when separate rows are clearer
- preserve traceability to source materials
- when importing an existing workbook, keep the imported workbook sheet/row as one visible `Source case`
- if the user provides their own table format, adapt while preserving the same semantics
- if a row is primarily inferred from a sibling module, keep that trace visible in `Reference type`
- if a row sits on a scope boundary, keep the row and flag it for confirmation instead of forcing certainty

## Suggested companion sections

After the main table, add these only when useful:

- `Top risks`
- `Rows needing confirmation`
- `Recommended actions`
- `Assumptions`
- `Source trace`

For Excel delivery, prefer separate worksheets instead of appending these sections under the main table.

## Confirmation queue fields

The confirmation queue should usually include:

| Field | Notes |
| --- | --- |
| Scope | where the row is currently placed |
| Row key | short label so the user can identify the draft row |
| Why confirmation is needed | ambiguous scope, weak evidence, uncertain `O/D`, or borrowed analogy |
| Suggested reviewer focus | what the expert should confirm or correct |
| Review comment | human review notes already written back but not yet fully closed |
| Plain-language question | question a non-expert user can answer from product facts |
| Why it matters | how the answer can change scope, score, control, or action priority |
| Suggested options | answer choices such as `multiple past issues`, `rare but possible`, `no known history`, `unknown` |
| Default assumption | AI assumption used for the draft |
| Impact if wrong | what may be wrong in the draft if the assumption is false |
| Reason tags | machine-readable tags such as `input_quality`, `coverage_gap`, `score_uncertainty`, `broader_analogy` |
| Priority | `critical`, `high`, `medium`, or `low` |
| Blocking | whether expert closure should block final signoff |

## Top-risk digest fields

For each high-risk row, keep:

| Field | Notes |
| --- | --- |
| Scope | risk location |
| Row key | stable locator back to the draft row |
| Failure mode | short risk label |
| Current RPN | current priority |
| Why it matters | business or engineering consequence |
| First action candidate | fastest meaningful mitigation |

## Notes from current project materials

The current sample files use slightly different headers such as:

- `零件名称`
- `子系统/功能模块`
- `子系统/组件`
- `潜在失效模式`
- `潜在失效后果`
- `现行设计控制`
- `建议改进措施`

Normalize them into the schema above unless the user explicitly needs the original spreadsheet wording.
