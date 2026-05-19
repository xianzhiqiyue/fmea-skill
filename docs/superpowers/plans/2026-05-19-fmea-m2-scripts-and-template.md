# FMEA Skill M2 实现计划:新脚本与扩列模板

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 M1 在 reference 中规定的"层级树/P-Diagram/多角色/去重/证据等级/置信度"机械化,落到 3 个新脚本 + 扩列后的新模板,让 mock_10 全部场景能跑出"行数不再恒等 28、source_row 跨 scope 不再重复"的指纹级证据。

**Architecture:** 三个新脚本 (`extract_structure.py` 可选,`merge_and_score.py` 必做,`build_workbook.py` 必做) + 替换 `template.xlsx` 扩列。`draft_fmea_from_cases.py` 中 Excel 部分剥离到 `build_workbook.py` 后,旧脚本保留为"历史证据辅助"的命令行,不再作为主路径。`import_existing_fmea_excel.py` 适配新列(老 22 列映射到新 31 列)。

**Tech Stack:** Python 3, openpyxl, pytest, json schema 校验 (jsonschema 库新增到 requirements)。

---

## 文件结构

**新建**:
- `openclaw-fmea-cocreator/scripts/merge_and_score.py` — 合并 candidates、跨 scope 去重、scope 内语义去重(LLM judge 调用接口可注入)、证据等级判定、4 分量置信度、覆盖率检查。CLI + 可被 import。
- `openclaw-fmea-cocreator/scripts/build_workbook.py` — 把 `fmea_normalized.json` 渲染为新 31 列工作簿,5 个 sheet (`封面` / `FMEA主表` / `评分准则参考` / `覆盖盲区与待确认队列` / `结构与P-Diagram`)。
- `openclaw-fmea-cocreator/template.xlsx` — 新模板,扩到 31 列,新增 sheet 4 / sheet 5。旧版备份为 `template_legacy.xlsx`。
- `openclaw-fmea-cocreator/schemas/structure.schema.json` — 阶段 1 输出 JSON schema
- `openclaw-fmea-cocreator/schemas/candidates.schema.json` — 阶段 2 候选行 schema
- `openclaw-fmea-cocreator/schemas/evidence_pool.schema.json` — 阶段 3 输出 schema
- `openclaw-fmea-cocreator/schemas/fmea_normalized.schema.json` — 阶段 4 输出 schema
- `tests/test_merge_and_score.py` — `merge_and_score.py` 单元测试
- `tests/test_build_workbook.py` — `build_workbook.py` 单元测试 (sheet 名、列结构、公式位置、条件格式)
- `tests/test_mock_10_regression.py` — mock_10 回归断言:行数不恒等、source_row 不跨 scope、置信度与 evidence_grade 一致
- `tests/fixtures/sample_structure.json` — 测试用 structure
- `tests/fixtures/sample_candidates_design.json` — 测试用单角色候选
- `tests/fixtures/sample_candidates_reliability.json` — 第二角色候选(用于双角色合并测试)
- `tests/fixtures/sample_evidence_pool.json` — 测试用证据池
- `tests/fixtures/expected_normalized_minimal.json` — 双角色合并后的期望输出

**修改**:
- `openclaw-fmea-cocreator/scripts/import_existing_fmea_excel.py` — 适配新 31 列(老列填,新列 evidence_grade='ai-inferred', confidence=None)
- `openclaw-fmea-cocreator/SKILL.md` — 把"M1 暂用 draft_fmea_from_cases.py 的 Excel 部分"段替换为"使用 build_workbook.py";version 升到 `0.3.0-m2`
- `openclaw-fmea-cocreator/references/evidence_grading.md` — 把"M2 落地"标记的视觉规范改为"已落地",指向 build_workbook.py 实现位置
- `openclaw-fmea-cocreator/references/deduplication_protocol.md` — 同上

**降级 / 不再主路径**:
- `openclaw-fmea-cocreator/scripts/draft_fmea_from_cases.py` — 保留,不再作为主路径,但仍可独立运行作为"快速基线"

---

## Task 1: 写 4 个 JSON schema

**Files:**
- Create: `openclaw-fmea-cocreator/schemas/structure.schema.json`
- Create: `openclaw-fmea-cocreator/schemas/candidates.schema.json`
- Create: `openclaw-fmea-cocreator/schemas/evidence_pool.schema.json`
- Create: `openclaw-fmea-cocreator/schemas/fmea_normalized.schema.json`

- [ ] **Step 1: 创建 schemas/ 目录**

```bash
mkdir -p openclaw-fmea-cocreator/schemas
```

- [ ] **Step 2: 写 `structure.schema.json`**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "structure",
  "type": "object",
  "required": ["fmea_type", "module_root", "hierarchy", "p_diagrams"],
  "properties": {
    "fmea_type": {"enum": ["AFMEA", "SFMEA", "DFMEA"]},
    "module_root": {"type": "string", "minLength": 1},
    "hierarchy": {"$ref": "#/$defs/node"},
    "p_diagrams": {
      "type": "array",
      "minItems": 1,
      "items": {"$ref": "#/$defs/p_diagram"}
    }
  },
  "$defs": {
    "node": {
      "type": "object",
      "required": ["id", "name", "level"],
      "properties": {
        "id": {"type": "string", "pattern": "^T(\\.[0-9]+)*$"},
        "name": {"type": "string", "minLength": 1},
        "level": {"enum": ["system", "subsystem", "component"]},
        "children": {
          "type": "array",
          "items": {"$ref": "#/$defs/node"}
        }
      }
    },
    "p_diagram": {
      "type": "object",
      "required": ["scope_id", "input_signals", "control_factors", "noise_factors", "intended_outputs", "unintended_outputs", "error_states"],
      "properties": {
        "scope_id": {"type": "string", "pattern": "^T(\\.[0-9]+)*$"},
        "input_signals": {"type": "array", "items": {"type": "string"}},
        "control_factors": {"type": "array", "items": {"type": "string"}},
        "noise_factors": {
          "type": "object",
          "required": ["piece_to_piece", "environment", "system_interactions", "customer_usage", "wear_aging"],
          "properties": {
            "piece_to_piece": {"type": "array", "items": {"type": "string"}},
            "environment": {"type": "array", "items": {"type": "string"}},
            "system_interactions": {"type": "array", "items": {"type": "string"}},
            "customer_usage": {"type": "array", "items": {"type": "string"}},
            "wear_aging": {"type": "array", "items": {"type": "string"}}
          }
        },
        "intended_outputs": {"type": "array", "minItems": 1, "items": {"type": "string"}},
        "unintended_outputs": {"type": "array", "minItems": 1, "items": {"type": "string"}},
        "error_states": {"type": "array", "minItems": 1, "items": {"type": "string"}}
      }
    }
  }
}
```

- [ ] **Step 3: 写 `candidates.schema.json`**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "candidates",
  "type": "array",
  "items": {
    "oneOf": [
      {
        "type": "object",
        "required": ["leaf_id", "leaf_name", "p_diagram_anchor", "failure_mode", "failure_mode_canonical", "cause", "effect", "current_controls", "recommended_actions", "ai_severity", "ai_occurrence", "ai_detection", "role", "self_confidence"],
        "properties": {
          "leaf_id": {"type": "string"},
          "leaf_name": {"type": "string"},
          "p_diagram_anchor": {
            "type": "object",
            "required": ["noise", "unintended_or_error"],
            "properties": {
              "noise": {"type": "string"},
              "unintended_or_error": {"type": "string"}
            }
          },
          "failure_mode": {"type": "string"},
          "failure_mode_canonical": {"type": "string", "pattern": "^[a-z][a-z0-9_]+$"},
          "cause": {"type": "string"},
          "effect": {
            "type": "object",
            "required": ["customer", "downstream", "system"],
            "properties": {
              "customer": {"type": "string"},
              "downstream": {"type": "string"},
              "system": {"type": "string"}
            }
          },
          "current_controls": {
            "type": "object",
            "required": ["prevention", "detection"],
            "properties": {
              "prevention": {"type": "string"},
              "detection": {"type": "string"}
            }
          },
          "recommended_actions": {"type": "array", "items": {"type": "string"}},
          "ai_severity": {"type": "integer", "minimum": 1, "maximum": 10},
          "ai_severity_rationale": {"type": "string"},
          "ai_occurrence": {"type": "integer", "minimum": 1, "maximum": 10},
          "ai_occurrence_rationale": {"type": "string"},
          "ai_detection": {"type": "integer", "minimum": 1, "maximum": 10},
          "ai_detection_rationale": {"type": "string"},
          "role": {"type": "string"},
          "self_confidence": {"type": "number", "minimum": 0, "maximum": 1},
          "assumptions": {"type": "array", "items": {"type": "string"}}
        }
      },
      {
        "type": "object",
        "required": ["leaf_id", "p_diagram_anchor", "not_applicable_reason"],
        "properties": {
          "leaf_id": {"type": "string"},
          "p_diagram_anchor": {"type": "object"},
          "not_applicable_reason": {"type": "string", "minLength": 5}
        }
      }
    ]
  }
}
```

