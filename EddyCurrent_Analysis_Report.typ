// ============================================================
// 开关柜金属隔板涡流损耗仿真分析报告
// 自动生成于 2025年12月19日
// 采用 Typst 排版系统
// ============================================================

#set document(title: "开关柜金属隔板涡流损耗仿真分析报告")
#set page(paper: "a4", margin: (x: 2.5cm, y: 2.5cm),
  header: align(right)[_KYN28 开关柜涡流损耗分析报告_],
  footer: context [#align(center)[第 #counter(page).display() 页，共 #counter(page).final().at(0) 页]]
)
#set text(font: ("Noto Serif CJK SC", "Noto Sans CJK SC"), size: 10.5pt, lang: "zh")
#set heading(numbering: "1.1.1")
#set par(first-line-indent: 2em, justify: true, leading: 1.5em)
#show heading.where(level: 1): set block(above: 1.5em, below: 1em)
#show heading.where(level: 2): set block(above: 1.2em, below: 0.8em)
#show heading.where(level: 3): set block(above: 1.5em, below: 1.5em)

// ===== 表格样式 =====
#let th(content) = text(fill: white, weight: "bold", size: 9pt)[#content]
#let header-blue = rgb("#2F5496")
#let alt-gray = rgb("#E7E6E6")

// ===== 标题页 =====
#align(center)[
  #v(1.5cm)
  #text(size: 22pt, weight: "bold")[开关柜金属隔板涡流损耗仿真分析报告]
  #v(0.4cm)
  #text(size: 14pt, weight: "bold")[KYN28-12A 型高压开关柜 · Maxwell 涡流场仿真]
  #v(1cm)
  #line(length: 50%, stroke: 0.5pt)
  #v(0.8cm)
  #set par(first-line-indent: 0em)
  #grid(
    columns: (6em, auto),
    row-gutter: 10pt,
    align: (right, left),
    [*分析类型：*], [涡流场仿真 (Eddy Current)],
    [*报告日期：*], [#underline[#h(3em)]年#underline[#h(2.5em)]月#underline[#h(2.5em)]日],
  )
  #v(1.5cm)
]

// ===== 正文 =====

= 概述

本报告对 KYN28-12A 型高压开关柜的金属隔板在三相交流母排电流作用下的涡流损耗进行有限元仿真分析。通过 ANSYS Maxwell 涡流场求解器计算隔板上的感应涡流及其产生的热损耗，为开关柜的热设计提供理论依据。

#block(fill: rgb("#e3f2fd"), inset: 10pt, radius: 4pt, width: 100%)[
  *分析目的*：评估不同隔板材料对涡流损耗的影响，为材料选型提供数据支撑，指导开关柜热设计优化。
]

= 仿真模型

== 几何模型

#figure(
  table(
    columns: (1fr, 1fr, 1fr),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[参数]], [#th[数值]], [#th[单位]],
    [母排宽度 (Bus_W)], [120], [mm],
    [母排深度 (Bus_D)], [10], [mm],
    [母排高度 (Bus_H)], [600], [mm],
    [母排间距 (Space)], [160], [mm],
    [隔板厚度 (Plate_Th)], [3], [mm],
    [过孔间隙 (Gap)], [20], [mm],
  ),
  caption: [几何模型参数]
)

== 材料参数

#figure(
  table(
    columns: (1fr, 1.2fr, 1.2fr, 1fr),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[零件]], [#th[材料]], [#th[电导率 (S/m)]], [#th[相对磁导率 μr]],
    [母排], [铜 (Copper)], [5.8×10⁷], [1],
    [隔板 (原方案)], [覆铝锌板 (Galvalume)], [4.032×10⁶], [4000],
    [隔板 (优化方案)], [不锈钢 (SS304)], [1.137×10⁶], [1],
  ),
  caption: [材料电磁参数]
)

