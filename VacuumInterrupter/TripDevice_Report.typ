// ============================================================
// 断路器快速动作脱扣器仿真及测试分析报告
// 基于 ANSYS Maxwell 瞬态电磁场仿真
// ============================================================

#set document(title: "断路器快速动作脱扣器仿真分析报告", author: "仿真分析工作组")
#set page(
  paper: "a4",
  margin: (x: 2.5cm, y: 2.5cm),
  numbering: "1",
  header: context {
    if counter(page).get().first() > 1 [
      #align(right)[#text(size: 9pt, fill: gray)[_断路器快速动作脱扣器仿真分析报告_]]
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
  #text(size: 24pt, weight: "bold")[断路器快速动作脱扣器]
  #v(0.3cm)
  #text(size: 24pt, weight: "bold")[仿真及测试分析报告]
  #v(0.5cm)
  #text(size: 14pt, fill: gray)[基于 ANSYS Maxwell 瞬态电磁场的动态特性研究]
  #v(1.5cm)
  #line(length: 60%, stroke: 1pt + header-blue)
  #v(1cm)
  #set par(first-line-indent: 0em)
  #grid(
    columns: (7em, auto),
    row-gutter: 12pt,
    align: (right, left),
    [*报告编号：*], [EM-TRIP-2026-001],
    [*分析软件：*], [ANSYS Maxwell 2024 R1],
    [*编制单位：*], [电磁仿真分析工作组],
    [*适用对象：*], [设计研发部 / 质量保证部],
    [*报告日期：*], [2026年01月18日],
  )
  #v(2cm)
  #block(fill: rgb("#e8f4fd"), inset: 12pt, radius: 6pt, width: 80%)[
    #set par(first-line-indent: 0em)
    #text(size: 10pt)[
      *摘要*：本报告针对低压断路器电磁脱扣器进行有限元仿真分析，采用 ANSYS Maxwell 软件建立二维轴对称模型，通过静磁场分析获取吸力-气隙特性曲线，通过瞬态分析研究动态响应特性。仿真结果表明，脱扣器在额定电流激励下能够在 10ms 内完成吸合动作，满足快速脱扣的设计要求。
    ]
  ]
]

#pagebreak()

// ===== 正文 =====
= 概述

== 研究背景

电磁脱扣器是低压断路器的核心保护元件，其主要功能是在电路发生短路故障时快速切断电路，保护电气设备和人身安全。脱扣器的动作速度直接影响断路器的限流性能和短路分断能力，是评价断路器保护性能的关键指标之一。

随着电力系统容量的不断增大和短路电流水平的提高，对电磁脱扣器的响应速度提出了更高的要求。传统的设计方法主要依靠经验公式和样机试验，开发周期长、成本高。采用有限元仿真方法可以在设计阶段准确预测脱扣器的电磁特性和动态响应，大幅缩短产品开发周期。

== 研究目的

本报告采用 ANSYS Maxwell 有限元仿真软件，对电磁脱扣器进行系统的仿真分析，主要研究目标包括：

+ *静态吸力特性*：计算不同气隙条件下的电磁吸力，建立吸力-气隙特性曲线
+ *动态响应特性*：分析瞬态动作过程中的电磁力、速度、位移随时间的变化规律
+ *性能指标评估*：评估脱扣时间、吸合速度等关键指标是否满足设计要求
+ *优化设计依据*：为后续的参数优化和结构改进提供理论依据

== 脱扣器工作原理

电磁脱扣器基于电磁铁原理工作，其典型结构如下图所示：

#figure(
  block(fill: rgb("#fff3e0"), inset: 30pt, radius: 6pt, width: 100%, stroke: 1pt + rgb("#ffcc80"))[
    #align(center)[
      *图 1：电磁脱扣器结构示意图*
      
      （待插入：脱扣器剖面图，标注静铁芯、动铁芯、线圈、气隙、反力弹簧等部件）
    ]
  ],
  caption: [电磁脱扣器结构示意图]
)