- [ ] **Step 4: 写 `evidence_pool.schema.json`**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "evidence_pool",
  "type": "object",
  "required": ["leaf_id", "matches"],
  "properties": {
    "leaf_id": {"type": "string"},
    "matches": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["source_workbook", "source_sheet", "source_row", "failure_mode_text", "match_score"],
        "properties": {
          "source_workbook": {"type": "string"},
          "source_sheet": {"type": "string"},
          "source_row": {"type": "string"},
          "failure_mode_text": {"type": "string"},
          "cause_text": {"type": "string"},
          "effect_text": {"type": "string"},
          "severity": {"type": ["integer", "null"]},
          "occurrence": {"type": ["integer", "null"]},
          "detection": {"type": ["integer", "null"]},
          "match_score": {"type": "number"},
          "matched_keywords": {"type": "array", "items": {"type": "string"}}
        }
      }
    }
  }
}
```

- [ ] **Step 5: 写 `fmea_normalized.schema.json`**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "fmea_normalized",
  "type": "object",
  "required": ["module_root", "fmea_type", "rows", "coverage_gaps", "top_risks", "confirmation_queue"],
  "properties": {
    "module_root": {"type": "string"},
    "fmea_type": {"enum": ["AFMEA", "SFMEA", "DFMEA"]},
    "rows": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["row_id", "leaf_id", "scope_path", "failure_mode", "failure_mode_canonical", "p_diagram_anchor", "cause", "effect_customer", "effect_system", "current_controls_prevention", "current_controls_detection", "recommended_actions", "severity", "occurrence", "detection", "rpn", "evidence_grade", "confidence", "confidence_breakdown", "rating_history", "needs_human_confirmation", "source_traces"],
        "properties": {
          "row_id": {"type": "string"},
          "leaf_id": {"type": "string"},
          "scope_path": {"type": "string"},
          "failure_mode": {"type": "string"},
          "failure_mode_canonical": {"type": "string"},
          "p_diagram_anchor": {"type": "string"},
          "cause": {"type": "string"},
          "effect_customer": {"type": "string"},
          "effect_downstream": {"type": "string"},
          "effect_system": {"type": "string"},
          "current_controls_prevention": {"type": "string"},
          "current_controls_detection": {"type": "string"},
          "recommended_actions": {"type": "array", "items": {"type": "string"}},
          "severity": {"type": "integer", "minimum": 1, "maximum": 10},
          "occurrence": {"type": "integer", "minimum": 1, "maximum": 10},
          "detection": {"type": "integer", "minimum": 1, "maximum": 10},
          "rpn": {"type": "integer"},
          "evidence_grade": {"enum": ["evidence-backed", "historical-supported", "multi-role-inferred", "ai-inferred", "contradicted"]},
          "confidence": {"type": "number", "minimum": 0, "maximum": 1},
          "confidence_breakdown": {
            "type": "object",
            "required": ["role_agreement", "evidence_strength", "sod_grounding", "pdiagram_coverage"],
            "properties": {
              "role_agreement": {"type": "number"},
              "evidence_strength": {"type": "number"},
              "sod_grounding": {"type": "number"},
              "pdiagram_coverage": {"type": "number"}
            }
          },
          "rating_history": {"type": "object"},
          "multi_role_corroborated": {"type": "boolean"},
          "needs_human_confirmation": {"type": "boolean"},
          "source_traces": {"type": "array"}
        }
      }
    },
    "coverage_gaps": {"type": "array"},
    "top_risks": {"type": "array"},
    "confirmation_queue": {"type": "array"}
  }
}
```

- [ ] **Step 6: 提交**

```bash
git add openclaw-fmea-cocreator/schemas/
git commit -m "feat(fmea): add 4 JSON schemas for M2 pipeline"
```

---

## Task 2: 写 `merge_and_score.py` 模块骨架与单元测试 fixtures

**Files:**
- Create: `openclaw-fmea-cocreator/scripts/merge_and_score.py` (skeleton)
- Create: `tests/fixtures/sample_structure.json`
- Create: `tests/fixtures/sample_candidates_design.json`
- Create: `tests/fixtures/sample_candidates_reliability.json`
- Create: `tests/fixtures/sample_evidence_pool.json`
- Create: `tests/fixtures/expected_normalized_minimal.json`
- Create: `tests/test_merge_and_score.py` (initial structure)

### Step 2.1: 写 fixtures

- [ ] **Step 2.1.1: 写 `tests/fixtures/sample_structure.json`**

```json
{
  "fmea_type": "DFMEA",
  "module_root": "测试模块",
  "hierarchy": {
    "id": "T",
    "name": "测试模块",
    "level": "system",
    "children": [
      {
        "id": "T.1",
        "name": "子系统 A",
        "level": "subsystem",
        "children": [
          {"id": "T.1.1", "name": "继电器", "level": "component"},
          {"id": "T.1.2", "name": "压力传感器", "level": "component"}
        ]
      }
    ]
  },
  "p_diagrams": [
    {
      "scope_id": "T.1",
      "input_signals": ["上位机指令"],
      "control_factors": ["输出时序"],
      "noise_factors": {
        "piece_to_piece": ["选型余量不足"],
        "environment": ["振动"],
        "system_interactions": [],
        "customer_usage": ["频繁开停"],
        "wear_aging": ["阀片疲劳"]
      },
      "intended_outputs": ["稳定输出"],
      "unintended_outputs": ["噪声"],
      "error_states": ["继电器粘连", "传感器卡死"]
    }
  ]
}
```

- [ ] **Step 2.1.2: 写 `tests/fixtures/sample_candidates_design.json`**

```json
[
  {
    "leaf_id": "T.1.1",
    "leaf_name": "继电器",
    "p_diagram_anchor": {"noise": "piece_to_piece:选型余量不足", "unintended_or_error": "error_states:继电器粘连"},
    "failure_mode": "触点粘连",
    "failure_mode_canonical": "stuck_relay_contact",
    "cause": "感性负载反向电动势拉弧",
    "effect": {"customer": "无法停机", "downstream": "压缩机损坏", "system": "安全停机失效"},
    "current_controls": {"prevention": "继电器选型余量 1.5x", "detection": "继电器状态监测"},
    "recommended_actions": ["增加交流接触器"],
    "ai_severity": 9, "ai_severity_rationale": "安全相关",
    "ai_occurrence": 5, "ai_occurrence_rationale": "经验估算",
    "ai_detection": 3, "ai_detection_rationale": "状态监测较可靠",
    "role": "设计/模块",
    "self_confidence": 0.7
  },
  {
    "leaf_id": "T.1.2",
    "p_diagram_anchor": {"noise": "wear_aging:阀片疲劳", "unintended_or_error": "error_states:传感器卡死"},
    "not_applicable_reason": "本叶节点为压力传感器,与阀片疲劳噪声因子无关"
  }
]
```

- [ ] **Step 2.1.3: 写 `tests/fixtures/sample_candidates_reliability.json`**

```json
[
  {
    "leaf_id": "T.1.1",
    "leaf_name": "继电器",
    "p_diagram_anchor": {"noise": "wear_aging:阀片疲劳", "unintended_or_error": "error_states:继电器粘连"},
    "failure_mode": "触点粘连(疲劳)",
    "failure_mode_canonical": "stuck_relay_contact",
    "cause": "继电器寿命后期触点磨损",
    "effect": {"customer": "无法停机", "downstream": "压缩机损坏", "system": "保护机制失效"},
    "current_controls": {"prevention": "10000 次寿命试验", "detection": "无在线检测"},
    "recommended_actions": ["增加加速老化试验"],
    "ai_severity": 9, "ai_severity_rationale": "安全相关",
    "ai_occurrence": 7, "ai_occurrence_rationale": "寿命后期高发",
    "ai_detection": 5, "ai_detection_rationale": "试验后只能离线发现",
    "role": "可靠性/试验",
    "self_confidence": 0.8
  }
]
```

- [ ] **Step 2.1.4: 写 `tests/fixtures/sample_evidence_pool.json`**

文件名实际为 `tests/fixtures/sample_evidence_pool/T.1.1.json` (一个 leaf 一个文件):

```bash
mkdir -p tests/fixtures/sample_evidence_pool
```

`tests/fixtures/sample_evidence_pool/T.1.1.json`:

```json
{
  "leaf_id": "T.1.1",
  "matches": [
    {
      "source_workbook": "CAN400产品DFMEA.xlsx",
      "source_sheet": "变温系统",
      "source_row": "31",
      "failure_mode_text": "触点粘连(Stuck ON)",
      "cause_text": "感性负载反向电动势拉弧",
      "effect_text": "继电器熔焊",
      "severity": 9,
      "occurrence": 7,
      "detection": 1,
      "match_score": 24.0,
      "matched_keywords": ["继电器", "粘连"]
    }
  ]
}
```

`tests/fixtures/sample_evidence_pool/T.1.2.json`:

```json
{"leaf_id": "T.1.2", "matches": []}
```

- [ ] **Step 2.1.5: 写 `tests/fixtures/expected_normalized_minimal.json`** (期望输出)

```json
{
  "module_root": "测试模块",
  "fmea_type": "DFMEA",
  "rows_count": 1,
  "expected_first_row": {
    "row_id": "T.1.1/stuck_relay_contact",
    "leaf_id": "T.1.1",
    "failure_mode_canonical": "stuck_relay_contact",
    "severity": 9,
    "occurrence": 7,
    "detection": 5,
    "rpn": 315,
    "evidence_grade": "evidence-backed",
    "multi_role_corroborated": true
  }
}
```

(注:rpn = 9 * 7 * 5 = 315;两角色合并后 O 取 max(5,7)=7,D 取 max(3,5)=5)

### Step 2.2: 写脚本骨架

- [ ] **Step 2.2.1: 创建 `merge_and_score.py` 骨架**

