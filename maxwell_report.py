#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
maxwell_report.py - 开关柜涡流损耗仿真报告生成脚本

功能:
  - 从 Maxwell 读取仿真结果
  - 导出场图图片
  - 生成材料对比分析
  - 输出 PDF 报告

用法:
  python maxwell_report.py                    # 读取所有可用设计
  python maxwell_report.py --design Steel     # 只读取钢板设计
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime
from pyaedt import Maxwell3d

# ======================================================================
# 配置
# ======================================================================
PROJECT_PATH = "/media/large_disk/Maxwell"
PROJECT_NAME = "KYN28_V19_Final"
OUTPUT_DIR = "/media/large_disk/Projects/Maxwell/results"
REPORT_DIR = "/media/large_disk/Projects/Maxwell"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 设计名称映射
DESIGNS = {
    "Steel": {
        "name": "EddyCurrent_Steel",
        "description": "钢板(铁磁材料)",
        "permeability": 4000,
        "conductivity": "4.032×10⁶ S/m"
    },
    "AlZn": {
        "name": "EddyCurrent_AlZn",
        "description": "铝锌板(非铁磁材料)",
        "permeability": 1,
        "conductivity": "3.77×10⁷ S/m"
    },
    # 兼容旧版设计名称
    "Py": {
        "name": "EddyCurrent_Py",
        "description": "钢板(铁磁材料)",
        "permeability": 4000,
        "conductivity": "4.032×10⁶ S/m"
    }
}

# 仿真参数 (用于报告)
SIM_PARAMS = {
    "frequency": "50 Hz",
    "current": "4000 A",
    "bus_w": "10 mm",
    "bus_d": "100 mm",
    "bus_h": "600 mm",
    "space": "160 mm",
    "plate_th": "3 mm",
    "gap": "20 mm",
}


def get_results(design_key: str) -> dict:
    """从 Maxwell 获取仿真结果"""
    
    config = DESIGNS[design_key]
    design_name = config["name"]
    
    print(f"\n读取设计: {design_name}")
    
    try:
        m3d = Maxwell3d(
            project=os.path.join(PROJECT_PATH, f"{PROJECT_NAME}.aedt"),
            design=design_name,
            version="2024.1",
            new_desktop=False,
            non_graphical=False
        )
    except Exception as e:
        print(f"  ✗ 无法连接设计: {e}")
        return None
    
    solution = "Setup1 : LastAdaptive"
    results = {
        "design": design_name,
        "description": config["description"],
        "permeability": config["permeability"],
        "conductivity": config["conductivity"],
        "total_loss": 0,
        "plate_loss": 0,
        "bus_losses": {}
    }
    
    # 总损耗
    try:
        data = m3d.post.get_solution_data(
            expressions=["SolidLoss"],
            setup_sweep_name=solution,
            report_category="EddyCurrent"
        )
        if data and data.data_real():
            results["total_loss"] = data.data_real()[0]
            print(f"  ✓ 总损耗: {results['total_loss']:.4f} W")
    except Exception as e:
        print(f"  ✗ 获取总损耗失败: {e}")
    
    # 隔板损耗
    try:
        data = m3d.post.get_solution_data(
            expressions=["SolidLoss(Isolation_Plate)"],
            setup_sweep_name=solution,
            report_category="EddyCurrent"
        )
        if data and data.data_real():
            results["plate_loss"] = data.data_real()[0]
            print(f"  ✓ 隔板损耗: {results['plate_loss']:.4f} W")
    except:
        pass
    
    # 母排损耗
    for phase in ["A", "B", "C"]:
        try:
            data = m3d.post.get_solution_data(
                expressions=[f"SolidLoss(Busbar_{phase})"],
                setup_sweep_name=solution,
                report_category="EddyCurrent"
            )
            if data and data.data_real():
                results["bus_losses"][phase] = data.data_real()[0]
        except:
            results["bus_losses"][phase] = 0
    
    # 导出场图
    print("  导出场图...")
    for plot_name in ["Plot_OhmicLoss", "Plot_J", "Plot_Mag_B"]:
        try:
            output_file = os.path.join(OUTPUT_DIR, f"{design_key}_{plot_name}.png")
            m3d.post.export_field_jpg(
                plot_name=plot_name,
                full_path=output_file,
                resolution=[1920, 1080]
            )
            print(f"    ✓ {plot_name}")
        except:
            print(f"    ✗ {plot_name}")
    
    m3d.release_desktop()
    return results


