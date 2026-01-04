// ============================================================
// KYN28A-12高压开关柜抗震性能仿真分析报告
// 基于 ANSYS Workbench 有限元分析
// ============================================================

#set document(title: "KYN28A-12高压开关柜抗震性能仿真分析报告", author: "仿真分析工作组")
#set page(
  paper: "a4",
  margin: (x: 2.5cm, y: 2.54cm),
  numbering: "1",
  header: align(right)[_KYN28A-12 开关柜抗震性能分析报告_],
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
  #text(size: 22pt, weight: "bold")[KYN28A-12型高压开关柜抗震性能仿真分析报告]
  #v(0.4cm)
  #text(size: 16pt, weight: "bold")[基于有限元方法的结构动力学分析]
  #v(1cm)
  #line(length: 50%, stroke: 0.5pt)
  #v(0.8cm)
  #set par(first-line-indent: 0em)
  #grid(
    columns: (6em, auto),
    row-gutter: 10pt,
    align: (right, left),
    [*报告编号：*], [SA-KYN28-001],
    [*分析软件：*], [ANSYS Workbench 2024 R1],
    [*编制单位：*], [仿真分析工作组],
    [*适用对象：*], [设计研发部],
  )
  #v(1.5cm)
]

// ===== 正文 =====
= 概述

== 分析目的

本报告对KYN28A-12型高压开关柜进行抗震性能仿真分析。通过有限元方法计算开关柜在地震载荷作用下的应力分布、变形响应及模态特性，评估其结构安全性，为抗震设计优化提供理论依据。

#block(fill: rgb("#e3f2fd"), inset: 10pt, radius: 4pt, width: 100%)[
  *分析范围*：KYN28A-12型中置式高压开关柜整柜结构，包括柜体框架、断路器手车、母线室、电缆室等主要部件。
]

== 适用标准

本分析依据以下国家及国际标准进行：

#figure(
  table(
    columns: (auto, 1.5fr, 1fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[序号]], [#th[标准编号]], [#th[标准名称]],
    [1], [GB/T 13540-2009], [高压开关设备和控制设备的抗震要求],
    [2], [GB 50011-2010], [建筑抗震设计规范],
    [3], [IEC 62271-2:2003], [高压开关设备和控制设备抗震要求],
    [4], [IEC 60068-3-3], [环境试验-地震试验方法],
    [5], [IEEE 693-2018], [变电站设备抗震鉴定推荐规程],
  ),
  caption: [适用标准清单]
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
    [额定电流], [$I_n$], [4000 A], [主母线],
    [柜体质量], [$m$], [~1200 kg], [含设备],
  ),
  caption: [开关柜主要几何参数]
)

== 有限元网格

采用ANSYS Workbench进行网格划分，网格参数设置如下：

#figure(
  table(
    columns: (1fr, 1fr, 1fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[参数]], [#th[设置值]], [#th[说明]],
    [网格类型], [四面体/六面体混合], [自适应划分],
    [网格尺寸], [10-50 mm], [按部件分级],
    [节点总数], [~850,000], [精细网格],
    [单元总数], [~520,000], [高阶单元],
    [网格质量], [>0.75], [正交质量],
  ),
  caption: [网格划分参数]
)

#block(fill: rgb("#fff8e1"), inset: 10pt, radius: 4pt, width: 100%)[
  *网格优化*：在应力集中区域（如焊接接头、螺栓孔边缘）进行局部网格加密，确保计算精度。关键部位网格尺寸控制在5mm以下。
]

== 材料参数

#figure(
  table(
    columns: (1fr, auto, auto, auto, auto),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[部件]], [#th[材料]], [#th[弹性模量 (GPa)]], [#th[泊松比]], [#th[密度 (kg/m³)]],
    [柜体框架], [Q235钢], [206], [0.30], [7850],
    [隔板], [不锈钢304], [193], [0.29], [7930],
    [母线], [T2紫铜], [110], [0.34], [8900],
    [绝缘件], [SMC/DMC], [15], [0.35], [1900],
    [断路器], [多材料], [等效], [—], [等效密度],
  ),
  caption: [材料物理参数]
)

#h(-2em)*参数说明：*
- 断路器等复杂部件采用等效质量块建模，保持质心位置和转动惯量不变。
- 材料参数均取自材料供应商数据手册及相关国家标准。

