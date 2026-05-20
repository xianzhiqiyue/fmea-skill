# OpenClaw Submission Assembly

Use this reference when implementing the backend bridge from an OpenClaw form payload to the local FMEA generation scripts.

This is the execution-layer companion to:

- `openclaw_interface_mapping.md`
- `openclaw_form_definition.json`
- `openclaw_submission_examples.json`

## Purpose

The current bridge should do seven things:

1. validate whether a payload has the minimum fields
2. merge distributed form fields into one drafting text body
3. convert manual scopes into repeatable `--scope` arguments
4. run `draft_fmea_from_cases.py` to generate the Excel workbook
5. when JSON output is enabled, optionally generate `cards.json` for OpenClaw review rendering
6. after human review, optionally execute a writeback bundle and regenerate reviewed artifacts
7. when an existing workbook path is provided, switch to workbook import instead of raw drafting

## Bridge script

Current bridge script:

```bash
python3 scripts/run_openclaw_submission.py --payload-file /path/to/payload.json
```

Current existing-workbook import script:

```bash
python3 scripts/import_existing_fmea_excel.py --input-excel /path/to/existing.xlsx --excel-out /path/to/normalized.xlsx --json-out /path/to/normalized.json
```

Current review writeback script:

```bash
python3 scripts/apply_openclaw_review_actions.py \
  --input-json /path/to/fmea_normalized.json \
  --actions-json /path/to/review_actions.json \
  --output-json /path/to/fmea_normalized.review_applied.json
```

It also supports example payloads:

```bash
python3 scripts/run_openclaw_submission.py --example-name auto_scope_dfmea_rf_power_amp --dry-run --print-input
```

## Execution flow

### 1. Load payload

The bridge accepts one of:

- `--payload-file`
- `--example-name`

If `--example-name` is used, the payload comes from `references/openclaw_submission_examples.json`.

### 2. Validate payload

The bridge currently enforces:

- for `new_fmea_draft`:
  - `module_name` is required
  - `fmea_type` is required and must be `AFMEA` / `SFMEA` / `DFMEA` / `PFMEA`
  - `function_description` is required
  - `use_scenario` is required
  - at least one context field is required:
    - `environment`
    - `interfaces`
    - `design_constraints`
    - `historical_issues`
    - `bom_or_key_parts`
- for `review_existing_fmea` or `high_risk_review`:
  - `existing_fmea_excel_path` or `existing_fmea_text` must be present
  - if `existing_fmea_excel_path` is present, `module_name` and `fmea_type` may be omitted and later recovered from workbook `封面` or legacy `概览`
- if `scope_mode = manual`, each scope must include:
  - `name`
  - `keywords`

### 3. Build merged input text

The bridge writes one merged input text file before calling the drafting script.

Current merge order:

1. `project_name`
2. `module_name`
3. `function_description`
4. `use_scenario`
5. `environment`
6. `interfaces`
7. `design_constraints`
8. `historical_issues`
9. `current_controls`
10. `bom_or_key_parts`
11. `customer_impact`
12. `attachments_summary`
13. `existing_fmea_text`

If `scope_mode = manual`, the bridge also appends:

- each scope name
- each scope keyword set
- each scope note if present

If `existing_fmea_excel_path` is present, this merged text becomes the import/review context note passed to the importer via `--context-file`.

### 4. Resolve output paths

The bridge creates one output stem from:

- `requested_output_name`, if provided
- otherwise `{module_name}_{scope_mode}_scope_draft`

Resolved artifacts:

- input text: `{stem}_input.txt`
- Excel workbook: `{stem}.xlsx`
- Markdown preview: `{stem}.md` when `include_markdown_preview = true`
- JSON payload: `{stem}.json` when `include_json_payload = true`
- review cards: `{stem}_cards.json` when `include_json_payload = true` and `include_review_cards = true`

Default output directory:

- `validation/openclaw_runs/`

### 5. Choose execution mode

If `intent` is `review_existing_fmea` or `high_risk_review` and `existing_fmea_excel_path` is provided, the bridge calls `import_existing_fmea_excel.py`.

Otherwise it calls `draft_fmea_from_cases.py`.

### 6. Build final command

The bridge converts payload fields into a command like:

```bash
python3 scripts/draft_fmea_from_cases.py \
  --module "模块名" \
  --fmea-type "DFMEA" \
  --input-file /path/to/merged_input.txt \
  --excel-out /path/to/output.xlsx
```

If `scope_mode = manual`, it appends repeated scope arguments:

```bash
--scope "子系统A::关键词1 关键词2"
--scope "子系统B::关键词3 关键词4"
```

If preview output is enabled:

- append `--markdown-out`
- append `--json-out`

In import mode, the command becomes:

```bash
python3 scripts/import_existing_fmea_excel.py \
  --input-excel /path/to/existing.xlsx \
  --context-file /path/to/merged_input.txt \
  --excel-out /path/to/output.xlsx
```

Optional:

- append `--module` when provided
- append `--fmea-type` when provided
- append `--markdown-out`
- append `--json-out`

## Dry run behavior

Use `--dry-run` when:

- validating frontend or backend integration
- checking filename and output path resolution
- reviewing generated input text before running the full draft

The bridge will:

- still validate the payload
- still write the merged input text
- print the resolved command and artifact paths
- not execute `draft_fmea_from_cases.py`
- not execute `build_openclaw_review_cards.py`

## Printed result contract

The bridge prints a JSON object with:

- `source`
- `submission_mode`
- `command`
- `input_text_path`
- `excel_path`
- `markdown_path`
- `json_path`
- `cards_path`

This is useful for backend logging and debugging.

## Recommended backend wiring

The current backend integration should follow this sequence:

1. receive the OpenClaw form payload
2. save the payload JSON for traceability
3. call `run_openclaw_submission.py`
4. collect the printed artifact paths
5. return the `.xlsx` as the primary artifact, regardless of whether it came from draft or import mode
6. optionally display the Markdown preview inline
7. optionally use the JSON artifact for later edits
8. use `cards.json` to render `确认队列` and `Top风险` cards in product
9. when the user confirms rows or scores, assemble a review action bundle and call `apply_openclaw_review_actions.py`
10. replace or version the reviewed `.xlsx/.json/.cards.json`

## Review writeback contract

When OpenClaw receives human review decisions from cards or table actions, it should:

1. build a bundle following `openclaw_review_action_protocol.json`
2. pass the original draft `.json` as `--input-json`
3. pass the action bundle as `--actions-json`
4. pass a reviewed normalized payload path as `--output-json`
5. return the reviewed `.xlsx` as the new primary artifact when a workbook refresh step is also run
6. refresh cards from the reviewed `.json`

Supported mutating action ids:

- `confirm`
- `edit`
- `reject`
- `defer`
- `promote_to_case`

## Current limits

The bridge does not yet:

- parse in-memory uploaded binaries directly without first saving a workbook path
- localize workbook column names to multiple enterprise templates

These should be treated as the next integration phase, not part of the current bridge.
