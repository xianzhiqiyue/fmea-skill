# FMEA Skill M1 实现计划:Reference 与 SKILL.md 重写

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 SKILL.md 的"多专家 + P-Diagram + 证据等级"承诺真正落到 reference 文档与流程指令上,使 Claude 能立刻按新流程跑 FMEA,无需任何新脚本。

**Architecture:** 不改任何脚本逻辑,只新增 4 份 reference,改写 SKILL.md 主流程,并对 `retrieve_cases.py` 加一个可选 `--json-out` 参数输出固定 schema(为 M2 铺路)。`draft_fmea_from_cases.py` 仍作为"历史证据辅助",但不再充当主表生成器。

**Tech Stack:** Markdown reference 文档、Python 3 (现有 `retrieve_cases.py`)、pytest (新增最小回归测试)。

---

## 文件结构

**新建**:
- `openclaw-fmea-cocreator/references/p_diagram_template.md` — P-Diagram 抽取范式 + JSON schema + AFMEA/SFMEA/DFMEA 差异
- `openclaw-fmea-cocreator/references/specialist_role_prompts.md` — 6 个角色卡 + 候选行 schema + 必扫描组合规则
- `openclaw-fmea-cocreator/references/deduplication_protocol.md` — 跨 scope (层级树主键) + scope 内 (语义判定) 去重规则
- `openclaw-fmea-cocreator/references/evidence_grading.md` — 4+1 状态证据等级 + 置信度公式 + 触发 confirmation_queue 的阈值
- `tests/test_retrieve_cases_json_out.py` — 验证 retrieve_cases.py 新 `--json-out` 输出 schema 合规

**修改**:
- `openclaw-fmea-cocreator/SKILL.md` — 重写"Core workflow"与"OpenClaw delivery contract",指向新 reference,降级旧脚本的角色
- `openclaw-fmea-cocreator/scripts/retrieve_cases.py` — 新增 `--json-out PATH` 与 `--leaf-id LEAF_ID`,输出固定 JSON schema (M2 的 `evidence_pool/<leaf_id>.json` 直接消费)

**不改**:
- `draft_fmea_from_cases.py`(M2 再剥离)
- `import_existing_fmea_excel.py`(M2 再适配)
- `template.xlsx`(M2 再扩列)

---

## Task 1: 新建 `references/p_diagram_template.md`

**Files:**
- Create: `openclaw-fmea-cocreator/references/p_diagram_template.md`

- [ ] **Step 1: 写文件**

文件全文(直接覆盖创建):

````markdown
# P-Diagram 抽取范式

每次 FMEA 生成的第一步,Claude 必须先把输入文本结构化为 **模块层级树 + P-Diagram** 的 `structure.json`,作为后续多角色失效模式生成的强制 checklist。

本文件定义抽取范式、JSON schema、AFMEA/SFMEA/DFMEA 的差异点,以及失败回滚规则。

## 强制顺序

1. 读完用户全部输入(包括 `validation/input/*.txt` 或用户当前对话)
2. 判定 FMEA 类型(参考 [prompt_templates.md](prompt_templates.md))
3. 按本文件 schema 抽出 `structure.json`,自检 schema 合规
4. 不允许跳过本步骤直接生成失效行

## JSON Schema

```json
{
  "fmea_type": "DFMEA",
  "module_root": "<用户提供的模块名>",
  "hierarchy": {
    "id": "T",
    "name": "<同 module_root>",
    "level": "system",
    "children": [
      {
        "id": "T.1",
        "name": "<子系统名>",
        "level": "subsystem",
        "children": [
          {"id": "T.1.1", "name": "<零部件名>", "level": "component"}
        ]
      }
    ]
  },
  "p_diagrams": [
    {
      "scope_id": "T.1",
      "input_signals": ["..."],
      "control_factors": ["..."],
      "noise_factors": {
        "piece_to_piece": ["..."],
        "environment": ["..."],
        "system_interactions": ["..."],
        "customer_usage": ["..."],
        "wear_aging": ["..."]
      },
      "intended_outputs": ["..."],
      "unintended_outputs": ["..."],
      "error_states": ["..."]
    }
  ]
}
```

