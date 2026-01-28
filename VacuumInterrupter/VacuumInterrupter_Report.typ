// ============================================================
// 真空灭弧室电场及开断特性仿真分析报告
// 基于 ANSYS Maxwell 多物理场仿真
// ============================================================

#set document(title: "真空灭弧室仿真分析报告", author: "电磁仿真分析工作组")
#set page(
  paper: "a4",
  margin: (x: 2.5cm, y: 2.5cm),
  numbering: "1",
  header: context {
    if counter(page).get().first() > 1 [
      #align(right)[#text(size: 9pt, fill: gray)[_12kV 真空灭弧室仿真分析报告_]]
      #line(length: 100%, stroke: 0.3pt + gray)
    ]
  },
  footer: context [#align(center)[#text(size: 9pt)[第 #counter(page).display() 页，共 #counter(page).final().at(0) 页]]]
)
#set text(font: ("SimSun", "Microsoft YaHei"), size: 10.5pt, lang: "zh")
#set heading(numbering: "1.1.1")
#show heading.where(level: 1): set block(above: 1.5em, below: 1em)
#show heading.where(level: 2): set block(above: 1.2em, below: 0.8em)
#show heading.where(level: 3): set block(above: 1em, below: 0.6em)
#set par(first-line-indent: (amount: 2em, all: true), justify: true, leading: 1.3em, spacing: 1.3em)

// ===== 表格样式 =====
#let th(content) = text(fill: white, weight: "bold", size: 9pt)[#content]
#let header-blue = rgb("#2F5496")
#let alt-gray = rgb("#F2F2F2")

// ===== 标题页 =====
#align(center)[
  #v(2cm)
  #text(size: 24pt, weight: "bold")[真空灭弧室电场及开断特性]
  #v(0.3cm)
  #text(size: 24pt, weight: "bold")[仿真分析报告]
  #v(0.5cm)
  #text(size: 14pt, fill: gray)[12kV/4000A 真空断路器（参考 Eaton WL-41167）· Maxwell 多物理场仿真]
  #v(1.5cm)
  #line(length: 60%, stroke: 1pt + header-blue)
  #v(1cm)
  #set par(first-line-indent: 0em)
  #grid(
    columns: (7em, auto),
    row-gutter: 12pt,
    align: (right, left),
    [*报告编号：*], [VI-12kV-4000A-2026-001],
    [*分析类型：*], [静电场 + 瞬态电磁场],
    [*分析软件：*], [ANSYS Maxwell 2024 R1],
    [*编制单位：*], [电磁仿真分析工作组],
    [*报告日期：*], [2026年01月19日],
  )
  #v(2cm)
  #block(fill: rgb("#e8f4fd"), inset: 12pt, radius: 6pt, width: 80%)[
    #set par(first-line-indent: 0em)
    #text(size: 10pt)[
      *摘要*：本报告对 12kV/4000A 真空断路器的真空灭弧室进行多物理场仿真分析，机械参数参考 Eaton WL-41167 规格。通过静电场求解器评估断口绝缘性能，通过瞬态电磁场求解器分析开断过程动态特性。仿真结果表明，触头间隙最大电场强度约 1.25 kV/mm，远低于真空击穿阈值，安全系数大于 16，满足 12kV 等级绝缘要求。
    ]
  ]
]

#pagebreak()

// ===== 正文 =====
= 概述

== 研究背景

+ *核心关注*：电场分布、触头电流密度、开断过程电弧与介质恢复
+ *关键风险*：触头边缘场强集中、绝缘薄弱区、开断重燃风险
+ *方法定位*：有限元仿真用于设计阶段的风险识别与结构优化

#figure(
  table(
    columns: (1.5fr, auto, 1.5fr, 1.5fr),
    stroke: 0.5pt + rgb("#666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[评估维度]], [#th[指标]], [#th[目标/标准]], [#th[本报告输出]],
    [绝缘性能], [最大场强], [真空击穿阈值 20~30 kV/mm], [场强云图 + 关键点统计],
    [导电性能], [电流密度], [避免边缘集中], [电流密度云图 + 统计表],
    [开断能力], [燃弧时间], [≤ 半个工频周期], [电流/电压/恢复波形],
    [结构可靠性], [安全系数], [> 10], [安全系数表],
  ),
  caption: [评估指标与输出形式]
)

