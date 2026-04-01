# 自动进样器 首版 DFMEA 草稿

- 生成方式: `draft_fmea_from_cases.py`
- 模块: `自动进样器`
- FMEA 类型: `DFMEA`
- 输入长度: `975` 字符

## 输入摘要

> 示例：我们目前正在设计一套用于 NMR 场景的自动进样器系统，目标是在储样、抓取、转运、进样和退样过程中，实现样品管及转子的自动搬运，减少人工干预，并保证样品在整个运动链路中的安全性、一致性和定位精度。该模块需要与储样筒、进样筒以及控制系统协同工作，既要完成机械运动，也要完成位置检测和气路控制。<br><br>自动进样器包含以下几个关键部分：<br><br>1、整体连接与供电：系统通过控制接口为各运动模块、传感器和执行器提供稳定供电与信号传输，要求设备在连续动作、震动和长时间运行下仍能保持可靠连接，不因接口松动导致中途停机、断联或动作失控。<br><br>2、竖直/水平气缸运动机构：自动进样器通过竖直和水平两个方向的气缸驱动样品完成抓取、平移和放置，要求滑块运动平稳，定位过程无明显晃动、偏摆或卡滞，能够精准把样品送到储样筒孔位、转盘孔位和进样筒交接位置。<br><br>3、位置调节与固定结构：系统在储样筒、夹爪、转盘和进样筒等多个交接点...

## Scope 规划

| Scope | 检索关键词 | 来源 | 命中数 | 说明 |
| --- | --- | --- | ---: | --- |
| 运动与抓取子系统 | 气缸 / 滑块 / 夹爪 / 储样筒 / 进样筒 / 转盘 / 样品管 / 扭簧 / 导轨 / 定位销 | auto | 7 | matched keywords: 气缸 / 滑块 / 夹爪 / 储样筒 / 进样筒 / 转盘 / 样品管 |
| 检测与气路控制子系统 | 检测 / 传感器 / 气路 / 气压 / 供电 / 接口 / 光电 / 对射 / 电磁阀 / 减压阀 | auto | 6 | matched keywords: 检测 / 传感器 / 气路 / 气压 / 供电 / 接口 |

## 运动与抓取子系统

