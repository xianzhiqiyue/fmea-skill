# 调谐单元 首版 DFMEA 草稿

- 生成方式: `draft_fmea_from_cases.py`
- 模块: `调谐单元`
- FMEA 类型: `DFMEA`
- 输入长度: `839` 字符

## 输入摘要

> 示例：我们目前正在设计一套用于 NMR 探头的调谐单元，目标是在不同样品、不同频点和不同负载条件下，自动完成调谐与匹配，使探头能够稳定找到合适的谐振点并实现接近 50Ω 的匹配状态，同时保证在大功率射频发射、复杂电磁环境以及频繁机械调节过程中，系统不会发生不可逆损伤或失控。<br><br>调谐单元主要包含以下几个方面：<br><br>1、射频调谐与匹配网络：需要在较宽的频率范围内完成调谐与匹配，并在大功率射频脉冲下保持稳定，不能因为局部高压、电场集中、绝缘不足或结构尖端效应导致器件损伤、放电、击穿或匹配失稳。调谐网络还需要兼顾高 Q 值、低损耗以及与后级功放和探头的协同安全性。<br><br>2、机械传动与限位结构：调谐单元通过电机、减速机构、连杆或调节杆实现位置调节，用于改变调谐和匹配状态。要求运动链条在自动调节过程中动作可控、传动平稳、定位准确，并在到达极限位置、遇到阻挡或异常负载时仍能保护易损部件，不因过扭矩、扫齿、连...

## Scope 规划

| Scope | 检索关键词 | 来源 | 命中数 | 说明 |
| --- | --- | --- | ---: | --- |
| 射频调谐与匹配子系统 | 射频 / 调谐 / 匹配 / 线圈 / 焊接 / 磁化率 / 电容 / 打火 / 梯度线圈 | auto | 6 | matched keywords: 射频 / 调谐 / 匹配 / 线圈 / 焊接 / 磁化率 |
| 机械传动与限位子系统 | 电机 / 编码器 / 限位 / 连杆 / 减速机 / 扭矩 / 离合器 / 齿轮 | auto | 6 | matched keywords: 电机 / 编码器 / 限位 / 连杆 / 减速机 / 扭矩 |
| EMC与算法控制子系统 | MCU / 搜索 / 陷波 / 算法 / EMC / CAN / RS422 / 光耦 / 扫掠 | auto | 4 | matched keywords: MCU / 搜索 / 陷波 / 算法 |

## 射频调谐与匹配子系统

