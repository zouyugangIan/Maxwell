// 开关柜金属隔板涡流损耗仿真分析报告
// Typst 格式，可直接编译为 PDF

#set document(
  title: "开关柜金属隔板涡流损耗仿真分析报告",
  author: "Maxwell 仿真分析",
  date: datetime.today(),
)

#set page(
  paper: "a4",
  margin: (x: 2.5cm, y: 2.5cm),
  header: align(right)[_开关柜金属隔板涡流损耗分析_],
  footer: context [
    #align(center)[#counter(page).display("1 / 1", both: true)]
  ],
)

#set text(
  font: ("Noto Serif CJK SC", "Times New Roman"),
  size: 11pt,
  lang: "zh",
)

#set heading(numbering: "1.1")
#set par(first-line-indent: 2em, justify: true, leading: 1.2em)

// 标题
#align(center)[
  #text(size: 22pt, weight: "bold")[开关柜金属隔板涡流损耗仿真分析报告]
  
  #v(1em)
  #text(size: 12pt)[KYN28-V19 型开关柜 · Maxwell 涡流场仿真]
  
  #v(0.5em)
  #text(size: 10pt, fill: gray)[
    日期：#datetime.today().display("[year]年[month]月[day]日")
  ]
]

#v(2em)

= 概述

本报告对 KYN28 型开关柜金属隔板在三相交流母排电流作用下的涡流损耗进行有限元仿真分析。通过 ANSYS Maxwell 涡流场求解器计算隔板上的感应涡流及其产生的热损耗，为开关柜的热设计提供理论依据。

#v(1em)

= 仿真模型

== 几何模型

#figure(
  table(
    columns: (1fr, 1fr, auto),
    align: (left, center, center),
    stroke: 0.5pt,
    inset: 8pt,
    [*参数*], [*数值*], [*单位*],
    [母排宽度 (Bus_W)], [10], [mm],
    [母排深度 (Bus_D)], [100], [mm],
    [母排高度 (Bus_H)], [600], [mm],
    [母排间距 (Space)], [160], [mm],
    [隔板厚度 (Plate_Th)], [3], [mm],
    [过孔间隙 (Gap)], [20], [mm],
  ),
  caption: [几何模型参数],
)

== 材料参数

#figure(
  table(
    columns: (auto, auto, 1fr, 1fr),
    align: (left, left, center, center),
    stroke: 0.5pt,
    inset: 8pt,
    [*零件*], [*材料*], [*电导率 (S/m)*], [*相对磁导率 μ#sub[r]*],
    [母排], [铜], [5.8×10#super[7]], [1],
    [隔板], [KYN_Steel], [4.032×10#super[6]], [4000],
  ),
  caption: [材料参数],
)

== 激励条件

- *电流幅值*：4000 A（有效值）
- *工作频率*：50 Hz
- *三相相位*：A相 = 0°，B相 = -120°，C相 = +120°

= 趋肤深度计算

趋肤深度公式：$ delta = sqrt(1 / (pi f mu sigma)) $

#figure(
  table(
    columns: (1fr, 1fr),
    align: center,
    stroke: 0.5pt,
    inset: 8pt,
    [*材料*], [*趋肤深度 (50Hz)*],
    [铜], [9.35 mm],
    [KYN_Steel], [0.56 mm],
  ),
  caption: [各材料趋肤深度],
)

#pagebreak()

= 仿真结果

== 涡流损耗

#figure(
  table(
    columns: (1fr, 1fr, auto),
    align: (left, center, center),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (col, row) => if row == 1 { rgb("#e6f3ff") } else { none },
    [*项目*], [*损耗值 (W)*], [*占比*],
    [*总涡流损耗*], [*163.39*], [*100%*],
    [隔离板 (Isolation_Plate)], [~160], [~98%],
    [母排 A (Busbar_A)], [< 1], [< 1%],
    [母排 B (Busbar_B)], [< 1], [< 1%],
    [母排 C (Busbar_C)], [< 1], [< 1%],
  ),
  caption: [涡流损耗分布],
)

