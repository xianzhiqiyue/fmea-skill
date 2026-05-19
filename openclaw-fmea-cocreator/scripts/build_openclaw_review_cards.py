from __future__ import annotations

import argparse
import datetime as dt
import json
import uuid
from pathlib import Path


ALL_ACTIONS = ["confirm", "edit", "reject", "defer", "promote_to_case"]


def row_to_card(row: dict, queue: str) -> dict:
    return {
        "card_id": f"card-{uuid.uuid4().hex[:8]}",
        "row_id": row["row_id"],
        "queue": queue,
        "title": f"{row.get('leaf_name', '')} | {row.get('failure_mode', '')}",
        "evidence_grade": row["evidence_grade"],
        "confidence": row["confidence"],
        "rpn": row.get("rpn"),
        "fields": {
            "scope_path": row.get("scope_path", ""),
            "leaf_name": row.get("leaf_name", ""),
            "failure_mode": row.get("failure_mode", ""),
            "cause": row.get("cause", ""),
            "effect": " | ".join(filter(None, [row.get("effect_customer", ""), row.get("effect_system", "")])),
            "current_controls": " | ".join(filter(None, [row.get("current_controls_prevention", ""), row.get("current_controls_detection", "")])),
            "recommended_actions": row.get("recommended_actions", []),
            "severity": row["severity"],
            "occurrence": row["occurrence"],
            "detection": row["detection"]
        },
        "available_actions": ALL_ACTIONS,
        "needs_human_confirmation": row.get("needs_human_confirmation", False),
        "source_traces": row.get("source_traces", [])
    }


def build_cards(normalized: dict) -> list[dict]:
    rows_by_id = {r["row_id"]: r for r in normalized.get("rows", [])}
    cards: list[dict] = []
    seen: set[str] = set()
    for row_id in normalized.get("top_risks", []):
        if row_id in rows_by_id and row_id not in seen:
            cards.append(row_to_card(rows_by_id[row_id], "top_risks"))
            seen.add(row_id)
    for row_id in normalized.get("confirmation_queue", []):
        if row_id in rows_by_id and row_id not in seen:
            cards.append(row_to_card(rows_by_id[row_id], "confirmation_queue"))
            seen.add(row_id)
    return cards


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", required=True)
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args()

    normalized = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "fmea_normalized_path": args.input_json,
        "cards": build_cards(normalized)
    }
    Path(args.output_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
