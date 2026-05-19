# FMEA Skill 重构设计文档

- 日期: 2026-05-19
- 目标 skill: `openclaw-fmea-cocreator`
- 当前版本: 0.2.2
- 目标版本: 0.3.0

## 背景与问题诊断

当前 `openclaw-fmea-cocreator` 的实际行为与 `SKILL.md` 描述存在巨大差距。

SKILL.md 声称采用"多专家 agent 集群协作生成 FMEA",但生成的真实路径完全集中在单个脚本 `draft_fmea_from_cases.py`(1796 行,占代码 87%),它做的事情只是:

1. 把用户输入文本按关键词切成几个 scope
2. 从 `excel_materials/workbooks/CAN400产品DFMEA/` 用关键词检索历史行
3. 把命中的历史行近似原样填进当前 FMEA 主表
4. 每行 `Source case` 都指向 `CAN400产品DFMEA.xlsx / 变温系统 / row N`

没有真正的 LLM 推理参与 FMEA 生成,是"关键词检索 + 历史行拷贝"。

这导致用户反馈的两个核心症状:

| 症状 | 根因 |
|---|---|
| 生成 FMEA 不全面 | 只能覆盖关键词命中的历史行;新模块、新工况、新接口里没有历史先例的失效模式无法生出。`validation/mock_10/` 中 10 个完全不同的场景都恰好产出 7 个 scope × 28 行,即为此 bug 的指纹。 |
| 重复数据 | 关键词在多个 scope 命中同一历史行;scope 分割基于关键词,本就有重叠;同一 `source_row` 在 `Source Trace` 中出现多次。 |

本设计将重构 skill 工作流,使其与声称能力一致,并解决以上两个症状。

## 设计选择(已与用户确认)

| 维度 | 决策 |
|---|---|
| 生成动力 | LLM 推理 + 历史检索两条腿并行,标证据等级,冲突时优先 LLM |
| 专家规模 | 轻量多角色: 主 agent 多轮提示,每轮以一个专家角色生成 |
| 覆盖度骨架 | P-Diagram 驱动 (输入信号/控制因子/噪声因子/输出响应/不期望响应/错误状态) |
| 去重 | 模块层级树(跨 scope)+ 语义判定(scope 内) |
| 可信度表达 | 4 状态证据等级 + 0-1 置信度评分 + 独立 `needs_human_confirmation` 列 |
| 落地范围 | A+B+C 一次性完整设计,但分 3 个里程碑交付 |
| 工作簿列结构 | 允许打破现有列,新 `template.xlsx` 扩列 |

## 顶层架构

```
┌──────────────────────────────────────────────────────────────┐
│  阶段1: 结构化抽取      → 阶段2: 多专家失效生成              │
│  ├─ 模块层级树.json     → 6 个角色轮次,各产 candidate.json  │
│  └─ p_diagram.json      → (失效模式 + S/O/D 自评 + 理由)     │
│                                                              │
│  阶段3: 历史证据池          阶段4: 合并·评级·置信度          │
│  ├─ retrieve_cases ─→ ─┐    ┌─→ merge_and_score.py           │
│  evidence_pool.json    │    │   → fmea_normalized.json       │
│                        ↓    ↓     (含证据等级/置信度/锚点)   │
│                                                              │
│  阶段5: 工作簿渲染          阶段6: OpenClaw 评审写回         │
│  build_workbook.py          apply_openclaw_review_actions    │
│  → xlsx (扩列)              → 确认行回流 case_library/       │
│                                ↓                             │
│                          case_library/ (持续增长)            │
└──────────────────────────────────────────────────────────────┘
```

### 组件清单

| 组件 | 输入 | 输出 | 性质 |
|---|---|---|---|
| `references/p_diagram_template.md` | — | prompt 模板 | 新增 reference |
| `references/specialist_role_prompts.md` | — | 6 个角色 prompt | 新增 reference |
| `references/deduplication_protocol.md` | — | 去重规则 | 新增 reference |
| `references/evidence_grading.md` | — | 证据等级与置信度公式 | 新增 reference |
| `scripts/extract_structure.py` (可选) | 文本+FMEA类型 | `structure.json` | 第一版用 prompt,后续按需脚本化 |
| `scripts/retrieve_cases.py` (扩展) | leaf 关键词 | `evidence_pool/<leaf_id>.json` | 现有,扩展输出 schema |
| `scripts/merge_and_score.py` | candidates + evidence_pool | `fmea_normalized.json` | 新脚本(核心) |
| `scripts/build_workbook.py` | `fmea_normalized.json` | `<output>.xlsx` | 从现有脚本剥离 |
| `scripts/confirmed_to_case_library.py` | review_actions + xlsx | `case_library/<module>/<YYYY-Q*>.json` | 新脚本 |
| `template.xlsx` | — | 扩列后的标准模板 | 替换 |