| Scope | Analysis object | Function or requirement | Failure mode | Failure effect | S | Cause or mechanism | O | Current controls | D | RPN | Recommended actions | Confirmation status | Rating basis | Reference type | Source case |
| --- | --- | --- | --- | --- | ---: | --- | ---: | --- | ---: | ---: | --- | --- | --- | --- | --- |
| 运动与抓取子系统 | 竖直/水平气缸运动 | 精准驱动样品到达指定位置，滑块运行平稳，无左右或侧向晃动。 | 大气缸滑块左右晃动加剧，位置跑偏 |  | 8 | POM材质滑块长期摩擦磨损；仅靠顶丝补偿无法抵抗长期侧向力。 | 7 | 顶丝将POM滑块顶在气缸两侧防晃。 | 6 | 336 | 结构升级：不要让气缸承受侧向和导向力。增加外部高精度直线导轨（如THK/银泰），气缸仅作驱动源。 | draft | S=8 继承自历史案例的后果强度；O=7、D=6 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | CAN400产品DFMEA.xlsx / 自动进样器 / row 3 |
| 运动与抓取子系统 | 储样筒防掉落机构 | 塞子在扭簧作用下可靠卡住样品管防掉落，在针型气缸驱动下顺畅退回放行。 | 跷跷板扭簧疲劳断裂或弹性衰减 |  | 9 | 弹簧长期高频次受交变应力导致金属疲劳。 | 4 | 针型气缸动作控制（但无扭簧状态检测）。 | 8 | 288 | 增加闭环检测：更换高疲劳寿命弹簧；在跷跷板塞子侧增加一个微型光电或接近开关，直接检测“塞子是否到位闭合”。 | draft | S=9 继承自历史案例的后果强度；O=4、D=8 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | CAN400产品DFMEA.xlsx / 自动进样器 / row 5 |
| 运动与抓取子系统 | 夹爪抓取模块 | 通过PEEK材质V型槽可靠夹持样品管及转子，在升降/平移中不滑脱、不掉落。 | 气爪抓取力不足或PEEK材质磨损打滑 |  | 8 | 气路气压波动；PEEK材料表面长期摩擦变光滑。 | 4 | 坦克链供气；V型结构件设计。 | 5 | 160 | 增加反馈与防滑：V型槽内贴敷高摩擦系数且不掉屑的弹性材料；气源入口增加数字压力开关，气压低时报警并禁止动作。 | draft | S=8 继承自历史案例的后果强度；O=4、D=5 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | CAN400产品DFMEA.xlsx / 自动进样器 / row 6 |
| 运动与抓取子系统 | 气动及筒体组件 | 样品管平稳上升与下降 | 样品管在进样筒内卡阻，无法升降 | 后工序（进样流程）：流程中断，无法将样品送达测试区。 | 7 | 1. 进样筒内壁粗糙或加工变形； | 4 | 1. 图纸要求气源洁净； | 5 | 140 | 1. 图纸明确进样筒内壁的光洁度(Ra)和直线度公差； | needs expert confirmation | S=7 继承自历史案例的后果强度；O=4、D=5 继承自成品 DFMEA，但仍需结合本企业标尺校准；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | CAN400产品DFMEA.xlsx / 进样筒 / row 7 |
| 运动与抓取子系统 | 气动及筒体组件 | 样品管平稳下降，落至匀场线圈顶部锥孔处 | 样品管下降速度过快/直接砸底 | 客户：设备宕机，需支付高昂维修费。 |  | 2. 进样筒内壁气道漏气； |  |  |  |  | 2. 软件增加“软着陆”缓降控制算法。 | needs expert confirmation | S 未在源案例中明确给出；O/D 未完整继承，需专家补齐评分依据；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | CAN400产品DFMEA.xlsx / 进样筒 / row 5 |
| 运动与抓取子系统 | 气动及筒体组件 | 样品管平稳上升与下降 | 样品管在进样筒内卡阻，无法升降 | 客户：无法进行后续测试实验。 |  | 2. 气源不洁净导致灰尘/杂质堆积；<br>3. 气流推力不足。 |  | 2. 机加工常规公差控制。 |  |  | 2. 建议客户增加气源前端的精密过滤装置。 | needs expert confirmation | S 未在源案例中明确给出；O/D 未完整继承，需专家补齐评分依据；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | CAN400产品DFMEA.xlsx / 进样筒 / row 8; CAN400产品DFMEA.xlsx / 进样筒 / row 9 |
| 运动与抓取子系统 | 转子与气动组件 | 带动样品管旋转 | 样品管完全不旋转 | 客户：测试结果无效。 |  | 2. 转子与进样筒卡死。 |  |  |  |  |  | needs expert confirmation | S 未在源案例中明确给出；O/D 未完整继承，需专家补齐评分依据；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | CAN400产品DFMEA.xlsx / 进样筒 / row 14 |

## 检测与气路控制子系统

