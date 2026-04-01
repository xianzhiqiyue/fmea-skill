# 收发机 首版 DFMEA 草稿

- 生成方式: `draft_fmea_from_cases.py`
- 模块: `收发机`
- FMEA 类型: `DFMEA`
- 输入长度: `816` 字符

## 输入摘要

> 示例：我们目前正在设计一套用于 NMR 系统的收发机模块，需要完成射频信号的发射、接收、上变频、下变频、增益控制、ADC 采集以及与背板和外部射频链路的连接。该模块既要在发射时保证激励脉冲的幅度和时间准确，又要在接收时保证微弱信号的线性放大和低噪声采集，同时还要兼顾频率纯度、时钟稳定性以及长期运行下的连接可靠性。<br><br>收发机主要包含以下几个方面：<br><br>1、射频发射链路：需要对发射脉冲进行精确衰减、调幅和功率控制，使激励信号满足幅度、相位和时间要求。要求在高衰减状态、快速切换状态和后级功放驱动场景下，链路不会出现过量泄漏、瞬时功率突波、控制毛刺或异常振荡，避免影响探头和功放安全。<br><br>2、射频接收链路：需要对微弱核磁共振信号进行高增益、低噪声、线性的接收与放大，并兼顾不同信号幅度下的动态范围。要求接收链路在强弱信号切换、带内干扰和温度变化条件下，仍能保持线性，不出现提前饱和、失真、基线扭曲或噪声底...

## Scope 规划

| Scope | 检索关键词 | 来源 | 命中数 | 说明 |
| --- | --- | --- | ---: | --- |
| 发射链路子系统 | 发射 / 上变频 / 调幅 / 功放驱动 / 衰减 / 功率 / 泄漏 | auto | 7 | matched keywords: 发射 / 上变频 / 调幅 / 功放驱动 / 衰减 / 功率 / 泄漏 |
| 接收与采集子系统 | 接收 / ADC / 时钟 / 噪声 / 解调 / 增益 / LNA | auto | 6 | matched keywords: 接收 / ADC / 时钟 / 噪声 / 解调 / 增益 |
| 频率合成与连接子系统 | 混频 / 本振 / 频率合成 / 背板 / 同轴 / 杂散 / 连接器 | auto | 6 | matched keywords: 混频 / 本振 / 频率合成 / 背板 / 同轴 / 杂散 |

## 发射链路子系统