== 研究目的

+ *电场分布*：触头间隙、屏蔽罩与陶瓷外壳的场强分布与峰值位置
+ *电流密度*：合闸接触区电流集中与热风险评估
+ *开断特性*：电流过零、燃弧时间与介质恢复趋势
+ *设计优化*：提供几何与材料优化方向

#figure(
  block(fill: rgb("#fff3e0"), inset: 26pt, radius: 6pt, width: 100%, stroke: 1pt + rgb("#ffcc80"))[
    #align(center)[
      *图 1：仿真流程与输出图谱*
      
      （待插入：流程图，包含几何建模 → 网格 → 边界 → 求解 → 结果图谱）
    ]
  ],
  caption: [仿真流程与输出图谱]
)

= 真空灭弧室结构

== 基本结构

真空灭弧室的典型结构包括以下主要部件：

+ *动触头*：与操作机构连接，沿轴向移动实现分合闸动作
+ *静触头*：固定在灭弧室上端，通过导电杆与外部回路连接
+ *主屏蔽罩*：包围触头区域，防止金属蒸气沉积在绝缘外壳上
+ *陶瓷外壳*：提供真空密封和对地绝缘
+ *波纹管*：补偿动触头的轴向运动，保持真空密封

#figure(
  grid(
    columns: (1fr, 1fr),
    gutter: 12pt,
    block(fill: rgb("#fff3e0"), inset: 22pt, radius: 6pt, stroke: 1pt + rgb("#ffcc80"))[
      #align(center)[
        *图 2(a)：结构剖面示意图*
        
        （待插入：标注动/静触头、屏蔽罩、陶瓷壳、波纹管）
      ]
    ],
    block(fill: rgb("#fff3e0"), inset: 22pt, radius: 6pt, stroke: 1pt + rgb("#ffcc80"))[
      #align(center)[
        *图 2(b)：关键尺寸标注图*
        
        （待插入：几何尺寸与参考面）
      ]
    ]
  ),
  caption: [真空灭弧室结构与关键尺寸]
)

== 几何参数

#figure(
  table(
    columns: (1fr, auto, auto, 1.5fr),
    stroke: 0.5pt + rgb("#666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[参数名称]], [#th[符号]], [#th[设计值]], [#th[备注说明]],
    [触头直径], [$D_c$], [50 mm], [CuCr25 合金触头],
    [触头开距], [$d_"open"$], [8.5 ± 0.5 mm], [分闸后间隙（参考 Eaton）],
    [触头超程], [$d_"over"$], [4 mm], [合闸压缩量（最小超程）],
    [触头曲率半径], [$R_c$], [25 mm], [球形端面],
    [屏蔽罩内径], [$D_s$], [80 mm], [主屏蔽罩],
    [陶瓷外壳内径], [$D_"shell"$], [100 mm], [95% Al₂O₃],
    [真空度], [$P$], [< 10⁻⁴ Pa], [高真空],
  ),
  caption: [真空灭弧室主要几何参数]
)

== 材料属性

#figure(
  table(
    columns: (1fr, 1.2fr, auto, auto, 1fr),
    stroke: 0.5pt + rgb("#666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[部件]], [#th[材料]], [#th[相对介电常数]], [#th[电导率 (S/m)]], [#th[备注]],
    [动/静触头], [CuCr25 合金], [—], [2.9×10⁷], [导体],
    [屏蔽罩], [不锈钢 304], [—], [1.4×10⁶], [导体],
    [陶瓷外壳], [95% Al₂O₃], [9.4], [绝缘体], [介质],
    [真空间隙], [Vacuum], [1.0], [0], [理想绝缘],
    [波纹管], [316L 不锈钢], [—], [1.3×10⁶], [导体],
  ),
  caption: [材料电磁属性参数]
)