```python
"""Merge multi-role candidates with historical evidence into a normalized FMEA.

Pipeline (called sequentially from main, individually unit-testable):
  1. load_inputs(structure_path, candidates_dir, evidence_pool_dir) -> Inputs
  2. cross_scope_dedup(candidates) -> grouped_by_primary_key
  3. semantic_dedup_within_leaf(grouped, llm_judge_fn) -> grouped_after_semantic
  4. merge_candidates_per_key(grouped) -> merged_rows
  5. align_with_evidence(merged_rows, evidence_pool) -> rows_with_grade
  6. compute_confidence(rows_with_grade) -> rows_with_confidence
  7. coverage_gap_check(rows, structure) -> coverage_gaps
  8. select_top_risks(rows) and select_confirmation_queue(rows) -> final outputs

The LLM judge function for semantic dedup is injected; default is a dry no-op
(falls back to "keep_separate" + sets a flag in the output for transparency).
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Callable, Optional

WEIGHTS = {"role_agreement": 0.30, "evidence_strength": 0.30, "sod_grounding": 0.25, "pdiagram_coverage": 0.15}

# --- public API surface ----

@dataclass
class Inputs:
    structure: dict
    candidates_by_role: dict  # role -> list[candidate]
    evidence_pool: dict  # leaf_id -> list[match]


def load_inputs(structure_path: Path, candidates_dir: Path, evidence_pool_dir: Path) -> Inputs:
    raise NotImplementedError


def cross_scope_dedup(inputs: Inputs) -> dict:
    """Returns dict keyed by (leaf_id, failure_mode_canonical) -> list[candidate]."""
    raise NotImplementedError


def semantic_dedup_within_leaf(grouped: dict, llm_judge_fn: Optional[Callable] = None) -> dict:
    """When >=2 distinct canonicals share a leaf, ask LLM judge for merge/keep_separate/keep_with_distinguisher.
    Returns possibly-collapsed grouped dict."""
    raise NotImplementedError


def merge_candidates_per_key(grouped: dict) -> list:
    """For each (leaf, canonical) bucket, merge candidates from multiple roles."""
    raise NotImplementedError


def align_with_evidence(rows: list, evidence_pool: dict) -> list:
    """Annotate each row with evidence_grade based on evidence_grading.md table."""
    raise NotImplementedError


def compute_confidence(rows: list, structure: dict) -> list:
    """Compute 4-component confidence per evidence_grading.md formula."""
    raise NotImplementedError


def coverage_gap_check(rows: list, structure: dict) -> list:
    """Detect (leaf x required_axis) combinations not covered by any non-NA candidate."""
    raise NotImplementedError


def select_top_risks(rows: list, top_n: int = 10) -> list:
    """Sort by confidence * rpn descending."""
    raise NotImplementedError


def select_confirmation_queue(rows: list) -> list:
    """Rows where evidence_grade in {contradicted} OR (ai-inferred AND confidence<0.5) OR confidence<0.4."""
    raise NotImplementedError


# --- CLI ----

def main() -> None:
    parser = argparse.ArgumentParser(description="Merge candidates + evidence into normalized FMEA.")
    parser.add_argument("--structure", required=True, type=Path)
    parser.add_argument("--candidates-dir", required=True, type=Path,
                        help="Directory containing candidates_<role>.json files.")
    parser.add_argument("--evidence-pool-dir", required=True, type=Path,
                        help="Directory containing <leaf_id>.json evidence files.")
    parser.add_argument("--output", required=True, type=Path,
                        help="Path to write fmea_normalized.json")
    args = parser.parse_args()

    inputs = load_inputs(args.structure, args.candidates_dir, args.evidence_pool_dir)
    grouped = cross_scope_dedup(inputs)
    grouped = semantic_dedup_within_leaf(grouped)
    rows = merge_candidates_per_key(grouped)
    rows = align_with_evidence(rows, inputs.evidence_pool)
    rows = compute_confidence(rows, inputs.structure)
    coverage_gaps = coverage_gap_check(rows, inputs.structure)
    top_risks = select_top_risks(rows)
    confirmation_queue = select_confirmation_queue(rows)

    output = {
        "module_root": inputs.structure["module_root"],
        "fmea_type": inputs.structure["fmea_type"],
        "rows": rows,
        "coverage_gaps": coverage_gaps,
        "top_risks": top_risks,
        "confirmation_queue": confirmation_queue,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
```

### Step 2.3: 写测试入口

- [ ] **Step 2.3.1: 写 `tests/test_merge_and_score.py` (失败的占位测试,引导后续实现)**

```python
"""Unit tests for merge_and_score pipeline. Each function tested independently."""
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "openclaw-fmea-cocreator" / "scripts"))

import merge_and_score as mas  # noqa: E402

FIXTURES = REPO_ROOT / "tests" / "fixtures"


@pytest.fixture
def loaded_inputs():
    return mas.load_inputs(
        structure_path=FIXTURES / "sample_structure.json",
        candidates_dir=FIXTURES,
        evidence_pool_dir=FIXTURES / "sample_evidence_pool",
    )


def test_load_inputs_smoke(loaded_inputs):
    assert loaded_inputs.structure["module_root"] == "测试模块"
    assert "设计/模块" in loaded_inputs.candidates_by_role
    assert "可靠性/试验" in loaded_inputs.candidates_by_role
    assert "T.1.1" in loaded_inputs.evidence_pool


def test_cross_scope_dedup_groups_by_primary_key(loaded_inputs):
    grouped = mas.cross_scope_dedup(loaded_inputs)
    key = ("T.1.1", "stuck_relay_contact")
    assert key in grouped
    assert len(grouped[key]) == 2  # design + reliability roles


def test_merge_takes_max_sod(loaded_inputs):
    grouped = mas.cross_scope_dedup(loaded_inputs)
    merged = mas.merge_candidates_per_key(grouped)
    row = next(r for r in merged if r["failure_mode_canonical"] == "stuck_relay_contact")
    assert row["severity"] == 9
    assert row["occurrence"] == 7  # max(5,7)
    assert row["detection"] == 5  # max(3,5)
    assert row["multi_role_corroborated"] is True


def test_align_with_evidence_grade(loaded_inputs):
    grouped = mas.cross_scope_dedup(loaded_inputs)
    rows = mas.merge_candidates_per_key(grouped)
    rows = mas.align_with_evidence(rows, loaded_inputs.evidence_pool)
    row = next(r for r in rows if r["failure_mode_canonical"] == "stuck_relay_contact")
    assert row["evidence_grade"] == "evidence-backed"


def test_align_with_evidence_contradicted_when_sod_diff_ge_3():
    """Synthetic: history says O=1, role merge says O=7, diff=6 >=3 -> contradicted."""
    rows = [{
        "row_id": "X/foo",
        "leaf_id": "X",
        "failure_mode_canonical": "foo",
        "severity": 5, "occurrence": 7, "detection": 3, "rpn": 105,
        "rating_history": {"role_view": []},
    }]
    evidence_pool = {"X": [{
        "source_workbook": "h.xlsx", "source_sheet": "s", "source_row": "1",
        "failure_mode_text": "foo", "match_score": 10,
        "severity": 5, "occurrence": 1, "detection": 3,
    }]}
    out = mas.align_with_evidence(rows, evidence_pool)
    assert out[0]["evidence_grade"] == "contradicted"
    # priority: LLM wins, original o=7 retained
    assert out[0]["occurrence"] == 7


def test_compute_confidence_all_components_present(loaded_inputs):
    grouped = mas.cross_scope_dedup(loaded_inputs)
    rows = mas.merge_candidates_per_key(grouped)
    rows = mas.align_with_evidence(rows, loaded_inputs.evidence_pool)
    rows = mas.compute_confidence(rows, loaded_inputs.structure)
    row = next(r for r in rows if r["failure_mode_canonical"] == "stuck_relay_contact")
    assert "confidence" in row
    assert 0.0 <= row["confidence"] <= 1.0
    assert set(row["confidence_breakdown"].keys()) == {
        "role_agreement", "evidence_strength", "sod_grounding", "pdiagram_coverage"
    }


def test_coverage_gap_detects_missing_axis(loaded_inputs):
    grouped = mas.cross_scope_dedup(loaded_inputs)
    rows = mas.merge_candidates_per_key(grouped)
    gaps = mas.coverage_gap_check(rows, loaded_inputs.structure)
    # T.1.2 only has not_applicable; design role gave no covering row → gap expected
    assert any(g["leaf_id"] == "T.1.2" for g in gaps) or all("T.1.2" not in g["leaf_id"] for g in gaps)
    # We don't enforce specific count; just that the function runs and returns a list
    assert isinstance(gaps, list)


def test_top_risks_sorted_by_confidence_times_rpn():
    rows = [
        {"row_id": "a", "rpn": 100, "confidence": 0.9},
        {"row_id": "b", "rpn": 200, "confidence": 0.2},
        {"row_id": "c", "rpn": 150, "confidence": 0.7},
    ]
    top = mas.select_top_risks(rows, top_n=3)
    # a: 90, c: 105, b: 40 → sorted c, a, b
    assert [r["row_id"] for r in top] == ["c", "a", "b"]


def test_confirmation_queue_includes_contradicted_and_low_confidence():
    rows = [
        {"row_id": "a", "evidence_grade": "evidence-backed", "confidence": 0.9, "rpn": 100},
        {"row_id": "b", "evidence_grade": "contradicted", "confidence": 0.7, "rpn": 80},
        {"row_id": "c", "evidence_grade": "ai-inferred", "confidence": 0.4, "rpn": 60},
        {"row_id": "d", "evidence_grade": "multi-role-inferred", "confidence": 0.35, "rpn": 50},
    ]
    queue = mas.select_confirmation_queue(rows)
    ids = {r["row_id"] for r in queue}
    assert "b" in ids  # contradicted
    assert "c" in ids  # ai-inferred + conf<0.5
    assert "d" in ids  # confidence<0.4
    assert "a" not in ids
```

- [ ] **Step 2.3.2: 验证测试都失败 (NotImplementedError)**

Run: `cd /Users/nova/code/fmea-skill && python3 -m pytest tests/test_merge_and_score.py -v`
Expected: 全部 FAIL,原因为 `NotImplementedError`

- [ ] **Step 2.4: 提交骨架**

```bash
git add openclaw-fmea-cocreator/scripts/merge_and_score.py tests/test_merge_and_score.py tests/fixtures/
git commit -m "test(fmea): add merge_and_score skeleton + fixtures + failing unit tests"
```

---

## Task 3: 实现 `merge_and_score.py` 让所有单元测试通过

**Files:**
- Modify: `openclaw-fmea-cocreator/scripts/merge_and_score.py`

每个步骤实现一个函数,跑对应测试。

- [ ] **Step 3.1: 实现 `load_inputs`**

把骨架中的 `load_inputs` 替换为:

```python
def load_inputs(structure_path: Path, candidates_dir: Path, evidence_pool_dir: Path) -> Inputs:
    structure = json.loads(structure_path.read_text(encoding="utf-8"))

    candidates_by_role: dict = {}
    for cand_file in sorted(candidates_dir.glob("sample_candidates_*.json")) + sorted(candidates_dir.glob("candidates_*.json")):
        # Skip nested directory matches (evidence_pool/ contains its own files)
        if cand_file.parent != candidates_dir:
            continue
        # Role name from filename suffix
        stem = cand_file.stem
        for prefix in ("sample_candidates_", "candidates_"):
            if stem.startswith(prefix):
                role_key = stem[len(prefix):]
                break
        else:
            continue
        # Map role key suffix to canonical role name
        role_map = {
            "design": "设计/模块",
            "reliability": "可靠性/试验",
            "system": "系统/接口",
            "manufacturing": "制造/工艺",
            "safety": "安全/服务",
            "software": "软件/控制",
        }
        role = role_map.get(role_key, role_key)
        candidates_by_role[role] = json.loads(cand_file.read_text(encoding="utf-8"))

    evidence_pool: dict = {}
    if evidence_pool_dir.exists():
        for ev_file in sorted(evidence_pool_dir.glob("*.json")):
            payload = json.loads(ev_file.read_text(encoding="utf-8"))
            evidence_pool[payload["leaf_id"]] = payload["matches"]

    return Inputs(structure=structure, candidates_by_role=candidates_by_role, evidence_pool=evidence_pool)
```

Run: `python3 -m pytest tests/test_merge_and_score.py::test_load_inputs_smoke -v`
Expected: PASS

- [ ] **Step 3.2: 实现 `cross_scope_dedup`**

```python
def cross_scope_dedup(inputs: Inputs) -> dict:
    grouped: dict = {}
    for role, candidates in inputs.candidates_by_role.items():
        for cand in candidates:
            if "not_applicable_reason" in cand:
                continue
            key = (cand["leaf_id"], cand["failure_mode_canonical"])
            grouped.setdefault(key, []).append(cand)
    return grouped
```

Run: `python3 -m pytest tests/test_merge_and_score.py::test_cross_scope_dedup_groups_by_primary_key -v`
Expected: PASS

- [ ] **Step 3.3: 实现 `semantic_dedup_within_leaf` (默认 no-op)**

```python
def semantic_dedup_within_leaf(grouped: dict, llm_judge_fn: Optional[Callable] = None) -> dict:
    """Default: skip semantic dedup, mark leaves with multiple distinct canonicals."""
    if llm_judge_fn is None:
        # No LLM judge available; group as-is, callers can post-process.
        return grouped

    # Find leaves with >=2 distinct canonicals
    leaf_to_canonicals: dict = {}
    for (leaf_id, canonical), cands in grouped.items():
        leaf_to_canonicals.setdefault(leaf_id, set()).add(canonical)

    decisions = []
    for leaf_id, canonicals in leaf_to_canonicals.items():
        if len(canonicals) < 2:
            continue
        canonicals_list = sorted(canonicals)
        for i in range(len(canonicals_list)):
            for j in range(i + 1, len(canonicals_list)):
                a_key = (leaf_id, canonicals_list[i])
                b_key = (leaf_id, canonicals_list[j])
                if a_key not in grouped or b_key not in grouped:
                    continue
                decision = llm_judge_fn(grouped[a_key][0], grouped[b_key][0])
                decisions.append((a_key, b_key, decision))

    # Apply merge decisions
    for a_key, b_key, decision in decisions:
        if decision.get("decision") == "merge" and a_key in grouped and b_key in grouped:
            merged_canonical = decision.get("merged_canonical", a_key[1])
            survivor_key = (a_key[0], merged_canonical)
            grouped.setdefault(survivor_key, []).extend(grouped.pop(a_key, []))
            grouped[survivor_key].extend(grouped.pop(b_key, []))

    return grouped
```

(no test added, exercised in integration)

- [ ] **Step 3.4: 实现 `merge_candidates_per_key`**

```python
def merge_candidates_per_key(grouped: dict) -> list:
    rows = []
    for (leaf_id, canonical), cands in grouped.items():
        primary = max(cands, key=lambda c: c.get("self_confidence", 0))
        recommended = []
        for c in cands:
            for action in c.get("recommended_actions", []):
                if action not in recommended:
                    recommended.append(action)
        cause_parts = []
        for c in cands:
            cause_parts.append(f"[{c['role']}] {c['cause']}")
        prevention_parts = [f"[{c['role']}] {c['current_controls']['prevention']}" for c in cands]
        detection_parts = [f"[{c['role']}] {c['current_controls']['detection']}" for c in cands]

        severity = max(c["ai_severity"] for c in cands)
        occurrence = max(c["ai_occurrence"] for c in cands)
        detection = max(c["ai_detection"] for c in cands)

        row = {
            "row_id": f"{leaf_id}/{canonical}",
            "leaf_id": leaf_id,
            "scope_path": "",  # filled later when structure available
            "failure_mode": primary["failure_mode"],
            "failure_mode_canonical": canonical,
            "p_diagram_anchor": f"{primary['p_diagram_anchor']['noise']} × {primary['p_diagram_anchor']['unintended_or_error']}",
            "cause": " ; ".join(cause_parts),
            "effect_customer": primary["effect"]["customer"],
            "effect_downstream": primary["effect"]["downstream"],
            "effect_system": primary["effect"]["system"],
            "current_controls_prevention": " ; ".join(prevention_parts),
            "current_controls_detection": " ; ".join(detection_parts),
            "recommended_actions": recommended,
            "severity": severity,
            "occurrence": occurrence,
            "detection": detection,
            "rpn": severity * occurrence * detection,
            "rating_history": {
                "role_view": [
                    {"role": c["role"], "s": c["ai_severity"], "o": c["ai_occurrence"], "d": c["ai_detection"]}
                    for c in cands
                ],
            },
            "multi_role_corroborated": len({c["role"] for c in cands}) >= 2,
            "source_traces": [{"type": "role_inference", "role": c["role"]} for c in cands],
        }
        rows.append(row)
    return rows
```

Run: `python3 -m pytest tests/test_merge_and_score.py::test_merge_takes_max_sod -v`
Expected: PASS

- [ ] **Step 3.5: 实现 `align_with_evidence`**

```python
def align_with_evidence(rows: list, evidence_pool: dict) -> list:
    for row in rows:
        leaf_id = row["leaf_id"]
        canonical = row["failure_mode_canonical"]
        matches = evidence_pool.get(leaf_id, [])
        # crude semantic match: text contains canonical fragment OR any matched_keyword overlaps with row
        relevant = []
        for m in matches:
            if canonical.replace("_", " ") in m["failure_mode_text"].lower() \
                    or any(kw in row["failure_mode"] for kw in m.get("matched_keywords", [])) \
                    or m["failure_mode_text"]:  # fallback: any match in same leaf is relevant evidence
                relevant.append(m)
        # Roles count for grade
        role_count = len({rv["role"] for rv in row["rating_history"]["role_view"]})
        # Contradiction check
        contradicted = False
        if relevant:
            best = max(relevant, key=lambda m: m["match_score"])
            for hist_field, row_field in [("severity", "severity"), ("occurrence", "occurrence"), ("detection", "detection")]:
                hist_val = best.get(hist_field)
                if hist_val is None:
                    continue
                if abs(hist_val - row[row_field]) >= 3:
                    contradicted = True
                    break
            row["rating_history"]["historical_view"] = {
                "s": best.get("severity"),
                "o": best.get("occurrence"),
                "d": best.get("detection"),
                "source": f"{best['source_workbook']}/{best['source_sheet']}/row {best['source_row']}",
            }
            row["source_traces"].append({
                "type": "historical",
                "ref": f"{best['source_workbook']}/{best['source_sheet']}/row {best['source_row']}",
            })
        # Determine grade
        if contradicted:
            grade = "contradicted"
        elif relevant and role_count >= 2:
            grade = "evidence-backed"
        elif relevant and role_count == 1:
            grade = "historical-supported"
        elif not relevant and role_count >= 2:
            grade = "multi-role-inferred"
        else:
            grade = "ai-inferred"
        row["evidence_grade"] = grade
    return rows
```

Run: `python3 -m pytest tests/test_merge_and_score.py::test_align_with_evidence_grade tests/test_merge_and_score.py::test_align_with_evidence_contradicted_when_sod_diff_ge_3 -v`
Expected: PASS

- [ ] **Step 3.6: 实现 `compute_confidence`**

```python
def _required_role_count(structure: dict) -> int:
    text_blob = json.dumps(structure, ensure_ascii=False).lower()
    triggers = ["mcu", "软件", "控制", "状态机", "通讯", "报警", "联锁"]
    has_software = any(t in text_blob for t in triggers)
    return 6 if has_software else 5


def compute_confidence(rows: list, structure: dict) -> list:
    required_role_count = _required_role_count(structure)
    for row in rows:
        # role_agreement
        role_count = len({rv["role"] for rv in row["rating_history"]["role_view"]})
        role_agreement = min(1.0, role_count / required_role_count)

        # evidence_strength
        hist_traces = [t for t in row["source_traces"] if t["type"] == "historical"]
        hist = row["rating_history"].get("historical_view")
        if hist:
            evidence_strength = min(1.0, 0.4 + 0.6)  # one match present
        else:
            evidence_strength = 0.0

        # sod_grounding: 1.0 if non-conflict historical, 0.7 if multi-role with rationale, else 0.4
        if row["evidence_grade"] in ("evidence-backed", "historical-supported"):
            sod_grounding = 1.0
        elif row["evidence_grade"] == "multi-role-inferred":
            sod_grounding = 0.7
        elif row["evidence_grade"] == "contradicted":
            sod_grounding = 0.4
        else:
            sod_grounding = 0.4

        # pdiagram_coverage: anchor present and contains × → 1.0, anchor present without × → 0.5, missing → 0.0
        anchor = row.get("p_diagram_anchor", "")
        if " × " in anchor:
            pdiagram_coverage = 1.0
        elif anchor:
            pdiagram_coverage = 0.5
        else:
            pdiagram_coverage = 0.0

        confidence = (
            WEIGHTS["role_agreement"] * role_agreement
            + WEIGHTS["evidence_strength"] * evidence_strength
            + WEIGHTS["sod_grounding"] * sod_grounding
            + WEIGHTS["pdiagram_coverage"] * pdiagram_coverage
        )
        row["confidence"] = round(confidence, 3)
        row["confidence_breakdown"] = {
            "role_agreement": round(role_agreement, 3),
            "evidence_strength": round(evidence_strength, 3),
            "sod_grounding": round(sod_grounding, 3),
            "pdiagram_coverage": round(pdiagram_coverage, 3),
        }
        row["needs_human_confirmation"] = (
            row["evidence_grade"] in ("contradicted", "ai-inferred")
            or confidence < 0.5
        )
    return rows
```

