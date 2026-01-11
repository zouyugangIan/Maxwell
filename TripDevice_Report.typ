// ============================================================
// 断路器快速动作脱扣器仿真及测试分析报告
// 基于 ANSYS Maxwell 瞬态电磁场仿真
// ============================================================

#set document(title: "断路器快速动作脱扣器仿真分析报告", author: "仿真分析工作组")
#set page(
  paper: "a4",
  margin: (x: 2.5cm, y: 2.54cm),
  numbering: "1",
  header: align(right)[_断路器快速动作脱扣器仿真分析报告_],
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
  #text(size: 22pt, weight: "bold")[断路器快速动作脱扣器]
  #v(0.3cm)
  #text(size: 22pt, weight: "bold")[仿真及测试分析报告]
  #v(0.4cm)
  #text(size: 16pt, weight: "bold")[基于Maxwell瞬态电磁场的动态特性研究]
  #v(1cm)
  #line(length: 50%, stroke: 0.5pt)
  #v(0.8cm)
  #set par(first-line-indent: 0em)
  #grid(
    columns: (6em, auto),
    row-gutter: 10pt,
    align: (right, left),
    [*报告编号：*], [EM-TRIP-001],
    [*分析软件：*], [ANSYS Maxwell 2024 R1],
    [*编制单位：*], [仿真分析工作组],
    [*适用对象：*], [设计研发部],
  )
  #v(1.5cm)
]

// ===== 正文 =====
= 概述

== 研究背景

电磁脱扣器是断路器的核心保护元件，用于在发生短路故障时快速切断电路。其动作速度直接影响断路器的限流性能和短路分断能力。本报告采用有限元仿真方法，对电磁脱扣器的静态电磁吸力特性和动态运动特性进行分析研究。

#block(fill: rgb("#e3f2fd"), inset: 10pt, radius: 4pt, width: 100%)[
  *研究目的*：
  - 计算电磁脱扣器的静态吸力特性曲线
  - 分析瞬态动作过程中的电磁力、速度、位移
  - 评估脱扣时间是否满足设计要求
  - 为优化设计提供理论依据
]

== 脱扣器工作原理

电磁脱扣器的工作原理如下：

+ *正常工作*：主回路电流流过脱扣器线圈，产生的电磁力不足以克服反力弹簧，衔铁保持静止
+ *短路脱扣*：当短路电流超过整定值时，电磁力突增，克服弹簧反力吸合衔铁，触发脱扣机构
+ *快速分断*：脱扣机构释放储能弹簧，驱动触头分离，切断故障电流

#figure(
  table(
    columns: (auto, 1.5fr, 1.5fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[脱扣类型]], [#th[触发条件]], [#th[典型动作时间]],
    [瞬时脱扣], [短路电流 > 整定值], [< 10 ms],
    [短延时脱扣], [过载电流持续], [50-200 ms],
    [长延时脱扣], [过载电流累积], [1-60 s],
  ),
  caption: [脱扣器类型及动作时间]
)

= 仿真模型

== 几何模型

脱扣器的主要结构参数如下：

#figure(
  table(
    columns: (auto, auto, auto, 1.5fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[参数]], [#th[符号]], [#th[数值]], [#th[说明]],
    [铁芯直径], [$D_c$], [20 mm], [静铁芯],
    [铁芯长度], [$L_c$], [40 mm], [磁路有效长度],
    [线圈匝数], [$N$], [1800 匝], [设计值],
    [线径], [$d_w$], [0.5 mm], [漆包线],
    [气隙长度], [$delta$], [5 mm], [初始气隙],
    [衔铁质量], [$m$], [50 g], [动铁芯],
    [弹簧预紧力], [$F_0$], [10 N], [反力弹簧],
    [弹簧刚度], [$k$], [500 N/m], [弹簧常数],
  ),
  caption: [脱扣器主要结构参数]
)

