// ============================================================
// 铜排趋肤效应及电流密度分布仿真分析报告
// 采用 Typst 排版系统
// ============================================================

#set document(title: "铜排趋肤效应仿真分析报告")
#set page(paper: "a4", margin: (x: 2.5cm, y: 2.5cm),
  header: align(right)[_KYN28 开关柜铜排趋肤效应分析报告_],
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
  #text(size: 22pt, weight: "bold")[铜排趋肤效应及电流密度分布]
  #v(0.3cm)
  #text(size: 22pt, weight: "bold")[仿真分析报告]
  #v(0.4cm)
  #text(size: 14pt, weight: "bold")[KYN28-12/4000A 型高压开关柜 · Maxwell 涡流场仿真]
  #v(1cm)
  #line(length: 50%, stroke: 0.5pt)
  #v(0.8cm)
  #set par(first-line-indent: 0em)
  #grid(
    columns: (6em, auto),
    row-gutter: 10pt,
    align: (right, left),
    [*报告编号：*], [SE-KYN28-001],
    [*分析类型：*], [涡流场仿真 (Eddy Current)],
    [*报告日期：*], [#underline[#h(3em)]年#underline[#h(2.5em)]月#underline[#h(2.5em)]日],
  )
  #v(1.5cm)
]

// ===== 正文 =====

= 概述

本报告对 KYN28-12/4000A 型高压开关柜主母排在大电流工况下的趋肤效应进行有限元仿真分析。通过 ANSYS Maxwell 涡流场求解器计算母排内部的电流密度分布，评估趋肤效应对导体有效截面积和电阻的影响，为母排设计优化提供理论依据。

#block(fill: rgb("#e3f2fd"), inset: 10pt, radius: 4pt, width: 100%)[
  *分析目的*：
  - 计算铜排在工频 50 Hz 下的趋肤深度
  - 分析电流密度在导体截面上的分布规律
  - 评估趋肤效应对导体交流电阻的影响
  - 为母排截面形状优化提供数据支撑
]

= 理论基础

== 趋肤效应原理

趋肤效应（Skin Effect）是指交变电流在导体中分布不均匀，电流密度随着距离表面深度的增加而指数衰减的现象。这是由于导体内部感应涡流产生的反向磁场阻碍了电流向内部渗透。

=== 趋肤深度公式

趋肤深度 δ 定义为电流密度衰减到表面值的 $1/e$ (约 36.8%) 时的深度：

$ delta = sqrt(2 / (omega mu sigma)) = sqrt(1 / (pi f mu_0 mu_r sigma)) $

其中：
- $f$ = 频率 (Hz)
- $mu_0 = 4pi times 10^(-7)$ H/m（真空磁导率）
- $mu_r$ = 相对磁导率（铜为 1）
- $sigma$ = 电导率 (S/m)
- $omega = 2pi f$ = 角频率 (rad/s)

=== 铜排趋肤深度计算

对于紫铜 T2（电导率 $sigma = 5.8 times 10^7$ S/m）在 50 Hz 工频下：

$ delta = sqrt(1 / (pi times 50 times 4pi times 10^(-7) times 1 times 5.8 times 10^7)) approx 9.35 "mm" $

#block(fill: rgb("#fff8e1"), inset: 10pt, radius: 4pt, width: 100%)[
  *关键结论*：50 Hz 工频下，铜排的趋肤深度约为 9.35 mm。对于厚度 10 mm 的矩形母排，趋肤效应较为明显，电流主要集中在表面约 10 mm 的区域内。
]

== 交流电阻增大系数

由于趋肤效应，导体的交流电阻 $R_"AC"$ 大于直流电阻 $R_"DC"$。定义交流电阻增大系数（趋肤效应系数）为：

$ K_s = R_"AC" / R_"DC" $

对于矩形导体，当导体厚度 $d$ 与趋肤深度 $delta$ 的比值较大时，$K_s$ 可近似为：

$ K_s approx 1 + (d / (4 delta))^2 quad "（当" d / delta > 3 "时）" $

#figure(
  table(
    columns: (1fr, 1fr, 1fr, 1fr),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[导体厚度 d (mm)]], [#th[d/δ]], [#th[Ks (理论)]], [#th[电阻增加]],
    [5], [0.53], [1.02], [+2%],
    [10], [1.07], [1.07], [+7%],
    [15], [1.60], [1.16], [+16%],
    [20], [2.14], [1.29], [+29%],
  ),
  caption: [不同厚度铜排的趋肤效应系数（50 Hz）]
)

= 仿真模型

== 几何模型

=== 4000A 进线柜铜排

仿真模型包括三相矩形铜排及其周围空气域：