## 字段规则

| 字段 | 必填 | 说明 |
|---|---|---|
| `fmea_type` | 是 | 三选一: `AFMEA` / `SFMEA` / `DFMEA` |
| `hierarchy.id` | 是 | 树结构稳定主键,从 `T` 开始,子节点 `T.1` `T.1.1` `T.1.1.1` |
| `hierarchy.level` | 是 | `system` / `subsystem` / `component`;叶节点 `level` 必须是 `component` |
| `p_diagrams[].scope_id` | 是 | 必须存在于 `hierarchy` 中且 `level != component` |
| `noise_factors` 五子项 | 是 | 必须全部 5 个子项都存在,可以为空数组但不可缺键 |
| `intended_outputs` | 是 | 至少 1 条 |
| `unintended_outputs` | 是 | 至少 1 条 |
| `error_states` | 是 | 至少 1 条 |

## AFMEA / SFMEA / DFMEA 的差异点

| 类型 | hierarchy 重点 | P-Diagram 重点 |
|---|---|---|
| **AFMEA** (Application/Lifecycle) | 按生命周期阶段分子节点: 制造 / 运输 / 安装 / 调试 / 使用 / 维护 / 退役 | `customer_usage` 与 `environment` 是主轴;`piece_to_piece` 简略 |
| **SFMEA** (System) | 按子系统与接口分: 子系统A / 子系统B / 接口 A↔B | `system_interactions` 与 `input_signals` 是主轴;`piece_to_piece` 简略 |
| **DFMEA** (Design) | 按零部件、材料、BOM 分 | `piece_to_piece` 与 `wear_aging` 是主轴;全部 5 项 noise 都要详 |

## 必扫描组合定义

P-Diagram 在阶段 2 充当 checklist。"必扫描组合"是指每个角色必须扫遍的轴对:

| 角色 | 必扫描轴 |
|---|---|
| 系统/接口工程师 | `system_interactions × intended_outputs` |
| 设计/模块工程师 | `piece_to_piece × control_factors` |
| 可靠性/试验工程师 | `wear_aging × environment` |
| 制造/工艺工程师 | `piece_to_piece × control_factors` (制造视角) |
| 安全/服务工程师 | `customer_usage × error_states` + 全部 `S≥8` 的 `error_states` |
| 软件/控制工程师 | `input_signals × control_factors × error_states` (仅当 `module_root` 含软件/控制时) |

详见 [specialist_role_prompts.md](specialist_role_prompts.md)。

## 失败回滚

如果用户输入信息不足以填出最低必填字段:

1. 不要伪造内容
2. 列出缺失的具体字段
3. 向用户要求补充输入,标明优先级 (例:`必须补 environment`,`建议补 customer_usage`)
4. 拿到补充再继续阶段 2

## 示例

完整示例放在 [../validation/mock_10/](../../validation/mock_10/) 的对应输入旁边(M2 之后)。
````

- [ ] **Step 2: 验证文件能被 SKILL.md 索引**

Run: `grep -l "p_diagram_template" openclaw-fmea-cocreator/SKILL.md openclaw-fmea-cocreator/references/*.md || echo "not referenced yet, OK before Task 5"`
Expected: 输出 `not referenced yet, OK before Task 5`

- [ ] **Step 3: 提交**

```bash
git add openclaw-fmea-cocreator/references/p_diagram_template.md
git commit -m "feat(fmea): add P-Diagram extraction reference"
```

---

## Task 2: 新建 `references/specialist_role_prompts.md`

**Files:**
- Create: `openclaw-fmea-cocreator/references/specialist_role_prompts.md`

