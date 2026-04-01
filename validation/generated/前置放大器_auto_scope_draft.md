# 前置放大器 首版 DFMEA 草稿

- 生成方式: `draft_fmea_from_cases.py`
- 模块: `前置放大器`
- FMEA 类型: `DFMEA`
- 输入长度: `801` 字符

## 输入摘要

> 示例：我们目前正在设计一套用于 NMR 系统的前置放大器模块，它位于探头与后级射频链路之间，需要在发射和接收两种工作状态下完成保护切换、低噪声放大、功率检测和接口控制。该模块既要在大功率发射瞬间保护低噪声器件不被击穿，也要在接收阶段保持较低噪声系数和稳定增益，同时保证控制模式切换和接口信号在复杂电磁环境下仍然可靠。<br><br>前置放大器主要包含以下几个方面：<br><br>1、T/R 开关与高功率保护链路：在发射状态下需要隔离高功率射频，保护 LNA 和后续敏感器件；在接收状态下需要快速导通，避免影响接收灵敏度。要求切换器件、保护链路和时序控制在高功率脉冲、热冲击和快速切换条件下仍然可靠，不出现热击穿、响应滞后、保护失效或误动作。<br><br>2、低噪声放大链路：需要在接收状态下提供稳定增益和较低噪声系数，并在温度变化、屏蔽条件变化和长期运行中保持一致性。要求放大链路不能因为温漂、偏置波动、自激、屏蔽不足或链路不平衡而...

## Scope 规划

| Scope | 检索关键词 | 来源 | 命中数 | 说明 |
| --- | --- | --- | ---: | --- |
| T/R与保护子系统 | T/R / 高功率 / 保护 / 功率检测 / PIN / 限幅 / 联动跳闸 / VSWR / 驻波 / 复位 / 热管理 | auto | 4 | matched keywords: T/R / 高功率 / 保护 / 功率检测 |
| 低噪声放大与接口子系统 | LNA / 增益 / 接口 / 振荡 / N-K / BNC / 回波损耗 | auto | 3 | matched keywords: LNA / 增益 / 接口 |
| 控制逻辑与供电子系统 | 供电 / 串扰 / 模式切换 / UNWORK / OBSERVE / Watchdog / DB-37 | auto | 3 | matched keywords: 供电 / 串扰 / 模式切换 |

## T/R与保护子系统

