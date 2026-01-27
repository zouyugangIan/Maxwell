// ============================================================
// 高压开关柜抗震性能仿真分析报告
// 基于 ANSYS Workbench 有限元分析
// ============================================================

#set document(title: "高压开关柜抗震性能仿真分析报告", author: "仿真分析工作组")
#set page(
  paper: "a4",
  margin: (x: 2.5cm, y: 2.54cm),
  numbering: "1",
  header: align(right)[高压开关柜抗震性能分析报告],
  footer: context [#align(center)[第 #counter(page).display() 页，共 #counter(page).final().at(0) 页]]
)
#set text(font: ("SimSun", "Microsoft YaHei"), size: 10.5pt, lang: "zh")
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
  #text(size: 22pt, weight: "bold")[高压开关柜抗震性能仿真分析报告]
  #v(0.4cm)
  #v(1cm)
  #line(length: 50%, stroke: 0.5pt)
  #v(0.8cm)
  #text(size: 16pt, weight: "bold")[抗震分析 (Seismic Analysis)]
  #v(1cm)
  #set par(first-line-indent: 0em)
  #v(1.5cm)
]

// ===== 正文 =====
= 概述

== 分析背景与目的

高压开关柜作为电力系统中的关键设备，其在地震作用下的结构安全性直接关系到电网的可靠运行。随着我国电力基础设施建设向高烈度地震区域延伸，以及核电、轨道交通等特殊行业对设备抗震性能要求的不断提高，开关柜的抗震设计与验证已成为产品研发的重要环节。

本次针对KYN28-12/1250A和KYN28-12/4000A高压开关柜的母线、触头盒、手车导轨三处关键部位，按核电项目开关柜安装工况进行抗震性能仿真分析。


== 适用标准与规范

本分析严格依据国家标准、行业标准及国际标准进行，确保分析方法和评判准则的权威性：

#figure(
  table(
    columns: (auto, 1.5fr, 1.5fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[序号]], [#th[标准编号]], [#th[标准名称]],
    [1], [GB/T 13540-2009], [高压开关设备和控制设备的抗震要求],
    [2], [GB 50011-2010], [建筑抗震设计规范],
    [3], [HAF J0053-1996], [核电厂设备抗震鉴定],
  ),
  caption: [适用标准清单]
)

== 抗震设防要求

根据设备使用场景的不同，本分析考虑两种抗震设防水准：

#figure(
  table(
    columns: (1fr, 1fr, 1.5fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[设防类别]], [#th[峰值加速度]], [#th[适用场景]],
    [民用标准工况], [0.40g (水平)], [常规变电站、工业配电],
    [核电极限工况], [7.80g (水平)], [核电站、重要军事设施],
  ),
  caption: [抗震设防水准]
)

= 有限元建模

== 材料属性

开关柜各部件采用的材料及其物理力学参数如下表所示。所有材料参数均取自材料供应商提供的质量证明书或相关国家标准。

#figure(
  table(
    columns: (1fr, auto, auto, auto, auto, auto),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[部件名称]], [#th[材料牌号]], [#th[弹性模量\ (GPa)]], [#th[泊松比]], [#th[密度\ (kg/m³)]], [#th[屈服强度\ (MPa)]],
    [主母线], [T2紫铜], [110], [0.34], [8900], [200],
    [绝缘支撑(触头盒)], [环氧树脂(玻纤增强)], [18], [0.30], [1900], [180],
    [手车导轨], [Q235B], [206], [0.30], [7850], [235],
  ),
  caption: [开关柜材料特性参数表]
)

#block(fill: rgb("#fff8e1"), inset: 10pt, radius: 4pt, width: 100%)[
  *材料说明*：
  - 铜母线材料屈服强度为200 MPa，抗拉强度为395 MPa
  - 触头盒采用玻纤增强环氧树脂材料，屈服强度为180 MPa
  - 手车导轨采用Q235B钢材，屈服强度为235 MPa
]

== 网格划分