// TODO: 插入几何模型图
// #figure(
//   image("field_plots/tripper/geometry.png", width: 80%),
//   caption: [脱扣器三维几何模型]
// )

#block(fill: rgb("#fff3e0"), inset: 10pt, radius: 4pt, width: 100%)[
  *图片待补充*：完成Maxwell建模后，在此处插入几何模型截图。
]

== 材料属性

#figure(
  table(
    columns: (1fr, 1.2fr, auto, auto, 1fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[部件]], [#th[材料]], [#th[相对磁导率 μr]], [#th[电导率 (S/m)]], [#th[B-H曲线]],
    [静铁芯], [DT4电工纯铁], [~5000], [1×10⁷], [非线性],
    [动铁芯（衔铁）], [DT4电工纯铁], [~5000], [1×10⁷], [非线性],
    [线圈], [铜 (Cu)], [1], [5.8×10⁷], [—],
    [外壳], [Q235钢], [~2000], [5×10⁶], [非线性],
    [永磁体], [NdFeB N35], [1.05], [6.25×10⁵], [退磁曲线],
  ),
  caption: [材料电磁属性]
)

== B-H磁化曲线

铁磁材料的非线性B-H曲线对电磁计算至关重要。DT4电工纯铁的典型B-H曲线如下：

#figure(
  table(
    columns: (auto, auto, auto, auto, auto, auto),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[H (A/m)]], [#th[B (T)]], [#th[H (A/m)]], [#th[B (T)]], [#th[H (A/m)]], [#th[B (T)]],
    [0], [0], [200], [1.2], [2000], [1.8],
    [50], [0.5], [400], [1.4], [5000], [2.0],
    [100], [0.9], [800], [1.6], [10000], [2.1],
  ),
  caption: [DT4电工纯铁B-H曲线数据（部分）]
)

#block(fill: rgb("#e8f5e9"), inset: 10pt, radius: 4pt, width: 100%)[
  *饱和特性*：DT4电工纯铁饱和磁感应强度约2.15T，在高电流工况下需注意磁路饱和对电磁力的影响。
]

== 有限元网格

#figure(
  table(
    columns: (1fr, 1fr, 1.5fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[参数]], [#th[设置值]], [#th[说明]],
    [分析类型], [2D轴对称 / 3D], [根据几何对称性选择],
    [网格类型], [三角形/四面体], [自适应细化],
    [气隙网格], [最大0.5 mm], [关键区域加密],
    [自适应细化], [能量误差 < 1%], [Maxwell自动细化],
    [总单元数], [~50,000], [2D模型],
  ),
  caption: [网格划分设置]
)

= 激励条件

== 驱动电路

脱扣器的驱动电路参数如下：

#figure(
  table(
    columns: (1fr, auto, 1.5fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[参数]], [#th[数值]], [#th[说明]],
    [驱动类型], [恒压驱动], [DC 220V / DC 110V],
    [驱动电压], [DC 220V], [额定控制电压],
    [线圈电阻], [50 Ω], [20°C时],
    [线圈电感], [~0.5 H], [依赖气隙长度],
    [额定电流], [4.4 A], [稳态电流],
    [时间常数], [~10 ms], [τ = L/R],
  ),
  caption: [驱动电路参数]
)

== 短路电流波形

对于瞬时脱扣仿真，采用以下短路电流波形：

#figure(
  table(
    columns: (1fr, auto, 1.5fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[参数]], [#th[数值]], [#th[说明]],
    [短路电流峰值], [50 kA], [预期短路电流],
    [电流频率], [50 Hz], [工频],
    [非周期分量衰减], [τ = 45 ms], [DC衰减时间常数],
    [整定电流倍数], [10×In], [瞬时脱扣整定值],
  ),
  caption: [短路电流参数]
)

= 静态吸力特性分析

== 静磁场仿真设置

