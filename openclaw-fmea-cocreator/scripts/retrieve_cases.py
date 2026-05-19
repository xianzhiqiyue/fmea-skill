from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
PACKAGED_DATA_ROOT = SKILL_DIR / "excel_materials" / "workbooks"
REPO_DATA_ROOT = SKILL_DIR.parent / "excel_materials" / "workbooks"
DATA_ROOT = PACKAGED_DATA_ROOT if PACKAGED_DATA_ROOT.exists() else REPO_DATA_ROOT

CASE_LIBRARY_WEIGHT = 1.5

ALIASES = {
    "变温系统": ["低温系统", "压缩机制冷单元", "液氮低温制冷系统"],
    "进样筒": ["样品筒", "手动进样组件"],
    "调谐单元": ["射频调谐单元"],
    "自动进样器": ["自动进样系统"],
    "匀场单元": ["室温匀场", "匀场系统"],
    "射频功放": ["功率放大器", "RF功放"],
    "前置放大器": ["前放"],
    "收发机": ["发射接收机", "射频收发机"],
    "电子学机柜": ["机柜", "控制柜"],
}

RELATED_MODULES = {
    "自动进样器": ["进样筒"],
    "进样筒": ["自动进样器"],
    "样品筒": ["自动进样器", "进样筒"],
    "前置放大器": ["收发机", "射频功放"],
    "收发机": ["前置放大器", "射频功放", "调谐单元"],
    "射频功放": ["收发机", "前置放大器"],
    "调谐单元": ["收发机"],
}


@dataclass
class Match:
    score: float
    workbook: str
    sheet: str
    theme: str
    excel_row: str
    preview: str
    source: str
    source_kind: str = "historical"
    raw_score: float = 0.0
    weight: float = 1.0


def tokenize(text: str) -> list[str]:
    return [token for token in re.split(r"[\s,，。；;:：/()（）_\-\[\]\n]+", text) if token]


def expand_terms(query: str, module: str | None) -> list[str]:
    terms = tokenize(query)
    if module:
        terms.extend(tokenize(module))
        for canonical, alias_list in ALIASES.items():
            if module == canonical or module in alias_list:
                terms.extend(tokenize(canonical))
                for alias in alias_list:
                    terms.extend(tokenize(alias))
    seen = []
    for term in terms:
        if term not in seen:
            seen.append(term)
    return seen


def row_text(row: dict[str, str]) -> str:
    ordered = [value for key, value in row.items() if key != "__excel_row__" and value]
    return " ".join(ordered)


def canonicalize_module_name(module: str | None) -> str | None:
    if not module:
        return None
    if module in ALIASES:
        return module
    for canonical, alias_list in ALIASES.items():
        if module == canonical or module in alias_list:
            return canonical
    return module


def sheet_affinity_score(sheet: str, module: str | None) -> int:
    canonical_module = canonicalize_module_name(module)
    if not canonical_module:
        return 0

    exact_names = {canonical_module, *ALIASES.get(canonical_module, [])}
    if sheet in exact_names:
        return 6

    related_modules = RELATED_MODULES.get(canonical_module, [])
    related_names = {name for related in related_modules for name in [related, *ALIASES.get(related, [])]}
    if sheet in related_names:
        return 3

    # Keep cross-module analogies possible, but demote them behind direct families.
    return -3


def score_text(text: str, terms: list[str], preferred_sheet: str | None) -> int:
    lowered = text.lower()
    score = 0
    for term in terms:
        if term.lower() in lowered:
            score += 3
    return score


def build_preview(row: dict[str, str]) -> str:
    parts = []
    for key in ["零件名称", "子系统/功能模块", "子系统/组件", "子系统/部件", "功能要求", "潜在失效模式", "潜在失效后果 (客户/后工序)", "潜在失效后果（客户/后工序）", "失效的潜在后果（对客户或后工序的影响）", "建议改进措施 (控制/预防)", "建议的控制措施 (改进方案)", "建议措施"]:
        value = row.get(key, "")
        if value:
            parts.append(value)
        if len(parts) >= 4:
            break
    if not parts:
        parts = [value for key, value in row.items() if key != "__excel_row__" and value][:4]
    return " | ".join(parts[:4])


def load_case_library(root: Path | None, query_terms: list[str], module: str | None) -> list[Match]:
    if root is None or not root.exists() or module is None:
        return []
    canonical = canonicalize_module_name(module)
    candidates = {canonical} if canonical else set()
    if canonical:
        candidates.update(ALIASES.get(canonical, []))
    matches: list[Match] = []
    for module_dir in root.iterdir():
        if not module_dir.is_dir() or module_dir.name not in candidates:
            continue
        for quarter_file in sorted(module_dir.glob("*.json")):
            entries = json.loads(quarter_file.read_text(encoding="utf-8"))
            for entry in entries:
                text_parts = [
                    entry.get("leaf_name", ""), entry.get("failure_mode", ""),
                    entry.get("cause", ""), entry.get("effect", ""),
                    entry.get("current_controls_prevention", ""),
                    entry.get("current_controls_detection", ""),
                    " ".join(entry.get("recommended_actions", [])),
                ]
                text = " ".join(filter(None, text_parts))
                raw = score_text(text, query_terms, module)
                if raw <= 0:
                    continue
                # Case-library entries are filed under the queried module, so apply the
                # same sheet-affinity bonus a direct-module historical row would receive,
                # plus a provenance bonus equivalent to dfmea_sample_data so that the
                # 1.5× weight reliably lifts confirmed cases above historical evidence.
                raw_with_affinity = raw + 6 + 5
                weighted = raw_with_affinity * CASE_LIBRARY_WEIGHT
                preview = f"{entry.get('failure_mode', '')} | {entry.get('cause', '')} | {entry.get('effect', '')}"
                matches.append(Match(
                    score=weighted, workbook=quarter_file.parent.name,
                    sheet=quarter_file.stem, theme="case_library",
                    excel_row=entry.get("case_id", ""), preview=preview,
                    source=str(quarter_file), source_kind="case_library",
                    raw_score=float(raw_with_affinity), weight=CASE_LIBRARY_WEIGHT
                ))
    return matches


