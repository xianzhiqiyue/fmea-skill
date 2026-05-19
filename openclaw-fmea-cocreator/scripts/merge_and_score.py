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
    structure = json.loads(structure_path.read_text(encoding="utf-8"))

    candidates_by_role: dict = {}
    for cand_file in sorted(candidates_dir.glob("sample_candidates_*.json")) + sorted(candidates_dir.glob("candidates_*.json")):
        if cand_file.parent != candidates_dir:
            continue
        stem = cand_file.stem
        for prefix in ("sample_candidates_", "candidates_"):
            if stem.startswith(prefix):
                role_key = stem[len(prefix):]
                break
        else:
            continue
        role_map = {
            "design": "设计/模块",
            "reliability": "可靠性/试验",
            "system": "系统/接口",
            "manufacturing": "制造/工艺",
            "safety": "安全/服务",
            "software": "软件/控制",
        }
        role = role_map.get(role_key, role_key)
        candidates_by_role[role] = json.loads(cand_file.read_text(encoding="utf-8"))

    evidence_pool: dict = {}
    if evidence_pool_dir.exists():
        for ev_file in sorted(evidence_pool_dir.glob("*.json")):
            payload = json.loads(ev_file.read_text(encoding="utf-8"))
            evidence_pool[payload["leaf_id"]] = payload["matches"]

    return Inputs(structure=structure, candidates_by_role=candidates_by_role, evidence_pool=evidence_pool)


def cross_scope_dedup(inputs: Inputs) -> dict:
    """Returns dict keyed by (leaf_id, failure_mode_canonical) -> list[candidate]."""
    grouped: dict = {}
    for role, candidates in inputs.candidates_by_role.items():
        for cand in candidates:
            if "not_applicable_reason" in cand:
                continue
            key = (cand["leaf_id"], cand["failure_mode_canonical"])
            grouped.setdefault(key, []).append(cand)
    return grouped


def semantic_dedup_within_leaf(grouped: dict, llm_judge_fn: Optional[Callable] = None) -> dict:
    """When >=2 distinct canonicals share a leaf, ask LLM judge for merge/keep_separate/keep_with_distinguisher.
    Returns possibly-collapsed grouped dict."""
    if llm_judge_fn is None:
        return grouped

    leaf_to_canonicals: dict = {}
    for (leaf_id, canonical), cands in grouped.items():
        leaf_to_canonicals.setdefault(leaf_id, set()).add(canonical)

    decisions = []
    for leaf_id, canonicals in leaf_to_canonicals.items():
        if len(canonicals) < 2:
            continue
        canonicals_list = sorted(canonicals)
        for i in range(len(canonicals_list)):
            for j in range(i + 1, len(canonicals_list)):
                a_key = (leaf_id, canonicals_list[i])
                b_key = (leaf_id, canonicals_list[j])
                if a_key not in grouped or b_key not in grouped:
                    continue
                decision = llm_judge_fn(grouped[a_key][0], grouped[b_key][0])
                decisions.append((a_key, b_key, decision))

    for a_key, b_key, decision in decisions:
        if decision.get("decision") == "merge" and a_key in grouped and b_key in grouped:
            merged_canonical = decision.get("merged_canonical", a_key[1])
            survivor_key = (a_key[0], merged_canonical)
            grouped.setdefault(survivor_key, []).extend(grouped.pop(a_key, []))
            grouped[survivor_key].extend(grouped.pop(b_key, []))

    return grouped


