# 去重协议

FMEA 重复行的根因是 (a) scope 划分基于关键词、(b) 不同角色产出同义失效。本协议定义两层去重:

1. **跨 scope 去重**: 由层级树主键约束,机械执行
2. **scope 内语义去重**: 由 LLM 仲裁,语义判定

## 主键定义

每个候选行的唯一主键:

```
(leaf_id, failure_mode_canonical)
```

- `leaf_id` 必须在 `structure.json` 的 hierarchy 中存在
- `failure_mode_canonical` 必须是 snake_case 英文短码

## 跨 scope 去重(机械)

输入: 6 份 `candidates_{role}.json` 的所有候选行

规则:
1. 按主键分桶
2. 同主键多角色: 合并入"待合并桶",进入步骤 4.3
3. 不同主键即视为不同行,即使 `failure_mode` 中文文本相似

**禁止**: 同一历史 `source_row` 出现在多个 `leaf_id` 下。如果检索结果命中多个 leaf,只能挂在最匹配的 leaf,其他 leaf 通过 `match_score` 在阶段 4 自动落选。

## scope 内语义去重(LLM 仲裁)

**触发条件**: 同一 `leaf_id` 下 candidate 数量 ≥ 2 (合并前)

**LLM judge prompt**:

```
以下两个失效模式都挂在叶节点 {leaf_name} 下,请判定它们是否是同一种失效:

A: failure_mode = "{A.failure_mode}", canonical = "{A.canonical}"
   cause = "{A.cause}"
   p_diagram_anchor = "{A.anchor}"

B: failure_mode = "{B.failure_mode}", canonical = "{B.canonical}"
   cause = "{B.cause}"
   p_diagram_anchor = "{B.anchor}"

输出严格 JSON:
{
  "decision": "merge" | "keep_separate" | "keep_with_distinguisher",
  "rationale": "...",
  "merged_canonical": "..."  // 仅 decision=merge 时,选 A 或 B 的 canonical 作为合并后主键
}
```

**判定标准**:
- `merge`: 机理相同、效果相同、控制相同 (例如 "冷缩泄漏" vs "低温密封失效")
- `keep_with_distinguisher`: 同一失效模式但不同诱因 (例如焊缝裂纹 vs 螺纹松动都会"泄漏",但根因不同)
- `keep_separate`: 完全不同的失效

## 合并候选行的字段规则

同主键多角色合并时:

| 字段 | 合并规则 |
|---|---|
| `failure_mode` (中文) | 取出现次数最多的;并列时取 `self_confidence` 最高的角色版本 |
| `cause` / `effect.*` / `current_controls.*` | 各角色版本去重后用 ` ; ` 拼接,前缀标 `[角色名]` |
| `recommended_actions` | 去重合并 (按文本相似度 ≥ 0.85 视为同动作) |
| `ai_severity` / `ai_occurrence` / `ai_detection` | **取最大值** |
| `rationale` (各维度) | 全部保留到 `rating_history.role_view` |
| `multi_role_corroborated` | 角色数 ≥ 2 时为 `true` |

## 与历史证据池的对齐(由 evidence_grading.md 接管)

合并完候选行后,再与 `evidence_pool/<leaf_id>.json` 对齐:

- 若历史命中同一 `failure_mode_canonical` → `evidence_grade = evidence-backed` 或 `historical-supported`
- 若历史 S/O/D 与合并后 S/O/D 任一维度差 ≥ 3 → `evidence_grade = contradicted`

详见 [evidence_grading.md](evidence_grading.md)。

## 反模式

以下做法会被阶段 4 检测并报警:

| 反模式 | 检测方式 |
|---|---|
| 同一历史 source_row 出现在 2+ scope | scan source_traces |
| 同一 leaf 下 2 行 canonical 相同 | scan 主键 |
| 同一 leaf 下 2 行 canonical 不同但 LLM 仲裁为 merge | scan 仲裁记录 |
| 整个 FMEA 行数恰好等于历史库行数 | 比较 `len(rows)` 与历史 source_row 集合大小,接近则报警 |