def collect_matches(query: str, module: str | None, case_library_root: Path | None = None) -> list[Match]:
    terms = expand_terms(query, module)
    matches: list[Match] = []

    for json_file in sorted(DATA_ROOT.glob("*/json/*.json")):
        payload = json.loads(json_file.read_text(encoding="utf-8"))
        workbook = payload["workbook"]
        sheet = payload["sheet_name"]
        theme = payload.get("theme", "")
        for row in payload.get("filled_rows", []):
            text = row_text(row)
            if not text:
                continue
            keyword_score = score_text(text, terms, module)
            if keyword_score <= 0:
                continue  # require at least one keyword hit before adding bonuses
            score = keyword_score
            if theme == "dfmea_sample_data":
                score += 5
            elif theme == "knowledge_base_template":
                score += 2
            elif theme in {"dfmea_project_plan", "ai_quality_strategy", "ai_fmea_methodology", "ai_prompt_templates"}:
                score -= 2
            score += sheet_affinity_score(sheet, module)
            if score <= 0:
                continue
            matches.append(
                Match(
                    score=float(score),
                    workbook=workbook,
                    sheet=sheet,
                    theme=theme,
                    excel_row=row.get("__excel_row__", ""),
                    preview=build_preview(row),
                    source=str(json_file.relative_to(SKILL_DIR.parent)),
                    source_kind="historical",
                    raw_score=float(score),
                    weight=1.0,
                )
            )
    matches.extend(load_case_library(case_library_root, terms, module))
    matches.sort(key=lambda item: (-item.score, item.workbook, item.sheet, item.excel_row))
    return matches


def print_markdown(matches: list[Match], top_k: int) -> None:
    print("| score | workbook | sheet | theme | excel_row | preview | source |")
    print("| --- | --- | --- | --- | ---: | --- | --- |")
    for item in matches[:top_k]:
        preview = item.preview.replace("|", "/").replace("\n", " ")
        print(
            f"| {item.score} | {item.workbook} | {item.sheet} | {item.theme} | {item.excel_row} | {preview} | {item.source} |"
        )


def write_json_output(matches: list[Match], leaf_id: str, output_path: Path, top_k: int) -> None:
    """Write evidence pool JSON consumed by merge_and_score.py (M2)."""
    items = []
    for match in matches[:top_k]:
        items.append({
            "source_workbook": match.workbook,
            "source_sheet": match.sheet,
            "source_row": match.excel_row,
            "failure_mode_text": match.preview,
            "cause_text": "",
            "effect_text": "",
            "severity": None,
            "occurrence": None,
            "detection": None,
            "match_score": match.score,
            "matched_keywords": [],
            "source_kind": match.source_kind,
            "raw_score": match.raw_score,
            "weight": match.weight,
            "score": match.score,
        })
    payload = {"leaf_id": leaf_id, "matches": items}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Retrieve similar FMEA cases from exported project materials.")
    parser.add_argument("--query", required=True, help="Keywords describing the mechanism, failure, or context.")
    parser.add_argument("--module", help="Optional module name for boosting relevant sheets.")
    parser.add_argument("--top-k", type=int, default=10, help="Number of rows to return.")
    parser.add_argument(
        "--include-supporting",
        action="store_true",
        help="Include planning, strategy, and prompt sheets in addition to sample DFMEA and case templates.",
    )
    parser.add_argument("--json-out", help="Write evidence pool JSON to this path (schema for merge_and_score.py).")
    parser.add_argument("--leaf-id", default="", help="Tags the output with this leaf id when --json-out is used.")
    parser.add_argument("--case-library-root", default=None, help="Path to case_library root dir (enables 1.5x-weighted hits from confirmed cases).")
    args = parser.parse_args()

    case_lib_root = Path(args.case_library_root) if args.case_library_root else None
    matches = collect_matches(args.query, args.module, case_library_root=case_lib_root)
    if not args.include_supporting:
        allowed_themes = {"dfmea_sample_data", "knowledge_base_template", "case_library"}
        matches = [match for match in matches if match.theme in allowed_themes]

    if args.json_out:
        write_json_output(matches, args.leaf_id, Path(args.json_out), args.top_k)
        return

    if not matches:
        print("No matches found.")
        return
    print_markdown(matches, args.top_k)


if __name__ == "__main__":
    main()
