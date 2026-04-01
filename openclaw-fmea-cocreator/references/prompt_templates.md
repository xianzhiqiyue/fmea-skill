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

## When to be conservative

Use more constrained prompting when:

- the module is safety-critical
- high-power, high-voltage, pressure, cryogenic, EMC, or motion hazards are involved
- the user wants action items, not only brainstorming