def generate_report(results_list: list):
    """生成 Typst 报告"""
    
    print("\n生成报告...")
    today = datetime.now().strftime("%Y年%m月%d日")
    
    # 检查是否有对比数据
    has_comparison = len(results_list) > 1
    
    # 获取主要结果
    main_result = results_list[0]
    
    # 生成 Typst 内容
    content = f'''// 开关柜金属隔板涡流损耗仿真分析报告
// 自动生成于 {today}

#set document(title: "开关柜金属隔板涡流损耗仿真分析报告")
#set page(paper: "a4", margin: (x: 2.5cm, y: 2.5cm),
  header: align(right)[_涡流损耗分析报告_],
  footer: context [#align(center)[#counter(page).display("1/1", both: true)]])
#set text(font: "Noto Serif CJK SC", size: 11pt, lang: "zh")
#set heading(numbering: "1.1")
#set par(first-line-indent: 2em, justify: true)

#align(center)[
  #text(size: 22pt, weight: "bold")[开关柜金属隔板涡流损耗仿真分析报告]
  #v(0.5em)
  #text(size: 12pt)[KYN28-V19 型开关柜 · Maxwell 涡流场仿真]
  #v(0.3em)
  #text(size: 10pt, fill: gray)[{today}]
]

#v(1.5em)

= 概述

本报告对 KYN28 型开关柜金属隔板在三相交流母排电流作用下的涡流损耗进行有限元仿真分析。

= 仿真模型

== 几何与激励参数

#figure(table(columns: (1fr, 1fr, 1fr, 1fr), stroke: 0.5pt, inset: 6pt,
  [*母排宽度*], [{SIM_PARAMS["bus_w"]}], [*母排深度*], [{SIM_PARAMS["bus_d"]}],
  [*母排高度*], [{SIM_PARAMS["bus_h"]}], [*母排间距*], [{SIM_PARAMS["space"]}],
  [*隔板厚度*], [{SIM_PARAMS["plate_th"]}], [*过孔间隙*], [{SIM_PARAMS["gap"]}],
  [*频率*], [{SIM_PARAMS["frequency"]}], [*电流*], [{SIM_PARAMS["current"]}],
), caption: [仿真参数])

= 仿真结果

== 涡流损耗

#figure(table(columns: (1fr, 1fr, auto), stroke: 0.5pt, inset: 8pt,
  align: (left, center, center),
  fill: (col, row) => if row == 1 {{ rgb("#e6f3ff") }} else {{ none }},
  [*项目*], [*损耗值 (W)*], [*占比*],
  [*总涡流损耗*], [*{main_result["total_loss"]:.2f}*], [*100%*],
  [隔离板], [{main_result["plate_loss"]:.2f}], [{main_result["plate_loss"]/main_result["total_loss"]*100 if main_result["total_loss"] > 0 else 0:.1f}%],
  [母排 A], [{main_result["bus_losses"].get("A", 0):.2f}], [-],
  [母排 B], [{main_result["bus_losses"].get("B", 0):.2f}], [-],
  [母排 C], [{main_result["bus_losses"].get("C", 0):.2f}], [-],
), caption: [{main_result["description"]}损耗分布])

'''

    # 添加材料对比分析
    if has_comparison:
        steel = next((r for r in results_list if "钢" in r["description"]), None)
        alzn = next((r for r in results_list if "铝" in r["description"]), None)
        
        if steel and alzn:
            reduction = (1 - alzn["plate_loss"] / steel["plate_loss"]) * 100 if steel["plate_loss"] > 0 else 0
            
            content += f'''
== 材料对比分析

#figure(table(columns: (1fr, 1fr, 1fr, auto), stroke: 0.5pt, inset: 8pt,
  align: (left, center, center, center),
  [*隔板材料*], [*相对磁导率 μr*], [*隔板损耗 (W)*], [*备注*],
  [{steel["description"]}], [{steel["permeability"]}], [{steel["plate_loss"]:.2f}], [原方案],
  [{alzn["description"]}], [{alzn["permeability"]}], [{alzn["plate_loss"]:.4f}], [优化方案],
), caption: [不同隔板材料涡流损耗对比])

#block(fill: rgb("#e8f5e9"), inset: 10pt, radius: 4pt, width: 100%)[
  *关键发现*：采用非铁磁材料（铝锌板）替代钢板后，隔板涡流损耗从 {steel["plate_loss"]:.2f}W 降至 {alzn["plate_loss"]:.4f}W，*降幅达 {reduction:.2f}%*。
]

= 分析与结论

根据仿真计算，当开关柜的额定电流为 {SIM_PARAMS["current"]} 时：

+ 采用钢板作为隔板材料，涡流损耗功率约 {steel["plate_loss"]:.2f}W
+ 采用铝锌板作为隔板材料，涡流损耗功率仅 {alzn["plate_loss"]:.4f}W
+ 铁磁材料对磁场具有明显的增强作用，会大幅增加涡流损耗

*工程建议*：
- 采用不锈钢等非铁磁材料可有效限制涡流损耗、降低能耗
- 在开展温度场仿真时，非铁磁隔板的涡流损耗可忽略不计
- 铁磁材料隔板的涡流损耗须作为重要热源参与计算

'''
    else:
        content += '''
= 结论

+ 涡流损耗主要发生在隔板上
+ 损耗集中在孔洞边缘，磁通变化率大的区域
+ 建议采用非铁磁材料降低涡流损耗

'''

    content += f'''
#v(2em)
#line(length: 100%, stroke: 0.5pt)
#text(size: 9pt, fill: gray)[
  *仿真工具*：ANSYS Maxwell 2024 R1 · *报告生成*：{today}
]
'''

    # 写入文件
    typst_file = os.path.join(REPORT_DIR, "EddyCurrent_Analysis_Report.typ")
    with open(typst_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✓ Typst: {typst_file}")
    
    # 编译 PDF
    pdf_file = os.path.join(REPORT_DIR, "EddyCurrent_Analysis_Report.pdf")
    try:
        result = subprocess.run(
            ["typst", "compile", typst_file, pdf_file],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            print(f"  ✓ PDF: {pdf_file}")
        else:
            print(f"  ✗ PDF 编译失败: {result.stderr}")
    except Exception as e:
        print(f"  ✗ PDF 错误: {e}")
    
    return pdf_file


def main():
    parser = argparse.ArgumentParser(description="Maxwell 涡流仿真报告生成")
    parser.add_argument(
        "--design", "-d",
        choices=["Steel", "AlZn", "Py", "all"],
        default="all",
        help="选择读取的设计"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("开关柜涡流损耗仿真 - 报告生成")
    print("=" * 70)
    
    results_list = []
    
    if args.design == "all":
        # 尝试读取所有可用设计
        for key in ["Steel", "AlZn", "Py"]:
            result = get_results(key)
            if result and result["total_loss"] > 0:
                results_list.append(result)
    else:
        result = get_results(args.design)
        if result:
            results_list.append(result)
    
    if not results_list:
        print("\n✗ 没有找到有效的仿真结果!")
        print("  请先运行: python maxwell_setup.py --analyze")
        sys.exit(1)
    
    # 生成报告
    pdf_file = generate_report(results_list)
    
    print("\n" + "=" * 70)
    print("✅ 报告生成完成!")
    print("=" * 70)
    print(f"\n📁 输出文件:")
    print(f"   - 场图: {OUTPUT_DIR}/*.png")
    print(f"   - 报告: {pdf_file}")


if __name__ == "__main__":
    main()