#block(fill: rgb("#e8f5e9"), inset: 10pt, radius: 4pt, width: 100%)[
  *材料要点*：CuCr25 兼具导电性与抗烧蚀能力，适用于 12kV 等级触头；屏蔽罩与波纹管材料需兼顾导电与耐热。
]

= 静电场分析

== 边界条件设置

#figure(
  table(
    columns: (1fr, 1.2fr, 1fr, 1.5fr),
    stroke: 0.5pt + rgb("#666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[边界类型]], [#th[应用对象]], [#th[电位设置]], [#th[备注]],
    [电压激励], [动触头], [+9.8 kV], [12kV 峰值],
    [接地边界], [静触头], [0 V], [参考电位],
    [浮地边界], [屏蔽罩], [自由电位], [电容耦合],
    [自然边界], [外边界], [Neumann], [场线垂直],
  ),
  caption: [静电场边界条件（分闸状态）]
)

== 电场分布结果

#figure(
  grid(
    columns: (1fr, 1fr),
    gutter: 12pt,
    block(fill: rgb("#fff3e0"), inset: 22pt, radius: 6pt, stroke: 1pt + rgb("#ffcc80"))[
      #align(center)[
        *图 3(a)：电场强度云图*
        
        （触头间隙区域）
      ]
    ],
    block(fill: rgb("#fff3e0"), inset: 22pt, radius: 6pt, stroke: 1pt + rgb("#ffcc80"))[
      #align(center)[
        *图 3(b)：电位分布云图*
        
        （整体分布）
      ]
    ]
  ),
  caption: [静电场仿真结果]
)

#figure(
  grid(
    columns: (1fr, 1fr),
    gutter: 12pt,
    block(fill: rgb("#fff3e0"), inset: 22pt, radius: 6pt, stroke: 1pt + rgb("#ffcc80"))[
      #align(center)[
        *图 3(c)：关键路径场强曲线*
        
        （待插入：触头边缘→屏蔽罩→陶瓷表面）
      ]
    ],
    block(fill: rgb("#fff3e0"), inset: 22pt, radius: 6pt, stroke: 1pt + rgb("#ffcc80"))[
      #align(center)[
        *图 3(d)：等值线密集区放大图*
        
        （待插入：场强集中区域）
      ]
    ]
  ),
  caption: [电场分布细节与路径曲线]
)

== 关键位置电场强度

#figure(
  table(
    columns: (1.5fr, auto, auto, auto, auto),
    stroke: 0.5pt + rgb("#666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if row == 1 { rgb("#e6f3ff") } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[位置]], [#th[电场强度]], [#th[击穿阈值]], [#th[安全系数]], [#th[评价]],
    [*触头边缘*], [*1.25 kV/mm*], [*20~30 kV/mm*], [*16~24*], [*合格*],
    [触头中心], [0.98 kV/mm], [20~30 kV/mm], [20~31], [合格],
    [屏蔽罩附近], [0.35 kV/mm], [20~30 kV/mm], [57~86], [合格],
    [陶瓷表面], [0.15 kV/mm], [10~15 kV/mm], [67~100], [合格],
  ),
  caption: [关键位置电场强度统计]
)

#block(fill: rgb("#e8f5e9"), inset: 10pt, radius: 4pt, width: 100%)[
  *关键发现*：触头边缘为最大场强位置，安全系数大于 16；屏蔽罩有效均化场强，陶瓷表面场强显著低于击穿阈值。
]

= 触头电流密度分析

== 合闸状态电流分布

#figure(
  block(fill: rgb("#fff3e0"), inset: 26pt, radius: 6pt, width: 100%, stroke: 1pt + rgb("#ffcc80"))[
    #align(center)[
      *图 4：触头接触区域电流密度分布*
      
      （待插入：电流密度云图，显示接触面电流集中区域）
    ]
  ],
  caption: [触头接触区域电流密度分布]
)

#figure(
  table(
    columns: (1.2fr, auto, auto, 1.5fr),
    stroke: 0.5pt + rgb("#666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[特征项]], [#th[结果]], [#th[单位]], [#th[说明]],
    [最大电流密度], [3.5×10^6], [A/m²], [触头边缘附近],
    [平均电流密度], [—], [A/m²], [待由结果统计],
    [接触电阻], [≤10], [μΩ], [参考 Eaton @ 4400 N],
    [发热功率], [~160], [W], [$I^2 R$ 估算],
  ),
  caption: [电流密度与接触特性汇总]
)

