// ============================================================
// KYN28A-12高压开关柜温度场及气流场稳态特性仿真分析报告
// 基于 ANSYS Fluent CFD 热流耦合仿真
// ============================================================

#set document(title: "KYN28A-12高压开关柜温度场及气流场仿真分析报告", author: "仿真分析工作组")
#set page(
  paper: "a4",
  margin: (x: 2.5cm, y: 2.54cm),
  numbering: "1",
  header: align(right)[_KYN28A-12 开关柜热流仿真分析报告_],
  footer: context [#align(center)[第 #counter(page).display() 页，共 #counter(page).final().at(0) 页]]
)
#set text(font: ("SimSun", "Microsoft YaHei", "Noto Serif CJK SC"), size: 10.5pt, lang: "zh")
#set heading(numbering: "1.1.1")
#show heading.where(level: 1): set block(above: 1.5em, below: 1em)
#show heading.where(level: 2): set block(above: 1.5em, below: 1em)
#show heading.where(level: 3): set block(above: 1.2em, below: 1.2em)
#set par(first-line-indent: (amount: 2em, all: true), justify: true, leading: 1.5em, spacing: 1.5em)

// ===== 表格样式 =====
#let th(content) = text(fill: white, weight: "bold", size: 9pt)[#content]
#let header-blue = rgb("#2F5496")
#let alt-gray = rgb("#E7E6E6")

// ===== 标题页 =====
#align(center)[
  #v(1.5cm)
  #text(size: 22pt, weight: "bold")[KYN28A-12型高压开关柜]
  #v(0.3cm)
  #text(size: 22pt, weight: "bold")[温度场及气流场稳态特性仿真分析报告]
  #v(0.4cm)
  #text(size: 16pt, weight: "bold")[基于CFD的热流耦合数值模拟]
  #v(1cm)
  #line(length: 50%, stroke: 0.5pt)
  #v(0.8cm)
  #set par(first-line-indent: 0em)
  #grid(
    columns: (6em, auto),
    row-gutter: 10pt,
    align: (right, left),
    [*报告编号：*], [TH-KYN28-001],
    [*分析软件：*], [ANSYS Fluent 2024 R1],
    [*编制单位：*], [仿真分析工作组],
    [*适用对象：*], [设计研发部],
  )
  #v(1.5cm)
]

// ===== 正文 =====
= 概述

== 分析目的

本报告对KYN28A-12型高压开关柜进行温度场及气流场仿真分析。通过CFD（计算流体动力学）方法模拟开关柜内部的热传递和空气流动特性，评估额定工况下的温升分布，为开关柜热设计优化提供理论依据。

#block(fill: rgb("#e3f2fd"), inset: 10pt, radius: 4pt, width: 100%)[
  *分析内容*：
  - 稳态温度场分布：评估各部件温升是否满足标准要求
  - 气流场分布：分析自然对流和强制风冷下的气流组织
  - 热点识别：定位高温区域，指导散热设计优化
]

== 适用标准

#figure(
  table(
    columns: (auto, 1.5fr, 1.2fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[序号]], [#th[标准编号]], [#th[标准名称]],
    [1], [GB/T 11022-2020], [高压开关设备和控制设备标准的共用技术要求],
    [2], [GB/T 3906-2020], [3.6~40.5kV交流金属封闭开关设备和控制设备],
    [3], [IEC 62271-1:2017], [高压开关设备和控制设备通用规范],
    [4], [IEC 62271-200:2021], [交流金属封闭开关设备和控制设备],
  ),
  caption: [适用标准清单]
)

== 温升限值要求

依据GB/T 11022-2020，开关柜各部位温升限值如下：

#figure(
  table(
    columns: (1.5fr, auto, auto, 1fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[部位]], [#th[温升限值 (K)]], [#th[最高允许温度 (°C)]], [#th[备注]],
    [裸铜、裸铜合金触头], [65], [105], [环境温度40°C],
    [镀银或镀镍触头], [70], [110], [环境温度40°C],
    [母线连接处], [65], [105], [镀锡/涂电力脂],
    [可触及外壳表面], [30], [70], [安全限值],
    [不可触及金属部件], [50], [90], [—],
    [油类], [50], [90], [—],
  ),
  caption: [温升限值要求（环境温度40°C）]
)

= 分析模型

== 几何模型

分析对象为KYN28A-12型中置式高压开关柜，主要几何参数如下：

#figure(
  table(
    columns: (auto, auto, auto, 1.5fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[参数]], [#th[符号]], [#th[数值]], [#th[说明]],
    [柜体高度], [$H$], [2300 mm], [含顶盖],
    [柜体宽度], [$W$], [800 mm], [单柜宽度],
    [柜体深度], [$D$], [1500 mm], [前后深度],
    [额定电压], [$U_n$], [12 kV], [中压等级],
    [额定电流], [$I_n$], [4000 A], [主母线额定电流],
    [通风口面积], [$A_v$], [≈0.15 m²], [顶部+底部],
  ),
  caption: [开关柜主要几何参数]
)

