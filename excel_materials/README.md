# Excel 资料整理索引

本目录是基于原始 Excel 自动生成的资料整理结果，目标是为后续的 OpenClaw/FMEA 开发工作提供稳定输入。

## 原始文件保留说明

- 根目录下的原始 Excel 文件保留不动，没有删除、改名或覆盖。
- 原始文件 1: `/Users/nova/code/fmea-skill/CAN400产品DFMEA.xlsx`
- 原始文件 2: `/Users/nova/code/fmea-skill/AI质量赋能.xlsx`

## 目录结构

- `workbooks/`: 按工作簿拆分的逐表导出结果。
- `theme_index.md`: 按主题分类的索引。

## 工作簿索引

| 工作簿 | 类型 | 说明 | 总览文件 |
| --- | --- | --- | --- |
| CAN400产品DFMEA | DFMEA 样例库 | NMR/CAN400 相关模块的 DFMEA 成品表和项目推进信息。 | workbooks/CAN400产品DFMEA/workbook_overview.md |
| AI质量赋能 | AI-FMEA 方法与规划库 | AI 赋能质量工作的总体思路、AI-FMEA 平台设计、计划推进与案例模板。 | workbooks/AI质量赋能/workbook_overview.md |

## 主题分类索引

| 分类 | 说明 | 工作表数量 |
| --- | --- | ---: |
| 项目计划与推进 | 模块负责人、时间计划、试点推进和进度跟踪资料。 | 5 |
| DFMEA 成品样例 | 已经形成的 DFMEA 表格，可直接作为案例库、字段模板和输出样板。 | 9 |
| 质量管理与 AI 赋能策略 | 质量管理环节、AI 赋能点、整体目标与实施背景。 | 2 |
| AI-FMEA 方法与平台设计 | 流程设计、平台蓝图、输入要求、功能规划与实施方式。 | 3 |
| 提示语与分析模板 | AFMEA/SFMEA/DFMEA 提示语模板、失效分类和提问框架。 | 1 |
| 案例库与知识沉淀模板 | 适合转成知识库、案例库和标准化输入输出结构的模板资料。 | 1 |

## 建议使用方式

1. 先看 `workbooks/*/workbook_overview.md` 确认每个工作簿和工作表的作用。
2. 需要完整信息时，优先查看对应 sheet 的 Markdown 和 CSV。
3. 做程序开发、索引构建或知识库导入时，优先消费 JSON 与 CSV。