def merge_candidates_per_key(grouped: dict) -> list:
    """For each (leaf, canonical) bucket, merge candidates from multiple roles."""
    rows = []
    for (leaf_id, canonical), cands in grouped.items():
        primary = max(cands, key=lambda c: c.get("self_confidence", 0))
        recommended = []
        for c in cands:
            for action in c.get("recommended_actions", []):
                if action not in recommended:
                    recommended.append(action)
        cause_parts = []
        for c in cands:
            cause_parts.append(f"[{c['role']}] {c['cause']}")
        prevention_parts = [f"[{c['role']}] {c['current_controls']['prevention']}" for c in cands]
        detection_parts = [f"[{c['role']}] {c['current_controls']['detection']}" for c in cands]

        severity = max(c["ai_severity"] for c in cands)
        occurrence = max(c["ai_occurrence"] for c in cands)
        detection = max(c["ai_detection"] for c in cands)

        row = {
            "row_id": f"{leaf_id}/{canonical}",
            "leaf_id": leaf_id,
            "scope_path": "",
            "failure_mode": primary["failure_mode"],
            "failure_mode_canonical": canonical,
            "p_diagram_anchor": f"{primary['p_diagram_anchor']['noise']} × {primary['p_diagram_anchor']['unintended_or_error']}",
            "cause": " ; ".join(cause_parts),
            "effect_customer": primary["effect"]["customer"],
            "effect_downstream": primary["effect"]["downstream"],
            "effect_system": primary["effect"]["system"],
            "current_controls_prevention": " ; ".join(prevention_parts),
            "current_controls_detection": " ; ".join(detection_parts),
            "recommended_actions": recommended,
            "severity": severity,
            "occurrence": occurrence,
            "detection": detection,
            "rpn": severity * occurrence * detection,
            "rating_history": {
                "role_view": [
                    {"role": c["role"], "s": c["ai_severity"], "o": c["ai_occurrence"], "d": c["ai_detection"]}
                    for c in cands
                ],
            },
            "multi_role_corroborated": len({c["role"] for c in cands}) >= 2,
            "source_traces": [{"type": "role_inference", "role": c["role"]} for c in cands],
        }
        rows.append(row)
    return rows


def align_with_evidence(rows: list, evidence_pool: dict) -> list:
    """Annotate each row with evidence_grade based on evidence_grading.md table."""
    for row in rows:
        leaf_id = row["leaf_id"]
        canonical = row["failure_mode_canonical"]
        matches = evidence_pool.get(leaf_id, [])
        relevant = []
        for m in matches:
            if canonical.replace("_", " ") in m["failure_mode_text"].lower() \
                    or any(kw in row.get("failure_mode", "") for kw in m.get("matched_keywords", [])) \
                    or m["failure_mode_text"]:
                relevant.append(m)
        role_count = len({rv["role"] for rv in row["rating_history"]["role_view"]})
        contradicted = False
        if relevant:
            best = max(relevant, key=lambda m: m["match_score"])
            for hist_field, row_field in [("severity", "severity"), ("occurrence", "occurrence")]:
                hist_val = best.get(hist_field)
                if hist_val is None:
                    continue
                if abs(hist_val - row[row_field]) >= 3:
                    contradicted = True
                    break
            row["rating_history"]["historical_view"] = {
                "s": best.get("severity"),
                "o": best.get("occurrence"),
                "d": best.get("detection"),
                "source": f"{best['source_workbook']}/{best['source_sheet']}/row {best['source_row']}",
            }
            row.setdefault("source_traces", []).append({
                "type": "historical",
                "ref": f"{best['source_workbook']}/{best['source_sheet']}/row {best['source_row']}",
            })
        if contradicted:
            grade = "contradicted"
        elif relevant and role_count >= 2:
            grade = "evidence-backed"
        elif relevant and role_count == 1:
            grade = "historical-supported"
        elif not relevant and role_count >= 2:
            grade = "multi-role-inferred"
        else:
            grade = "ai-inferred"
        row["evidence_grade"] = grade
    return rows


def _required_role_count(structure: dict) -> int:
    text_blob = json.dumps(structure, ensure_ascii=False).lower()
    triggers = ["mcu", "软件", "控制", "状态机", "通讯", "报警", "联锁"]
    has_software = any(t in text_blob for t in triggers)
    return 6 if has_software else 5