| Scope | Analysis object | Function or requirement | Failure mode | Failure effect | S | Cause or mechanism | O | Current controls | D | RPN | Recommended actions | Confirmation status | Rating basis | Reference type | Source case |
| --- | --- | --- | --- | --- | ---: | --- | ---: | --- | ---: | ---: | --- | --- | --- | --- | --- |
| T/R与保护子系统 | 异常状态保护 (核心逻辑) | 功率/脉宽/驻波超限时，极速切断射频输出，保护功放与探头。 | 保护动作严重滞后（器件已烧毁才触发） | 客户：由于5s的检测周期远大于100ms的脉宽，反射功率瞬间击穿末级功率管或毁坏探头。 | 10 | 依赖软件轮询进行异常检测，5s的周期对于微秒级的射频脉冲而言太慢。 | 6 | 软件轮询检测（周期5s）+ 蜂鸣器告警。 | 8 | 480 | 引入纯硬件级联锁保护（Hard Interlock）：采用高速比较器直接切断射频输入开关或偏置电压，响应时间控制在微秒（$\mu$s）级。5s周期仅用于UI刷新和软件复位逻辑。 | needs expert confirmation | S=10 继承自历史案例的后果强度；O=6、D=8 继承自成品 DFMEA，但仍需结合本企业标尺校准；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 2 |
| T/R与保护子系统 | VSWR 失配检测 | 精确检测正反向功率，反射>50%或驻波>6关断。 | 宽频段内（5-400MHz）反射功率测量严重失准 | 客户：假报警导致实验频频中断（过保护），或驻波已极大但不报警（漏保护）。 | 9 | 宽带定向耦合器的方向性（Directivity）在低频和高频端衰减严重，无法区分正反向。 | 5 | 驻波比阈值检测。 | 6 | 270 | 已采用分段耦合器或在DSP端对不同频点的耦合度进行频率补偿（Look-up Table）；过滤瞬时尖峰防误报。 | needs expert confirmation | S=9 继承自历史案例的后果强度；O=5、D=6 继承自成品 DFMEA，但仍需结合本企业标尺校准；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 5 |
| T/R与保护子系统 | 热管理系统 | 保障长脉宽下的有效散热，>85℃时保护关断。 | 局部热斑失控，温度传感器未及时感知 | 后工序：老化测试报废率高。 客户：夏天环境温度高时频繁过热死机。 | 7 | 传感器贴装位置距离发热核心（功率管法兰）过远；风扇故障。 | 4 | 整体温度监测。 | 5 | 140 | 热敏电阻需贴紧功率管法兰；已增加风扇转速（RPM）实时监测，转速掉线直接预警。 | needs expert confirmation | S=7 继承自历史案例的后果强度；O=4、D=5 继承自成品 DFMEA，但仍需结合本企业标尺校准；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 6 |
| T/R与保护子系统 |  | 功率超阈值时关闭射频输入并告警。 | 功率检测耦合器失效或响应过慢 |  | 9 | 耦合路径阻抗失配；检波器动态范围受限。 | 3 | 耦合功率监测；手动解除告警。 | 5 | 135 | 引入硬件联动跳闸：告警信号不经过上位机，直接硬件拉低功率门控。 | draft | S=9 继承自历史案例的后果强度；O=3、D=5 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | CAN400产品DFMEA.xlsx / 前置放大器 / row 4 |
| T/R与保护子系统 |  | 发射时隔离高功率(300W+)，保护LNA；接收时快速导通。 | PIN二极管热击穿或响应滞后 |  | 10 | 散热设计不足；RGP信号边沿抖动或时序竞争。 | 3 | 交叉PIN管短路引导地；限幅电路。 选用更高功率余量的PIN管 | 4 | 120 |  | draft | S=10 继承自历史案例的后果强度；O=3、D=4 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | CAN400产品DFMEA.xlsx / 前置放大器 / row 2 |
| T/R与保护子系统 | 故障复位逻辑 | 保护触发后，待手动复位重新工作。 | 死板的手动复位导致自动化实验完全瘫痪 | 客户：仅因为极其短暂的脉冲毛刺触发了驻波保护，导致长达几天的实验报废。 | 6 | 一刀切的软件锁定逻辑。 功放链路中对输入脉冲进行平稳、去毛刺处理 | 6 | 手动复位。 | 3 | 108 | 引入智能重试机制（Auto-Recovery）：对于轻微且时间极短的故障（如瞬态VSWR尖峰），允许系统在降功率后自动重试3次，失败后再彻底锁死求助人工。 | needs expert confirmation | S=6 继承自历史案例的后果强度；O=6、D=3 继承自成品 DFMEA，但仍需结合本企业标尺校准；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 7 |

## 低噪声放大与接口子系统

| Scope | Analysis object | Function or requirement | Failure mode | Failure effect | S | Cause or mechanism | O | Current controls | D | RPN | Recommended actions | Confirmation status | Rating basis | Reference type | Source case |
| --- | --- | --- | --- | --- | ---: | --- | ---: | --- | ---: | ---: | --- | --- | --- | --- | --- |
| 低噪声放大与接口子系统 |  | 射频信号稳定传输，低插入损耗。 | 接口在大功率下产生电弧或击穿 |  | 9 | 同轴线缆中心针位移；接头紧固力矩不一。 | 4 | 手动紧固；柔性电缆连接。 | 6 | 216 | 定期对接口进行电磁回波损耗（Return Loss）测试；使用力矩扳手规定装配标准。 | draft | S=9 继承自历史案例的后果强度；O=4、D=6 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | CAN400产品DFMEA.xlsx / 前置放大器 / row 5 |
| 低噪声放大与接口子系统 | 双通道射频放大 | 在指定频段提供51±1 dB稳定增益，输出140W/300W线性功率。 | 大动态脉冲下增益压缩或相位失真 | 客户：射频脉冲翻转角不准，NMR信号强度异常，甚至无法激发出信号。 | 8 | 大功率输出时晶体管结温急剧上升，导致跨导变化，引发热记忆效应。 | 5 | 出厂静态标定51dB。 | 5 | 200 | 增加包络反馈或动态偏置控制；使用包络跟踪（Envelope Tracking）技术补偿大功率下的增益压缩。 | needs expert confirmation | S=8 继承自历史案例的后果强度；O=5、D=5 继承自成品 DFMEA，但仍需结合本企业标尺校准；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 3 |
| 低噪声放大与接口子系统 | 射频接收路径 (微弱信号放大) | 接收机提供65dB最大增益，0.5dB精确步进。 | 接收链路非线性失真或提前饱和 |  | 8 | 大信号恢复时间慢；放大器偏置电压温漂；带内强干扰导致LNA阻塞。 | 5 | 静态增益校准测试。 优化链路中的自动增益分配方案，ADC采集端增加算法优化采集前信号的线性度 | 4 | 160 | 增强动态范围：接收机前端增加极速限幅器（Limiter）-尝试过会引入额外的噪声；选用高P1dB和IP3的低噪声放大器（LNA）-已实施。 | needs expert confirmation | S=8 继承自历史案例的后果强度；O=5、D=4 继承自成品 DFMEA，但仍需结合本企业标尺校准；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | CAN400产品DFMEA.xlsx / 收发机 / row 4 |
| 低噪声放大与接口子系统 |  | 提供$\ge$30dB增益，NF$\le$1.2-1.8dB。 | 增益波动或自激振荡 |  | 8 | 工作环境温升导致偏置电流漂移；屏蔽腔隔离度不足。 | 4 | 屏蔽腔设计；金属外壳隔离。链路中对增益进行均衡化设计 | 3 | 96 | 增加板载温度补偿电路；优化腔体电磁屏蔽分区。 | draft | S=8 继承自历史案例的后果强度；O=4、D=3 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | CAN400产品DFMEA.xlsx / 前置放大器 / row 3 |