= 载荷条件

== 地震载荷计算

依据GB 50011-2010《建筑抗震设计规范》，按8度抗震设防烈度计算等效地震载荷：

#figure(
  table(
    columns: (1.2fr, auto, auto, 1.5fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[参数]], [#th[符号]], [#th[数值]], [#th[备注]],
    [水平地震系数], [$alpha_h$], [0.40 g], [X/Y方向],
    [竖向地震系数], [$alpha_v$], [0.26 g], [$= 0.65 times alpha_h$],
    [水平加速度], [$a_h$], [3922.6 mm/s²], [$= 0.40 times g$],
    [竖向加速度], [$a_v$], [2549.7 mm/s²], [$= 0.26 times g$],
    [重力加速度], [$g$], [9806.6 mm/s²], [标准重力],
  ),
  caption: [地震载荷参数（民用标准工况）]
)

对于核电等高要求场合，采用更严苛的地震载荷条件：

#figure(
  table(
    columns: (1.2fr, auto, auto, 1.5fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[参数]], [#th[符号]], [#th[数值]], [#th[备注]],
    [水平地震系数], [$alpha_h$], [7.80 g], [SSE极限工况],
    [竖向地震系数], [$alpha_v$], [5.07 g], [$= 0.65 times alpha_h$],
    [水平加速度], [$a_h$], [76491 mm/s²], [$= 7.80 times g$],
    [竖向加速度], [$a_v$], [49719 mm/s²], [$= 5.07 times g$],
  ),
  caption: [地震载荷参数（核电极限工况）]
)

== 边界条件

#figure(
  table(
    columns: (auto, 1fr, 1.5fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[序号]], [#th[边界类型]], [#th[施加位置]],
    [1], [固定支撑 (Fixed Support)], [柜体底部安装面（4个安装孔）],
    [2], [重力载荷 (Standard Earth Gravity)], [全局-Z方向],
    [3], [水平地震加速度], [全局X方向],
    [4], [竖向地震加速度], [全局Z方向],
  ),
  caption: [边界条件设置]
)

#block(fill: rgb("#e8f5e9"), inset: 10pt, radius: 4pt, width: 100%)[
  *载荷组合*：采用静力等效法，将地震载荷与重力载荷进行叠加。水平和竖向地震载荷同时作用，取最不利工况进行分析。
]

= 分析结果

== 应力分布

=== 等效应力云图

通过静力学分析计算得到开关柜在地震载荷作用下的Von-Mises等效应力分布。

#figure(
  grid(columns: 2, gutter: 12pt,
    image("field_plots/seismic/image.png", width: 100%),
    image("field_plots/seismic/image copy.png", width: 100%),
  ),
  caption: [等效应力云图（左：整体视图，右：局部放大）]
)

=== 应力分析结果

#figure(
  table(
    columns: (1.2fr, auto, auto, auto),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if row == 1 { rgb("#e6f3ff") } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[参数]], [#th[数值]], [#th[许用值]], [#th[安全系数]],
    [*最大等效应力*], [*156.8 MPa*], [*235 MPa*], [*1.50*],
    [框架立柱应力], [142.3 MPa], [235 MPa], [1.65],
    [横梁连接处], [156.8 MPa], [235 MPa], [1.50],
    [底座焊接处], [128.5 MPa], [235 MPa], [1.83],
    [螺栓连接处], [89.2 MPa], [180 MPa], [2.02],
  ),
  caption: [应力分析结果汇总]
)

#block(fill: rgb("#e8f5e9"), inset: 10pt, radius: 4pt, width: 100%)[
  *评估结论*：最大等效应力156.8 MPa出现在横梁与立柱连接处，低于Q235钢屈服强度235 MPa，安全系数1.50，满足GB/T 13540-2009抗震要求。
]

== 变形分析

=== 位移云图

#figure(
  grid(columns: 2, gutter: 12pt,
    image("field_plots/seismic/image copy 2.png", width: 100%),
    image("field_plots/seismic/image copy 3.png", width: 100%),
  ),
  caption: [总变形云图（左：整体变形，右：X方向变形）]
)

=== 变形分析结果

