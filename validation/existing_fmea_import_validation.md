# Existing FMEA Import Validation

## Scope

This validation checks the new import-first review path:

1. import an existing FMEA Excel workbook
2. normalize it into the current OpenClaw Excel/JSON/cards contract
3. apply review actions on the imported JSON
4. confirm that reviewed Excel and cards stay in sync

## Import through OpenClaw bridge

Command:

```bash
python3 /Users/nova/code/fmea-skill/openclaw-fmea-cocreator/scripts/run_openclaw_submission.py \
  --example-name review_existing_fmea_rf_power_amp_import
```

Input workbook:

- `/Users/nova/code/fmea-skill/validation/openclaw_runs/射频功放_auto_scope_draft.xlsx`

Imported artifacts:

- `/Users/nova/code/fmea-skill/validation/openclaw_runs/射频功放_existing_fmea_import.xlsx`
- `/Users/nova/code/fmea-skill/validation/openclaw_runs/射频功放_existing_fmea_import.md`
- `/Users/nova/code/fmea-skill/validation/openclaw_runs/射频功放_existing_fmea_import.json`
- `/Users/nova/code/fmea-skill/validation/openclaw_runs/射频功放_existing_fmea_import_cards.json`

## Review writeback on imported JSON

Command:

```bash
python3 /Users/nova/code/fmea-skill/openclaw-fmea-cocreator/scripts/apply_openclaw_review_actions.py \
  --input-json /Users/nova/code/fmea-skill/validation/openclaw_runs/射频功放_existing_fmea_import.json \
  --example-name rf_power_amp_review_round_1
```

Reviewed artifacts:

- `/Users/nova/code/fmea-skill/validation/openclaw_runs/射频功放_existing_fmea_import_reviewed.xlsx`
- `/Users/nova/code/fmea-skill/validation/openclaw_runs/射频功放_existing_fmea_import_reviewed.md`
- `/Users/nova/code/fmea-skill/validation/openclaw_runs/射频功放_existing_fmea_import_reviewed.json`
- `/Users/nova/code/fmea-skill/validation/openclaw_runs/射频功放_existing_fmea_import_reviewed_cards.json`

## Checked outcomes

- bridge returned `submission_mode = existing_fmea_import`
- imported workbook produced the same 3-scope structure as the source workbook
- imported JSON kept `确认队列` reasons, including `scope 归属存在边界`
- imported `Source case` prepended workbook trace like:
  - `射频功放_auto_scope_draft.xlsx / 02-放大与通道切换子系统 / row 4`
- imported cards were generated with `cards_version = 0.2.0`
- after applying the same review action bundle:
  - confirmation queue dropped from `5` to `3`
  - `接收链路非线性失真或提前饱和` became `confirmed`
  - `S/O/D` changed to `8/4/4`
  - `owner` and `target_date` were written back

## Tooling validation

- `python3 -m py_compile` passed for:
  - `import_existing_fmea_excel.py`
  - `run_openclaw_submission.py`
  - `apply_openclaw_review_actions.py`
- `python3 -m json.tool` passed for:
  - `openclaw_form_definition.json`
  - `openclaw_submission_examples.json`