| Scope | Analysis object | Function or requirement | Failure mode | Failure effect | S | Cause or mechanism | O | Current controls | D | RPN | Recommended actions | Confirmation status | Rating basis | Reference type | Source case |
| --- | --- | --- | --- | --- | ---: | --- | ---: | --- | ---: | ---: | --- | --- | --- | --- | --- |
| 发射链路子系统 | 异常状态保护 (核心逻辑) | 功率/脉宽/驻波超限时，极速切断射频输出，保护功放与探头。 | 保护动作严重滞后（器件已烧毁才触发） | 客户：由于5s的检测周期远大于100ms的脉宽，反射功率瞬间击穿末级功率管或毁坏探头。 | 10 | 依赖软件轮询进行异常检测，5s的周期对于微秒级的射频脉冲而言太慢。 | 6 | 软件轮询检测（周期5s）+ 蜂鸣器告警。 | 8 | 480 | 引入纯硬件级联锁保护（Hard Interlock）：采用高速比较器直接切断射频输入开关或偏置电压，响应时间控制在微秒（$\mu$s）级。5s周期仅用于UI刷新和软件复位逻辑。 | needs expert confirmation | S=10 继承自历史案例的后果强度；O=6、D=8 继承自成品 DFMEA，但仍需结合本企业标尺校准；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 2 |
| 发射链路子系统 | 射频调谐/匹配网络 | 实现宽频调谐与50Ω匹配；承受大功率发射时不击穿。 | 大功率射频脉冲下电容器件或节点发生打火 (Arcing) | 客户：探头内部烧毁，引发射频全反射烧毁功放。 后工序：高功测试时探头报废。 | 10 | 强射频场在电容两端产生千伏高压；空气介电强度不足或存在金属毛刺尖端放电。 | 5 | 选用高耐压无磁电容。 | 6 | 300 | 增加高压节点的聚四氟乙烯 (PTFE) 绝缘灌封或充入绝缘气体 (如SF6或高压氮气)；电路板进行严格的去毛刺抛光工艺。 | needs expert confirmation | S=10 继承自历史案例的后果强度；O=5、D=6 继承自成品 DFMEA，但仍需结合本企业标尺校准；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | CAN400产品DFMEA.xlsx / 调谐单元 / row 2 |
| 发射链路子系统 | VSWR 失配检测 | 精确检测正反向功率，反射>50%或驻波>6关断。 | 宽频段内（5-400MHz）反射功率测量严重失准 | 客户：假报警导致实验频频中断（过保护），或驻波已极大但不报警（漏保护）。 | 9 | 宽带定向耦合器的方向性（Directivity）在低频和高频端衰减严重，无法区分正反向。 | 5 | 驻波比阈值检测。 | 6 | 270 | 已采用分段耦合器或在DSP端对不同频点的耦合度进行频率补偿（Look-up Table）；过滤瞬时尖峰防误报。 | needs expert confirmation | S=9 继承自历史案例的后果强度；O=5、D=6 继承自成品 DFMEA，但仍需结合本企业标尺校准；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 5 |
| 发射链路子系统 |  | 射频信号稳定传输，低插入损耗。 | 接口在大功率下产生电弧或击穿 |  | 9 | 同轴线缆中心针位移；接头紧固力矩不一。 | 4 | 手动紧固；柔性电缆连接。 | 6 | 216 | 定期对接口进行电磁回波损耗（Return Loss）测试；使用力矩扳手规定装配标准。 | needs expert confirmation | S=9 继承自历史案例的后果强度；O=4、D=6 继承自成品 DFMEA，但仍需结合本企业标尺校准；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | CAN400产品DFMEA.xlsx / 前置放大器 / row 5 |
| 发射链路子系统 | 射频发射路径 (上变频与调幅) | 提供≥90dB精确衰减控制，输出功率大于等于3dBm，激励脉冲准确。 | 大衰减状态下实际衰减量不达标（射频泄漏） |  | 7 | 高衰减量下，射频信号通过PCB基材、电源网络或空间直接串扰至输出端。 | 6 | 常规PCB布线，软件闭环控制。 | 5 | 210 | 物理隔离：对衰减器链路分腔屏蔽-已实施（加装金属屏蔽罩）；电源走线增加多级LC滤波。-已实施 | draft | S=7 继承自历史案例的后果强度；O=6、D=5 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | CAN400产品DFMEA.xlsx / 收发机 / row 2 |
| 发射链路子系统 | 双通道射频放大 | 在指定频段提供51±1 dB稳定增益，输出140W/300W线性功率。 | 大动态脉冲下增益压缩或相位失真 | 客户：射频脉冲翻转角不准，NMR信号强度异常，甚至无法激发出信号。 | 8 | 大功率输出时晶体管结温急剧上升，导致跨导变化，引发热记忆效应。 | 5 | 出厂静态标定51dB。 | 5 | 200 | 增加包络反馈或动态偏置控制；使用包络跟踪（Envelope Tracking）技术补偿大功率下的增益压缩。 | needs expert confirmation | S=8 继承自历史案例的后果强度；O=5、D=5 继承自成品 DFMEA，但仍需结合本企业标尺校准；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 3 |
| 发射链路子系统 | 射频发射路径 (功放驱动) | 稳定输出射频信号至后级功放。 | 射频输出功率瞬间突波/失控超标 |  | 9 | DAC控制毛刺；ALC（自动电平控制）环路因温度或时序异常发生自激震荡。 | 4 | 软件功率上限限制。输入和输出端之间增加匹配电路 | 5 | 180 | 硬件级保护：在输出端增加定向耦合器+检波器，引入纯硬件的极速过功率切断开关（PIN二极管）。 | draft | S=9 继承自历史案例的后果强度；O=4、D=5 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | CAN400产品DFMEA.xlsx / 收发机 / row 3 |
| 发射链路子系统 | 通道切换 (BB与2H复用) | BB通道与2H通道共享功率放大器，通过开关切换。 | 带载热切换（Hot Switching）导致开关拉弧击穿 | 后工序：联调时切换通道烧毁继电器。 客户：射频泄漏，观察核信号被锁场信号污染。 | 7 | 软件时序存在竞争，在还有射频输出时执行了继电器/同轴开关的物理切换动作。 | 4 | 无明确的防误切机制。 | 5 | 140 | 强制冷切换逻辑：软件下发切换指令前，硬件强制拉低BLNK信号屏蔽射频输入，延时几十毫秒后再进行开关切换。 | needs expert confirmation | S=7 继承自历史案例的后果强度；O=4、D=5 继承自成品 DFMEA，但仍需结合本企业标尺校准；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 4 |
| 发射链路子系统 |  | 功率超阈值时关闭射频输入并告警。 | 功率检测耦合器失效或响应过慢 |  | 9 | 耦合路径阻抗失配；检波器动态范围受限。 | 3 | 耦合功率监测；手动解除告警。 | 5 | 135 | 引入硬件联动跳闸：告警信号不经过上位机，直接硬件拉低功率门控。 | needs expert confirmation | S=9 继承自历史案例的后果强度；O=3、D=5 继承自成品 DFMEA，但仍需结合本企业标尺校准；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | CAN400产品DFMEA.xlsx / 前置放大器 / row 4 |
| 发射链路子系统 |  | 发射时隔离高功率(300W+)，保护LNA；接收时快速导通。 | PIN二极管热击穿或响应滞后 |  | 10 | 散热设计不足；RGP信号边沿抖动或时序竞争。 | 3 | 交叉PIN管短路引导地；限幅电路。 选用更高功率余量的PIN管 | 4 | 120 |  | needs expert confirmation | S=10 继承自历史案例的后果强度；O=3、D=4 继承自成品 DFMEA，但仍需结合本企业标尺校准；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | CAN400产品DFMEA.xlsx / 前置放大器 / row 2 |