## 阶段 1: 结构化抽取(P-Diagram + 层级树)

**输入**: 用户文本(模块描述 / 已有 FMEA 摘要)+ FMEA 类型(AFMEA / SFMEA / DFMEA)

**输出 `structure.json` schema**:

```json
{
  "fmea_type": "DFMEA",
  "module_root": "变温系统",
  "hierarchy": {
    "id": "T",
    "name": "变温系统",
    "level": "system",
    "children": [
      {
        "id": "T.1",
        "name": "压缩机制冷子系统",
        "level": "subsystem",
        "children": [
          {"id": "T.1.1", "name": "压缩机本体", "level": "component"},
          {"id": "T.1.2", "name": "气液分离器", "level": "component"},
          {"id": "T.1.3", "name": "毛细管", "level": "component"},
          {"id": "T.1.4", "name": "蒸发器", "level": "component"},
          {"id": "T.1.5", "name": "控制板卡(MCU+继电器+422)", "level": "component"}
        ]
      }
    ]
  },
  "p_diagrams": [
    {
      "scope_id": "T.1",
      "input_signals": ["上位机功率指令", "压缩机状态查询", "温度反馈"],
      "control_factors": ["继电器输出时序", "1028 阀开启时机", "MCU 启动延时 5s"],
      "noise_factors": {
        "piece_to_piece": ["压缩机选型 CAJZ2432PBR 容差", "焊缝壁厚不均"],
        "environment": ["室温 -10~45℃", "电网电压波动", "运输振动"],
        "system_interactions": ["与液氮蒸发子系统温度耦合", "上位机断电"],
        "customer_usage": ["频繁开停机", "0 档紧急停机", "长时间高功率运行"],
        "wear_aging": ["阀片疲劳", "波纹管疲劳", "O 圈低温脆化", "焊缝热影响区疲劳"]
      },
      "intended_outputs": ["稳定输出冷量至样品端 ≤ -40℃"],
      "unintended_outputs": ["振动传递至探头(信噪比下降)", "冷媒泄漏", "噪声"],
      "error_states": ["液击", "带液启动", "冰堵", "继电器粘连", "传感器读数卡死"]
    }
  ]
}
```

**约束**:
1. 每个 P-Diagram 对应一个 hierarchy 子系统节点(`scope_id`)。
2. 叶节点必须挂在某个 P-Diagram scope 下。后续 FMEA 行通过 `leaf_id` 唯一,通过 `p_diagram_anchor` 引用 P-Diagram 上的"必扫描组合"。

**实现**:第一版纯 prompt 完成,不写脚本。`references/p_diagram_template.md` 提供抽取指令、schema 示例、与各 FMEA 类型的差异点(AFMEA 强调生命周期阶段、SFMEA 强调接口、DFMEA 强调零部件)。

**回滚**:如果 hierarchy 抽取不完整,在阶段 4 `merge_and_score.py` 会做 schema 校验并报错。

## 阶段 2: 多专家失效模式生成

**6 个固定角色**(`references/specialist_role_prompts.md`):

| 角色 | P-Diagram 必扫描轴 | 输出聚焦 |
|---|---|---|
| 系统/接口工程师 | `system_interactions × intended_outputs` | 子系统边界、信号/能量/物质传递、接口失配 |
| 设计/模块工程师 | `piece_to_piece × control_factors` | 零部件结构、公差、选型、设计缺陷 |
| 可靠性/试验工程师 | `wear_aging × environment` | 寿命、加速老化、试验逃逸、覆盖盲区 |
| 制造/工艺工程师 | `piece_to_piece × control_factors`(制造源) | 焊接、装配、来料、检验、过程能力 |
| 安全/服务工程师 | `customer_usage × error_states` + 高 S 错误状态 | 误操作、保护层、检修/服务、警告/告警 |
| 软件/控制工程师 | `input_signals × control_factors × error_states` | 状态机、报警、联锁、回滚、配置/数据 |

