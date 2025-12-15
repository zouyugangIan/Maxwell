// 使用模板示例
// 导入模板
#import "chinese-tech-template.typ": *

// 应用模板
#show: chinese-tech-doc.with(
  title: "您的文档标题",
  subtitle: "副标题（可选）",
  author: "作者姓名",
  organization: "仿真分析工作组",
  target: "甲方设计研发部",
)

// ===== 以下是正文内容 =====

= 总则

== 目的
这里是目的描述文字，首行会自动缩进2个字符。

== 适用范围
本文档涵盖了仿真所需的核心几何模型、材料物理属性、热工边界条件及动力学参数。

= 数据需求

== 几何参数

=== 需求内容
+ 第一项数据需求
+ 第二项数据需求
+ 第三项数据需求

=== 技术说明
这里写技术说明，首行自动缩进。

== 参数汇总表

// 使用表格样式函数
#styled-table(
  columns: (auto, auto, auto, auto),
  table.header(
    th[序号], th[参数名称], th[单位], th[典型值],
  ),
  [1], [参数A], [mm], [10],
  [2], [参数B], [kg], [2.5],
  [3], [参数C], [N/mm], [20],
)

// 参数说明（不缩进）
#param-note()
- *参数A*：参数A的详细说明。
- *参数B*：参数B的详细说明。
- *参数C*：参数C的详细说明。

= 数据确认与授权

为推进项目进度，若上述数据暂时缺失，甲方可选择以下方式处理：

#set par(first-line-indent: 0em)
#box(width: 1em)[☐] *方式A：*由甲方协调供应商补充测试或提供。

#box(width: 1em)[☐] *方式B：*授权我方依据IEC/GB标准及行业典型数据库选取经验值进行计算。

// 签名区域
#signature-block()