| Scope | Analysis object | Function or requirement | Failure mode | Failure effect | S | Cause or mechanism | O | Current controls | D | RPN | Recommended actions | Confirmation status | Rating basis | Reference type | Source case |
| --- | --- | --- | --- | --- | ---: | --- | ---: | --- | ---: | ---: | --- | --- | --- | --- | --- |
| 检测与气路控制子系统 | 整体连接与供电 | 提供稳定的电力与控制信号传输，确保各运动模块与传感器的正常通讯与供电。 | Type-C接口松动或接触不良 |  | 9 | 设备运行时的持续震动导致接口物理松脱。 | 5 | 无特殊防脱落设计。 | 5 | 225 | 更改接口标准：废弃Type-C，改用带螺纹锁紧的工业航空插头（如M8/M12）或带螺丝固定的端子排。 | draft | S=9 继承自历史案例的后果强度；O=5、D=5 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | CAN400产品DFMEA.xlsx / 自动进样器 / row 2 |
| 检测与气路控制子系统 | 进/退样气路控制 | 进样提供缓冲气防止自由落体；退样提供适宜抬升气将转子安全吹至储样筒。 | 退样时底部抬升吹气气压过大/过小 |  | 7 | 气源总压波动；快拆接头或深小孔气阻变化。 | 4 | 电磁阀控制，定制化气路分割。 | 5 | 140 | 增加精密调压与缓冲：在抬升气路上单独增加高精度减压阀；储样筒顶部增加物理柔性缓冲垫（如硅胶垫）。 | draft | S=7 继承自历史案例的后果强度；O=4、D=5 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | CAN400产品DFMEA.xlsx / 自动进样器 / row 8 |
| 检测与气路控制子系统 | 气动及筒体组件 | 样品管平稳下降，落至匀场线圈顶部锥孔处 | 样品管下降速度过快/直接砸底 | 后工序（探头检测）：样品管破裂导致样品泄漏，严重污染甚至损坏昂贵的探头。 | 8 | 1. 缓冲气罐气压不足或失效； | 4 | 气路设计中引入了缓冲气罐防止冲击。 | 4 | 128 | 1. 增加气压传感器实时监控气流压力，异常时GLCB触发闭锁； | needs expert confirmation | S=8 继承自历史案例的后果强度；O=4、D=4 继承自成品 DFMEA，但仍需结合本企业标尺校准；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | CAN400产品DFMEA.xlsx / 进样筒 / row 4 |
| 检测与气路控制子系统 | 转盘检测模块 | 准确检测转盘4圈72个孔位内样品管的有无情况，无漏报或误报。 | 底部光电传感器误判样品有无 |  | 7 | 玻璃样品管透明度高，反光/折射导致光电开关失效；底部孔体积灰。 | 5 | 发射接收型对射光电。 | 3 | 105 | 优化传感器：选用专门针对透明物体的同轴偏振反射传感器，或加入超声波传感器辅助判断；增加定期清洁维护规程。 | draft | S=7 继承自历史案例的后果强度；O=5、D=3 继承自成品 DFMEA，但仍需结合本企业标尺校准 | current module | CAN400产品DFMEA.xlsx / 自动进样器 / row 7 |
| 检测与气路控制子系统 | 光电系统 (传感器) | 准确探测样品管/转子位置及转速 | 传感器信号丢失或误报 | 后工序（动作执行）：GLCB接收错误信号，导致提前切断缓冲气或错误喷气。 | 8 | 1. 光纤头被灰尘遮挡； | 3 | 采用机加工光纤传输信号，避免电气干扰。 | 4 | 96 | 1. 进样筒顶部和底部的光纤探头处增加防尘结构设计； | needs expert confirmation | S=8 继承自历史案例的后果强度；O=3、D=4 继承自成品 DFMEA，但仍需结合本企业标尺校准；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | CAN400产品DFMEA.xlsx / 进样筒 / row 15 |
| 检测与气路控制子系统 | 光电系统 (传感器) | 准确探测样品管/转子位置及转速 | 传感器信号丢失或误报 | 客户：可能引发“飞管”或砸碎管的安全隐患。 |  | 2. 机加工光纤内部断裂导致衰减；<br>3. 环境光干扰。 |  |  |  |  | 2. 软件增加防呆逻辑（如：超时未检测到信号自动切入安全状态）。 | needs expert confirmation | S 未在源案例中明确给出；O/D 未完整继承，需专家补齐评分依据；本行属于 direct family reference，仅建议作为补缺参考 | direct family reference | CAN400产品DFMEA.xlsx / 进样筒 / row 16; CAN400产品DFMEA.xlsx / 进样筒 / row 17 |

## Top Risks