- [ ] **Step 1: 写文件**

````markdown
# 多专家失效模式生成 Prompt 卡

阶段 2 由主 agent 依次扮演 6 个专家角色,每轮以一个角色生成候选失效模式。本文件提供每个角色的 prompt 模板、必扫描轴、输出 schema、独立性约束。

## 通用约束

1. **角色独立**: 每轮只看 `structure.json`,不看其他角色已产出的候选行
2. **强制扫描**: 必扫描组合的每个 (叶节点 × 轴对) 都必须有产出,否则给 `not_applicable_reason`
3. **不许静默跳过**: 任何漏写都会在阶段 4 `merge_and_score.py` 的覆盖率检查中暴露
4. **使用规范化短码**: `failure_mode_canonical` 用 snake_case 英文 (如 `stuck_relay_contact`),保证后续机械去重稳定

## 输出 schema(每个候选行)

```json
{
  "leaf_id": "T.1.5",
  "leaf_name": "控制板卡(MCU+继电器+422)",
  "p_diagram_anchor": {
    "noise": "wear_aging:继电器选型余量不足",
    "unintended_or_error": "error_states:继电器粘连"
  },
  "failure_mode": "触点粘连(Stuck ON)",
  "failure_mode_canonical": "stuck_relay_contact",
  "cause": "感性负载反向电动势拉弧 + 选型余量不足",
  "effect": {
    "customer": "...",
    "downstream": "...",
    "system": "..."
  },
  "current_controls": {
    "prevention": "...",
    "detection": "..."
  },
  "recommended_actions": ["..."],
  "ai_severity": 9,  "ai_severity_rationale": "...",
  "ai_occurrence": 7, "ai_occurrence_rationale": "...",
  "ai_detection": 1,  "ai_detection_rationale": "...",
  "role": "<角色名>",
  "self_confidence": 0.0,
  "assumptions": ["..."]
}
```

**不适用时输出**:

```json
{
  "leaf_id": "T.1.5",
  "p_diagram_anchor": {"noise": "...", "unintended_or_error": "..."},
  "not_applicable_reason": "本叶节点不涉及该噪声组合,因为 ..."
}
```

## 6 个角色卡

### 角色 1: 系统/接口工程师

> 你是 FMEA 团队中的 **系统/接口工程师**,关注子系统边界、信号/能量/物质传递、接口失配。
>
> 这是模块层级树和 P-Diagram:
> ```json
> {structure_json}
> ```
>
> 对 hierarchy 中**每一个叶节点**,扫遍 P-Diagram 中 `system_interactions × intended_outputs` 的所有组合。
>
> 每个组合按本文件"输出 schema"产出 1 行;不适用即给 `not_applicable_reason`,不许静默跳过。
>
> 输出整体为 JSON 数组,可直接被 `merge_and_score.py` 消费。

### 角色 2: 设计/模块工程师

> 你是 FMEA 团队中的 **设计/模块工程师**,关注零部件结构、公差、选型、设计缺陷。
>
> [同上的 structure_json]
>
> 扫遍 `piece_to_piece × control_factors`。其他要求同角色 1。

### 角色 3: 可靠性/试验工程师

> 你是 FMEA 团队中的 **可靠性/试验工程师**,关注寿命、加速老化、试验逃逸、覆盖盲区。
>
> 扫遍 `wear_aging × environment`。在 `current_controls.detection` 字段重点说明现有测试是否能在交付前发现该失效。

### 角色 4: 制造/工艺工程师

> 你是 FMEA 团队中的 **制造/工艺工程师**,关注焊接、装配、来料、检验、过程能力。
>
> 扫遍 `piece_to_piece × control_factors` 中**制造源**的组合(零部件公差、焊接、装配工艺)。
>
> `current_controls.prevention` 重点说明现有工艺与来料控制。

### 角色 5: 安全/服务工程师

