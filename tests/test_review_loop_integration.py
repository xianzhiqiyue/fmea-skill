import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
APPLY = REPO / "openclaw-fmea-cocreator/scripts/apply_openclaw_review_actions.py"
WRITEBACK = REPO / "openclaw-fmea-cocreator/scripts/confirmed_to_case_library.py"
RETRIEVE = REPO / "openclaw-fmea-cocreator/scripts/retrieve_cases.py"


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def test_full_review_loop_increases_case_library_evidence(tmp_path):
    normalized = {
        "module_root": "变温系统",
        "rows": [
            {
                "row_id": "T.1.5/stuck_relay_contact",
                "leaf_id": "T.1.5", "leaf_name": "控制板卡",
                "scope_path": "T → T.1 → T.1.5",
                "failure_mode": "触点粘连", "failure_mode_canonical": "stuck_relay_contact",
                "cause": "感性负载反向电动势", "effect_customer": "压缩机不可控",
                "effect_system": "温度失控",
                "current_controls_prevention": "选型", "current_controls_detection": "状态机",
                "recommended_actions": ["增加 RC"],
                "severity": 9, "occurrence": 7, "detection": 1, "rpn": 63,
                "evidence_grade": "evidence-backed", "confidence": 0.78,
                "needs_human_confirmation": False, "source_traces": []
            }
        ],
        "top_risks": ["T.1.5/stuck_relay_contact"],
        "confirmation_queue": [], "coverage_gaps": []
    }
    norm_path = tmp_path / "fmea_normalized.json"
    write_json(norm_path, normalized)

    actions = {
        "fmea_normalized_path": str(norm_path),
        "actions": [{
            "row_id": "T.1.5/stuck_relay_contact", "action": "confirm",
            "reviewer": "u1", "reviewed_at": "2026-05-19T10:00:00+08:00"
        }]
    }
    actions_path = tmp_path / "actions.json"
    write_json(actions_path, actions)

    applied_path = tmp_path / "applied.json"
    subprocess.run(
        [sys.executable, str(APPLY), "--input-json", str(norm_path),
         "--actions-json", str(actions_path), "--output-json", str(applied_path)],
        check=True
    )

    case_lib_root = tmp_path / "case_library"
    subprocess.run(
        [sys.executable, str(WRITEBACK), "--input-json", str(applied_path),
         "--case-library-root", str(case_lib_root),
         "--source-fmea-path", str(norm_path)],
        check=True
    )
    assert (case_lib_root / "变温系统" / "2026-Q2.json").exists()

    retrieve_out = tmp_path / "retrieved.json"
    subprocess.run(
        [sys.executable, str(RETRIEVE),
         "--query", "继电器 触点 粘连", "--module", "变温系统",
         "--case-library-root", str(case_lib_root),
         "--json-out", str(retrieve_out), "--top-k", "20"],
        check=True
    )
    matches = json.loads(retrieve_out.read_text(encoding="utf-8"))["matches"]
    case_lib_hits = [m for m in matches if m["source_kind"] == "case_library"]
    assert len(case_lib_hits) >= 1
    assert all(abs(h["weight"] - 1.5) < 1e-6 for h in case_lib_hits)
    top_kind = matches[0]["source_kind"]
    assert top_kind == "case_library", f"expected case_library to dominate, got {top_kind}"