| Scope | Failure mode | Current RPN | Why it matters | First action candidate | Reference type |
| --- | --- | ---: | --- | --- | --- |
| 运动与抓取子系统 | 大气缸滑块左右晃动加剧，位置跑偏 | 336 |  | 结构升级：不要让气缸承受侧向和导向力。增加外部高精度直线导轨（如THK/银泰），气缸仅作驱动源。 | current module |
| 运动与抓取子系统 | 跷跷板扭簧疲劳断裂或弹性衰减 | 288 |  | 增加闭环检测：更换高疲劳寿命弹簧；在跷跷板塞子侧增加一个微型光电或接近开关，直接检测“塞子是否到位闭合”。 | current module |
| 检测与气路控制子系统 | Type-C接口松动或接触不良 | 225 |  | 更改接口标准：废弃Type-C，改用带螺纹锁紧的工业航空插头（如M8/M12）或带螺丝固定的端子排。 | current module |
| 运动与抓取子系统 | 气爪抓取力不足或PEEK材质磨损打滑 | 160 |  | 增加反馈与防滑：V型槽内贴敷高摩擦系数且不掉屑的弹性材料；气源入口增加数字压力开关，气压低时报警并禁止动作。 | current module |
| 检测与气路控制子系统 | 退样时底部抬升吹气气压过大/过小 | 140 |  | 增加精密调压与缓冲：在抬升气路上单独增加高精度减压阀；储样筒顶部增加物理柔性缓冲垫（如硅胶垫）。 | current module |
| 运动与抓取子系统 | 样品管在进样筒内卡阻，无法升降 | 140 | 后工序（进样流程）：流程中断，无法将样品送达测试区。 | 1. 图纸明确进样筒内壁的光洁度(Ra)和直线度公差； | direct family reference |
| 检测与气路控制子系统 | 样品管下降速度过快/直接砸底 | 128 | 后工序（探头检测）：样品管破裂导致样品泄漏，严重污染甚至损坏昂贵的探头。 | 1. 增加气压传感器实时监控气流压力，异常时GLCB触发闭锁； | direct family reference |
| 检测与气路控制子系统 | 底部光电传感器误判样品有无 | 105 |  | 优化传感器：选用专门针对透明物体的同轴偏振反射传感器，或加入超声波传感器辅助判断；增加定期清洁维护规程。 | current module |

## Rows Needing Confirmation

| Scope | Row key | Why confirmation is needed | Suggested reviewer focus | Reference type | Source case |
| --- | --- | --- | --- | --- | --- |
| 运动与抓取子系统 | 气动及筒体组件 / 样品管在进样筒内卡阻，无法升降 | 该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围 | 确认该类比是否适用于当前模块机理、接口和责任范围；校准 O/D 与实际保护、测试和筛选能力是否匹配 | direct family reference | CAN400产品DFMEA.xlsx / 进样筒 / row 7 |
| 运动与抓取子系统 | 气动及筒体组件 / 样品管下降速度过快/直接砸底 | 源案例缺少完整评分字段：S/O/D；该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围 | 确认该类比是否适用于当前模块机理、接口和责任范围；补齐 O/D 与现行检测控制 | direct family reference | CAN400产品DFMEA.xlsx / 进样筒 / row 5 |
| 运动与抓取子系统 | 气动及筒体组件 / 样品管在进样筒内卡阻，无法升降 | 源案例缺少完整评分字段：S/O/D；该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围 | 确认该类比是否适用于当前模块机理、接口和责任范围；补齐 O/D 与现行检测控制 | direct family reference | CAN400产品DFMEA.xlsx / 进样筒 / row 8; CAN400产品DFMEA.xlsx / 进样筒 / row 9 |
| 运动与抓取子系统 | 转子与气动组件 / 样品管完全不旋转 | 源案例缺少完整评分字段：S/O/D；该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围 | 确认该类比是否适用于当前模块机理、接口和责任范围；补齐 O/D 与现行检测控制 | direct family reference | CAN400产品DFMEA.xlsx / 进样筒 / row 14 |
| 检测与气路控制子系统 | 气动及筒体组件 / 样品管下降速度过快/直接砸底 | 该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围；scope 归属存在边界，当前放在本 scope，但也可能属于：运动与抓取子系统 | 确认 scope 归属与责任边界；确认该类比是否适用于当前模块机理、接口和责任范围；校准 O/D 与实际保护、测试和筛选能力是否匹配 | direct family reference | CAN400产品DFMEA.xlsx / 进样筒 / row 4 |
| 检测与气路控制子系统 | 光电系统 (传感器) / 传感器信号丢失或误报 | 该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围 | 确认该类比是否适用于当前模块机理、接口和责任范围；校准 O/D 与实际保护、测试和筛选能力是否匹配 | direct family reference | CAN400产品DFMEA.xlsx / 进样筒 / row 15 |
| 检测与气路控制子系统 | 光电系统 (传感器) / 传感器信号丢失或误报 | 源案例缺少完整评分字段：S/O/D；该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围 | 确认该类比是否适用于当前模块机理、接口和责任范围；补齐 O/D 与现行检测控制 | direct family reference | CAN400产品DFMEA.xlsx / 进样筒 / row 16; CAN400产品DFMEA.xlsx / 进样筒 / row 17 |

