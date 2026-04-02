from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = SKILL_DIR.parent
EXAMPLES_PATH = SKILL_DIR / "references" / "openclaw_submission_examples.json"
DRAFT_SCRIPT_PATH = SCRIPT_DIR / "draft_fmea_from_cases.py"
IMPORT_SCRIPT_PATH = SCRIPT_DIR / "import_existing_fmea_excel.py"
REVIEW_CARDS_SCRIPT_PATH = SCRIPT_DIR / "build_openclaw_review_cards.py"

INPUT_BODY_ORDER = [
    "project_name",
    "module_name",
    "function_description",
    "use_scenario",
    "environment",
    "interfaces",
    "design_constraints",
    "historical_issues",
    "current_controls",
    "bom_or_key_parts",
    "customer_impact",
    "attachments_summary",
    "existing_fmea_text",
    "existing_fmea_excel_path",
]

FIELD_LABELS = {
    "project_name": "项目/产品名称",
    "module_name": "模块/分析对象名称",
    "function_description": "功能/要求描述",
    "use_scenario": "使用场景/任务场景",
    "environment": "环境与工况",
    "interfaces": "接口信息",
    "design_constraints": "设计约束",
    "historical_issues": "历史问题/投诉/维修",
    "current_controls": "当前控制/检测/联锁",
    "bom_or_key_parts": "BOM/关键部件",
    "customer_impact": "客户或后工序影响",
    "attachments_summary": "附件摘要",
    "existing_fmea_text": "已有 FMEA 内容",
    "existing_fmea_excel_path": "已有 FMEA Excel 路径",
}

MINIMUM_CORE_FIELDS = ["module_name", "fmea_type", "function_description", "use_scenario"]
MINIMUM_CONTEXT_FIELDS = [
    "environment",
    "interfaces",
    "design_constraints",
    "historical_issues",
    "bom_or_key_parts",
]


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "\n".join(normalize_text(item) for item in value if normalize_text(item))
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line).strip()


def sanitize_stem(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value.strip())
    cleaned = cleaned.strip("_")
    return cleaned or "openclaw_fmea_draft"


def normalize_intent(payload: dict[str, Any]) -> str:
    return normalize_text(payload.get("intent")) or "new_fmea_draft"


def uses_existing_excel_import(payload: dict[str, Any]) -> bool:
    intent = normalize_intent(payload)
    return intent in {"review_existing_fmea", "high_risk_review"} and bool(normalize_text(payload.get("existing_fmea_excel_path")))


def payload_output_stem(payload: dict[str, Any]) -> str:
    requested = normalize_text(payload.get("requested_output_name"))
    if requested:
        return Path(requested).stem
    if uses_existing_excel_import(payload):
        module_name = normalize_text(payload.get("module_name")) or Path(normalize_text(payload.get("existing_fmea_excel_path"))).stem
        return f"{module_name}_existing_fmea_import"
    module_name = normalize_text(payload.get("module_name")) or "未命名模块"
    scope_mode = normalize_text(payload.get("scope_mode")) or "auto"
    return f"{module_name}_{scope_mode}_scope_draft"


def load_examples() -> list[dict[str, Any]]:
    return json.loads(EXAMPLES_PATH.read_text(encoding="utf-8")).get("examples", [])


