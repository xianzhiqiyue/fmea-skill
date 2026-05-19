# FMEA Skill M3 实现计划:案例库飞轮 + OpenClaw 评审写回

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 M2 已能稳定产出的 `fmea_normalized.json + 工作簿` 与人工评审决策连接起来,使确认行回流到 `case_library/`,并被下一次 `retrieve_cases.py` 重新喂回检索池;最终在"再跑一次 FMEA → evidence-backed 比例可观提升"上得到可测量证据,完成自我改进飞轮。

**Architecture:** 一个新脚本 `confirmed_to_case_library.py` (写回侧) + 重做 `apply_openclaw_review_actions.py` (评审动作执行) + `retrieve_cases.py` 扩展检索源 + 两份 OpenClaw 协议 schema (cards / action protocol)。所有评审动作以 JSON 文件描述,脚本 idempotent,允许多次重跑。

**Tech Stack:** Python 3, openpyxl, pytest, jsonschema。无新增依赖。

---

## 文件结构

**新建**:
- `openclaw-fmea-cocreator/scripts/confirmed_to_case_library.py` — 把 review_actions + 工作簿/normalized 中的"已确认行"按模块/季度落到 `case_library/<module>/<YYYY-Q*>.json`。
- `openclaw-fmea-cocreator/scripts/apply_openclaw_review_actions.py` — 把 review_actions 应用到 `fmea_normalized.json` (修改 S/O/D / controls / actions / 标注 reject/defer / 标注 promote_to_case),并产出新的 `fmea_normalized.review_applied.json`。
- `openclaw-fmea-cocreator/scripts/build_openclaw_review_cards.py` — 把 `fmea_normalized.json` 中 `confirmation_queue + top_risks` 渲染为 OpenClaw 评审卡 JSON。
- `openclaw-fmea-cocreator/references/openclaw_review_action_protocol.json` — 5 种动作 (`confirm` / `edit` / `reject` / `defer` / `promote_to_case`) 的 JSON schema。
- `openclaw-fmea-cocreator/references/openclaw_review_cards_schema.json` — 卡片 schema,带 `evidence_grade` 与 `confidence` 显示项。
- `openclaw-fmea-cocreator/references/openclaw_review_action_examples.json` — 5 种动作各一个示例。
- `openclaw-fmea-cocreator/schemas/case_library_entry.schema.json` — `case_library/<module>/<YYYY-Q*>.json` 单条记录 schema。
- `openclaw-fmea-cocreator/schemas/review_actions.schema.json` — 评审动作文件 schema (引用 protocol)。
- `case_library/.gitkeep` — 占位,确认目录在 git 中存在。
- `tests/test_apply_openclaw_review_actions.py` — 5 种动作单测,含 idempotency (重跑结果不变)。
- `tests/test_confirmed_to_case_library.py` — 回填条件、provenance 字段、季度路径切分、idempotent append。
- `tests/test_retrieve_cases_with_case_library.py` — case_library 命中加权 1.5x、源 mix 优先级。
- `tests/test_review_loop_integration.py` — 端到端两轮:同一输入跑一次 FMEA → 模拟评审确认若干行 → 再跑 retrieve_cases → 再合并 → evidence-backed 比例严格上升。
- `tests/fixtures/sample_review_actions.json` — 测试用 review_actions。
- `tests/fixtures/sample_normalized_for_review.json` — 测试用 normalized 输入。
- `tests/fixtures/sample_case_library_entry.json` — 测试用回填后的目标条目。

**修改**:
- `openclaw-fmea-cocreator/scripts/retrieve_cases.py` — 新增检索源 `case_library/**/*.json`,模块同名时 score × 1.5;`--json-out` (M1 已加) 输出包含 `source_kind ∈ {historical, case_library}`。
- `openclaw-fmea-cocreator/SKILL.md` — 加阶段 6 评审写回与飞轮;version 升到 `0.3.0`。
- `openclaw-fmea-cocreator/references/evidence_grading.md` — 末尾追加"`case_library` 来源命中权重 1.5x、回填条件"段。

---

## Task 1: 写 OpenClaw 评审 schema 与示例

**Files:**
- Create: `openclaw-fmea-cocreator/references/openclaw_review_action_protocol.json`
- Create: `openclaw-fmea-cocreator/references/openclaw_review_cards_schema.json`
- Create: `openclaw-fmea-cocreator/references/openclaw_review_action_examples.json`
- Create: `openclaw-fmea-cocreator/schemas/review_actions.schema.json`
- Create: `openclaw-fmea-cocreator/schemas/case_library_entry.schema.json`