结合仿真模型的外形特征，对母线及触头盒模型选择六面体网格划分方法，对手车导轨模型选择四面体网格划分方法，经优化调整后均得到了贴体程度良好的网格。母线及触头盒模型的网格尺寸为5mm，其中网格节点416846个，网格数量234315个。手车导轨模型的网格尺寸为5mm，其中网格节点75512个，网格数量39232个。网格质量均符合计算要求。

#figure(
  grid(columns: 2, gutter: 12pt,
    image("../field_plots/SeismicAnalysis/CopperSeismicMesh.png", width: 100%, height: 6.5cm, fit: "stretch"),
    image("../field_plots/SeismicAnalysis/HandcartSeismicMesh.png", width: 100%, height: 6.5cm, fit: "stretch"),
  ),
  caption: [网格剖分情况（左：母线及触头盒模型网格，右：手车导轨模型网格）]
)

== 求解器设置

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
    [惯性释放], [关闭],
    [并行计算], [8核 Distributed],
  ),
  caption: [求解器设置参数]
)

= 载荷与边界条件

== 地震载荷计算

=== 民用标准工况

依据GB 50011-2010《建筑抗震设计规范》，按8度抗震设防烈度（设计基本地震加速度0.20g）计算，考虑设备重要性系数1.5和场地放大系数1.33，得到等效静力地震载荷：

#figure(
  table(
    columns: (1.2fr, auto, auto, 1.5fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[载荷参数]], [#th[符号]], [#th[数值]], [#th[计算依据]],
    [水平地震系数], [$alpha_h$], [0.40 g], [0.20×1.5×1.33≈0.40],
    [竖向地震系数], [$alpha_v$], [0.26 g], [$= 0.65 times alpha_h$],
    [水平加速度], [$a_h$], [4 m/s²], [$= 0.40 times g$],
    [竖向加速度], [$a_v$], [3 m/s²], [$= 0.26 times g$],
    [重力加速度], [$g$], [10 m/s²], [标准重力加速度],
  ),
  caption: [地震载荷参数（民用标准工况）]
)

=== 核电极限工况

对于核电站等高安全要求场合，依据HAF J0053-1996《核电厂设备抗震鉴定》，采用安全停堆地震（SSE）载荷进行分析：

#figure(
  table(
    columns: (1.2fr, auto, auto, 1.5fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[载荷参数]], [#th[符号]], [#th[数值]], [#th[备注]],
    [水平地震系数], [$alpha_h$], [7.80 g], [SSE极限工况],
    [竖向地震系数], [$alpha_v$], [5.07 g], [$= 0.65 times alpha_h$],
    [水平加速度], [$a_h$], [80 m/s²], [$= 7.80 times g$],
    [竖向加速度], [$a_v$], [50 m/s²], [$= 5.07 times g$],
  ),
  caption: [地震载荷参数（核电极限工况）]
)

== 边界条件设置

开关柜通过底座上的4个安装孔与基础地面采用螺栓连接固定。在有限元模型中，边界条件设置如下：

#figure(
  grid(columns: 2, gutter: 12pt,
    image("../field_plots/SeismicAnalysis/CopperSeismicConstraint.png", width: 100%, height: 6.5cm, fit: "stretch"),
    image("../field_plots/SeismicAnalysis/HandcartSeismicConstraint.png", width: 100%, height: 6.5cm, fit: "stretch"),
  ),
  caption: [约束位置示意图（左：母线与触头盒；右：手车导轨）]
)

#figure(
  table(
    columns: (auto, 1fr, 1.5fr),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[序号]], [#th[边界类型]], [#th[施加位置及说明]],
    [1], [固定支撑], [手车导轨螺栓孔、穿墙套筒安装孔固定约束],
    [2], [重力载荷], [全局坐标系-Z方向，g=10 m/s²],
    [3], [水平地震加速度], [全局X方向（前后方向）],
    [4], [竖向地震加速度], [全局Z方向（垂直方向）],
  ),
  caption: [边界条件设置]
)

