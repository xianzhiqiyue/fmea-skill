# Workflow

This skill should behave like a collaborative FMEA facilitator, not just a table generator.

## Default flow

1. Identify whether the task is `AFMEA`, `SFMEA`, or `DFMEA`.
2. Decide whether the material should be treated as one scope or split into multiple scopes.
3. Extract or request the minimum inputs needed to build a first draft.
4. Normalize module names and retrieve similar historical cases.
5. Draft a normalized FMEA table.
6. Mark uncertain ratings and assumptions.
7. Produce a review-oriented follow-up section.
8. If the user confirms rows, suggest which ones should be added to the case library.

For OpenClaw delivery, package the result as:

1. scope split summary
2. per-scope FMEA draft worksheets
3. confirmation queue
4. top-risk digest
5. action list
6. source trace

The preferred artifact is one Excel workbook. Markdown can still be used as a review preview, and JSON can still be used as a structured interface payload.

Retrieval and grouping rules:

- prioritize the current module first
- allow directly related modules when they share the same transfer chain, interface, or mechanism
- demote unrelated modules when a query contains generic words like `供电`, `接口`, or `传感器`
- if one case could fit multiple scopes, assign it to the best-fitting scope instead of duplicating it everywhere
- if a given scope already has enough cases from the current module family, suppress unrelated-module analogies for that scope
- only widen to broader analogies when the current module family is too sparse to draft a useful first pass
- when a case comes from outside the current module family, require a stronger match in the row's analysis object, function, or failure mode before keeping it
- for tightly coupled technical families, define direct relatives explicitly instead of relying on keyword coincidence alone
- classify every reused row as `current module`, `direct family reference`, or `broader analogy`
- treat direct family rows as gap-filling support, not the default backbone, when the current module already has a stable risk skeleton

## Scope split rule

Split the analysis before drafting when the input mixes:

- different physical architectures
- different major operating modes with distinct failure logic
- different subsystem boundaries that should own different controls
- different lifecycle stages that really belong to AFMEA vs DFMEA

Examples:

- one module description mixes compression refrigeration and liquid-nitrogen evaporation
- one file mixes cabinet structural risks and RF electronic risks

If you split the scope:

- explain the split briefly
- keep the parent module name visible
- generate either separate tables or clearly separated sections
- flag any boundary row that could reasonably belong to more than one scope

## Branches

### New draft from raw description

Use when the user provides a module description, work principle, BOM summary, use environment, or design goals.

Useful helper:

```bash
python3 scripts/draft_fmea_from_cases.py --module "模块名" --input-file /path/to/input.txt
```

Behavior:

- if `--scope` is omitted, the script first tries module-specific auto-scope suggestions
- if no strong profile matches, it falls back to one overall scope
- if the auto-scope split is not good enough, rerun with manual `--scope`
- retrieval should prefer the current module family, then direct siblings, then broader analogies
- draft rows should stay in the most relevant scope when possible

Expected result:

- a first FMEA draft
- explicit assumptions
- a list of missing inputs that would improve quality
- a clear distinction between primary rows and analogy-supported rows

### Review of an existing FMEA

Use when the user already has a table or sheet and wants help improving it.

Focus on:

- missing failure modes
- weak cause/effect separation
- unrealistic ratings
- vague controls or actions
- opportunities to merge duplicate rows or split overloaded rows

### High-risk action review

Use when the table already exists and the user mainly wants prioritization.

Focus on:

- top RPN rows
- actions with strongest RPN reduction
- actions that convert weak detection into prevention

### Case-library extraction

Use when a row or incident has already been validated by experts.

Focus on converting it into:

- normalized function
- failure mode category
- effect
- root cause
- current control

## Source mapping

- historical DFMEA examples: `excel_materials/workbooks/CAN400产品DFMEA/`
- prompt and planning materials: `excel_materials/workbooks/AI质量赋能/`
- project-wide source index: `excel_materials/theme_index.md`

## Collaboration rules

- keep the user in the loop for low-confidence ratings
- prefer draft-first, refine-second
- do not force a perfect input package before helping
- always separate `AI suggestion` from `confirmed by user or source`
- when ownership, scope, or rating basis is ambiguous, route the row into the confirmation queue instead of hiding the ambiguity