#block(
  fill: rgb("#fff8e1"),
  inset: 10pt,
  radius: 4pt,
  width: 100%,
)[
  *关键发现*：涡流损耗主要发生在隔板上，占总损耗的 98% 以上。这是因为钢制隔板的高磁导率 (μ#sub[r]=4000) 导致磁通集中，产生大量感应涡流。
]

== 场分布云图分析

=== (1) 欧姆损耗密度分布 (Ohmic_Loss)

- *最大值*：6.89×10#super[7] W/m³
- *分布特点*：损耗密度集中在隔板孔洞边缘
- *原因分析*：
  - 孔洞边缘的涡流路径最短
  - 磁通密度变化率最大
  - 趋肤效应使电流集中在表面

=== (2) 磁通密度分布 (Mag_B)

- *最大值*：约 0.12 T (117.8 mT)
- *分布特点*：位于母排表面附近，呈对称分布
- *物理意义*：磁场分布符合三相交流电流产生的旋转磁场预期

=== (3) 磁场强度分布 (Mag_H)

- *最大值*：23,426 A/m
- *分布位置*：
  - 母排表面
  - 隔板靠近母排的区域

=== (4) 电流密度分布 (J)

母排中的电流密度呈现明显的趋肤效应，电流集中在导体表面。

#pagebreak()

= 结果分析

== 损耗分析

+ *涡流损耗主要发生在隔板上*：占总损耗的 98% 以上
+ *损耗集中在孔洞边缘*：磁通变化率大的区域
+ *母排损耗很小*：因为铜的电导率高，趋肤深度大

== 工程意义

根据仿真结果，对于额定电流 4000A 的开关柜：

#figure(
  table(
    columns: (1fr, 1fr),
    align: (left, center),
    stroke: 0.5pt,
    inset: 8pt,
    [*参数*], [*数值*],
    [隔板涡流损耗功率], [~160 W],
    [等效发热量], [576 kJ/h],
  ),
  caption: [隔板发热量],
)

此损耗会导致隔板温升，需要在设计中考虑：
- 增加通风散热
- 选用低磁导率材料减少涡流（如用铝锌板代替钢板）
- 优化过孔尺寸减少磁通集中

== 材料对比

#figure(
  table(
    columns: (1fr, 1fr, 2fr),
    align: (left, center, left),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (col, row) => if row == 2 { rgb("#e8f5e9") } else { none },
    [*隔板材料*], [*涡流损耗 (W)*], [*备注*],
    [不锈钢], [144.02], [原方案],
    [覆铝锌板], [0.018], [优化方案，降低 99.99%],
  ),
  caption: [不同隔板材料涡流损耗对比（参考文献）],
)

#v(1em)
#block(
  fill: rgb("#e3f2fd"),
  inset: 12pt,
  radius: 4pt,
  width: 100%,
)[
  *结论*：采用铝锌板等非铁磁材料可大幅降低涡流损耗，是限制涡流损耗、降低能耗的有效手段。
]

= 结论

+ 本仿真采用 ANSYS Maxwell 涡流场求解器，成功模拟了开关柜三相母排对金属隔板的涡流效应
+ 在 4000A、50Hz 工况下，钢制隔板涡流损耗约 *163 W*
+ 损耗主要集中在隔板孔洞边缘，与理论分析一致
+ 建议采用非铁磁材料（如铝锌板）替代钢板，可将损耗降低 99% 以上

#v(2em)
#line(length: 100%, stroke: 0.5pt)
#v(0.5em)

#text(size: 9pt, fill: gray)[
  *仿真工具*：ANSYS Electronics Suite 2024 R1 (Maxwell 3D) \
  *仿真类型*：涡流场 (Eddy Current) \
  *求解频率*：50 Hz
]