**每个角色 prompt 必须**:
1. 接收完整 `structure.json`
2. 对每一个叶节点扫过 P-Diagram 中"必扫描轴"的所有组合
3. 命中即输出完整 schema 行;不适用即输出 `{leaf_id, anchor, not_applicable_reason}`,不许静默跳过
4. 完全独立,不看其他角色输出

**候选行 schema**(`candidates_{role}.json` 中每条):

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
  "current_controls": {"prevention": "...", "detection": "..."},
  "recommended_actions": ["..."],
  "ai_severity": 9,  "ai_severity_rationale": "...",
  "ai_occurrence": 7, "ai_occurrence_rationale": "...",
  "ai_detection": 1,  "ai_detection_rationale": "...",
  "role": "设计/模块",
  "self_confidence": 0.75,
  "assumptions": ["..."]
}
```

**关键设计点**:
- P-Diagram 当作 checklist,强制扫遍组合(治"不全面")
- `p_diagram_anchor` 是后续合并、覆盖率检查的对齐键
- `failure_mode_canonical` 是 snake_case 英文规范化短码,后续去重主键
- 自评 `self_confidence` 进入综合置信度公式
- 各角色独立,避免互相渍染

**Token 预算**:6 角色 × 每次 5-15k 输入 + 3-8k 输出 ≈ 单次 FMEA 阶段 2 消耗 50-100k 输入 / 20-50k 输出。

**风险与兜底**:LLM 在"必扫描组合"上仍可能漏。阶段 4 `merge_and_score.py` 做组合覆盖率检查,未覆盖且无 `not_applicable_reason` 的组合进入 `coverage_gaps.json`。

## 阶段 3: 历史证据池

**调用**:对 hierarchy 每个 leaf 跑一次 `retrieve_cases.py`

```bash
python3 scripts/retrieve_cases.py \
  --query "<leaf_name + 关键词>" \
  --module "<module_root>" \
  --output evidence_pool/<leaf_id>.json