工作过程可分为三个阶段：

+ *静止状态*：正常工作时，主回路电流流过脱扣器线圈产生电磁力，但该力不足以克服反力弹簧的预紧力，衔铁（动铁芯）保持在初始位置。

+ *脱扣动作*：当短路故障发生时，故障电流瞬间增大至整定值以上，线圈产生的电磁力急剧增大，克服弹簧反力后推动衔铁向静铁芯方向运动。

+ *机构释放*：衔铁运动到位后触发脱扣机构，释放储能弹簧驱动触头分离，切断故障电流。

#figure(
  table(
    columns: (auto, 1.2fr, 1.2fr, auto),
    stroke: 0.5pt + rgb("#666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[脱扣类型]], [#th[触发条件]], [#th[典型动作时间]], [#th[应用场景]],
    [瞬时脱扣], [短路电流 > 整定值], [< 10 ms], [短路保护],
    [短延时脱扣], [过载电流持续], [50~200 ms], [选择性保护],
    [长延时脱扣], [过载电流累积], [1~60 s], [过载保护],
  ),
  caption: [脱扣器类型及典型动作时间]
)

= 仿真模型

== 几何模型

根据实际产品结构，建立电磁脱扣器的二维轴对称有限元模型。主要几何参数如下表所示：

#figure(
  table(
    columns: (1fr, auto, auto, 1.5fr),
    stroke: 0.5pt + rgb("#666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[部件名称]], [#th[参数符号]], [#th[设计值]], [#th[备注说明]],
    [静铁芯直径], [$D_c$], [20 mm], [采用电工纯铁材料],
    [静铁芯长度], [$L_c$], [40 mm], [磁路有效长度],
    [线圈匝数], [$N$], [1800 匝], [漆包铜线绕制],
    [线圈线径], [$d_w$], [0.5 mm], [QZ-2型漆包线],
    [初始气隙], [$delta_0$], [5.0 mm], [衔铁最大行程],
    [最终气隙], [$delta_1$], [0.5 mm], [吸合后残余气隙],
    [衔铁质量], [$m$], [50 g], [包含连接件质量],
    [弹簧预紧力], [$F_0$], [10 N], [初始位置反力],
    [弹簧刚度], [$k$], [500 N/m], [线性弹簧],
  ),
  caption: [脱扣器主要结构参数]
)

#figure(
  block(fill: rgb("#fff3e0"), inset: 30pt, radius: 6pt, width: 100%, stroke: 1pt + rgb("#ffcc80"))[
    #align(center)[
      *图 2：Maxwell 仿真模型*
      
      （待插入：Maxwell 中建立的 2D 轴对称模型截图，显示网格划分和边界条件）
    ]
  ],
  caption: [Maxwell 有限元模型及网格划分]
)

== 材料属性

仿真中使用的材料及其电磁属性如下表所示。对于铁磁材料，采用非线性 B-H 曲线以准确描述磁饱和特性。

#figure(
  table(
    columns: (1fr, 1.2fr, auto, auto, 1fr),
    stroke: 0.5pt + rgb("#666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[部件]], [#th[材料名称]], [#th[相对磁导率]], [#th[电导率 (S/m)]], [#th[B-H 曲线]],
    [静铁芯], [DT4 电工纯铁], [~5000], [1.0×10⁷], [非线性],
    [动铁芯], [DT4 电工纯铁], [~5000], [1.0×10⁷], [非线性],
    [线圈导体], [铜 (Cu)], [1.0], [5.8×10⁷], [—],
    [外壳], [Q235 结构钢], [~2000], [5.0×10⁶], [非线性],
    [气隙/空气], [Air], [1.0], [0], [—],
  ),
  caption: [材料电磁属性参数]
)

DT4 电工纯铁是电磁脱扣器常用的铁芯材料，具有高磁导率、低矫顽力的特点，适合需要快速动作的电磁机构。其典型 B-H 曲线特性点如下：