- [ ] **Step 1.1: 写 `openclaw_review_action_protocol.json` (协议层规范)**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "openclaw_review_action_protocol",
  "description": "Contract describing the 5 review actions OpenClaw frontend can emit per FMEA row.",
  "actions": {
    "confirm": {
      "purpose": "Reviewer accepts the AI draft row as-is.",
      "required_fields": ["row_id", "action", "reviewer", "reviewed_at"],
      "optional_fields": ["comment"]
    },
    "edit": {
      "purpose": "Reviewer modifies one or more fields. The patch carries new values.",
      "required_fields": ["row_id", "action", "reviewer", "reviewed_at", "patch"],
      "patch_allowed_fields": [
        "severity", "occurrence", "detection",
        "current_controls_prevention", "current_controls_detection",
        "recommended_actions", "owner", "target_date",
        "effect_customer", "effect_system", "cause"
      ]
    },
    "reject": {
      "purpose": "Reviewer marks row as not applicable to current scope.",
      "required_fields": ["row_id", "action", "reviewer", "reviewed_at", "reason"]
    },
    "defer": {
      "purpose": "Reviewer cannot conclude now, asks to revisit.",
      "required_fields": ["row_id", "action", "reviewer", "reviewed_at"],
      "optional_fields": ["revisit_after", "comment"]
    },
    "promote_to_case": {
      "purpose": "Reviewer confirms row AND explicitly requests writing it into case_library as a new historical case.",
      "required_fields": ["row_id", "action", "reviewer", "reviewed_at"],
      "optional_fields": ["case_tags", "case_severity_override", "comment"],
      "note": "Implies confirm semantics. Routes the row to case_library writeback regardless of evidence_grade."
    }
  },
  "ordering": "If multiple actions target the same row_id, last-write-wins by reviewed_at timestamp.",
  "idempotency": "Re-applying the same action file MUST produce the same result. Scripts must read the latest action per row_id rather than appending."
}
```

- [ ] **Step 1.2: 写 `review_actions.schema.json` (验证用 JSON schema)**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "review_actions",
  "type": "object",
  "required": ["fmea_normalized_path", "actions"],
  "properties": {
    "fmea_normalized_path": {"type": "string"},
    "actions": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["row_id", "action", "reviewer", "reviewed_at"],
        "properties": {
          "row_id": {"type": "string"},
          "action": {"enum": ["confirm", "edit", "reject", "defer", "promote_to_case"]},
          "reviewer": {"type": "string"},
          "reviewed_at": {"type": "string", "format": "date-time"},
          "comment": {"type": "string"},
          "reason": {"type": "string"},
          "revisit_after": {"type": "string", "format": "date"},
          "case_tags": {"type": "array", "items": {"type": "string"}},
          "case_severity_override": {"type": "integer", "minimum": 1, "maximum": 10},
          "patch": {
            "type": "object",
            "additionalProperties": false,
            "properties": {
              "severity": {"type": "integer", "minimum": 1, "maximum": 10},
              "occurrence": {"type": "integer", "minimum": 1, "maximum": 10},
              "detection": {"type": "integer", "minimum": 1, "maximum": 10},
              "current_controls_prevention": {"type": "string"},
              "current_controls_detection": {"type": "string"},
              "recommended_actions": {"type": "array", "items": {"type": "string"}},
              "owner": {"type": "string"},
              "target_date": {"type": "string"},
              "effect_customer": {"type": "string"},
              "effect_system": {"type": "string"},
              "cause": {"type": "string"}
            }
          }
        },
        "allOf": [
          {
            "if": {"properties": {"action": {"const": "edit"}}},
            "then": {"required": ["patch"]}
          },
          {
            "if": {"properties": {"action": {"const": "reject"}}},
            "then": {"required": ["reason"]}
          }
        ]
      }
    }
  }
}
```

- [ ] **Step 1.3: 写 `openclaw_review_cards_schema.json`**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "openclaw_review_cards",
  "type": "object",
  "required": ["generated_at", "fmea_normalized_path", "cards"],
  "properties": {
    "generated_at": {"type": "string", "format": "date-time"},
    "fmea_normalized_path": {"type": "string"},
    "cards": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["card_id", "row_id", "queue", "title", "evidence_grade", "confidence", "fields", "available_actions"],
        "properties": {
          "card_id": {"type": "string"},
          "row_id": {"type": "string"},
          "queue": {"enum": ["confirmation_queue", "top_risks"]},
          "title": {"type": "string"},
          "evidence_grade": {
            "enum": ["evidence-backed", "historical-supported", "multi-role-inferred", "ai-inferred", "contradicted"]
          },
          "confidence": {"type": "number", "minimum": 0, "maximum": 1},
          "rpn": {"type": "integer", "minimum": 1, "maximum": 1000},
          "fields": {
            "type": "object",
            "required": ["scope_path", "leaf_name", "failure_mode", "cause", "effect", "current_controls", "recommended_actions", "severity", "occurrence", "detection"],
            "properties": {
              "scope_path": {"type": "string"},
              "leaf_name": {"type": "string"},
              "failure_mode": {"type": "string"},
              "cause": {"type": "string"},
              "effect": {"type": "string"},
              "current_controls": {"type": "string"},
              "recommended_actions": {"type": "array", "items": {"type": "string"}},
              "severity": {"type": "integer"},
              "occurrence": {"type": "integer"},
              "detection": {"type": "integer"}
            }
          },
          "available_actions": {
            "type": "array",
            "items": {"enum": ["confirm", "edit", "reject", "defer", "promote_to_case"]},
            "minItems": 1
          },
          "needs_human_confirmation": {"type": "boolean"},
          "source_traces": {"type": "array", "items": {"type": "object"}}
        }
      }
    }
  }
}
```

- [ ] **Step 1.4: 写 `case_library_entry.schema.json`**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "case_library_entry",
  "type": "object",
  "required": ["case_id", "module", "leaf_name", "failure_mode", "failure_mode_canonical", "cause", "effect", "severity", "occurrence", "detection", "provenance"],
  "properties": {
    "case_id": {"type": "string", "pattern": "^CASE-[0-9]{4}-Q[1-4]-[0-9]{4}$"},
    "module": {"type": "string"},
    "leaf_id": {"type": "string"},
    "leaf_name": {"type": "string"},
    "failure_mode": {"type": "string"},
    "failure_mode_canonical": {"type": "string", "pattern": "^[a-z][a-z0-9_]*$"},
    "cause": {"type": "string"},
    "effect": {"type": "string"},
    "current_controls_prevention": {"type": "string"},
    "current_controls_detection": {"type": "string"},
    "recommended_actions": {"type": "array", "items": {"type": "string"}},
    "severity": {"type": "integer", "minimum": 1, "maximum": 10},
    "occurrence": {"type": "integer", "minimum": 1, "maximum": 10},
    "detection": {"type": "integer", "minimum": 1, "maximum": 10},
    "tags": {"type": "array", "items": {"type": "string"}},
    "provenance": {
      "type": "object",
      "required": ["source_fmea", "confirmed_at", "reviewer", "promotion_action", "evidence_grade_at_confirm"],
      "properties": {
        "source_fmea": {"type": "string"},
        "confirmed_at": {"type": "string", "format": "date-time"},
        "reviewer": {"type": "string"},
        "promotion_action": {"enum": ["confirm", "promote_to_case"]},
        "evidence_grade_at_confirm": {
          "enum": ["evidence-backed", "historical-supported", "multi-role-inferred", "ai-inferred", "contradicted"]
        },
        "confidence_at_confirm": {"type": "number"}
      }
    }
  }
}
```

- [ ] **Step 1.5: 写 `openclaw_review_action_examples.json` (5 个动作各一例)**

