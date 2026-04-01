from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import draft_fmea_from_cases as draft
from build_openclaw_review_cards import build_cards_payload


ACTION_EXAMPLES_PATH = SKILL_DIR / "references" / "openclaw_review_action_examples.json"
MUTATING_ACTIONS = {
    "confirm_row",
    "confirm_scope_owner",
    "confirm_reference_fit",
    "confirm_scores",
    "set_owner_target",
}


def load_action_bundle(args: argparse.Namespace) -> tuple[dict[str, Any], str]:
    if args.actions_json:
        bundle = json.loads(Path(args.actions_json).read_text(encoding="utf-8"))
        source_label = str(Path(args.actions_json))
    else:
        examples = json.loads(ACTION_EXAMPLES_PATH.read_text(encoding="utf-8"))
        if args.example_name not in examples:
            raise ValueError(f"Unknown review action example: {args.example_name}")
        bundle = examples[args.example_name]
        source_label = f"{ACTION_EXAMPLES_PATH}#{args.example_name}"

    if "actions" not in bundle or not isinstance(bundle["actions"], list):
        raise ValueError("Review action bundle must contain an 'actions' array.")
    return bundle, source_label


def derive_output_paths(args: argparse.Namespace, input_json_path: Path) -> dict[str, Path]:
    base_stem = input_json_path.with_suffix("")
    default_stem = base_stem.parent / f"{base_stem.name}_reviewed"
    json_path = Path(args.json_out) if args.json_out else default_stem.with_suffix(".json")
    return {
        "excel": Path(args.excel_out) if args.excel_out else default_stem.with_suffix(".xlsx"),
        "markdown": Path(args.markdown_out) if args.markdown_out else default_stem.with_suffix(".md"),
        "json": json_path,
        "cards": Path(args.cards_out) if args.cards_out else json_path.with_name(f"{json_path.stem}_cards.json"),
    }


def scope_from_dict(data: dict[str, Any]) -> draft.ScopeDefinition:
    return draft.ScopeDefinition(
        name=data.get("name", "").strip(),
        query_terms=list(data.get("query_terms", [])),
        extracted_terms=list(data.get("extracted_terms", [])),
        auto_suggested=bool(data.get("auto_suggested", False)),
        hit_count=int(data.get("hit_count", 0) or 0),
        reason=data.get("reason", ""),
    )


def row_from_dict(data: dict[str, Any]) -> draft.DraftRow:
    payload = dict(data)
    payload.setdefault("review_comment", "")
    payload.setdefault("source_cases", [])
    payload.setdefault("confirmation_reasons", [])
    payload.setdefault("reviewer_focus", "")
    payload.setdefault("boundary_scopes", [])
    payload.setdefault("max_match_score", 0)
    payload.setdefault("max_scope_hits", 0)
    return draft.DraftRow(**payload)


def append_comment(existing: str, new_comment: str) -> str:
    cleaned = draft.normalize_space(new_comment)
    if not cleaned:
        return existing
    current = [line.strip() for line in existing.splitlines() if line.strip()]
    if cleaned not in current:
        current.append(cleaned)
    return "\n".join(current)


def remove_reason_categories(reasons: list[str], categories: set[str]) -> list[str]:
    kept: list[str] = []
    for reason in reasons:
        if "reference" in categories and "跨模块家族类比" in reason:
            continue
        if "scope" in categories and "scope 归属存在边界" in reason:
            continue
        if "score" in categories and ("缺少完整评分字段" in reason or "O/D 评分依据仍不完整" in reason):
            continue
        kept.append(reason)
    return kept


def rebuild_score_reason(row: draft.DraftRow) -> list[str]:
    missing_scores = [label for label, value in [("S", row.severity), ("O", row.occurrence), ("D", row.detection)] if not value]
    if missing_scores:
        return [f"源案例缺少完整评分字段：{'/'.join(missing_scores)}"]
    if not row.occurrence or not row.detection:
        return ["O/D 评分依据仍不完整"]
    return []


def rebuild_reviewer_focus(row: draft.DraftRow) -> str:
    focus_points: list[str] = []
    if any("scope 归属存在边界" in reason for reason in row.confirmation_reasons):
        focus_points.append("确认 scope 归属与责任边界")
    if any("跨模块家族类比" in reason for reason in row.confirmation_reasons):
        focus_points.append("确认该类比是否适用于当前模块机理、接口和责任范围")
    if any("缺少完整评分字段" in reason or "O/D 评分依据仍不完整" in reason for reason in row.confirmation_reasons):
        focus_points.append("补齐或校准 S/O/D 与现行检测控制")
    if any("模板或知识库" in reason for reason in row.confirmation_reasons):
        focus_points.append("确认是否已经落到具体机理、失效后果和现行控制")
    return "；".join(focus_points)