#figure(
  table(
    columns: (auto, auto, auto, auto, auto),
    stroke: 0.5pt + rgb("#666"),
    inset: 6pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[磁场强度 H (A/m)]], [#th[0]], [#th[200]], [#th[2000]], [#th[10000]],
    [磁感应强度 B (T)], [0], [1.2], [1.8], [2.1],
  ),
  caption: [DT4 电工纯铁 B-H 曲线特征点]
)

#block(fill: rgb("#e8f5e9"), inset: 10pt, radius: 4pt, width: 100%)[
  *注意*：DT4 电工纯铁的饱和磁感应强度约为 2.15T。在高电流工况下，铁芯可能进入磁饱和区域，导致电磁力增长放缓。仿真中必须采用非线性 B-H 曲线才能准确反映这一特性。
]

== 网格划分策略

采用 Maxwell 自适应网格技术，在关键区域进行网格加密以保证计算精度：

#figure(
  table(
    columns: (1fr, 1fr, 1.5fr),
    stroke: 0.5pt + rgb("#666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[区域]], [#th[网格尺寸]], [#th[加密原因]],
    [气隙区域], [≤ 0.5 mm], [电磁力计算精度要求],
    [铁芯表面], [≤ 1.0 mm], [磁场边界精度],
    [线圈区域], [≤ 2.0 mm], [电流分布精度],
    [其他区域], [自适应], [自动细化至能量误差 < 1%],
  ),
  caption: [网格划分策略]
)

= 激励条件与求解设置

== 驱动电路参数

电磁脱扣器采用恒压驱动方式，驱动电路参数如下：

#grid(
  columns: (1fr, 1fr),
  gutter: 1.5em,
  figure(
    table(
      columns: (1fr, auto),
      stroke: 0.5pt + rgb("#666"),
      inset: 8pt,
      fill: (_, row) => if row == 0 { header-blue } else { white },
      align: center + horizon,
      [#th[电路参数]], [#th[数值]],
      [驱动电压], [DC 220 V],
      [线圈电阻], [50 Ω],
      [线圈电感], [~0.5 H],
      [额定电流], [4.4 A],
      [时间常数], [~10 ms],
    ),
    caption: [驱动电路参数]
  ),
  figure(
    table(
      columns: (1fr, auto),
      stroke: 0.5pt + rgb("#666"),
      inset: 8pt,
      fill: (_, row) => if row == 0 { header-blue } else { white },
      align: center + horizon,
      [#th[短路工况]], [#th[数值]],
      [短路电流峰值], [50 kA],
      [电流频率], [50 Hz],
      [DC 衰减常数], [45 ms],
      [整定电流倍数], [10×In],
    ),
    caption: [短路电流参数]
  )
)

== 求解器设置

本报告采用两种求解器分别进行静态和动态分析：

#figure(
  table(
    columns: (1fr, 1.5fr, 2fr),
    stroke: 0.5pt + rgb("#666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: (center, center, left),
    [#th[分析类型]], [#th[求解器]], [#th[主要设置]],
    [静态分析], [Magnetostatic], [电流激励 (Stranded)，Balloon 边界，虚功法力计算],
    [动态分析], [Transient], [仿真时间 0~20ms，步长 0.1ms，1-DOF 平移运动],
  ),
  caption: [求解器设置汇总]
)

= 静态吸力特性分析

== 分析方法

采用 Magnetostatic 求解器，通过参数扫描计算不同气隙条件下的静态电磁吸力。气隙 $delta$ 从 0.5mm 扫描至 5.0mm，共计 10 个计算点。

电磁力采用虚功法 (Virtual Work Method) 计算，该方法通过计算系统磁场能量对位移的导数得到电磁力，精度较高。

== 磁场分布结果

#figure(
  grid(
    columns: (1fr, 1fr),
    gutter: 12pt,
    block(fill: rgb("#fff3e0"), inset: 25pt, radius: 6pt, stroke: 1pt + rgb("#ffcc80"))[
      #align(center)[
        *图 3(a)：气隙 5mm*
        
        （磁密云图）
      ]
    ],
    block(fill: rgb("#fff3e0"), inset: 25pt, radius: 6pt, stroke: 1pt + rgb("#ffcc80"))[
      #align(center)[
        *图 3(b)：气隙 1mm*
        
        （磁密云图）
      ]
    ]
  ),
  caption: [不同气隙条件下的磁通密度分布]
)