> 你是 FMEA 团队中的 **安全/服务工程师**,关注误操作、保护层、检修/服务、警告/告警。
>
> 扫遍 `customer_usage × error_states`,**额外**对所有 `ai_severity ≥ 8` 的 `error_states` 做一次保护层扫描:这些错误是否有独立的保护机制?
>
> 对高 S 行,`recommended_actions` 必须包含至少 1 个独立保护层 (硬件联锁 / 软件警告 / 程序停机 / 物理隔离)。

### 角色 6: 软件/控制工程师 (条件触发)

> **触发条件**: `module_root` 描述含 `MCU` / `软件` / `控制` / `状态机` / `通讯` / `报警` / `联锁` 任一关键词;或 `p_diagram.input_signals` / `control_factors` 含数字信号、协议、配置参数。
> **不触发则跳过此角色**。
>
> 你是 FMEA 团队中的 **软件/控制工程师**,关注状态机、报警、联锁、回滚、配置/数据。
>
> 扫遍 `input_signals × control_factors × error_states` (三维组合,每个叶节点会产生较多行)。
>
> `current_controls.detection` 必须明确"软件能在多少时间内识别此错误,是否触发自动停机"。

## Token 预算

- 每个角色单次调用: 输入 5-15k token (structure_json 主体) + 输出 3-8k token
- 6 个角色总计: 50-100k 输入 / 20-50k 输出
- 如果触达 token 上限: 优先按 hierarchy 分批 (每次只送 2-3 个 leaf)

## 自评 self_confidence 评分指南

| 分值 | 含义 |
|---|---|
| 0.9-1.0 | 在该角色专业范围内,失效模式机理与 S/O/D 评分都有明确依据 |
| 0.7-0.8 | 失效模式确定,但 S/O/D 需企业数据校准 |
| 0.5-0.6 | 失效模式从相邻领域类推,S/O/D 是估算 |
| 0.3-0.4 | 失效模式存在但角色专业外,建议交由更适合的角色复查 |
| 0.0-0.2 | 不该由本角色产出,但 P-Diagram 强制扫描产生了这一行 |
````

- [ ] **Step 2: 提交**

```bash
git add openclaw-fmea-cocreator/references/specialist_role_prompts.md
git commit -m "feat(fmea): add 6 specialist role prompt cards"
```

---

## Task 3: 新建 `references/deduplication_protocol.md`

**Files:**
- Create: `openclaw-fmea-cocreator/references/deduplication_protocol.md`

- [ ] **Step 1: 写文件**

````markdown
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
````

- [ ] **Step 2: 提交**

```bash
git add openclaw-fmea-cocreator/references/deduplication_protocol.md
git commit -m "feat(fmea): add deduplication protocol reference"
```

---

## Task 4: 新建 `references/evidence_grading.md`

**Files:**
- Create: `openclaw-fmea-cocreator/references/evidence_grading.md`

- [ ] **Step 1: 写文件**

````markdown
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
| 历史 S/O/D 与合并后 S/O/D **任一维度差 ≥ 3** | `contradicted` (覆盖以上 4 个) |

**判定顺序**: 先判 contradicted,再判其他 4 个 (因为冲突需要被特别处理)。

**冲突时如何取值**: S/O/D **优先 LLM 推理结果**(取最大值),历史值落入 `rating_history.historical_view` 保留。

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
````

- [ ] **Step 2: 提交**

```bash
git add openclaw-fmea-cocreator/references/evidence_grading.md
git commit -m "feat(fmea): add evidence grading + confidence formula reference"
```

---

## Task 5: 重写 `SKILL.md` 的 Core workflow 与 OpenClaw delivery contract

**Files:**
- Modify: `openclaw-fmea-cocreator/SKILL.md` (全文)

- [ ] **Step 1: 备份当前 SKILL.md**

```bash
cp openclaw-fmea-cocreator/SKILL.md openclaw-fmea-cocreator/SKILL.md.m1_backup
```

