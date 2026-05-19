from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path


HIGH_GRADE = {"evidence-backed", "historical-supported"}


def quarter_of(iso: str) -> str:
    parsed = dt.datetime.fromisoformat(iso)
    quarter = (parsed.month - 1) // 3 + 1
    return f"{parsed.year}-Q{quarter}"


def sanitize(name: str) -> str:
    return re.sub(r"[^\w一-鿿\-]+", "_", name).strip("_") or "unknown"


def should_write_back(row: dict) -> tuple[bool, str]:
    status = row.get("review_status", "pending")
    grade = row.get("evidence_grade", "ai-inferred")
    if status == "promoted":
        return True, "promote_to_case"
    if status == "confirmed" and grade in HIGH_GRADE:
        return True, "confirm"
    return False, ""


def row_to_entry(row: dict, module: str, source_fmea: str, promotion_action: str, case_id: str) -> dict:
    meta = row.get("review_meta", {})
    return {
        "case_id": case_id,
        "module": module,
        "leaf_id": row.get("leaf_id", ""),
        "leaf_name": row.get("leaf_name", ""),
        "failure_mode": row.get("failure_mode", ""),
        "failure_mode_canonical": row["failure_mode_canonical"],
        "cause": row.get("cause", ""),
        "effect": " | ".join(filter(None, [row.get("effect_customer", ""), row.get("effect_system", "")])),
        "current_controls_prevention": row.get("current_controls_prevention", ""),
        "current_controls_detection": row.get("current_controls_detection", ""),
        "recommended_actions": row.get("recommended_actions", []),
        "severity": row["severity"], "occurrence": row["occurrence"], "detection": row["detection"],
        "tags": meta.get("case_tags", []),
        "provenance": {
            "source_fmea": source_fmea,
            "confirmed_at": meta.get("reviewed_at", ""),
            "reviewer": meta.get("reviewer", ""),
            "promotion_action": promotion_action,
            "evidence_grade_at_confirm": row.get("evidence_grade", "ai-inferred"),
            "confidence_at_confirm": row.get("confidence")
        }
    }


def upsert_case(quarter_file: Path, entry: dict) -> None:
    existing: list[dict] = []
    if quarter_file.exists():
        existing = json.loads(quarter_file.read_text(encoding="utf-8"))
    existing_by_canonical = {e["failure_mode_canonical"]: e for e in existing}
    if entry["failure_mode_canonical"] in existing_by_canonical:
        existing_by_canonical[entry["failure_mode_canonical"]] = entry
        merged = list(existing_by_canonical.values())
    else:
        merged = existing + [entry]
    merged.sort(key=lambda e: e["case_id"])
    quarter_file.parent.mkdir(parents=True, exist_ok=True)
    quarter_file.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")


def next_case_id(existing: list[dict], quarter: str) -> str:
    used = set()
    for entry in existing:
        if entry["case_id"].startswith(f"CASE-{quarter}-"):
            try:
                used.add(int(entry["case_id"].rsplit("-", 1)[-1]))
            except ValueError:
                continue
    n = 1
    while n in used:
        n += 1
    return f"CASE-{quarter}-{n:04d}"


def writeback(applied: dict, root: Path, source_fmea: str) -> list[Path]:
    module = applied.get("module_root", "unknown")
    sanitized_module = sanitize(module)
    written: list[Path] = []
    for row in applied.get("rows", []):
        ok, promotion_action = should_write_back(row)
        if not ok:
            continue
        meta = row.get("review_meta", {})
        if "reviewed_at" not in meta:
            continue
        quarter = quarter_of(meta["reviewed_at"])
        quarter_file = root / sanitized_module / f"{quarter}.json"
        existing = json.loads(quarter_file.read_text(encoding="utf-8")) if quarter_file.exists() else []
        existing_by_canonical = {e["failure_mode_canonical"]: e for e in existing}
        if row["failure_mode_canonical"] in existing_by_canonical:
            case_id = existing_by_canonical[row["failure_mode_canonical"]]["case_id"]
        else:
            case_id = next_case_id(existing, quarter)
        entry = row_to_entry(row, module, source_fmea, promotion_action, case_id)
        upsert_case(quarter_file, entry)
        written.append(quarter_file)
    return written


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", required=True, help="fmea_normalized.review_applied.json")
    parser.add_argument("--case-library-root", required=True)
    parser.add_argument("--source-fmea-path", required=True)
    args = parser.parse_args()

    applied = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    root = Path(args.case_library_root)
    written = writeback(applied, root, args.source_fmea_path)
    for path in written:
        print(str(path))


if __name__ == "__main__":
    main()