## 接收与采集子系统

| Scope | Analysis object | Function or requirement | Failure mode | Failure effect | S | Cause or mechanism | O | Current controls | D | RPN | Recommended actions | Confirmation status | Rating basis | Reference type | Source case |
| --- | --- | --- | --- | --- | ---: | --- | ---: | --- | ---: | ---: | --- | --- | --- | --- | --- |
| 接收与采集子系统 | 射频接收路径 (微弱信号放大) | 接收机提供65dB最大增益，0.5dB精确步进。 | 接收链路非线性失真或提前饱和 |  | 8 | 大信号恢复时间慢；放大器偏置电压温漂；带内强干扰导致LNA阻塞。 | 5 | 静态增益校准测试。 优化链路中的自动增益分配方案，ADC采集端增加算法优化采集前信号的线性度 | 4 | 160 | 增强动态范围：接收机前端增加极速限幅器（Limiter）-尝试过会引入额外的噪声；选用高P1dB和IP3的低噪声放大器（LNA）-已实施。 | draft | S=8 继承自历史案例的后果强度；O=5、D=4 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | CAN400产品DFMEA.xlsx / 收发机 / row 4 |
| 接收与采集子系统 |  | 提供$\ge$30dB增益，NF$\le$1.2-1.8dB。 | 增益波动或自激振荡 |  | 8 | 工作环境温升导致偏置电流漂移；屏蔽腔隔离度不足。 | 4 | 屏蔽腔设计；金属外壳隔离。链路中对增益进行均衡化设计 | 3 | 96 | 增加板载温度补偿电路；优化腔体电磁屏蔽分区。 | needs expert confirmation | S=8 继承自历史案例的后果强度；O=4、D=3 继承自成品 DFMEA，但仍需结合本企业标尺校准；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | CAN400产品DFMEA.xlsx / 前置放大器 / row 3 |
| 接收与采集子系统 | 数字采集与处理 | 对下变频后的信号进行高精度ADC采集与数字解调。 | ADC时钟抖动过大或参考电压受扰 |  | 7 | 与时钟板（REF）的同轴连接不良；板内数字电路高频噪声串入模拟电源区。 | 4 | 独立的LDO供电。 选用高稳定性ADC时钟的晶振， PCB走线布局避开高速干扰 | 3 | 84 | 时钟净化：在ADC时钟输入端增加高低频去耦网络-已实施；引入差分时钟传输-已实施；优化数模地（AGND/DGND）分割-已实施。 | draft | S=7 继承自历史案例的后果强度；O=4、D=3 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | CAN400产品DFMEA.xlsx / 收发机 / row 6 |

