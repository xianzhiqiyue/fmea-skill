"""Merge multi-role candidates with historical evidence into a normalized FMEA.

Pipeline (called sequentially from main, individually unit-testable):
  1. load_inputs(structure_path, candidates_dir, evidence_pool_dir) -> Inputs
  2. cross_scope_dedup(candidates) -> grouped_by_primary_key
  3. semantic_dedup_within_leaf(grouped, llm_judge_fn) -> grouped_after_semantic
  4. merge_candidates_per_key(grouped) -> merged_rows
  5. align_with_evidence(merged_rows, evidence_pool) -> rows_with_grade
  6. compute_confidence(rows_with_grade) -> rows_with_confidence
  7. coverage_gap_check(rows, structure) -> coverage_gaps
  8. select_top_risks(rows) and select_confirmation_queue(rows) -> final outputs

The LLM judge function for semantic dedup is injected; default is a dry no-op
(falls back to "keep_separate" + sets a flag in the output for transparency).
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Callable, Optional

WEIGHTS = {"role_agreement": 0.30, "evidence_strength": 0.30, "sod_grounding": 0.25, "pdiagram_coverage": 0.15}

# --- public API surface ----

@dataclass
class Inputs:
    structure: dict
    candidates_by_role: dict  # role -> list[candidate]
    evidence_pool: dict  # leaf_id -> list[match]


def load_inputs(structure_path: Path, candidates_dir: Path, evidence_pool_dir: Path) -> Inputs:
    raise NotImplementedError


def cross_scope_dedup(inputs: Inputs) -> dict:
    """Returns dict keyed by (leaf_id, failure_mode_canonical) -> list[candidate]."""
    raise NotImplementedError


def semantic_dedup_within_leaf(grouped: dict, llm_judge_fn: Optional[Callable] = None) -> dict:
    """When >=2 distinct canonicals share a leaf, ask LLM judge for merge/keep_separate/keep_with_distinguisher.
    Returns possibly-collapsed grouped dict."""
    raise NotImplementedError


def merge_candidates_per_key(grouped: dict) -> list:
    """For each (leaf, canonical) bucket, merge candidates from multiple roles."""
    raise NotImplementedError


def align_with_evidence(rows: list, evidence_pool: dict) -> list:
    """Annotate each row with evidence_grade based on evidence_grading.md table."""
    raise NotImplementedError


def compute_confidence(rows: list, structure: dict) -> list:
    """Compute 4-component confidence per evidence_grading.md formula."""
    raise NotImplementedError


def coverage_gap_check(rows: list, structure: dict) -> list:
    """Detect (leaf x required_axis) combinations not covered by any non-NA candidate."""
    raise NotImplementedError


def select_top_risks(rows: list, top_n: int = 10) -> list:
    """Sort by confidence * rpn descending."""
    raise NotImplementedError


def select_confirmation_queue(rows: list) -> list:
    """Rows where evidence_grade in {contradicted} OR (ai-inferred AND confidence<0.5) OR confidence<0.4."""
    raise NotImplementedError


# --- CLI ----

def main() -> None:
    parser = argparse.ArgumentParser(description="Merge candidates + evidence into normalized FMEA.")
    parser.add_argument("--structure", required=True, type=Path)
    parser.add_argument("--candidates-dir", required=True, type=Path,
                        help="Directory containing candidates_<role>.json files.")
    parser.add_argument("--evidence-pool-dir", required=True, type=Path,
                        help="Directory containing <leaf_id>.json evidence files.")
    parser.add_argument("--output", required=True, type=Path,
                        help="Path to write fmea_normalized.json")
    args = parser.parse_args()

    inputs = load_inputs(args.structure, args.candidates_dir, args.evidence_pool_dir)
    grouped = cross_scope_dedup(inputs)
    grouped = semantic_dedup_within_leaf(grouped)
    rows = merge_candidates_per_key(grouped)
    rows = align_with_evidence(rows, inputs.evidence_pool)
    rows = compute_confidence(rows, inputs.structure)
    coverage_gaps = coverage_gap_check(rows, inputs.structure)
    top_risks = select_top_risks(rows)
    confirmation_queue = select_confirmation_queue(rows)

    output = {
        "module_root": inputs.structure["module_root"],
        "fmea_type": inputs.structure["fmea_type"],
        "rows": rows,
        "coverage_gaps": coverage_gaps,
        "top_risks": top_risks,
        "confirmation_queue": confirmation_queue,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