```json
{
  "fmea_normalized_path": "validation/mock_10/scenarios/01_rf_power_amp/fmea_normalized.json",
  "actions": [
    {
      "row_id": "T.1.5/stuck_relay_contact",
      "action": "confirm",
      "reviewer": "qa-engineer-01",
      "reviewed_at": "2026-05-19T10:15:00+08:00",
      "comment": "S/O/D 与历史一致,接受"
    },
    {
      "row_id": "T.1.4/evaporator_frosting",
      "action": "edit",
      "reviewer": "design-engineer-02",
      "reviewed_at": "2026-05-19T10:18:00+08:00",
      "patch": {
        "occurrence": 5,
        "current_controls_prevention": "蒸发器加热丝预热 30s + MCU 状态机校验"
      },
      "comment": "O 调整为 5,结合本月返修数据"
    },
    {
      "row_id": "T.1.3/capillary_clog_dust",
      "action": "reject",
      "reviewer": "design-engineer-02",
      "reviewed_at": "2026-05-19T10:20:00+08:00",
      "reason": "本机型用毛细管已过滤,场景不适用"
    },
    {
      "row_id": "T.2.1/probe_signal_drift",
      "action": "defer",
      "reviewer": "reliability-engineer-03",
      "reviewed_at": "2026-05-19T10:25:00+08:00",
      "revisit_after": "2026-06-01",
      "comment": "等待 5 月底加速老化数据"
    },
    {
      "row_id": "T.1.5/relay_arcing_inductive_load",
      "action": "promote_to_case",
      "reviewer": "qa-engineer-01",
      "reviewed_at": "2026-05-19T10:30:00+08:00",
      "case_tags": ["继电器选型", "感性负载"],
      "comment": "已在 3 个项目复现,作为通用案例"
    }
  ]
}
```

- [ ] **Step 1.6: 提交**

```bash
git add openclaw-fmea-cocreator/references/openclaw_review_action_protocol.json \
        openclaw-fmea-cocreator/references/openclaw_review_cards_schema.json \
        openclaw-fmea-cocreator/references/openclaw_review_action_examples.json \
        openclaw-fmea-cocreator/schemas/review_actions.schema.json \
        openclaw-fmea-cocreator/schemas/case_library_entry.schema.json
git commit -m "feat(fmea): M3 add OpenClaw review action protocol & schemas"
```

---

## Task 2: 写 `build_openclaw_review_cards.py`

**Files:**
- Create: `openclaw-fmea-cocreator/scripts/build_openclaw_review_cards.py`
- Test: `tests/test_build_openclaw_review_cards.py`

- [ ] **Step 2.1: 写测试 (失败测试先)**

Create `tests/test_build_openclaw_review_cards.py`:

```python
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
```

- [ ] **Step 2.2: 跑测试确认失败**

Run: `cd /Users/nova/code/fmea-skill && python3 -m pytest tests/test_build_openclaw_review_cards.py -v`
Expected: FAIL with FileNotFoundError 或 module not found。

- [ ] **Step 2.3: 写脚本**

Create `openclaw-fmea-cocreator/scripts/build_openclaw_review_cards.py`:

```python
from __future__ import annotations

import argparse
import datetime as dt
import json
import uuid
from pathlib import Path


ALL_ACTIONS = ["confirm", "edit", "reject", "defer", "promote_to_case"]


def row_to_card(row: dict, queue: str) -> dict:
    return {
        "card_id": f"card-{uuid.uuid4().hex[:8]}",
        "row_id": row["row_id"],
        "queue": queue,
        "title": f"{row.get('leaf_name', '')} | {row.get('failure_mode', '')}",
        "evidence_grade": row["evidence_grade"],
        "confidence": row["confidence"],
        "rpn": row.get("rpn"),
        "fields": {
            "scope_path": row.get("scope_path", ""),
            "leaf_name": row.get("leaf_name", ""),
            "failure_mode": row.get("failure_mode", ""),
            "cause": row.get("cause", ""),
            "effect": " | ".join(filter(None, [row.get("effect_customer", ""), row.get("effect_system", "")])),
            "current_controls": " | ".join(filter(None, [row.get("current_controls_prevention", ""), row.get("current_controls_detection", "")])),
            "recommended_actions": row.get("recommended_actions", []),
            "severity": row["severity"],
            "occurrence": row["occurrence"],
            "detection": row["detection"]
        },
        "available_actions": ALL_ACTIONS,
        "needs_human_confirmation": row.get("needs_human_confirmation", False),
        "source_traces": row.get("source_traces", [])
    }


def build_cards(normalized: dict) -> list[dict]:
    rows_by_id = {r["row_id"]: r for r in normalized.get("rows", [])}
    cards: list[dict] = []
    seen: set[str] = set()
    for row_id in normalized.get("top_risks", []):
        if row_id in rows_by_id and row_id not in seen:
            cards.append(row_to_card(rows_by_id[row_id], "top_risks"))
            seen.add(row_id)
    for row_id in normalized.get("confirmation_queue", []):
        if row_id in rows_by_id and row_id not in seen:
            cards.append(row_to_card(rows_by_id[row_id], "confirmation_queue"))
            seen.add(row_id)
    return cards


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", required=True)
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args()

    normalized = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "fmea_normalized_path": args.input_json,
        "cards": build_cards(normalized)
    }
    Path(args.output_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2.4: 跑测试确认通过**

Run: `cd /Users/nova/code/fmea-skill && python3 -m pytest tests/test_build_openclaw_review_cards.py -v`
Expected: PASS

- [ ] **Step 2.5: 提交**

```bash
git add openclaw-fmea-cocreator/scripts/build_openclaw_review_cards.py tests/test_build_openclaw_review_cards.py
git commit -m "feat(fmea): M3 build_openclaw_review_cards script"
```

---

## Task 3: 写 `apply_openclaw_review_actions.py`

**Files:**
- Create: `openclaw-fmea-cocreator/scripts/apply_openclaw_review_actions.py`
- Test: `tests/test_apply_openclaw_review_actions.py`

实现 5 种动作: `confirm` / `edit` / `reject` / `defer` / `promote_to_case`,产物为 `fmea_normalized.review_applied.json`。每行加 `review_status` 与 `review_meta`。Idempotent: 相同 actions 重跑结果不变。

- [ ] **Step 3.1: 写 fixture**

Create `tests/fixtures/sample_normalized_for_review.json`:

```json
{
  "rows": [
    {
      "row_id": "T.1.5/stuck_relay_contact",
      "leaf_id": "T.1.5", "leaf_name": "控制板卡",
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
      "needs_human_confirmation": false,
      "source_traces": []
    },
    {
      "row_id": "T.1.4/evaporator_frosting",
      "leaf_id": "T.1.4", "leaf_name": "蒸发器",
      "scope_path": "T → T.1 → T.1.4",
      "failure_mode": "结霜导致换热衰减",
      "failure_mode_canonical": "evaporator_frosting",
      "cause": "湿度高 + 长时间运行",
      "effect_customer": "降温慢", "effect_system": "热管理失稳",
      "current_controls_prevention": "周期除霜", "current_controls_detection": "温差监测",
      "recommended_actions": ["增加除霜频率"],
      "severity": 6, "occurrence": 7, "detection": 4, "rpn": 168,
      "evidence_grade": "ai-inferred", "confidence": 0.42,
      "needs_human_confirmation": true,
      "source_traces": []
    },
    {
      "row_id": "T.1.3/capillary_clog_dust",
      "leaf_id": "T.1.3", "leaf_name": "毛细管",
      "scope_path": "T → T.1 → T.1.3",
      "failure_mode": "毛细管堵塞",
      "failure_mode_canonical": "capillary_clog_dust",
      "cause": "颗粒物","effect_customer":"流量异常","effect_system":"压力高",
      "current_controls_prevention": "上游过滤", "current_controls_detection": "压力开关",
      "recommended_actions": [],
      "severity": 5, "occurrence": 4, "detection": 5, "rpn": 100,
      "evidence_grade": "ai-inferred", "confidence": 0.40,
      "needs_human_confirmation": true,
      "source_traces": []
    }
  ],
  "top_risks": ["T.1.4/evaporator_frosting", "T.1.5/stuck_relay_contact"],
  "confirmation_queue": ["T.1.4/evaporator_frosting", "T.1.3/capillary_clog_dust"],
  "coverage_gaps": []
}
```

Create `tests/fixtures/sample_review_actions.json`:

```json
{
  "fmea_normalized_path": "tests/fixtures/sample_normalized_for_review.json",
  "actions": [
    {"row_id": "T.1.5/stuck_relay_contact", "action": "confirm", "reviewer": "u1", "reviewed_at": "2026-05-19T10:00:00+08:00"},
    {"row_id": "T.1.4/evaporator_frosting", "action": "edit", "reviewer": "u2", "reviewed_at": "2026-05-19T10:05:00+08:00",
     "patch": {"occurrence": 5, "current_controls_prevention": "加热丝预热 30s"}},
    {"row_id": "T.1.3/capillary_clog_dust", "action": "reject", "reviewer": "u2", "reviewed_at": "2026-05-19T10:10:00+08:00", "reason": "已过滤"}
  ]
}
```

- [ ] **Step 3.2: 写测试 (失败)**

Create `tests/test_apply_openclaw_review_actions.py`:

```python
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
```

Run: `cd /Users/nova/code/fmea-skill && python3 -m pytest tests/test_apply_openclaw_review_actions.py -v`
Expected: FAIL (脚本不存在)。

- [ ] **Step 3.3: 写脚本**

Create `openclaw-fmea-cocreator/scripts/apply_openclaw_review_actions.py`:

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path


PATCH_ALLOWED = {
    "severity", "occurrence", "detection",
    "current_controls_prevention", "current_controls_detection",
    "recommended_actions", "owner", "target_date",
    "effect_customer", "effect_system", "cause"
}

STATUS_BY_ACTION = {
    "confirm": "confirmed",
    "edit": "edited",
    "reject": "rejected",
    "defer": "deferred",
    "promote_to_case": "promoted"
}


def latest_action_per_row(actions: list[dict]) -> dict[str, dict]:
    latest: dict[str, dict] = {}
    for action in actions:
        row_id = action["row_id"]
        if row_id not in latest or action["reviewed_at"] > latest[row_id]["reviewed_at"]:
            latest[row_id] = action
    return latest


def apply_one(row: dict, action: dict) -> dict:
    name = action["action"]
    row = dict(row)
    row["review_status"] = STATUS_BY_ACTION[name]
    meta = {k: v for k, v in action.items() if k not in {"row_id", "action", "patch"}}
    if name == "edit":
        patch = action.get("patch", {})
        for key, value in patch.items():
            if key in PATCH_ALLOWED:
                row[key] = value
        row["rpn"] = row["severity"] * row["occurrence"] * row["detection"]
    if name == "reject":
        row["needs_human_confirmation"] = False
    if name == "promote_to_case":
        row["needs_human_confirmation"] = False
    row["review_meta"] = meta
    return row


def apply_review_actions(normalized: dict, actions_doc: dict) -> dict:
    latest = latest_action_per_row(actions_doc.get("actions", []))
    new_rows = []
    for row in normalized.get("rows", []):
        action = latest.get(row["row_id"])
        if action is None:
            new_rows.append(dict(row, review_status="pending", review_meta={}))
        else:
            new_rows.append(apply_one(row, action))
    out = dict(normalized)
    out["rows"] = new_rows
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", required=True)
    parser.add_argument("--actions-json", required=True)
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args()

    normalized = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    actions = json.loads(Path(args.actions_json).read_text(encoding="utf-8"))
    applied = apply_review_actions(normalized, actions)
    Path(args.output_json).write_text(json.dumps(applied, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3.4: 跑测试确认通过**

Run: `cd /Users/nova/code/fmea-skill && python3 -m pytest tests/test_apply_openclaw_review_actions.py -v`
Expected: PASS (7 个测试)。

- [ ] **Step 3.5: 提交**

```bash
git add openclaw-fmea-cocreator/scripts/apply_openclaw_review_actions.py \
        tests/test_apply_openclaw_review_actions.py \
        tests/fixtures/sample_normalized_for_review.json \
        tests/fixtures/sample_review_actions.json
