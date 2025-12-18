#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
maxwell_setup.py - 开关柜涡流损耗仿真设置脚本

基于可用的 eddy_current_sim.py 添加材料参数化支持

用法:
  python maxwell_setup.py                    # 默认: 钢板材料
  python maxwell_setup.py --material steel   # 钢板材料
  python maxwell_setup.py --material alzn    # 铝锌板材料  
  python maxwell_setup.py --all              # 两种材料都仿真
"""

import os
import sys
import time
import argparse
from pyaedt import Maxwell3d

# ======================================================================
# 配置参数
# ======================================================================
AEDT_VERSION = "2024.1" 
PROJECT_NAME = "KYN28_V19_Final"
SOLVER_TYPE = "EddyCurrent"

if "ANSYSEM_ROOT241" not in os.environ:
    os.environ["ANSYSEM_ROOT241"] = "/media/large_disk/ansysLinux/AnsysEM/v241/Linux64"
    os.environ["ANSYSEM_DIR"] = "/media/large_disk/ansysLinux/AnsysEM/v241/Linux64"

# ======================================================================
# 隔板材料定义 (与参考文献一致)
# ======================================================================
PLATE_MATERIALS = {
    "galvalume": {
        "name": "Structural_Steel",
        "description": "覆铝锌板(结构钢基材,铁磁材料)",
        "conductivity": 4032000,    # S/m (4.032e6)
        "permeability": 4000,       # 相对磁导率 (铁磁)
        "design_suffix": "Galvalume"
    },
    "stainless": {
        "name": "Stainless_Steel", 
        "description": "不锈钢板(非铁磁材料)",
        "conductivity": 1137000,    # S/m (1.137e6)
        "permeability": 1,          # 相对磁导率 (非磁性)
        "design_suffix": "Stainless"
    }
}

# 几何参数 (与参考文献一致)
# 铜排规格: 3-TMY (120×10), 截面积 3535.62mm²
# 参考图: 铜排垂直放置，L型框架水平放置在铜排中间
bus_w = 120.0        # 铜排宽度 (沿 X 方向)
bus_d = 10.0         # 铜排厚度 (沿 Y 方向)
bus_h = 600.0        # 铜排高度 (沿 Z 方向，垂直向上)
space_pitch = 160.0  # 铜排中心间距 (沿 Y 方向)

# L 型铁框参数 (水平放置，铜排从中间穿过)
# 框架由顶盖 + 四边立壁组成
frame_length = 300.0  # 框架长度 (沿 X 方向，覆盖铜排宽度)
frame_width = 540.0   # 框架宽度 (沿 Y 方向，容纳3根铜排)
frame_flange = 50.0   # 框架翼缘高度 (沿 Z 方向向下)
frame_th = 3.0        # 框架板厚
gap = 20.0            # 铜排与框架间隙


def create_simulation(material_key: str):
    """创建指定材料的涡流仿真"""
    
    mat = PLATE_MATERIALS[material_key]
    design_name = f"EddyCurrent_{mat['design_suffix']}"
    
    print("=" * 70)
    print(f"创建仿真: {design_name}")
    print(f"隔板材料: {mat['description']}")
    print(f"  电导率: {mat['conductivity']} S/m")
    print(f"  相对磁导率: {mat['permeability']}")
    print("=" * 70)
    
    # 连接 Maxwell
    m3d = Maxwell3d(project=PROJECT_NAME, version=AEDT_VERSION, new_desktop=False)
    
    # 清理或创建设计
    print("准备设计...")
    try:
        current_designs = m3d.design_list
        if design_name in current_designs:
            print(f"  清理现有设计: {design_name}")
            m3d.set_active_design(design_name)
            try:
                m3d.stop_simulations()
                time.sleep(1)
            except:
                pass
            m3d.modeler.delete()
            for s in m3d.setup_names:
                m3d.delete_setup(s)
        else:
            print(f"  创建新设计: {design_name}")
            m3d.insert_design(design_name)
            m3d.solution_type = SOLVER_TYPE
    except Exception as e:
        print(f"  设计准备错误: {e}")
        if design_name not in m3d.design_list:
            m3d.insert_design(design_name)
    
    m3d.modeler.model_units = "mm"
    
    # ======================================================================
    # 同步参数到 Maxwell
    # ======================================================================
    print("  [1/7] 定义参数...")
    params = {
        "Bus_W": f"{bus_w}mm",         # 铜排宽度 120mm (X)
        "Bus_D": f"{bus_d}mm",         # 铜排厚度 10mm (Y)
        "Bus_H": f"{bus_h}mm",         # 铜排高度 600mm (Z)
        "Space": f"{space_pitch}mm",   # 铜排间距 160mm (Y)
        "Frame_L": f"{frame_length}mm",   # 框架长度 (X)
        "Frame_W": f"{frame_width}mm",    # 框架宽度 (Y)
        "Frame_F": f"{frame_flange}mm",   # 框架翼缘高度 (Z)
        "Frame_Th": f"{frame_th}mm",      # 框架板厚
        "Gap": f"{gap}mm"
    }
    for k, v in params.items():
        m3d[k] = v
    
    # ======================================================================
    # 定义材料
    # ======================================================================
    print("  [2/7] 定义材料...")
    mat_name = mat["name"]
    if mat_name not in m3d.materials.material_keys:
        m = m3d.materials.add_material(mat_name)
    else:
        m = m3d.materials[mat_name]
    
    m.permeability = mat["permeability"]
    m.conductivity = mat["conductivity"]
    m.dielectric_permittivity = 1
    
    # ======================================================================
    # 几何建模 - 参考图结构
    # 铜排垂直 (沿 Z 向上)，L 型框架水平放置在铜排中间
    # ======================================================================
    print("  [3/7] 创建几何模型...")
    
    # --- 母排 (3-TMY 120×10mm，垂直放置) ---
    # 铜排沿 Z 方向 (高度)，宽度沿 X，厚度沿 Y
    # 原点设在模型中心
    bus_a = m3d.modeler.create_box(
        origin=["-Bus_W/2", "-Bus_D/2 - Space", "-Bus_H/2"],
        sizes=["Bus_W", "Bus_D", "Bus_H"],
        name="Busbar_A", material="copper"
    )
    bus_a.color = (255, 0, 0)
    
    bus_b = m3d.modeler.create_box(
        origin=["-Bus_W/2", "-Bus_D/2", "-Bus_H/2"],
        sizes=["Bus_W", "Bus_D", "Bus_H"],
        name="Busbar_B", material="copper"
    )
    bus_b.color = (0, 255, 0)
    
    bus_c = m3d.modeler.create_box(
        origin=["-Bus_W/2", "-Bus_D/2 + Space", "-Bus_H/2"],
        sizes=["Bus_W", "Bus_D", "Bus_H"],
        name="Busbar_C", material="copper"
    )
    bus_c.color = (255, 255, 0)
    
    # ======================================================================
    # L 型角钢框架 (两条平行角钢，铜排从中间穿过)
    # ======================================================================
    # 参考图结构：
    # - 两条 L 型角钢沿 Y 方向放置 (跨越三根铜排)
    # - 角钢 1 在 +X 侧，角钢 2 在 -X 侧
    # - 每条角钢截面：水平翼缘 (宽) + 垂直翼缘 (向下)
    
    # 角钢尺寸
    angle_width = 50.0   # 翼缘宽度 (L 的两边)
    angle_th = 3.0       # 角钢厚度
    angle_length = frame_width  # 角钢长度 (沿 Y 方向)
    
    # 角钢 1 (+X 侧)：水平翼缘向外 (+X)，垂直翼缘向下 (-Z)
    # 水平翼缘
    angle1_horiz = m3d.modeler.create_box(
        origin=[f"{bus_w/2 + gap}", f"-{angle_length}/2", "0"],
        sizes=[f"{angle_width}", f"{angle_length}", f"{angle_th}"],
        name="Angle1_Horiz"
    )
    # 垂直翼缘 (从水平翼缘内侧向下)
    angle1_vert = m3d.modeler.create_box(
        origin=[f"{bus_w/2 + gap}", f"-{angle_length}/2", f"-{angle_width}"],
        sizes=[f"{angle_th}", f"{angle_length}", f"{angle_width}"],
        name="Angle1_Vert"
    )
    m3d.modeler.unite([angle1_horiz.name, angle1_vert.name])
    
    # 角钢 2 (-X 侧)：水平翼缘向外 (-X)，垂直翼缘向下 (-Z)
    # 水平翼缘
    angle2_horiz = m3d.modeler.create_box(
        origin=[f"-{bus_w/2 + gap + angle_width}", f"-{angle_length}/2", "0"],
        sizes=[f"{angle_width}", f"{angle_length}", f"{angle_th}"],
        name="Angle2_Horiz"
    )
    # 垂直翼缘 (从水平翼缘内侧向下)
    angle2_vert = m3d.modeler.create_box(
        origin=[f"-{bus_w/2 + gap + angle_th}", f"-{angle_length}/2", f"-{angle_width}"],
        sizes=[f"{angle_th}", f"{angle_length}", f"{angle_width}"],
        name="Angle2_Vert"
    )
    m3d.modeler.unite([angle2_horiz.name, angle2_vert.name])
    
    # 合并两条角钢为一个整体
    m3d.modeler.unite([angle1_horiz.name, angle2_horiz.name])
    
    frame = m3d.modeler[angle1_horiz.name]
    frame.name = "L_Frame"
    frame.material_name = mat_name
    frame.color = (143, 175, 143)
    frame.transparency = 0.4
    
    # ======================================================================
    # 仿真区域 (Z 方向 padding=0，母排端面在边界上)
    # ======================================================================
    print("  [4/7] 创建仿真区域...")
    m3d.modeler.create_air_region(
        x_pos=50, x_neg=50,
        y_pos=50, y_neg=50,
        z_pos=0, z_neg=0,  # Z 方向无 padding，母排端面在边界
        is_percentage=True
    )
    
    # ======================================================================
    # 电流激励 (使用母排 Z 方向端面)
    # ======================================================================
    print("  [5/7] 分配电流激励...")
    
    phases = ["A", "B", "C"]
    phase_angles = {"A": "0deg", "B": "-120deg", "C": "120deg"}
    y_centers = {"A": -space_pitch, "B": 0.0, "C": space_pitch}
    bus_objs = {"A": bus_a, "B": bus_b, "C": bus_c}
    
    # 铜排垂直放置，端面在 Z 方向
    z_bottom = -bus_h / 2.0  # 底端
    z_top = bus_h / 2.0      # 顶端
    x_center = 0.0
    
    for phase in phases:
        bus_obj = bus_objs[phase]
        angle = phase_angles[phase]
        y_c = y_centers[phase]
        
        pos_bottom = [x_center, y_c, z_bottom]
        pos_top = [x_center, y_c, z_top]
        face_bottom_id = m3d.modeler.get_faceid_from_position(pos_bottom, obj_name=bus_obj.name)
        face_top_id = m3d.modeler.get_faceid_from_position(pos_top, obj_name=bus_obj.name)
        
        if face_bottom_id and face_top_id:
            m3d.assign_current(face_bottom_id, amplitude="4000A", phase=angle, name=f"Cur_{phase}_In", solid=False)
            m3d.assign_current(face_top_id, amplitude="4000A", phase=angle, name=f"Cur_{phase}_Out", solid=False, swap_direction=True)
            print(f"    {phase}相: 4000A @ {angle}")
        else:
            print(f"    ERROR: 无法找到 {phase} 相端面")
    
    # ======================================================================
    # 涡流效应和网格
    # ======================================================================
    print("  [6/7] 配置涡流效应和网格...")
    
    m3d.eddy_effects_on(
        [frame.name, bus_a.name, bus_b.name, bus_c.name],
        enable_eddy_effects=True,
        enable_displacement_current=False
    )
    
    m3d.mesh.assign_length_mesh([bus_a.name, bus_b.name, bus_c.name], maximum_length="100mm", name="Mesh_Busbars")
    m3d.mesh.assign_length_mesh([frame.name], maximum_length="30mm", name="Mesh_Frame")
    
    # ======================================================================
    # 求解设置和场图
    # ======================================================================
    print("  [7/7] 配置求解器和场图...")
    
    setup = m3d.create_setup(name="Setup1")
    setup.props["Frequency"] = "50Hz"
    setup.props["PercentError"] = 2
    setup.props["MaximumPasses"] = 6
    setup.props["PercentRefinement"] = 30
    setup.props["BasisOrder"] = 1
    
    # 场图
    m3d.post.create_fieldplot_surface([frame.name], "Ohmic_Loss", plot_name="Plot_OhmicLoss")
    m3d.post.create_fieldplot_surface([bus_a.name, bus_b.name, bus_c.name], "J", plot_name="Plot_J")
    m3d.post.create_fieldplot_surface([frame.name, bus_a.name, bus_b.name, bus_c.name], "Mag_B", plot_name="Plot_Mag_B")
    
    # 验证
    is_valid = m3d.validate_simple()
    if is_valid:
        print("  ✓ 验证通过")
    else:
        print("  ✗ 验证警告，请检查消息")
    
    # 保存
    m3d.save_project()
    
    # 释放但不关闭
    m3d.release_desktop(close_projects=False, close_desktop=False)
    
    print(f"\n✅ 设计 '{design_name}' 创建完成!")
    return design_name


def main():
    parser = argparse.ArgumentParser(description="Maxwell 涡流仿真设置")
    parser.add_argument("--material", "-m", choices=["galvalume", "stainless"], default="galvalume", help="隔板材料: galvalume(覆铝锌板) 或 stainless(不锈钢板)")
    parser.add_argument("--all", "-a", action="store_true", help="仿真所有材料")
    
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("开关柜金属隔板涡流损耗仿真")
    print("=" * 70)
    
    if args.all:
        print("模式: 材料对比 (钢板 + 铝锌板)")
        designs = []
        for mat_key in PLATE_MATERIALS:
            design = create_simulation(mat_key)
            designs.append(design)
            time.sleep(2)
        print(f"\n创建的设计: {designs}")
    else:
        print(f"材料: {PLATE_MATERIALS[args.material]['description']}")
        create_simulation(args.material)
    
    print("\n" + "=" * 70)
    print("完成! 下一步:")
    print("  1. 在 Maxwell 中点击 'Analyze All' 运行仿真")
    print("  2. 仿真完成后运行 maxwell_report.py 生成报告")
    print("=" * 70)


if __name__ == "__main__":
    main()
