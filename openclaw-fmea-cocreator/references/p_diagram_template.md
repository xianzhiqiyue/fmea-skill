# P-Diagram 抽取范式

每次 FMEA 生成的第一步,Claude 必须先把输入文本结构化为 **模块层级树 + P-Diagram** 的 `structure.json`,作为后续多角色失效模式生成的强制 checklist。

本文件定义抽取范式、JSON schema、AFMEA/SFMEA/DFMEA/PFMEA 的差异点,以及失败回滚规则。

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
| `fmea_type` | 是 | 四选一: `AFMEA` / `SFMEA` / `DFMEA` / `PFMEA` |
| `hierarchy.id` | 是 | 树结构稳定主键,从 `T` 开始,子节点 `T.1` `T.1.1` `T.1.1.1` |
| `hierarchy.level` | 是 | `system` / `subsystem` / `component`;叶节点 `level` 必须是 `component` |
| `p_diagrams[].scope_id` | 是 | 必须存在于 `hierarchy` 中且 `level != component` |
| `noise_factors` 五子项 | 是 | 必须全部 5 个子项都存在,可以为空数组但不可缺键 |
| `intended_outputs` | 是 | 至少 1 条 |
| `unintended_outputs` | 是 | 至少 1 条 |
| `error_states` | 是 | 至少 1 条 |

## AFMEA / SFMEA / DFMEA / PFMEA 的差异点

| 类型 | hierarchy 重点 | P-Diagram 重点 |
|---|---|---|
| **AFMEA** (Application/Lifecycle) | 按生命周期阶段分子节点: 制造 / 运输 / 安装 / 调试 / 使用 / 维护 / 退役 | `customer_usage` 与 `environment` 是主轴;`piece_to_piece` 简略 |
| **SFMEA** (System) | 按子系统与接口分: 子系统A / 子系统B / 接口 A↔B | `system_interactions` 与 `input_signals` 是主轴;`piece_to_piece` 简略 |
| **DFMEA** (Design) | 按零部件、材料、BOM 分 | `piece_to_piece` 与 `wear_aging` 是主轴;全部 5 项 noise 都要详 |
| **PFMEA** (Process) | 按过程步骤/工位/检验点分: 来料 / 装配 / 参数控制 / 测试 / 包装放行 | `piece_to_piece`、`control_factors`、`system_interactions` 关注人机料法环测与后工序流出 |

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