#figure(
  table(
    columns: (1fr, 1.5fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: (left, left),
    [#th[参数]], [#th[设置值]],
    [求解器类型], [Magnetostatic],
    [激励类型], [电流激励 (Stranded)],
    [边界条件], [Balloon (无穷远)],
    [虚拟力计算], [Virtual Work Method],
    [自适应细化], [开启，误差目标1%],
  ),
  caption: [静磁场仿真设置]
)

== 磁通密度分布

// TODO: 插入磁通密度云图
// #figure(
//   grid(columns: 2, gutter: 12pt,
//     image("field_plots/tripper/Mag_B_gap5mm.png", width: 100%),
//     image("field_plots/tripper/Mag_B_gap1mm.png", width: 100%),
//   ),
//   caption: [磁通密度分布（左：气隙5mm，右：气隙1mm）]
// )

#block(fill: rgb("#fff3e0"), inset: 10pt, radius: 4pt, width: 100%)[
  *图片待补充*：完成Maxwell静磁场仿真后，在此处插入磁通密度云图。
]

== 静态吸力曲线

通过改变气隙长度δ（0.5mm~5mm），计算不同气隙下的电磁吸力F：

#figure(
  table(
    columns: (auto, auto, auto, auto, auto, auto),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[气隙 δ (mm)]], [#th[电磁吸力 F (N)]], [#th[弹簧反力 (N)]], [#th[净力 (N)]], [#th[磁导 (μH)]], [#th[电流 (A)]],
    [5.0], [—], [12.5], [—], [—], [4.4],
    [4.0], [—], [12.0], [—], [—], [4.4],
    [3.0], [—], [11.5], [—], [—], [4.4],
    [2.0], [—], [11.0], [—], [—], [4.4],
    [1.0], [—], [10.5], [—], [—], [4.4],
    [0.5], [—], [10.25], [—], [—], [4.4],
  ),
  caption: [静态吸力特性数据（待填入仿真结果）]
)

#h(-2em)*反力计算*：弹簧反力 $F_s = F_0 + k dot (delta_0 - delta) = 10 + 500 times (5 - delta) / 1000$ N

// TODO: 插入吸力特性曲线图
// #figure(
//   image("field_plots/tripper/force_vs_gap.png", width: 80%),
//   caption: [静态吸力特性曲线（电磁力 vs 弹簧反力）]
// )

#block(fill: rgb("#fff3e0"), inset: 10pt, radius: 4pt, width: 100%)[
  *图片待补充*：完成参数扫描后，在此处插入吸力特性曲线图。
]

= 瞬态动态特性分析

== 瞬态仿真设置

#figure(
  table(
    columns: (1fr, 1.5fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: (left, left),
    [#th[参数]], [#th[设置值]],
    [求解器类型], [Transient],
    [仿真时间], [0 ~ 20 ms],
    [时间步长], [0.1 ms (固定) / 自适应],
    [运动设置], [Translation (1-DOF)],
    [运动方向], [Z轴 (轴向)],
    [初始位置], [气隙 δ = 5 mm],
    [运动终止], [气隙 δ = 0.5 mm (吸合)],
    [机械阻尼], [10 N·s/m],
  ),
  caption: [瞬态仿真设置]
)

== 运动方程

衔铁的运动由以下方程描述：

$ m (d^2 x) / (d t^2) = F_"em" (i, x) - F_"spring" (x) - F_"friction" - F_"trip" $

其中：
- $m$ — 衔铁质量 (kg)
- $x$ — 衔铁位移 (m)
- $F_"em"$ — 电磁吸力 (N)，与电流$i$和位移$x$相关
- $F_"spring"$ — 弹簧反力 (N)
- $F_"friction"$ — 摩擦力 (N)
- $F_"trip"$ — 脱扣力 (N)

== 电压平衡方程

线圈的电压方程：

$ U = i R + (d Psi) / (d t) = i R + L(x) (d i) / (d t) + i (d L) / (d x) (d x) / (d t) $

其中磁链 $Psi = L(x) dot i$，电感$L$随气隙变化。

== 动态仿真结果

=== 位移-时间曲线

// TODO: 插入位移曲线
// #figure(
//   image("field_plots/tripper/displacement_vs_time.png", width: 80%),
//   caption: [衔铁位移随时间变化曲线]
// )

#block(fill: rgb("#fff3e0"), inset: 10pt, radius: 4pt, width: 100%)[
  *图片待补充*：完成瞬态仿真后，在此处插入位移-时间曲线。
]

