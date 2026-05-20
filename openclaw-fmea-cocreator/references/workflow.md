# Workflow

This skill should behave like a collaborative FMEA facilitator, not just a table generator.

## Default flow

1. Identify whether the task is `AFMEA`, `SFMEA`, or `DFMEA`.
2. Decide whether the material should be treated as one scope or split into multiple scopes.
3. Extract or request the minimum inputs needed to build a first draft.
4. Diagnose input quality and record missing context before drafting.
5. Normalize module names and retrieve similar historical cases.
6. For broad or OpenClaw-ready work, run a multi-specialist FMEA cluster.
7. Draft and consolidate a normalized FMEA table.
8. Mark uncertain ratings and assumptions.
9. Review lifecycle/interface/component coverage for likely gaps.
10. Convert important uncertainty into non-expert validation questions.
11. Produce a review-oriented follow-up section.
12. If the user confirms rows, suggest which ones should be added to the case library.

For OpenClaw delivery, use the reference workbook shape as the standard output format.
Use the bundled `template.xlsx` as the standard output template; it must remain content-clean, with sample-specific document content removed.
Package the result as:

1. scope split summary
2. input quality diagnosis
3. coverage matrix review
4. per-scope FMEA draft worksheets
5. confirmation queue
6. top-risk digest
7. action list
8. source trace

The preferred artifact is one Excel workbook with the standard sheets `封面`, `FMEA主表`, and `评分准则参考`.
`FMEA主表` keeps headers in `B2:W2` and generated data from row `3`.
Markdown can still be used as a review preview, and JSON can still be used as a structured interface payload.

Input quality diagnosis rules:

- classify every raw-input draft as `strong`, `usable_with_assumptions`, or `high_risk_missing_context`
- treat the diagnosis as a confidence signal, not as a blocker; draft-first still applies when the user needs a starting point
- check for module/object, function, scenario/lifecycle, environment, interfaces, BOM/key parts, current controls/tests, historical issues, customer/downstream impact, and scoring evidence
- convert missing high-value inputs into specific validation questions rather than generic requests for more material
- route missing context that could change scope, `O/D`, controls, or action priority into the confirmation queue

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

## Multi-specialist cluster rule

FMEA should be treated as a cross-functional review, not a single-perspective generation task.

Use a multi-specialist agent cluster when:

- the user asks for an OpenClaw-ready workbook or detailed draft
- the module spans more than one discipline, lifecycle stage, subsystem, or interface
- safety, reliability, field service, customer operation, logistics, or software/control risks materially affect the result
- the input is sparse but a first draft still needs broad coverage

If native subagents are available, assign bounded lanes to relevant specialist agents.
If they are not available, run the same specialist passes sequentially and keep the viewpoint labels in the synthesis.

Recommended lanes:

| Lane | Specialist perspective | Must inspect / emphasize |
| --- | --- | --- |
| A | System / architecture | boundaries, interfaces, transfer chains, integration assumptions |
| B | Design / module | function decomposition, design constraints, tolerances, component causes |
| C | Reliability / test | validation coverage, lifetime assumptions, O/D evidence, test escapes |
| D | Manufacturing / quality | process variation, supplier quality, inspection and prevention controls |
| E | Safety / compliance | hazards, misuse, protection layers, high-severity rows |
| F | Field service / maintenance | installation, calibration, wear, maintainability, diagnostics |
| G | Customer / application | real workflows, misuse, acceptance criteria, task interruption |
| H | Supply chain / logistics | packaging, storage, transport, incoming quality |
| I | Software / controls | state logic, alarms, interlocks, configuration, data/control failures |

Each specialist output must use the normalized row shape:

- scope / lifecycle or subsystem grouping
- analysis object
- function or requirement
- failure mode
- effect
- S with rationale
- cause
- O with rationale
- current prevention and detection controls
- D with rationale
- recommended action
- owner placeholder
- target-date placeholder
- reference type and source trace
- assumptions and confirmation needs

Consolidation rules:

- merge duplicate rows only when the failure mode, cause, and effect are truly the same
- keep separate rows when the same failure mode has different causes or different controls
- do not average specialist scores silently; preserve score disagreements in `AI打分推导依据`
- route disputed scope, score, ownership, or evidence basis into `Rows needing confirmation`
- keep safety/compliance high-S concerns visible even if RPN is lower than other rows
- after consolidation, rank top risks and list which professional role should confirm each uncertain row

## Coverage matrix review

Run coverage review after the draft is consolidated and before final delivery. The matrix is a review aid, not a correctness guarantee.

Expected dimensions by type:

| FMEA type | Coverage dimensions |
| --- | --- |
| `AFMEA` | storage, transport, installation, operation, abnormal use, maintenance, movement, disposal |
| `SFMEA` | system decomposition, subsystem functions, structural/signal/energy/material interfaces, boundary ownership |
| `DFMEA` | component/function/cause/control coverage, design constraints, materials/tolerances, supplier/manufacturing, validation and detection controls |

Coverage behavior:

- mark a dimension `covered` when rows and source trace provide direct support
- mark it `weak` when rows exist but rely on broad analogy, missing controls, or low evidence
- mark it `missing` when no meaningful row or source supports it
- turn `weak` and `missing` dimensions into plain-language confirmation cards when they could affect risk priority
- keep high-severity safety and compliance gaps visible even if RPN is unknown

## Non-expert validation mode

When the reviewer may not have senior FMEA experience, express confirmation items as answerable business or engineering facts:

- ask what the user can observe: past occurrence, existing test, alarm/interlock, interface owner, customer impact, maintenance reality
- include suggested options such as `multiple past issues`, `rare but possible`, `no known history`, `unknown`
- state the AI default assumption and impact if the answer is wrong
- keep the expert reviewer focus in the same item so the card still works for senior reviewers

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

Useful helper:

```bash
python3 scripts/import_existing_fmea_excel.py --input-excel /path/to/existing.xlsx --excel-out /path/to/normalized.xlsx --json-out /path/to/normalized.json
```

Focus on:

- missing failure modes
- weak cause/effect separation
- unrealistic ratings
- vague controls or actions
- opportunities to merge duplicate rows or split overloaded rows

Behavior:

- first normalize the imported workbook into the current OpenClaw schema
- preserve scope sheets when possible
- preserve `确认队列` reasons if the source workbook already contains them
- prepend imported workbook traceability into `Source case`
- then hand the normalized `.json` to review cards and review writeback actions

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