## 控制逻辑与供电子系统

| Scope | Analysis object | Function or requirement | Failure mode | Failure effect | S | Cause or mechanism | O | Current controls | D | RPN | Recommended actions | Confirmation status | Rating basis | Reference type | Source case |
| --- | --- | --- | --- | --- | ---: | --- | ---: | --- | ---: | ---: | --- | --- | --- | --- | --- |
| 控制逻辑与供电子系统 |  | 提供稳定供电及控制信号。 | 多芯线束线间干扰（Crosstalk） |  | 7 | 控制信号与大电流电源线未分层屏蔽。 | 4 | 软件滤波处理。 | 5 | 140 | 线束采用屏蔽电缆；DB-37接口端增加滤波电容阵列。 | draft | S=7 继承自历史案例的后果强度；O=4、D=5 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | CAN400产品DFMEA.xlsx / 前置放大器 / row 7 |
| 控制逻辑与供电子系统 |  | 保护模式切换（UNWORK vs OBSERVE）。 | 逻辑死锁导致模式切换失败 |  | 8 | CPU受强电磁脉冲干扰死机；程序逻辑分支未覆盖异常态。 | 3 | 默认UNWORK模式。 | 5 | 120 | 增加物理Watchdog复位电路；关键逻辑采用FPGA硬件状态机。 | draft | S=8 继承自历史案例的后果强度；O=3、D=5 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | CAN400产品DFMEA.xlsx / 前置放大器 / row 6 |

## Top Risks

| Scope | Failure mode | Current RPN | Why it matters | First action candidate | Reference type |
| --- | --- | ---: | --- | --- | --- |
| T/R与保护子系统 | 保护动作严重滞后（器件已烧毁才触发） | 480 | 客户：由于5s的检测周期远大于100ms的脉宽，反射功率瞬间击穿末级功率管或毁坏探头。 | 引入纯硬件级联锁保护（Hard Interlock）：采用高速比较器直接切断射频输入开关或偏置电压，响应时间控制在微秒（$\mu$s）级。5s周期仅用于U... | direct family reference |
| T/R与保护子系统 | 宽频段内（5-400MHz）反射功率测量严重失准 | 270 | 客户：假报警导致实验频频中断（过保护），或驻波已极大但不报警（漏保护）。 | 已采用分段耦合器或在DSP端对不同频点的耦合度进行频率补偿（Look-up Table）；过滤瞬时尖峰防误报。 | direct family reference |
| 低噪声放大与接口子系统 | 接口在大功率下产生电弧或击穿 | 216 |  | 定期对接口进行电磁回波损耗（Return Loss）测试；使用力矩扳手规定装配标准。 | current module |
| 低噪声放大与接口子系统 | 大动态脉冲下增益压缩或相位失真 | 200 | 客户：射频脉冲翻转角不准，NMR信号强度异常，甚至无法激发出信号。 | 增加包络反馈或动态偏置控制；使用包络跟踪（Envelope Tracking）技术补偿大功率下的增益压缩。 | direct family reference |
| 低噪声放大与接口子系统 | 接收链路非线性失真或提前饱和 | 160 |  | 增强动态范围：接收机前端增加极速限幅器（Limiter）-尝试过会引入额外的噪声；选用高P1dB和IP3的低噪声放大器（LNA）-已实施。 | direct family reference |
| 控制逻辑与供电子系统 | 多芯线束线间干扰（Crosstalk） | 140 |  | 线束采用屏蔽电缆；DB-37接口端增加滤波电容阵列。 | current module |
| T/R与保护子系统 | 局部热斑失控，温度传感器未及时感知 | 140 | 后工序：老化测试报废率高。 客户：夏天环境温度高时频繁过热死机。 | 热敏电阻需贴紧功率管法兰；已增加风扇转速（RPM）实时监测，转速掉线直接预警。 | direct family reference |
| T/R与保护子系统 | 功率检测耦合器失效或响应过慢 | 135 |  | 引入硬件联动跳闸：告警信号不经过上位机，直接硬件拉低功率门控。 | current module |

