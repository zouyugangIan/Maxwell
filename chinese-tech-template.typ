// ============================================================
// 中文技术文档模板 - Chinese Technical Document Template
// 适用于：技术报告、数据需求书、仿真分析文档
// 版本：1.0
// ============================================================

// 导出模板函数
#let chinese-tech-doc(
  title: "文档标题",
  subtitle: none,
  author: "作者",
  organization: "单位",
  target: "适用对象",
  show-date: false,
  body
) = {
  // ===== 页面设置 =====
  set document(title: title, author: author)
  set page(
    paper: "a4",
    margin: (x: 2.5cm, y: 2.54cm),
    numbering: "1"
  )
  
  // ===== 字体设置 =====
  // 正文：宋体（Noto Serif CJK SC）
  // 备用：黑体（Noto Sans CJK SC）
  set text(
    font: ("Noto Serif CJK SC", "Noto Sans CJK SC"),
    size: 10.5pt,
    lang: "zh"
  )
  
  // ===== 标题设置 =====
  set heading(numbering: "1.1.1")
  
  // 一级标题间距
  show heading.where(level: 1): set block(above: 1.5em, below: 1em)
  // 二级标题间距
  show heading.where(level: 2): set block(above: 1.5em, below: 1em)
  // 三级标题间距（与正文间距稍大）
  show heading.where(level: 3): set block(above: 1.2em, below: 1.2em)
  
  // ===== 段落设置 =====
  // 首行缩进2字符，所有段落（包括标题后第一段）
  // 1.5倍行距
  set par(
    first-line-indent: (amount: 2em, all: true),
    justify: true,
    leading: 1.5em,
    spacing: 1.5em
  )
  
  // ===== 标题页 =====
  align(center)[
    #v(1.5cm)
    #text(size: 22pt, weight: "bold")[#title]
    #if subtitle != none {
      v(0.4cm)
      text(size: 16pt, weight: "bold")[#subtitle]
    }
    #v(1cm)
    #line(length: 50%, stroke: 0.5pt)
    #v(0.8cm)
    #set par(first-line-indent: 0em)
    #grid(
      columns: (6em, auto),
      row-gutter: 10pt,
      align: (right, left),
      [*编制单位：*], [#organization],
      [*适用对象：*], [#target],
    )
    #v(1.5cm)
  ]
  
  // ===== 正文内容 =====
  body
}

// ===== 表格样式函数 =====
// 专业蓝色表头 + 交替行背景
#let styled-table(..args) = {
  figure(
    table(
      fill: (_, row) => if row == 0 { rgb("#2F5496") } else if calc.odd(row) { white } else { rgb("#E7E6E6") },
      stroke: 0.5pt + rgb("#666666"),
      inset: 6pt,
      align: center + horizon,
      ..args
    )
  )
}

// 表头单元格样式
#let th(content) = text(fill: white, weight: "bold", size: 9pt)[#content]

// ===== 参数说明样式 =====
// 使用 #h(-2em) 取消首行缩进
#let param-note() = [#h(-2em)*参数说明：*]

// ===== 签名区域 =====
#let signature-block() = {
  v(2cm)
  align(right)[
    甲方代表签字：#underline[#h(5cm)]
    
    日#h(5em)期：#underline[#h(5cm)]
  ]
}