def load_payload(args: argparse.Namespace) -> tuple[dict[str, Any], str]:
    if args.payload_file:
        payload_path = Path(args.payload_file)
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        return payload, payload_path.stem

    if args.example_name:
        for example in load_examples():
            if example.get("name") == args.example_name:
                return example["payload"], example["name"]
        raise ValueError(f"Could not find example '{args.example_name}' in {EXAMPLES_PATH}.")

    raise ValueError("Provide either --payload-file or --example-name.")


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    intent = normalize_intent(payload)
    import_mode = uses_existing_excel_import(payload)

    if intent == "new_fmea_draft":
        for field in MINIMUM_CORE_FIELDS:
            if not normalize_text(payload.get(field)):
                errors.append(f"缺少必填字段: {field}")
        if not any(normalize_text(payload.get(field)) for field in MINIMUM_CONTEXT_FIELDS):
            errors.append("缺少最小上下文字段: environment/interfaces/design_constraints/historical_issues/bom_or_key_parts 至少需要一个")
    elif intent in {"review_existing_fmea", "high_risk_review"}:
        if not import_mode and not normalize_text(payload.get("existing_fmea_text")):
            errors.append("审查已有 FMEA 时，至少需要 existing_fmea_excel_path 或 existing_fmea_text 其中之一")
    elif intent == "case_library_extract":
        if not normalize_text(payload.get("existing_fmea_text")) and not import_mode:
            errors.append("案例沉淀至少需要 existing_fmea_text 或 existing_fmea_excel_path")

    scope_mode = normalize_text(payload.get("scope_mode")) or "auto"
    if scope_mode not in {"auto", "manual"}:
        errors.append("scope_mode 只能是 auto 或 manual")

    if scope_mode == "manual" and not import_mode:
        scopes = payload.get("scopes") or []
        if not isinstance(scopes, list) or not scopes:
            errors.append("scope_mode=manual 时必须提供 scopes 列表")
        else:
            for index, scope in enumerate(scopes, start=1):
                name = normalize_text(scope.get("name"))
                keywords = normalize_text(scope.get("keywords"))
                if not name or not keywords:
                    errors.append(f"手工 scope 第 {index} 项必须同时提供 name 和 keywords")

    fmea_type = normalize_text(payload.get("fmea_type"))
    if fmea_type and fmea_type not in {"AFMEA", "SFMEA", "DFMEA"}:
        errors.append("fmea_type 只能是 AFMEA / SFMEA / DFMEA")
    if intent == "new_fmea_draft" and not fmea_type:
        errors.append("缺少必填字段: fmea_type")

    return errors


def build_input_text(payload: dict[str, Any]) -> str:
    sections: list[str] = []
    for field in INPUT_BODY_ORDER:
        value = normalize_text(payload.get(field))
        if not value:
            continue
        label = FIELD_LABELS[field]
        sections.append(f"{label}:\n{value}")

    scope_mode = normalize_text(payload.get("scope_mode")) or "auto"
    if scope_mode == "manual":
        scope_blocks = []
        for scope in payload.get("scopes", []):
            name = normalize_text(scope.get("name"))
            keywords = normalize_text(scope.get("keywords"))
            notes = normalize_text(scope.get("notes"))
            block = [f"scope 名称: {name}", f"scope 关键词: {keywords}"]
            if notes:
                block.append(f"scope 说明: {notes}")
            scope_blocks.append("\n".join(block))
        if scope_blocks:
            sections.append("手工 scope 定义:\n" + "\n\n".join(scope_blocks))

    return "\n\n".join(sections).strip() + "\n"


def as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def build_scope_args(payload: dict[str, Any]) -> list[str]:
    scope_mode = normalize_text(payload.get("scope_mode")) or "auto"
    if scope_mode != "manual":
        return []

    args: list[str] = []
    for scope in payload.get("scopes", []):
        name = normalize_text(scope.get("name"))
        keywords = normalize_text(scope.get("keywords")).replace("\n", " ")
        args.extend(["--scope", f"{name}::{keywords}"])
    return args


def resolve_existing_excel_path(payload: dict[str, Any]) -> Path:
    raw_path = Path(normalize_text(payload.get("existing_fmea_excel_path")))
    if raw_path.is_absolute():
        return raw_path
    return PROJECT_ROOT / raw_path


def resolved_output_paths(payload: dict[str, Any], output_dir: Path) -> dict[str, Path | None]:
    stem = sanitize_stem(payload_output_stem(payload))
    include_json_payload = as_bool(payload.get("include_json_payload"), True)
    include_review_cards = as_bool(payload.get("include_review_cards"), True)
    return {
        "input_text": output_dir / f"{stem}_input.txt",
        "excel": output_dir / f"{stem}.xlsx",
        "markdown": output_dir / f"{stem}.md" if as_bool(payload.get("include_markdown_preview"), True) else None,
        "json": output_dir / f"{stem}.json" if include_json_payload else None,
        "cards": output_dir / f"{stem}_cards.json" if include_json_payload and include_review_cards else None,
    }


