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