git commit -m "feat(fmea): M3 apply_openclaw_review_actions with 5 actions"
```

---

## Task 4: 写 `confirmed_to_case_library.py`

**Files:**
- Create: `openclaw-fmea-cocreator/scripts/confirmed_to_case_library.py`
- Create: `case_library/.gitkeep`
- Test: `tests/test_confirmed_to_case_library.py`

**回填条件 (来自 spec §6.2)**:仅当 `review_status == "promoted"` 或 (`review_status == "confirmed"` 且 `evidence_grade ∈ {evidence-backed, historical-supported}`) 时才回填,避免把 `ai-inferred` 行直接写进案例库形成回声室。

**输出路径**: `case_library/<sanitized_module>/<YYYY-Q*>.json`,季度由 `reviewed_at` 决定。文件已存在则 append (按 `case_id` 去重)。

- [ ] **Step 4.1: 创建占位**

```bash
mkdir -p case_library && touch case_library/.gitkeep
```

- [ ] **Step 4.2: 写 fixture**

Create `tests/fixtures/sample_case_library_entry.json`:

```json
{
  "case_id": "CASE-2026-Q2-0001",
  "module": "变温系统",
  "leaf_id": "T.1.5",
  "leaf_name": "控制板卡",
  "failure_mode": "触点粘连",
  "failure_mode_canonical": "stuck_relay_contact",
  "cause": "感性负载反向电动势",
  "effect": "压缩机不可控 | 温度失控",
  "current_controls_prevention": "选型余量",
  "current_controls_detection": "状态机检测",
  "recommended_actions": ["增加 RC 缓冲"],
  "severity": 9, "occurrence": 7, "detection": 1,
  "tags": [],
  "provenance": {
    "source_fmea": "validation/mock_10/scenarios/01_rf_power_amp/fmea_normalized.json",
    "confirmed_at": "2026-05-19T10:00:00+08:00",
    "reviewer": "u1",
    "promotion_action": "confirm",
    "evidence_grade_at_confirm": "evidence-backed",
    "confidence_at_confirm": 0.78
  }
}
```

- [ ] **Step 4.3: 写测试 (失败)**

Create `tests/test_confirmed_to_case_library.py`:

```python
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
```

Run: `cd /Users/nova/code/fmea-skill && python3 -m pytest tests/test_confirmed_to_case_library.py -v`
Expected: FAIL。

- [ ] **Step 4.4: 写脚本**

Create `openclaw-fmea-cocreator/scripts/confirmed_to_case_library.py`:

```python
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path


HIGH_GRADE = {"evidence-backed", "historical-supported"}


def quarter_of(iso: str) -> str:
    parsed = dt.datetime.fromisoformat(iso)
    quarter = (parsed.month - 1) // 3 + 1
    return f"{parsed.year}-Q{quarter}"


def sanitize(name: str) -> str:
    return re.sub(r"[^\w一-鿿\-]+", "_", name).strip("_") or "unknown"


def should_write_back(row: dict) -> tuple[bool, str]:
    status = row.get("review_status", "pending")
    grade = row.get("evidence_grade", "ai-inferred")
    if status == "promoted":
        return True, "promote_to_case"
    if status == "confirmed" and grade in HIGH_GRADE:
        return True, "confirm"
    return False, ""


def row_to_entry(row: dict, module: str, source_fmea: str, promotion_action: str, case_id: str) -> dict:
    meta = row.get("review_meta", {})
    return {
        "case_id": case_id,
        "module": module,
        "leaf_id": row.get("leaf_id", ""),
        "leaf_name": row.get("leaf_name", ""),
        "failure_mode": row.get("failure_mode", ""),
        "failure_mode_canonical": row["failure_mode_canonical"],
        "cause": row.get("cause", ""),
        "effect": " | ".join(filter(None, [row.get("effect_customer", ""), row.get("effect_system", "")])),
        "current_controls_prevention": row.get("current_controls_prevention", ""),
        "current_controls_detection": row.get("current_controls_detection", ""),
        "recommended_actions": row.get("recommended_actions", []),
        "severity": row["severity"], "occurrence": row["occurrence"], "detection": row["detection"],
        "tags": meta.get("case_tags", []),
        "provenance": {
            "source_fmea": source_fmea,
            "confirmed_at": meta.get("reviewed_at", ""),
            "reviewer": meta.get("reviewer", ""),
            "promotion_action": promotion_action,
            "evidence_grade_at_confirm": row.get("evidence_grade", "ai-inferred"),
            "confidence_at_confirm": row.get("confidence")
        }
    }


def upsert_case(quarter_file: Path, entry: dict) -> None:
    existing: list[dict] = []
    if quarter_file.exists():
        existing = json.loads(quarter_file.read_text(encoding="utf-8"))
    existing_by_canonical = {e["failure_mode_canonical"]: e for e in existing}
    if entry["failure_mode_canonical"] in existing_by_canonical:
        existing_by_canonical[entry["failure_mode_canonical"]] = entry
        merged = list(existing_by_canonical.values())
    else:
        merged = existing + [entry]
    merged.sort(key=lambda e: e["case_id"])
    quarter_file.parent.mkdir(parents=True, exist_ok=True)
    quarter_file.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")


def next_case_id(existing: list[dict], quarter: str) -> str:
    used = set()
    for entry in existing:
        if entry["case_id"].startswith(f"CASE-{quarter}-"):
            try:
                used.add(int(entry["case_id"].rsplit("-", 1)[-1]))
            except ValueError:
                continue
    n = 1
    while n in used:
        n += 1
    return f"CASE-{quarter}-{n:04d}"


def writeback(applied: dict, root: Path, source_fmea: str) -> list[Path]:
    module = applied.get("module_root", "unknown")
    sanitized_module = sanitize(module)
    written: list[Path] = []
    for row in applied.get("rows", []):
        ok, promotion_action = should_write_back(row)
        if not ok:
            continue
        meta = row.get("review_meta", {})
        if "reviewed_at" not in meta:
            continue
        quarter = quarter_of(meta["reviewed_at"])
        quarter_file = root / sanitized_module / f"{quarter}.json"
        existing = json.loads(quarter_file.read_text(encoding="utf-8")) if quarter_file.exists() else []
        existing_by_canonical = {e["failure_mode_canonical"]: e for e in existing}
        if row["failure_mode_canonical"] in existing_by_canonical:
            case_id = existing_by_canonical[row["failure_mode_canonical"]]["case_id"]
        else:
            case_id = next_case_id(existing, quarter)
        entry = row_to_entry(row, module, source_fmea, promotion_action, case_id)
        upsert_case(quarter_file, entry)
        written.append(quarter_file)
    return written


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", required=True, help="fmea_normalized.review_applied.json")
    parser.add_argument("--case-library-root", required=True)
    parser.add_argument("--source-fmea-path", required=True)
    args = parser.parse_args()

    applied = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    root = Path(args.case_library_root)
    written = writeback(applied, root, args.source_fmea_path)
    for path in written:
        print(str(path))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4.5: 跑测试确认通过**