#pagebreak()
#block(fill: rgb("#e8f5e9"), inset: 10pt, radius: 4pt, width: 100%, breakable: false)[
  *载荷组合原则*：
  - 采用静力等效法，将地震惯性力作为静载荷施加
  - 重力载荷与地震载荷同时作用，进行线性叠加
  - 水平和竖向地震载荷同时施加，考虑最不利组合
  - 分析X方向（前后）和Y方向（左右）两种水平地震工况
]

= 求解参数设置

按核电项目开关柜安装工况综合考虑，地震时的加速值按7.8g计算。

== 母线及触头盒设置

A相母线（最左端）加触头盒重量：m=15.585Kg，重力G=mg=15.585×9.8=152.74N，受到加速力f=ma=15.585×7.8×9.8=1191.38N，故A相母线所受垂直方向力F=mg+ma=1344.128N，方向为垂直向下，水平方向的力为ma=1191.38N，方向水平向内。

B相母线（中间）加触头盒重量：m=17.919Kg，重力G=mg=17.919×9.8=175.61N，受到加速力f=ma=17.919×7.8×9.8=1369.73N，故B相母线所受垂直方向力F=mg+ma=1545.38N，方向为垂直向下，水平方向的力为ma=1369.73N，方向水平向内。

C相母线（最右端）加触头盒重量：m=19.46Kg，重力G=mg=19.46×9.8=190.71N，受到加速力f=ma=19.46×7.8×9.8=1487.52N，故C相母线所受垂直方向力F=mg+ma=1678.22N，方向为垂直向下，水平方向的力为ma=1487.52N，方向水平向内。

== 手车导轨设置

断路器小车重量m=220kg，重力G=mg=220×9.8=2156N。受到加速力f=ma=220×7.8×9.8=16816.8N，故导轨所受合力F=mg+ma=18972.8N。左右导轨两边对称，右导轨受力为合力一半即为18972.8/2=9486.4N。

断路器小车与导轨的接触方式为前后两条直线。每条直线加载荷为9486.4/2=4743.2N，加载荷的方式如图4所示，力A与力B之间直线距离为320mm，为手车的等效长度距离。

#figure(
  grid(columns: 2, gutter: 12pt,
    image("../field_plots/SeismicAnalysis/CopperSeismicLoad.png", width: 100%, height: 6.5cm, fit: "stretch"),
    image("../field_plots/SeismicAnalysis/HandcartSeismicLoad.png", width: 100%, height: 6.5cm, fit: "stretch"),
  ),
  caption: [载荷施加图示（左：母线及触头盒载荷，右：手车导轨载荷）]
)

= 分析结果与评价

== 等效应力应变分布图

=== 母线及触头盒模型

母线及触头盒模型的最大主应力为142.08MPa，主要集中在最长分支母线C相转角处，分布如图5所示；最大剪切应力为81.64MPa，集中在触头盒与螺栓接触及过渡区域，分布如图6所示。

#figure(
  grid(columns: 2, gutter: 12pt,
    image("../field_plots/SeismicAnalysis/CopperSeismic1.png", width: 100%, height: 6.5cm, fit: "stretch"),
    image("../field_plots/SeismicAnalysis/CopperSeismic2.png", width: 100%, height: 6.5cm, fit: "stretch"),
  ),
  caption: [母线及触头盒应力分布图（左：最大主应力，右：最大剪切应力）]
)

=== 手车导轨模型

手车导轨的最大主应力为175.73MPa，集中在力A的直线处，最大剪切应力为67.91MPa，集中在力A的直线处及其上方的拐角处。

#figure(
  grid(columns: 2, gutter: 12pt,
    image("../field_plots/SeismicAnalysis/HandcartSeismic1.png", width: 100%, height: 6.5cm, fit: "stretch"),
    image("../field_plots/SeismicAnalysis/HandcartSeismic2.png", width: 100%, height: 6.5cm, fit: "stretch"),
  ),
  caption: [手车导轨应力分布图（左：最大主应力，右：最大剪切应力）]
)

