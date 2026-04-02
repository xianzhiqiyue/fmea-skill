# 射频功放 首版 DFMEA 草稿

- 生成方式: `draft_fmea_from_cases.py`
- 模块: `射频功放`
- FMEA 类型: `DFMEA`
- 输入长度: `83` 字符

## 输入摘要

> 导入已有 FMEA 工作簿: 射频功放_auto_scope_draft_reviewed.xlsx<br><br>模块/分析对象名称:<br>射频功放<br><br>FMEA 类型:<br>DFMEA

## Scope 规划

| Scope | 检索关键词 | 来源 | 命中数 | 说明 |
| --- | --- | --- | ---: | --- |
| 热管理与复位子系统 | 热管理 / 温度 / 风扇 / 热斑 / 复位 / 散热 / Auto-Recovery | auto | 6 | matched keywords: 热管理 / 温度 / 风扇 / 热斑 / 复位 / 散热 |
| 放大与通道切换子系统 | 放大 / 切换 / 热切换 / 继电器 / 功率管 / 增益 / 双通道 | auto | 5 | matched keywords: 放大 / 切换 / 热切换 / 继电器 / 功率管 |
| 异常保护与联锁子系统 | 保护 / 联锁 / 比较器 / 驻波 / 切断 / 反射功率 / 异常检测 | auto | 4 | matched keywords: 保护 / 联锁 / 比较器 / 驻波 |

## 热管理与复位子系统

| Scope | Analysis object | Function or requirement | Failure mode | Failure effect | S | Cause or mechanism | O | Current controls | D | RPN | Recommended actions | Confirmation status | Review comment | Rating basis | Reference type | Source case |
| --- | --- | --- | --- | --- | ---: | --- | ---: | --- | ---: | ---: | --- | --- | --- | --- | --- | --- |
| 热管理与复位子系统 | 热管理系统 | 保障长脉宽下的有效散热，>85℃时保护关断。 | 局部热斑失控，温度传感器未及时感知 | 后工序：老化测试报废率高。 客户：夏天环境温度高时频繁过热死机。 | 7 | 传感器贴装位置距离发热核心（功率管法兰）过远；风扇故障。 | 4 | 整体温度监测。 | 5 | 140 | 热敏电阻需贴紧功率管法兰；已增加风扇转速（RPM）实时监测，转速掉线直接预警。 | draft |  | S=7 继承自历史案例的后果强度；O=4、D=5 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | 射频功放_auto_scope_draft_reviewed.xlsx / 01-热管理与复位子系统 / row 2; CAN400产品DFMEA.xlsx / 射频功放 / row 6 |
| 热管理与复位子系统 | 故障复位逻辑 | 保护触发后，待手动复位重新工作。 | 死板的手动复位导致自动化实验完全瘫痪 | 客户：仅因为极其短暂的脉冲毛刺触发了驻波保护，导致长达几天的实验报废。 | 6 | 一刀切的软件锁定逻辑。 功放链路中对输入脉冲进行平稳、去毛刺处理 | 6 | 手动复位。 | 3 | 108 | 引入智能重试机制（Auto-Recovery）：对于轻微且时间极短的故障（如瞬态VSWR尖峰），允许系统在降功率后自动重试3次，失败后再彻底锁死求助人工。 | confirmed | 复位策略与自动恢复归口到热管理与复位责任域。 移动 scope 后补齐责任人和计划节点。 | S=6 继承自历史案例的后果强度；O=6、D=3 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | 射频功放_auto_scope_draft_reviewed.xlsx / 01-热管理与复位子系统 / row 3; CAN400产品DFMEA.xlsx / 射频功放 / row 7 |

## 放大与通道切换子系统