Run: `cd /Users/nova/code/fmea-skill && python3 -m pytest tests/test_confirmed_to_case_library.py -v`
Expected: PASS (7 个测试)。

- [ ] **Step 4.6: 提交**

```bash
git add openclaw-fmea-cocreator/scripts/confirmed_to_case_library.py \
        tests/test_confirmed_to_case_library.py \
        tests/fixtures/sample_case_library_entry.json \
        case_library/.gitkeep
git commit -m "feat(fmea): M3 confirmed_to_case_library writeback"
```

---

## Task 5: 扩展 `retrieve_cases.py` 支持 `case_library/`

**Files:**
- Modify: `openclaw-fmea-cocreator/scripts/retrieve_cases.py`
- Test: `tests/test_retrieve_cases_with_case_library.py`

加权规则 (来自 spec §6.3):同模块的 `case_library/` 命中权重 × 1.5。来源标 `source_kind ∈ {historical, case_library}`。

- [ ] **Step 5.1: 写测试 (失败)**

Create `tests/test_retrieve_cases_with_case_library.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

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
         "--json-out", str(out), "--top-k", "10"],
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


import pytest
```

Run: `cd /Users/nova/code/fmea-skill && python3 -m pytest tests/test_retrieve_cases_with_case_library.py -v`
Expected: FAIL (脚本不支持新参数)。

- [ ] **Step 5.2: 修改 `retrieve_cases.py`**

在文件顶部加导入 / 常量:

```python
CASE_LIBRARY_WEIGHT = 1.5
```

把 `Match` dataclass 扩 2 个字段:

```python
@dataclass
class Match:
    score: float
    workbook: str
    sheet: str
    theme: str
    excel_row: str
    preview: str
    source: str
    source_kind: str = "historical"
    raw_score: float = 0.0
    weight: float = 1.0
```

新增函数,从 `case_library/<module>/*.json` 读取并构造 `Match`:

```python
def load_case_library(root: Path | None, query_terms: list[str], module: str | None) -> list[Match]:
    if root is None or not root.exists() or module is None:
        return []
    canonical = canonicalize_module_name(module)
    candidates = [canonical] if canonical else []
    candidates += ALIASES.get(canonical, []) if canonical else []
    matches: list[Match] = []
    for module_dir in root.iterdir():
        if not module_dir.is_dir() or module_dir.name not in candidates:
            continue
        for quarter_file in sorted(module_dir.glob("*.json")):
            entries = json.loads(quarter_file.read_text(encoding="utf-8"))
            for entry in entries:
                text_parts = [
                    entry.get("leaf_name", ""), entry.get("failure_mode", ""),
                    entry.get("cause", ""), entry.get("effect", "")
                ]
                text = " ".join(filter(None, text_parts))
                raw = score_text(text, query_terms, module)
                if raw <= 0:
                    continue
                weighted = raw * CASE_LIBRARY_WEIGHT
                preview = f"{entry.get('failure_mode', '')} | {entry.get('cause', '')} | {entry.get('effect', '')}"
                matches.append(Match(
                    score=weighted, workbook=quarter_file.parent.name,
                    sheet=quarter_file.stem, theme="case_library",
                    excel_row=entry.get("case_id", ""), preview=preview,
                    source=str(quarter_file), source_kind="case_library",
                    raw_score=float(raw), weight=CASE_LIBRARY_WEIGHT
                ))
    return matches
```

把 `collect_matches` 改为也接收 `case_library_root` 并把 case_library 命中并入:

```python
def collect_matches(query: str, module: str | None, case_library_root: Path | None = None) -> list[Match]:
    terms = expand_terms(query, module)
    matches: list[Match] = []

    for json_file in sorted(DATA_ROOT.glob("*/json/*.json")):
        ...  # 既有逻辑保留
        for row in payload.get("filled_rows", []):
            ...
            matches.append(Match(
                score=float(score), workbook=workbook, sheet=sheet, theme=theme,
                excel_row=row.get("__excel_row__", ""), preview=build_preview(row),
                source=str(json_file.relative_to(SKILL_DIR.parent)),
                source_kind="historical", raw_score=float(score), weight=1.0
            ))

    matches.extend(load_case_library(case_library_root, terms, module))
    matches.sort(key=lambda item: (-item.score, item.workbook, item.sheet, item.excel_row))
    return matches
```

把 `main()` 加 `--case-library-root` / `--json-out` 参数 (后者可能 M1 已加,确保保留),并在 JSON 输出中带上 `source_kind / raw_score / weight`:

```python
parser.add_argument("--case-library-root", default=None)
parser.add_argument("--json-out", default=None)
...
case_lib_root = Path(args.case_library_root) if args.case_library_root else None
matches = collect_matches(args.query, args.module, case_library_root=case_lib_root)
...
if args.json_out:
    payload = {
        "query": args.query, "module": args.module,
        "matches": [
            {
                "score": m.score, "raw_score": m.raw_score, "weight": m.weight,
                "source_kind": m.source_kind,
                "workbook": m.workbook, "sheet": m.sheet, "theme": m.theme,
                "excel_row": m.excel_row, "preview": m.preview, "source": m.source
            } for m in matches[:args.top_k]
        ]
    }
    Path(args.json_out).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
```

- [ ] **Step 5.3: 跑测试确认通过**

Run: `cd /Users/nova/code/fmea-skill && python3 -m pytest tests/test_retrieve_cases_with_case_library.py -v`
Expected: PASS (2 个测试)。

- [ ] **Step 5.4: 跑 M1 已加的 retrieve_cases 测试,确认无回归**

Run: `cd /Users/nova/code/fmea-skill && python3 -m pytest tests/ -k retrieve_cases -v`
Expected: PASS (M1 + M3 测试全过)。

- [ ] **Step 5.5: 提交**

```bash
git add openclaw-fmea-cocreator/scripts/retrieve_cases.py tests/test_retrieve_cases_with_case_library.py
git commit -m "feat(fmea): M3 retrieve_cases reads case_library with 1.5x weight"
```

---

## Task 6: 端到端两轮飞轮集成测试

**Files:**
- Test: `tests/test_review_loop_integration.py`

**断言**:同一输入跑一次 FMEA → 模拟评审确认 N 行 → 把案例库回填 → 再跑 retrieve_cases (输入相同 query) → evidence-backed 比例严格上升 (或 case_library 命中数 > 0 且权重正确)。

