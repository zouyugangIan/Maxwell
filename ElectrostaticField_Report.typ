// ============================================================
// 开关柜电场仿真分析报告
// 采用 Typst 排版系统
// ============================================================

#set document(title: "开关柜电场仿真分析报告")
#set page(paper: "a4", margin: (x: 2.5cm, y: 2.5cm),
  header: align(right)[_KYN28 开关柜电场分析报告_],
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
  #text(size: 22pt, weight: "bold")[开关柜电场仿真分析报告]
  #v(0.4cm)
  #text(size: 14pt, weight: "bold")[KYN28-12/4000A 型高压开关柜 · Maxwell 静电场仿真]
  #v(1cm)
  #line(length: 50%, stroke: 0.5pt)
  #v(0.8cm)
  #set par(first-line-indent: 0em)
  #grid(
    columns: (6em, auto),
    row-gutter: 10pt,
    align: (right, left),
    [*分析类型：*], [静电场仿真 (Electrostatic)],
    [*报告日期：*], [#underline[#h(3em)]年#underline[#h(2.5em)]月#underline[#h(2.5em)]日],
  )
  #v(1.5cm)
]

// ===== 正文 =====

= 概述

本报告对 KYN28-12/4000A 型高压开关柜内部电场分布进行有限元仿真分析。通过 ANSYS Maxwell 静电场求解器计算柜内各关键部位的电场强度分布，评估电气间隙和爬电距离的合理性，为开关柜的绝缘设计提供理论依据。

#block(fill: rgb("#e3f2fd"), inset: 10pt, radius: 4pt, width: 100%)[
  *分析目的*：评估开关柜内关键部位的电场强度，识别可能发生电晕或击穿的高场强区域，指导绝缘结构优化设计。
]

= 仿真模型

== 几何模型

仿真模型基于 KYN28-12/4000A 型开关柜的三维几何模型，包括：
- 主母排（三相 A/B/C）
- 绝缘支撑件
- 金属框架和隔板
- 接地外壳

#figure(
  table(
    columns: (1fr, 1fr, 1fr),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[参数]], [#th[数值]], [#th[单位]],
    [额定电压], [12], [kV],
    [额定电流], [4000], [A],
    [相间距离], [160], [mm],
    [对地距离], [125], [mm],
    [柜体尺寸 (宽×深×高)], [1110×2500×1882], [mm],
  ),
  caption: [开关柜基本参数]
)

== 材料参数

#figure(
  table(
    columns: (1fr, 1.5fr, 1fr),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[零件类型]], [#th[材料]], [#th[相对介电常数 εr]],
    [导体（母排、框架）], [铜 / 钢], [—（导体）],
    [空气域], [空气 (Air)], [1.0],
    [绝缘子/支撑件], [环氧树脂], [3.5～4.0],
  ),
  caption: [材料介电参数]
)

== 边界条件与激励

#figure(
  table(
    columns: (1fr, 1.5fr, 1fr),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[边界/激励]], [#th[对象]], [#th[电位 (kV)]],
    [电压激励], [A相母排], [+9.8 (峰值)],
    [电压激励], [B相母排], [−4.9],
    [电压激励], [C相母排], [−4.9],
    [接地边界], [金属框架/外壳], [0],
    [自然边界], [空气域外边界], [Neumann (∂φ/∂n=0)],
  ),
  caption: [边界条件设置]
)

#block(fill: rgb("#fff8e1"), inset: 10pt, radius: 4pt, width: 100%)[
  *说明*：电压激励采用工频 50 Hz 时最不利状态（A相电压达峰值时刻），此时相间电压差最大，电场强度最大。12 kV 系统线电压有效值对应的峰值电压为 $12 times sqrt(2) / sqrt(3) approx 9.8$ kV。
]

= 理论分析

== 电场强度安全阈值

对于空气介质，在标准大气压、常温条件下：

#figure(
  table(
    columns: (1fr, 1.5fr, 1fr),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[现象]], [#th[临界场强]], [#th[备注]],
    [电晕起始], [≈ 3 kV/mm], [导体尖端附近],
    [空气击穿], [≈ 3～3.5 kV/mm], [均匀电场],
    [沿面闪络], [≈ 1～2 kV/mm], [取决于表面状态],
  ),
  caption: [空气中电场强度安全阈值]
)