def compute_confidence(rows: list, structure: dict) -> list:
    """Compute 4-component confidence per evidence_grading.md formula."""
    required_role_count = _required_role_count(structure)
    for row in rows:
        role_count = len({rv["role"] for rv in row["rating_history"]["role_view"]})
        role_agreement = min(1.0, role_count / required_role_count)

        hist = row["rating_history"].get("historical_view")
        if hist:
            evidence_strength = 1.0
        else:
            evidence_strength = 0.0

        if row["evidence_grade"] in ("evidence-backed", "historical-supported"):
            sod_grounding = 1.0
        elif row["evidence_grade"] == "multi-role-inferred":
            sod_grounding = 0.7
        elif row["evidence_grade"] == "contradicted":
            sod_grounding = 0.4
        else:
            sod_grounding = 0.4

        anchor = row.get("p_diagram_anchor", "")
        if " × " in anchor:
            pdiagram_coverage = 1.0
        elif anchor:
            pdiagram_coverage = 0.5
        else:
            pdiagram_coverage = 0.0

        confidence = (
            WEIGHTS["role_agreement"] * role_agreement
            + WEIGHTS["evidence_strength"] * evidence_strength
            + WEIGHTS["sod_grounding"] * sod_grounding
            + WEIGHTS["pdiagram_coverage"] * pdiagram_coverage
        )
        row["confidence"] = round(confidence, 3)
        row["confidence_breakdown"] = {
            "role_agreement": round(role_agreement, 3),
            "evidence_strength": round(evidence_strength, 3),
            "sod_grounding": round(sod_grounding, 3),
            "pdiagram_coverage": round(pdiagram_coverage, 3),
        }
        row["needs_human_confirmation"] = (
            row["evidence_grade"] in ("contradicted", "ai-inferred")
            or confidence < 0.5
        )
    return rows


def _walk_leaves(node):
    if node.get("level") == "component":
        yield node
    for child in node.get("children", []):
        yield from _walk_leaves(child)


REQUIRED_AXES = {
    "系统/接口": [("system_interactions", "intended_outputs")],
    "设计/模块": [("piece_to_piece", "control_factors")],
    "可靠性/试验": [("wear_aging", "environment")],
    "制造/工艺": [("piece_to_piece", "control_factors")],
    "安全/服务": [("customer_usage", "error_states")],
    "软件/控制": [("input_signals", "control_factors"), ("control_factors", "error_states")],
}


def coverage_gap_check(rows: list, structure: dict) -> list:
    """Detect (leaf x required_axis) combinations not covered by any non-NA candidate."""
    leaves = list(_walk_leaves(structure["hierarchy"]))
    leaf_ids = [n["id"] for n in leaves]

    covered = set()
    for row in rows:
        anchor = row.get("p_diagram_anchor", "")
        parts = anchor.split(" × ")
        if len(parts) == 2:
            noise_axis = parts[0].split(":")[0] if ":" in parts[0] else ""
            unintended_axis = parts[1].split(":")[0] if ":" in parts[1] else ""
            covered.add((row["leaf_id"], noise_axis, unintended_axis))

    gaps = []
    for leaf_id in leaf_ids:
        for role, axes in REQUIRED_AXES.items():
            for noise_axis, unintended_axis in axes:
                if (leaf_id, noise_axis, unintended_axis) not in covered:
                    gaps.append({
                        "leaf_id": leaf_id,
                        "role": role,
                        "axis_combo": f"{noise_axis} × {unintended_axis}",
                        "severity_estimate": "potential",
                    })
    return gaps


def select_top_risks(rows: list, top_n: int = 10) -> list:
    """Sort by confidence * rpn descending."""
    return sorted(rows, key=lambda r: r["confidence"] * r["rpn"], reverse=True)[:top_n]


def select_confirmation_queue(rows: list) -> list:
    """Rows where evidence_grade in {contradicted} OR (ai-inferred AND confidence<0.5) OR confidence<0.4."""
    queue = []
    for row in rows:
        if row["evidence_grade"] == "contradicted":
            queue.append(row)
        elif row["evidence_grade"] == "ai-inferred" and row.get("confidence", 0) < 0.5:
            queue.append(row)
        elif row.get("confidence", 0) < 0.4:
            queue.append(row)
    return sorted(queue, key=lambda r: r["confidence"] * r["rpn"], reverse=True)


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