| Scope | Analysis object | Function or requirement | Failure mode | Failure effect | S | Cause or mechanism | O | Current controls | D | RPN | Recommended actions | Confirmation status | Review comment | Rating basis | Reference type | Source case |
| --- | --- | --- | --- | --- | ---: | --- | ---: | --- | ---: | ---: | --- | --- | --- | --- | --- | --- |
| 放大与通道切换子系统 | 双通道射频放大 | 在指定频段提供51±1 dB稳定增益，输出140W/300W线性功率。 | 大动态脉冲下增益压缩或相位失真 | 客户：射频脉冲翻转角不准，NMR信号强度异常，甚至无法激发出信号。 | 8 | 大功率输出时晶体管结温急剧上升，导致跨导变化，引发热记忆效应。 | 5 | 出厂静态标定51dB。 | 5 | 200 | 增加包络反馈或动态偏置控制；使用包络跟踪（Envelope Tracking）技术补偿大功率下的增益压缩。 | draft |  | S=8 继承自历史案例的后果强度；O=5、D=5 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | 射频功放_auto_scope_draft_reviewed.xlsx / 02-放大与通道切换子系统 / row 2; CAN400产品DFMEA.xlsx / 射频功放 / row 3 |
| 放大与通道切换子系统 | 通道切换 (BB与2H复用) | BB通道与2H通道共享功率放大器，通过开关切换。 | 带载热切换（Hot Switching）导致开关拉弧击穿 | 后工序：联调时切换通道烧毁继电器。 客户：射频泄漏，观察核信号被锁场信号污染。 | 7 | 软件时序存在竞争，在还有射频输出时执行了继电器/同轴开关的物理切换动作。 | 4 | 无明确的防误切机制。 | 5 | 140 | 强制冷切换逻辑：软件下发切换指令前，硬件强制拉低BLNK信号屏蔽射频输入，延时几十毫秒后再进行开关切换。 | draft |  | S=7 继承自历史案例的后果强度；O=4、D=5 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | 射频功放_auto_scope_draft_reviewed.xlsx / 02-放大与通道切换子系统 / row 3; CAN400产品DFMEA.xlsx / 射频功放 / row 4 |
| 放大与通道切换子系统 | 射频接收路径 (微弱信号放大) | 接收机提供65dB最大增益，0.5dB精确步进。 | 接收链路非线性失真或提前饱和 |  | 8 | 大信号恢复时间慢；放大器偏置电压温漂；带内强干扰导致LNA阻塞。 | 4 | 静态增益校准测试。 优化链路中的自动增益分配方案，ADC采集端增加算法优化采集前信号的线性度 | 4 | 128 | 增强动态范围：接收机前端增加极速限幅器（Limiter）-尝试过会引入额外的噪声；选用高P1dB和IP3的低噪声放大器（LNA）-已实施。 | confirmed | 评审确认该条失效模式对当前模块仍有参考价值，保留为家族参考。 已补齐并确认评分。 纳入本轮整改闭环。 参考适用性、评分和责任节点均已确认。 | 经射频评审确认：按当前保护链路和出厂测试能力校准 S=8、O=4、D=4。 | direct family reference | 射频功放_auto_scope_draft_reviewed.xlsx / 02-放大与通道切换子系统 / row 4; CAN400产品DFMEA.xlsx / 收发机 / row 4 |
| 放大与通道切换子系统 |  | 保护模式切换（UNWORK vs OBSERVE）。 | 逻辑死锁导致模式切换失败 |  | 8 | CPU受强电磁脉冲干扰死机；程序逻辑分支未覆盖异常态。 | 3 | 默认UNWORK模式。 | 5 | 120 | 增加物理Watchdog复位电路；关键逻辑采用FPGA硬件状态机。 | needs expert confirmation |  | S=8 继承自历史案例的后果强度；O=3、D=5 继承自成品 DFMEA，但仍需结合本企业标尺校准；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | 射频功放_auto_scope_draft_reviewed.xlsx / 02-放大与通道切换子系统 / row 5; CAN400产品DFMEA.xlsx / 前置放大器 / row 6 |
| 放大与通道切换子系统 |  | 提供$\ge$30dB增益，NF$\le$1.2-1.8dB。 | 增益波动或自激振荡 |  | 8 | 工作环境温升导致偏置电流漂移；屏蔽腔隔离度不足。 | 4 | 屏蔽腔设计；金属外壳隔离。链路中对增益进行均衡化设计 | 3 | 96 | 增加板载温度补偿电路；优化腔体电磁屏蔽分区。 | needs expert confirmation |  | S=8 继承自历史案例的后果强度；O=4、D=3 继承自成品 DFMEA，但仍需结合本企业标尺校准；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | 射频功放_auto_scope_draft_reviewed.xlsx / 02-放大与通道切换子系统 / row 6; CAN400产品DFMEA.xlsx / 前置放大器 / row 3 |