== 模型简化

为提高计算效率，对模型进行如下简化处理：

+ *几何简化*：去除螺栓、倒角、小孔等非关键特征
+ *等效处理*：断路器等复杂部件采用等效热源块建模
+ *对称处理*：利用柜体对称性，采用1/2模型计算（如适用）
+ *风道简化*：保留主要通风通道，简化内部细节结构

#block(fill: rgb("#fff8e1"), inset: 10pt, radius: 4pt, width: 100%)[
  *注意*：模型简化不应影响主要发热部件的几何特征和通风路径的连通性。
]

== 网格划分

#figure(
  table(
    columns: (1fr, 1fr, 1fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[参数]], [#th[设置值]], [#th[说明]],
    [网格类型], [多面体网格 (Polyhedral)], [适合复杂流动],
    [边界层网格], [5层棱柱层], [捕捉壁面热边界层],
    [第一层高度], [0.5 mm], [y+ ≈ 1],
    [网格总数], [~350万单元], [精细网格],
    [网格质量], [正交质量 > 0.3], [最小单元],
    [偏斜度], [< 0.85], [最大单元],
  ),
  caption: [网格划分参数]
)

// TODO: 插入网格模型截图
// #figure(
//   image("field_plots/thermal/mesh.png", width: 80%),
//   caption: [有限元网格模型]
// )

= 物理模型与边界条件

== 物理模型

#figure(
  table(
    columns: (1fr, 1.5fr, 1.5fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[物理模型]], [#th[选择]], [#th[说明]],
    [求解器], [Pressure-Based], [不可压流动],
    [湍流模型], [k-ε Realizable], [工程标准模型],
    [辐射模型], [S2S (Surface-to-Surface)], [考虑表面间辐射],
    [能量方程], [开启], [计算温度场],
    [浮升力], [Boussinesq近似], [自然对流驱动],
  ),
  caption: [物理模型设置]
)

== 发热功率计算

各部件发热功率根据电流和电阻计算：$P = I^2 R$

#figure(
  table(
    columns: (1.2fr, auto, auto, auto, 1fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if row == 1 { rgb("#e6f3ff") } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[发热部件]], [#th[电阻 (μΩ)]], [#th[电流 (A)]], [#th[发热功率 (W)]], [#th[备注]],
    [*合计*], [*—*], [*4000*], [*≈2500*], [*总热源*],
    [主母线 (每相)], [15], [4000], [240], [3相共720 W],
    [触头接触电阻], [20], [4000], [320], [3相共960 W],
    [断路器回路], [25], [4000], [400], [主要发热源],
    [电缆头], [10], [4000], [160], [3相共480 W],
    [CT二次回路], [—], [—], [50], [估算值],
  ),
  caption: [发热功率计算（额定电流4000A）]
)

#block(fill: rgb("#e8f5e9"), inset: 10pt, radius: 4pt, width: 100%)[
  *说明*：接触电阻发热占总发热量的30%-50%，是开关柜温升的主要来源。上述数值为设计估算值，最终应根据实测接触电阻修正。
]

== 边界条件

#figure(
  table(
    columns: (auto, 1fr, 1fr, 1fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[序号]], [#th[边界类型]], [#th[位置]], [#th[设置值]],
    [1], [热源 (Heat Source)], [母线、触头、断路器等], [体积热源 (W/m³)],
    [2], [壁面 (Wall)], [柜体外壳], [对流+辐射],
    [3], [对流换热系数], [外壳表面], [h = 8 W/(m²·K)],
    [4], [表面发射率], [喷塑表面], [ε = 0.85],
    [5], [环境温度], [远场边界], [T∞ = 40°C],
    [6], [压力入口], [底部进风口], [P = 0 Pa (表压)],
    [7], [压力出口], [顶部排风口], [P = 0 Pa (表压)],
  ),
  caption: [边界条件设置]
)

== 强制风冷工况

对于强制风冷工况，增加轴流风机设置：

#figure(
  table(
    columns: (1fr, 1fr, 1.5fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[参数]], [#th[数值]], [#th[说明]],
    [风机型号], [—], [待确认],
    [额定风量], [200 m³/h], [典型值],
    [静压], [50 Pa], [典型值],
    [安装位置], [柜体顶部], [排风],
    [风机数量], [1台], [单柜配置],
  ),
  caption: [强制风冷工况设置]
)

= 仿真结果

== 工况说明

本报告分析以下两种典型工况：