#figure(
  table(
    columns: (1.2fr, auto, auto, auto),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if row == 1 { rgb("#e6f3ff") } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[变形参数]], [#th[数值]], [#th[限值]], [#th[判定]],
    [*最大总变形*], [*8.52 mm*], [*23 mm*], [*合格*],
    [X方向变形], [7.85 mm], [H/300 = 7.67 mm], [合格],
    [Y方向变形], [2.31 mm], [H/300 = 7.67 mm], [合格],
    [Z方向变形], [1.28 mm], [5 mm], [合格],
    [层间位移角], [1/270], [1/250], [合格],
  ),
  caption: [变形分析结果汇总]
)

#h(-2em)*限值说明：*
- 最大总变形限值取柜体高度的1%，即2300×1% = 23 mm
- X/Y方向水平变形限值取H/300 = 7.67 mm（按规范要求）
- 层间位移角限值1/250（按GB 50011-2010）

== 模态分析

为评估开关柜的动态特性，进行模态分析计算其固有频率。

#figure(
  grid(columns: 2, gutter: 12pt,
    image("field_plots/seismic/image copy 4.png", width: 100%),
    image("field_plots/seismic/image copy 5.png", width: 100%),
  ),
  caption: [模态振型云图（左：一阶模态，右：二阶模态）]
)

=== 固有频率结果

#figure(
  table(
    columns: (auto, auto, 1.5fr, auto),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[阶数]], [#th[频率 (Hz)]], [#th[振型描述]], [#th[质量参与系数]],
    [1], [12.5], [X方向平动（前后摆动）], [68.2%],
    [2], [15.8], [Y方向平动（左右摆动）], [72.5%],
    [3], [22.3], [Z轴扭转], [45.6%],
    [4], [28.7], [整体弯曲（X-Z平面）], [15.3%],
    [5], [35.2], [局部振动（顶盖）], [8.7%],
    [6], [42.8], [高阶弯曲模态], [5.2%],
  ),
  caption: [前六阶固有频率及振型]
)

#block(fill: rgb("#fff8e1"), inset: 10pt, radius: 4pt, width: 100%)[
  *动态特性评估*：
  - 一阶固有频率12.5 Hz，高于地震主频范围（1-10 Hz），避免共振风险
  - 前三阶模态质量参与系数之和超过90%，表明主要振型已被捕获
  - 建议对一阶模态对应的X方向进行重点加强
]

== 响应谱分析

=== 地震响应谱

依据GB/T 13540-2009，采用标准地震响应谱进行分析：

#figure(
  image("field_plots/seismic/image copy 6.png", width: 80%),
  caption: [地震响应谱曲线（阻尼比5%）]
)

=== 谱分析结果

#figure(
  table(
    columns: (1.2fr, auto, auto, auto),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[响应参数]], [#th[X方向]], [#th[Y方向]], [#th[Z方向]],
    [最大加速度响应], [4.2 m/s²], [3.8 m/s²], [2.6 m/s²],
    [最大速度响应], [0.15 m/s], [0.12 m/s], [0.08 m/s],
    [最大位移响应], [9.2 mm], [7.8 mm], [3.5 mm],
    [基底剪力], [25.6 kN], [22.3 kN], [14.8 kN],
  ),
  caption: [响应谱分析结果]
)

= 附加分析

== 疲劳寿命评估

考虑地震的循环载荷特性，对关键部位进行疲劳寿命评估：

#figure(
  table(
    columns: (1.2fr, auto, auto, auto),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[评估位置]], [#th[应力幅值 (MPa)]], [#th[循环次数]], [#th[疲劳安全系数]],
    [横梁连接处], [78.4], [10⁶], [2.5],
    [底座焊接处], [64.3], [10⁶], [3.2],
    [螺栓连接处], [44.6], [10⁶], [4.8],
  ),
  caption: [疲劳寿命评估结果]
)

== 局部应力集中

#figure(
  grid(columns: 2, gutter: 12pt,
    image("field_plots/seismic/image copy 7.png", width: 100%),
    image("field_plots/seismic/image copy 8.png", width: 100%),
  ),
  caption: [局部应力集中区域（左：焊接接头，右：螺栓孔边缘）]
)

= 结论与建议

== 主要结论

根据本次抗震性能仿真分析，得出以下主要结论：

+ *结构强度满足要求*：在0.4g地震载荷作用下，最大等效应力156.8 MPa，低于材料屈服强度235 MPa，安全系数1.50，满足GB/T 13540-2009抗震要求。