| Scope | Analysis object | Function or requirement | Failure mode | Failure effect | S | Cause or mechanism | O | Current controls | D | RPN | Recommended actions | Confirmation status | Rating basis | Reference type | Source case |
| --- | --- | --- | --- | --- | ---: | --- | ---: | --- | ---: | ---: | --- | --- | --- | --- | --- |
| 射频调谐与匹配子系统 | 射频调谐/匹配网络 | 实现宽频调谐与50Ω匹配；承受大功率发射时不击穿。 | 大功率射频脉冲下电容器件或节点发生打火 (Arcing) | 客户：探头内部烧毁，引发射频全反射烧毁功放。 后工序：高功测试时探头报废。 | 10 | 强射频场在电容两端产生千伏高压；空气介电强度不足或存在金属毛刺尖端放电。 | 5 | 选用高耐压无磁电容。 | 6 | 300 | 增加高压节点的聚四氟乙烯 (PTFE) 绝缘灌封或充入绝缘气体 (如SF6或高压氮气)；电路板进行严格的去毛刺抛光工艺。 | draft | S=10 继承自历史案例的后果强度；O=5、D=6 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | CAN400产品DFMEA.xlsx / 调谐单元 / row 2 |
| 射频调谐与匹配子系统 | 射频线圈与焊接 | 提供极高Q值和B0均匀性；确保材料磁化率极低。 | 射频线圈局部引入磁性杂质，导致磁化率异常 | 客户：谱图线型展宽（Line broadening），分辨率达不到ppb级要求。 后工序：匀场困难，耗费大量工时。 | 8 | “焊料焊接在电路中”——普通焊锡或助焊剂中常含有微量镍(Ni)或铁(Fe)等铁磁性杂质。 | 5 | 规定使用无磁材料。 | 7 | 280 | 严格规范BOM，必须采用高纯度无磁焊料 (如特定配比的锡银铜 Sn-Ag-Cu)；后工序增加焊点的高灵敏度 SQUID 磁性初筛。 | draft | S=8 继承自历史案例的后果强度；O=5、D=7 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | CAN400产品DFMEA.xlsx / 调谐单元 / row 5 |
| 射频调谐与匹配子系统 | 物理连接 (背板与外部) | 与CAS背板建立高可靠的电源与数据硬连接；同轴线传输射频。 | 背板连接器金手指磨损或受应力产生微断路 |  | 8 | “硬链接”缺乏机械公差吸收能力，机箱热变形或震动直接产生剪切应力。 | 5 | 出厂人工目检插拔。 参考竞品选择高稳定性的插针式连接器 | 6 | 240 | 消除机械应力：弃用刚性硬插拔，改用具有盲插浮动容差能力的工业背板连接器（Floating Connector），并增加导向定位销。 | needs expert confirmation | S=8 继承自历史案例的后果强度；O=5、D=6 继承自成品 DFMEA，但仍需结合本企业标尺校准；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | CAN400产品DFMEA.xlsx / 收发机 / row 7 |
| 射频调谐与匹配子系统 | Z向梯度线圈 | 抵消外部涡流，提供精准线性梯度。 | 主线圈与屏蔽线圈产生的震动声学谐振 (Acoustic Ringing) | 客户：梯度脉冲结束后，线圈震动切割磁力线产生假性RF信号，干扰微弱的NMR回波。 | 7 | 大电流梯度脉冲在强磁场中产生巨大的洛伦兹力，导致线圈骨架发生微米级形变震荡。 | 6 | 主动屏蔽设计。 | 5 | 210 | 采用环氧树脂真空含浸灌封 (VPI) 加固梯度线圈骨架，并在梯度线圈与射频线圈之间增加特种声学阻尼材料隔离震动。 | draft | S=7 继承自历史案例的后果强度；O=6、D=5 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | CAN400产品DFMEA.xlsx / 调谐单元 / row 6 |
| 射频调谐与匹配子系统 | 射频发射路径 (上变频与调幅) | 提供≥90dB精确衰减控制，输出功率大于等于3dBm，激励脉冲准确。 | 大衰减状态下实际衰减量不达标（射频泄漏） |  | 7 | 高衰减量下，射频信号通过PCB基材、电源网络或空间直接串扰至输出端。 | 6 | 常规PCB布线，软件闭环控制。 | 5 | 210 | 物理隔离：对衰减器链路分腔屏蔽-已实施（加装金属屏蔽罩）；电源走线增加多级LC滤波。-已实施 | needs expert confirmation | S=7 继承自历史案例的后果强度；O=6、D=5 继承自成品 DFMEA，但仍需结合本企业标尺校准；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | CAN400产品DFMEA.xlsx / 收发机 / row 2 |
| 射频调谐与匹配子系统 | 射频发射路径 (功放驱动) | 稳定输出射频信号至后级功放。 | 射频输出功率瞬间突波/失控超标 |  | 9 | DAC控制毛刺；ALC（自动电平控制）环路因温度或时序异常发生自激震荡。 | 4 | 软件功率上限限制。输入和输出端之间增加匹配电路 | 5 | 180 | 硬件级保护：在输出端增加定向耦合器+检波器，引入纯硬件的极速过功率切断开关（PIN二极管）。 | needs expert confirmation | S=9 继承自历史案例的后果强度；O=4、D=5 继承自成品 DFMEA，但仍需结合本企业标尺校准；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | CAN400产品DFMEA.xlsx / 收发机 / row 3 |
| 射频调谐与匹配子系统 | 射频接收路径 (微弱信号放大) | 接收机提供65dB最大增益，0.5dB精确步进。 | 接收链路非线性失真或提前饱和 |  | 8 | 大信号恢复时间慢；放大器偏置电压温漂；带内强干扰导致LNA阻塞。 | 5 | 静态增益校准测试。 优化链路中的自动增益分配方案，ADC采集端增加算法优化采集前信号的线性度 | 4 | 160 | 增强动态范围：接收机前端增加极速限幅器（Limiter）-尝试过会引入额外的噪声；选用高P1dB和IP3的低噪声放大器（LNA）-已实施。 | needs expert confirmation | S=8 继承自历史案例的后果强度；O=5、D=4 继承自成品 DFMEA，但仍需结合本企业标尺校准；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | CAN400产品DFMEA.xlsx / 收发机 / row 4 |

## 机械传动与限位子系统