## 频率合成与连接子系统

| Scope | Analysis object | Function or requirement | Failure mode | Failure effect | S | Cause or mechanism | O | Current controls | D | RPN | Recommended actions | Confirmation status | Rating basis | Reference type | Source case |
| --- | --- | --- | --- | --- | ---: | --- | ---: | --- | ---: | ---: | --- | --- | --- | --- | --- |
| 频率合成与连接子系统 | 物理连接 (背板与外部) | 与CAS背板建立高可靠的电源与数据硬连接；同轴线传输射频。 | 背板连接器金手指磨损或受应力产生微断路 |  | 8 | “硬链接”缺乏机械公差吸收能力，机箱热变形或震动直接产生剪切应力。 | 5 | 出厂人工目检插拔。 参考竞品选择高稳定性的插针式连接器 | 6 | 240 | 消除机械应力：弃用刚性硬插拔，改用具有盲插浮动容差能力的工业背板连接器（Floating Connector），并增加导向定位销。 | draft | S=8 继承自历史案例的后果强度；O=5、D=6 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | CAN400产品DFMEA.xlsx / 收发机 / row 7 |
| 频率合成与连接子系统 | 混频与频率合成 (上/下变频) | 产生64MHz中频，进行5~400MHz的高纯度变频。 | 杂散信号与本振（LO）泄漏落入10MHz模拟带宽内 |  | 8 | 混频器隔离度不足；5~400MHz宽带滤波难度大，高次谐波未滤除净。 | 6 | 依赖芯片自带抑制能力。 频率规划设计保证 | 4 | 192 | 优化频率规划-已实施：采用高隔离度混频器；由于64MHz在射频带内，需设计高阶切换滤波器组（Switched Filter Bank）进行分段滤波-不适用。 | draft | S=8 继承自历史案例的后果强度；O=6、D=4 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | CAN400产品DFMEA.xlsx / 收发机 / row 5 |

## Top Risks

| Scope | Failure mode | Current RPN | Why it matters | First action candidate | Reference type |
| --- | --- | ---: | --- | --- | --- |
| 发射链路子系统 | 保护动作严重滞后（器件已烧毁才触发） | 480 | 客户：由于5s的检测周期远大于100ms的脉宽，反射功率瞬间击穿末级功率管或毁坏探头。 | 引入纯硬件级联锁保护（Hard Interlock）：采用高速比较器直接切断射频输入开关或偏置电压，响应时间控制在微秒（$\mu$s）级。5s周期仅用于U... | direct family reference |
| 发射链路子系统 | 大功率射频脉冲下电容器件或节点发生打火 (Arcing) | 300 | 客户：探头内部烧毁，引发射频全反射烧毁功放。 后工序：高功测试时探头报废。 | 增加高压节点的聚四氟乙烯 (PTFE) 绝缘灌封或充入绝缘气体 (如SF6或高压氮气)；电路板进行严格的去毛刺抛光工艺。 | direct family reference |
| 发射链路子系统 | 宽频段内（5-400MHz）反射功率测量严重失准 | 270 | 客户：假报警导致实验频频中断（过保护），或驻波已极大但不报警（漏保护）。 | 已采用分段耦合器或在DSP端对不同频点的耦合度进行频率补偿（Look-up Table）；过滤瞬时尖峰防误报。 | direct family reference |
| 频率合成与连接子系统 | 背板连接器金手指磨损或受应力产生微断路 | 240 |  | 消除机械应力：弃用刚性硬插拔，改用具有盲插浮动容差能力的工业背板连接器（Floating Connector），并增加导向定位销。 | current module |
| 发射链路子系统 | 接口在大功率下产生电弧或击穿 | 216 |  | 定期对接口进行电磁回波损耗（Return Loss）测试；使用力矩扳手规定装配标准。 | direct family reference |
| 发射链路子系统 | 大衰减状态下实际衰减量不达标（射频泄漏） | 210 |  | 物理隔离：对衰减器链路分腔屏蔽-已实施（加装金属屏蔽罩）；电源走线增加多级LC滤波。-已实施 | current module |
| 发射链路子系统 | 大动态脉冲下增益压缩或相位失真 | 200 | 客户：射频脉冲翻转角不准，NMR信号强度异常，甚至无法激发出信号。 | 增加包络反馈或动态偏置控制；使用包络跟踪（Envelope Tracking）技术补偿大功率下的增益压缩。 | direct family reference |
| 频率合成与连接子系统 | 杂散信号与本振（LO）泄漏落入10MHz模拟带宽内 | 192 |  | 优化频率规划-已实施：采用高隔离度混频器；由于64MHz在射频带内，需设计高阶切换滤波器组（Switched Filter Bank）进行分段滤波-不适用。 | current module |