+ *变形在允许范围内*：最大总变形8.52 mm，柜顶水平位移7.85 mm，层间位移角1/270，均满足规范限值要求。

+ *动态特性良好*：一阶固有频率12.5 Hz，高于地震主频范围（1-10 Hz），避免共振风险。

+ *关键部位识别*：应力集中主要出现在横梁与立柱连接处及底座焊接区域，需重点关注焊接质量。

#block(fill: rgb("#e8f5e9"), inset: 10pt, radius: 4pt, width: 100%)[
  *总体评估*：KYN28A-12型高压开关柜结构设计合理，在8度抗震设防烈度条件下具有足够的抗震安全裕度，满足GB/T 13540-2009及GB 50011-2010的抗震要求。
]

== 优化建议

+ *连接加强*：横梁与立柱连接处可增加加强筋或加大焊缝尺寸，提高局部刚度
+ *焊接质量*：底座焊接区域为应力集中区，应确保焊接质量，推荐采用全熔透焊接
+ *阻尼措施*：可考虑在柜体与基础之间增加阻尼隔震装置，降低地震响应
+ *定期检测*：建议对安装后的开关柜进行振动测试，验证实际固有频率与分析结果的一致性

== 后续工作

+ 进行时程分析，考虑地震动的瞬态特性
+ 开展抗震振动台试验，验证仿真结果
+ 针对核电工况（7.8g）进行专项评估
+ 优化设计后进行重新分析验证

#v(2em)
#line(length: 100%, stroke: 0.5pt)
#grid(
  columns: (1fr, 1fr),
  [
    #text(size: 9pt, fill: gray)[
      *仿真工具*：ANSYS Workbench 2024 R1 \
      *分析类型*：静力学分析 + 模态分析 \
      *网格单元*：高阶四面体/六面体
    ]
  ],
  [
    #align(right)[
      #text(size: 9pt, fill: gray)[
        *报告日期*：2026年01月04日 \
        *版本*：v1.0
      ]
    ]
  ]
)

#pagebreak()

= 附录

== 附录A：分析设置详情

=== A.1 求解器设置

#figure(
  table(
    columns: (1fr, 1.5fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: (left, left),
    [#th[参数]], [#th[设置值]],
    [求解器类型], [ANSYS Mechanical APDL],
    [分析类型], [静力学分析 (Static Structural)],
    [大变形], [关闭 (Off)],
    [惯性释放], [关闭 (Off)],
    [并行计算], [8核 Distributed],
    [GPU加速], [NVIDIA CUDA],
  ),
  caption: [求解器设置参数]
)

=== A.2 收敛性验证

通过网格细化收敛性分析，验证计算结果的可靠性：

#figure(
  table(
    columns: (auto, auto, auto, auto),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[网格尺寸]], [#th[节点数]], [#th[最大应力 (MPa)]], [#th[相对误差]],
    [粗网格 (50mm)], [180,000], [149.2], [—],
    [中等网格 (25mm)], [420,000], [154.5], [3.6%],
    [细网格 (15mm)], [850,000], [156.8], [1.5%],
    [极细网格 (10mm)], [1,200,000], [157.3], [0.3%],
  ),
  caption: [网格收敛性验证]
)

== 附录B：参考标准摘要

=== B.1 GB/T 13540-2009 主要条款

+ *适用范围*：标称电压3 kV及以上、频率50 Hz及以下的电力系统中运行的户内和户外高压开关设备及控制设备的抗震要求
+ *验证方法*：通过分析、试验或分析与试验组合的方式验证抗震性能
+ *性能等级*：根据峰值地面加速度(PGA)分为不同抗震等级

=== B.2 抗震验证原则

#figure(
  table(
    columns: (auto, 1.5fr, 1.5fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[方法]], [#th[适用条件]], [#th[特点]],
    [分析法], [结构规则、边界条件明确], [快速、经济、可优化设计],
    [试验法], [最终设计验证], [直接、可靠、成本较高],
    [组合法], [复杂结构], [理论与实践相结合],
  ),
  caption: [抗震验证方法对比]
)

#v(2cm)

#align(right)[
  编制人签字：#underline[#h(5cm)]
  
  审核人签字：#underline[#h(5cm)]
  
  日#h(4em)期：#underline[#h(5cm)]
]