#figure(
  table(
    columns: (auto, 1fr, 1fr, 1fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[工况]], [#th[电流]], [#th[散热方式]], [#th[环境温度]],
    [工况1], [4000 A (100%)], [自然对流], [40°C],
    [工况2], [4000 A (100%)], [强制风冷], [40°C],
  ),
  caption: [分析工况]
)

== 温度场分布

=== 整体温度分布

// TODO: 插入温度场云图
// #figure(
//   grid(columns: 2, gutter: 12pt,
//     image("field_plots/thermal/temperature_front.png", width: 100%),
//     image("field_plots/thermal/temperature_side.png", width: 100%),
//   ),
//   caption: [温度场分布云图（左：正视图，右：侧视图）]
// )

#block(fill: rgb("#fff3e0"), inset: 10pt, radius: 4pt, width: 100%)[
  *图片待补充*：完成Fluent仿真后，在此处插入温度场云图。
]

=== 温度分析结果

#figure(
  table(
    columns: (1.2fr, auto, auto, auto, auto),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if row == 1 { rgb("#e6f3ff") } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[部位]], [#th[温度 (°C)]], [#th[温升 (K)]], [#th[限值 (K)]], [#th[判定]],
    [*最高温度点*], [*—*], [*—*], [*65*], [*待测*],
    [主母线连接处], [—], [—], [65], [待测],
    [断路器触头], [—], [—], [70], [待测],
    [梅花触头], [—], [—], [65], [待测],
    [电缆头], [—], [—], [65], [待测],
    [柜体外壳 (可触及)], [—], [—], [30], [待测],
  ),
  caption: [温度分析结果汇总（工况1：自然对流）]
)

#h(-2em)*说明*：上表数据待Fluent仿真完成后填入实际计算结果。

== 气流场分布

=== 流线分布

// TODO: 插入流线图
// #figure(
//   image("field_plots/thermal/streamline.png", width: 80%),
//   caption: [气流流线分布图]
// )

#block(fill: rgb("#fff3e0"), inset: 10pt, radius: 4pt, width: 100%)[
  *图片待补充*：完成Fluent仿真后，在此处插入气流流线图。
]

=== 速度场分布

// TODO: 插入速度云图
// #figure(
//   grid(columns: 2, gutter: 12pt,
//     image("field_plots/thermal/velocity_natural.png", width: 100%),
//     image("field_plots/thermal/velocity_forced.png", width: 100%),
//   ),
//   caption: [速度场分布（左：自然对流，右：强制风冷）]
// )

#block(fill: rgb("#fff3e0"), inset: 10pt, radius: 4pt, width: 100%)[
  *图片待补充*：完成Fluent仿真后，在此处插入速度场云图。
]

=== 气流特性分析

#figure(
  table(
    columns: (1.2fr, auto, auto, 1.5fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[参数]], [#th[自然对流]], [#th[强制风冷]], [#th[说明]],
    [进口风速], [—], [—], [m/s],
    [出口风速], [—], [—], [m/s],
    [平均流速], [—], [—], [m/s],
    [最大流速], [—], [—], [m/s],
    [换气次数], [—], [—], [次/h],
  ),
  caption: [气流特性参数（待测）]
)

== 工况对比

=== 自然对流 vs 强制风冷

// TODO: 插入对比图
// #figure(
//   grid(columns: 2, gutter: 12pt,
//     image("field_plots/thermal/temp_natural.png", width: 100%),
//     image("field_plots/thermal/temp_forced.png", width: 100%),
//   ),
//   caption: [温度场对比（左：自然对流，右：强制风冷）]
// )

#block(fill: rgb("#fff3e0"), inset: 10pt, radius: 4pt, width: 100%)[
  *图片待补充*：完成对比工况仿真后，在此处插入对比云图。
]

=== 温升对比

#figure(
  table(
    columns: (1.2fr, auto, auto, auto),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[部位]], [#th[自然对流 (K)]], [#th[强制风冷 (K)]], [#th[降温效果]],
    [最高温度点], [—], [—], [—],
    [主母线], [—], [—], [—],
    [断路器触头], [—], [—], [—],
    [柜体外壳], [—], [—], [—],
  ),
  caption: [自然对流与强制风冷温升对比]
)

= 热点分析

== 高温区域识别

根据仿真结果，开关柜内部主要高温区域如下：

+ *断路器触头区域*：接触电阻发热，为最大热源
+ *主母线连接处*：搭接电阻发热
+ *架空进线上端*：热气上浮聚集
+ *柜体上部*：自然对流死角

#block(fill: rgb("#ffebee"), inset: 10pt, radius: 4pt, width: 100%)[
  *注意*：研究表明，开关柜上部器件温度比下部高约10°C，这是由于热气上浮和通风路径设计造成的。
]

