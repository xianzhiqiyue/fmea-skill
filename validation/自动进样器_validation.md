# 自动进样器第二轮验证

## 目的

使用第二个真实模块 `自动进样器` 验证 `openclaw-fmea-cocreator` 的两项能力：

1. 自动 `scope` 是否能泛化到新的机电一体化模块
2. 案例检索是否会被泛化关键词带偏

这轮验证也用于检验新增脚本 `draft_fmea_from_cases.py` 在真实模块上的稳定性。

## 验证对象

- 模块名称：`自动进样器`
- FMEA 类型：`DFMEA`
- 验证重点：`运动/抓取` 与 `检测/气路` 两类风险是否能自然拆分

## 输入来源

### 输入样板

输入文件：

- `/Users/nova/code/fmea-skill/validation/input/自动进样器_input.txt`

输入内容不是直接照抄失效模式，而是基于以下资料整理出的“模块组成 + 功能要求”：

- `/Users/nova/code/fmea-skill/excel_materials/workbooks/CAN400产品DFMEA/sheets/04_自动进样器.md`
- `/Users/nova/code/fmea-skill/excel_materials/workbooks/AI质量赋能/sheets/07_NMR-FMEA计划与实施.md`

输入里保留了这些关键信息：

- 整体连接与供电
- 竖直/水平气缸运动机构
- 位置调节与固定结构
- 储样筒防掉落机构
- 夹爪抓取模块
- 转盘检测模块
- 进样/退样气路控制

### 运行命令

```bash
python3 /Users/nova/code/fmea-skill/openclaw-fmea-cocreator/scripts/draft_fmea_from_cases.py \
  --module "自动进样器" \
  --input-file /Users/nova/code/fmea-skill/validation/input/自动进样器_input.txt \
  --excel-out /Users/nova/code/fmea-skill/validation/generated/自动进样器_auto_scope_draft.xlsx \
  --markdown-out /Users/nova/code/fmea-skill/validation/generated/自动进样器_auto_scope_draft.md \
  --json-out /Users/nova/code/fmea-skill/validation/generated/自动进样器_auto_scope_draft.json
```

## 自动 scope 结果

本轮自动识别出了两个 scope：

1. `运动与抓取子系统`
2. `检测与气路控制子系统`

这次拆分是合理的，因为自动进样器虽然是单一模块名，但内部确实混合了两类控制逻辑：

- 一类是气缸、滑块、夹爪、储样筒、进样筒之间的运动与交接风险
- 一类是供电、传感器、光电检测、气路调压和抬升缓冲风险

## 验证产物

- `/Users/nova/code/fmea-skill/validation/generated/自动进样器_auto_scope_draft.xlsx`
- `/Users/nova/code/fmea-skill/validation/generated/自动进样器_auto_scope_draft.md`
- `/Users/nova/code/fmea-skill/validation/generated/自动进样器_auto_scope_draft.json`

## 这轮验证发现的问题

第一次试跑时，自动 `scope` 虽然是对的，但检索被 `供电`、`接口`、`传感器` 这类泛化关键词干扰，混进了：

- `电子学机柜`
- `前置放大器`

这说明仅靠关键词命中还不够，需要加入“模块家族优先级”。

## 这轮验证后的修正

基于这次结果，已经补了两条规则到脚本里：

1. 案例检索优先当前模块及直接相关模块
   - `自动进样器` 会优先命中本模块
   - 同时允许召回直接相关的 `进样筒`
   - 其他无关模块会被降权，而不是与本模块同权参与竞争

2. 同一条案例优先归到最匹配的 `scope`
   - 通过 `analysis_object + function + failure_mode` 的焦点命中做归属判断
   - 减少同一行案例同时出现在多个 scope 下的情况

修正后，生成结果已经不再混入 `电子学机柜` 和 `前置放大器` 的噪音行。

## 当前结果评价

### 已证明有效的部分

- 自动 `scope` 能在第二个真实模块上泛化，不只适用于 `变温系统`
- 首版草稿能自然形成“运动抓取”和“检测气路”两块
- 检索在加入模块家族优先级后明显更稳定
- `自动进样器` 与 `进样筒` 的跨模块借鉴是合理的，说明“相关模块召回”是有价值的

### 仍然存在的边界

1. `进样筒` 中部分案例是续行式补充
   - 有些行只有原因或措施片段
   - 因此在首版草稿里会出现 `S/O/D` 不完整的低置信度条目

2. `O/D` 仍不能自动拍板
   - 尤其是气压波动、光电误判、卡阻、飞管风险
   - 这些都高度依赖现场验证、气源质量和检测手段

3. 个别边界条目仍需要人工决定归属
   - 例如 `转盘检测模块`
   - 它既涉及机构位置，也涉及检测判断
   - 目前脚本已能更合理地归入检测侧，但正式版仍建议人工复核

## 对 skill 的直接结论

这轮验证让 skill 的设计更清楚了：

1. `scope` 自动拆分可以继续保留，并且已经具备初步泛化能力
2. 案例召回不能只看关键词，必须叠加模块家族权重
3. 自动进样器这类模块天然适合“本模块 + 相关模块”的组合召回
4. 对续行和残缺案例，skill 需要明确输出“低置信度草稿”而不是硬补满评分

## 下一步建议

最值得继续推进的是下面两个方向之一：

1. 做第三个真实模块验证，例如 `调谐单元` 或 `收发机`
2. 继续改进 `draft_fmea_from_cases.py`，让它对续行式样例做更强的片段合并