## 异常保护与联锁子系统

| Scope | Analysis object | Function or requirement | Failure mode | Failure effect | S | Cause or mechanism | O | Current controls | D | RPN | Recommended actions | Confirmation status | Review comment | Rating basis | Reference type | Source case |
| --- | --- | --- | --- | --- | ---: | --- | ---: | --- | ---: | ---: | --- | --- | --- | --- | --- | --- |
| 异常保护与联锁子系统 | 异常状态保护 (核心逻辑) | 功率/脉宽/驻波超限时，极速切断射频输出，保护功放与探头。 | 保护动作严重滞后（器件已烧毁才触发） | 客户：由于5s的检测周期远大于100ms的脉宽，反射功率瞬间击穿末级功率管或毁坏探头。 | 10 | 依赖软件轮询进行异常检测，5s的周期对于微秒级的射频脉冲而言太慢。 | 6 | 软件轮询检测（周期5s）+ 蜂鸣器告警。 | 8 | 480 | 引入纯硬件级联锁保护（Hard Interlock）：采用高速比较器直接切断射频输入开关或偏置电压，响应时间控制在微秒（$\mu$s）级。5s周期仅用于UI刷新和软件复位逻辑。 | draft |  | S=10 继承自历史案例的后果强度；O=6、D=8 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | 射频功放_auto_scope_draft_reviewed.xlsx / 03-异常保护与联锁子系统 / row 2; CAN400产品DFMEA.xlsx / 射频功放 / row 2 |
| 异常保护与联锁子系统 | VSWR 失配检测 | 精确检测正反向功率，反射>50%或驻波>6关断。 | 宽频段内（5-400MHz）反射功率测量严重失准 | 客户：假报警导致实验频频中断（过保护），或驻波已极大但不报警（漏保护）。 | 9 | 宽带定向耦合器的方向性（Directivity）在低频和高频端衰减严重，无法区分正反向。 | 5 | 驻波比阈值检测。 | 6 | 270 | 已采用分段耦合器或在DSP端对不同频点的耦合度进行频率补偿（Look-up Table）；过滤瞬时尖峰防误报。 | draft |  | S=9 继承自历史案例的后果强度；O=5、D=6 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | 射频功放_auto_scope_draft_reviewed.xlsx / 03-异常保护与联锁子系统 / row 3; CAN400产品DFMEA.xlsx / 射频功放 / row 5 |
| 异常保护与联锁子系统 |  | 发射时隔离高功率(300W+)，保护LNA；接收时快速导通。 | PIN二极管热击穿或响应滞后 |  | 10 | 散热设计不足；RGP信号边沿抖动或时序竞争。 | 3 | 交叉PIN管短路引导地；限幅电路。 选用更高功率余量的PIN管 | 4 | 120 |  | needs expert confirmation |  | S=10 继承自历史案例的后果强度；O=3、D=4 继承自成品 DFMEA，但仍需结合本企业标尺校准；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | 射频功放_auto_scope_draft_reviewed.xlsx / 03-异常保护与联锁子系统 / row 4; CAN400产品DFMEA.xlsx / 前置放大器 / row 2 |

## Top Risks