#block(fill: rgb("#fff8e1"), inset: 10pt, radius: 4pt, width: 100%)[
  *说明*：覆铝锌板本质是冷轧钢板镀铝锌涂层，基材具有铁磁性（μr≈4000）。不锈钢（304/316奥氏体）为非铁磁材料（μr≈1）。
]

== 激励条件

#figure(
  table(
    columns: (1fr, 1fr, 1.5fr),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[参数]], [#th[数值]], [#th[说明]],
    [电流幅值], [4000 A], [有效值 (RMS)],
    [工作频率], [50 Hz], [工频交流],
    [A相相位], [0°], [参考相],
    [B相相位], [-120°], [滞后120°],
    [C相相位], [+120°], [超前120°],
  ),
  caption: [三相激励条件]
)

= 理论分析

== 趋肤深度计算

趋肤效应使交变电流集中在导体表面。趋肤深度 δ 由下式计算：

$ delta = sqrt(1 / (pi f mu sigma)) = sqrt(1 / (pi f mu_0 mu_r sigma)) $

其中：$f$ 为频率 (Hz)，$mu_0 = 4pi times 10^(-7)$ H/m，$mu_r$ 为相对磁导率，$sigma$ 为电导率 (S/m)。

#figure(
  table(
    columns: (1fr, 1fr, 1fr),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[材料]], [#th[趋肤深度 (50Hz)]], [#th[备注]],
    [铜 (Copper)], [9.35 mm], [非铁磁材料],
    [覆铝锌板 (Galvalume)], [0.56 mm], [铁磁材料],
    [不锈钢 (SS304)], [21.2 mm], [非铁磁材料],
  ),
  caption: [不同材料趋肤深度]
)

#block(fill: rgb("#e8f5e9"), inset: 10pt, radius: 4pt, width: 100%)[
  *关键结论*：覆铝锌板的趋肤深度仅 0.56 mm，远小于隔板厚度 (3 mm)，涡流高度集中于表面，导致局部损耗密度极高。
]

= 仿真结果

== 涡流损耗汇总

#figure(
  table(
    columns: (1.5fr, 1fr, 0.8fr),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if row == 1 { rgb("#e6f3ff") } else if calc.odd(row) { white } else { alt-gray },
    align: (left, center, center),
    [#th[项目]], [#th[损耗值 (W)]], [#th[占比]],
    [*总涡流损耗*], [*1199.35*], [*100%*],
    [隔离板 (Plate_Frame)], [1199.35], [100.0%],
    [母排 A (Busbar_A)], [0.00], [＜1%],
    [母排 B (Busbar_B)], [0.00], [＜1%],
    [母排 C (Busbar_C)], [0.00], [＜1%],
  ),
  caption: [覆铝锌板(结构钢,铁磁材料) 条件下各部件损耗分布]
)


== 材料对比分析

#figure(
  table(
    columns: (1.4fr, 0.6fr, 1fr, 1fr),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: (left, center, center, center),
    [#th[隔板材料]], [#th[μr]], [#th[隔板损耗 (W)]], [#th[备注]],
    [覆铝锌板(结构钢,铁磁材料)], [4000], [1199.35], [原方案],
    [不锈钢板(非铁磁材料)], [1], [24.6701], [优化方案],
  ),
  caption: [不同隔板材料涡流损耗对比]
)

#block(fill: rgb("#e8f5e9"), inset: 10pt, radius: 4pt, width: 100%)[
  *关键发现*：采用非铁磁材料（不锈钢，μr≈1）替代覆铝锌板（铁磁钢板，μr≈4000）后，隔板涡流损耗从 *1199.35 W* 降至 *24.6701 W*，降幅达 *97.94%*。
]


= 场分布云图

== 覆铝锌板隔板方案（原方案）

#figure(
  grid(columns: 2, gutter: 16pt,
    image("field_plots/Galvalume/Mag_B.png", width: 100%),
    image("field_plots/Galvalume/ohmicLoss.png", width: 100%),
  ),
  caption: [覆铝锌板隔板方案场分布（左：磁通密度 Mag_B，右：欧姆损耗 OhmicLoss）]
)

