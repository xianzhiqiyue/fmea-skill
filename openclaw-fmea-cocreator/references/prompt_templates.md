# Prompt Templates

These templates are adapted from the current project materials and should be used as framing aids, not copied mechanically.

Primary source:

- `excel_materials/workbooks/AI质量赋能/sheets/06_AI-FMEA提示语模板.md`

## AFMEA framing

Use for:

- storage
- transport
- operation flow
- maintenance
- lifecycle environment stress

Template:

```text
分析对象是：{product_or_module}
生命周期阶段是：{stage}
相关环境或任务剖面是：{environment_or_flow}

请识别该阶段可能的失效模式、失效原因、对客户或后工序的影响，
并按 S/O/D 给出初步评分与理由，计算 RPN。
请同时给出建议措施，并标记哪些评分需要专家确认。
```

## SFMEA framing

Use for:

- whole system to subsystem decomposition
- interface analysis
- structure, information, and energy transfer relationships

Template:

```text
请针对 {system_name} 做 SFMEA 共创。
系统分解如下：{system_breakdown}
关键接口如下：{interfaces}
请围绕系统功能、子系统边界和接口关系，识别主要失效模式、
影响、原因、现行控制与建议措施，并输出结构化表格。
```

## DFMEA framing

Use for:

- subsystem to component or material analysis
- BOM展开
- design requirement to part-level risk decomposition

Template:

```text
请针对 {module_name} 做 DFMEA 共创。
模块功能与指标：{functions_and_requirements}
关键零件或BOM：{bom_or_parts}
使用环境与边界条件：{environment}
历史问题或相似案例：{historical_cases}

请输出按功能展开的 DFMEA 草稿，包括失效模式、影响、原因、
现行控制、建议措施、S/O/D 初步评分和 RPN，并标出待确认项。
```

## Failure-mode-class prompts

When the user wants to expand a function from different failure categories, use these categories:

- 功能丧失
- 功能退化
- 间歇性功能
- 部分功能
- 非预期功能
- 功能不足
- 功能错误

Template:

```text
围绕功能“{function_name}”，分别从以下失效类别展开：
功能丧失、功能退化、间歇性功能、部分功能、非预期功能、功能不足、功能错误。
每一类给出可能失效模式、影响、原因、现行控制和建议措施。
```

## Multi-specialist FMEA cluster prompts

Use these prompts when the task needs a cross-functional FMEA team.
Choose only the specialist roles relevant to the module.

### Cluster leader prompt

```text
你是FMEA共创负责人。请把输入材料分配给多个专业视角进行分析：
系统/架构、设计/模块、可靠性/测试、制造/质量、安全/合规、现场服务/维护、
客户/应用、供应链/物流、软件/控制（仅选择相关角色）。

每个专业视角必须输出标准FMEA行：
生命周期维度或scope、模块/零件、功能及要求、参数指标性能、失效影响、
严重度S及依据、潜在失效模式、失效原因、现行预防措施、频度O及依据、
现行探测控制、探测度D及依据、RPN、建议措施、措施负责人、完成时间、
参考类型、来源追溯、待确认原因。

汇总时请去重、保留评分分歧、把证据不足或角色冲突的行放入确认队列，
并输出Top风险和建议动作。
```

### Specialist lane prompt

```text
你代表专业角色：{specialist_role}
分析对象：{module_or_scope}
输入材料：{input_summary}
历史或相似案例：{case_trace}

请只从你的专业视角提出FMEA候选行。
不要覆盖其他专业角色的职责。
每行必须做到：
1. 一个失效模式一行；
2. 明确功能、失效影响、失效原因、现行预防/探测控制；
3. 给出S/O/D/RPN和评分依据；
4. 标记证据类型：current module / direct family reference / broader analogy；
5. 标记待专家确认项和假设；
6. 给出建议措施、责任角色占位、完成时间占位。
```

### Specialist role focus

| Role | Focus |
| --- | --- |
| 系统/架构工程师 | 系统边界、接口、能量/材料/信息传递、集成假设 |
| 设计/模块工程师 | 功能分解、设计裕量、部件失效、DFMEA原因 |
| 可靠性/测试工程师 | 寿命、应力、验证覆盖、测试逃逸、O/D依据 |
| 制造/质量工程师 | 装配、过程波动、供应商质量、检验和预防控制 |
| 安全/合规工程师 | 危害、误用、法规、安全联锁、高S风险 |
| 现场服务/维护工程师 | 安装、校准、磨损、可维护性、诊断、备件 |
| 客户/应用工程师 | 实际工况、误操作、验收标准、任务中断 |
| 供应链/物流工程师 | 包装、运输、存储、来料质量、交付损伤 |
| 软件/控制工程师 | 状态机、报警、联锁、配置、数据和控制失效 |

## When to be conservative

Use more constrained prompting when:

- the module is safety-critical
- high-power, high-voltage, pressure, cryogenic, EMC, or motion hazards are involved
- the user wants action items, not only brainstorming
