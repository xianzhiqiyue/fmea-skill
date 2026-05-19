# 证据等级与置信度

每行 FMEA 必须有两个独立可信度维度:

1. **证据等级**(`evidence_grade`): 5 状态枚举,描述证据来源类型
2. **置信度**(`confidence`): 0-1 连续值,描述综合可信度

两者都不能省略,工作簿中各占一列。

## 证据等级 5 状态判定表

| 条件 | `evidence_grade` |
|---|---|
| ≥ 1 历史匹配 + ≥ 2 角色覆盖 | `evidence-backed` |
| ≥ 1 历史匹配 + 仅 1 角色覆盖 | `historical-supported` |
| 0 历史匹配 + ≥ 2 角色覆盖 | `multi-role-inferred` |
| 0 历史匹配 + 仅 1 角色覆盖 | `ai-inferred` |
| 历史 S 或 O 与合并后 S 或 O **任一维度差 ≥ 3** | `contradicted` (覆盖以上 4 个) |

**判定顺序**: 先判 contradicted,再判其他 4 个 (因为冲突需要被特别处理)。

**冲突时如何取值**: S/O/D **优先 LLM 推理结果**(取最大值),历史值落入 `rating_history.historical_view` 保留。

**为什么只看 S 与 O 而不看 D**: Severity 与 Occurrence 是失效模式的本质属性,差 ≥ 3 通常意味着两边对失效机理或发生频率的判断不一致,需要人工裁决。Detection 反映的是控制能力,会随企业检测手段升级而显著漂移(老历史 D=1 不代表新设计也能 D=1),把 D 纳入冲突判定会把"能力进步"误判为"语义矛盾"。Detection 差异保留在 `rating_history.historical_view`,由人工在评审阶段对照。

## 置信度公式

```
confidence = w1 * role_agreement
           + w2 * evidence_strength
           + w3 * sod_grounding
           + w4 * pdiagram_coverage

w1 = 0.30
w2 = 0.30
w3 = 0.25
w4 = 0.15
```

每分量 0-1 归一化。最终输出保留 4 分量明细到 `confidence_breakdown`。

### 4 个分量定义

#### `role_agreement`

```
role_agreement = covered_role_count / applicable_role_count
```

- `covered_role_count`: 给出过该 (leaf, failure_mode_canonical) 的角色数
- `applicable_role_count`: 该 leaf 应该被几个角色覆盖 (软件角色仅当触发条件成立才计入)

#### `evidence_strength`

```
evidence_strength = min(1.0, match_count * 0.4 + max(match_score) * 0.6)
```

- `match_count`: 该 (leaf, canonical) 在 evidence_pool 中的历史命中数
- `max(match_score)`: 命中行中最高的 retrieve_cases 评分 (归一化到 0-1, retrieve_cases 原始 score 除以 30)

#### `sod_grounding`

按 S/O/D 三个维度评分,取均值:

| 评分依据 | 单维度得分 |
|---|---|
| 有企业数据 / 历史命中且未冲突 | 1.0 |
| 角色给出明确机理推导 | 0.7 |
| 角色仅给出经验估算 | 0.4 |
| 无任何依据 (兜底值) | 0.2 |

#### `pdiagram_coverage`

```
pdiagram_coverage = covered_axis_count / required_axis_count
```

- `covered_axis_count`: 该行的 `p_diagram_anchor` 覆盖了多少必扫描轴
- `required_axis_count`: 按角色的必扫描组合,该行至少应覆盖几条轴 (通常 2-3)

## 触发 `confirmation_queue` 的阈值

以下行**自动**进入 `confirmation_queue`:

1. `evidence_grade = contradicted` (优先级最高)
2. `evidence_grade = ai-inferred` 且 `confidence < 0.5`
3. `confidence < 0.4` 无视 grade
4. 该行所在 leaf 有 `coverage_gaps` 未覆盖项 (置信度衰减信号)

`confirmation_queue` 内按 `confidence × rpn` 倒序排,让评审者优先处理"高影响低置信"的行。

## 触发 `needs_human_confirmation = true` 的条件

任一条:
- 在 `confirmation_queue` 中
- 用户在阶段 1 明确说过该 leaf 缺企业数据
- `evidence_grade ∈ {contradicted, ai-inferred}`

## top_risks 排序公式

```
top_risk_score = confidence * rpn
```

不用纯 rpn 排序,避免"高 RPN 但 confidence < 0.3 的纸老虎"压倒"高 confidence 的真问题"。

## 在工作簿中的视觉表达 (M2 落地)

| 列 | 视觉规范 |
|---|---|
| `evidence_grade` | 5 色条件格式 |
| `confidence` | 数据条 0-1 灰阶 |
| `confidence_breakdown` | 4 分量明细文本 |
| 整行底色 | `needs_human_confirmation=true` → 浅红 |

## 权重可调

`w1/w2/w3/w4` 权重可调,但调整必须有原因记录(写在评审记录中)。默认权重的依据:

- 多角色证据 (w1=0.30) 与历史证据 (w2=0.30) 等权,因为本企业历史库目前仅 CAN400 一份,需要 LLM 补足覆盖
- `sod_grounding` (w3=0.25) 高于 `pdiagram_coverage` (w4=0.15) 因为评分质量影响 RPN,而 P-Diagram 覆盖影响"是否漏行"——后者已由 `coverage_gaps.json` 单独表达