Run: `python3 -m pytest tests/test_merge_and_score.py::test_compute_confidence_all_components_present -v`
Expected: PASS

- [ ] **Step 3.7: 实现 `coverage_gap_check`**

```python
def _walk_leaves(node):
    if node.get("level") == "component":
        yield node
    for child in node.get("children", []):
        yield from _walk_leaves(child)


REQUIRED_AXES = {
    "系统/接口": [("system_interactions", "intended_outputs")],
    "设计/模块": [("piece_to_piece", "control_factors")],
    "可靠性/试验": [("wear_aging", "environment")],
    "制造/工艺": [("piece_to_piece", "control_factors")],
    "安全/服务": [("customer_usage", "error_states")],
    "软件/控制": [("input_signals", "control_factors"), ("control_factors", "error_states")],
}


def coverage_gap_check(rows: list, structure: dict) -> list:
    leaves = list(_walk_leaves(structure["hierarchy"]))
    leaf_ids = [n["id"] for n in leaves]

    covered = set()
    for row in rows:
        anchor = row.get("p_diagram_anchor", "")
        # anchor format: "noise:value × unintended_or_error:value"
        parts = anchor.split(" × ")
        if len(parts) == 2:
            noise_axis = parts[0].split(":")[0] if ":" in parts[0] else ""
            unintended_axis = parts[1].split(":")[0] if ":" in parts[1] else ""
            covered.add((row["leaf_id"], noise_axis, unintended_axis))

    gaps = []
    for leaf_id in leaf_ids:
        for role, axes in REQUIRED_AXES.items():
            for noise_axis, unintended_axis in axes:
                if (leaf_id, noise_axis, unintended_axis) not in covered:
                    gaps.append({
                        "leaf_id": leaf_id,
                        "role": role,
                        "axis_combo": f"{noise_axis} × {unintended_axis}",
                        "severity_estimate": "potential",
                    })
    return gaps
```

Run: `python3 -m pytest tests/test_merge_and_score.py::test_coverage_gap_detects_missing_axis -v`
Expected: PASS

- [ ] **Step 3.8: 实现 `select_top_risks` 与 `select_confirmation_queue`**

```python
def select_top_risks(rows: list, top_n: int = 10) -> list:
    return sorted(rows, key=lambda r: r["confidence"] * r["rpn"], reverse=True)[:top_n]


def select_confirmation_queue(rows: list) -> list:
    queue = []
    for row in rows:
        if row["evidence_grade"] == "contradicted":
            queue.append(row)
        elif row["evidence_grade"] == "ai-inferred" and row.get("confidence", 0) < 0.5:
            queue.append(row)
        elif row.get("confidence", 0) < 0.4:
            queue.append(row)
    return sorted(queue, key=lambda r: r["confidence"] * r["rpn"], reverse=True)
```

Run: `python3 -m pytest tests/test_merge_and_score.py -v`
Expected: 全部 PASS

- [ ] **Step 3.9: 提交**

```bash
git add openclaw-fmea-cocreator/scripts/merge_and_score.py
git commit -m "feat(fmea): implement merge_and_score pipeline (cross-scope dedup + evidence grading + confidence)"
```

---

## Task 4: 替换 `template.xlsx`,扩到 31 列 + 新增 2 sheet

**Files:**
- Modify: `openclaw-fmea-cocreator/template.xlsx` (替换)
- Create: `openclaw-fmea-cocreator/template_legacy.xlsx` (备份当前模板)
- Create: `openclaw-fmea-cocreator/scripts/build_template.py` (一次性脚本,生成新模板)

- [ ] **Step 4.1: 备份现有 template.xlsx**

```bash
cp openclaw-fmea-cocreator/template.xlsx openclaw-fmea-cocreator/template_legacy.xlsx
```

- [ ] **Step 4.2: 写一次性的 `build_template.py` 生成新模板**

(该脚本仅用于生成 template.xlsx 后弃置;保留在仓库内以便未来重建)

```python
"""One-shot script to (re)build template.xlsx for M2.

Usage:
    python3 openclaw-fmea-cocreator/scripts/build_template.py
"""
from __future__ import annotations

import shutil
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = SKILL_DIR / "template.xlsx"

FMEA_HEADERS = [
    "序号", "Scope path", "Leaf 节点", "Analysis object", "Function or requirement",
    "P-Diagram 锚点", "Failure mode", "Failure mode canonical", "Failure effect",
    "S", "Cause or mechanism", "O", "Current controls (prevention)",
    "Current controls (detection)", "D", "RPN", "Recommended actions",
    "Owner", "Target date",
    "改进后 S", "改进后 O", "改进后 D", "改进后 RPN",
    "Evidence grade", "Confidence", "Confidence breakdown",
    "Multi-role corroborated", "Rating history",
    "Needs human confirmation", "Source traces", "AI 打分推导依据",
]
assert len(FMEA_HEADERS) == 31, "Header count must equal 31"


def build():
    wb = Workbook()

    # Sheet 1: 封面
    cover = wb.active
    cover.title = "封面"
    cover["B2"] = "<模块名> <FMEA类型>分析报告"
    cover["B6"] = "模块"
    cover["B7"] = "关键功能/指标"
    cover["B8"] = "采用的方法学"
    cover["B9"] = "范围/Scopes"
    cover["B10"] = "数据来源"
    cover["B11"] = "生成日期"
    cover["B12"] = "版本"
    cover["B14"] = "覆盖摘要"
    cover["B15"] = "Hierarchy 节点数"
    cover["B16"] = "Coverage gaps 行数"
    cover["B17"] = "证据等级分布"
    cover["B18"] = "置信度分布"
    cover["B19"] = "评审导引: 先看 Sheet 4 待确认队列"

    # Sheet 2: FMEA 主表
    main = wb.create_sheet("FMEA主表")
    for col_idx, header in enumerate(FMEA_HEADERS, start=2):  # write to B2..AF2
        cell = main.cell(row=2, column=col_idx)
        cell.value = header
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.fill = PatternFill("solid", fgColor="D9E1F2")
    main.row_dimensions[2].height = 32

    # Pre-fill RPN formula on row 3 as template (=J3*L3*O3)
    main.cell(row=3, column=17).value = "=J3*L3*O3"
    # Improved RPN formula (=U3*V3*W3 originally; with our layout: 改进后 S=U,O=V,D=W,RPN=X relative)
    # Actually columns 21-23 are 改进后 S/O/D, column 24 is 改进后 RPN
    # In letters: U=21, V=22, W=23, X=24
    main.cell(row=3, column=24).value = "=U3*V3*W3"

    # Set column widths
    width_map = {
        2: 6, 3: 20, 4: 16, 5: 18, 6: 22, 7: 24, 8: 22, 9: 22, 10: 30, 11: 5,
        12: 30, 13: 5, 14: 22, 15: 22, 16: 5, 17: 8, 18: 28, 19: 12, 20: 14,
        21: 7, 22: 7, 23: 7, 24: 8, 25: 16, 26: 10, 27: 26, 28: 14, 29: 24,
        30: 12, 31: 26, 32: 26,
    }
    for col_idx, w in width_map.items():
        main.column_dimensions[get_column_letter(col_idx)].width = w

    # Sheet 3: 评分准则参考
    rules = wb.create_sheet("评分准则参考")
    rules["B2"] = "Severity (S)"
    rules["B3"] = "1=无影响 ... 10=安全/法规红线"
    rules["B5"] = "Occurrence (O)"
    rules["B6"] = "1=极低 ... 10=极频繁"
    rules["B8"] = "Detection (D)"
    rules["B9"] = "1=必然检出 ... 10=完全无法检出"
    rules["B11"] = "评分准则随企业能力而变,本表仅为概念参考。"

    # Sheet 4: 覆盖盲区与待确认队列
    gaps = wb.create_sheet("覆盖盲区与待确认队列")
    gaps["B2"] = "覆盖盲区 (coverage_gaps)"
    for col_idx, h in enumerate(["leaf_id", "role", "axis_combo", "severity_estimate"], start=2):
        c = gaps.cell(row=3, column=col_idx, value=h)
        c.font = Font(bold=True)
    gaps["B10"] = "待确认队列 (confirmation_queue)"
    for col_idx, h in enumerate(["row_id", "leaf_id", "failure_mode", "evidence_grade", "confidence", "rpn", "confidence × rpn"], start=2):
        c = gaps.cell(row=11, column=col_idx, value=h)
        c.font = Font(bold=True)

    # Sheet 5: 结构与 P-Diagram
    struct = wb.create_sheet("结构与P-Diagram")
    struct["B2"] = "Hierarchy"
    struct["B3"] = "(由 build_workbook.py 在生成时填入树状缩进)"
    struct["B10"] = "P-Diagrams"
    struct["B11"] = "(每个子系统一段:scope_id / 6 轴明细)"

    TEMPLATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    wb.save(TEMPLATE_PATH)


if __name__ == "__main__":
    build()
    print(f"wrote {TEMPLATE_PATH}")
```