def refresh_confirmation_state(row: draft.DraftRow, force_confirmed: bool = False) -> None:
    row.reviewer_focus = rebuild_reviewer_focus(row)
    if force_confirmed:
        row.confirmation_status = "confirmed"
        return
    if row.confirmation_reasons:
        row.confirmation_status = "needs expert confirmation"
    elif row.confirmation_status == "draft":
        row.confirmation_status = "draft"
    else:
        row.confirmation_status = "confirmed"


def ensure_scope(scopes: list[draft.ScopeDefinition], new_scope_name: str, reason: str) -> None:
    if any(scope.name == new_scope_name for scope in scopes):
        return
    scopes.append(
        draft.ScopeDefinition(
            name=new_scope_name,
            query_terms=[],
            extracted_terms=[],
            auto_suggested=False,
            hit_count=0,
            reason=reason,
        )
    )


def row_identity(row: draft.DraftRow) -> tuple[str, str]:
    return row.scope, draft.row_key(row)


def find_row(rows: list[draft.DraftRow], target: dict[str, Any], aliases: dict[tuple[str, str], draft.DraftRow]) -> draft.DraftRow:
    row_key = draft.normalize_space(target.get("row_key", ""))
    scope = draft.normalize_space(target.get("scope", ""))
    if not row_key:
        raise ValueError("Each mutating review action must include target.row_key.")

    if scope:
        aliased = aliases.get((scope, row_key))
        if aliased in rows:
            return aliased

    exact_matches = [row for row in rows if draft.row_key(row) == row_key and (not scope or row.scope == scope)]
    if len(exact_matches) == 1:
        return exact_matches[0]
    if len(exact_matches) > 1:
        raise ValueError(f"Ambiguous review action target: {scope or '*'} / {row_key}")

    fallback_matches = [row for row in rows if draft.row_key(row) == row_key]
    if len(fallback_matches) == 1:
        return fallback_matches[0]
    if not fallback_matches:
        raise ValueError(f"Could not find review target: {scope or '*'} / {row_key}")
    raise ValueError(f"Ambiguous review action target by row_key only: {row_key}")


def confirm_row_action(row: draft.DraftRow, action: dict[str, Any]) -> None:
    row.confirmation_reasons = []
    row.boundary_scopes = []
    row.reviewer_focus = ""
    row.review_comment = append_comment(row.review_comment, action.get("review_comment", ""))
    if action.get("rating_basis"):
        row.rating_basis = action["rating_basis"]
    refresh_confirmation_state(row, force_confirmed=True)


def confirm_scope_owner_action(scopes: list[draft.ScopeDefinition], row: draft.DraftRow, action: dict[str, Any]) -> None:
    new_scope = draft.normalize_space(action.get("new_scope", ""))
    if not new_scope:
        raise ValueError("confirm_scope_owner requires 'new_scope'.")
    ensure_scope(scopes, new_scope, "review action: scope confirmed by expert")
    row.scope = new_scope
    row.boundary_scopes = []
    row.confirmation_reasons = remove_reason_categories(row.confirmation_reasons, {"scope"})
    row.review_comment = append_comment(row.review_comment, action.get("review_comment", ""))
    refresh_confirmation_state(row)


def confirm_reference_fit_action(row: draft.DraftRow, action: dict[str, Any]) -> bool:
    decision = draft.normalize_space(action.get("decision", "keep")) or "keep"
    if decision not in {"keep", "remove"}:
        raise ValueError("confirm_reference_fit requires decision = keep | remove.")
    row.review_comment = append_comment(row.review_comment, action.get("review_comment", ""))
    if decision == "remove":
        return False
    row.confirmation_reasons = remove_reason_categories(row.confirmation_reasons, {"reference"})
    refresh_confirmation_state(row)
    return True


def confirm_scores_action(row: draft.DraftRow, action: dict[str, Any]) -> None:
    if "severity" in action:
        row.severity = str(action["severity"]).strip()
    if "occurrence" in action:
        row.occurrence = str(action["occurrence"]).strip()
    if "detection" in action:
        row.detection = str(action["detection"]).strip()
    row.rpn = draft.compute_rpn(row.severity, row.occurrence, row.detection, "")
    row.confirmation_reasons = remove_reason_categories(row.confirmation_reasons, {"score"})
    row.confirmation_reasons.extend(
        reason for reason in rebuild_score_reason(row) if reason not in row.confirmation_reasons
    )
    if action.get("rating_basis"):
        row.rating_basis = str(action["rating_basis"]).strip()
    else:
        row.rating_basis = f"经人工确认：S={row.severity or '?'}，O={row.occurrence or '?'}，D={row.detection or '?'}。"
    row.review_comment = append_comment(row.review_comment, action.get("review_comment", ""))
    refresh_confirmation_state(row)


def set_owner_target_action(row: draft.DraftRow, action: dict[str, Any]) -> None:
    if "owner" in action:
        row.owner = str(action["owner"]).strip()
    if "target_date" in action:
        row.target_date = str(action["target_date"]).strip()
    row.review_comment = append_comment(row.review_comment, action.get("review_comment", ""))
    refresh_confirmation_state(row)


