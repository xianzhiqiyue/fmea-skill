"""Verify retrieve_cases.py --json-out produces schema expected by merge_and_score.py (M2)."""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "openclaw-fmea-cocreator" / "scripts" / "retrieve_cases.py"


def test_json_out_schema(tmp_path):
    out_file = tmp_path / "evidence.json"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--query", "压缩机 冷媒 液击",
            "--module", "变温系统",
            "--leaf-id", "T.1.5",
            "--json-out", str(out_file),
            "--top-k", "5",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    assert out_file.exists()

    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert payload["leaf_id"] == "T.1.5"
    assert isinstance(payload["matches"], list)
    assert len(payload["matches"]) <= 5
    if payload["matches"]:
        first = payload["matches"][0]
        for key in [
            "source_workbook",
            "source_sheet",
            "source_row",
            "failure_mode_text",
            "cause_text",
            "effect_text",
            "severity",
            "occurrence",
            "detection",
            "match_score",
            "matched_keywords",
        ]:
            assert key in first, f"missing key {key} in {first}"


def test_json_out_no_match_returns_empty(tmp_path):
    out_file = tmp_path / "evidence.json"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--query", "完全不存在的关键词abcxyz",
            "--module", "变温系统",
            "--leaf-id", "T.99.99",
            "--json-out", str(out_file),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert payload["leaf_id"] == "T.99.99"
    assert payload["matches"] == []
