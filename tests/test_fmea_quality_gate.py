import sys
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "openclaw-fmea-cocreator/scripts"
sys.path.insert(0, str(SCRIPTS))

import draft_fmea_from_cases as draft  # noqa: E402


def make_row(**overrides):
    values = {
        "scope": "装配工序",
        "analysis_object": "线束装配工位",
        "function": "按SOP完成线束插接并通过扫码追溯",
        "failure_mode": "线束插错接口",
        "effect": "客户现场上电失败，后工序联调停机",
        "severity": "8",
        "cause": "操作员未使用防错夹具且接口外形相似",
        "occurrence": "5",
        "current_controls": "人工目视检查",
        "detection": "6",
        "rpn": "240",
        "recommended_actions": "加强培训",
        "owner": "制造工程师",
        "target_date": "待定",
        "confirmation_status": "draft",
        "rating_basis": "AI草稿",
        "reference_type": "current module",
        "source_cases": [],
    }
    values.update(overrides)
    return draft.DraftRow(**values)


def test_quality_gate_flags_vague_action_and_queues_blocker():
    row = make_row()
    findings = draft.build_quality_gate_findings("PFMEA", {"装配工序": [row]})

    assert any(item.gate == "actionability" and "vague_action" in item.reason_tags for item in findings)

    queue = draft.build_confirmation_queue({"装配工序": [row]}, quality_gate_findings=findings)
    assert any(item.scope == "质量门禁" and item.blocking for item in queue)


def test_quality_gate_flags_dfmea_process_crosstalk():
    row = make_row(
        scope="设计对象",
        analysis_object="控制板",
        function="提供稳定供电和信号控制",
        failure_mode="控制板放行后间歇性失效",
        cause="操作员在工位未按SOP点检，包装入库漏检",
        recommended_actions="增加工位扫码放行记录和首件复核",
    )
    findings = draft.build_quality_gate_findings("DFMEA", {"设计对象": [row]})

    assert any(item.gate == "type_boundary" and item.blocking for item in findings)


def test_json_payload_includes_quality_gate_findings():
    row = make_row()
    scope = draft.ScopeDefinition(name="装配工序", query_terms=["装配", "工装"])
    payload = draft.build_json_payload(
        "线束装配",
        "PFMEA",
        "装配过程包含线束插接、扫码追溯、工装点检和后工序联调。",
        [scope],
        {"装配工序": [row]},
    )

    assert payload["quality_gate_findings"]
    assert any("quality_gate" in item["reason_tags"] for item in payload["confirmation_queue"])


def test_fallback_coverage_rows_are_distinct_and_reviewable():
    scope = draft.ScopeDefinition(name="装配工序", query_terms=["装配", "工装"])
    profile = draft.lifecycle_profile_by_name(scope.name, draft.PFMEA_COVERAGE_PROFILES)
    rows = [draft.fallback_lifecycle_row(scope, profile, "线束装配", index) for index in range(1, 5)]

    assert len({row.failure_mode for row in rows}) == 4
    assert all(row.confirmation_status == "needs expert confirmation" for row in rows)
    assert all("guideword=" in row.rating_basis for row in rows)
    assert all(row.recommended_actions for row in rows)


def test_manual_scope_rows_are_padded_to_minimum():
    scope = draft.ScopeDefinition(name="装配工序", query_terms=["装配", "工装"])
    scope_rows = draft.pad_scope_rows_to_minimum(
        "线束装配",
        [scope],
        {"装配工序": []},
        min_rows=6,
        profiles=draft.PFMEA_COVERAGE_PROFILES,
    )

    rows = scope_rows["装配工序"]
    assert len(rows) == 6
    assert len({row.failure_mode for row in rows}) == 6
    assert all(row.reference_type == "broader analogy" for row in rows)