=== 速度-时间曲线

// TODO: 插入速度曲线
// #figure(
//   image("field_plots/tripper/velocity_vs_time.png", width: 80%),
//   caption: [衔铁速度随时间变化曲线]
// )

#block(fill: rgb("#fff3e0"), inset: 10pt, radius: 4pt, width: 100%)[
  *图片待补充*：完成瞬态仿真后，在此处插入速度-时间曲线。
]

=== 电磁力-时间曲线

// TODO: 插入电磁力曲线
// #figure(
//   image("field_plots/tripper/force_vs_time.png", width: 80%),
//   caption: [电磁吸力随时间变化曲线]
// )

#block(fill: rgb("#fff3e0"), inset: 10pt, radius: 4pt, width: 100%)[
  *图片待补充*：完成瞬态仿真后，在此处插入电磁力-时间曲线。
]

=== 电流-时间曲线

// TODO: 插入电流曲线
// #figure(
//   image("field_plots/tripper/current_vs_time.png", width: 80%),
//   caption: [线圈电流随时间变化曲线]
// )

#block(fill: rgb("#fff3e0"), inset: 10pt, radius: 4pt, width: 100%)[
  *图片待补充*：完成瞬态仿真后，在此处插入电流-时间曲线。
]

== 动态特性汇总

#figure(
  table(
    columns: (1.5fr, auto, auto, auto),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if row == 1 { rgb("#e6f3ff") } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[参数]], [#th[仿真值]], [#th[设计目标]], [#th[判定]],
    [*脱扣时间*], [*— ms*], [*< 10 ms*], [*待测*],
    [最大电磁力], [— N], [> 20 N], [待测],
    [吸合速度], [— m/s], [> 0.5 m/s], [待测],
    [吸合冲击力], [— N], [< 100 N], [待测],
    [电流峰值], [— A], [< 10 A], [待测],
  ),
  caption: [动态特性参数汇总]
)

= 多物理场联合仿真

== 联合仿真方法

对于复杂的电磁机构分析，可采用多物理场联合仿真方法：

#figure(
  table(
    columns: (auto, 1.2fr, 1.5fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[物理场]], [#th[软件]], [#th[计算内容]],
    [电磁场], [ANSYS Maxwell], [磁场分布、电磁力],
    [电路], [ANSYS Simplorer / MATLAB], [电压/电流响应],
    [动力学], [ADAMS / MATLAB], [运动轨迹、碰撞],
    [热场], [ANSYS Icepak], [温升（如需）],
  ),
  caption: [多物理场联合仿真软件配置]
)

#block(fill: rgb("#e8f5e9"), inset: 10pt, radius: 4pt, width: 100%)[
  *推荐方案*：Maxwell + MATLAB/Simulink联合仿真，通过S-Function接口传递电磁力和位移数据。
]

== 联合仿真流程

```
1. Maxwell静磁场 → 生成力-位移-电流查找表 F(i, x)
2. MATLAB/Simulink → 构建电路方程和运动方程
3. 联合求解 → 迭代计算瞬态响应
4. 后处理 → 提取动态特性曲线
```

= 永磁机构分析（可选）

== 永磁保持原理

永磁操动机构采用永磁体提供保持力，具有以下优点：

+ 零功耗保持合闸/分闸状态
+ 结构简单，零部件少
+ 可靠性高，免维护

== 永磁体退磁分析

高温或强反向磁场可能导致永磁体退磁，需进行退磁分析：

