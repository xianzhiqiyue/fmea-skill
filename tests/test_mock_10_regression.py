"""mock_10 regression: assert the indicators that proved M0 was broken are gone in M2.

The hallmark bug was:
- 10 different scenarios each produced exactly 28 rows
- The same source_row appeared in multiple scopes ("source_trace duplication")

If our M2 pipeline genuinely produces FMEA rather than copying historical rows,
these patterns must NOT reappear.
"""
import json
from collections import Counter
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATED_DIR = REPO_ROOT / "validation" / "mock_10" / "m2_generated"


def _load_normalized_outputs():
    if not GENERATED_DIR.exists():
        pytest.skip("M2 mock_10 outputs not yet generated; run validation/mock_10/run_m2.sh first")
    files = sorted(GENERATED_DIR.glob("*_normalized.json"))
    if not files:
        pytest.skip("M2 mock_10 outputs directory exists but is empty")
    return [json.loads(f.read_text(encoding="utf-8")) for f in files]


def test_row_counts_are_not_all_equal():
    """Indicator: in M0, all 10 scenarios produced exactly 28 rows.
    In M2 they should differ — they are different modules with different P-Diagrams."""
    outputs = _load_normalized_outputs()
    counts = [len(o["rows"]) for o in outputs]
    assert len(set(counts)) > 1, f"All scenarios produced same row count: {counts}"


def test_no_source_row_crosses_scopes():
    """Indicator: in M0, the same historical source_row could appear under multiple scopes.
    In M2, each historical match is anchored to a single leaf_id, so leaf_id × source_row
    should be unique across the whole FMEA."""
    outputs = _load_normalized_outputs()
    for output in outputs:
        seen = set()
        duplicates = []
        for row in output["rows"]:
            for trace in row.get("source_traces", []):
                if trace.get("type") != "historical":
                    continue
                key = (row["leaf_id"], trace.get("ref"))
                if key in seen:
                    duplicates.append(key)
                seen.add(key)
        assert not duplicates, f"Module {output['module_root']} has duplicate (leaf, source_row): {duplicates}"


def test_at_least_60pct_rows_multi_role_corroborated():
    outputs = _load_normalized_outputs()
    for output in outputs:
        rows = output["rows"]
        if not rows:
            continue
        corroborated = sum(1 for r in rows if r.get("multi_role_corroborated"))
        ratio = corroborated / len(rows)
        assert ratio >= 0.6, f"Module {output['module_root']} has only {ratio:.0%} multi-role rows"


def test_evidence_grade_consistent_with_confidence():
    """evidence-backed rows should have confidence >= 0.5;
    ai-inferred rows should rarely exceed 0.7 (low evidence_strength dominates)."""
    outputs = _load_normalized_outputs()
    for output in outputs:
        for row in output["rows"]:
            if row["evidence_grade"] == "evidence-backed":
                assert row["confidence"] >= 0.5, f"evidence-backed row has low confidence: {row['row_id']}"
            if row["evidence_grade"] == "ai-inferred" and row["confidence"] >= 0.7:
                pytest.fail(f"ai-inferred row with high confidence is suspicious: {row['row_id']}")