## Suggested Actions

| Scope | Row key | Current RPN | Recommended action | Owner | Target date | Confirmation status | Reference type | Source case |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| 运动与抓取子系统 | 竖直/水平气缸运动 / 大气缸滑块左右晃动加剧，位置跑偏 | 336 | 结构升级：不要让气缸承受侧向和导向力。增加外部高精度直线导轨（如THK/银泰），气缸仅作驱动源。 |  |  | draft | current module | CAN400产品DFMEA.xlsx / 自动进样器 / row 3 |
| 运动与抓取子系统 | 储样筒防掉落机构 / 跷跷板扭簧疲劳断裂或弹性衰减 | 288 | 增加闭环检测：更换高疲劳寿命弹簧；在跷跷板塞子侧增加一个微型光电或接近开关，直接检测“塞子是否到位闭合”。 |  |  | draft | current module | CAN400产品DFMEA.xlsx / 自动进样器 / row 5 |
| 检测与气路控制子系统 | 整体连接与供电 / Type-C接口松动或接触不良 | 225 | 更改接口标准：废弃Type-C，改用带螺纹锁紧的工业航空插头（如M8/M12）或带螺丝固定的端子排。 |  |  | draft | current module | CAN400产品DFMEA.xlsx / 自动进样器 / row 2 |
| 运动与抓取子系统 | 夹爪抓取模块 / 气爪抓取力不足或PEEK材质磨损打滑 | 160 | 增加反馈与防滑：V型槽内贴敷高摩擦系数且不掉屑的弹性材料；气源入口增加数字压力开关，气压低时报警并禁止动作。 |  |  | draft | current module | CAN400产品DFMEA.xlsx / 自动进样器 / row 6 |
| 检测与气路控制子系统 | 进/退样气路控制 / 退样时底部抬升吹气气压过大/过小 | 140 | 增加精密调压与缓冲：在抬升气路上单独增加高精度减压阀；储样筒顶部增加物理柔性缓冲垫（如硅胶垫）。 |  |  | draft | current module | CAN400产品DFMEA.xlsx / 自动进样器 / row 8 |
| 运动与抓取子系统 | 气动及筒体组件 / 样品管在进样筒内卡阻，无法升降 | 140 | 1. 图纸明确进样筒内壁的光洁度(Ra)和直线度公差； |  |  | needs expert confirmation | direct family reference | CAN400产品DFMEA.xlsx / 进样筒 / row 7 |
| 检测与气路控制子系统 | 气动及筒体组件 / 样品管下降速度过快/直接砸底 | 128 | 1. 增加气压传感器实时监控气流压力，异常时GLCB触发闭锁； |  |  | needs expert confirmation | direct family reference | CAN400产品DFMEA.xlsx / 进样筒 / row 4 |
| 检测与气路控制子系统 | 转盘检测模块 / 底部光电传感器误判样品有无 | 105 | 优化传感器：选用专门针对透明物体的同轴偏振反射传感器，或加入超声波传感器辅助判断；增加定期清洁维护规程。 |  |  | draft | current module | CAN400产品DFMEA.xlsx / 自动进样器 / row 7 |
| 检测与气路控制子系统 | 光电系统 (传感器) / 传感器信号丢失或误报 | 96 | 1. 进样筒顶部和底部的光纤探头处增加防尘结构设计； |  |  | needs expert confirmation | direct family reference | CAN400产品DFMEA.xlsx / 进样筒 / row 15 |
| 检测与气路控制子系统 | 光电系统 (传感器) / 传感器信号丢失或误报 |  | 2. 软件增加防呆逻辑（如：超时未检测到信号自动切入安全状态）。 |  |  | needs expert confirmation | direct family reference | CAN400产品DFMEA.xlsx / 进样筒 / row 16; CAN400产品DFMEA.xlsx / 进样筒 / row 17 |
| 运动与抓取子系统 | 气动及筒体组件 / 样品管下降速度过快/直接砸底 |  | 2. 软件增加“软着陆”缓降控制算法。 |  |  | needs expert confirmation | direct family reference | CAN400产品DFMEA.xlsx / 进样筒 / row 5 |
| 运动与抓取子系统 | 气动及筒体组件 / 样品管在进样筒内卡阻，无法升降 |  | 2. 建议客户增加气源前端的精密过滤装置。 |  |  | needs expert confirmation | direct family reference | CAN400产品DFMEA.xlsx / 进样筒 / row 8; CAN400产品DFMEA.xlsx / 进样筒 / row 9 |

