#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
OUT="$ROOT/validation/mock_10/m2_generated"
mkdir -p "$OUT"
echo "Note: this script only stitches outputs. Each scenario must first have:"
echo "  - structure.json (produced by Claude per p_diagram_template.md)"
echo "  - candidates_*.json (per specialist_role_prompts.md, 6 roles)"
echo "  - evidence_pool/<leaf_id>.json (via retrieve_cases.py --json-out)"

for scenario_dir in "$ROOT"/validation/mock_10/scenarios/*/; do
  name=$(basename "$scenario_dir")
  out_norm="$OUT/${name}_normalized.json"
  out_xlsx="$OUT/${name}.xlsx"
  python3 "$ROOT/openclaw-fmea-cocreator/scripts/merge_and_score.py" \
    --structure "$scenario_dir/structure.json" \
    --candidates-dir "$scenario_dir" \
    --evidence-pool-dir "$scenario_dir/evidence_pool" \
    --output "$out_norm"
  python3 "$ROOT/openclaw-fmea-cocreator/scripts/build_workbook.py" \
    --normalized "$out_norm" \
    --structure "$scenario_dir/structure.json" \
    --output "$out_xlsx"
done
echo "Done. Run pytest tests/test_mock_10_regression.py to validate."