## Rows Needing Confirmation

| Scope | Row key | Why confirmation is needed | Suggested reviewer focus | Reference type | Source case |
| --- | --- | --- | --- | --- | --- |
| T/R与保护子系统 | 异常状态保护 (核心逻辑) / 保护动作严重滞后（器件已烧毁才触发） | 该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围 | 确认该类比是否适用于当前模块机理、接口和责任范围；校准 O/D 与实际保护、测试和筛选能力是否匹配 | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 2 |
| T/R与保护子系统 | VSWR 失配检测 / 宽频段内（5-400MHz）反射功率测量严重失准 | 该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围 | 确认该类比是否适用于当前模块机理、接口和责任范围；校准 O/D 与实际保护、测试和筛选能力是否匹配 | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 5 |
| T/R与保护子系统 | 热管理系统 / 局部热斑失控，温度传感器未及时感知 | 该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围 | 确认该类比是否适用于当前模块机理、接口和责任范围；校准 O/D 与实际保护、测试和筛选能力是否匹配 | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 6 |
| T/R与保护子系统 | 故障复位逻辑 / 死板的手动复位导致自动化实验完全瘫痪 | 该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围 | 确认该类比是否适用于当前模块机理、接口和责任范围；校准 O/D 与实际保护、测试和筛选能力是否匹配 | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 7 |
| 低噪声放大与接口子系统 | 双通道射频放大 / 大动态脉冲下增益压缩或相位失真 | 该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围 | 确认该类比是否适用于当前模块机理、接口和责任范围；校准 O/D 与实际保护、测试和筛选能力是否匹配 | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 3 |
| 低噪声放大与接口子系统 | 射频接收路径 (微弱信号放大) / 接收链路非线性失真或提前饱和 | 该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围 | 确认该类比是否适用于当前模块机理、接口和责任范围；校准 O/D 与实际保护、测试和筛选能力是否匹配 | direct family reference | CAN400产品DFMEA.xlsx / 收发机 / row 4 |

## Suggested Actions