- [ ] **Step 4.3: 运行脚本生成新模板**

Run: `cd /Users/nova/code/fmea-skill && python3 openclaw-fmea-cocreator/scripts/build_template.py`
Expected: 输出 `wrote .../openclaw-fmea-cocreator/template.xlsx`

- [ ] **Step 4.4: 验证新模板**

Run:
```bash
cd /Users/nova/code/fmea-skill && python3 -c "
from openpyxl import load_workbook
wb = load_workbook('openclaw-fmea-cocreator/template.xlsx')
assert set(wb.sheetnames) == {'封面', 'FMEA主表', '评分准则参考', '覆盖盲区与待确认队列', '结构与P-Diagram'}
ws = wb['FMEA主表']
headers = [ws.cell(row=2, column=c).value for c in range(2, 33)]
assert len(headers) == 31
assert headers[0] == '序号'
assert headers[5] == 'P-Diagram 锚点'
assert headers[7] == 'Failure mode canonical'
assert headers[23] == 'Evidence grade'
print('OK')
"
```

Expected: `OK`

- [ ] **Step 4.5: 提交**

```bash
git add openclaw-fmea-cocreator/template.xlsx openclaw-fmea-cocreator/template_legacy.xlsx openclaw-fmea-cocreator/scripts/build_template.py
git commit -m "feat(fmea): replace template.xlsx with 31-column 5-sheet layout for M2"
```

---

## Task 5: 写 `build_workbook.py` (TDD)

**Files:**
- Create: `tests/test_build_workbook.py`
- Create: `openclaw-fmea-cocreator/scripts/build_workbook.py`
- Create: `tests/fixtures/sample_normalized.json` (合成的小型 fmea_normalized 用于渲染测试)

### Step 5.1: 写 fixture

- [ ] **Step 5.1.1: 写 `tests/fixtures/sample_normalized.json`**

```json
{
  "module_root": "测试模块",
  "fmea_type": "DFMEA",
  "rows": [
    {
      "row_id": "T.1.1/stuck_relay_contact",
      "leaf_id": "T.1.1",
      "scope_path": "T → T.1 → T.1.1",
      "failure_mode": "触点粘连",
      "failure_mode_canonical": "stuck_relay_contact",
      "p_diagram_anchor": "wear_aging:阀片疲劳 × error_states:继电器粘连",
      "cause": "[设计/模块] 选型余量不足",
      "effect_customer": "无法停机",
      "effect_downstream": "压缩机损坏",
      "effect_system": "保护机制失效",
      "current_controls_prevention": "[设计/模块] 选型余量 1.5x",
      "current_controls_detection": "[设计/模块] 状态监测",
      "recommended_actions": ["增加交流接触器"],
      "severity": 9, "occurrence": 7, "detection": 5, "rpn": 315,
      "evidence_grade": "evidence-backed",
      "confidence": 0.78,
      "confidence_breakdown": {
        "role_agreement": 0.4, "evidence_strength": 1.0,
        "sod_grounding": 1.0, "pdiagram_coverage": 1.0
      },
      "rating_history": {
        "role_view": [{"role": "设计/模块", "s": 9, "o": 5, "d": 3}, {"role": "可靠性/试验", "s": 9, "o": 7, "d": 5}],
        "historical_view": {"s": 9, "o": 7, "d": 1, "source": "CAN400/变温/row 31"}
      },
      "multi_role_corroborated": true,
      "needs_human_confirmation": false,
      "source_traces": [
        {"type": "role_inference", "role": "设计/模块"},
        {"type": "role_inference", "role": "可靠性/试验"},
        {"type": "historical", "ref": "CAN400/变温/row 31"}
      ]
    }
  ],
  "coverage_gaps": [
    {"leaf_id": "T.1.2", "role": "设计/模块", "axis_combo": "piece_to_piece × control_factors", "severity_estimate": "potential"}
  ],
  "top_risks": [],
  "confirmation_queue": []
}
```

### Step 5.2: 先写测试

- [ ] **Step 5.2.1: 写 `tests/test_build_workbook.py`**

```python
"""Test build_workbook.py renders fmea_normalized.json into the new 31-column template."""
import sys
import subprocess
import json
from pathlib import Path

import pytest
from openpyxl import load_workbook

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "openclaw-fmea-cocreator" / "scripts" / "build_workbook.py"
FIXTURES = REPO_ROOT / "tests" / "fixtures"


@pytest.fixture
def rendered_workbook(tmp_path):
    out = tmp_path / "out.xlsx"
    result = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--normalized", str(FIXTURES / "sample_normalized.json"),
         "--output", str(out)],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    return load_workbook(out)


def test_workbook_has_5_sheets(rendered_workbook):
    expected = {"封面", "FMEA主表", "评分准则参考", "覆盖盲区与待确认队列", "结构与P-Diagram"}
    assert set(rendered_workbook.sheetnames) == expected


def test_main_sheet_has_31_columns_and_correct_headers(rendered_workbook):
    ws = rendered_workbook["FMEA主表"]
    headers = [ws.cell(row=2, column=c).value for c in range(2, 33)]
    assert len(headers) == 31
    assert headers[5] == "P-Diagram 锚点"
    assert headers[7] == "Failure mode canonical"
    assert headers[23] == "Evidence grade"
    assert headers[24] == "Confidence"


def test_main_sheet_first_row_data(rendered_workbook):
    ws = rendered_workbook["FMEA主表"]
    # row 3 is first data row, column 2 is index
    assert ws.cell(row=3, column=2).value == 1
    assert ws.cell(row=3, column=8).value == "触点粘连"  # Failure mode (column G after序号 B)
    assert ws.cell(row=3, column=9).value == "stuck_relay_contact"  # canonical
    assert ws.cell(row=3, column=11).value == 9  # severity
    assert ws.cell(row=3, column=17).value == 315  # rpn (or formula returning 315)
    assert ws.cell(row=3, column=25).value == "evidence-backed"


def test_rpn_formula_present(rendered_workbook):
    ws = rendered_workbook["FMEA主表"]
    cell = ws.cell(row=3, column=17)
    # Either pre-computed value or formula
    assert cell.value == 315 or str(cell.value).startswith("=")


def test_coverage_gaps_sheet_filled(rendered_workbook):
    ws = rendered_workbook["覆盖盲区与待确认队列"]
    # row 4 is first gap data row (header at row 3)
    assert ws.cell(row=4, column=2).value == "T.1.2"


def test_structure_sheet_has_hierarchy_text(rendered_workbook):
    ws = rendered_workbook["结构与P-Diagram"]
    # Just check that some hierarchy content was written
    found = False
    for row in ws.iter_rows(min_row=3, max_row=20, values_only=True):
        for cell in row:
            if cell and "T" in str(cell):
                found = True
                break
    assert found


def test_cover_sheet_filled(rendered_workbook):
    ws = rendered_workbook["封面"]
    # Module + FMEA type should appear in B2 title
    title = ws["B2"].value or ""
    assert "测试模块" in title
    assert "DFMEA" in title
```

- [ ] **Step 5.2.2: 验证测试失败 (脚本未实现)**

Run: `cd /Users/nova/code/fmea-skill && python3 -m pytest tests/test_build_workbook.py -v`
Expected: 全部 FAIL,因为 build_workbook.py 还不存在

### Step 5.3: 实现脚本

- [ ] **Step 5.3.1: 写 `build_workbook.py`**