| Scope | Row key | Failure mode | Current RPN | Why it matters | First action candidate | Reference type |
| --- | --- | --- | ---: | --- | --- | --- |
| 异常保护与联锁子系统 | 异常状态保护 (核心逻辑) / 保护动作严重滞后（器件已烧毁才触发） | 保护动作严重滞后（器件已烧毁才触发） | 480 | 客户：由于5s的检测周期远大于100ms的脉宽，反射功率瞬间击穿末级功率管或毁坏探头。 | 引入纯硬件级联锁保护（Hard Interlock）：采用高速比较器直接切断射频输入开关或偏置电压，响应时间控制在微秒（$\mu$s）级。5s周期仅用于U... | current module |
| 异常保护与联锁子系统 | VSWR 失配检测 / 宽频段内（5-400MHz）反射功率测量严重失准 | 宽频段内（5-400MHz）反射功率测量严重失准 | 270 | 客户：假报警导致实验频频中断（过保护），或驻波已极大但不报警（漏保护）。 | 已采用分段耦合器或在DSP端对不同频点的耦合度进行频率补偿（Look-up Table）；过滤瞬时尖峰防误报。 | current module |
| 放大与通道切换子系统 | 双通道射频放大 / 大动态脉冲下增益压缩或相位失真 | 大动态脉冲下增益压缩或相位失真 | 200 | 客户：射频脉冲翻转角不准，NMR信号强度异常，甚至无法激发出信号。 | 增加包络反馈或动态偏置控制；使用包络跟踪（Envelope Tracking）技术补偿大功率下的增益压缩。 | current module |
| 热管理与复位子系统 | 热管理系统 / 局部热斑失控，温度传感器未及时感知 | 局部热斑失控，温度传感器未及时感知 | 140 | 后工序：老化测试报废率高。 客户：夏天环境温度高时频繁过热死机。 | 热敏电阻需贴紧功率管法兰；已增加风扇转速（RPM）实时监测，转速掉线直接预警。 | current module |
| 放大与通道切换子系统 | 通道切换 (BB与2H复用) / 带载热切换（Hot Switching）导致开关拉弧击穿 | 带载热切换（Hot Switching）导致开关拉弧击穿 | 140 | 后工序：联调时切换通道烧毁继电器。 客户：射频泄漏，观察核信号被锁场信号污染。 | 强制冷切换逻辑：软件下发切换指令前，硬件强制拉低BLNK信号屏蔽射频输入，延时几十毫秒后再进行开关切换。 | current module |
| 放大与通道切换子系统 | 射频接收路径 (微弱信号放大) / 接收链路非线性失真或提前饱和 | 接收链路非线性失真或提前饱和 | 128 |  | 增强动态范围：接收机前端增加极速限幅器（Limiter）-尝试过会引入额外的噪声；选用高P1dB和IP3的低噪声放大器（LNA）-已实施。 | direct family reference |
| 放大与通道切换子系统 | 保护模式切换（UNWORK vs OBSERVE）。 / 逻辑死锁导致模式切换失败 | 逻辑死锁导致模式切换失败 | 120 |  | 增加物理Watchdog复位电路；关键逻辑采用FPGA硬件状态机。 | direct family reference |
| 异常保护与联锁子系统 | 发射时隔离高功率(300W+)，保护LNA；接收时快速导通。 / PIN二极管热击穿或响应滞后 | PIN二极管热击穿或响应滞后 | 120 |  |  | direct family reference |

## Rows Needing Confirmation

| Scope | Row key | Why confirmation is needed | Suggested reviewer focus | Review comment | Reference type | Source case |
| --- | --- | --- | --- | --- | --- | --- |
| 放大与通道切换子系统 | 保护模式切换（UNWORK vs OBSERVE）。 / 逻辑死锁导致模式切换失败 | 该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围；scope 归属存在边界，当前放在本 scope，但也可能属于：异常保护与联锁子系统 | 确认 scope 归属与责任边界；确认该类比是否适用于当前模块机理、接口和责任范围；校准 O/D 与实际保护、测试和筛选能力是否匹配 |  | direct family reference | 射频功放_auto_scope_draft_reviewed.xlsx / 02-放大与通道切换子系统 / row 5; CAN400产品DFMEA.xlsx / 前置放大器 / row 6 |
| 放大与通道切换子系统 | 提供$\ge$30dB增益，NF$\le$1.2-1.8dB。 / 增益波动或自激振荡 | 该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围 | 确认该类比是否适用于当前模块机理、接口和责任范围；校准 O/D 与实际保护、测试和筛选能力是否匹配 |  | direct family reference | 射频功放_auto_scope_draft_reviewed.xlsx / 02-放大与通道切换子系统 / row 6; CAN400产品DFMEA.xlsx / 前置放大器 / row 3 |
| 异常保护与联锁子系统 | 发射时隔离高功率(300W+)，保护LNA；接收时快速导通。 / PIN二极管热击穿或响应滞后 | 该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围；scope 归属存在边界，当前放在本 scope，但也可能属于：热管理与复位子系统 | 确认 scope 归属与责任边界；确认该类比是否适用于当前模块机理、接口和责任范围；校准 O/D 与实际保护、测试和筛选能力是否匹配 |  | direct family reference | 射频功放_auto_scope_draft_reviewed.xlsx / 03-异常保护与联锁子系统 / row 4; CAN400产品DFMEA.xlsx / 前置放大器 / row 2 |