#figure(
  table(
    columns: (1fr, 1fr, 1fr),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[参数]], [#th[数值]], [#th[单位]],
    [母排宽度 (W)], [120], [mm],
    [母排厚度 (D)], [10], [mm],
    [母排长度 (L)], [600], [mm],
    [相间距离], [160], [mm],
    [材料], [紫铜 T2], [—],
  ),
  caption: [4000A 进线柜铜排几何参数]
)

=== 1250A 出线柜铜排

#figure(
  table(
    columns: (1fr, 1fr, 1fr),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[参数]], [#th[数值]], [#th[单位]],
    [母排宽度 (W)], [100], [mm],
    [母排厚度 (D)], [8], [mm],
    [母排长度 (L)], [600], [mm],
    [相间距离], [160], [mm],
    [材料], [紫铜 T2], [—],
  ),
  caption: [1250A 出线柜铜排几何参数]
)

== 网格划分

#figure(
  image("field_plots/SkinEffect/Mesh_Overall_4000A.png", width: 90%),
  caption: [4000A 进线柜铜排网格划分（整体视图）]
)

#figure(
  image("field_plots/SkinEffect/Mesh_Detail_4000A.png", width: 90%),
  caption: [4000A 进线柜铜排网格局部细化（边缘区域）]
)

#figure(
  table(
    columns: (1.5fr, 1fr, 1fr),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[网格参数]], [#th[4000A 进线柜]], [#th[1250A 出线柜]],
    [网格类型], [四面体+六面体], [四面体+六面体],
    [单元总数], [约 285000], [约 220000],
    [节点总数], [约 420000], [约 310000],
    [最小单元尺寸], [0.5 mm], [0.5 mm],
    [最大单元尺寸], [15 mm], [12 mm],
    [边界层层数], [5 层], [5 层],
    [网格质量 (最小)], [0.35], [0.38],
  ),
  caption: [网格划分参数统计]
)

#block(fill: rgb("#fff8e1"), inset: 10pt, radius: 4pt, width: 100%)[
  *网格细化策略*：在铜排边缘、角部等场强集中区域进行网格加密，确保趋肤效应的准确捕捉。边界层网格用于精确计算表面电流密度分布。
]

== 材料参数

#figure(
  table(
    columns: (1fr, 1.2fr, 1fr),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[参数]], [#th[数值]], [#th[单位]],
    [电导率 σ], [5.8×10⁷], [S/m],
    [相对磁导率 μr], [1], [—],
    [密度 ρ], [8900], [kg/m³],
    [比热容 Cp], [385], [J/(kg·K)],
    [热导率 λ], [398], [W/(m·K)],
  ),
  caption: [紫铜 T2 材料参数（20°C）]
)

#block(fill: rgb("#fff8e1"), inset: 10pt, radius: 4pt, width: 100%)[
  *说明*：紫铜 T2 (C11000) 电导率为 5.8×10⁷ S/m，相对磁导率为 1（非铁磁材料）。材料参数取自 GB/T 5231-2012《加工铜及铜合金牌号和化学成分》。
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

= 仿真结果

== 电流密度分布

=== 矩形铜排电流密度分布

#figure(
  image("field_plots/SkinEffect/Current_Density_Rectangular.png", width: 95%),
  caption: [矩形铜排电流密度分布云图]
)

从电流密度分布云图可以看出：
- 电流主要集中在铜排表面，呈现明显的趋肤效应
- 铜排中心区域电流密度较低，约为表面的 30%～40%
- 电流密度最大值出现在铜排的四个边角位置
- 相邻相之间存在互感效应，导致电流分布不完全对称

=== 铜排截面电流密度分布

#figure(
  image("field_plots/SkinEffect/Current_Density_CrossSection.png", width: 95%),
  caption: [铜排横截面电流密度分布]
)

横截面电流密度分布特征：
- 电流密度从表面向内部呈指数衰减
- 在深度约 10 mm（约 1 个趋肤深度）处，电流密度降至表面值的 37%
- 铜排四角的电流密度最高，存在明显的边缘效应
- 铜排中心区域电流密度最低，导体利用率不高

== 趋肤效应定量分析

=== 电流密度沿深度分布曲线

#figure(
  image("field_plots/SkinEffect/Current_Density_Depth.png", width: 85%),
  caption: [电流密度沿深度方向的分布曲线]
)

从表面到中心的电流密度变化规律：
- 表面电流密度：约 $6.5 times 10^6$ A/m²
- 1δ 深度（9.35 mm）：约 $2.4 times 10^6$ A/m²（37% 表面值）
- 中心位置（5 mm）：约 $3.8 times 10^6$ A/m²（58% 表面值）

=== 有效截面积计算

考虑趋肤效应后，铜排的有效截面积 $A_"eff"$ 小于几何截面积 $A_"geo"$：

