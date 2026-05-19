import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import validate

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "openclaw-fmea-cocreator/scripts/build_openclaw_review_cards.py"
SCHEMA = REPO / "openclaw-fmea-cocreator/references/openclaw_review_cards_schema.json"


@pytest.fixture
def sample_normalized(tmp_path):
    payload = {
        "rows": [
            {
                "row_id": "T.1.5/stuck_relay_contact",
                "leaf_id": "T.1.5",
                "leaf_name": "控制板卡",
                "scope_path": "T → T.1 → T.1.5",
                "failure_mode": "触点粘连",
                "failure_mode_canonical": "stuck_relay_contact",
                "cause": "感性负载反向电动势",
                "effect_customer": "压缩机不可控",
                "effect_system": "温度失控",
                "current_controls_prevention": "选型余量",
                "current_controls_detection": "状态机检测",
                "recommended_actions": ["增加 RC 缓冲"],
                "severity": 9, "occurrence": 7, "detection": 1, "rpn": 63,
                "evidence_grade": "evidence-backed",
                "confidence": 0.78,
                "needs_human_confirmation": False,
                "source_traces": []
            }
        ],
        "top_risks": ["T.1.5/stuck_relay_contact"],
        "confirmation_queue": []
    }
    path = tmp_path / "fmea_normalized.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def test_build_cards_produces_valid_schema(sample_normalized, tmp_path):
    out = tmp_path / "cards.json"
    subprocess.run(
        [sys.executable, str(SCRIPT), "--input-json", str(sample_normalized), "--output-json", str(out)],
        check=True
    )
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    payload = json.loads(out.read_text(encoding="utf-8"))
    validate(instance=payload, schema=schema)
    assert len(payload["cards"]) == 1
    assert payload["cards"][0]["queue"] == "top_risks"
    assert payload["cards"][0]["evidence_grade"] == "evidence-backed"
    assert "confirm" in payload["cards"][0]["available_actions"]
    assert "promote_to_case" in payload["cards"][0]["available_actions"]