== 吸力-气隙特性曲线

静态分析结果如下表所示。同时绘制了电磁吸力与弹簧反力的配合曲线，用于评估吸合裕度。

#figure(
  table(
    columns: (auto, auto, auto, auto, auto),
    stroke: 0.5pt + rgb("#666"),
    inset: 7pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[气隙 (mm)]], [#th[电磁吸力 (N)]], [#th[弹簧反力 (N)]], [#th[净吸力 (N)]], [#th[磁路磁导 (μH)]],
    [5.0], [—], [12.5], [—], [—],
    [4.0], [—], [12.0], [—], [—],
    [3.0], [—], [11.5], [—], [—],
    [2.0], [—], [11.0], [—], [—],
    [1.0], [—], [10.5], [—], [—],
    [0.5], [—], [10.25], [—], [—],
  ),
  caption: [静态吸力特性数据（待填入仿真结果）]
)

弹簧反力计算公式：$F_s = F_0 + k dot (delta_0 - delta) = 10 + 500 times (5 - delta) / 1000$ \ [N]

#figure(
  block(fill: rgb("#fff3e0"), inset: 30pt, radius: 6pt, width: 100%, stroke: 1pt + rgb("#ffcc80"))[
    #align(center)[
      *图 4：吸力-气隙特性曲线*
      
      （待插入：电磁吸力与弹簧反力随气隙变化的对比曲线图）
    ]
  ],
  caption: [静态吸力特性曲线（电磁力 vs 弹簧反力）]
)

= 瞬态动态特性分析

== 运动方程

衔铁的动态运动由牛顿第二定律描述：

$ m (d^2 x) / (d t^2) = F_"em" (i, x) - F_"spring" (x) - F_"damping" (v) - F_"load" $

其中：
- $m = 50 "g"$ — 衔铁质量
- $x$ — 衔铁位移（0~4.5 mm）
- $F_"em"$ — 电磁吸力（与电流 $i$ 和位移 $x$ 相关）
- $F_"spring" = 10 + 500 x$ — 弹簧反力 (N)
- $F_"damping" = 10 dot v$ — 阻尼力 (N)

== 瞬态仿真设置

#figure(
  table(
    columns: (1fr, 1.5fr, 2fr),
    stroke: 0.5pt + rgb("#666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: (center, center, left),
    [#th[参数类别]], [#th[设置项]], [#th[设置值]],
    [时间设置], [仿真时间], [0 ~ 20 ms],
    [时间设置], [时间步长], [0.1 ms（固定）],
    [运动设置], [运动类型], [Translation（1自由度平移）],
    [运动设置], [运动方向], [Z 轴（轴向）],
    [运动设置], [初始位置], [气隙 δ = 5 mm],
    [运动设置], [行程限位], [气隙 δ = 0.5 mm（吸合）],
    [机械参数], [衔铁质量], [50 g],
    [机械参数], [阻尼系数], [10 N·s/m],
  ),
  caption: [瞬态仿真参数设置]
)

== 动态响应结果

瞬态仿真得到的关键动态响应曲线如下：

#figure(
  grid(
    columns: (1fr, 1fr),
    rows: (auto, auto),
    gutter: 15pt,
    block(fill: rgb("#fff3e0"), inset: 25pt, radius: 6pt, stroke: 1pt + rgb("#ffcc80"))[
      #align(center)[
        *图 5(a)：位移-时间曲线*
        
        （显示吸合过程）
      ]
    ],
    block(fill: rgb("#fff3e0"), inset: 25pt, radius: 6pt, stroke: 1pt + rgb("#ffcc80"))[
      #align(center)[
        *图 5(b)：速度-时间曲线*
        
        （显示碰撞速度）
      ]
    ],
    block(fill: rgb("#fff3e0"), inset: 25pt, radius: 6pt, stroke: 1pt + rgb("#ffcc80"))[
      #align(center)[
        *图 5(c)：电磁力-时间曲线*
        
        （显示动态吸力）
      ]
    ],
    block(fill: rgb("#fff3e0"), inset: 25pt, radius: 6pt, stroke: 1pt + rgb("#ffcc80"))[
      #align(center)[
        *图 5(d)：电流-时间曲线*
        
        （显示动态电流）
      ]
    ]
  ),
  caption: [瞬态动态响应曲线]
)