| Scope | Analysis object | Function or requirement | Failure mode | Failure effect | S | Cause or mechanism | O | Current controls | D | RPN | Recommended actions | Confirmation status | Rating basis | Reference type | Source case |
| --- | --- | --- | --- | --- | ---: | --- | ---: | --- | ---: | ---: | --- | --- | --- | --- | --- |
| 机械传动与限位子系统 | 硬件系统 (抗电磁干扰) | 编码器信号准确传输至MCU，保证闭环位置精度。 | 电机转动丢步、编码器脉冲错乱或MCU死机 | 客户：调谐位置漂移，匹配曲线不对称，信号灵敏度严重下降。 | 8 | 探头发射千瓦级射频时，能量通过电机线缆、编码器线缆耦合进控制板卡，击穿LDO或干扰光耦。 | 7 | 选用隔离CAN；浪涌保护。 | 5 | 280 | 电机与编码器线缆必须使用双层编织屏蔽线，并在进入控制板处增加 LC 穿心电容滤波器；编码器信号采用RS422差分传输替代单端传输。 | needs expert confirmation | S=8 继承自历史案例的后果强度；O=7、D=5 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | CAN400产品DFMEA.xlsx / 调谐单元 / row 4 |
| 机械传动与限位子系统 | 探头机械传动 (硬限位) | 通过电机驱动芯片检测电流，对比DAC参考电压实现防撞硬限位保护。 | 调谐杆被电机扭断或齿轮扫齿，限位保护未触发 | 客户：自动调谐瘫痪，机械结构不可逆损坏需返厂。 后工序：装配调试时极易损坏精密连杆。 | 9 | 减速机(110310)放大扭矩极大，在电流显著突变(达到比较器阈值)之前，机械脆弱点(如玻璃/蓝宝石调节杆)已达到屈服极限而断裂。 | 6 | 驱动芯片电流感应+比较器硬件限位。 | 5 | 270 | 绝对禁止纯依赖电流检测限位。增加机械滑动离合器 (Slip Clutch) 进行扭矩物理卸载；或在连杆末端增加微型光电开关作物理限位。 | draft | S=9 继承自历史案例的后果强度；O=6、D=5 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | CAN400产品DFMEA.xlsx / 调谐单元 / row 3 |

## EMC与算法控制子系统

| Scope | Analysis object | Function or requirement | Failure mode | Failure effect | S | Cause or mechanism | O | Current controls | D | RPN | Recommended actions | Confirmation status | Rating basis | Reference type | Source case |
| --- | --- | --- | --- | --- | ---: | --- | ---: | --- | ---: | ---: | --- | --- | --- | --- | --- |
| EMC与算法控制子系统 | 软件调谐算法 | 陷波搜索法，自动找到中心频率并最大化匹配。 | 搜索失败陷入死循环，或锁定到错误的“假陷波” (Cable Resonance) | 客户：换了一个极性差异大的样品后，系统一直报错“Tuning Failed”。 | 7 | 用户更换溶剂（如从CDCl3换到极性极强的水或高盐溶液）导致谐振频偏远远超出了数据库记录的附近范围；同轴电缆自身的驻波被误认为是探头陷波。 | 6 | 分两段高低分辨率搜索；依赖数据库起点。 | 4 | 168 | 算法增加**“宽带全扫掠 (Full-span Sweep) 扫底”后备逻辑**；引入波形模式识别，判断陷波的Q值深度，排除电缆谐振的宽缓假波。 | draft | S=7 继承自历史案例的后果强度；O=6、D=4 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | CAN400产品DFMEA.xlsx / 调谐单元 / row 7 |
| EMC与算法控制子系统 | 匀场算法与控制软件 | 准确计算并下发码值，防止系统挂死或参数丢失。 | SDB板卡通信挂死 / 参数掉电丢失 |  | 7 | 通信总线（如SPI/I2C/CAN）受外部强磁或梯度线圈脉冲干扰；无本地固化存储。 | 4 | 软件电流超限报警。 | 4 | 112 | 增加通信看门狗（Watchdog）自动复位机制；SDB板载EEPROM，每次调节后自动备份当前最优Shimmap参数。 | needs expert confirmation | S=7 继承自历史案例的后果强度；O=4、D=4 继承自成品 DFMEA，但仍需结合本企业标尺校准；本行属于 broader analogy，仅建议作为补缺参考 | broader analogy | CAN400产品DFMEA.xlsx / 匀场单元 / row 6 |

## Top Risks

