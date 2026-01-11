#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KYN28_EddyCurrent_Conversion.py - 自动将静电场模型转换为涡流场发热模型

功能:
1. 继承原有的几何导入与分类逻辑 (母排 vs 柜体)
2. 自动识别母排的电流进出端面 (基于最长边)
3. 施加三相交流电流 (4000A, 50Hz, 120度相位差)
4. 开启 欧姆损耗 (Ohmic Loss) 计算
5. 设置 集肤效应 (Skin Depth) 网格

用法:
  python KYN28_EddyCurrent_Conversion.py
  python KYN28_EddyCurrent_Conversion.py --current 3150
"""

import os
import sys
import argparse
import math

# 设置 ANSYS 路径 (如果需要)
os.environ["ANSYSEM_ROOT242"] = r"G:\Ansys2024R2\v242\Win64"

# PyAEDT 配置
from pyaedt import settings
settings.use_grpc_api = False
settings.enable_error_handler = False

from pyaedt import Maxwell3d

# 配置
MODEL_FILE = r"F:\MULTI\drawings\SeismicAnalysis_In.igs"
PROJECT_NAME = "KYN28_Thermal_Source"
DESIGN_NAME = "EddyCurrent_Main"
AEDT_VERSION = "2024.2"
CURRENT_AMP = 4000  # 额定电流 4000A

def get_face_center(face):
    """计算面的中心点"""
    try:
        # PyAEDT 的 face 对象可能有 center 属性或者 vertices
        # 这里使用 vertices 计算平均值作为近似中心
        vertices = face.vertices
        if not vertices:
            return None
        x = sum(v.position[0] for v in vertices) / len(vertices)
        y = sum(v.position[1] for v in vertices) / len(vertices)
        z = sum(v.position[2] for v in vertices) / len(vertices)
        return [x, y, z]
    except:
        return None

def main(current=None, analyze=False):
    if current is None:
        current = CURRENT_AMP
        
    print(f"\n[KYN28 涡流场转换] ANSYS {AEDT_VERSION}")
    print(f"  目标: 计算发热损耗 (Ohmic Loss)")
    print(f"  电流: {current} A (三相)")
    
    if not os.path.exists(MODEL_FILE):
        print(f"✗ 模型不存在: {MODEL_FILE}")
        return False

    # [1] 创建 Maxwell 项目 (EddyCurrent)
    print("\n[1] 创建 EddyCurrent 项目...")
    try:
        m3d = Maxwell3d(
            projectname=PROJECT_NAME,
            designname=DESIGN_NAME,
            solution_type="EddyCurrent",  # <--- 关键修改：涡流场
            specified_version=AEDT_VERSION,
            new_desktop_session=True
        )
        print(f"  ✓ {m3d.project_name}/{m3d.design_name}")
    except Exception as e:
        print(f"  ✗ 失败: {e}")
        return False

    # [2] 导入几何
    print("\n[2] 导入模型...")
    try:
        m3d.modeler.import_3d_cad(MODEL_FILE, healing=True)
        m3d.modeler.refresh_all_ids()
        objs = [n for n in m3d.modeler.solid_names if "Region" not in n]
        print(f"  ✓ {len(objs)} 个对象")
    except Exception as e:
        print(f"  ✗ 导入失败: {e}")
        m3d.release_desktop(False, False)
        return False

    # [3] 分类 (沿用逻辑)
    print("\n[3] 智能分类部件...")
    busbars = []
    frames = []
    
    # 临时字典用于存储边界框，避免重复查询
    obj_bboxes = {} 
    
    for n in objs:
        try:
            bb = m3d.modeler[n].bounding_box
            if bb:
                dims = [abs(bb[i+3]-bb[i]) for i in range(3)]
                obj_bboxes[n] = (bb, dims)
                
                # 判定逻辑：长宽比 > 5 且 长度 > 100mm 认为是母排
                if max(dims)/min(dims) > 5 and max(dims) > 100:
                    busbars.append(n)
                else:
                    frames.append(n)
        except:
            pass
            
    # 如果没识别出母排(可能是模型问题)，取前3个
    if not busbars and len(objs) >= 3:
        busbars = objs[:3]
        frames = objs[3:]
        
    print(f"  母排 (发热源): {len(busbars)} 个")
    print(f"  柜体 (涡流损耗): {len(frames)} 个")

    # [4] 赋材料
    print("\n[4] 赋材料与属性...")
    # 母排 -> 铜
    if busbars:
        m3d.assign_material(busbars, "copper")
    # 柜体 -> 钢 (注意：涡流场中钢的磁导率和电导率至关重要)
    if frames:
        m3d.assign_material(frames, "steel_1008") # 默认 steel_1008 是导磁导电的
        
    # 开启涡流计算 (Set Eddy Effect)
    # 对于涡流场，必须显式开启 Eddy Effect 才能计算涡流损耗
    print("  开启涡流效应...")
    all_conductors = busbars + frames
    try:
        m3d.eddy_effects_on(all_conductors, enable_eddy_effects=True)
    except Exception as e:
        print(f"  ⚠ 开启涡流效应警告: {e}")

    # [5] 自动施加电流激励
    print("\n[5] 自动识别端面并施加电流...")
    
    # 将母排按 X 坐标排序，以区分 A(左)/B(中)/C(右) 相
    # 假设母排是并排排列的
    busbar_centers = []
    for b in busbars:
        if b in obj_bboxes:
            bb = obj_bboxes[b][0]
            cx = (bb[0] + bb[3]) / 2
            busbar_centers.append((cx, b))
    
    # 排序：X 从小到大 -> A, B, C
    busbar_centers.sort(key=lambda x: x[0])
    sorted_busbars = [x[1] for x in busbar_centers]
    
    phases = ["A", "B", "C"]
    phase_angles = [0, -120, 120]  # deg
    
    assigned_count = 0
    
    # 遍历每个母排，寻找长方向的两个端面
    for i, bus_name in enumerate(sorted_busbars):
        # 循环分配 A, B, C
        phase_idx = i % 3
        phase_name = phases[phase_idx]
        angle = str(phase_angles[phase_idx]) + "deg"
        
        # 获取尺寸信息
        bb, dims = obj_bboxes[bus_name]
        
        # 找出最长维度 (0=X, 1=Y, 2=Z)
        long_dim_idx = dims.index(max(dims))
        
        # 寻找该方向上的两个极值面
        # 策略：遍历该对象的所有 Face，计算 Face Center
        # 如果 Center 在该维度的 max 或 min 附近，则选中
        try:
            faces = m3d.modeler[bus_name].faces
            input_face = None
            output_face = None
            
            min_val = bb[long_dim_idx]
            max_val = bb[long_dim_idx + 3]
            tol = 5.0 # mm 容差
            
            for f in faces:
                c = f.center
                if c:
                    cmd_pos = c[long_dim_idx]
                    # 检查是否在两端
                    if abs(cmd_pos - min_val) < tol:
                        input_face = f.id
                    elif abs(cmd_pos - max_val) < tol:
                        output_face = f.id
            
            if input_face and output_face:
                # 施加电流
                # Current In
                m3d.assign_current(input_face, amplitude=f"{current}A", phase=angle, 
                                 name=f"Cur_{bus_name}_In", swap_direction=False)
                # Current Out (方向相反? 还是用 Current Sink? 
                # Maxwell 规则：Out 面的电流方向如果是流出，通常不需要 swap，或者需根据法线判断
                # 稳妥做法：两个面都设 Current，只要方向一致即可。
                # 简单做法：In 面设 Current, Out 面设 Current 但 Swap Direction)
                m3d.assign_current(output_face, amplitude=f"{current}A", phase=angle, 
                                 name=f"Cur_{bus_name}_Out", swap_direction=True)
                
                print(f"  {bus_name} (Ln={max(dims):.0f}mm) -> Phase {phase_name} @ {angle}")
                assigned_count += 1
            else:
                print(f"  ⚠ {bus_name} 未找到完整的两端面 (Axis {long_dim_idx})")
                
        except Exception as e:
            print(f"  ⚠ 处理 {bus_name} 出错: {e}")

    if assigned_count == 0:
        print("  ❌ 严重警告：未成功施加任何电流激励！请手动检查模型。")

    # [6] 创建 Region
    print("\n[6] 创建仿真区域 (Region)...")
    if "Region" not in m3d.modeler.solid_names:
        m3d.modeler.create_region(pad_percent=50) # 涡流场建议稍大一点，防止磁力线截断

    # [7] 网格设置 (Skin Efffect)
    print("\n[7] 设置集肤效应网格...")
    try:
        # 铜排表面网格加密
        # 对于 50Hz 铜，集肤深度 ~9.3mm。但这只是穿透深度。
        # 为了精确计算损耗，表面网格建议 < 1/2 集肤深度 或 简单设为 4-6mm
        if busbars:
            m3d.mesh.assign_length_mesh(busbars, maximum_length=8, name="Skin_Mesh_Busbars")
        
        # 柜体虽然集肤深度很小（钢），但也需要一定加密
        if frames:
            m3d.mesh.assign_length_mesh(frames, maximum_length=25, name="Frame_Mesh")
            
        print("  ✓ 已应用 Surface Approximation 策略 (通过 Length Mesh)")
    except Exception as e:
        print(f"  ⚠ 网格设置失败: {e}")

    # [8] 求解设置
    print("\n[8] 求解设置...")
    setup = m3d.create_setup("Setup1")
    setup.props["Frequency"] = "50Hz"
    setup.props["MaximumPasses"] = 6  # 涡流场通常不需要特别多 Pass
    setup.props["PercentError"] = 1.0
    
    # 启用 Power Loss 计算 (PyAEDT 默认会自动启用如果分配了 Conductivity)
    # 但我们明确一下
    print("  ✓ 频率: 50Hz")

    # [9] 保存
    m3d.save_project()
    print(f"\n✅ 转换完成！项目已保存至: {m3d.project_path}")
    print("后续步骤:")
    print("1. 在 Maxwell 中运行 Analyze All")
    print("2. 求解完成后，右键 Field Overlays -> Fields -> Other -> Ohmic Loss")
    print("3. 这个 Ohmic Loss 分布就是导入 Fluent 的热源")

    m3d.release_desktop(False, False)
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", "-c", type=float, default=4000, help="Phase Current (RMS)")
    parser.add_argument("--analyze", "-a", action="store_true")
    args = parser.parse_args()
    
    main(args.current, args.analyze)