```

**evidence_pool/<leaf_id>.json schema**:

```json
{
  "leaf_id": "T.1.5",
  "matches": [
    {
      "source_workbook": "CAN400产品DFMEA.xlsx",
      "source_sheet": "变温系统",
      "source_row": 25,
      "failure_mode_text": "液击风险 (Liquid Hammer)",
      "cause_text": "...",
      "effect_text": "...",
      "severity": 7, "occurrence": 6, "detection": 8,
      "match_score": 0.78,
      "matched_keywords": ["压缩机", "冷媒", "液击"]
    }
  ]
}
```

**对 retrieve_cases.py 的扩展**:
1. 输入由单句 query 改为按 leaf 自动展开
2. 输出固定 schema,便于 `merge_and_score.py` 消费
3. 检索源扩展到 `case_library/**/*.json`(M3 落地后由飞轮持续填充)

## 阶段 4: 合并、去重、评级、置信度

**核心新脚本 `scripts/merge_and_score.py`**。
输入: `structure.json` + 6 份 `candidates_{role}.json` + `evidence_pool/*.json`
输出: `fmea_normalized.json`

### 步骤 4.1 — 跨 scope 去重(层级树主键约束)
- 主键: `(leaf_id, failure_mode_canonical)`
- 来自不同角色的候选只要主键相同,进入"待合并桶"
- 这一步是机械去重,不调 LLM

### 步骤 4.2 — scope 内语义去重(LLM 仲裁,可选触发)
- 同一 leaf_id 下,若两条 `failure_mode_canonical` 不同但语义可能重叠(如 "冷缩泄漏" vs "低温密封失效"),发一次 LLM judge 调用
- 输出: `merge / keep_separate / keep_with_distinguisher`
- 触发条件: 同一 leaf 下 candidate ≥ 2 才跑

### 步骤 4.3 — 合并候选行(同一主键内)
- `effect` / `cause` / `current_controls` / `recommended_actions`: 联合(去重后用 `;` 拼接,保留 role 标签)
- `ai_severity` / `ai_occurrence` / `ai_detection`: 取最大值,记录每角色原始评分到 `rating_history`
- 角色数 ≥ 2 时,行获得 `multi_role_corroborated = true`

### 步骤 4.4 — 历史证据对齐与证据等级判定

| 条件 | 证据等级 |
|---|---|
| ≥ 1 历史匹配 + ≥ 2 角色覆盖 | `evidence-backed` |
| ≥ 1 历史匹配 + 仅 1 角色覆盖 | `historical-supported` |
| 0 历史匹配 + ≥ 2 角色覆盖 | `multi-role-inferred` |
| 0 历史匹配 + 仅 1 角色覆盖 | `ai-inferred` |
| 历史 S/O/D 与 LLM 自评相差 ≥ 3(任一维度) | `contradicted`(覆盖以上) |

**冲突优先 LLM**:S/O/D 取 LLM 最大值,历史值落入 `rating_history.historical_view`,标 `contradicted`。

### 步骤 4.5 — 置信度评分 0-1

```
confidence = w1 * role_agreement
           + w2 * evidence_strength
           + w3 * sod_grounding
           + w4 * pdiagram_coverage

w1=0.30, w2=0.30, w3=0.25, w4=0.15
```

- `role_agreement`: 给出过该 (leaf, failure_mode) 的角色比例
- `evidence_strength`: 历史匹配数与 max(match_score) 加权
- `sod_grounding`: S/O/D 是否有企业数据/历史依据 vs 纯估
- `pdiagram_coverage`: 该行的 `p_diagram_anchor` 是否覆盖了"必扫描"轴

每分量 0-1 归一化。权重写在 `references/evidence_grading.md`,可调。最终输出保留 4 分量明细。

### 步骤 4.6 — 覆盖率检查
- 对 P-Diagram 每条轴 × 每个 leaf 做笛卡尔积
- 检查未被任何候选行覆盖且无 `not_applicable_reason` 的组合
- 输出 `coverage_gaps.json`

### `fmea_normalized.json` 关键 schema

```json
{
  "rows": [
    {
      "row_id": "T.1.5/继电器粘连",
      "leaf_id": "T.1.5",
      "scope_path": "T → T.1 → T.1.5",
      "failure_mode": "触点粘连(Stuck ON)",
      "failure_mode_canonical": "stuck_relay_contact",
      "p_diagram_anchor": "wear_aging:继电器选型余量不足 × error_states:继电器粘连",
      "cause": "...合并文本...",
      "effect_customer": "...",
      "effect_system": "...",
      "current_controls_prevention": "...",
      "current_controls_detection": "...",
      "recommended_actions": ["..."],
      "severity": 9, "occurrence": 7, "detection": 1, "rpn": 63,
      "evidence_grade": "evidence-backed",
      "confidence": 0.78,
      "confidence_breakdown": {
        "role_agreement": 0.67, "evidence_strength": 0.85,
        "sod_grounding": 0.80, "pdiagram_coverage": 0.80
      },
      "rating_history": {
        "role_view": [{"role": "设计/模块", "s":9, "o":7, "d":1}],
        "historical_view": {
          "s":9, "o":7, "d":1,
          "source": "CAN400产品DFMEA.xlsx/变温系统/row 31"
        }
      },
      "needs_human_confirmation": false,
      "source_traces": [
        {"type": "historical", "ref": "CAN400产品DFMEA.xlsx/变温系统/row 31"},
        {"type": "role_inference", "role": "设计/模块"}
      ]
    }
  ],
  "coverage_gaps": [
    {"leaf_id": "T.1.2", "axis_combo": "wear_aging × intended_outputs", "severity_estimate": "潜在"}
  ],
  "top_risks": [],
  "confirmation_queue": []
}
```

- `top_risks` 排序: `confidence × rpn`,防止高 RPN 低置信度的纸老虎压倒高置信度真问题
- `confirmation_queue`: `evidence_grade ∈ {contradicted, ai-inferred}` 或 `confidence < 0.5` 自动入列

## 阶段 5: 工作簿渲染

**新脚本 `scripts/build_workbook.py`**(从现有 1796 行 `draft_fmea_from_cases.py` 中剥离 Excel 部分)。
**新 `template.xlsx`**(允许打破现有列结构)。

### Sheet 布局

**Sheet 1: 封面** — 加 4 个新区块
- 基本信息: 模块、FMEA 类型、生成时间 (保留)
- 覆盖摘要 (新): hierarchy 节点数 / 角色覆盖热力图 / coverage_gaps 行数
- 证据等级分布 (新): 饼图,5 等级各占多少行
- 置信度分布 (新): 直方图,0-1 分桶
- 评审导引 (新): 指引人工先看 confirmation_queue

**Sheet 2: FMEA 主表** — 列结构调整为 31 列

```
A  序号
B  Scope path  (T → T.1 → T.1.5)
C  Leaf 节点
D  Analysis object
E  Function or requirement
F  P-Diagram 锚点  (新)
G  Failure mode
H  Failure mode canonical  (新)
I  Failure effect
J  S (Severity)
K  Cause or mechanism
L  O (Occurrence)
M  Current controls (prevention)
N  Current controls (detection)
O  D (Detection)
P  RPN  (=J*L*O)
Q  Recommended actions
R  Owner
S  Target date
T  改进后 S
U  改进后 O
V  改进后 D
W  改进后 RPN  (=T*U*V)
X  Evidence grade  (新, 5 类条件格式着色)
Y  Confidence  (新, 0-1 数据条)
Z  Confidence breakdown  (新, 4 分量明细)
AA Multi-role corroborated  (新, Y/N)
AB Rating history  (新, 各角色 + 历史的原始评分)
AC Needs human confirmation  (新, 布尔)
AD Source traces  (新, 历史 + 角色合并)
AE AI 打分推导依据  (保留, 来自 confidence_breakdown.justification)
```

**主要变化**:
- 22 → 31 列
- 新增 F 让评审者看 P-Diagram 哪个组合产出此行
- 新增 H canonical 用于历史回写稳定主键
- 删除现有 `Reference type` / `Source case` 单列,合并到 AD `source_traces`(可承载多源)

**Sheet 3: 评分准则参考** — 保留不变

**Sheet 4 (新): 覆盖盲区与待确认队列**
- 上半: `coverage_gaps` 列表,带"未覆盖原因可能是: P-Diagram 抽错 / 不适用 / 专家漏写"提示
- 下半: `confirmation_queue` 按 `confidence × rpn` 倒序

**Sheet 5 (新): 结构与 P-Diagram**
- 上半: hierarchy 树状文本
- 下半: 每个子系统的 P-Diagram(6 轴 × 条目)

### 视觉规范

| 元素 | 处理 |
|---|---|
| `evidence_grade` | 5 色条件格式: evidence-backed=深绿 / historical-supported=浅绿 / multi-role-inferred=浅黄 / ai-inferred=橙 / contradicted=红 |
| `confidence` | 数据条 0-1 灰阶 |
| RPN 与改进后 RPN | 保留 Excel 公式 |
| `needs_human_confirmation = true` 的行 | 整行浅红底 |

### 兼容性
- 直接替换 `template.xlsx`,旧版备份为 `template_legacy.xlsx`
- `import_existing_fmea_excel.py` 适配: 老 22 列映射到新 31 列(新列留空待补)

## 阶段 6: OpenClaw 评审写回与案例库飞轮

### 6.1 评审动作

OpenClaw 评审卡片新增 5 种动作:

| 动作 | 触发 |
|---|---|
| `confirm` | 接受 AI 草稿,无修改 |
| `edit` | 评审修改字段(主要 S/O/D 或 controls/actions) |
| `reject` | 不适用 |
| `defer` | 暂无结论 |
| `promote_to_case` | 作为新历史案例回填案例库 |

### 6.2 新脚本 `scripts/confirmed_to_case_library.py`

**回填条件**:仅当 `action ∈ {confirm + evidence_grade ≥ historical-supported, promote_to_case}` 时才回填,避免把 `ai-inferred` 行直接写进案例库形成回声室。

**回填条目** schema 与 `excel_materials/workbooks/CAN400产品DFMEA/` 现有行兼容,但增加 `provenance`(来自哪份 FMEA、什么时候确认、谁确认)。

**输出路径**: `case_library/<module>/<YYYY-Q*>.json`

### 6.3 retrieve_cases.py 检索源扩展

```python
case_sources = [
    "excel_materials/workbooks/CAN400产品DFMEA/...",  # 原始
    "case_library/**/*.json",                          # 新, 飞轮产物
]
```

**加权**: `case_library/` 同模块的命中权重 × 1.5(本企业、近期、已确认 → 优先于通用历史)。

### 6.4 与 OpenClaw 后端的最小耦合
- `references/openclaw_review_action_protocol.json` 加 `promote_to_case` 字段(向后兼容)
- `references/openclaw_review_cards_schema.json` 加 `evidence_grade` / `confidence` 显示项
- 后端可选改造:评审完成后调一次 `confirmed_to_case_library.py`;不改造也不影响主流程

## 错误处理

| 失败点 | 表现 | 处理 |
|---|---|---|
| 阶段 1 schema 不合法 | LLM 非法 JSON | Schema 校验, 重试 1 次, 二次失败报错 |
| 阶段 2 某角色超时/空 | 该角色无候选 | 跳过, 记录 `role_failure`, confidence 计算降 `role_agreement` |
| 阶段 2 全部角色失败 | 灾难 | 终止流水线, 不输出"半个表" |
| 阶段 3 0 命中 | 新模块, 无历史 | 全部行落 `ai-inferred`, 封面醒目提示 |
| 阶段 4 主键冲突 | 合并 | 自动合并, `rating_history` 保留各源 |
| 阶段 4 LLM 仲裁失败 | 网络 | 降级: 跳过 scope 内语义去重, 标 `semantic_dedup_skipped` |
| 阶段 5 模板缺失/损坏 | 渲染失败 | 报错给用户 |
| 阶段 6 review_actions schema 不合法 | 写回失败 | 不影响主 FMEA, 飞轮不转 |

**通用原则**:任何降级在工作簿封面/日志明示,不悄悄发生。

## 测试结构

```
tests/
├── unit/
│   ├── test_extract_structure_schema.py
│   ├── test_merge_and_score.py
│   ├── test_coverage_gap_detection.py
│   ├── test_build_workbook.py
│   └── test_confirmed_to_case_library.py
├── integration/
│   ├── test_end_to_end_dfmea.py
│   ├── test_end_to_end_existing_import.py
│   └── test_review_writeback_loop.py
└── regression/
    └── mock_10/
        └── assertions:
            - 每场景 hierarchy ≥ 5 leaf
            - 没有跨 scope 共享 source_row
            - 至少 60% 行 multi_role_corroborated
            - confidence 与 evidence_grade 一致
            - rows 数量不再统一为 28