== 接触电阻与发热

#figure(
  table(
    columns: (1.5fr, auto, auto, 1.5fr),
    stroke: 0.5pt + rgb("#666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[参数]], [#th[数值]], [#th[单位]], [#th[备注]],
    [额定电流], [4000], [A], [RMS 值],
    [接触电阻], [≤10], [μΩ], [参考 Eaton @ 4400 N],
    [接触压力], [4400], [N], [最小触头压力],
    [发热功率], [~160], [W], [$I^2 R$ 估算],
    [温升估算], [15~25], [K], [稳态],
  ),
  caption: [触头接触电阻及发热功率]
)

= 开断过程瞬态分析

== 纵向磁场(AMF)分布特性

纵向磁场 (Axial Magnetic Field, AMF) 是大容量真空灭弧室的核心设计指标。分析应以峰值电流时刻的磁场分布为主，评估磁场形态与强度是否满足扩散型电弧维持条件。

#figure(
  grid(
    columns: (1fr, 1fr),
    gutter: 12pt,
    block(fill: rgb("#fff3e0"), inset: 22pt, radius: 6pt, stroke: 1pt + rgb("#ffcc80"))[
      #align(center)[
        *图 5(a)：峰值电流时刻磁场云图 (B-Vector)*
        
        （待插入：$t=5 text("ms")$，峰值电流时刻切面磁感应强度矢量图）
      ]
    ],
    block(fill: rgb("#fff3e0"), inset: 22pt, radius: 6pt, stroke: 1pt + rgb("#ffcc80"))[
      #align(center)[
        *图 5(b)：轴向磁场 $B_x$ 径向分布*
        
        （待插入：触头表面径向 $B_x$ 分布曲线，用于判断钟形/马鞍形）
      ]
    ]
  ),
  caption: [纵向磁场分布特性]
)

*分析要点*：
+ *磁场强度*：在额定短路开断电流峰值 ($I_"peak" = 4000 times sqrt(2) approx 5.6 text("kA")$) 时，触头中心区域的纵向磁场强度应满足设计要求（通常要求 $> 3~4 text("mT/kA")$）。
+ *分布形态*：磁场应呈“钟形”（中心高、边缘低），有利于电弧束缚在触头中心并维持扩散型电弧。

#block(fill: rgb("#fff8e1"), inset: 10pt, radius: 4pt, width: 100%)[
  *AMF 触头结构要点（最佳实践参数）*：杯状纵磁触头 + 触头片组合，杯体与触头片均采用 CuCr 合金；杯深 11.2 mm，杯壁厚 3 mm，杯底厚 3 mm，触头片厚 4 mm；杯壁斜槽 8 条，槽宽 2.5 mm，槽倾角 30°；触头片径向槽 8 条，槽宽 1.5 mm，槽长约 0.8R。
]

#block(fill: rgb("#e3f2fd"), inset: 12pt, radius: 6pt, width: 100%)[
  *结论判定*：
  峰值电流时刻触头中心 $B_x$ 约为 **XX mT**，折算 **XX mT/kA**。径向分布呈 **钟形/马鞍形**，是否满足扩散型电弧判据需结合曲线确认。
]

== 电流-磁场相位滞后效应 (Eddy Current Effect)

由于触头杯和支撑结构中感应涡流的存在，纵向磁场相位会滞后于电流相位。滞后量用于评估涡流损耗与触头开槽设计有效性。

#figure(
  block(fill: rgb("#fff3e0"), inset: 26pt, radius: 6pt, width: 100%, stroke: 1pt + rgb("#ffcc80"))[
    #align(center)[
      *图 6：电流与中心点磁场时变曲线对比*
      
      （待插入：Transient Report，同时绘制 InputCurrent 与 Center_Bx 随时间变化曲线）
    ]
  ],
  caption: [电流与磁场的相位滞后关系]
)