// TODO: 插入退磁分析图
// #figure(
//   image("field_plots/tripper/demagnetization.png", width: 80%),
//   caption: [永磁体退磁区域分析]
// )

#block(fill: rgb("#fff3e0"), inset: 10pt, radius: 4pt, width: 100%)[
  *图片待补充*：如分析永磁机构，在此处插入退磁分析云图。
]

= 结论与建议

== 主要结论

根据本次电磁脱扣器仿真分析，得出以下主要结论：

+ *静态吸力特性*：电磁吸力随气隙减小而增大，满足脱扣力矩要求（待仿真结果验证）

+ *动态响应特性*：脱扣时间预期 < 10 ms，满足瞬时脱扣要求（待仿真结果验证）

+ *磁路设计*：铁芯材料DT4电工纯铁具有良好的磁导率和低矫顽力，适合快速动作机构

+ *驱动电路*：DC 220V恒压驱动可提供足够的励磁能量

#block(fill: rgb("#e8f5e9"), inset: 10pt, radius: 4pt, width: 100%)[
  *总体评估*：待仿真完成后填写总体评估结论。
]

== 优化建议

+ *磁路优化*：
  - 减少磁路中的气隙和非磁性间隙
  - 优化铁芯截面形状，减少磁阻
  
+ *线圈优化*：
  - 适当增加匝数可提高磁动势
  - 采用分数槽绕组降低铜耗

+ *动态优化*：
  - 减小衔铁质量提高动作速度
  - 优化弹簧参数平衡吸力与返回力

+ *可靠性*：
  - 增加防松动设计
  - 考虑高温工况下的性能降额

== 试验验证

建议进行以下试验验证仿真结果：

#figure(
  table(
    columns: (auto, 1.5fr, 1.5fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[试验项目]], [#th[测量参数]], [#th[测量方法]],
    [静态吸力], [F vs δ曲线], [拉力传感器],
    [动态特性], [位移-时间曲线], [位移传感器/高速摄影],
    [脱扣时间], [启动到吸合时间], [示波器],
    [吸合电流], [电流波形], [电流探头],
  ),
  caption: [试验验证项目]
)

#v(2em)
#line(length: 100%, stroke: 0.5pt)
#grid(
  columns: (1fr, 1fr),
  [
    #text(size: 9pt, fill: gray)[
      *仿真工具*：ANSYS Maxwell 2024 R1 \
      *求解器*：Magnetostatic / Transient \
      *联合仿真*：Maxwell + MATLAB
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

== 附录A：Maxwell Transient仿真步骤

=== A.1 模型创建

1. 创建2D轴对称模型或3D模型
2. 定义材料属性（特别是B-H曲线）
3. 划分网格，气隙区域加密

=== A.2 激励设置

1. 定义线圈激励（Stranded或Solid）
2. 连接外部电路（Excitation > External Circuit）
3. 设置驱动电压波形

=== A.3 运动设置

1. 创建Band对象包裹运动部件
2. 设置Motion Setup (Translation)
3. 定义运动质量、阻尼、弹簧力
4. 设置正负行程限位

=== A.4 求解设置

1. 设置仿真时间和步长
2. 开启自适应网格细化
3. 设置数据保存选项

== 附录B：仿真结果后处理

=== B.1 常用后处理变量

#figure(
  table(
    columns: (1fr, 1.5fr, 1fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: (left, left, left),
    [#th[变量名]], [#th[物理意义]], [#th[单位]],
    [Force_z], [Z方向电磁力], [N],
    [Position], [衔铁位移], [mm],
    [Speed], [衔铁速度], [m/s],
    [Current(Coil)], [线圈电流], [A],
    [Flux_Linkage], [磁链], [Wb],
    [CoreLoss], [铁损], [W],
  ),
  caption: [常用后处理变量]
)

#v(2cm)

#align(right)[
  编制人签字：#underline[#h(5cm)]
  
  审核人签字：#underline[#h(5cm)]
  
  日#h(4em)期：#underline[#h(5cm)]
]