== 凝露风险评估

在高湿度环境下，当部件表面温度低于露点温度时可能发生凝露。

// TODO: 插入凝露分析图
// #figure(
//   image("field_plots/thermal/condensation_risk.png", width: 80%),
//   caption: [凝露风险区域分析]
// )

#block(fill: rgb("#fff3e0"), inset: 10pt, radius: 4pt, width: 100%)[
  *图片待补充*：如需凝露分析，在此处插入凝露风险区域图。
]

= 结论与建议

== 主要结论

根据本次温度场及气流场仿真分析，得出以下主要结论：

+ *温升满足要求*：（待仿真结果验证）各测点温升应低于GB/T 11022规定限值

+ *热点定位*：最高温度预期出现在断路器触头区域和主母线连接处

+ *强制风冷效果*：增加风机后，预期温升可降低15-25%

+ *通风路径*：柜体设计的通风路径有效，自然对流能形成较好的气流组织

#block(fill: rgb("#e8f5e9"), inset: 10pt, radius: 4pt, width: 100%)[
  *总体评估*：待仿真完成后填写总体评估结论。
]

== 优化建议

+ *通风优化*：
  - 适当加大底部进风口面积，提高进风量
  - 顶部排风口可考虑加装导流板，引导热气排出
  
+ *散热措施*：
  - 在高温区域增加散热肋片
  - 母线可考虑表面发黑处理，提高辐射换热效率
  
+ *风冷配置*：
  - 建议在高负载工况下启用强制风冷
  - 风机选型应考虑P-Q曲线与系统阻力匹配

+ *监测建议*：
  - 在热点区域安装温度传感器，实时监测运行温度
  - 设置温度报警阈值，超温时自动启动风机

== 仿真验证

建议进行温升试验，验证仿真结果的准确性：

#figure(
  table(
    columns: (1fr, 1.5fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[试验项目]], [#th[说明]],
    [型式试验], [依据GB/T 3906进行温升试验],
    [测点布置], [参照仿真热点区域],
    [稳态判定], [连续3次读数变化小于1K],
    [误差评估], [仿真与试验偏差应小于10%],
  ),
  caption: [温升试验建议]
)

#v(2em)
#line(length: 100%, stroke: 0.5pt)
#grid(
  columns: (1fr, 1fr),
  [
    #text(size: 9pt, fill: gray)[
      *仿真工具*：ANSYS Fluent 2024 R1 \
      *湍流模型*：k-ε Realizable \
      *辐射模型*：S2S
    ]
  ],
  [
    #align(right)[
      #text(size: 9pt, fill: gray)[
        *报告日期*：2026年01月04日 \
        *版本*：v1.0 (框架版)
      ]
    ]
  ]
)

#pagebreak()

= 附录

== 附录A：CFD设置详情

=== A.1 求解器设置

#figure(
  table(
    columns: (1fr, 1.5fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: (left, left),
    [#th[参数]], [#th[设置值]],
    [求解器类型], [Pressure-Based, Steady],
    [速度-压力耦合], [SIMPLE算法],
    [压力离散], [Second Order],
    [动量离散], [Second Order Upwind],
    [能量离散], [Second Order Upwind],
    [湍流离散], [First Order Upwind],
    [收敛残差], [能量 < 10⁻⁶, 其他 < 10⁻⁴],
  ),
  caption: [Fluent求解器设置]
)

=== A.2 材料属性

#figure(
  table(
    columns: (1fr, auto, auto, auto, auto),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[材料]], [#th[密度 (kg/m³)]], [#th[比热 (J/kg·K)]], [#th[导热系数 (W/m·K)]], [#th[发射率]],
    [空气 (40°C)], [1.127], [1006.4], [0.0271], [—],
    [铜 (Cu)], [8900], [385], [400], [0.7],
    [钢 (Q235)], [7850], [500], [50], [0.85],
    [不锈钢 (304)], [7930], [500], [16], [0.6],
    [环氧树脂], [1200], [1000], [0.3], [0.9],
  ),
  caption: [材料热物性参数]
)

== 附录B：收敛性验证

// TODO: 插入收敛曲线
// #figure(
//   image("field_plots/thermal/residual.png", width: 80%),
//   caption: [计算残差收敛曲线]
// )

#block(fill: rgb("#fff3e0"), inset: 10pt, radius: 4pt, width: 100%)[
  *图片待补充*：完成Fluent仿真后，在此处插入收敛曲线图。
]

#v(2cm)

#align(right)[
  编制人签字：#underline[#h(5cm)]
  
  审核人签字：#underline[#h(5cm)]
  
  日#h(4em)期：#underline[#h(5cm)]
]
