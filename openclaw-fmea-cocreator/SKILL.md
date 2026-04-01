---
name: openclaw-fmea-cocreator
description: Use when the user wants to co-create AFMEA, SFMEA, or DFMEA on OpenClaw; turn module descriptions, BOM or environment inputs into structured FMEA drafts; review or expand existing FMEA tables; retrieve similar historical failure cases; or convert quality materials into reusable FMEA knowledge and action items.
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
4. draft a normalized FMEA table
5. separate AI suggestions from human-confirmed judgments
6. output both the FMEA table and a follow-up action list

## Core workflow

### 1. Determine the job to be done

Start by identifying which of these the user needs:

- new FMEA draft from raw module description
- review or completion of an existing FMEA
- high-risk item rework or action-plan output
- conversion of a confirmed FMEA row into a reusable case

If the user does not specify the FMEA type, infer it from scope:

- lifecycle, transport, storage, maintenance, operation: likely `AFMEA`
- system to subsystem decomposition and interfaces: likely `SFMEA`
- subsystem to part, BOM, material, component risk: likely `DFMEA`

If needed, read [references/prompt_templates.md](references/prompt_templates.md).

### 2. Gather inputs before drafting

Use the minimum checklist in [references/input_checklist.md](references/input_checklist.md).

Required minimum for a useful draft:

- analysis object or module name
- key function or requirement
- use or task scenario
- at least one of: environment, interface, historical issue, BOM, design constraint

Before drafting, decide whether the input is actually one analysis scope or multiple distinct scopes.

If the material contains clearly different architectures, subsystems, or operating principles, split the draft into separate sections or separate FMEA tables first.

When using `scripts/draft_fmea_from_cases.py`, the script will try to suggest scopes automatically if `--scope` is not provided.

Do not block on perfect input. Draft with assumptions when needed, but label them clearly.

### 3. Normalize names and locate similar cases

Before drafting, normalize module names using [references/module_aliases.md](references/module_aliases.md).

When historical support would help, retrieve cases from the exported materials:

```bash
python3 scripts/retrieve_cases.py --query "压缩机 液击 冷媒 泄漏" --module "变温系统"
```

Use the retrieved rows as references, not as facts to copy blindly. Keep source traceability.

When the user already has a natural-language module description and wants a fast first draft, bootstrap it with:

```bash
python3 scripts/draft_fmea_from_cases.py --module "变温系统" --input-file /path/to/input.txt
```

If the automatic scope suggestion is not ideal, rerun with explicit `--scope "范围名::关键词..."` overrides.

If needed, read [references/case_sources.md](references/case_sources.md).

### 4. Draft the FMEA in a normalized schema

Always prefer the normalized output structure in [references/output_schema.md](references/output_schema.md).

Important formatting rules:

- one failure mode per row
- keep cause, effect, and control separate
- do not split one logical row across multiple spreadsheet rows unless the user explicitly asks for that format
- include `RPN = S * O * D`
- if the user needs a deliverable artifact, default to Excel workbook; use Markdown for conversational preview and JSON for structured handoff
- if a row is derived from a related-module analogy, mark it as `family analogy reference` instead of presenting it as the primary source

### 5. Apply scoring guardrails

Use [references/scoring_guardrails.md](references/scoring_guardrails.md).

Especially important:

- `S` can often be estimated from customer or downstream impact
- `O` and `D` are highly organization-specific and should usually be marked as `AI draft, needs confirmation` unless grounded in provided process capability or historical data
- when confidence is low, say so plainly

### 6. End with co-creation, not just generation

After producing a draft, always help the user move to the next step:

- highlight top RPN items
- list rows that most need expert confirmation
- propose action items with owner and target date placeholders when useful
- suggest which confirmed rows should be added back into the case library

## OpenClaw delivery contract

When this skill is used as an OpenClaw workflow building block, the default output should be a compact package with these parts:

1. `Scope split`
2. `FMEA draft`
3. `Rows needing confirmation`
4. `Top risks`
5. `Suggested actions`
6. `Source trace`

Minimum delivery rules:

- keep one worksheet per scope in the Excel workbook
- label each row as `current module`, `direct family reference`, or `broader analogy`
- keep `O` and `D` in `draft` state unless the user or source gave enough enterprise evidence
- call out boundary rows whose scope ownership is ambiguous
- preserve workbook and sheet traceability whenever a historical row influenced the draft
- keep Markdown or JSON only as preview or system interface companions when useful

## Output expectations

For most requests, return these sections when useful:

1. `FMEA draft`
2. `Rows needing confirmation`
3. `Top risks`
4. `Suggested actions`

If the user only asks for one of these, keep the response scoped.

If the user asks for an OpenClaw-ready result, follow the full delivery contract above and the field rules in [references/output_schema.md](references/output_schema.md).

If the task is about OpenClaw form design, workflow integration, field binding, or workbook-to-system mapping, read [references/openclaw_interface_mapping.md](references/openclaw_interface_mapping.md).
If a machine-readable form definition or example payload is needed, also use `references/openclaw_form_definition.json` and `references/openclaw_submission_examples.json`.
If the task is about backend assembly, payload execution, or artifact path resolution, also read [references/openclaw_submission_assembly.md](references/openclaw_submission_assembly.md).
If the task is about in-product review cards for `确认队列` or `Top风险`, also use `references/openclaw_review_cards_schema.json` and `scripts/build_openclaw_review_cards.py`.
If the task is about writing human review decisions back into the workbook, also use `references/openclaw_review_action_protocol.json`, `references/openclaw_review_action_examples.json`, and `scripts/apply_openclaw_review_actions.py`.

Current script support:

```bash
python3 scripts/draft_fmea_from_cases.py --module "模块名" --input-file /path/to/input.txt --excel-out /path/to/output.xlsx
```

OpenClaw bridge support:

```bash
python3 scripts/run_openclaw_submission.py --payload-file /path/to/payload.json
python3 scripts/run_openclaw_submission.py --example-name auto_scope_dfmea_rf_power_amp --dry-run --print-input
python3 scripts/build_openclaw_review_cards.py --input-json /path/to/draft.json --output-json /path/to/cards.json
python3 scripts/apply_openclaw_review_actions.py --input-json /path/to/draft.json --actions-json /path/to/review_actions.json
```

## When to read which reference

- `references/workflow.md`: when you need the full co-creation workflow
- `references/input_checklist.md`: when input is incomplete or scattered
- `references/output_schema.md`: when generating or normalizing tables
- `references/openclaw_interface_mapping.md`: when mapping OpenClaw fields to script inputs, workbook sheets, or structured payloads
- `references/openclaw_form_definition.json`: when building the actual OpenClaw form config
- `references/openclaw_submission_examples.json`: when preparing request payloads or testing submission shape
- `references/openclaw_submission_assembly.md`: when wiring backend payload assembly or executing the bridge script
- `references/openclaw_review_cards_schema.json`: when rendering `确认队列` and `Top风险` as OpenClaw cards
- `references/openclaw_review_action_protocol.json`: when frontend review actions need a writeback contract
- `references/openclaw_review_action_examples.json`: when testing or mocking review writeback payloads
- `references/prompt_templates.md`: when constructing prompts or choosing AFMEA/SFMEA/DFMEA framing
- `references/scoring_guardrails.md`: whenever assigning or reviewing S/O/D
- `references/module_aliases.md`: when module naming is inconsistent
- `references/case_sources.md`: when searching historical examples

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
