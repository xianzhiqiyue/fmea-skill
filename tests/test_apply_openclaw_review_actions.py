import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "openclaw-fmea-cocreator/scripts/apply_openclaw_review_actions.py"
NORM = REPO / "tests/fixtures/sample_normalized_for_review.json"
ACTIONS = REPO / "tests/fixtures/sample_review_actions.json"


def run_apply(actions_path, out_path):
    subprocess.run(
        [sys.executable, str(SCRIPT),
         "--input-json", str(NORM),
         "--actions-json", str(actions_path),
         "--output-json", str(out_path)],
        check=True
    )


def test_confirm_sets_review_status(tmp_path):
    out = tmp_path / "applied.json"
    run_apply(ACTIONS, out)
    payload = json.loads(out.read_text(encoding="utf-8"))
    by_id = {r["row_id"]: r for r in payload["rows"]}
    assert by_id["T.1.5/stuck_relay_contact"]["review_status"] == "confirmed"
    assert by_id["T.1.5/stuck_relay_contact"]["review_meta"]["reviewer"] == "u1"


def test_edit_updates_fields_and_recomputes_rpn(tmp_path):
    out = tmp_path / "applied.json"
    run_apply(ACTIONS, out)
    by_id = {r["row_id"]: r for r in json.loads(out.read_text(encoding="utf-8"))["rows"]}
    edited = by_id["T.1.4/evaporator_frosting"]
    assert edited["review_status"] == "edited"
    assert edited["occurrence"] == 5
    assert edited["current_controls_prevention"] == "加热丝预热 30s"
    assert edited["rpn"] == edited["severity"] * edited["occurrence"] * edited["detection"]


def test_reject_marks_row(tmp_path):
    out = tmp_path / "applied.json"
    run_apply(ACTIONS, out)
    by_id = {r["row_id"]: r for r in json.loads(out.read_text(encoding="utf-8"))["rows"]}
    assert by_id["T.1.3/capillary_clog_dust"]["review_status"] == "rejected"
    assert by_id["T.1.3/capillary_clog_dust"]["review_meta"]["reason"] == "已过滤"


def test_idempotent(tmp_path):
    out1 = tmp_path / "a.json"
    out2 = tmp_path / "b.json"
    run_apply(ACTIONS, out1)
    run_apply(ACTIONS, out2)
    assert out1.read_text(encoding="utf-8") == out2.read_text(encoding="utf-8")


def test_last_write_wins(tmp_path):
    actions_doubled = {
        "fmea_normalized_path": str(NORM),
        "actions": [
            {"row_id": "T.1.5/stuck_relay_contact", "action": "confirm", "reviewer": "u1", "reviewed_at": "2026-05-19T10:00:00+08:00"},
            {"row_id": "T.1.5/stuck_relay_contact", "action": "reject", "reviewer": "u3", "reviewed_at": "2026-05-19T11:00:00+08:00", "reason": "再分析后不适用"}
        ]
    }
    actions_path = tmp_path / "ad.json"
    actions_path.write_text(json.dumps(actions_doubled, ensure_ascii=False), encoding="utf-8")
    out = tmp_path / "out.json"
    run_apply(actions_path, out)
    by_id = {r["row_id"]: r for r in json.loads(out.read_text(encoding="utf-8"))["rows"]}
    assert by_id["T.1.5/stuck_relay_contact"]["review_status"] == "rejected"


def test_promote_to_case_implies_confirmed(tmp_path):
    actions = {
        "fmea_normalized_path": str(NORM),
        "actions": [
            {"row_id": "T.1.5/stuck_relay_contact", "action": "promote_to_case",
             "reviewer": "u1", "reviewed_at": "2026-05-19T12:00:00+08:00",
             "case_tags": ["继电器", "感性负载"]}
        ]
    }
    actions_path = tmp_path / "p.json"
    actions_path.write_text(json.dumps(actions, ensure_ascii=False), encoding="utf-8")
    out = tmp_path / "applied.json"
    run_apply(actions_path, out)
    by_id = {r["row_id"]: r for r in json.loads(out.read_text(encoding="utf-8"))["rows"]}
    promoted = by_id["T.1.5/stuck_relay_contact"]
    assert promoted["review_status"] == "promoted"
    assert promoted["review_meta"]["case_tags"] == ["继电器", "感性负载"]


def test_defer_marks_revisit(tmp_path):
    actions = {
        "fmea_normalized_path": str(NORM),
        "actions": [
            {"row_id": "T.1.4/evaporator_frosting", "action": "defer",
             "reviewer": "u1", "reviewed_at": "2026-05-19T13:00:00+08:00", "revisit_after": "2026-06-01"}
        ]
    }
    actions_path = tmp_path / "d.json"
    actions_path.write_text(json.dumps(actions, ensure_ascii=False), encoding="utf-8")
    out = tmp_path / "applied.json"
    run_apply(actions_path, out)
    by_id = {r["row_id"]: r for r in json.loads(out.read_text(encoding="utf-8"))["rows"]}
    deferred = by_id["T.1.4/evaporator_frosting"]
    assert deferred["review_status"] == "deferred"
    assert deferred["review_meta"]["revisit_after"] == "2026-06-01"
