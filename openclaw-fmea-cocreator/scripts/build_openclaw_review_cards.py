from __future__ import annotations

import argparse
import datetime as dt
import json
import uuid
from pathlib import Path
from typing import Any


ALL_ACTIONS = ["confirm", "edit", "reject", "defer", "promote_to_case"]


def as_number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def unique_tags(tags: list[Any]) -> list[str]:
    out: list[str] = []
    for tag in tags:
        if tag is None:
            continue
        text = str(tag).strip()
        if text and text not in out:
            out.append(text)
    return out


def review_tags(row: dict[str, Any], queue: str) -> list[str]:
    tags: list[Any] = [queue, row.get("evidence_grade")]
    tags.extend(row.get("reason_tags", []))
    if row.get("needs_human_confirmation"):
        tags.append("needs_human_confirmation")
    if row.get("evidence_grade") in {"contradicted", "ai-inferred"}:
        tags.append("score_uncertainty")
    if as_number(row.get("confidence")) < 0.5:
        tags.append("low_confidence")
    if row.get("plain_language_question"):
        tags.append("non_expert_validation")
    if row.get("input_quality_diagnosis"):
        tags.append("input_quality")
    if row.get("coverage_gap") or row.get("coverage_gaps"):
        tags.append("coverage_gap")
    return unique_tags(tags)


def priority_for(row: dict[str, Any], queue: str) -> str:
    provided = row.get("priority")
    if provided in {"critical", "high", "medium", "low"}:
        return provided

    rpn = as_int(row.get("rpn"))
    confidence = as_number(row.get("confidence"))
    evidence_grade = row.get("evidence_grade")
    severity = as_int(row.get("severity"))

    if evidence_grade == "contradicted" or (severity >= 9 and confidence < 0.5):
        return "critical"
    if queue == "confirmation_queue" and (confidence < 0.5 or evidence_grade == "ai-inferred"):
        return "high"
    if rpn >= 300:
        return "critical"
    if rpn >= 150:
        return "high"
    if rpn >= 80 or row.get("needs_human_confirmation"):
        return "medium"
    return "low"


def row_effect(row: dict[str, Any]) -> str:
    return " | ".join(
        filter(
            None,
            [
                row.get("effect_customer", ""),
                row.get("effect_downstream", ""),
                row.get("effect_system", ""),
            ],
        )
    )


def row_controls(row: dict[str, Any]) -> str:
    return " | ".join(
        filter(
            None,
            [
                row.get("current_controls_prevention", ""),
                row.get("current_controls_detection", ""),
            ],
        )
    )


def review_context(row: dict[str, Any], tags: list[str]) -> dict[str, Any]:
    context = {
        "reason_tags": tags,
        "plain_language_question": row.get("plain_language_question", ""),
        "why_it_matters": row.get("why_it_matters", ""),
        "suggested_options": row.get("suggested_options", []),
        "default_assumption": row.get("default_assumption", ""),
        "impact_if_wrong": row.get("impact_if_wrong", ""),
        "blocking": bool(row.get("blocking")),
    }
    return {key: value for key, value in context.items() if value not in ("", [], False)}


def row_to_card(row: dict[str, Any], queue: str) -> dict[str, Any]:
    tags = review_tags(row, queue)
    return {
        "card_id": f"card-{uuid.uuid4().hex[:8]}",
        "row_id": row["row_id"],
        "queue": queue,
        "title": f"{row.get('leaf_name', '')} | {row.get('failure_mode', '')}",
        "priority": priority_for(row, queue),
        "reason_tags": tags,
        "evidence_grade": row["evidence_grade"],
        "confidence": row["confidence"],
        "rpn": row.get("rpn"),
        "fields": {
            "scope_path": row.get("scope_path", ""),
            "leaf_name": row.get("leaf_name", ""),
            "failure_mode": row.get("failure_mode", ""),
            "cause": row.get("cause", ""),
            "effect": row_effect(row),
            "current_controls": row_controls(row),
            "recommended_actions": row.get("recommended_actions", []),
            "severity": row["severity"],
            "occurrence": row["occurrence"],
            "detection": row["detection"],
            "p_diagram_anchor": row.get("p_diagram_anchor", ""),
            "reference_type": row.get("reference_type", ""),
        },
        "review_context": review_context(row, tags),
        "available_actions": ALL_ACTIONS,
        "needs_human_confirmation": row.get("needs_human_confirmation", False),
        "source_traces": row.get("source_traces", []),
    }


def resolve_queue_rows(normalized: dict[str, Any], queue_key: str) -> list[dict[str, Any]]:
    rows_by_id = {row["row_id"]: row for row in normalized.get("rows", []) if "row_id" in row}
    resolved: list[dict[str, Any]] = []
    for item in normalized.get(queue_key, []):
        if isinstance(item, str):
            row = rows_by_id.get(item)
            if row:
                resolved.append(row)
        elif isinstance(item, dict):
            row_id = item.get("row_id")
            base = rows_by_id.get(row_id, {}) if row_id else {}
            row = {**base, **item}
            if "row_id" in row:
                resolved.append(row)
    return resolved


def build_cards(normalized: dict[str, Any]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    seen: set[str] = set()
    for queue in ("top_risks", "confirmation_queue"):
        for row in resolve_queue_rows(normalized, queue):
            row_id = row["row_id"]
            if row_id not in seen:
                cards.append(row_to_card(row, queue))
                seen.add(row_id)
    return cards


def coverage_gap_count(normalized: dict[str, Any]) -> int:
    gaps = normalized.get("coverage_gaps", normalized.get("coverage_matrix", []))
    return len(gaps) if isinstance(gaps, list) else 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", required=True)
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args()

    normalized = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    cards = build_cards(normalized)
    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "fmea_normalized_path": args.input_json,
        "summary": {
            "card_count": len(cards),
            "input_quality_level": normalized.get("input_quality_diagnosis", {}).get("level", ""),
            "coverage_gap_count": coverage_gap_count(normalized),
        },
        "cards": cards,
    }
    Path(args.output_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
