# Mock 10 场景 FMEA 生成测试报告

## 测试目标

验证 `openclaw-fmea-cocreator` 在 10 个不同 FMEA 场景下能生成标准模板格式的 Excel、Markdown 和 JSON 产物，并满足字段完整性、工作簿结构、RPN 公式和确认队列输出要求。

## 场景覆盖

| ID | 模块 | 类型 | 关注点 |
| --- | --- | --- | --- |
| 01_rf_power_amp | 射频功放 | DFMEA | 高功率、负载失配、散热、保护 |
| 02_variable_temp | 变温系统 | DFMEA | 压缩机/液氮/温控/结霜/泄漏 |
| 03_autosampler | 自动进样器 | SFMEA | 机械臂、夹爪、扫码、接口和安全门 |
| 04_tuning_unit | 调谐单元 | DFMEA | 可变电容、电机、位置反馈、高压击穿 |
| 05_receiver | 收发机 | SFMEA | 频率合成、门控、接收保护、同步 |
| 06_preamp | 前置放大器 | DFMEA | LNA、T/R保护、过载、静电 |
| 07_gradient_cabinet | 梯度功放柜 | AFMEA | 运输、安装、水冷、安全、维护 |
| 08_cryo_probe | 低温探头 | DFMEA | 真空、低温、冷凝、运输和维护 |
| 09_quality_import | 既有FMEA评审对象 | DFMEA | 供应商FMEA质量、评分偏差、检测逃逸 |
| 10_software_control | 控制软件与联锁 | SFMEA | 状态机、报警、权限、回滚和联锁 |

## 验证项

- 脚本返回码为 0
- 输出 `.xlsx` / `.md` / `.json`
- Excel sheet 名称为 `封面`、`FMEA主表`、`评分准则参考`
- `FMEA主表` 表头保持 `B2:W2`
- Excel 数据行数与 JSON `rows` 数一致
- `O3` 当前 RPN 公式为 `=H3*L3*N3`
- `W3` 改进后 RPN 公式为 `=T3*U3*V3`
- 必填字段无空值：scope、analysis_object、function、failure_mode、effect、S/O/D/RPN、cause、recommended_actions
- 每个场景生成 Top risks 和 confirmation queue

## 结果摘要

详见 `summary.json`。当前 10/10 通过，`problems=[]`。

## 发现并修复的问题

初次测试时 `08_cryo_probe` 暴露缺陷：部分历史案例缺少 S/O/D 时，输出行的评分和 RPN 为空。

已修复：当源案例缺少 S/O/D 时，脚本填入保守 AI 草稿评分 `S/O/D=7/5/5`，计算 RPN，并在 `AI打分推导依据` 和确认队列中明确要求专家确认。