- [ ] **Step 6.1: 写测试**

Create `tests/test_review_loop_integration.py`:

```python
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
```

- [ ] **Step 6.2: 跑测试确认通过**

Run: `cd /Users/nova/code/fmea-skill && python3 -m pytest tests/test_review_loop_integration.py -v`
Expected: PASS。

- [ ] **Step 6.3: 提交**

```bash
git add tests/test_review_loop_integration.py
git commit -m "test(fmea): M3 end-to-end review writeback flywheel"
```

---

## Task 7: SKILL.md / evidence_grading.md 加阶段 6 说明,version 0.3.0

**Files:**
- Modify: `openclaw-fmea-cocreator/SKILL.md`
- Modify: `openclaw-fmea-cocreator/references/evidence_grading.md`

- [ ] **Step 7.1: SKILL.md version → 0.3.0**

Edit `openclaw-fmea-cocreator/SKILL.md`,frontmatter `version: 0.3.0-m2` → `version: 0.3.0`。

- [ ] **Step 7.2: SKILL.md 加阶段 6 段落**

在 SKILL.md "Core workflow" 末尾追加:

```markdown
### 6. 评审写回与案例库飞轮 (M3)

完成 `fmea_normalized.json` 与工作簿后,把人工评审与回流闭环:

1. 用 `scripts/build_openclaw_review_cards.py` 从 `fmea_normalized.json` 生成 OpenClaw 评审卡
   ```bash
   python3 scripts/build_openclaw_review_cards.py \
     --input-json /path/to/fmea_normalized.json \
     --output-json /path/to/cards.json
   ```
2. 评审者通过 OpenClaw 产生 `review_actions.json` (5 种动作: confirm/edit/reject/defer/promote_to_case),协议见 [`references/openclaw_review_action_protocol.json`](references/openclaw_review_action_protocol.json)。
3. 用 `scripts/apply_openclaw_review_actions.py` 把动作应用到 normalized JSON
   ```bash
   python3 scripts/apply_openclaw_review_actions.py \
     --input-json /path/to/fmea_normalized.json \
     --actions-json /path/to/review_actions.json \
     --output-json /path/to/fmea_normalized.review_applied.json
   ```
4. 用 `scripts/confirmed_to_case_library.py` 把"已确认 + 高证据等级"或"`promote_to_case`"的行回流到 `case_library/<module>/<YYYY-Q*>.json`
   ```bash
   python3 scripts/confirmed_to_case_library.py \
     --input-json /path/to/fmea_normalized.review_applied.json \
     --case-library-root case_library/ \
     --source-fmea-path /path/to/fmea_normalized.json
   ```
5. 下一次跑 `retrieve_cases.py` 时加 `--case-library-root case_library/`,本企业历史案例命中权重自动 × 1.5,优先级高于通用历史案例。

**回流条件 (避免 echo chamber)**:
- `review_status == "promoted"` (`promote_to_case` 动作) — 无条件回流
- `review_status == "confirmed"` 且 `evidence_grade ∈ {evidence-backed, historical-supported}` — 回流
- 其他情况 (`confirmed + ai-inferred` / `rejected` / `deferred`) — 不回流
```

- [ ] **Step 7.3: SKILL.md 加 case_library 检索调用**

把"### 3. Normalize names and locate similar cases"段中的 retrieve_cases 调用改为带 `--case-library-root`:

```bash
python3 scripts/retrieve_cases.py --query "压缩机 液击 冷媒 泄漏" --module "变温系统" \
    --case-library-root case_library/
```

- [ ] **Step 7.4: evidence_grading.md 追加 case_library 段**

在 evidence_grading.md 末尾追加:

```markdown
## 案例库 (`case_library/`) 来源加权

`scripts/retrieve_cases.py` 在传入 `--case-library-root` 时,会同时检索 `excel_materials/workbooks/**/json/*.json` (通用历史) 与 `case_library/<module>/<YYYY-Q*>.json` (本企业已确认案例)。

后者在同模块命中时按 1.5x 加权,理由:
- 来源是本企业,贴合工艺与组织
- 已经过人工评审确认
- 时间近,与当前问题更相关

合并后按 `score` 排序统一返回,候选行的 `source_kind ∈ {historical, case_library}` 会进入 `evidence_pool/<leaf_id>.json`,后续 `merge_and_score.py` 在 `evidence_strength` 分量中可识别 `case_library` 来源,作为更强证据。

## 回流条件 (`scripts/confirmed_to_case_library.py`)

| `review_status` | `evidence_grade` | 是否回流 |
|---|---|---|
| `promoted` | 任意 | 是 (`promotion_action: promote_to_case`) |
| `confirmed` | `evidence-backed` 或 `historical-supported` | 是 (`promotion_action: confirm`) |
| `confirmed` | `multi-role-inferred` / `ai-inferred` / `contradicted` | 否 |
| `rejected` / `deferred` / `pending` | 任意 | 否 |

不回流 `ai-inferred` + confirmed 是为了避免回声室:LLM 推断 → 评审过快确认 → 回流 → 又被 LLM 当历史依据。要回流必须 `promote_to_case` 显式声明。
```

- [ ] **Step 7.5: 跑全测试**

Run: `cd /Users/nova/code/fmea-skill && python3 -m pytest tests/ -v`
Expected: 全部 PASS (M1 + M2 + M3 测试合计)。

- [ ] **Step 7.6: 提交**

```bash
git add openclaw-fmea-cocreator/SKILL.md openclaw-fmea-cocreator/references/evidence_grading.md
git commit -m "docs(fmea): M3 SKILL.md & evidence_grading add review writeback & case library"
```

---

## Task 8: M3 端到端验收 (mock 场景实跑)

**Files:**
- Create: `docs/superpowers/specs/m3_acceptance_notes.md`

- [ ] **Step 8.1: 在 M2 已经跑过的 `01_rf_power_amp` 场景上模拟 5 个评审动作**

Create `validation/mock_10/scenarios/01_rf_power_amp/review_actions.json` (从该场景 `fmea_normalized.json` 真实 row_id 选 5 个):

```json
{
  "fmea_normalized_path": "validation/mock_10/scenarios/01_rf_power_amp/fmea_normalized.json",
  "actions": [
    {"row_id": "<高 evidence 行>", "action": "confirm", "reviewer": "qa-01", "reviewed_at": "2026-05-19T10:00:00+08:00"},
    {"row_id": "<另一高 evidence>", "action": "edit", "reviewer": "qa-01", "reviewed_at": "2026-05-19T10:05:00+08:00",
     "patch": {"occurrence": 5}},
    {"row_id": "<ai-inferred 行>", "action": "reject", "reviewer": "qa-01", "reviewed_at": "2026-05-19T10:10:00+08:00", "reason": "本机型不适用"},
    {"row_id": "<ai-inferred 行>", "action": "defer", "reviewer": "qa-01", "reviewed_at": "2026-05-19T10:15:00+08:00", "revisit_after": "2026-06-01"},
    {"row_id": "<具复用价值的 ai-inferred>", "action": "promote_to_case", "reviewer": "qa-01", "reviewed_at": "2026-05-19T10:20:00+08:00", "case_tags": ["射频功放"]}
  ]
}
```

实际 `<...>` 占位需要按 fresh subagent 报告的 row_id 替换。让 subagent 用 `jq` 列前 5 行真实 row_id 后填回。

- [ ] **Step 8.2: 跑评审应用**

Run:
```bash
cd /Users/nova/code/fmea-skill && python3 openclaw-fmea-cocreator/scripts/apply_openclaw_review_actions.py \
  --input-json validation/mock_10/scenarios/01_rf_power_amp/fmea_normalized.json \
  --actions-json validation/mock_10/scenarios/01_rf_power_amp/review_actions.json \
  --output-json validation/mock_10/scenarios/01_rf_power_amp/fmea_normalized.review_applied.json
```
Expected: 退出 0,产物文件存在,5 行 `review_status` 分别为 `confirmed/edited/rejected/deferred/promoted`。

- [ ] **Step 8.3: 跑回填**

Run:
```bash
cd /Users/nova/code/fmea-skill && python3 openclaw-fmea-cocreator/scripts/confirmed_to_case_library.py \
  --input-json validation/mock_10/scenarios/01_rf_power_amp/fmea_normalized.review_applied.json \
  --case-library-root case_library/ \
  --source-fmea-path validation/mock_10/scenarios/01_rf_power_amp/fmea_normalized.json
```
Expected: 至少产生 1 个 `case_library/射频功放/2026-Q2.json` (取决于场景 module),包含 `confirm + 高 evidence` 与 `promote_to_case` 共 2 条。`reject/defer` 不出现在文件中。

- [ ] **Step 8.4: 跑第二轮检索证明 case_library 生效**

Run:
```bash
cd /Users/nova/code/fmea-skill && python3 openclaw-fmea-cocreator/scripts/retrieve_cases.py \
  --query "<场景关键词,如 功放 推动管 失谐>" \
  --module "射频功放" \
  --case-library-root case_library/ \
  --json-out validation/mock_10/scenarios/01_rf_power_amp/retrieve_after_review.json \
  --top-k 20
```
Expected: 输出 JSON `matches` 中至少有 1 条 `source_kind == "case_library"`,且 `weight == 1.5`。

- [ ] **Step 8.5: 写验收记录**

Create `docs/superpowers/specs/m3_acceptance_notes.md`:

```markdown
# M3 验收记录

- 日期: <YYYY-MM-DD>
- 单元测试: <PASS/FAIL>
- 端到端 1 个场景:
  - 评审 5 种动作均成功应用: <PASS/FAIL>
  - case_library 回流: <N 条 / 期望 ≥2>
  - 第二轮 retrieve 命中 case_library: <PASS/FAIL>
  - 回声室检查: 是否有 `ai-inferred + confirmed` 错误回流: <无/有>
- 关键回归断言: 单测 7 (apply) + 7 (writeback) + 2 (retrieve) + 1 (loop) = 17 项 PASS
- 结论: <通过/不通过>
```

- [ ] **Step 8.6: 提交**

```bash
git add docs/superpowers/specs/m3_acceptance_notes.md \
        validation/mock_10/scenarios/01_rf_power_amp/review_actions.json \
        validation/mock_10/scenarios/01_rf_power_amp/fmea_normalized.review_applied.json \
        validation/mock_10/scenarios/01_rf_power_amp/retrieve_after_review.json \
        case_library/
git commit -m "docs(fmea): M3 acceptance notes and demo case_library entry"
```

---

## Self-Review 自检

**Spec 覆盖**:
- §6.1 评审动作 5 种 → Task 1 (协议 schema) + Task 3 (apply 脚本) + Task 8 (端到端)
- §6.2 confirmed_to_case_library + 回流条件 → Task 4
- §6.3 retrieve_cases case_library 1.5x 加权 → Task 5
- §6.4 OpenClaw 后端最小耦合 → Task 1 (schema 文件) + Task 2 (build cards)
- 飞轮可测量 → Task 6 (集成测试) + Task 8 (实跑)
- SKILL.md / 文档同步 → Task 7

**Placeholder 扫描**:
- Task 8 中 `<高 evidence 行>` 等占位符是给 subagent 在执行时填的真实 row_id;每处都说明了"按 jq 列前 5 行真实 row_id 后填回",非 plan 失败。
- 无其他 TBD/TODO/implement-later 占位。

**类型一致性**:
- `row_id` (`<leaf_id>/<failure_mode_canonical>`) 在 normalized / cards / actions / writeback / case_library_entry 间一致
- `evidence_grade` 5 状态枚举在 schemas / build_cards / writeback 阈值表 / SKILL.md 间一致
- 5 种动作枚举 `confirm/edit/reject/defer/promote_to_case` 在 protocol / actions schema / apply 脚本 / cards.available_actions 间一致
- `review_status` 5 值 `confirmed/edited/rejected/deferred/promoted` (+ pending 默认) 在 apply / writeback 间一致
- `source_kind ∈ {historical, case_library}` 在 retrieve / 加权逻辑 / 测试断言间一致
- `case_id` 格式 `CASE-YYYY-Q[1-4]-NNNN` 在 schema / writeback / 测试间一致
- `provenance.promotion_action ∈ {confirm, promote_to_case}` 与 writeback 条件分支一致
- 加权常数 1.5 在 retrieve_cases.CASE_LIBRARY_WEIGHT / SKILL.md / evidence_grading.md / 测试断言间一致