## Suggested Actions

| Scope | Row key | Current RPN | Recommended action | Owner | Target date | Confirmation status | Review comment | Reference type | Source case |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| 异常保护与联锁子系统 | 异常状态保护 (核心逻辑) / 保护动作严重滞后（器件已烧毁才触发） | 480 | 引入纯硬件级联锁保护（Hard Interlock）：采用高速比较器直接切断射频输入开关或偏置电压，响应时间控制在微秒（$\mu$s）级。5s周期仅用于UI刷新和软件复位逻辑。 |  |  | draft |  | current module | 射频功放_auto_scope_draft_reviewed.xlsx / 03-异常保护与联锁子系统 / row 2; CAN400产品DFMEA.xlsx / 射频功放 / row 2 |
| 异常保护与联锁子系统 | VSWR 失配检测 / 宽频段内（5-400MHz）反射功率测量严重失准 | 270 | 已采用分段耦合器或在DSP端对不同频点的耦合度进行频率补偿（Look-up Table）；过滤瞬时尖峰防误报。 |  |  | draft |  | current module | 射频功放_auto_scope_draft_reviewed.xlsx / 03-异常保护与联锁子系统 / row 3; CAN400产品DFMEA.xlsx / 射频功放 / row 5 |
| 放大与通道切换子系统 | 双通道射频放大 / 大动态脉冲下增益压缩或相位失真 | 200 | 增加包络反馈或动态偏置控制；使用包络跟踪（Envelope Tracking）技术补偿大功率下的增益压缩。 |  |  | draft |  | current module | 射频功放_auto_scope_draft_reviewed.xlsx / 02-放大与通道切换子系统 / row 2; CAN400产品DFMEA.xlsx / 射频功放 / row 3 |
| 热管理与复位子系统 | 热管理系统 / 局部热斑失控，温度传感器未及时感知 | 140 | 热敏电阻需贴紧功率管法兰；已增加风扇转速（RPM）实时监测，转速掉线直接预警。 |  |  | draft |  | current module | 射频功放_auto_scope_draft_reviewed.xlsx / 01-热管理与复位子系统 / row 2; CAN400产品DFMEA.xlsx / 射频功放 / row 6 |
| 放大与通道切换子系统 | 通道切换 (BB与2H复用) / 带载热切换（Hot Switching）导致开关拉弧击穿 | 140 | 强制冷切换逻辑：软件下发切换指令前，硬件强制拉低BLNK信号屏蔽射频输入，延时几十毫秒后再进行开关切换。 |  |  | draft |  | current module | 射频功放_auto_scope_draft_reviewed.xlsx / 02-放大与通道切换子系统 / row 3; CAN400产品DFMEA.xlsx / 射频功放 / row 4 |
| 放大与通道切换子系统 | 射频接收路径 (微弱信号放大) / 接收链路非线性失真或提前饱和 | 128 | 增强动态范围：接收机前端增加极速限幅器（Limiter）-尝试过会引入额外的噪声；选用高P1dB和IP3的低噪声放大器（LNA）-已实施。 | 射频硬件负责人 | 2026-04-18 | confirmed | 评审确认该条失效模式对当前模块仍有参考价值，保留为家族参考。 已补齐并确认评分。 纳入本轮整改闭环。 参考适用性、评分和责任节点均已确认。 | direct family reference | 射频功放_auto_scope_draft_reviewed.xlsx / 02-放大与通道切换子系统 / row 4; CAN400产品DFMEA.xlsx / 收发机 / row 4 |
| 放大与通道切换子系统 | 保护模式切换（UNWORK vs OBSERVE）。 / 逻辑死锁导致模式切换失败 | 120 | 增加物理Watchdog复位电路；关键逻辑采用FPGA硬件状态机。 |  |  | needs expert confirmation |  | direct family reference | 射频功放_auto_scope_draft_reviewed.xlsx / 02-放大与通道切换子系统 / row 5; CAN400产品DFMEA.xlsx / 前置放大器 / row 6 |
| 热管理与复位子系统 | 故障复位逻辑 / 死板的手动复位导致自动化实验完全瘫痪 | 108 | 引入智能重试机制（Auto-Recovery）：对于轻微且时间极短的故障（如瞬态VSWR尖峰），允许系统在降功率后自动重试3次，失败后再彻底锁死求助人工。 | 控制逻辑负责人 | 2026-04-22 | confirmed | 复位策略与自动恢复归口到热管理与复位责任域。 移动 scope 后补齐责任人和计划节点。 | current module | 射频功放_auto_scope_draft_reviewed.xlsx / 01-热管理与复位子系统 / row 3; CAN400产品DFMEA.xlsx / 射频功放 / row 7 |
| 放大与通道切换子系统 | 提供$\ge$30dB增益，NF$\le$1.2-1.8dB。 / 增益波动或自激振荡 | 96 | 增加板载温度补偿电路；优化腔体电磁屏蔽分区。 |  |  | needs expert confirmation |  | direct family reference | 射频功放_auto_scope_draft_reviewed.xlsx / 02-放大与通道切换子系统 / row 6; CAN400产品DFMEA.xlsx / 前置放大器 / row 3 |