## Source Trace

| Scope | Row key | Reference type | Source case |
| --- | --- | --- | --- |
| 运动与抓取子系统 | 竖直/水平气缸运动 / 大气缸滑块左右晃动加剧，位置跑偏 | current module | CAN400产品DFMEA.xlsx / 自动进样器 / row 3 |
| 运动与抓取子系统 | 储样筒防掉落机构 / 跷跷板扭簧疲劳断裂或弹性衰减 | current module | CAN400产品DFMEA.xlsx / 自动进样器 / row 5 |
| 运动与抓取子系统 | 夹爪抓取模块 / 气爪抓取力不足或PEEK材质磨损打滑 | current module | CAN400产品DFMEA.xlsx / 自动进样器 / row 6 |
| 运动与抓取子系统 | 气动及筒体组件 / 样品管在进样筒内卡阻，无法升降 | direct family reference | CAN400产品DFMEA.xlsx / 进样筒 / row 7 |
| 运动与抓取子系统 | 气动及筒体组件 / 样品管下降速度过快/直接砸底 | direct family reference | CAN400产品DFMEA.xlsx / 进样筒 / row 5 |
| 运动与抓取子系统 | 气动及筒体组件 / 样品管在进样筒内卡阻，无法升降 | direct family reference | CAN400产品DFMEA.xlsx / 进样筒 / row 8; CAN400产品DFMEA.xlsx / 进样筒 / row 9 |
| 运动与抓取子系统 | 转子与气动组件 / 样品管完全不旋转 | direct family reference | CAN400产品DFMEA.xlsx / 进样筒 / row 14 |
| 检测与气路控制子系统 | 整体连接与供电 / Type-C接口松动或接触不良 | current module | CAN400产品DFMEA.xlsx / 自动进样器 / row 2 |
| 检测与气路控制子系统 | 进/退样气路控制 / 退样时底部抬升吹气气压过大/过小 | current module | CAN400产品DFMEA.xlsx / 自动进样器 / row 8 |
| 检测与气路控制子系统 | 气动及筒体组件 / 样品管下降速度过快/直接砸底 | direct family reference | CAN400产品DFMEA.xlsx / 进样筒 / row 4 |
| 检测与气路控制子系统 | 转盘检测模块 / 底部光电传感器误判样品有无 | current module | CAN400产品DFMEA.xlsx / 自动进样器 / row 7 |
| 检测与气路控制子系统 | 光电系统 (传感器) / 传感器信号丢失或误报 | direct family reference | CAN400产品DFMEA.xlsx / 进样筒 / row 15 |
| 检测与气路控制子系统 | 光电系统 (传感器) / 传感器信号丢失或误报 | direct family reference | CAN400产品DFMEA.xlsx / 进样筒 / row 16; CAN400产品DFMEA.xlsx / 进样筒 / row 17 |