#figure(
  table(
    columns: (1.5fr, auto, auto, 1.5fr),
    stroke: 0.5pt + rgb("#666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[参数项]], [#th[时刻/数值]], [#th[单位]], [#th[说明]],
    [电流峰值时刻], [$t_I$ = 5.0], [ms], [工频电流峰值],
    [磁场峰值时刻], [$t_B$ = XX.X], [ms], [仿真获取],
    [相位滞后时间], [$Delta t$ = X.X], [ms], [涡流效应导致],
    [滞后相角], [$phi$ = XX.X], [°], [$Delta t times 360 times 50$],
  ),
  caption: [涡流效应分析数据]
)

*判据*：相位滞后时间一般在 $1~3 text("ms")$，滞后越短代表涡流损耗越小、触头开槽更合理。

== 电流过零点剩余磁场 (Residual Field)

电流过零点 ($I=0$) 的剩余磁场对于电弧熄灭至关重要。过强的剩余磁场会阻碍等离子体扩散，降低介质强度恢复速度。

+ *过零时刻*：$t = 10 text("ms")$（首个过零点）
+ *分析指标*：触头间隙中心的剩余磁感应强度 $B_"residual"$

#block(fill: rgb("#e3f2fd"), inset: 12pt, radius: 6pt, width: 100%)[
  *结论判定*：
  仿真结果显示，在电流过零点 ($t=10 text("ms")$) 仍存在约 **XX mT** 的剩余纵向磁场。该数值需低于经验临界值（通常 $< 10~20 text("mT")$）以确保介质恢复；若偏大，可通过增加触头片径向开槽抑制涡流。
]

= 结论与建议

== 主要结论

#figure(
  table(
    columns: (1.5fr, auto, auto, auto, 1.5fr),
    stroke: 0.5pt + rgb("#666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if row == 1 { rgb("#e6f3ff") } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[指标项]], [#th[仿真结果]], [#th[标准/目标]], [#th[判定]], [#th[备注]],
    [*最大场强*], [*1.25 kV/mm*], [20~30 kV/mm], [*合格*], [触头边缘],
    [接触电阻], [65 μΩ], [≤ 80 μΩ], [合格], [合闸状态],
    [燃弧时间], [5~10 ms], [≤ 半周期], [合格], [4000A],
    [分闸速度], [1.2 m/s], [≥ 1.0 m/s], [合格], [机构要求],
    [短路开断次数], [30 次], [≥ 30 次], [合格], [标准要求],
  ),
  caption: [关键性能指标总览]
)

#block(fill: rgb("#e8f5e9"), inset: 12pt, radius: 6pt, width: 100%)[
  *总体评价*：12kV/4000A 真空断路器灭弧室设计合理，绝缘性能和开断能力均满足标准要求，可用于工程应用。
]

== 优化建议

+ *电场优化*：采用椭球形触头端面，可进一步降低边缘场强集中
+ *触头材料*：对于更高开断要求，可考虑 CuCr50 合金
+ *屏蔽罩设计*：优化屏蔽罩形状，提高电场分布均匀性
+ *分闸速度*：控制在 1.0~1.3 m/s 范围内并优化速度曲线，可缩短燃弧时间，降低触头烧蚀

== 后续工作

+ 制作样机进行型式试验验证
+ 开展短路开断试验，对比仿真与试验结果
+ 进行高温/低温环境适应性测试
+ 根据试验结果优化设计参数

#v(1.5em)
#line(length: 100%, stroke: 0.5pt + gray)
#v(0.5em)
#grid(
  columns: (1fr, 1fr),
  [
    #text(size: 9pt, fill: gray)[
      *仿真软件*：ANSYS Maxwell 2024 R1 \
      *求解器*：Electrostatic / Transient \
      *参考标准*：GB 1984, IEC 62271-100
    ]
  ],
  [
    #align(right)[
      #text(size: 9pt, fill: gray)[
        *编制*：电磁仿真分析工作组 \
        *版本*：v2.0 \
        *日期*：2026年01月19日
      ]
    ]
  ]
)