def build_command(payload: dict[str, Any], input_path: Path, outputs: dict[str, Path | None]) -> list[str]:
    if uses_existing_excel_import(payload):
        command = [
            sys.executable,
            str(IMPORT_SCRIPT_PATH),
            "--input-excel",
            str(resolve_existing_excel_path(payload)),
            "--excel-out",
            str(outputs["excel"]),
            "--context-file",
            str(input_path),
        ]
        if normalize_text(payload.get("module_name")):
            command.extend(["--module", normalize_text(payload["module_name"])])
        if normalize_text(payload.get("fmea_type")):
            command.extend(["--fmea-type", normalize_text(payload["fmea_type"])])
        if outputs["markdown"] is not None:
            command.extend(["--markdown-out", str(outputs["markdown"])])
        if outputs["json"] is not None:
            command.extend(["--json-out", str(outputs["json"])])
        return command

    command = [
        sys.executable,
        str(DRAFT_SCRIPT_PATH),
        "--module",
        normalize_text(payload["module_name"]),
        "--fmea-type",
        normalize_text(payload["fmea_type"]),
        "--input-file",
        str(input_path),
        "--excel-out",
        str(outputs["excel"]),
    ]
    command.extend(build_scope_args(payload))
    if outputs["markdown"] is not None:
        command.extend(["--markdown-out", str(outputs["markdown"])])
    if outputs["json"] is not None:
        command.extend(["--json-out", str(outputs["json"])])
    return command


def run_submission(payload: dict[str, Any], output_dir: Path, dry_run: bool) -> dict[str, Any]:
    errors = validate_payload(payload)
    if errors:
        raise ValueError("\n".join(errors))

    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = resolved_output_paths(payload, output_dir)
    input_text = build_input_text(payload)
    input_path = outputs["input_text"]
    input_path.write_text(input_text, encoding="utf-8")
    command = build_command(payload, input_path, outputs)

    if not dry_run:
        subprocess.run(command, check=True, cwd=PROJECT_ROOT)
        if outputs["json"] is not None and outputs["cards"] is not None:
            subprocess.run(
                [
                    sys.executable,
                    str(REVIEW_CARDS_SCRIPT_PATH),
                    "--input-json",
                    str(outputs["json"]),
                    "--output-json",
                    str(outputs["cards"]),
                ],
                check=True,
                cwd=PROJECT_ROOT,
            )

    return {
        "submission_mode": "existing_fmea_import" if uses_existing_excel_import(payload) else "new_fmea_draft",
        "command": command,
        "input_text_path": str(input_path),
        "excel_path": str(outputs["excel"]),
        "markdown_path": str(outputs["markdown"]) if outputs["markdown"] is not None else None,
        "json_path": str(outputs["json"]) if outputs["json"] is not None else None,
        "cards_path": str(outputs["cards"]) if outputs["cards"] is not None else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Bridge an OpenClaw form payload into the FMEA draft generator.")
    parser.add_argument("--payload-file", help="Path to a JSON payload generated by OpenClaw.")
    parser.add_argument("--example-name", help="Example payload name from references/openclaw_submission_examples.json.")
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "validation" / "openclaw_runs"), help="Directory for generated artifacts.")
    parser.add_argument("--dry-run", action="store_true", help="Only resolve paths and print the command without executing it.")
    parser.add_argument("--print-input", action="store_true", help="Print the merged input text body.")
    args = parser.parse_args()

    payload, source_name = load_payload(args)
    result = run_submission(payload, Path(args.output_dir), args.dry_run)

    print(json.dumps({"source": source_name, **result}, ensure_ascii=False, indent=2))
    if args.print_input:
        print("\n--- input-text ---\n")
        print(Path(result["input_text_path"]).read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
