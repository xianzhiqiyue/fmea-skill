import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "openclaw-fmea-cocreator/scripts/retrieve_cases.py"


def make_case_lib(tmp_path, module, entries):
    root = tmp_path / "case_library"
    folder = root / module
    folder.mkdir(parents=True)
    (folder / "2026-Q2.json").write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")
    return root


def run_retrieve(tmp_path, query, module, case_library_root):
    out = tmp_path / "out.json"
    subprocess.run(
        [sys.executable, str(SCRIPT),
         "--query", query, "--module", module,
         "--case-library-root", str(case_library_root),
         "--json-out", str(out),
         "--leaf-id", "T.1.5",
         "--top-k", "10"],
        check=True
    )
    return json.loads(out.read_text(encoding="utf-8"))


def test_case_library_hit_appears_in_results(tmp_path):
    entries = [{
        "case_id": "CASE-2026-Q2-0001", "module": "变温系统",
        "leaf_name": "控制板卡", "failure_mode": "触点粘连",
        "failure_mode_canonical": "stuck_relay_contact",
        "cause": "感性负载反向电动势", "effect": "压缩机不可控",
        "current_controls_prevention": "选型", "current_controls_detection": "状态机",
        "recommended_actions": [],
        "severity": 9, "occurrence": 7, "detection": 1,
        "provenance": {"source_fmea": "x", "confirmed_at": "2026-05-19T10:00:00+08:00",
                       "reviewer": "u1", "promotion_action": "confirm",
                       "evidence_grade_at_confirm": "evidence-backed"}
    }]
    root = make_case_lib(tmp_path, "变温系统", entries)
    payload = run_retrieve(tmp_path, "继电器 触点 粘连", "变温系统", root)
    kinds = {m["source_kind"] for m in payload["matches"]}
    assert "case_library" in kinds


def test_case_library_match_weighted_1_5x(tmp_path):
    entries = [{
        "case_id": "CASE-2026-Q2-0002", "module": "变温系统",
        "leaf_name": "控制板卡", "failure_mode": "触点粘连",
        "failure_mode_canonical": "stuck_relay_contact",
        "cause": "感性负载", "effect": "不可控",
        "current_controls_prevention": "选型", "current_controls_detection": "状态机",
        "recommended_actions": [],
        "severity": 9, "occurrence": 7, "detection": 1,
        "provenance": {"source_fmea": "x", "confirmed_at": "2026-05-19T10:00:00+08:00",
                       "reviewer": "u1", "promotion_action": "confirm",
                       "evidence_grade_at_confirm": "evidence-backed"}
    }]
    root = make_case_lib(tmp_path, "变温系统", entries)
    payload = run_retrieve(tmp_path, "继电器 触点 粘连", "变温系统", root)
    cl_match = next(m for m in payload["matches"] if m["source_kind"] == "case_library")
    assert cl_match["weight"] == 1.5
    assert cl_match["raw_score"] > 0
    assert cl_match["score"] == pytest.approx(cl_match["raw_score"] * 1.5)
