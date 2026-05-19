import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "openclaw-fmea-cocreator/scripts/confirmed_to_case_library.py"


def write_applied(tmp_path, rows, module="变温系统"):
    payload = {"module_root": module, "rows": rows}
    path = tmp_path / "applied.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def run(applied, out_root, source_fmea="src.json"):
    subprocess.run(
        [sys.executable, str(SCRIPT),
         "--input-json", str(applied),
         "--case-library-root", str(out_root),
         "--source-fmea-path", source_fmea],
        check=True
    )


def make_row(row_id, evidence_grade, review_status, reviewed_at="2026-05-19T10:00:00+08:00", **overrides):
    base = {
        "row_id": row_id, "leaf_id": "T.1.5", "leaf_name": "控制板卡",
        "failure_mode": "触点粘连", "failure_mode_canonical": row_id.split("/")[-1],
        "cause": "感性负载", "effect_customer": "不可控", "effect_system": "失控",
        "current_controls_prevention": "选型", "current_controls_detection": "状态机",
        "recommended_actions": ["增加 RC"],
        "severity": 9, "occurrence": 7, "detection": 1, "rpn": 63,
        "evidence_grade": evidence_grade, "confidence": 0.78,
        "review_status": review_status,
        "review_meta": {"reviewer": "u1", "reviewed_at": reviewed_at}
    }
    base.update(overrides)
    return base


def test_confirm_with_high_evidence_writes_back(tmp_path):
    rows = [make_row("T.1.5/stuck_relay_contact", "evidence-backed", "confirmed")]
    applied = write_applied(tmp_path, rows)
    out_root = tmp_path / "case_library"
    run(applied, out_root)
    files = list(out_root.rglob("*.json"))
    assert len(files) == 1
    assert "变温系统" in str(files[0])
    assert "2026-Q2" in files[0].name
    payload = json.loads(files[0].read_text(encoding="utf-8"))
    assert len(payload) == 1
    assert payload[0]["failure_mode_canonical"] == "stuck_relay_contact"
    assert payload[0]["provenance"]["promotion_action"] == "confirm"
    assert payload[0]["provenance"]["evidence_grade_at_confirm"] == "evidence-backed"


def test_confirm_with_ai_inferred_does_not_write(tmp_path):
    rows = [make_row("T.1.5/stuck_relay_contact", "ai-inferred", "confirmed")]
    out_root = tmp_path / "case_library"
    run(write_applied(tmp_path, rows), out_root)
    assert list(out_root.rglob("*.json")) == []


def test_promote_to_case_writes_back_regardless_of_evidence(tmp_path):
    rows = [make_row("T.1.5/relay_arcing", "ai-inferred", "promoted")]
    out_root = tmp_path / "case_library"
    run(write_applied(tmp_path, rows), out_root)
    files = list(out_root.rglob("*.json"))
    assert len(files) == 1
    payload = json.loads(files[0].read_text(encoding="utf-8"))
    assert payload[0]["provenance"]["promotion_action"] == "promote_to_case"


def test_rejected_and_deferred_do_not_write(tmp_path):
    rows = [
        make_row("T.1.3/clog", "evidence-backed", "rejected"),
        make_row("T.1.4/frost", "evidence-backed", "deferred"),
        make_row("T.1.5/pending", "evidence-backed", "pending"),
    ]
    out_root = tmp_path / "case_library"
    run(write_applied(tmp_path, rows), out_root)
    assert list(out_root.rglob("*.json")) == []


def test_quarter_routing(tmp_path):
    rows = [
        make_row("T.1.5/a", "evidence-backed", "confirmed", reviewed_at="2026-02-15T10:00:00+08:00"),
        make_row("T.1.5/b", "evidence-backed", "confirmed", reviewed_at="2026-08-15T10:00:00+08:00"),
    ]
    out_root = tmp_path / "case_library"
    run(write_applied(tmp_path, rows), out_root)
    files = sorted([str(p.name) for p in out_root.rglob("*.json")])
    assert any("2026-Q1" in f for f in files)
    assert any("2026-Q3" in f for f in files)


def test_idempotent_append_dedup_by_failure_mode_canonical(tmp_path):
    rows = [make_row("T.1.5/stuck_relay_contact", "evidence-backed", "confirmed")]
    out_root = tmp_path / "case_library"
    run(write_applied(tmp_path, rows), out_root)
    run(write_applied(tmp_path, rows), out_root)
    files = list(out_root.rglob("*.json"))
    assert len(files) == 1
    payload = json.loads(files[0].read_text(encoding="utf-8"))
    assert len(payload) == 1


def test_case_id_format(tmp_path):
    rows = [make_row("T.1.5/stuck_relay_contact", "evidence-backed", "confirmed")]
    out_root = tmp_path / "case_library"
    run(write_applied(tmp_path, rows), out_root)
    payload = json.loads(next(out_root.rglob("*.json")).read_text(encoding="utf-8"))
    assert payload[0]["case_id"].startswith("CASE-2026-Q2-")
    assert len(payload[0]["case_id"]) == len("CASE-2026-Q2-0001")