## Rows Needing Confirmation

| Scope | Row key | Why confirmation is needed | Suggested reviewer focus | Reference type | Source case |
| --- | --- | --- | --- | --- | --- |
| 发射链路子系统 | 异常状态保护 (核心逻辑) / 保护动作严重滞后（器件已烧毁才触发） | 该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围 | 确认该类比是否适用于当前模块机理、接口和责任范围；校准 O/D 与实际保护、测试和筛选能力是否匹配 | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 2 |
| 发射链路子系统 | 射频调谐/匹配网络 / 大功率射频脉冲下电容器件或节点发生打火 (Arcing) | 该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围 | 确认该类比是否适用于当前模块机理、接口和责任范围；校准 O/D 与实际保护、测试和筛选能力是否匹配 | direct family reference | CAN400产品DFMEA.xlsx / 调谐单元 / row 2 |
| 发射链路子系统 | VSWR 失配检测 / 宽频段内（5-400MHz）反射功率测量严重失准 | 该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围 | 确认该类比是否适用于当前模块机理、接口和责任范围；校准 O/D 与实际保护、测试和筛选能力是否匹配 | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 5 |
| 发射链路子系统 | 射频信号稳定传输，低插入损耗。 / 接口在大功率下产生电弧或击穿 | 该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围；scope 归属存在边界，当前放在本 scope，但也可能属于：频率合成与连接子系统 | 确认 scope 归属与责任边界；确认该类比是否适用于当前模块机理、接口和责任范围；校准 O/D 与实际保护、测试和筛选能力是否匹配 | direct family reference | CAN400产品DFMEA.xlsx / 前置放大器 / row 5 |
| 发射链路子系统 | 双通道射频放大 / 大动态脉冲下增益压缩或相位失真 | 该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围；scope 归属存在边界，当前放在本 scope，但也可能属于：接收与采集子系统 | 确认 scope 归属与责任边界；确认该类比是否适用于当前模块机理、接口和责任范围；校准 O/D 与实际保护、测试和筛选能力是否匹配 | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 3 |
| 发射链路子系统 | 通道切换 (BB与2H复用) / 带载热切换（Hot Switching）导致开关拉弧击穿 | 该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围 | 确认该类比是否适用于当前模块机理、接口和责任范围；校准 O/D 与实际保护、测试和筛选能力是否匹配 | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 4 |
| 发射链路子系统 | 功率超阈值时关闭射频输入并告警。 / 功率检测耦合器失效或响应过慢 | 该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围 | 确认该类比是否适用于当前模块机理、接口和责任范围；校准 O/D 与实际保护、测试和筛选能力是否匹配 | direct family reference | CAN400产品DFMEA.xlsx / 前置放大器 / row 4 |
| 发射链路子系统 | 发射时隔离高功率(300W+)，保护LNA；接收时快速导通。 / PIN二极管热击穿或响应滞后 | 该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围；scope 归属存在边界，当前放在本 scope，但也可能属于：接收与采集子系统 | 确认 scope 归属与责任边界；确认该类比是否适用于当前模块机理、接口和责任范围；校准 O/D 与实际保护、测试和筛选能力是否匹配 | direct family reference | CAN400产品DFMEA.xlsx / 前置放大器 / row 2 |
| 接收与采集子系统 | 提供$\ge$30dB增益，NF$\le$1.2-1.8dB。 / 增益波动或自激振荡 | 该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围 | 确认该类比是否适用于当前模块机理、接口和责任范围；校准 O/D 与实际保护、测试和筛选能力是否匹配 | direct family reference | CAN400产品DFMEA.xlsx / 前置放大器 / row 3 |

