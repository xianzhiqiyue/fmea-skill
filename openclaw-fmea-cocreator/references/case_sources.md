# Case Sources

Use these sources when grounding a draft in historical material.

## Main source directories

- `excel_materials/workbooks/CAN400产品DFMEA/`
- `excel_materials/workbooks/AI质量赋能/`

## Best sheets for historical DFMEA examples

These are the strongest first-pass case sources:

- `变温系统`
- `调谐单元`
- `自动进样器`
- `收发机`
- `前置放大器`
- `射频功放`
- `进样筒`
- `匀场单元`
- `电子学机柜`

These live under:

- `excel_materials/workbooks/CAN400产品DFMEA/sheets/`
- `excel_materials/workbooks/CAN400产品DFMEA/json/`

## Best sheets for method and prompt support

- `AI-FMEA提示语模板`
- `模型规划蓝图`
- `DB600模组-FMEA计划与实施`
- `案例库模板`

These live under:

- `excel_materials/workbooks/AI质量赋能/sheets/`

## Retrieval guidance

Prefer this order:

1. same module or closest alias
2. directly related module in the same transfer chain or interface path
3. same technical mechanism
4. same interface or environment type
5. same failure category

Examples of direct technical families:

- `自动进样器` <-> `进样筒`
- `前置放大器` <-> `收发机` <-> `射频功放`
- `调谐单元` can be a near RF relative of `收发机` when the issue is truly in the front-end RF chain

When the query contains very generic words such as `供电`, `接口`, `传感器`, or `通信`:

- keep the current module as the strongest source
- allow direct sibling modules if they are structurally coupled
- demote unrelated modules to avoid noisy draft rows
- if the current module family already covers a scope well enough, suppress unrelated-module analogies for that scope
- only keep broader analogies when the current module family is too thin to form a usable first draft
- for broader analogies, prefer rows whose analysis object, function, or failure mode strongly matches the current scope

## Traceability

When citing a reused idea, mention at least:

- workbook
- sheet
- if practical, the Excel row or exported row number

## Script

For lightweight retrieval, use:

```bash
python3 scripts/retrieve_cases.py --query "EMC 编码器 丢步 死机"
```

For first-draft table generation from a natural-language description, use:

```bash
python3 scripts/draft_fmea_from_cases.py --module "模块名" --input-file /path/to/input.txt
```

The script is designed to:

- prefer cases from the current module and its direct relatives
- use broader cross-module analogies only as fallback support
- assign each reused case to the best-fitting scope when possible
- keep weak cross-module hits out unless they strongly match the current scope in the row's focal fields

If you want to force your own scope split:

```bash
python3 scripts/draft_fmea_from_cases.py --module "模块名" --input-file /path/to/input.txt --scope "子系统A::关键词1 关键词2" --scope "子系统B::关键词3 关键词4"
```