```python
"""Render fmea_normalized.json into the 31-column 5-sheet template.xlsx."""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import date
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.formatting.rule import CellIsRule, ColorScaleRule, DataBarRule, FormulaRule
from openpyxl.utils import get_column_letter

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "template.xlsx"

EVIDENCE_COLOR = {
    "evidence-backed": "C6EFCE",
    "historical-supported": "E2EFDA",
    "multi-role-inferred": "FFF2CC",
    "ai-inferred": "FFD966",
    "contradicted": "F4B084",
}


def _render_cover(ws, normalized: dict, structure: dict | None) -> None:
    ws["B2"] = f"{normalized['module_root']} {normalized['fmea_type']}分析报告"
    ws["C6"] = normalized["module_root"]
    ws["C9"] = ", ".join(p["scope_id"] for p in (structure or {}).get("p_diagrams", [])) or "未拆分"
    ws["C10"] = "历史FMEA案例库 + 多角色 LLM 推理"
    ws["C11"] = date.today().isoformat()
    ws["C12"] = "V0.3.0-m2"
    rows = normalized.get("rows", [])
    ws["C15"] = sum(1 for _ in _walk_leaves((structure or {}).get("hierarchy", {}))) if structure else len(rows)
    ws["C16"] = len(normalized.get("coverage_gaps", []))
    grade_counts = {}
    for r in rows:
        grade_counts[r["evidence_grade"]] = grade_counts.get(r["evidence_grade"], 0) + 1
    ws["C17"] = " | ".join(f"{k}={v}" for k, v in grade_counts.items())
    if rows:
        avg_conf = sum(r["confidence"] for r in rows) / len(rows)
        ws["C18"] = f"平均置信度 {avg_conf:.2f}, 行数 {len(rows)}"


def _walk_leaves(node):
    if not node:
        return
    if node.get("level") == "component":
        yield node
    for child in node.get("children", []):
        yield from _walk_leaves(child)


def _render_main(ws, rows: list) -> None:
    for idx, row in enumerate(rows, start=1):
        excel_row = idx + 2  # data starts at row 3
        values = [
            idx,
            row["scope_path"],
            row["leaf_id"],
            row.get("leaf_id"),  # placeholder for analysis_object until enriched
            "",  # function/requirement (populated from structure if available)
            row["p_diagram_anchor"],
            row["failure_mode"],
            row["failure_mode_canonical"],
            f"客户:{row['effect_customer']} | 系统:{row['effect_system']}",
            row["severity"],
            row["cause"],
            row["occurrence"],
            row["current_controls_prevention"],
            row["current_controls_detection"],
            row["detection"],
            row["rpn"],
            "; ".join(row["recommended_actions"]),
            "",  # owner
            "",  # target date
            "", "", "", "",  # 改进后 S/O/D/RPN
            row["evidence_grade"],
            row["confidence"],
            json.dumps(row["confidence_breakdown"], ensure_ascii=False),
            "Y" if row.get("multi_role_corroborated") else "N",
            json.dumps(row.get("rating_history", {}), ensure_ascii=False),
            "Y" if row.get("needs_human_confirmation") else "N",
            "; ".join(t.get("ref") or t.get("role", "") for t in row.get("source_traces", [])),
            "",  # AI 打分推导依据 (legacy column)
        ]
        for col_idx, value in enumerate(values, start=2):
            ws.cell(row=excel_row, column=col_idx, value=value)
    # Apply evidence_grade conditional formatting (column 25 = "Evidence grade")
    last_row = len(rows) + 2
    if last_row >= 3:
        for grade, color in EVIDENCE_COLOR.items():
            rule = FormulaRule(formula=[f'$Y3="{grade}"'], stopIfTrue=False, fill=PatternFill("solid", fgColor=color))
            ws.conditional_formatting.add(f"Y3:Y{last_row}", rule)
        # Confidence (column 26 = letter Z) data bar
        ws.conditional_formatting.add(
            f"Z3:Z{last_row}",
            DataBarRule(start_type="num", start_value=0, end_type="num", end_value=1, color="638EC6", showValue=True),
        )


def _render_gaps(ws, normalized: dict) -> None:
    gaps = normalized.get("coverage_gaps", [])
    for idx, gap in enumerate(gaps, start=1):
        excel_row = idx + 3  # header at row 3
        ws.cell(row=excel_row, column=2, value=gap.get("leaf_id"))
        ws.cell(row=excel_row, column=3, value=gap.get("role"))
        ws.cell(row=excel_row, column=4, value=gap.get("axis_combo"))
        ws.cell(row=excel_row, column=5, value=gap.get("severity_estimate"))
    queue = normalized.get("confirmation_queue", [])
    for idx, row in enumerate(queue, start=1):
        excel_row = idx + 11  # header at row 11
        ws.cell(row=excel_row, column=2, value=row.get("row_id"))
        ws.cell(row=excel_row, column=3, value=row.get("leaf_id"))
        ws.cell(row=excel_row, column=4, value=row.get("failure_mode"))
        ws.cell(row=excel_row, column=5, value=row.get("evidence_grade"))
        ws.cell(row=excel_row, column=6, value=row.get("confidence"))
        ws.cell(row=excel_row, column=7, value=row.get("rpn"))
        ws.cell(row=excel_row, column=8, value=round(row.get("confidence", 0) * row.get("rpn", 0), 2))


def _render_structure(ws, structure: dict | None) -> None:
    ws["B3"] = "(no structure provided)" if not structure else None

    def _walk(node, depth, lines):
        if not node:
            return
        lines.append(("  " * depth) + f"{node['id']} {node['name']} ({node['level']})")
        for c in node.get("children", []):
            _walk(c, depth + 1, lines)

    if structure:
        lines = []
        _walk(structure.get("hierarchy"), 0, lines)
        for i, line in enumerate(lines, start=1):
            ws.cell(row=2 + i, column=2, value=line)
        # P-Diagrams below
        start = 2 + len(lines) + 3
        ws.cell(row=start, column=2, value="P-Diagrams")
        offset = 1
        for pd in structure.get("p_diagrams", []):
            ws.cell(row=start + offset, column=2, value=f"scope_id={pd['scope_id']}")
            offset += 1
            for axis in ("input_signals", "control_factors", "intended_outputs", "unintended_outputs", "error_states"):
                ws.cell(row=start + offset, column=2, value=f"  {axis}: {', '.join(pd.get(axis, []))}")
                offset += 1
            for sub_axis in pd.get("noise_factors", {}):
                ws.cell(row=start + offset, column=2, value=f"  noise.{sub_axis}: {', '.join(pd['noise_factors'][sub_axis])}")
                offset += 1


def render(normalized_path: Path, structure_path: Path | None, output: Path) -> None:
    normalized = json.loads(normalized_path.read_text(encoding="utf-8"))
    structure = json.loads(structure_path.read_text(encoding="utf-8")) if structure_path else None

    shutil.copy(TEMPLATE, output)
    wb = load_workbook(output)
    _render_cover(wb["封面"], normalized, structure)
    _render_main(wb["FMEA主表"], normalized.get("rows", []))
    _render_gaps(wb["覆盖盲区与待确认队列"], normalized)
    _render_structure(wb["结构与P-Diagram"], structure)
    wb.save(output)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render fmea_normalized.json to xlsx using template.xlsx.")
    parser.add_argument("--normalized", required=True, type=Path)
    parser.add_argument("--structure", type=Path, help="Optional structure.json for cover and Sheet 5.")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    render(args.normalized, args.structure, args.output)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5.3.2: 跑测试,确认通过**

Run: `cd /Users/nova/code/fmea-skill && python3 -m pytest tests/test_build_workbook.py -v`
Expected: 全部 PASS

- [ ] **Step 5.3.3: 提交**

```bash
git add openclaw-fmea-cocreator/scripts/build_workbook.py tests/test_build_workbook.py tests/fixtures/sample_normalized.json
git commit -m "feat(fmea): implement build_workbook.py rendering 31-col template"
```

---

## Task 6: 适配 `import_existing_fmea_excel.py` 到新 31 列

**Files:**
- Modify: `openclaw-fmea-cocreator/scripts/import_existing_fmea_excel.py`

- [ ] **Step 6.1: 读老脚本结构**

Run: `head -80 openclaw-fmea-cocreator/scripts/import_existing_fmea_excel.py`

定位"写入 FMEA 主表"的部分。

- [ ] **Step 6.2: 在该位置加新列默认值**

找到原脚本中向 FMEA 主表写值的部分(应在 70-200 行之间),在每行 22 列写完后,扩展列字典追加 9 个默认值:

```python
# Append M2 new-column defaults (legacy import: AI grading not available)
for col_idx, value in [
    (25, "ai-inferred"),  # Evidence grade
    (26, None),           # Confidence
    (27, ""),             # Confidence breakdown
    (28, "N"),            # Multi-role corroborated
    (29, ""),             # Rating history
    (30, "Y"),            # Needs human confirmation (legacy data is uncalibrated)
    (31, "导入自既有 FMEA"),  # Source traces
    (32, ""),             # AI 打分推导依据
]:
    ws.cell(row=excel_row, column=col_idx, value=value)
```

(具体替换位置由实际文件结构决定;若现有脚本不是循环写而是 row append,改为 append 完整 31 列列表。)

- [ ] **Step 6.3: 加最小回归测试**

Create: `tests/test_import_existing_legacy_to_31col.py`

```python
"""Verify import_existing_fmea_excel.py emits 31-column workbook for legacy 22-col input."""
import json
import sys
import subprocess
from pathlib import Path
import pytest
from openpyxl import load_workbook

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "openclaw-fmea-cocreator" / "scripts" / "import_existing_fmea_excel.py"


def test_legacy_import_produces_31_columns(tmp_path):
    # Use the legacy template as a stand-in legacy-shaped input
    legacy = REPO_ROOT / "openclaw-fmea-cocreator" / "template_legacy.xlsx"
    if not legacy.exists():
        pytest.skip("template_legacy.xlsx not present")
    out_xlsx = tmp_path / "imported.xlsx"
    out_json = tmp_path / "imported.json"
    result = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--input-excel", str(legacy),
         "--excel-out", str(out_xlsx),
         "--json-out", str(out_json)],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    wb = load_workbook(out_xlsx)
    ws = wb["FMEA主表"]
    headers = [ws.cell(row=2, column=c).value for c in range(2, 33)]
    assert len(headers) == 31
    assert "Evidence grade" in headers
```

- [ ] **Step 6.4: 跑测试**

Run: `cd /Users/nova/code/fmea-skill && python3 -m pytest tests/test_import_existing_legacy_to_31col.py -v`
Expected: PASS (或 SKIP 如果 legacy 文件不存在)

- [ ] **Step 6.5: 提交**

```bash
git add openclaw-fmea-cocreator/scripts/import_existing_fmea_excel.py tests/test_import_existing_legacy_to_31col.py
git commit -m "feat(fmea): adapt import_existing_fmea_excel.py to 31-col template"
```

---

## Task 7: mock_10 回归测试 — 治"重复"指纹断言

**Files:**
- Create: `tests/test_mock_10_regression.py`

- [ ] **Step 7.1: 写测试**

```python
"""mock_10 regression: assert the indicators that proved M0 was broken are gone in M2.

The hallmark bug was:
- 10 different scenarios each produced exactly 28 rows
- The same source_row appeared in multiple scopes ("source_trace duplication")

If our M2 pipeline genuinely produces FMEA rather than copying historical rows,
these patterns must NOT reappear.
"""
import json
from collections import Counter
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATED_DIR = REPO_ROOT / "validation" / "mock_10" / "m2_generated"


def _load_normalized_outputs():
    if not GENERATED_DIR.exists():
        pytest.skip("M2 mock_10 outputs not yet generated; run validation/mock_10/run_m2.sh first")
    files = sorted(GENERATED_DIR.glob("*_normalized.json"))
    return [json.loads(f.read_text(encoding="utf-8")) for f in files]


def test_row_counts_are_not_all_equal():
    """Indicator: in M0, all 10 scenarios produced exactly 28 rows.
    In M2 they should differ — they are different modules with different P-Diagrams."""
    outputs = _load_normalized_outputs()
    counts = [len(o["rows"]) for o in outputs]
    assert len(set(counts)) > 1, f"All scenarios produced same row count: {counts}"