## Suggested Actions

| Scope | Row key | Current RPN | Recommended action | Owner | Target date | Confirmation status | Reference type | Source case |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| 发射链路子系统 | 异常状态保护 (核心逻辑) / 保护动作严重滞后（器件已烧毁才触发） | 480 | 引入纯硬件级联锁保护（Hard Interlock）：采用高速比较器直接切断射频输入开关或偏置电压，响应时间控制在微秒（$\mu$s）级。5s周期仅用于UI刷新和软件复位逻辑。 |  |  | needs expert confirmation | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 2 |
| 发射链路子系统 | 射频调谐/匹配网络 / 大功率射频脉冲下电容器件或节点发生打火 (Arcing) | 300 | 增加高压节点的聚四氟乙烯 (PTFE) 绝缘灌封或充入绝缘气体 (如SF6或高压氮气)；电路板进行严格的去毛刺抛光工艺。 |  |  | needs expert confirmation | direct family reference | CAN400产品DFMEA.xlsx / 调谐单元 / row 2 |
| 发射链路子系统 | VSWR 失配检测 / 宽频段内（5-400MHz）反射功率测量严重失准 | 270 | 已采用分段耦合器或在DSP端对不同频点的耦合度进行频率补偿（Look-up Table）；过滤瞬时尖峰防误报。 |  |  | needs expert confirmation | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 5 |
| 频率合成与连接子系统 | 物理连接 (背板与外部) / 背板连接器金手指磨损或受应力产生微断路 | 240 | 消除机械应力：弃用刚性硬插拔，改用具有盲插浮动容差能力的工业背板连接器（Floating Connector），并增加导向定位销。 |  |  | draft | current module | CAN400产品DFMEA.xlsx / 收发机 / row 7 |
| 发射链路子系统 | 射频信号稳定传输，低插入损耗。 / 接口在大功率下产生电弧或击穿 | 216 | 定期对接口进行电磁回波损耗（Return Loss）测试；使用力矩扳手规定装配标准。 |  |  | needs expert confirmation | direct family reference | CAN400产品DFMEA.xlsx / 前置放大器 / row 5 |
| 发射链路子系统 | 射频发射路径 (上变频与调幅) / 大衰减状态下实际衰减量不达标（射频泄漏） | 210 | 物理隔离：对衰减器链路分腔屏蔽-已实施（加装金属屏蔽罩）；电源走线增加多级LC滤波。-已实施 |  |  | draft | current module | CAN400产品DFMEA.xlsx / 收发机 / row 2 |
| 发射链路子系统 | 双通道射频放大 / 大动态脉冲下增益压缩或相位失真 | 200 | 增加包络反馈或动态偏置控制；使用包络跟踪（Envelope Tracking）技术补偿大功率下的增益压缩。 |  |  | needs expert confirmation | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 3 |
| 频率合成与连接子系统 | 混频与频率合成 (上/下变频) / 杂散信号与本振（LO）泄漏落入10MHz模拟带宽内 | 192 | 优化频率规划-已实施：采用高隔离度混频器；由于64MHz在射频带内，需设计高阶切换滤波器组（Switched Filter Bank）进行分段滤波-不适用。 |  |  | draft | current module | CAN400产品DFMEA.xlsx / 收发机 / row 5 |
| 发射链路子系统 | 射频发射路径 (功放驱动) / 射频输出功率瞬间突波/失控超标 | 180 | 硬件级保护：在输出端增加定向耦合器+检波器，引入纯硬件的极速过功率切断开关（PIN二极管）。 |  |  | draft | current module | CAN400产品DFMEA.xlsx / 收发机 / row 3 |
| 接收与采集子系统 | 射频接收路径 (微弱信号放大) / 接收链路非线性失真或提前饱和 | 160 | 增强动态范围：接收机前端增加极速限幅器（Limiter）-尝试过会引入额外的噪声；选用高P1dB和IP3的低噪声放大器（LNA）-已实施。 |  |  | draft | current module | CAN400产品DFMEA.xlsx / 收发机 / row 4 |
| 发射链路子系统 | 通道切换 (BB与2H复用) / 带载热切换（Hot Switching）导致开关拉弧击穿 | 140 | 强制冷切换逻辑：软件下发切换指令前，硬件强制拉低BLNK信号屏蔽射频输入，延时几十毫秒后再进行开关切换。 |  |  | needs expert confirmation | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 4 |
| 发射链路子系统 | 功率超阈值时关闭射频输入并告警。 / 功率检测耦合器失效或响应过慢 | 135 | 引入硬件联动跳闸：告警信号不经过上位机，直接硬件拉低功率门控。 |  |  | needs expert confirmation | direct family reference | CAN400产品DFMEA.xlsx / 前置放大器 / row 4 |

