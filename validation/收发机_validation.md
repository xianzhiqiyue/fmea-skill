# 收发机第四轮验证

## 目的

使用第四个真实模块 `收发机` 验证 `openclaw-fmea-cocreator` 在射频链路模块上的表现，重点看三件事：

1. 自动 `scope` 是否能稳定拆出发射、接收采集、频率合成连接三类子系统
2. 当前模块样例充足时，是否仍以本模块为主
3. 跨模块类比是否只保留真正同机制、强匹配的条目

## 验证对象

- 模块名称：`收发机`
- FMEA 类型：`DFMEA`
- 验证重点：发射链路、接收链路、混频合成、ADC 时钟、背板连接

## 输入来源

### 输入样板

输入文件：

- `/Users/nova/code/fmea-skill/validation/input/收发机_input.txt`

输入样板基于以下资料整理：

- `/Users/nova/code/fmea-skill/excel_materials/workbooks/CAN400产品DFMEA/sheets/05_收发机.md`
- `/Users/nova/code/fmea-skill/excel_materials/workbooks/AI质量赋能/sheets/07_NMR-FMEA计划与实施.md`

输入里保留了这些功能边界：

- 射频发射链路
- 射频接收链路
- 混频与频率合成链路
- 数字采集与时钟链路
- 物理连接与接口链路

### 运行命令

```bash
python3 /Users/nova/code/fmea-skill/openclaw-fmea-cocreator/scripts/draft_fmea_from_cases.py \
  --module "收发机" \
  --input-file /Users/nova/code/fmea-skill/validation/input/收发机_input.txt \
  --excel-out /Users/nova/code/fmea-skill/validation/generated/收发机_auto_scope_draft.xlsx \
  --markdown-out /Users/nova/code/fmea-skill/validation/generated/收发机_auto_scope_draft.md \
  --json-out /Users/nova/code/fmea-skill/validation/generated/收发机_auto_scope_draft.json
```

## 自动 scope 结果

本轮自动识别出了 3 个 scope：

1. `发射链路子系统`
2. `接收与采集子系统`
3. `频率合成与连接子系统`

这个拆分是合理的，也和收发机实际的链路边界一致。

## 初次试跑发现的问题

第一次试跑时，虽然整体 scope 是对的，但仍混入了两类弱相关噪音：

- `变温系统` 的振动与传感器条目
- 部分只是因为原因/后果文本里碰巧带了 `噪声`、`ADC` 等泛词才被拉进来的条目

这说明“模块家族优先”还不够，跨模块类比还需要再加一层“焦点字段强匹配”。

## 这轮新增修正

基于这次验证，已经把一条更细的过滤规则补进脚本：

1. 对非当前模块家族的案例
2. 不仅要在整体文本上命中 scope 关键词
3. 还要在 `analysis_object + function + failure_mode` 这些焦点字段里形成足够强的匹配
4. 只有达到这个门槛，才允许作为跨模块类比进入草稿

修正后，`变温系统` 的弱相关噪音已经被清掉，保留下来的跨模块条目主要是：

- `调谐单元` 的高功打火风险
- `射频功放` 的 VSWR / 热切换风险
- `前置放大器` 的 T/R 保护与增益稳定性风险

这些都属于对 `收发机` 有实际参考价值的同机制类比。

## 验证产物

- `/Users/nova/code/fmea-skill/validation/generated/收发机_auto_scope_draft.xlsx`
- `/Users/nova/code/fmea-skill/validation/generated/收发机_auto_scope_draft.md`
- `/Users/nova/code/fmea-skill/validation/generated/收发机_auto_scope_draft.json`

## 当前结果评价

### 已证明有效的部分

- 自动 scope 能稳定拆出 3 条射频链路
- 当前模块样例已经能覆盖主干风险
- 跨模块类比被压缩到了少量高价值条目
- 检索结果已经更像“共创补位”，而不是“关键词乱召回”

### 当前仍需人工把关的点

1. `发射链路子系统` 仍保留了若干跨模块保护类条目
   - 例如 `VSWR 失配检测`
   - 例如 `PIN 二极管热击穿`
   - 这些在工程上很有参考意义，但正式版仍要确认是否属于当前收发机的设计边界

2. `系统电磁抗扰 (EMC)` 目前被归到了发射链路
   - 从机理上它也可以被视为全局电磁兼容风险
   - 正式共创时建议人工确认归属

3. `O/D` 仍需专家确认
   - 尤其是射频泄漏、功率突波、杂散泄漏、时钟抖动、热切换和保护链路失效
   - 这些都依赖真实板级调试、频谱测试和系统联调能力

## 对 skill 的直接结论

这轮验证让 skill 的检索策略又往前走了一步：

1. 现在不仅有“模块家族优先”
2. 还有“跨模块类比必须在焦点字段里强匹配”
3. 这样既能保留有价值类比，也能明显减少弱相关噪音

## 下一步建议

下一步最合适的是下面两个方向之一：

1. 做第五个真实模块验证，例如 `前置放大器`
2. 继续增强 `draft_fmea_from_cases.py`，让它对跨模块类比自动打上“类比参考”标签
