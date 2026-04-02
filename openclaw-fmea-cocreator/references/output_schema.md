# Output Schema

Use this normalized schema for most FMEA drafts and reviews.

For OpenClaw delivery, prefer a stable Excel workbook package made of:

1. `Scope split`
2. `FMEA draft`
3. `Rows needing confirmation`
4. `Top risks`
5. `Suggested actions`
6. `Source trace`

## Workbook layout

The default deliverable should be one `.xlsx` workbook with these worksheets:

1. `概览`
2. `Scope规划`
3. one worksheet per scope
4. `确认队列`
5. `Top风险`
6. `建议动作`
7. `来源追踪`

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