- [ ] **Step 2: 用 Edit 替换 `## Core workflow` 整段 (现有第 36-162 行)**

找到 `## Core workflow` 段头,替换为以下内容(到下一段 `## OpenClaw delivery contract` 之前):

```markdown
## Core workflow

新工作流由 6 个强制阶段构成,Claude 必须按顺序执行,不可跳步。

### 阶段 1: 结构化抽取 (P-Diagram + 模块层级树)

在生成任何 FMEA 行之前,先按 [references/p_diagram_template.md](references/p_diagram_template.md) 抽出 `structure.json`:

- `hierarchy` 模块层级树
- `p_diagrams[]` 每个子系统一份 P-Diagram

输出必须通过 schema 自检(详见 reference)。如果用户输入不足,列出缺失字段并要求补充,不要伪造。

### 阶段 2: 多专家失效模式生成 (6 个角色)

按 [references/specialist_role_prompts.md](references/specialist_role_prompts.md) 依次扮演 6 个专家角色:

1. 系统/接口工程师
2. 设计/模块工程师
3. 可靠性/试验工程师
4. 制造/工艺工程师
5. 安全/服务工程师
6. 软件/控制工程师 (条件触发)

每个角色独立,只看 `structure.json`,不看其他角色已产出。每个角色对 hierarchy 每个叶节点扫遍"必扫描轴对",输出 `candidates_{role}.json`。

**强制约束**: 不能静默跳过任何 (叶节点 × 必扫描轴对) 组合。不适用即给 `not_applicable_reason`。

### 阶段 3: 历史证据池

对 hierarchy 每个叶节点跑一次 `retrieve_cases.py`:

```bash
python3 openclaw-fmea-cocreator/scripts/retrieve_cases.py \
  --query "<leaf_name + 上下文关键词>" \
  --module "<module_root>" \
  --json-out evidence_pool/<leaf_id>.json
```

输出 `evidence_pool/<leaf_id>.json` 固定 schema,M2 起由 `merge_and_score.py` 直接消费。

### 阶段 4: 合并、去重、评级、置信度

按 [references/deduplication_protocol.md](references/deduplication_protocol.md) 与 [references/evidence_grading.md](references/evidence_grading.md):

1. 跨 scope 机械去重 (主键 = `leaf_id` × `failure_mode_canonical`)
2. scope 内语义去重 (LLM 仲裁,触发条件: 同 leaf 下 candidate ≥ 2)
3. 合并候选行 (S/O/D 取最大值,rationale 全留)
4. 与历史证据对齐,判定 5 状态 `evidence_grade`
5. 计算 4 分量 `confidence`
6. 覆盖率检查,输出 `coverage_gaps.json`

M1 由 Claude 按 reference 手动执行;M2 起由 `merge_and_score.py` 脚本承担,Claude 只做最后审阅。

### 阶段 5: 工作簿渲染

M1 暂用现有 `draft_fmea_from_cases.py` 的 Excel 部分(列结构未扩),把 evidence_grade / confidence 写入 `AI打分推导依据` 列。

M2 起替换为 `build_workbook.py` + 扩列后的 `template.xlsx`。

### 阶段 6: 评审写回 (M3)

M1/M2 不实现。M3 落地 `confirmed_to_case_library.py` 实现案例库飞轮。
```

- [ ] **Step 3: 替换 `## OpenClaw delivery contract` 整段(指向新 reference)**

找到 `## OpenClaw delivery contract` 段,在原有 minimum delivery rules 之上**加** 5 条新规则(保留原有 rules):

```markdown
### M1 新增交付规则

- 每行必须有 `evidence_grade ∈ {evidence-backed, historical-supported, multi-role-inferred, ai-inferred, contradicted}`,见 [references/evidence_grading.md](references/evidence_grading.md)
- 每行必须有 `confidence ∈ [0,1]`,以及 4 分量明细
- 每行必须有 `p_diagram_anchor` 字符串,指明该行来自 P-Diagram 哪个组合
- `top_risks` 按 `confidence × rpn` 排序,不再按纯 rpn
- `confirmation_queue` 自动包含 `evidence_grade ∈ {contradicted, ai-inferred}` 或 `confidence < 0.5` 的行
```

