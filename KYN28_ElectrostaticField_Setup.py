#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KYN28_ElectrostaticField_Setup.py - KYN28开关柜静电场分析

用法:
  python KYN28_ElectrostaticField_Setup.py
  python KYN28_ElectrostaticField_Setup.py --voltage 42000
"""

import os
import sys
import argparse

# 设置 ANSYS 2024R2 路径
os.environ["ANSYSEM_ROOT242"] = r"G:\Ansys2024R2\v242\Win64"

# PyAEDT 配置
from pyaedt import settings
settings.use_grpc_api = False
settings.enable_error_handler = False

from pyaedt import Maxwell3d

# 配置
MODEL_FILE = r"F:\MULTI\drawings\SeismicAnalysis_In.igs"
PROJECT_NAME = "KYN28_Electrostatic"
DESIGN_NAME = "ElectrostaticField"
AEDT_VERSION = "2024.2"
VOLTAGE = 16970  # 12kV × √2

def main(voltage=None, analyze=False, fillet_radius=0):
    if voltage is None:
        voltage = VOLTAGE
    
    print(f"\n[KYN28 静电场分析] ANSYS 2024R2")
    print(f"  模型: {os.path.basename(MODEL_FILE)}")
    print(f"  电压: ±{voltage/1000:.1f}kV")
    if fillet_radius > 0:
        print(f"  倒角: R={fillet_radius}mm (优化尖峰场强)")
    print("")
    
    if not os.path.exists(MODEL_FILE):
        print(f"✗ 模型不存在: {MODEL_FILE}")
        return False
    
    # 创建 Maxwell 项目 - 让 PyAEDT 处理一切
    print("[1] 创建Maxwell项目...")
    try:
        m3d = Maxwell3d(
            projectname=PROJECT_NAME,
            designname=DESIGN_NAME,
            solution_type="Electrostatic",
            specified_version=AEDT_VERSION,
            new_desktop_session=True
        )
        print(f"  ✓ {m3d.project_name}/{m3d.design_name}")
    except Exception as e:
        print(f"  ✗ 失败: {e}")
        print("\n许可证可能未正确配置。请检查 ANSYS License Manager。")
        return False
    
    # 导入模型
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
    
    # 分类对象
    print("\n[3] 分类...")
    busbars, frames = [], []
    for n in objs:
        try:
            bb = m3d.modeler[n].bounding_box
            if bb:
                dims = [abs(bb[i+3]-bb[i]) for i in range(3)]
                if max(dims)/min(dims) > 8 and max(dims) > 100:
                    busbars.append(n)
                elif dims[0]*dims[1]*dims[2] > 1e8:
                    frames.append(n)
        except:
            pass
    if not frames:
        frames = objs[:10]
    print(f"  母排: {len(busbars)} | 框架: {len(frames)}")
    
    # 赋材料
    print("\n[4] 赋材料...")
    for n in busbars:
        try: m3d.modeler[n].material_name = "copper"
        except: pass
    for n in frames + [o for o in objs if o not in busbars]:
        try: m3d.modeler[n].material_name = "steel_1008"
        except: pass
    print("  ✓ copper / steel_1008")
    
    # 几何倒角处理 (解决奇异性)
    if fillet_radius > 0:
        print(f"\n[4.5] 几何倒角 (R={fillet_radius}mm)...")
        count = 0
        for n in busbars:
            try:
                # 获取对象的所有边
                edges = m3d.modeler.get_object_edges(n)
                if edges:
                    m3d.modeler.fillet(edges, fillet_radius)
                    count += 1
            except Exception as e:
                print(f"  ⚠ {n} 倒角失败: {e}")
        print(f"  ✓ 已对 {count} 个母排进行倒角优化")
    
    # Region
    print("\n[5] 创建Region...")
    try:
        if "Region" not in m3d.modeler.solid_names:
            m3d.modeler.create_region(pad_percent=30)
        print("  ✓ Region")
    except Exception as e:
        print(f"  ⚠ {e}")
    
    # 边界条件
    print("\n[6] 边界条件...")
    for i, n in enumerate(busbars):
        v = [voltage, 0, -voltage][i % 3]
        try:
            m3d.assign_voltage([n], v, name=f"V{i}")
            print(f"  {n[:20]}: {v/1000:+.0f}kV")
        except: pass
    
    gnd = [n for n in frames if n not in busbars][:15]
    if gnd:
        try:
            m3d.assign_voltage(gnd, 0, name="GND")
            print(f"  接地: {len(gnd)} 个")
        except: pass
    
    # 网格
    print("\n[7] 网格设置...")
    try:
        m3d.mesh.assign_length_mesh(assignment=objs, maximum_length=30, name="Global")
        if busbars:
            m3d.mesh.assign_length_mesh(assignment=busbars, maximum_length=8, name="Busbar")
        print("  ✓ 全局30mm / 母排8mm")
    except: pass
    
    # 分析设置
    print("\n[8] 分析设置...")
    try:
        setup = m3d.create_setup("Setup1")
        setup.props["MaximumPasses"] = 10
        setup.props["PercentError"] = 1.0
        print("  ✓ MaxPasses=10, Error=1%")
    except: pass
    
    # 求解
    if analyze:
        print("\n[求解中...]")
        try:
            m3d.analyze()
            print("  ✓ 完成")
        except Exception as e:
            print(f"  ✗ {e}")
    
    # 保存
    try:
        m3d.save_project()
        print(f"\n✓ 项目已保存")
    except: pass
    
    m3d.release_desktop(False, False)
    print("\n后续: Maxwell → Analyze All → Field Overlays → Mag_E")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--voltage", "-v", type=float)
    parser.add_argument("--analyze", "-a", action="store_true")
    parser.add_argument("--fillet", "-f", type=float, default=0.0, help="Fillet radius in mm for busbars")
    args = parser.parse_args()
    
    if main(args.voltage, args.analyze, args.fillet):
        print("\n✅ 完成")
    else:
        print("\n❌ 失败")
        sys.exit(1)
