# M3 验收记录

- 日期: 2026-05-20
- 验收人: Claude (subagent-driven dev)
- 验收场景: `01_rf_power_amp` (射频功放 DFMEA)

## 单元测试

- 17 项 M3 相关测试 + 23 项 M1/M2 测试 = 40 PASS, 1 SKIP
- 详见 `python3 -m pytest tests/ -v`
- 关键覆盖:
  - apply_openclaw_review_actions: 7 项 (5 action × confirm/edit/reject/defer/promote, idempotency, last-write-wins)
  - confirmed_to_case_library: 7 项 (writeback 阈值表 5 行 + 季度路由 + 幂等 + case_id 格式)
  - retrieve_cases case_library: 2 项 (命中存在 + 1.5x 加权正确)
  - test_review_loop_integration: 1 项 (端到端 apply → writeback → retrieve,断言 case_library 命中且占据 top-1)

## 端到端 5 动作验证

| action | row_id | review_status | 写回 case_library |
|---|---|---|---|
| confirm | T.1.2/pa_transistor_vswr_damage | confirmed | 是 (evidence-backed) |
| edit | T.1.2/pa_transistor_thermal_runaway | edited | 否 |
| reject | T.4.2/gate_bias_voltage_drift | rejected | 否 |
| defer | T.2.1/heatsink_coating_degradation | deferred | 否 |
| promote_to_case | T.1.1/driver_gain_insufficient | promoted | 是 (promote_to_case) |

回流文件 `case_library/射频功放/2026-Q2.json`: 2 条 (期望 ≥2 ✓)
- CASE-2026-Q2-0001 (provenance.promotion_action = promote_to_case)
- CASE-2026-Q2-0002 (provenance.promotion_action = confirm)

edit 行的 RPN 重算: 240 → 240 (occurrence patch=4, 原始 occurrence 已为 4，RPN=10×4×6=240 不变)

## 回声室检查

- `T.1.2/pa_transistor_thermal_runaway` edited 状态: 未回流 ✓
- `T.4.2/gate_bias_voltage_drift` rejected 状态: 未回流 ✓
- `T.2.1/heatsink_coating_degradation` deferred 状态: 未回流 ✓
- 仅 confirmed + 高 evidence 与 promoted 写入,符合 echo-chamber 防护规则。

## 第二轮 retrieve 证明 case_library 生效

查询: `功放管 反射 VSWR 损毁` (匹配 promoted 行 T.1.2)
- matches 总数: 10
- `source_kind == "case_library"` 数量: 2
- 最高分匹配 source_kind: case_library (score=34.5, weight=1.5)
- case_library 命中均带 `weight == 1.5` ✓

## 结论

**通过**。M3 落地达到目标:
- 评审动作 5 种均成功应用且幂等
- 写回闭环按"evidence_grade 阈值 + promote_to_case 例外"工作,无 echo chamber 风险
- 下一轮检索按 1.5x 加权倾向本企业已确认案例,飞轮成立

## 下一步

M3 后续可观察:
1. mock_10 剩余 9 个场景跑 `run_m2.sh` 后启用 `test_row_counts_are_not_all_equal` 完整断言
2. 真实评审反馈可校准 1.5x 权重 (在 `evidence_grading.md` 中已说明可调原因)