| Scope | Failure mode | Current RPN | Why it matters | First action candidate | Reference type |
| --- | --- | ---: | --- | --- | --- |
| 射频调谐与匹配子系统 | 大功率射频脉冲下电容器件或节点发生打火 (Arcing) | 300 | 客户：探头内部烧毁，引发射频全反射烧毁功放。 后工序：高功测试时探头报废。 | 增加高压节点的聚四氟乙烯 (PTFE) 绝缘灌封或充入绝缘气体 (如SF6或高压氮气)；电路板进行严格的去毛刺抛光工艺。 | current module |
| 射频调谐与匹配子系统 | 射频线圈局部引入磁性杂质，导致磁化率异常 | 280 | 客户：谱图线型展宽（Line broadening），分辨率达不到ppb级要求。 后工序：匀场困难，耗费大量工时。 | 严格规范BOM，必须采用高纯度无磁焊料 (如特定配比的锡银铜 Sn-Ag-Cu)；后工序增加焊点的高灵敏度 SQUID 磁性初筛。 | current module |
| 机械传动与限位子系统 | 电机转动丢步、编码器脉冲错乱或MCU死机 | 280 | 客户：调谐位置漂移，匹配曲线不对称，信号灵敏度严重下降。 | 电机与编码器线缆必须使用双层编织屏蔽线，并在进入控制板处增加 LC 穿心电容滤波器；编码器信号采用RS422差分传输替代单端传输。 | current module |
| 机械传动与限位子系统 | 调谐杆被电机扭断或齿轮扫齿，限位保护未触发 | 270 | 客户：自动调谐瘫痪，机械结构不可逆损坏需返厂。 后工序：装配调试时极易损坏精密连杆。 | 绝对禁止纯依赖电流检测限位。增加机械滑动离合器 (Slip Clutch) 进行扭矩物理卸载；或在连杆末端增加微型光电开关作物理限位。 | current module |
| 射频调谐与匹配子系统 | 背板连接器金手指磨损或受应力产生微断路 | 240 |  | 消除机械应力：弃用刚性硬插拔，改用具有盲插浮动容差能力的工业背板连接器（Floating Connector），并增加导向定位销。 | direct family reference |
| 射频调谐与匹配子系统 | 主线圈与屏蔽线圈产生的震动声学谐振 (Acoustic Ringing) | 210 | 客户：梯度脉冲结束后，线圈震动切割磁力线产生假性RF信号，干扰微弱的NMR回波。 | 采用环氧树脂真空含浸灌封 (VPI) 加固梯度线圈骨架，并在梯度线圈与射频线圈之间增加特种声学阻尼材料隔离震动。 | current module |
| 射频调谐与匹配子系统 | 大衰减状态下实际衰减量不达标（射频泄漏） | 210 |  | 物理隔离：对衰减器链路分腔屏蔽-已实施（加装金属屏蔽罩）；电源走线增加多级LC滤波。-已实施 | direct family reference |
| 射频调谐与匹配子系统 | 射频输出功率瞬间突波/失控超标 | 180 |  | 硬件级保护：在输出端增加定向耦合器+检波器，引入纯硬件的极速过功率切断开关（PIN二极管）。 | direct family reference |

## Rows Needing Confirmation

| Scope | Row key | Why confirmation is needed | Suggested reviewer focus | Reference type | Source case |
| --- | --- | --- | --- | --- | --- |
| 射频调谐与匹配子系统 | 物理连接 (背板与外部) / 背板连接器金手指磨损或受应力产生微断路 | 该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围 | 确认该类比是否适用于当前模块机理、接口和责任范围；校准 O/D 与实际保护、测试和筛选能力是否匹配 | direct family reference | CAN400产品DFMEA.xlsx / 收发机 / row 7 |
| 射频调谐与匹配子系统 | 射频发射路径 (上变频与调幅) / 大衰减状态下实际衰减量不达标（射频泄漏） | 该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围 | 确认该类比是否适用于当前模块机理、接口和责任范围；校准 O/D 与实际保护、测试和筛选能力是否匹配 | direct family reference | CAN400产品DFMEA.xlsx / 收发机 / row 2 |
| 射频调谐与匹配子系统 | 射频发射路径 (功放驱动) / 射频输出功率瞬间突波/失控超标 | 该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围 | 确认该类比是否适用于当前模块机理、接口和责任范围；校准 O/D 与实际保护、测试和筛选能力是否匹配 | direct family reference | CAN400产品DFMEA.xlsx / 收发机 / row 3 |
| 射频调谐与匹配子系统 | 射频接收路径 (微弱信号放大) / 接收链路非线性失真或提前饱和 | 该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围 | 确认该类比是否适用于当前模块机理、接口和责任范围；校准 O/D 与实际保护、测试和筛选能力是否匹配 | direct family reference | CAN400产品DFMEA.xlsx / 收发机 / row 4 |
| 机械传动与限位子系统 | 硬件系统 (抗电磁干扰) / 电机转动丢步、编码器脉冲错乱或MCU死机 | scope 归属存在边界，当前放在本 scope，但也可能属于：射频调谐与匹配子系统 / EMC与算法控制子系统 | 确认 scope 归属与责任边界；校准 O/D 与实际保护、测试和筛选能力是否匹配 | current module | CAN400产品DFMEA.xlsx / 调谐单元 / row 4 |
| EMC与算法控制子系统 | 匀场算法与控制软件 / SDB板卡通信挂死 / 参数掉电丢失 | 该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围；scope 归属存在边界，当前放在本 scope，但也可能属于：射频调谐与匹配子系统 | 确认 scope 归属与责任边界；确认该类比是否适用于当前模块机理、接口和责任范围；校准 O/D 与实际保护、测试和筛选能力是否匹配 | broader analogy | CAN400产品DFMEA.xlsx / 匀场单元 / row 6 |