- [ ] **Step 4: 更新 SKILL.md 末尾的 "When to read which reference" 章节**

在该章节中插入 4 条新 reference:

```markdown
- `references/p_diagram_template.md`: 每次生成 FMEA 前都要读,定义结构化抽取范式
- `references/specialist_role_prompts.md`: 阶段 2 多专家轮次的 prompt 卡
- `references/deduplication_protocol.md`: 跨 scope 与 scope 内去重协议
- `references/evidence_grading.md`: 证据等级与置信度公式
```

- [ ] **Step 5: 提升 SKILL.md `version` 到 `0.3.0-m1`**

替换 `version: 0.2.2` 为 `version: 0.3.0-m1`。

- [ ] **Step 6: 删除备份并提交**

```bash
rm openclaw-fmea-cocreator/SKILL.md.m1_backup
git add openclaw-fmea-cocreator/SKILL.md
git commit -m "refactor(fmea): rewrite SKILL.md workflow around P-Diagram + multi-role + evidence grading"
```

---

## Task 6: 给 `retrieve_cases.py` 加 `--json-out` 与 `--leaf-id` 参数

**Files:**
- Modify: `openclaw-fmea-cocreator/scripts/retrieve_cases.py`

### Step 1: 先写测试

- [ ] **Step 1.1: 创建测试目录与文件**

```bash
mkdir -p tests
```

- [ ] **Step 1.2: 写测试 `tests/test_retrieve_cases_json_out.py`**

```python
"""Verify retrieve_cases.py --json-out produces schema expected by merge_and_score.py (M2)."""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "openclaw-fmea-cocreator" / "scripts" / "retrieve_cases.py"


def test_json_out_schema(tmp_path):
    out_file = tmp_path / "evidence.json"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--query", "压缩机 冷媒 液击",
            "--module", "变温系统",
            "--leaf-id", "T.1.5",
            "--json-out", str(out_file),
            "--top-k", "5",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    assert out_file.exists()

    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert payload["leaf_id"] == "T.1.5"
    assert isinstance(payload["matches"], list)
    assert len(payload["matches"]) <= 5
    if payload["matches"]:
        first = payload["matches"][0]
        for key in [
            "source_workbook",
            "source_sheet",
            "source_row",
            "failure_mode_text",
            "cause_text",
            "effect_text",
            "severity",
            "occurrence",
            "detection",
            "match_score",
            "matched_keywords",
        ]:
            assert key in first, f"missing key {key} in {first}"


def test_json_out_no_match_returns_empty(tmp_path):
    out_file = tmp_path / "evidence.json"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--query", "完全不存在的关键词abcxyz",
            "--module", "变温系统",
            "--leaf-id", "T.99.99",
            "--json-out", str(out_file),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert payload["leaf_id"] == "T.99.99"
    assert payload["matches"] == []
```

- [ ] **Step 1.3: 验证测试当前会失败**

Run: `cd /Users/nova/code/fmea-skill && python3 -m pytest tests/test_retrieve_cases_json_out.py -v`
Expected: FAIL,因为 `--json-out` / `--leaf-id` 还不存在

### Step 2: 实现

- [ ] **Step 2.1: 修改 `retrieve_cases.py` 的 `main()`,加 2 个参数与 JSON 输出分支**

把 `main()` 函数(从 `def main() -> None:` 开始到 `if __name__ == "__main__":` 之前)替换为:

```python
def write_json_output(matches: list[Match], leaf_id: str, output_path: Path, top_k: int) -> None:
    """Write evidence pool JSON consumed by merge_and_score.py (M2)."""
    items = []
    for match in matches[:top_k]:
        items.append({
            "source_workbook": match.workbook,
            "source_sheet": match.sheet,
            "source_row": match.excel_row,
            "failure_mode_text": match.preview,
            "cause_text": "",
            "effect_text": "",
            "severity": None,
            "occurrence": None,
            "detection": None,
            "match_score": match.score,
            "matched_keywords": [],
        })
    payload = {"leaf_id": leaf_id, "matches": items}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Retrieve similar FMEA cases from exported project materials.")
    parser.add_argument("--query", required=True, help="Keywords describing the mechanism, failure, or context.")
    parser.add_argument("--module", help="Optional module name for boosting relevant sheets.")
    parser.add_argument("--top-k", type=int, default=10, help="Number of rows to return.")
    parser.add_argument(
        "--include-supporting",
        action="store_true",
        help="Include planning, strategy, and prompt sheets in addition to sample DFMEA and case templates.",
    )
    parser.add_argument("--json-out", help="Write evidence pool JSON to this path (schema for merge_and_score.py).")
    parser.add_argument("--leaf-id", help="Required when --json-out is used; tags the output with this leaf id.")
    args = parser.parse_args()

    matches = collect_matches(args.query, args.module)
    if not args.include_supporting:
        allowed_themes = {"dfmea_sample_data", "knowledge_base_template"}
        matches = [match for match in matches if match.theme in allowed_themes]

    if args.json_out:
        if not args.leaf_id:
            parser.error("--leaf-id is required when --json-out is used")
        write_json_output(matches, args.leaf_id, Path(args.json_out), args.top_k)
        return

    if not matches:
        print("No matches found.")
        return
    print_markdown(matches, args.top_k)
```

- [ ] **Step 2.2: 运行测试,确认通过**

Run: `cd /Users/nova/code/fmea-skill && python3 -m pytest tests/test_retrieve_cases_json_out.py -v`
Expected: 2 个测试都 PASS

- [ ] **Step 2.3: 验证旧调用方式没坏(Markdown 表格输出)**

Run: `cd /Users/nova/code/fmea-skill && python3 openclaw-fmea-cocreator/scripts/retrieve_cases.py --query "压缩机 冷媒" --module "变温系统" --top-k 3`
Expected: 仍输出 `| score | workbook | sheet | ... |` 表格

- [ ] **Step 3: 提交**

```bash
git add openclaw-fmea-cocreator/scripts/retrieve_cases.py tests/test_retrieve_cases_json_out.py
git commit -m "feat(fmea): add --json-out and --leaf-id to retrieve_cases.py for M2 hand-off"
```

---

## Task 7: 端到端手工验证 M1 跑通

**Files:**
- 仅运行命令,无文件修改

- [ ] **Step 1: 选一个 mock 输入做完整试跑**

Run:
```bash
cat /Users/nova/code/fmea-skill/validation/input/变温系统_input.txt | head -50
```

确认输入存在且可读。

- [ ] **Step 2: 让一个 fresh subagent 按新 SKILL.md 走阶段 1**

使用 Agent 工具,subagent_type=`Explore` 不行(它不能用 Edit),用 `general-purpose`:

prompt:
```
按 openclaw-fmea-cocreator/SKILL.md 的"阶段 1: 结构化抽取"指令,读 validation/input/变温系统_input.txt 全文,产出 structure.json。

要求:
1. 严格按 references/p_diagram_template.md 的 schema
2. 不调用任何脚本,纯按 reference 推理
3. 输出文件到 /tmp/m1_test_structure.json
4. 自检 schema 合规后回复"OK + leaf 节点数 + p_diagrams 数"
```

Expected: subagent 返回 "OK",叶节点数 ≥ 5,p_diagrams 数 ≥ 2

- [ ] **Step 3: 对每个 leaf 跑 retrieve_cases.py 形成 evidence_pool**