def apply_actions(
    scopes: list[draft.ScopeDefinition],
    rows: list[draft.DraftRow],
    actions: list[dict[str, Any]],
) -> dict[str, int]:
    aliases = {row_identity(row): row for row in rows}
    summary = {"applied": 0, "removed": 0, "ignored": 0}

    for action in actions:
        action_id = action.get("action_id", "")
        if action_id not in MUTATING_ACTIONS:
            summary["ignored"] += 1
            continue

        target = action.get("target", {})
        row = find_row(rows, target, aliases)
        original_identity = row_identity(row)
        aliases[original_identity] = row

        if action_id == "confirm_row":
            confirm_row_action(row, action)
        elif action_id == "confirm_scope_owner":
            confirm_scope_owner_action(scopes, row, action)
        elif action_id == "confirm_reference_fit":
            if not confirm_reference_fit_action(row, action):
                rows.remove(row)
                summary["removed"] += 1
                summary["applied"] += 1
                continue
        elif action_id == "confirm_scores":
            confirm_scores_action(row, action)
        elif action_id == "set_owner_target":
            set_owner_target_action(row, action)

        aliases[row_identity(row)] = row
        summary["applied"] += 1

    return summary


def group_scope_rows(scopes: list[draft.ScopeDefinition], rows: list[draft.DraftRow]) -> dict[str, list[draft.DraftRow]]:
    ordered_scopes = [scope.name for scope in scopes]
    for row in rows:
        if row.scope not in ordered_scopes:
            ordered_scopes.append(row.scope)

    scope_rows = {scope_name: [] for scope_name in ordered_scopes}
    for row in rows:
        scope_rows.setdefault(row.scope, []).append(row)

    for scope_name, scope_row_list in scope_rows.items():
        scope_row_list.sort(
            key=lambda item: (
                -(draft.safe_int(item.rpn) or -1),
                -item.max_scope_hits,
                -item.max_match_score,
                item.analysis_object,
                item.failure_mode,
            )
        )
    return scope_rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply OpenClaw review actions back to a generated FMEA draft.")
    parser.add_argument("--input-json", required=True, help="Path to the generated FMEA JSON artifact.")
    parser.add_argument("--actions-json", help="Path to a review action bundle JSON.")
    parser.add_argument("--example-name", help="Example action bundle name from references/openclaw_review_action_examples.json.")
    parser.add_argument("--excel-out", help="Optional output path for the reviewed Excel workbook.")
    parser.add_argument("--markdown-out", help="Optional output path for the reviewed Markdown preview.")
    parser.add_argument("--json-out", help="Optional output path for the reviewed JSON artifact.")
    parser.add_argument("--cards-out", help="Optional output path for the reviewed review-cards JSON.")
    args = parser.parse_args()

    if bool(args.actions_json) == bool(args.example_name):
        raise ValueError("Provide exactly one of --actions-json or --example-name.")

    input_json_path = Path(args.input_json)
    input_payload = json.loads(input_json_path.read_text(encoding="utf-8"))
    bundle, action_source = load_action_bundle(args)

    scopes = [scope_from_dict(item) for item in input_payload.get("scopes", [])]
    rows = [row_from_dict(item) for item in input_payload.get("rows", [])]
    summary = apply_actions(scopes, rows, bundle["actions"])
    scope_rows = group_scope_rows(scopes, rows)

    outputs = derive_output_paths(args, input_json_path)
    payload = draft.build_json_payload(
        input_payload.get("module", ""),
        input_payload.get("fmea_type", "DFMEA"),
        input_payload.get("input_text", ""),
        scopes,
        scope_rows,
    )
    payload["review_action_source"] = action_source
    payload["review_action_summary"] = {
        **summary,
        "requested_actions": len(bundle["actions"]),
        "executed_actions": summary["applied"],
    }

    draft.render_excel_workbook(
        input_payload.get("module", ""),
        input_payload.get("fmea_type", "DFMEA"),
        input_payload.get("input_text", ""),
        scopes,
        scope_rows,
        outputs["excel"],
    )

    outputs["markdown"].parent.mkdir(parents=True, exist_ok=True)
    outputs["markdown"].write_text(
        draft.render_markdown(
            input_payload.get("module", ""),
            input_payload.get("fmea_type", "DFMEA"),
            input_payload.get("input_text", ""),
            scopes,
            scope_rows,
        ),
        encoding="utf-8",
    )

    outputs["json"].parent.mkdir(parents=True, exist_ok=True)
    outputs["json"].write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    cards_payload = build_cards_payload(payload, outputs["json"])
    outputs["cards"].parent.mkdir(parents=True, exist_ok=True)
    outputs["cards"].write_text(json.dumps(cards_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "input_json": str(input_json_path),
                "action_source": action_source,
                "excel_path": str(outputs["excel"]),
                "markdown_path": str(outputs["markdown"]),
                "json_path": str(outputs["json"]),
                "cards_path": str(outputs["cards"]),
                "summary": payload["review_action_summary"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