## Suggested Actions

| Scope | Row key | Current RPN | Recommended action | Owner | Target date | Confirmation status | Reference type | Source case |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| 射频调谐与匹配子系统 | 射频调谐/匹配网络 / 大功率射频脉冲下电容器件或节点发生打火 (Arcing) | 300 | 增加高压节点的聚四氟乙烯 (PTFE) 绝缘灌封或充入绝缘气体 (如SF6或高压氮气)；电路板进行严格的去毛刺抛光工艺。 |  |  | draft | current module | CAN400产品DFMEA.xlsx / 调谐单元 / row 2 |
| 射频调谐与匹配子系统 | 射频线圈与焊接 / 射频线圈局部引入磁性杂质，导致磁化率异常 | 280 | 严格规范BOM，必须采用高纯度无磁焊料 (如特定配比的锡银铜 Sn-Ag-Cu)；后工序增加焊点的高灵敏度 SQUID 磁性初筛。 |  |  | draft | current module | CAN400产品DFMEA.xlsx / 调谐单元 / row 5 |
| 机械传动与限位子系统 | 硬件系统 (抗电磁干扰) / 电机转动丢步、编码器脉冲错乱或MCU死机 | 280 | 电机与编码器线缆必须使用双层编织屏蔽线，并在进入控制板处增加 LC 穿心电容滤波器；编码器信号采用RS422差分传输替代单端传输。 |  |  | needs expert confirmation | current module | CAN400产品DFMEA.xlsx / 调谐单元 / row 4 |
| 机械传动与限位子系统 | 探头机械传动 (硬限位) / 调谐杆被电机扭断或齿轮扫齿，限位保护未触发 | 270 | 绝对禁止纯依赖电流检测限位。增加机械滑动离合器 (Slip Clutch) 进行扭矩物理卸载；或在连杆末端增加微型光电开关作物理限位。 |  |  | draft | current module | CAN400产品DFMEA.xlsx / 调谐单元 / row 3 |
| 射频调谐与匹配子系统 | 物理连接 (背板与外部) / 背板连接器金手指磨损或受应力产生微断路 | 240 | 消除机械应力：弃用刚性硬插拔，改用具有盲插浮动容差能力的工业背板连接器（Floating Connector），并增加导向定位销。 |  |  | needs expert confirmation | direct family reference | CAN400产品DFMEA.xlsx / 收发机 / row 7 |
| 射频调谐与匹配子系统 | Z向梯度线圈 / 主线圈与屏蔽线圈产生的震动声学谐振 (Acoustic Ringing) | 210 | 采用环氧树脂真空含浸灌封 (VPI) 加固梯度线圈骨架，并在梯度线圈与射频线圈之间增加特种声学阻尼材料隔离震动。 |  |  | draft | current module | CAN400产品DFMEA.xlsx / 调谐单元 / row 6 |
| 射频调谐与匹配子系统 | 射频发射路径 (上变频与调幅) / 大衰减状态下实际衰减量不达标（射频泄漏） | 210 | 物理隔离：对衰减器链路分腔屏蔽-已实施（加装金属屏蔽罩）；电源走线增加多级LC滤波。-已实施 |  |  | needs expert confirmation | direct family reference | CAN400产品DFMEA.xlsx / 收发机 / row 2 |
| 射频调谐与匹配子系统 | 射频发射路径 (功放驱动) / 射频输出功率瞬间突波/失控超标 | 180 | 硬件级保护：在输出端增加定向耦合器+检波器，引入纯硬件的极速过功率切断开关（PIN二极管）。 |  |  | needs expert confirmation | direct family reference | CAN400产品DFMEA.xlsx / 收发机 / row 3 |
| EMC与算法控制子系统 | 软件调谐算法 / 搜索失败陷入死循环，或锁定到错误的“假陷波” (Cable Resonance) | 168 | 算法增加**“宽带全扫掠 (Full-span Sweep) 扫底”后备逻辑**；引入波形模式识别，判断陷波的Q值深度，排除电缆谐振的宽缓假波。 |  |  | draft | current module | CAN400产品DFMEA.xlsx / 调谐单元 / row 7 |
| 射频调谐与匹配子系统 | 射频接收路径 (微弱信号放大) / 接收链路非线性失真或提前饱和 | 160 | 增强动态范围：接收机前端增加极速限幅器（Limiter）-尝试过会引入额外的噪声；选用高P1dB和IP3的低噪声放大器（LNA）-已实施。 |  |  | needs expert confirmation | direct family reference | CAN400产品DFMEA.xlsx / 收发机 / row 4 |
| EMC与算法控制子系统 | 匀场算法与控制软件 / SDB板卡通信挂死 / 参数掉电丢失 | 112 | 增加通信看门狗（Watchdog）自动复位机制；SDB板载EEPROM，每次调节后自动备份当前最优Shimmap参数。 |  |  | needs expert confirmation | broader analogy | CAN400产品DFMEA.xlsx / 匀场单元 / row 6 |