Run(用 leaf_id 列表,假设 5 个 leaf):
```bash
mkdir -p /tmp/m1_evidence_pool
# 示例 leaf
python3 openclaw-fmea-cocreator/scripts/retrieve_cases.py \
  --query "压缩机 冷媒 气液分离器" --module "变温系统" \
  --leaf-id "T.1.1" --json-out /tmp/m1_evidence_pool/T.1.1.json
python3 openclaw-fmea-cocreator/scripts/retrieve_cases.py \
  --query "继电器 控制板卡 422" --module "变温系统" \
  --leaf-id "T.1.5" --json-out /tmp/m1_evidence_pool/T.1.5.json
ls /tmp/m1_evidence_pool/
```

Expected: 每个 leaf 一个 .json 文件,schema 合规

- [ ] **Step 4: 让 subagent 按 specialist_role_prompts.md 跑阶段 2 一个角色作为 smoke test**

prompt:
```
作为"设计/模块工程师"角色,按 openclaw-fmea-cocreator/references/specialist_role_prompts.md 的角色 2 指令,基于 /tmp/m1_test_structure.json 产出候选行 JSON 数组。

要求:
1. 扫遍 piece_to_piece × control_factors 的所有组合
2. 不适用即给 not_applicable_reason
3. 每行必须含 failure_mode_canonical (snake_case)
4. 输出到 /tmp/m1_candidates_design.json
5. 回复候选行总数 + 不适用条目数
```

Expected: 候选行总数 ≥ 8,不适用条目数 ≥ 0

- [ ] **Step 5: 验收 M1 是否真"动起来"**

- ✅ `structure.json` schema 合规
- ✅ 6 个角色的指令可被 subagent 执行
- ✅ `retrieve_cases.py --json-out` 输出 evidence_pool 可读
- ✅ SKILL.md 新流程章节存在,旧脚本被降级而非主路径

如果以上 4 条全过 → M1 验收通过。

- [ ] **Step 6: 写一份简短的 M1 验收记录**

Create: `docs/superpowers/specs/m1_acceptance_notes.md`

内容:
```markdown
# M1 验收记录

- 日期: <YYYY-MM-DD>
- 验收人: <name>
- 输入场景: 变温系统
- structure.json leaf 数: <N>
- p_diagrams 数: <N>
- 一个角色 (设计/模块) 候选行数: <N>
- evidence_pool 命中数: <N>
- 结论: 通过 / 不通过 + 原因
```

- [ ] **Step 7: 提交验收记录**

```bash
git add docs/superpowers/specs/m1_acceptance_notes.md
git commit -m "docs(fmea): M1 acceptance notes"
```

---

## Self-Review 自检

**Spec 覆盖**:
- § 1 结构化抽取 → Task 1 (p_diagram_template.md)
- § 2 多专家失效生成 → Task 2 (specialist_role_prompts.md)
- § 4 合并去重评级 → Task 3 (deduplication) + Task 4 (evidence_grading)
- § 5 工作簿渲染 → M1 不动模板,Task 5 在 SKILL.md 中明示"M1 暂用现有 draft_fmea_from_cases.py 的 Excel 部分"
- § 6 评审写回 → M1 不做,SKILL.md 中明示 M3 实现
- 错误处理 → 散落在 4 个 reference 中(回滚规则、不适用处理、冲突优先 LLM、确认队列触发)
- 测试结构 → Task 6 加了单元测试,Task 7 是端到端手工验收

**Placeholder 扫描**: 已确认无 TBD / TODO / "implement later" 类占位符。

**类型一致性**: `structure.json` / `candidates_{role}.json` / `evidence_pool/<leaf_id>.json` 三个 schema 在 4 个 reference 间字段命名一致(`leaf_id`, `failure_mode_canonical`, `p_diagram_anchor`, `evidence_grade`, `confidence`, `confidence_breakdown` 完全统一)。