#block(fill: rgb("#e8f5e9"), inset: 10pt, radius: 4pt, width: 100%)[
  *设计准则*：工程设计中，通常将工作电场强度控制在击穿场强的 30%～50% 以下，即 *≤ 1.0～1.5 kV/mm*，以保证足够的安全裕度。
]

= 仿真结果

== 电场分布云图

#figure(
  image("field_plots/Electrostatic/开关柜电场仿真分析01.png", width: 95%),
  caption: [开关柜整体电场强度分布（俯视图）]
)

#figure(
  image("field_plots/Electrostatic/开关柜电场仿真分析02.png", width: 95%),
  caption: [母排区域电场强度分布]
)

#figure(
  image("field_plots/Electrostatic/开关柜电场仿真分析03.png", width: 95%),
  caption: [相间电场强度分布]
)

== 电场强度关键区域分析

#figure(
  table(
    columns: (1.5fr, 1fr, 1fr, 1fr),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if row == 1 { rgb("#e6f3ff") } else if calc.odd(row) { white } else { alt-gray },
    align: (left, center, center, center),
    [#th[区域]], [#th[最大场强 (kV/mm)]], [#th[安全阈值 (kV/mm)]], [#th[安全系数]],
    [*A-B 相间*], [*0.85*], [*1.5*], [*1.76*],
    [B-C 相间], [0.82], [1.5], [1.83],
    [A相对地], [0.45], [1.5], [3.33],
    [母排边缘], [1.12], [1.5], [1.34],
    [隔板穿孔处], [0.68], [1.5], [2.21],
  ),
  caption: [关键区域电场强度统计]
)

#block(fill: rgb("#e8f5e9"), inset: 10pt, radius: 4pt, width: 100%)[
  *关键发现*：所有监测区域的电场强度均低于安全阈值 1.5 kV/mm，安全系数均大于 1.3，满足绝缘设计要求。母排边缘处场强最高（1.12 kV/mm），需重点关注。
]

== 电位分布

#figure(
  image("field_plots/Electrostatic/开关柜电场仿真分析04.png", width: 95%),
  caption: [开关柜内部电位分布]
)

= 工程意义

== 绝缘设计评估

根据仿真结果，对开关柜绝缘设计进行如下评估：

#figure(
  table(
    columns: (1.5fr, 1fr, 1fr),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[评估项目]], [#th[仿真结果]], [#th[评价]],
    [相间电气间隙], [场强 ≤ 1.0 kV/mm], [合格 ✓],
    [对地电气间隙], [场强 ≤ 0.5 kV/mm], [合格 ✓],
    [母排边缘], [场强 1.12 kV/mm], [需关注 ⚠],
  ),
  caption: [绝缘设计评估结果]
)

== 优化建议

+ *母排边缘处理*：对母排边缘进行倒圆处理（半径 ≥ 5 mm），可有效降低边缘场强集中
+ *屏蔽措施*：在高场强区域增设均压环或屏蔽罩，改善电场分布均匀性
+ *爬电距离*：确保绝缘子表面爬电距离满足规范要求（≥ 25 mm/kV）
+ *绝缘材料*：对于场强较高区域，考虑使用高介电强度绝缘材料进行包覆

= 结论

根据本次静电场仿真分析，主要结论如下：

+ 在 12 kV 工频电压最不利工况下，开关柜内各区域电场强度均低于空气击穿临界值
+ 相间最大电场强度约 *0.85 kV/mm*，对地最大电场强度约 *0.45 kV/mm*，均有足够的安全裕度
+ 母排边缘存在场强集中现象，最大场强 *1.12 kV/mm*，建议进行边缘倒圆优化
+ 整体绝缘设计满足 GB 3906 标准要求，电气间隙和爬电距离配置合理
+ *建议*：对母排边缘进行倒圆处理，并在高场强区域加强绝缘监测

#v(2em)
#line(length: 100%, stroke: 0.5pt)
#grid(
  columns: (1fr, 1fr),
  [
    #text(size: 9pt, fill: gray)[
      *仿真工具*：ANSYS Maxwell 2022 R2 \
      *仿真类型*：静电场 (Electrostatic) \
      *激励条件*：12 kV 线电压峰值
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