## Source Trace

| Scope | Row key | Reference type | Source case |
| --- | --- | --- | --- |
| 射频调谐与匹配子系统 | 射频调谐/匹配网络 / 大功率射频脉冲下电容器件或节点发生打火 (Arcing) | current module | CAN400产品DFMEA.xlsx / 调谐单元 / row 2 |
| 射频调谐与匹配子系统 | 射频线圈与焊接 / 射频线圈局部引入磁性杂质，导致磁化率异常 | current module | CAN400产品DFMEA.xlsx / 调谐单元 / row 5 |
| 射频调谐与匹配子系统 | 物理连接 (背板与外部) / 背板连接器金手指磨损或受应力产生微断路 | direct family reference | CAN400产品DFMEA.xlsx / 收发机 / row 7 |
| 射频调谐与匹配子系统 | Z向梯度线圈 / 主线圈与屏蔽线圈产生的震动声学谐振 (Acoustic Ringing) | current module | CAN400产品DFMEA.xlsx / 调谐单元 / row 6 |
| 射频调谐与匹配子系统 | 射频发射路径 (上变频与调幅) / 大衰减状态下实际衰减量不达标（射频泄漏） | direct family reference | CAN400产品DFMEA.xlsx / 收发机 / row 2 |
| 射频调谐与匹配子系统 | 射频发射路径 (功放驱动) / 射频输出功率瞬间突波/失控超标 | direct family reference | CAN400产品DFMEA.xlsx / 收发机 / row 3 |
| 射频调谐与匹配子系统 | 射频接收路径 (微弱信号放大) / 接收链路非线性失真或提前饱和 | direct family reference | CAN400产品DFMEA.xlsx / 收发机 / row 4 |
| 机械传动与限位子系统 | 硬件系统 (抗电磁干扰) / 电机转动丢步、编码器脉冲错乱或MCU死机 | current module | CAN400产品DFMEA.xlsx / 调谐单元 / row 4 |
| 机械传动与限位子系统 | 探头机械传动 (硬限位) / 调谐杆被电机扭断或齿轮扫齿，限位保护未触发 | current module | CAN400产品DFMEA.xlsx / 调谐单元 / row 3 |
| EMC与算法控制子系统 | 软件调谐算法 / 搜索失败陷入死循环，或锁定到错误的“假陷波” (Cable Resonance) | current module | CAN400产品DFMEA.xlsx / 调谐单元 / row 7 |
| EMC与算法控制子系统 | 匀场算法与控制软件 / SDB板卡通信挂死 / 参数掉电丢失 | broader analogy | CAN400产品DFMEA.xlsx / 匀场单元 / row 6 |
