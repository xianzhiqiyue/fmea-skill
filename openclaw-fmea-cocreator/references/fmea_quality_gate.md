# FMEA Quality Gate

Use this gate before finalizing any AFMEA, SFMEA, DFMEA, or PFMEA draft. The goal is to force the draft to read like an engineering review, not a generic table.

This gate does not require or introduce historical case retrieval. Historical evidence can still improve confidence when available, but the checks below must work from the current input and generated rows alone.

## 1. Type Boundary And Anti-crosstalk

Every row must stay inside the selected FMEA type. If a row crosses boundaries, keep it only when the ownership is explicitly explained and route it to confirmation.

| Type | Primary object | Valid causes | Crosstalk to flag |
| --- | --- | --- | --- |
| `AFMEA` | application scenario, lifecycle step, customer operation, abnormal event | misuse, site operation, installation, maintenance, transport, storage, power/air loss, workflow break | pure BOM, part material, drawing tolerance, process-step workmanship as the primary cause |
| `SFMEA` | system boundary, subsystem interface, function chain, energy/material/information flow, state logic | interface mismatch, timing, ownership gap, integration order, cross-subsystem disturbance | single part material, single process step, operator workmanship as the primary cause |
| `DFMEA` | design item, component, BOM part, material, connector, PCBA, tolerance, derating, thermal/EMC/control interface | design margin, material compatibility, fatigue, drift, short/open circuit, tolerance stack, environmental stress | operator hand method, station sequence, inspection release, packaging process as the primary cause |
| `PFMEA` | process step, station, operator method, tooling/fixture, equipment, inspection, test, packaging, release | missing tooling, wrong sequence, parameter drift, fixture wear, torque/window miss, material mix-up, inspection escape | design margin, material selection, drawing tolerance, derating as the primary cause unless converted into process control escape |

Minimum behavior:

- Do not silently rewrite the row into another FMEA type.
- If the same risk genuinely belongs to two types, split it into two rows with different causes and controls.
- If the ownership is unclear, mark the row as `needs expert confirmation` and add a quality gate finding.

## 2. Engineering And Physics Self-consistency

Each failure line must be physically plausible.

Check these pairs:

- `analysis object -> function`: the object must actually perform or support the stated function.
- `failure mode -> effect`: the effect must follow from the failure mode without a missing intermediate step.
- `cause -> failure mode`: the cause must be a real mechanism in the object's domain.
- `current controls -> detection score`: a weak manual check cannot justify a strong detection score.
- `recommended action -> cause`: the action must reduce occurrence or improve detection for the stated cause.

Domain cues to preserve:

- Mechanical: wear, friction, clearance, stiffness, deformation, looseness, interference, torque.
- Fluid/gas/vacuum: pressure, leakage, flow, sealing, condensation, contamination, venting.
- Electrical/RF/EMC: open/short, drift, noise, grounding, shielding, derating, timing, communication.
- Software/control: state transition, threshold, alarm, interlock, configuration, logging, watchdog.
- Thermal/material: expansion, aging, embrittlement, heat path, compatibility, corrosion.
- Process/manufacturing: station, tooling, fixture, torque, parameter window, inspection, MSA, SPC, release.

Red flags:

- cause text is only "设计不足", "控制不足", "异常", "问题", or similar.
- action only says "优化设计", "加强检查", "加强培训", "图纸审核", "采购认证" without a concrete control.
- effect is severe but no customer, system, safety, downstream, or service consequence is named.
- detection is scored low-risk while the row only has visual check, manual review, or no clear detection method.

## 3. Site Pain And Poka-yoke Actionability

Recommended actions must be usable by engineering, quality, manufacturing, service, or OpenClaw reviewers.

Prefer actions that can enter one of these places:

- BOM, drawing, material lock, derating rule, tolerance stack, design checklist.
- Fixture/tooling, torque tool, sensor, hard interlock, poka-yoke geometry, barcode scan, parameter lock.
- SOP/control plan, first-piece/last-piece check, IQC/OQC/FCT/ICT, MSA, SPC, calibration, maintenance.
- Test plan, failure injection, environmental stress, alarm threshold, log trace, diagnostic coverage.
- Review card with named owner, acceptance evidence, and target closure condition.

Reject or flag actions that are only:

- "加强培训"
- "加强检查"
- "优化设计"
- "提高质量"
- "图纸审核"
- "采购认证"
- "定期检查"
- "规范操作"
- "加强管理"

These phrases are allowed only when paired with a measurable control, for example:

- "使用定扭矩扳手并记录 0.8 N·m 扭矩值"
- "夹具增加不对称定位销，无法反装"
- "扫码绑定物料批次和工位，错料时禁止放行"
- "增加硬线互锁，门未开到位时 Z 轴禁止下探"
- "用 MSA 验证量具能力，GR&R 不满足时禁止使用该治具放行"

## 4. Long-cell Structure

For dense fields such as failure effect, cause, current controls, and recommended actions, prefer multi-level numbered text:

```text
1. customer or downstream impact
2. system or process impact
3. detection/action implication
```

Short cells are acceptable when the row is simple, but overloaded rows must be split or numbered.

## 5. Excel Formatting Gate

Generated workbooks should meet the standard visual contract:

- Header cells: `#333333` fill, white bold text, centered, bordered.
- Serial-number column: centered, light blue `#D9E1F2`, bold.
- Text columns: left aligned, top aligned, wrap text enabled.
- Numeric score columns: `S`, `O`, `D`, `RPN`, post-action `S/O/D/RPN`, and confidence centered.
- Long text in workbook cells should preserve numbered line breaks where possible.

If the renderer cannot apply formatting because an optional dependency is missing, report that limitation instead of claiming workbook formatting was verified.

## 6. Quality Gate Finding Shape

When a row fails or needs confirmation, emit a finding in companion JSON/Markdown:

| Field | Meaning |
| --- | --- |
| `gate` | `type_boundary`, `physics_self_consistency`, `actionability`, `formatting` |
| `status` | `fail`, `review`, or `pass_with_note` |
| `row_key` | stable row label |
| `finding` | what looks wrong or weak |
| `required_fix_or_confirmation` | concrete fix, or the exact expert confirmation needed |
| `reason_tags` | machine-readable tags such as `fmea_type_boundary`, `vague_action`, `weak_physics`, `poka_yoke_missing` |
| `blocking` | whether expert signoff should block final delivery |

The gate is a review aid, not a proof of correctness. It should make weak reasoning visible before the workbook enters OpenClaw review.