```

**关键回归断言**: 当前 10 场景"行数恒等 28"现象作为 **必须打破的 anti-pattern**,新版**不**出现此现象。这是治"重复"成功的指纹。

## 分阶段交付里程碑

### M1: Reference 与 SKILL.md 重写 (约 3-4 天)
- 4 个新 reference: `p_diagram_template.md` / `specialist_role_prompts.md` / `deduplication_protocol.md` / `evidence_grading.md`
- SKILL.md 主流程重写
- 现有脚本最小修改(retrieve_cases 输出 schema 扩展)
- **验收**: 单个 mock 场景手工跑通, 产出能看到证据等级、置信度、coverage gaps

### M2: 新脚本与新模板 (约 1 周)
- `extract_structure.py` (可选)、`merge_and_score.py`、`build_workbook.py`、新 `template.xlsx`
- `import_existing_fmea_excel.py` 适配新列
- 完整单元测试 + mock_10 回归
- **验收**: `validation/mock_10/` 全部跑过, 行数与 source row 不再恒等

### M3: 案例库飞轮 + OpenClaw 接口 (约 1 周)
- `confirmed_to_case_library.py`
- `apply_openclaw_review_actions.py` 扩展
- OpenClaw schema 文件更新
- **验收**: "FMEA → 评审 → 再 FMEA" 双循环, evidence-backed 比例可测量提升

## 不在本设计范围内的事项

- 不重写 retrieve_cases 的索引算法(当前 BM25 风格够用)
- 不构建独立 LLM API 主体(继续 Claude/Codex 驱动)
- 不引入嵌入向量检索(M2 完成后视效果再评估)
- 不动 OpenClaw 后端代码,只动 skill 这一侧的 schema 与脚本接口
