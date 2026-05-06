# Scoring Guardrails

Use these rules whenever assigning or reviewing `S`, `O`, and `D`.

The generated workbook must include `评分准则参考` copied from the standard workbook template without structural or content rewrites.
Use the guidance below to explain row-level S/O/D rationale in the FMEA table, not to replace the template sheet.

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

Suggested draft anchors:

| S | Anchor |
| ---: | --- |
| 10 | Safety/regulatory red-line failure with no warning |
| 9 | Safety or severe equipment damage risk with warning |
| 8 | Complete loss of core function or mission-critical task |
| 7 | Severe degradation of a main function or customer task interruption |
| 6 | Loss of a secondary function or constrained degraded operation |
| 5 | Noticeable performance loss or repeated adjustment/rework |
| 4 | Minor performance fluctuation with limited customer impact |
| 3 | Recoverable warning/log-level issue with little task impact |
| 2 | Internal-only minor deviation |
| 1 | No recognizable customer/task/process impact |

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

Suggested draft anchors:

| O | Anchor |
| ---: | --- |
| 10 | No prevention control; no experience; likely to happen |
| 9 | Mostly behavior-based prevention; very weak effect |
| 8 | Early prevention exists but unstable or unvalidated |
| 7 | Partial prevention; standards/practices do not fully fit this use |
| 6 | Technical prevention exists but boundary/long-term evidence is thin |
| 5 | Basic validation and lessons learned exist; long-term consistency unknown |
| 4 | Similar design has short-term validation; residual boundary risk |
| 3 | Mature design and strong validation history |
| 2 | Long-term field/production evidence supports very low likelihood |
| 1 | Design elimination or poka-yoke makes the cause nearly impossible |

## Detection

`D` is also enterprise-specific.

Base it on actual controls such as:

- test coverage
- alarms and interlocks
- inspection method
- screening strength
- whether the control is preventive, detective, or only after-the-fact

If the control is vague like `样机测试` or `人工目检`, say that detection confidence is limited.

Suggested draft anchors:

| D | Anchor |
| ---: | --- |
| 10 | No known detection control |
| 9 | Very unlikely to detect the cause/mode |
| 8 | Low detection probability; mostly visual or experience-based |
| 7 | Some checks exist but coverage is incomplete |
| 6 | Partial detection, often offline/sample/periodic |
| 5 | Fairly reliable but after-the-fact or late-stage detection |
| 4 | Reliable and near-real-time detection/alarm |
| 3 | Highly reliable real-time detection with automatic mitigation |
| 2 | Redundant detection or cross-checking makes escape unlikely |
| 1 | Error-proofing/design elimination prevents escape |

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
