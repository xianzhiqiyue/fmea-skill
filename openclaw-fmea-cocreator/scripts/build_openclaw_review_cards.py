from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def path_or_none(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None
    return str(path)


def infer_artifact_links(input_json_path: Path) -> dict[str, str | None]:
    stem = input_json_path.stem
    base = input_json_path.with_suffix("")
    excel_path = base.with_suffix(".xlsx")
    markdown_path = base.with_suffix(".md")
    return {
        "json_source": str(input_json_path),
        "excel_workbook": path_or_none(excel_path),
        "markdown_preview": path_or_none(markdown_path),
    }


def reason_tags(reason_text: str) -> list[str]:
    tags: list[str] = []
    if "跨模块家族类比" in reason_text:
        tags.append("family_analogy")
    if "scope 归属存在边界" in reason_text:
        tags.append("scope_boundary")
    if "缺少完整评分字段" in reason_text or "O/D" in reason_text:
        tags.append("score_incomplete")
    if "模板或知识库" in reason_text:
        tags.append("template_source")
    return tags


def confirmation_priority(tags: list[str]) -> str:
    if "scope_boundary" in tags and "family_analogy" in tags:
        return "high"
    if "score_incomplete" in tags or "scope_boundary" in tags or "family_analogy" in tags:
        return "medium"
    return "low"


def rpn_band(rpn_value: int | None) -> str:
    if rpn_value is None:
        return "unknown"
    if rpn_value >= 300:
        return "critical"
    if rpn_value >= 150:
        return "high"
    if rpn_value >= 80:
        return "medium"
    return "low"


def top_risk_priority(rpn_value: int | None) -> str:
    band = rpn_band(rpn_value)
    if band == "critical":
        return "critical"
    if band == "high":
        return "high"
    if band == "medium":
        return "medium"
    return "low"


def confirmation_actions(tags: list[str], reference_type: str) -> list[dict[str, str]]:
    actions = [{"action_id": "confirm_row", "label": "确认该条目"}]
    if "scope_boundary" in tags:
        actions.append({"action_id": "confirm_scope_owner", "label": "确认 scope 归属"})
    if "family_analogy" in tags or reference_type != "current module":
        actions.append({"action_id": "confirm_reference_fit", "label": "确认类比适用性"})
    if "score_incomplete" in tags:
        actions.append({"action_id": "confirm_scores", "label": "补齐或校准评分"})
    actions.append({"action_id": "set_owner_target", "label": "补齐责任人与节点"})
    return actions


def top_risk_actions(reference_type: str, first_action_candidate: str) -> list[dict[str, str]]:
    actions = [{"action_id": "open_source_trace", "label": "查看来源追踪"}]
    if first_action_candidate:
        actions.append({"action_id": "set_owner_target", "label": "补齐责任人与节点"})
    if reference_type != "current module":
        actions.append({"action_id": "confirm_reference_fit", "label": "确认类比适用性"})
    return actions


def build_confirmation_cards(data: dict[str, Any]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for index, item in enumerate(data.get("confirmation_queue", []), start=1):
        tags = reason_tags(item.get("why_confirmation_is_needed", ""))
        cards.append(
            {
                "card_id": f"confirmation-{index:03d}",
                "card_type": "confirmation_review",
                "title": item.get("row_key", "待确认条目"),
                "subtitle": item.get("scope", ""),
                "target": {
                    "scope": item.get("scope", ""),
                    "row_key": item.get("row_key", ""),
                },
                "priority": confirmation_priority(tags),
                "tags": [item.get("reference_type", ""), *tags],
                "payload": {
                    "scope": item.get("scope", ""),
                    "row_key": item.get("row_key", ""),
                    "why_confirmation_is_needed": item.get("why_confirmation_is_needed", ""),
                    "suggested_reviewer_focus": item.get("suggested_reviewer_focus", ""),
                    "review_comment": item.get("review_comment", ""),
                    "reference_type": item.get("reference_type", ""),
                    "source_cases": item.get("source_cases", []),
                    "reason_tags": tags,
                },
                "actions": confirmation_actions(tags, item.get("reference_type", "")),
            }
        )
    return cards


def build_top_risk_cards(data: dict[str, Any]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for index, item in enumerate(data.get("top_risks", []), start=1):
        current_rpn = safe_int(item.get("current_rpn"))
        band = rpn_band(current_rpn)
        cards.append(
            {
                "card_id": f"risk-{index:03d}",
                "card_type": "top_risk_digest",
                "title": item.get("failure_mode", "未命名风险"),
                "subtitle": item.get("scope", ""),
                "target": {
                    "scope": item.get("scope", ""),
                    "row_key": item.get("row_key", ""),
                },
                "priority": top_risk_priority(current_rpn),
                "tags": [band, item.get("reference_type", "")],
                "payload": {
                    "scope": item.get("scope", ""),
                    "row_key": item.get("row_key", ""),
                    "failure_mode": item.get("failure_mode", ""),
                    "current_rpn": current_rpn,
                    "rpn_band": band,
                    "why_it_matters": item.get("why_it_matters", ""),
                    "first_action_candidate": item.get("first_action_candidate", ""),
                    "reference_type": item.get("reference_type", ""),
                },
                "actions": top_risk_actions(item.get("reference_type", ""), item.get("first_action_candidate", "")),
            }
        )
    return cards


def build_cards_payload(data: dict[str, Any], input_json_path: Path) -> dict[str, Any]:
    confirmation_cards = build_confirmation_cards(data)
    top_risk_cards = build_top_risk_cards(data)
    return {
        "cards_version": "0.2.0",
        "module": data.get("module", ""),
        "fmea_type": data.get("fmea_type", ""),
        "summary": {
            "confirmation_count": len(confirmation_cards),
            "top_risk_count": len(top_risk_cards),
        },
        "artifact_links": infer_artifact_links(input_json_path),
        "sections": [
            {
                "section_id": "confirmation_queue",
                "title": "确认队列",
                "card_type": "confirmation_review",
                "cards": confirmation_cards,
            },
            {
                "section_id": "top_risks",
                "title": "Top风险",
                "card_type": "top_risk_digest",
                "cards": top_risk_cards,
            },
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build OpenClaw review cards from a generated FMEA JSON artifact.")
    parser.add_argument("--input-json", required=True, help="Path to the FMEA JSON artifact.")
    parser.add_argument("--output-json", help="Optional path for the review cards JSON.")
    args = parser.parse_args()

    input_json_path = Path(args.input_json)
    data = json.loads(input_json_path.read_text(encoding="utf-8"))
    payload = build_cards_payload(data, input_json_path)

    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