## Source Trace

| Scope | Row key | Reference type | Source case |
| --- | --- | --- | --- |
| 热管理与复位子系统 | 热管理系统 / 局部热斑失控，温度传感器未及时感知 | current module | 射频功放_auto_scope_draft_reviewed.xlsx / 01-热管理与复位子系统 / row 2; CAN400产品DFMEA.xlsx / 射频功放 / row 6 |
| 热管理与复位子系统 | 故障复位逻辑 / 死板的手动复位导致自动化实验完全瘫痪 | current module | 射频功放_auto_scope_draft_reviewed.xlsx / 01-热管理与复位子系统 / row 3; CAN400产品DFMEA.xlsx / 射频功放 / row 7 |
| 放大与通道切换子系统 | 双通道射频放大 / 大动态脉冲下增益压缩或相位失真 | current module | 射频功放_auto_scope_draft_reviewed.xlsx / 02-放大与通道切换子系统 / row 2; CAN400产品DFMEA.xlsx / 射频功放 / row 3 |
| 放大与通道切换子系统 | 通道切换 (BB与2H复用) / 带载热切换（Hot Switching）导致开关拉弧击穿 | current module | 射频功放_auto_scope_draft_reviewed.xlsx / 02-放大与通道切换子系统 / row 3; CAN400产品DFMEA.xlsx / 射频功放 / row 4 |
| 放大与通道切换子系统 | 射频接收路径 (微弱信号放大) / 接收链路非线性失真或提前饱和 | direct family reference | 射频功放_auto_scope_draft_reviewed.xlsx / 02-放大与通道切换子系统 / row 4; CAN400产品DFMEA.xlsx / 收发机 / row 4 |
| 放大与通道切换子系统 | 保护模式切换（UNWORK vs OBSERVE）。 / 逻辑死锁导致模式切换失败 | direct family reference | 射频功放_auto_scope_draft_reviewed.xlsx / 02-放大与通道切换子系统 / row 5; CAN400产品DFMEA.xlsx / 前置放大器 / row 6 |
| 放大与通道切换子系统 | 提供$\ge$30dB增益，NF$\le$1.2-1.8dB。 / 增益波动或自激振荡 | direct family reference | 射频功放_auto_scope_draft_reviewed.xlsx / 02-放大与通道切换子系统 / row 6; CAN400产品DFMEA.xlsx / 前置放大器 / row 3 |
| 异常保护与联锁子系统 | 异常状态保护 (核心逻辑) / 保护动作严重滞后（器件已烧毁才触发） | current module | 射频功放_auto_scope_draft_reviewed.xlsx / 03-异常保护与联锁子系统 / row 2; CAN400产品DFMEA.xlsx / 射频功放 / row 2 |
| 异常保护与联锁子系统 | VSWR 失配检测 / 宽频段内（5-400MHz）反射功率测量严重失准 | current module | 射频功放_auto_scope_draft_reviewed.xlsx / 03-异常保护与联锁子系统 / row 3; CAN400产品DFMEA.xlsx / 射频功放 / row 5 |
| 异常保护与联锁子系统 | 发射时隔离高功率(300W+)，保护LNA；接收时快速导通。 / PIN二极管热击穿或响应滞后 | direct family reference | 射频功放_auto_scope_draft_reviewed.xlsx / 03-异常保护与联锁子系统 / row 4; CAN400产品DFMEA.xlsx / 前置放大器 / row 2 |
