from __future__ import annotations

import argparse
import json
from pathlib import Path


PATCH_ALLOWED = {
    "severity", "occurrence", "detection",
    "current_controls_prevention", "current_controls_detection",
    "recommended_actions", "owner", "target_date",
    "effect_customer", "effect_system", "cause"
}

STATUS_BY_ACTION = {
    "confirm": "confirmed",
    "edit": "edited",
    "reject": "rejected",
    "defer": "deferred",
    "promote_to_case": "promoted"
}


def latest_action_per_row(actions: list[dict]) -> dict[str, dict]:
    latest: dict[str, dict] = {}
    for action in actions:
        row_id = action["row_id"]
        if row_id not in latest or action["reviewed_at"] > latest[row_id]["reviewed_at"]:
            latest[row_id] = action
    return latest


def apply_one(row: dict, action: dict) -> dict:
    name = action["action"]
    row = dict(row)
    row["review_status"] = STATUS_BY_ACTION[name]
    meta = {k: v for k, v in action.items() if k not in {"row_id", "action", "patch"}}
    if name == "edit":
        patch = action.get("patch", {})
        for key, value in patch.items():
            if key in PATCH_ALLOWED:
                row[key] = value
        row["rpn"] = row["severity"] * row["occurrence"] * row["detection"]
    if name == "reject":
        row["needs_human_confirmation"] = False
    if name == "promote_to_case":
        row["needs_human_confirmation"] = False
    row["review_meta"] = meta
    return row


def apply_review_actions(normalized: dict, actions_doc: dict) -> dict:
    latest = latest_action_per_row(actions_doc.get("actions", []))
    new_rows = []
    for row in normalized.get("rows", []):
        action = latest.get(row["row_id"])
        if action is None:
            new_rows.append(dict(row, review_status="pending", review_meta={}))
        else:
            new_rows.append(apply_one(row, action))
    out = dict(normalized)
    out["rows"] = new_rows
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", required=True)
    parser.add_argument("--actions-json", required=True)
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args()

    normalized = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    actions = json.loads(Path(args.actions_json).read_text(encoding="utf-8"))
    applied = apply_review_actions(normalized, actions)
    Path(args.output_json).write_text(json.dumps(applied, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