## Source Trace

| Scope | Row key | Reference type | Source case |
| --- | --- | --- | --- |
| 发射链路子系统 | 异常状态保护 (核心逻辑) / 保护动作严重滞后（器件已烧毁才触发） | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 2 |
| 发射链路子系统 | 射频调谐/匹配网络 / 大功率射频脉冲下电容器件或节点发生打火 (Arcing) | direct family reference | CAN400产品DFMEA.xlsx / 调谐单元 / row 2 |
| 发射链路子系统 | VSWR 失配检测 / 宽频段内（5-400MHz）反射功率测量严重失准 | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 5 |
| 发射链路子系统 | 射频信号稳定传输，低插入损耗。 / 接口在大功率下产生电弧或击穿 | direct family reference | CAN400产品DFMEA.xlsx / 前置放大器 / row 5 |
| 发射链路子系统 | 射频发射路径 (上变频与调幅) / 大衰减状态下实际衰减量不达标（射频泄漏） | current module | CAN400产品DFMEA.xlsx / 收发机 / row 2 |
| 发射链路子系统 | 双通道射频放大 / 大动态脉冲下增益压缩或相位失真 | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 3 |
| 发射链路子系统 | 射频发射路径 (功放驱动) / 射频输出功率瞬间突波/失控超标 | current module | CAN400产品DFMEA.xlsx / 收发机 / row 3 |
| 发射链路子系统 | 通道切换 (BB与2H复用) / 带载热切换（Hot Switching）导致开关拉弧击穿 | direct family reference | CAN400产品DFMEA.xlsx / 射频功放 / row 4 |
| 发射链路子系统 | 功率超阈值时关闭射频输入并告警。 / 功率检测耦合器失效或响应过慢 | direct family reference | CAN400产品DFMEA.xlsx / 前置放大器 / row 4 |
| 发射链路子系统 | 发射时隔离高功率(300W+)，保护LNA；接收时快速导通。 / PIN二极管热击穿或响应滞后 | direct family reference | CAN400产品DFMEA.xlsx / 前置放大器 / row 2 |
| 接收与采集子系统 | 射频接收路径 (微弱信号放大) / 接收链路非线性失真或提前饱和 | current module | CAN400产品DFMEA.xlsx / 收发机 / row 4 |
| 接收与采集子系统 | 提供$\ge$30dB增益，NF$\le$1.2-1.8dB。 / 增益波动或自激振荡 | direct family reference | CAN400产品DFMEA.xlsx / 前置放大器 / row 3 |
| 接收与采集子系统 | 数字采集与处理 / ADC时钟抖动过大或参考电压受扰 | current module | CAN400产品DFMEA.xlsx / 收发机 / row 6 |
| 频率合成与连接子系统 | 物理连接 (背板与外部) / 背板连接器金手指磨损或受应力产生微断路 | current module | CAN400产品DFMEA.xlsx / 收发机 / row 7 |
| 频率合成与连接子系统 | 混频与频率合成 (上/下变频) / 杂散信号与本振（LO）泄漏落入10MHz模拟带宽内 | current module | CAN400产品DFMEA.xlsx / 收发机 / row 5 |
