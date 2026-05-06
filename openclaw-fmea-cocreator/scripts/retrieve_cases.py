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
    score: int
    workbook: str
    sheet: str
    theme: str
    excel_row: str
    preview: str
    source: str


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


def collect_matches(query: str, module: str | None) -> list[Match]:
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
            score = score_text(text, terms, module)
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
                    score=score,
                    workbook=workbook,
                    sheet=sheet,
                    theme=theme,
                    excel_row=row.get("__excel_row__", ""),
                    preview=build_preview(row),
                    source=str(json_file.relative_to(SKILL_DIR.parent)),
                )
            )
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
    args = parser.parse_args()

    matches = collect_matches(args.query, args.module)
    if not args.include_supporting:
        allowed_themes = {"dfmea_sample_data", "knowledge_base_template"}
        matches = [match for match in matches if match.theme in allowed_themes]
    if not matches:
        print("No matches found.")
        return
    print_markdown(matches, args.top_k)


if __name__ == "__main__":
    main()
