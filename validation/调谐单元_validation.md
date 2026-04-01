# 调谐单元第三轮验证

## 目的

使用第三个真实模块 `调谐单元` 验证 `openclaw-fmea-cocreator` 在更复杂模块上的表现，重点看三件事：

1. 自动 `scope` 能否拆出 3 类子系统
2. 当当前模块家族案例已经足够时，是否还能压住无关模块噪音
3. 当某个 scope 的本模块样例不足时，是否还能适度借用跨模块类比

## 验证对象

- 模块名称：`调谐单元`
- FMEA 类型：`DFMEA`
- 验证重点：射频高压匹配、机械限位保护、EMC/算法控制的混合场景

## 输入来源

### 输入样板

输入文件：

- `/Users/nova/code/fmea-skill/validation/input/调谐单元_input.txt`

输入样板基于以下资料整理：

- `/Users/nova/code/fmea-skill/excel_materials/workbooks/CAN400产品DFMEA/sheets/03_调谐单元.md`
- `/Users/nova/code/fmea-skill/excel_materials/workbooks/AI质量赋能/sheets/07_NMR-FMEA计划与实施.md`

输入里没有直接照抄失效项，而是保留了这些功能边界：

- 射频调谐与匹配网络
- 机械传动与限位结构
- 编码器与闭环控制
- 线圈、焊接与材料控制
- 调谐算法与搜索策略

### 运行命令

```bash
python3 /Users/nova/code/fmea-skill/openclaw-fmea-cocreator/scripts/draft_fmea_from_cases.py \
  --module "调谐单元" \
  --input-file /Users/nova/code/fmea-skill/validation/input/调谐单元_input.txt \
  --excel-out /Users/nova/code/fmea-skill/validation/generated/调谐单元_auto_scope_draft.xlsx \
  --markdown-out /Users/nova/code/fmea-skill/validation/generated/调谐单元_auto_scope_draft.md \
  --json-out /Users/nova/code/fmea-skill/validation/generated/调谐单元_auto_scope_draft.json
```

## 自动 scope 结果

这次自动识别出了 3 个 scope：

1. `射频调谐与匹配子系统`
2. `机械传动与限位子系统`
3. `EMC与算法控制子系统`

这个拆分整体是成立的，说明自动 scope 已经不只是“二分法”，也能处理更典型的复杂 DFMEA 模块。

## 初次试跑发现的问题

第一次试跑时，`射频调谐与匹配子系统` 虽然已经有足够多的本模块案例，但草稿里仍混入了：

- `前置放大器`
- `收发机`
- `变温系统`

这些条目不是完全无价值，但在当前模块样例已足够时，会明显稀释首版草稿的边界感。

## 这轮新增修正

基于这次验证，已经把一条更硬的规则补进脚本：

1. 对每个 scope 单独判断
2. 如果当前模块家族在该 scope 下已经有足够案例
3. 就优先只保留当前模块家族
4. 只有当当前模块家族在该 scope 下样例不足时，才允许更广泛的跨模块类比进入

修正后，`射频调谐与匹配子系统` 和 `机械传动与限位子系统` 已经基本只保留 `调谐单元` 自身案例。

## 验证产物

- `/Users/nova/code/fmea-skill/validation/generated/调谐单元_auto_scope_draft.xlsx`
- `/Users/nova/code/fmea-skill/validation/generated/调谐单元_auto_scope_draft.md`
- `/Users/nova/code/fmea-skill/validation/generated/调谐单元_auto_scope_draft.json`

## 当前结果评价

### 已证明有效的部分

- 自动 scope 能稳定拆出 3 个子系统
- 当本模块家族样例充足时，草稿可以明显收敛到当前模块边界
- `调谐单元` 的核心 DFMEA 风险已经能被较完整地召回出来
- 当 `EMC与算法控制子系统` 自身案例不足时，脚本会保留少量跨模块类比作为补充

### 当前仍需人工把关的点

1. `硬件系统 (抗电磁干扰)` 当前被分配到了 `机械传动与限位子系统`
   - 这是因为该条目同时命中了 `电机`、`编码器`、`MCU` 三类关键词
   - 从失效机理看，它也可以被理解为 `EMC与算法控制子系统` 的边界案例
   - 正式版建议人工复核归属

2. `EMC与算法控制子系统` 仍保留了少量跨模块类比
   - 例如 `变温系统` 的通信失联保护
   - `匀场单元` 的通信挂死与参数固化
   - 这些类比在当前阶段是有帮助的，但不应直接等价视为 `调谐单元` 的最终正式条目

3. `O/D` 仍需专家确认
   - 尤其是打火、EMC 干扰、误锁定假陷波、机械限位失效等项
   - 这些风险强依赖真实高功测试、EMC 测试和机械验证手段

## 对 skill 的直接结论

这轮验证让 skill 的“检索边界控制”更成熟了：

1. 自动 `scope` 已经通过第 3 个真实模块验证
2. 草稿生成不能只靠全局 `top-k`，还要按 scope 做“模块家族优先”
3. 跨模块类比应该是补位策略，而不是默认主来源
4. 对边界条目，skill 最好明确告诉用户“建议复核 scope 归属”

## 下一步建议

下一步最合适的是下面两个方向之一：

1. 做第四个真实模块验证，例如 `收发机`
2. 继续增强 `draft_fmea_from_cases.py`，让它对“边界条目”的 scope 归属给出显式提示
