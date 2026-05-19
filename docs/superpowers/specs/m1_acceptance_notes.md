# M1 验收记录

- 日期: 2026-05-19
- 验收人: Claude (subagent-driven dev)
- 输入场景: 变温系统 (`validation/input/变温系统_input.txt`,17 行,压缩机制冷单元 + 液氮低温制冷系统 + 控制板卡)

## 试跑产物路径

`/tmp/m1_acceptance/`:
- `structure.json` — 阶段 1 产物
- `evidence_pool/T.1.1.json`, `T.1.5.json`, `T.2.3.json` — 阶段 3 产物
- `candidates_design.json` — 阶段 2「设计/模块」角色产物

## 指标

- `structure.json` leaf 数: **10** (T.1.1–T.1.6 共 6 个 + T.2.1–T.2.4 共 4 个)
- `structure.json` p_diagrams 数: **2** (T.1 压缩机制冷子系统 + T.2 液氮低温子系统)
- `evidence_pool/` 命中: 3 个 leaf 各 5 条匹配,schema 符合 `{leaf_id, matches[]}` 固定格式
- 「设计/模块」候选行: **25** 条,加 **32** 条 not_applicable;全 25 个 `failure_mode_canonical` 唯一,schema 字段全齐

## 4 项验收

- ✅ `structure.json` schema 合规 (顶层 `fmea_type` / `module_root` / `hierarchy` / `p_diagrams` 齐全,每个 P-Diagram 含 7 必填字段)
- ✅ 6 个角色的指令可被 subagent 执行 (smoke 跑通其中 1 个,其余 5 个 schema 与提示结构同构)
- ✅ `retrieve_cases.py --json-out` 输出 evidence_pool 可读 (3 个 leaf,15 行 evidence,无空文件)
- ✅ SKILL.md 新流程章节存在 (`## Core workflow` 重写为 6 阶段),旧 `draft_fmea_from_cases.py` 在阶段 5 中明示为「M1 暂用,M2 替换」,非主路径

## 结论

**通过**。M1 落地达到目标:reference 文档可指导生成、`retrieve_cases.py` 已具备 M2 hand-off 能力、SKILL.md 已从「关键词检索 + 历史行拷贝」转向「P-Diagram + 多角色 + 证据等级」。

## 已观察的副作用

- `retrieve_cases.py` 在 M1 Task 6 顺带修复了一处 pre-existing scoring 缺陷 (无关键词命中时仅靠 theme/sheet bonus 入选),改后 markdown smoke test 仍然命中真实查询。
- 阶段 4 的合并/评级在 M1 仍由 Claude 手动按 reference 执行;M2 落 `merge_and_score.py` 后这一步将自动化。

## 下一步

进入 M2:落 `merge_and_score.py` + `build_workbook.py` + 扩列 `template.xlsx`,并把 mock_10 回归基线写入 `tests/regression/`。