== 不锈钢隔板方案（优化方案）

#figure(
  grid(columns: 2, gutter: 16pt,
    image("field_plots/Stainless/Mag_B.png", width: 100%),
    image("field_plots/Stainless/ohmicLoss.png", width: 100%),
  ),
  caption: [不锈钢隔板方案场分布（左：磁通密度 Mag_B，右：欧姆损耗 OhmicLoss）]
)

== 场分布特征分析

=== 欧姆损耗密度分布 (OhmicLoss)

损耗密度集中在隔板孔洞边缘，这是因为：

+ *涡流路径最短*：孔洞边缘的涡流环绕路径长度最短，感应电流密度最大
+ *磁通变化率最大*：三相母排产生的交变磁场在孔洞边缘区域梯度最大
+ *趋肤效应*：高频电流集中在导体表面薄层区域（趋肤深度 ≈ 0.56 mm）

=== 磁通密度分布 (B)

磁场分布呈对称特性，符合三相交流电流产生的旋转磁场预期。主要分布特征：

+ 磁通密度最大值位于母排表面附近
+ 三相母排间的磁场存在复杂的叠加与抵消效应
+ 隔板表面存在明显的磁通集中现象（铁磁材料时）

=== 电流密度分布 (J)

在 50 Hz 工频下，铜母排的趋肤深度（9.35 mm）接近导体厚度（10 mm），电流分布较为均匀，趋肤效应不明显。

= 工程意义

== 损耗与发热

根据仿真结果，对于额定电流 4000 A 的开关柜：

#figure(
  table(
    columns: (1.5fr, 1fr, 1fr),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[参数]], [#th[覆铝锌板]], [#th[不锈钢板]],
    [隔板涡流损耗功率], [1199.35 W], [24.6701 W],
    [等效发热量 (1小时)], [4317.7 kJ], [88.81 kJ],
  ),
  caption: [损耗与发热对比]
)

== 热设计建议

+ *材料替换*：采用不锈钢（304/316）等非铁磁材料替代覆铝锌板/钢板，可有效降低涡流损耗达 97.9%
+ *通风散热*：覆铝锌板隔板产生的涡流损耗约 1199 W，需考虑增加通风散热措施
+ *过孔优化*：适当加大过孔尺寸可减少孔洞边缘的磁通集中，降低局部损耗密度
+ *温度场仿真*：
  - 不锈钢隔板方案：涡流损耗可忽略不计，温升主要由铜排焦耳热决定
  - 覆铝锌板方案：须将涡流损耗作为重要热源参与温度场计算

= 结论

根据本次仿真分析，主要结论如下：

+ 在 4000 A、50 Hz 工况下，采用覆铝锌板（铁磁钢板）作为隔板，涡流损耗功率约 *1199.35 W*
+ 采用不锈钢板（非铁磁材料）作为隔板，涡流损耗功率仅 *24.67 W*，降幅达 *97.94%*
+ 涡流损耗主要发生在隔板上，损耗集中在孔洞边缘区域，与理论分析一致
+ 铁磁材料（覆铝锌板/钢板）对磁场具有明显增强作用，大幅增加涡流损耗
+ *建议*：采用非铁磁材料（304/316不锈钢）作为金属隔板材料，可有效限制涡流损耗，是优化开关柜热设计的有效手段

#v(2em)
#line(length: 100%, stroke: 0.5pt)
#grid(
  columns: (1fr, 1fr),
  [
    #text(size: 9pt, fill: gray)[
      *仿真工具*：ANSYS Maxwell 2022 R2 \
      *仿真类型*：涡流场 (Eddy Current) \
      *求解频率*：50 Hz
    ]
  ],
  [
    #align(right)[
      #text(size: 9pt, fill: gray)[
        *报告日期*：#underline[#h(2em)]年#underline[#h(1em)]月#underline[#h(1em)]日 \
        *版本*：v1.0
      ]
    ]
  ]
)