== 最大变形与安全系数

#figure(
  grid(columns: 2, gutter: 12pt,
    image("../field_plots/SeismicAnalysis/CopperSeismicMaxDeformation.png", width: 100%, height: 6.5cm, fit: "stretch"),
    image("../field_plots/SeismicAnalysis/HandcartSeismicMaxDeformation.png", width: 100%, height: 6.5cm, fit: "stretch"),
  ),
  caption: [最大变形结果图（左：母线与触头盒；右：手车导轨）]
)

#figure(
  grid(columns: 2, gutter: 12pt,
    image("../field_plots/SeismicAnalysis/CopperSeismicSafetyFactor.png", width: 100%, height: 6.5cm, fit: "stretch"),
    image("../field_plots/SeismicAnalysis/HandcartSeismicSafetyFactor.png", width: 100%, height: 6.5cm, fit: "stretch"),
  ),
  caption: [安全系数结果图（左：母线与触头盒；右：手车导轨）]
)

最大变形结果显示，手车导轨的变形主要集中在加载区域及其附近的结构过渡处，母线与触头盒的变形集中在转角与连接过渡区域，属于局部集中变形。安全系数结果显示，两类部件的最小安全系数均大于1，整体满足抗震强度与稳定性要求。

== 应力结果汇总

#figure(
  table(
    columns: (1.2fr, auto, auto, auto, auto),
    stroke: 0.5pt + rgb("#666666"),
    inset: 8pt,
    fill: (_, row) => if row == 0 { header-blue } else if calc.odd(row) { white } else { alt-gray },
    align: center + horizon,
    [#th[评估部位]], [#th[最大主/剪切应力 (MPa)]], [#th[许用应力 (MPa)]], [#th[安全系数]], [#th[判定]],
    [母线（C相转角处）], [142.08], [395], [2.78], [合格],
    [触头盒与螺栓固定处], [81.64], [180], [2.20], [合格],
    [手车导轨], [175.73], [235], [1.34], [合格],
  ),
  caption: [应力分析结果汇总]
)

#block(fill: rgb("#e8f5e9"), inset: 10pt, radius: 4pt, width: 100%)[
  *应力评价*：母线部分最大主应力为142.08MPa，应力集中于分支母线拐角处，安全系数为2.78；触头盒部分最大剪切应力为81.64MPa，安全系数为2.20；手车导轨最大主应力为175.73MPa，安全系数为1.34，满足核电项目开关柜的抗震强度要求。
]


= 结论

母线部分最大主应力为142.08MPa（T2紫铜材料许用应力为395MPa），安全系数为2.78；触头盒部分最大剪切应力为81.64MPa（玻纤增强环氧树脂材料许用应力为180MPa），安全系数为2.20；手车导轨最大主应力值为175.73MPa（Q235B钢材许用应力为235MPa），安全系数为1.34。以上三处关键部位应力值均小于其材料许用应力，满足核电项目开关柜的抗震强度要求。最大变形主要集中在导轨加载区域与母线转角处，安全系数均大于1，满足抗震强度要求。

通过针对移开式开关柜的母线、触头盒、手车导轨三处关键部位，按核电项目的要求开展地震工况仿真模拟，分析结果表明，以上所有部位均满足地震烈度8度（AG5）抗震水平的设计要求。

#place(bottom)[
  #line(length: 100%, stroke: 0.5pt)
  #v(0.6em)
  #grid(
    columns: (1fr, 1fr),
    [
      #text(size: 9pt, fill: gray)[
        *仿真工具*：ANSYSWorkbench2024R2 \
        *分析类型*：抗震分析 \
      ]
    ],
    [
      #align(right)[
        #text(size: 9pt, fill: gray)[
          *报告日期*：#underline[#h(2em)]年#underline[#h(1em)]月#underline[#h(1em)]日 \
        ]
      ]
    ]
  )
]
