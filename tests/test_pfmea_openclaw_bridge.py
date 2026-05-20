import json
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
DRAFT = REPO / "openclaw-fmea-cocreator/scripts/draft_fmea_from_cases.py"
CARDS = REPO / "openclaw-fmea-cocreator/scripts/build_openclaw_review_cards.py"
SUBMIT = REPO / "openclaw-fmea-cocreator/scripts/run_openclaw_submission.py"


def test_pfmea_draft_json_builds_review_cards(tmp_path):
    draft_json = tmp_path / "pfmea.json"
    cards_json = tmp_path / "pfmea_cards.json"

    subprocess.run(
        [
            sys.executable,
            str(DRAFT),
            "--module",
            "射频功放装配测试过程",
            "--fmea-type",
            "PFMEA",
            "--input-text",
            "装配测试过程包含来料检验、PCBA装配、线束连接、扭矩拧紧、ICT/FCT测试、老炼、包装放行和后工序联调。已有SOP、工装点检、扭矩记录、功能测试和异常品隔离。",
            "--json-out",
            str(draft_json),
            "--markdown-out",
            str(tmp_path / "pfmea.md"),
        ],
        check=True,
    )
    subprocess.run(
        [sys.executable, str(CARDS), "--input-json", str(draft_json), "--output-json", str(cards_json)],
        check=True,
    )

    draft = json.loads(draft_json.read_text(encoding="utf-8"))
    cards = json.loads(cards_json.read_text(encoding="utf-8"))
    assert draft["fmea_type"] == "PFMEA"
    assert draft["rows"]
    assert cards["cards"]


def test_openclaw_submission_pfmea_dry_run(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            str(SUBMIT),
            "--example-name",
            "auto_scope_pfmea_module_assembly",
            "--output-dir",
            str(tmp_path),
            "--dry-run",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["submission_mode"] == "new_fmea_draft"
    assert "--fmea-type" in payload["command"]
    assert "PFMEA" in payload["command"]
    assert payload["cards_path"].endswith("_cards.json")
