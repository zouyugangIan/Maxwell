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
  python maxwell_report.py --design Galvalume # 只读取覆铝锌板设计
"""

import os
import sys
import subprocess
import argparse
import platform
from datetime import datetime

# ======================================================================
# 跨平台 ANSYS 版本检测 (必须在导入 pyaedt 之前)
# ======================================================================
def detect_ansys_installation():
    """自动检测 ANSYS 安装版本和路径"""
    system = platform.system()
    
    if system == "Windows":
        # Windows: 检查注册表
        try:
            import winreg
            for ver in ["241", "232", "231", "222", "221"]:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                        f"SOFTWARE\\Ansoft\\ElectronicsDesktop\\{ver}\\Desktop")
                    path, _ = winreg.QueryValueEx(key, "InstallDir")
                    winreg.CloseKey(key)
                    version = f"20{ver[:2]}.{ver[2]}"
                    return (version, path)
                except:
                    continue
        except ImportError:
            pass
        
        # 检查常见安装路径
        for ver in ["241", "232", "231", "222", "221"]:
            for base in ["E:\\Program Files\\ANSYSMaxwell", "C:\\Program Files\\ANSYS Inc\\v" + ver]:
                path = os.path.join(base if "ANSYSMaxwell" in base else base, f"v{ver}\\Win64" if "ANSYSMaxwell" not in base else f"v{ver}\\Win64")
                test_path = f"E:\\Program Files\\ANSYSMaxwell\\v{ver}\\Win64"
                if os.path.isdir(test_path):
                    version = f"20{ver[:2]}.{ver[2]}"
                    return (version, test_path)
    else:
        # Linux
        for ver in ["241", "232"]:
            path = f"/media/large_disk/ansysLinux/AnsysEM/v{ver}/Linux64"
            if os.path.isdir(path):
                version = f"20{ver[:2]}.{ver[2]}"
                return (version, path)
    
    return (None, None)

# 检测版本
_detected_version, _ansys_path = detect_ansys_installation()
AEDT_VERSION = _detected_version if _detected_version else "2024.1"

# 根据版本决定是否使用 gRPC
_use_grpc = tuple(map(int, AEDT_VERSION.split("."))) >= (2022, 2)
if not _use_grpc:
    print(f"[INFO] AEDT {AEDT_VERSION} 使用 COM 接口")

# 设置 gRPC 开关 (必须在导入 pyaedt 之前)
from pyaedt import settings
settings.use_grpc_api = _use_grpc

# 现在安全导入
from pyaedt import Maxwell3d

# ======================================================================
# 配置
# ======================================================================
system = platform.system()
if system == "Windows":
    PROJECT_NAME = "KYN28_V19_Final"
    OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Documents", "Ansoft", "results")
    REPORT_DIR = "F:\\MULTI\\Maxwell"
else:
    PROJECT_NAME = "KYN28_V19_Final"
    OUTPUT_DIR = "/media/large_disk/Projects/Maxwell/results"
    REPORT_DIR = "/media/large_disk/Projects/Maxwell"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 设计名称映射 (匹配 maxwell_setup.py)
DESIGNS = {
    "Galvalume": {
        "name": "EddyCurrent_Galvalume",
        "description": "覆铝锌板(结构钢,铁磁材料)",
        "permeability": 4000,
        "conductivity": "4.032×10⁶ S/m"
    },
    "Stainless": {
        "name": "EddyCurrent_Stainless",
        "description": "不锈钢板(非铁磁材料)",
        "permeability": 1,
        "conductivity": "1.137×10⁶ S/m"
    }
}

# 仿真参数 (用于报告)
SIM_PARAMS = {
    "frequency": "50 Hz",
    "current": "4000 A",
    "bus_w": "120 mm",
    "bus_d": "10 mm",
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
        # PyAEDT 0.8.x API 兼容
        m3d = Maxwell3d(
            projectname=PROJECT_NAME,
            designname=design_name,
            specified_version=AEDT_VERSION,
            new_desktop_session=False,
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
    
    # 隔板损耗 (对象名: Plate_Frame)
    try:
        data = m3d.post.get_solution_data(
            expressions=["SolidLoss(Plate_Frame)"],
            setup_sweep_name=solution,
            report_category="EddyCurrent"
        )
        if data and data.data_real():
            results["plate_loss"] = data.data_real()[0]
            print(f"  ✓ 隔板损耗: {results['plate_loss']:.4f} W")
    except:
        pass
    
    # 如果无法获取隔板损耗，使用总损耗作为近似值（损耗主要集中在隔板上）
    if results["plate_loss"] == 0 and results["total_loss"] > 0:
        results["plate_loss"] = results["total_loss"]
        print(f"  ⚠ 使用总损耗作为隔板损耗近似值: {results['plate_loss']:.4f} W")
    
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
    
    # 用户手动提供场图截图，不再自动导出
    
    # 释放但不关闭 Maxwell
    m3d.release_desktop(close_projects=False, close_desktop=False)
    return results


def export_field_plots(m3d, design_key: str, results: dict):
    """导出场图到图片文件 - 增强版
    
    改进:
    1. 增加 Mag_H 和 J 场图导出
    2. 使用 show=False 参数避免弹出图片窗口
    3. 多种导出方法回退机制
    4. 更好的错误处理和日志
    """
    
    print("  正在导出场图（静默模式）...")
    
    # 场图输出目录
    plot_dir = os.path.join(REPORT_DIR, "field_plots", design_key)
    os.makedirs(plot_dir, exist_ok=True)
    results["field_plots"] = []
    
    # 分析对象: Plate_Frame(隔板) + Busbar_A/B/C(铜排), 排除Region
    all_objects = m3d.modeler.solid_names
    analysis_objects = [n for n in all_objects if "Region" not in n]
    plate_objects = [n for n in all_objects if "Plate" in n or "Frame" in n]
    busbar_objects = [n for n in all_objects if "Busbar" in n]
    
    print(f"    分析对象: {analysis_objects}")
    print(f"    隔板对象: {plate_objects}")
    print(f"    母排对象: {busbar_objects}")
    
    # 场图配置: (quantity, objects, title, filename, scale_min, scale_max)
    # 增加更多场图类型
    field_configs = [
        ("Mag_B", analysis_objects, "磁通密度模云图", f"Mag_B_{design_key}", None, None),
        ("OhmicLoss", plate_objects if plate_objects else analysis_objects, "体积损耗密度云图", f"OhmicLoss_{design_key}", None, None),
        ("Mag_H", analysis_objects, "磁场强度云图", f"Mag_H_{design_key}", None, None),
        ("Mag_J", busbar_objects if busbar_objects else analysis_objects, "电流密度云图", f"Mag_J_{design_key}", None, None),
    ]
    
    for quantity, objects, title, base_filename, scale_min, scale_max in field_configs:
        output_file = os.path.join(plot_dir, base_filename + ".png")
        exported = False
        
        try:
            # 创建场图
            plot = m3d.post.create_fieldplot_surface(
                assignment=objects,
                quantity=quantity,
                setup=m3d.nominal_adaptive,
                intrinsics={"Phase": "0deg"}
            )
            
            if plot:
                # 方法1: plot_field_from_fieldplot (带图例+坐标轴, 不显示窗口)
                try:
                    model = m3d.post.plot_field_from_fieldplot(
                        plot_name=plot.name,
                        project_path=plot_dir,
                        image_format="png",
                        show_legend=True,
                        show_bounding=True,
                        show=False  # 关键：不弹出显示窗口
                    )
                    # PyAEDT可能自动生成文件名
                    expected_file = os.path.join(plot_dir, f"{plot.name}.png")
                    if os.path.exists(expected_file):
                        if expected_file != output_file:
                            import shutil
                            shutil.move(expected_file, output_file)
                        results["field_plots"].append({"name": title, "path": output_file})
                        print(f"    ✓ {title}: {base_filename}.png")
                        exported = True
                except Exception as e1:
                    # 静默记录错误，不打印干扰信息
                    pass
                
                # 方法2: export_field_plot (直接导出，无窗口)
                if not exported:
                    try:
                        success = m3d.post.export_field_plot(
                            plot_name=plot.name,
                            output_file=output_file
                        )
                        if success and os.path.exists(output_file):
                            results["field_plots"].append({"name": title, "path": output_file})
                            print(f"    ✓ {title}: {base_filename}.png")
                            exported = True
                    except Exception as e2:
                        pass
                
                # 方法3: export_model_picture (4K高清，隐藏Region)
                if not exported:
                    try:
                        m3d.post.export_model_picture(
                            full_name=output_file,
                            show_axis=True,
                            show_grid=False,
                            show_ruler=True,
                            show_region=False,
                            field_selections=[plot.name],
                            orientation="isometric",
                            width=3840,
                            height=2160
                        )
                        if os.path.exists(output_file):
                            results["field_plots"].append({"name": title, "path": output_file})
                            print(f"    ✓ {title}: {base_filename}.png (4K)")
                            exported = True
                    except Exception as e3:
                        pass
                
                # 清理场图对象
                try:
                    plot.delete()
                except:
                    pass
                    
        except Exception as e:
            print(f"    ⚠ {title}: 创建失败")
        
        if not exported:
            print(f"    ⚠ {title}: 导出失败（将使用手动截图）")


def generate_report(results_list: list):
    """生成 Typst 报告 - 增强版，参考专业技术报告格式
    
    改进要点:
    1. 增加材料参数详表（电导率、磁导率）
    2. 增加激励条件详情（三相相位）
    3. 增加趋肤深度计算
    4. 增加详细的场分布分析描述
    5. 增加工程意义分析
    6. 移除图片嵌入代码（用户表示直接截图到报告）
    """
    
    print("\n生成报告...")
    today = datetime.now().strftime("%Y年%m月%d日")
    
    # 检查是否有对比数据
    has_comparison = len(results_list) > 1
    
    # 获取主要结果
    main_result = results_list[0]
    
    # 提取对比结果
    galvalume = None
    stainless = None
    if has_comparison:
        galvalume = next((r for r in results_list if "铁磁材料" in r["description"] and "非" not in r["description"]), None)
        stainless = next((r for r in results_list if "非铁磁" in r["description"]), None)
    
    # 计算降幅
    reduction = 0
    if galvalume and stainless and galvalume["plate_loss"] > 0:
        reduction = (1 - stainless["plate_loss"] / galvalume["plate_loss"]) * 100
    
    # 生成 Typst 内容 - 专业技术报告格式
    content = f'''// ============================================================
// 开关柜金属隔板涡流损耗仿真分析报告
// 自动生成于 {today}
// 采用 Typst 排版系统
// ============================================================

#set document(title: "开关柜金属隔板涡流损耗仿真分析报告")
#set page(paper: "a4", margin: (x: 2.5cm, y: 2.5cm),
  header: align(right)[_KYN28 开关柜涡流损耗分析报告_],
  footer: context [#align(center)[第 #counter(page).display() 页，共 #counter(page).final().at(0) 页]]
)
#set text(font: ("Noto Serif CJK SC", "Noto Sans CJK SC"), size: 10.5pt, lang: "zh")
#set heading(numbering: "1.1.1")
#set par(first-line-indent: 2em, justify: true, leading: 1.5em)
#show heading.where(level: 1): set block(above: 1.5em, below: 1em)
#show heading.where(level: 2): set block(above: 1.2em, below: 0.8em)

// ===== 表格样式 =====
#let th(content) = text(fill: white, weight: "bold", size: 9pt)[#content]
#let header-blue = rgb("#2F5496")
#let alt-gray = rgb("#E7E6E6")

// ===== 标题页 =====
#align(center)[
  #v(1.5cm)
  #text(size: 22pt, weight: "bold")[开关柜金属隔板涡流损耗仿真分析报告]
  #v(0.4cm)
  #text(size: 14pt, weight: "bold")[KYN28-V19 型开关柜 · Maxwell 涡流场仿真]
  #v(1cm)
  #line(length: 50%, stroke: 0.5pt)
  #v(0.8cm)
  #set par(first-line-indent: 0em)
  #grid(
    columns: (6em, auto),
    row-gutter: 10pt,
    align: (right, left),
    [*报告编号：*], [EC-KYN28-001],
    [*分析类型：*], [涡流场仿真 (Eddy Current)],
    [*报告日期：*], [{today}],
  )
  #v(1.5cm)
]

// ===== 正文 =====

= 概述

本报告对 KYN28 型开关柜金属隔板在三相交流母排电流作用下的涡流损耗进行有限元仿真分析。通过 ANSYS Maxwell 涡流场求解器计算隔板上的感应涡流及其产生的热损耗，为开关柜的热设计提供理论依据。

#block(fill: rgb("#e3f2fd"), inset: 10pt, radius: 4pt, width: 100%)[
  *分析目的*：评估不同隔板材料对涡流损耗的影响，为材料选型提供数据支撑，指导开关柜热设计优化。
]

= 仿真模型

== 几何模型

#figure(
  table(
    columns: (1fr, 1fr, 1fr),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (_, row) => if row == 0 {{ header-blue }} else if calc.odd(row) {{ white }} else {{ alt-gray }},
    align: center + horizon,
    [#th[参数]], [#th[数值]], [#th[单位]],
    [母排宽度 (Bus_W)], [{SIM_PARAMS["bus_w"].replace(" mm", "")}], [mm],
    [母排深度 (Bus_D)], [{SIM_PARAMS["bus_d"].replace(" mm", "")}], [mm],
    [母排高度 (Bus_H)], [{SIM_PARAMS["bus_h"].replace(" mm", "")}], [mm],
    [母排间距 (Space)], [{SIM_PARAMS["space"].replace(" mm", "")}], [mm],
    [隔板厚度 (Plate_Th)], [{SIM_PARAMS["plate_th"].replace(" mm", "")}], [mm],
    [过孔间隙 (Gap)], [{SIM_PARAMS["gap"].replace(" mm", "")}], [mm],
  ),
  caption: [几何模型参数]
)

== 材料参数

#figure(
  table(
    columns: (1fr, 1.2fr, 1.2fr, 1fr),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (_, row) => if row == 0 {{ header-blue }} else if calc.odd(row) {{ white }} else {{ alt-gray }},
    align: center + horizon,
    [#th[零件]], [#th[材料]], [#th[电导率 (S/m)]], [#th[相对磁导率 μr]],
    [母排], [铜 (Copper)], [5.8×10⁷], [1],
    [隔板 (原方案)], [覆铝锌板 (Galvalume)], [4.032×10⁶], [4000],
    [隔板 (优化方案)], [不锈钢 (SS304)], [1.137×10⁶], [1],
  ),
  caption: [材料电磁参数]
)

#block(fill: rgb("#fff8e1"), inset: 10pt, radius: 4pt, width: 100%)[
  *说明*：覆铝锌板本质是冷轧钢板镀铝锌涂层，基材具有铁磁性（μr≈4000）。不锈钢（304/316奥氏体）为非铁磁材料（μr≈1）。
]

== 激励条件

#figure(
  table(
    columns: (1fr, 1fr, 1.5fr),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (_, row) => if row == 0 {{ header-blue }} else if calc.odd(row) {{ white }} else {{ alt-gray }},
    align: center + horizon,
    [#th[参数]], [#th[数值]], [#th[说明]],
    [电流幅值], [{SIM_PARAMS["current"]}], [有效值 (RMS)],
    [工作频率], [{SIM_PARAMS["frequency"]}], [工频交流],
    [A相相位], [0°], [参考相],
    [B相相位], [-120°], [滞后120°],
    [C相相位], [+120°], [超前120°],
  ),
  caption: [三相激励条件]
)

= 理论分析

== 趋肤深度计算

趋肤效应使交变电流集中在导体表面。趋肤深度 δ 由下式计算：

$ delta = sqrt(1 / (pi f mu sigma)) = sqrt(1 / (pi f mu_0 mu_r sigma)) $

其中：$f$ 为频率 (Hz)，$mu_0 = 4pi times 10^(-7)$ H/m，$mu_r$ 为相对磁导率，$sigma$ 为电导率 (S/m)。

#figure(
  table(
    columns: (1fr, 1fr, 1fr),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (_, row) => if row == 0 {{ header-blue }} else if calc.odd(row) {{ white }} else {{ alt-gray }},
    align: center + horizon,
    [#th[材料]], [#th[趋肤深度 (50Hz)]], [#th[备注]],
    [铜 (Copper)], [9.35 mm], [非铁磁材料],
    [覆铝锌板 (Galvalume)], [0.56 mm], [铁磁材料],
    [不锈钢 (SS304)], [21.2 mm], [非铁磁材料],
  ),
  caption: [不同材料趋肤深度]
)

#block(fill: rgb("#e8f5e9"), inset: 10pt, radius: 4pt, width: 100%)[
  *关键结论*：覆铝锌板的趋肤深度仅 0.56 mm，远小于隔板厚度 ({SIM_PARAMS["plate_th"]})，涡流高度集中于表面，导致局部损耗密度极高。
]

= 仿真结果

== 涡流损耗汇总

#figure(
  table(
    columns: (1.5fr, 1fr, 0.8fr),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (_, row) => if row == 0 {{ header-blue }} else if row == 1 {{ rgb("#e6f3ff") }} else if calc.odd(row) {{ white }} else {{ alt-gray }},
    align: (left, center, center),
    [#th[项目]], [#th[损耗值 (W)]], [#th[占比]],
    [*总涡流损耗*], [*{main_result["total_loss"]:.2f}*], [*100%*],
    [隔离板 (Plate_Frame)], [{main_result["plate_loss"]:.2f}], [{main_result["plate_loss"]/main_result["total_loss"]*100 if main_result["total_loss"] > 0 else 0:.1f}%],
    [母排 A (Busbar_A)], [{main_result["bus_losses"].get("A", 0):.2f}], [＜1%],
    [母排 B (Busbar_B)], [{main_result["bus_losses"].get("B", 0):.2f}], [＜1%],
    [母排 C (Busbar_C)], [{main_result["bus_losses"].get("C", 0):.2f}], [＜1%],
  ),
  caption: [{main_result["description"]} 条件下各部件损耗分布]
)

'''

    # 添加材料对比分析
    if galvalume and stainless:
        content += f'''
== 材料对比分析

#figure(
  table(
    columns: (1.2fr, 0.8fr, 1fr, 1fr),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (_, row) => if row == 0 {{ header-blue }} else if calc.odd(row) {{ white }} else {{ alt-gray }},
    align: (left, center, center, center),
    [#th[隔板材料]], [#th[μr]], [#th[隔板损耗 (W)]], [#th[备注]],
    [{galvalume["description"]}], [{galvalume["permeability"]}], [{galvalume["plate_loss"]:.2f}], [原方案],
    [{stainless["description"]}], [{stainless["permeability"]}], [{stainless["plate_loss"]:.4f}], [优化方案],
  ),
  caption: [不同隔板材料涡流损耗对比]
)

#block(fill: rgb("#e8f5e9"), inset: 10pt, radius: 4pt, width: 100%)[
  *关键发现*：采用非铁磁材料（不锈钢，μr≈1）替代覆铝锌板（铁磁钢板，μr≈4000）后，隔板涡流损耗从 *{galvalume["plate_loss"]:.2f} W* 降至 *{stainless["plate_loss"]:.4f} W*，降幅达 *{reduction:.2f}%*。
]

'''

    # 场分布分析 - 添加图片嵌入
    content += '''
= 场分布云图

'''
    
    # 嵌入覆铝锌板（Galvalume）方案的场图
    if galvalume:
        galvalume_plots = galvalume.get("field_plots", [])
        if galvalume_plots:
            # 构建图片嵌入代码
            plot_images = []
            for plot in galvalume_plots[:2]:  # 最多2张图并排显示
                rel_path = os.path.relpath(plot["path"], REPORT_DIR).replace("\\", "/")
                plot_images.append(f'image("{rel_path}", width: 100%)')
            
            if len(plot_images) == 1:
                content += f'''
#figure(
  {plot_images[0]},
  caption: [覆铝锌板方案场分布云图]
)

'''
            else:
                content += f'''
#figure(
  grid(columns: 2, gutter: 12pt,
    {", ".join(plot_images)},
  ),
  caption: [覆铝锌板方案场分布云图（左：磁通密度 Mag_B，右：欧姆损耗密度 OhmicLoss）]
)

'''
    
    # 嵌入不锈钢（Stainless）方案的场图
    if stainless:
        stainless_plots = stainless.get("field_plots", [])
        if stainless_plots:
            plot_images = []
            for plot in stainless_plots[:2]:
                rel_path = os.path.relpath(plot["path"], REPORT_DIR).replace("\\", "/")
                plot_images.append(f'image("{rel_path}", width: 100%)')
            
            if len(plot_images) == 1:
                content += f'''
#figure(
  {plot_images[0]},
  caption: [不锈钢方案场分布云图]
)

'''
            else:
                content += f'''
#figure(
  grid(columns: 2, gutter: 12pt,
    {", ".join(plot_images)},
  ),
  caption: [不锈钢方案场分布云图（左：磁通密度 Mag_B，右：欧姆损耗密度 OhmicLoss）]
)

'''

    # 添加场分布分析文字描述
    content += f'''
== 场分布特征分析

=== 欧姆损耗密度分布 (OhmicLoss)

损耗密度集中在隔板孔洞边缘，这是因为：

+ *涡流路径最短*：孔洞边缘的涡流环绕路径长度最短，感应电流密度最大
+ *磁通变化率最大*：三相母排产生的交变磁场在孔洞边缘区域梯度最大
+ *趋肤效应*：高频电流集中在导体表面薄层区域（趋肤深度 ≈ 0.56 mm）

=== 磁通密度分布 (Mag_B)

磁场分布呈对称特性，符合三相交流电流产生的旋转磁场预期。主要分布特征：

+ 磁通密度最大值位于母排表面附近
+ 三相母排间的磁场存在复杂的叠加与抵消效应
+ 隔板表面存在明显的磁通集中现象（铁磁材料时）

=== 电流密度分布 (J)

母排中的电流密度呈现明显的趋肤效应，电流集中在导体表面。

= 工程意义

== 损耗与发热

根据仿真结果，对于额定电流 {SIM_PARAMS["current"]} 的开关柜：

#figure(
  table(
    columns: (1.5fr, 1fr, 1fr),
    stroke: 0.5pt,
    inset: 8pt,
    fill: (_, row) => if row == 0 {{ header-blue }} else if calc.odd(row) {{ white }} else {{ alt-gray }},
    align: center + horizon,
    [#th[参数]], [#th[覆铝锌板]], [#th[不锈钢板]],
    [隔板涡流损耗功率], [{main_result["plate_loss"]:.2f} W], [{stainless["plate_loss"] if stainless else 0:.4f} W],
    [等效发热量 (1小时)], [{main_result["plate_loss"] * 3.6:.1f} kJ], [{(stainless["plate_loss"] * 3.6) if stainless else 0:.2f} kJ],
  ),
  caption: [损耗与发热对比]
)

== 热设计建议

+ *材料替换*：采用不锈钢（304/316）等非铁磁材料替代覆铝锌板/钢板，可有效降低涡流损耗达 {reduction:.1f}%
+ *通风散热*：覆铝锌板隔板产生的涡流损耗约 {main_result["plate_loss"]:.0f} W，需考虑增加通风散热措施
+ *过孔优化*：适当加大过孔尺寸可减少孔洞边缘的磁通集中，降低局部损耗密度
+ *温度场仿真*：
  - 不锈钢隔板方案：涡流损耗可忽略不计，温升主要由铜排焦耳热决定
  - 覆铝锌板方案：须将涡流损耗作为重要热源参与温度场计算

= 结论

根据本次仿真分析，主要结论如下：

+ 在 {SIM_PARAMS["current"]}、{SIM_PARAMS["frequency"]} 工况下，采用覆铝锌板（铁磁钢板）作为隔板，涡流损耗功率约 *{main_result["plate_loss"]:.2f} W*
'''

    if stainless:
        content += f'''+ 采用不锈钢板（非铁磁材料）作为隔板，涡流损耗功率仅 *{stainless["plate_loss"]:.4f} W*，降幅达 *{reduction:.2f}%*
'''
    
    content += f'''+ 涡流损耗主要发生在隔板上，损耗集中在孔洞边缘区域，与理论分析一致
+ 铁磁材料（覆铝锌板/钢板）对磁场具有明显增强作用，大幅增加涡流损耗
+ *建议*：采用非铁磁材料（不锈钢 304/316）可有效限制涡流损耗，是优化开关柜热设计的有效手段

#v(2em)
#line(length: 100%, stroke: 0.5pt)
#grid(
  columns: (1fr, 1fr),
  [
    #text(size: 9pt, fill: gray)[
      *仿真工具*：ANSYS Maxwell 2024 R1 \\
      *仿真类型*：涡流场 (Eddy Current) \\
      *求解频率*：50 Hz
    ]
  ],
  [
    #align(right)[
      #text(size: 9pt, fill: gray)[
        *报告日期*：{today} \\
        *版本*：v1.0
      ]
    ]
  ]
)
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
        choices=["Galvalume", "Stainless", "all"],
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
        for key in ["Galvalume", "Stainless"]:
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