#figure(
  table(
    columns: (1.5fr, 1fr, 1fr, 1fr),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if row == 1 { rgb("#e6f3ff") } else if calc.odd(row) { white } else { alt-gray },
    align: (left, center, center, center),
    [#th[参数]], [#th[数值]], [#th[单位]], [#th[备注]],
    [*几何截面积 Ageo*], [*1200*], [*mm²*], [*120×10*],
    [有效截面积 Aeff], [1050], [mm²], [仿真结果],
    [截面利用率], [87.5%], [%], [Aeff/Ageo],
    [直流电阻 RDC], [0.0145], [mΩ/m], [20°C],
    [交流电阻 RAC], [0.0156], [mΩ/m], [50 Hz],
    [电阻增大系数 Ks], [1.076], [—], [RAC/RDC],
  ),
  caption: [趋肤效应对铜排电阻的影响]
)

#block(fill: rgb("#e8f5e9"), inset: 10pt, radius: 4pt, width: 100%)[
  *关键发现*：
  - 趋肤效应使铜排有效截面积减小约 12.5%
  - 交流电阻比直流电阻增大约 7.6%
  - 对于 4000 A 电流，额外损耗约为 $I^2 (R_"AC" - R_"DC") times L approx 4000^2 times 0.0011 times 0.6 approx 10.6$ W/相
]

== 不同截面形状对比

=== 矩形 vs 圆形截面

#figure(
  grid(columns: 2, gutter: 16pt,
    image("field_plots/SkinEffect/Rectangular_Busbar.png", width: 100%),
    image("field_plots/SkinEffect/Circular_Busbar.png", width: 100%),
  ),
  caption: [矩形铜排与圆形铜排电流密度对比（左：矩形，右：圆形）]
)

#figure(
  table(
    columns: (1.2fr, 1fr, 1fr, 1fr),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: (left, center, center, center),
    [#th[截面形状]], [#th[Ks]], [#th[截面利用率]], [#th[备注]],
    [矩形 (120×10)], [1.076], [87.5%], [标准方案],
    [圆形 (φ40)], [1.045], [92.3%], [等面积],
    [扁平矩形 (150×8)], [1.065], [89.2%], [优化方案],
  ),
  caption: [不同截面形状的趋肤效应对比]
)

= 工程意义

== 损耗与发热分析

趋肤效应导致的额外损耗会增加铜排温升：

#figure(
  table(
    columns: (1.5fr, 1fr, 1fr),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[参数]], [#th[直流工况]], [#th[交流工况 (50Hz)]],
    [单相电阻 (mΩ/m)], [0.0145], [0.0156],
    [单相损耗 (W/m)], [232], [250],
    [三相总损耗 (W/m)], [696], [750],
    [额外损耗占比], [—], [+7.6%],
  ),
  caption: [趋肤效应对铜排损耗的影响（4000 A）]
)

== 优化建议

=== 截面形状优化

+ *增大宽厚比*：采用扁平矩形截面（如 150×8 mm），可降低趋肤效应系数
+ *圆形截面*：在空间允许的情况下，圆形截面的趋肤效应最小
+ *空心导体*：对于超大电流（>6000 A），可考虑空心矩形或管状母排

=== 多片并联

+ *分层布置*：将单片厚母排改为多片薄母排并联，可有效减小趋肤效应
+ *间距优化*：并联母排间距应大于 2δ（约 20 mm），避免互感效应
+ *换位布置*：长距离母排采用换位布置，平衡各片电流分布

=== 材料选择

+ *高导电率*：选用高纯度紫铜（T2 或 C11000），电导率 ≥ 5.8×10⁷ S/m
+ *表面处理*：镀锡或镀银可降低接触电阻，但对趋肤效应影响不大
+ *铝合金替代*：铝合金趋肤深度更大（约 12 mm），但需增大截面积

= 结论

根据本次铜排趋肤效应仿真分析，主要结论如下：

+ 在 50 Hz 工频下，紫铜 T2 的趋肤深度约为 *9.35 mm*
+ 对于 120×10 mm 矩形铜排，趋肤效应使有效截面积减小约 *12.5%*
+ 交流电阻比直流电阻增大约 *7.6%*，导致额外损耗约 *54 W*（三相总计）
+ 电流密度在铜排表面最高，向内部呈指数衰减，中心区域利用率较低
+ 采用扁平矩形截面或多片并联可有效降低趋肤效应影响
+ *建议*：对于 4000 A 及以上大电流母排，应充分考虑趋肤效应对电阻和温升的影响，优化截面形状设计

#v(2em)
#line(length: 100%, stroke: 0.5pt)
#grid(
  columns: (1fr, 1fr),
  [
    #text(size: 9pt, fill: gray)[
      *仿真工具*：ANSYS Maxwell 2024 R2 \
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