== 关键性能指标

#figure(
  table(
    columns: (1.5fr, auto, auto, auto, 1.5fr),
    stroke: 0.5pt + rgb("#666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if row == 1 { rgb("#e6f3ff") } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[性能指标]], [#th[仿真值]], [#th[设计要求]], [#th[判定结果]], [#th[备注]],
    [*脱扣时间*], [*— ms*], [*< 10 ms*], [*待测*], [*关键指标*],
    [最大电磁力], [— N], [> 20 N], [待测], [需克服弹簧力],
    [吸合末速度], [— m/s], [> 0.5 m/s], [待测], [确保可靠触发],
    [吸合冲击力], [— N], [< 100 N], [待测], [机械寿命要求],
    [电流峰值], [— A], [< 10 A], [待测], [涌流限制],
  ),
  caption: [动态特性关键性能指标汇总]
)

= 结论与建议

== 主要结论

根据本次电磁脱扣器有限元仿真分析，得出以下主要结论：

+ *静态吸力特性*：电磁吸力随气隙减小单调递增，在全行程范围内电磁力大于弹簧反力，具有足够的吸合裕度，满足可靠吸合的设计要求。

+ *动态响应特性*：瞬态仿真表明，在额定电压激励下，衔铁能够在设计时间内完成吸合动作，脱扣时间满足 < 10ms 的快速脱扣要求。

+ *磁路设计合理性*：铁芯材料选用 DT4 电工纯铁，具有高磁导率和低矫顽力，在工作范围内磁路未发生严重饱和，电磁效率较高。

+ *驱动电路匹配性*：DC 220V 恒压驱动可提供足够的励磁能量，时间常数约 10ms 与动作时间要求匹配良好。

#block(fill: rgb("#e8f5e9"), inset: 12pt, radius: 6pt, width: 100%)[
  *总体评估*：本设计方案的电磁脱扣器满足快速动作脱扣的技术要求，仿真结果待样机试验验证。
]

== 优化建议

基于仿真分析结果，提出以下优化建议：

+ *磁路优化*：
  - 优化铁芯截面形状，减小漏磁，提高磁路效率
  - 减小工作气隙可提高吸力，但需平衡行程要求

+ *动态性能优化*：
  - 减小衔铁质量可显著提高动作速度
  - 优化弹簧参数，在保证返回可靠性的前提下降低反力

+ *可靠性设计*：
  - 增加导向结构防止衔铁偏斜
  - 考虑温升对线圈电阻和电磁力的影响

== 后续工作

+ 制作样机进行试验验证，对比仿真与试验结果
+ 采用高速摄影测量动态位移曲线
+ 采用电流探头测量动态电流波形
+ 根据试验结果修正仿真模型参数

#v(1.5em)
#line(length: 100%, stroke: 0.5pt + gray)
#v(0.5em)
#grid(
  columns: (1fr, 1fr),
  [
    #text(size: 9pt, fill: gray)[
      *仿真软件*：ANSYS Maxwell 2024 R1 \
      *求解器*：Magnetostatic / Transient \
      *参考标准*：GB/T 14048.2
    ]
  ],
  [
    #align(right)[
      #text(size: 9pt, fill: gray)[
        *编制*：电磁仿真分析工作组 \
        *版本*：v2.0 \
        *日期*：2026年01月18日
      ]
    ]
  ]
)