| Scope | Row key | Current RPN | Recommended action | Owner | Target date | Confirmation status | Reference type | Source case |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| T/R与保护子系统 | 异常状态保护 (核心逻辑) / 保护动作严重滞后（器件已烧毁才触发） | 480 | 引入纯硬件级联锁保护（Hard Interlock）：采用高速比较器直接切断射频输入开关或偏置电压，响应时间控制在微秒（$\mu$s）级。5s周期仅用于UI刷新和软件复位逻辑。 |  |  | needs expert confirmation | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 2 |
| T/R与保护子系统 | VSWR 失配检测 / 宽频段内（5-400MHz）反射功率测量严重失准 | 270 | 已采用分段耦合器或在DSP端对不同频点的耦合度进行频率补偿（Look-up Table）；过滤瞬时尖峰防误报。 |  |  | needs expert confirmation | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 5 |
| 低噪声放大与接口子系统 | 射频信号稳定传输，低插入损耗。 / 接口在大功率下产生电弧或击穿 | 216 | 定期对接口进行电磁回波损耗（Return Loss）测试；使用力矩扳手规定装配标准。 |  |  | draft | current module | CAN400产品DFMEA.xlsx / 前置放大器 / row 5 |
| 低噪声放大与接口子系统 | 双通道射频放大 / 大动态脉冲下增益压缩或相位失真 | 200 | 增加包络反馈或动态偏置控制；使用包络跟踪（Envelope Tracking）技术补偿大功率下的增益压缩。 |  |  | needs expert confirmation | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 3 |
| 低噪声放大与接口子系统 | 射频接收路径 (微弱信号放大) / 接收链路非线性失真或提前饱和 | 160 | 增强动态范围：接收机前端增加极速限幅器（Limiter）-尝试过会引入额外的噪声；选用高P1dB和IP3的低噪声放大器（LNA）-已实施。 |  |  | needs expert confirmation | direct family reference | CAN400产品DFMEA.xlsx / 收发机 / row 4 |
| 控制逻辑与供电子系统 | 提供稳定供电及控制信号。 / 多芯线束线间干扰（Crosstalk） | 140 | 线束采用屏蔽电缆；DB-37接口端增加滤波电容阵列。 |  |  | draft | current module | CAN400产品DFMEA.xlsx / 前置放大器 / row 7 |
| T/R与保护子系统 | 热管理系统 / 局部热斑失控，温度传感器未及时感知 | 140 | 热敏电阻需贴紧功率管法兰；已增加风扇转速（RPM）实时监测，转速掉线直接预警。 |  |  | needs expert confirmation | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 6 |
| T/R与保护子系统 | 功率超阈值时关闭射频输入并告警。 / 功率检测耦合器失效或响应过慢 | 135 | 引入硬件联动跳闸：告警信号不经过上位机，直接硬件拉低功率门控。 |  |  | draft | current module | CAN400产品DFMEA.xlsx / 前置放大器 / row 4 |
| 控制逻辑与供电子系统 | 保护模式切换（UNWORK vs OBSERVE）。 / 逻辑死锁导致模式切换失败 | 120 | 增加物理Watchdog复位电路；关键逻辑采用FPGA硬件状态机。 |  |  | draft | current module | CAN400产品DFMEA.xlsx / 前置放大器 / row 6 |
| T/R与保护子系统 | 故障复位逻辑 / 死板的手动复位导致自动化实验完全瘫痪 | 108 | 引入智能重试机制（Auto-Recovery）：对于轻微且时间极短的故障（如瞬态VSWR尖峰），允许系统在降功率后自动重试3次，失败后再彻底锁死求助人工。 |  |  | needs expert confirmation | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 7 |
| 低噪声放大与接口子系统 | 提供$\ge$30dB增益，NF$\le$1.2-1.8dB。 / 增益波动或自激振荡 | 96 | 增加板载温度补偿电路；优化腔体电磁屏蔽分区。 |  |  | draft | current module | CAN400产品DFMEA.xlsx / 前置放大器 / row 3 |

## Source Trace

| Scope | Row key | Reference type | Source case |
| --- | --- | --- | --- |
| T/R与保护子系统 | 异常状态保护 (核心逻辑) / 保护动作严重滞后（器件已烧毁才触发） | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 2 |
| T/R与保护子系统 | VSWR 失配检测 / 宽频段内（5-400MHz）反射功率测量严重失准 | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 5 |
| T/R与保护子系统 | 热管理系统 / 局部热斑失控，温度传感器未及时感知 | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 6 |
| T/R与保护子系统 | 功率超阈值时关闭射频输入并告警。 / 功率检测耦合器失效或响应过慢 | current module | CAN400产品DFMEA.xlsx / 前置放大器 / row 4 |
| T/R与保护子系统 | 发射时隔离高功率(300W+)，保护LNA；接收时快速导通。 / PIN二极管热击穿或响应滞后 | current module | CAN400产品DFMEA.xlsx / 前置放大器 / row 2 |
| T/R与保护子系统 | 故障复位逻辑 / 死板的手动复位导致自动化实验完全瘫痪 | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 7 |
| 低噪声放大与接口子系统 | 射频信号稳定传输，低插入损耗。 / 接口在大功率下产生电弧或击穿 | current module | CAN400产品DFMEA.xlsx / 前置放大器 / row 5 |
| 低噪声放大与接口子系统 | 双通道射频放大 / 大动态脉冲下增益压缩或相位失真 | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 3 |
| 低噪声放大与接口子系统 | 射频接收路径 (微弱信号放大) / 接收链路非线性失真或提前饱和 | direct family reference | CAN400产品DFMEA.xlsx / 收发机 / row 4 |
| 低噪声放大与接口子系统 | 提供$\ge$30dB增益，NF$\le$1.2-1.8dB。 / 增益波动或自激振荡 | current module | CAN400产品DFMEA.xlsx / 前置放大器 / row 3 |
| 控制逻辑与供电子系统 | 提供稳定供电及控制信号。 / 多芯线束线间干扰（Crosstalk） | current module | CAN400产品DFMEA.xlsx / 前置放大器 / row 7 |
| 控制逻辑与供电子系统 | 保护模式切换（UNWORK vs OBSERVE）。 / 逻辑死锁导致模式切换失败 | current module | CAN400产品DFMEA.xlsx / 前置放大器 / row 6 |