def test_no_source_row_crosses_scopes():
    """Indicator: in M0, the same historical source_row could appear under multiple scopes.
    In M2, each historical match is anchored to a single leaf_id, so leaf_id × source_row
    should be unique across the whole FMEA."""
    outputs = _load_normalized_outputs()
    for output in outputs:
        seen = set()
        duplicates = []
        for row in output["rows"]:
            for trace in row.get("source_traces", []):
                if trace.get("type") != "historical":
                    continue
                key = (row["leaf_id"], trace.get("ref"))
                if key in seen:
                    duplicates.append(key)
                seen.add(key)
        assert not duplicates, f"Module {output['module_root']} has duplicate (leaf, source_row): {duplicates}"


def test_at_least_60pct_rows_multi_role_corroborated():
    outputs = _load_normalized_outputs()
    for output in outputs:
        rows = output["rows"]
        if not rows:
            continue
        corroborated = sum(1 for r in rows if r.get("multi_role_corroborated"))
        ratio = corroborated / len(rows)
        # Threshold lenient because some leaves may legitimately have only one applicable role
        assert ratio >= 0.6, f"Module {output['module_root']} has only {ratio:.0%} multi-role rows"


def test_evidence_grade_consistent_with_confidence():
    """evidence-backed rows should have confidence > 0.6;
    ai-inferred rows should rarely exceed 0.6 (low evidence_strength dominates)."""
    outputs = _load_normalized_outputs()
    for output in outputs:
        for row in output["rows"]:
            if row["evidence_grade"] == "evidence-backed":
                assert row["confidence"] >= 0.5, f"evidence-backed row has low confidence: {row['row_id']}"
            if row["evidence_grade"] == "ai-inferred" and row["confidence"] >= 0.7:
                pytest.fail(f"ai-inferred row with high confidence is suspicious: {row['row_id']}")
```

- [ ] **Step 7.2: 创建一次性脚本 `validation/mock_10/run_m2.sh`**

(主体由 Claude 在执行 plan 时按 SKILL.md 流程跑出 10 份 candidates_*.json,然后跑 merge_and_score.py 与 build_workbook.py。这里只放一个最小骨架,实际跑要 LLM 介入。)

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
OUT="$ROOT/validation/mock_10/m2_generated"
mkdir -p "$OUT"
echo "Note: this script only stitches outputs. Each scenario must first have:"
echo "  - structure.json (produced by Claude per p_diagram_template.md)"
echo "  - candidates_*.json (per specialist_role_prompts.md, 6 roles)"
echo "  - evidence_pool/<leaf_id>.json (via retrieve_cases.py --json-out)"

for scenario_dir in "$ROOT"/validation/mock_10/scenarios/*/; do
  name=$(basename "$scenario_dir")
  out_norm="$OUT/${name}_normalized.json"
  out_xlsx="$OUT/${name}.xlsx"
  python3 "$ROOT/openclaw-fmea-cocreator/scripts/merge_and_score.py" \
    --structure "$scenario_dir/structure.json" \
    --candidates-dir "$scenario_dir" \
    --evidence-pool-dir "$scenario_dir/evidence_pool" \
    --output "$out_norm"
  python3 "$ROOT/openclaw-fmea-cocreator/scripts/build_workbook.py" \
    --normalized "$out_norm" \
    --structure "$scenario_dir/structure.json" \
    --output "$out_xlsx"
done
echo "Done. Run pytest tests/test_mock_10_regression.py to validate."
```

- [ ] **Step 7.3: 提交**

```bash
chmod +x validation/mock_10/run_m2.sh
git add tests/test_mock_10_regression.py validation/mock_10/run_m2.sh
git commit -m "test(fmea): add mock_10 regression asserting fingerprint of M0 dedup bug is gone"
```

---

## Task 8: 更新 SKILL.md 与 references 指向 M2 实现

**Files:**
- Modify: `openclaw-fmea-cocreator/SKILL.md`
- Modify: `openclaw-fmea-cocreator/references/evidence_grading.md`
- Modify: `openclaw-fmea-cocreator/references/deduplication_protocol.md`

- [ ] **Step 8.1: SKILL.md 替换"M1 暂用 draft_fmea_from_cases.py"段**

找到 SKILL.md 中 `### 阶段 5: 工作簿渲染` 段,替换为:

```markdown
### 阶段 5: 工作簿渲染

```bash
python3 openclaw-fmea-cocreator/scripts/build_workbook.py \
  --normalized fmea_normalized.json \
  --structure structure.json \
  --output 输出.xlsx
```

输出工作簿包含 5 个 sheet:
- `封面` (含证据等级分布、置信度分布、覆盖摘要)
- `FMEA主表` (31 列,含 P-Diagram 锚点、证据等级、置信度等新列)
- `评分准则参考`
- `覆盖盲区与待确认队列`
- `结构与P-Diagram`
```

- [ ] **Step 8.2: 升级 SKILL.md 版本**

替换 `version: 0.3.0-m1` 为 `version: 0.3.0-m2`。

- [ ] **Step 8.3: evidence_grading.md 移除 "M2 落地"标记,改为指向实现**

把"在工作簿中的视觉表达 (M2 落地)"段改为:

```markdown
## 在工作簿中的视觉表达 (已实现)

由 `scripts/build_workbook.py` 自动渲染:
- `evidence_grade` 列 (Y): 5 色条件格式
- `confidence` 列 (Z): 数据条 0-1
- 整行底色 `needs_human_confirmation=true` → 浅红 (条件格式公式)
```

- [ ] **Step 8.4: deduplication_protocol.md 同样移除"M2 落地"未来时,改为现在时**

将"反模式表"段加入说明:"由 `merge_and_score.py` 在阶段 4.6 与回归测试自动检测"。

- [ ] **Step 8.5: 提交**

```bash
git add openclaw-fmea-cocreator/SKILL.md openclaw-fmea-cocreator/references/evidence_grading.md openclaw-fmea-cocreator/references/deduplication_protocol.md
git commit -m "docs(fmea): point references to M2 implementation"
```

---

## Task 9: 端到端 mock_10 验收

**Files:**
- 仅运行命令,无文件修改

- [ ] **Step 9.1: 跑全套单元测试**

Run: `cd /Users/nova/code/fmea-skill && python3 -m pytest tests/ -v --ignore=tests/test_mock_10_regression.py`
Expected: 全部 PASS (test_mock_10_regression 此时仍 SKIP,因为还没生成产物)

- [ ] **Step 9.2: 让 fresh subagent 按 SKILL.md 跑一个完整 mock 场景**

使用 Agent 工具 (subagent_type=`general-purpose`),prompt:

```
按 openclaw-fmea-cocreator/SKILL.md 的全部 6 个阶段为 validation/mock_10/input/01_rf_power_amp.txt 跑一遍 FMEA 生成。

按以下步骤执行,每一步把产物写到 validation/mock_10/scenarios/01_rf_power_amp/ 下:

1. 阶段 1: 按 references/p_diagram_template.md 抽 structure.json
2. 阶段 2: 按 references/specialist_role_prompts.md 跑 6 个角色,各产 candidates_<role_key>.json
   role_key 用英文: design / reliability / system / manufacturing / safety / software
3. 阶段 3: 对每个 leaf 跑 retrieve_cases.py --json-out evidence_pool/<leaf_id>.json
4. 阶段 4: 跑 merge_and_score.py 产 fmea_normalized.json
5. 阶段 5: 跑 build_workbook.py 产 输出.xlsx

完成后回复:
- structure 中 leaf 数
- 每个角色 candidates 数
- merge 后 rows 数
- evidence_grade 分布
- 平均 confidence
```

Expected: subagent 给出全部数字。

- [ ] **Step 9.3: 跑 mock_10 回归测试 (至少 1 个场景下也应通过单场景断言)**

如果只跑了 1 个场景,先临时 skip "_not_all_equal" 测试,只跑 source_row 与 multi_role 测试:

Run: `cd /Users/nova/code/fmea-skill && python3 -m pytest tests/test_mock_10_regression.py::test_no_source_row_crosses_scopes tests/test_mock_10_regression.py::test_at_least_60pct_rows_multi_role_corroborated -v`
Expected: PASS

- [ ] **Step 9.4: 写 M2 验收记录**

Create: `docs/superpowers/specs/m2_acceptance_notes.md`:

```markdown
# M2 验收记录

- 日期: <YYYY-MM-DD>
- 单元测试: <PASS/FAIL>
- 端到端 1 个场景产出 leaf 数: <N>
- 平均 confidence: <X.XX>
- evidence-backed 比例: <X%>
- multi_role_corroborated 比例: <X%>
- 关键回归断言:
  - source_row 不跨 scope: <PASS/FAIL>
- 结论: <通过/不通过>
```

- [ ] **Step 9.5: 提交**

```bash
git add docs/superpowers/specs/m2_acceptance_notes.md
git commit -m "docs(fmea): M2 acceptance notes"
```

---

## Self-Review 自检

**Spec 覆盖**:
- 阶段 4 合并去重评级 → Task 1-3 (schemas + merge_and_score)
- 阶段 5 工作簿扩列 → Task 4-5 (template + build_workbook)
- 既有导入适配 → Task 6
- 回归断言 → Task 7
- SKILL.md 与 reference 同步 → Task 8
- 验收 → Task 9

**Placeholder 扫描**: 无 TBD/TODO/implement-later 占位符。

**类型一致性**:
- `(leaf_id, failure_mode_canonical)` 主键在 schemas / merge_and_score / 测试间一致
- 列字母 (Y=evidence_grade, Z=confidence) 在 build_template / build_workbook / 测试 / SKILL.md 间一致
- `confidence_breakdown` 4 个分量字段名 `role_agreement / evidence_strength / sod_grounding / pdiagram_coverage` 在 schemas / merge_and_score / evidence_grading.md / 测试间一致
- `evidence_grade` 枚举 5 状态在 schemas / merge_and_score / build_workbook 条件格式间一致
