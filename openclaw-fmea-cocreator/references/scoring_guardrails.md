# Scoring Guardrails

Use these rules whenever assigning or reviewing `S`, `O`, and `D`.

## Core principle

The current project materials explicitly show that `O` and `D` depend heavily on real enterprise capability.

Therefore:

- do not present low-confidence `O` or `D` as authoritative
- prefer `AI draft, needs confirmation` when data is thin
- explain the basis of each score in plain language

## Severity

`S` is often the easiest for AI to draft because it depends on impact.

You may estimate `S` from:

- customer safety or property risk
- core functionality loss
- downstream debugging, rework, scrap, or process interruption
- regulatory or major reliability consequence

## Occurrence

`O` should be treated cautiously.

Only assign with confidence when grounded by:

- historical incidents
- process capability
- supplier quality history
- validation or test escape data
- repeated examples in similar modules

If those are missing:

- draft a tentative value
- say why it is uncertain
- invite expert calibration

## Detection

`D` is also enterprise-specific.

Base it on actual controls such as:

- test coverage
- alarms and interlocks
- inspection method
- screening strength
- whether the control is preventive, detective, or only after-the-fact

If the control is vague like `样机测试` or `人工目检`, say that detection confidence is limited.

## Good phrasing

Use language like:

- `S=8 draft: the effect reaches core function loss and likely causes customer-visible failure.`
- `O=5 draft, needs confirmation: the cause is plausible but no process escape data was provided.`
- `D=6 draft: current control is mainly sample testing, so escape probability may still be meaningful.`

## Bad phrasing

Avoid:

- `O=3 because it feels uncommon`
- `D=2 because there is some test`
- `The ratings are accurate`

## Review behavior

When reviewing an existing table:

- challenge scores that contradict the stated controls
- challenge low `D` if controls are only manual or late-stage
- challenge low `O` if the cause is supplier variation, fatigue, contamination, or EMI without robust controls
- highlight rows where action changes `O` or `D` but no mechanism for improvement is described
