#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ElectrostaticField_Setup.py - KYN28开关柜静电场仿真分析设置脚本

功能:
  - 自动检测 ANSYS 2024R2/2023R2 等版本
  - 导入开关柜三维模型 (.igs)
  - 分类母排与金属构架并赋予材料 (铜/钢)
  - 自动创建仿真区域 (Region)
  - 设置三相电压激励与接地边界
  - 配置自适应网格与求解设置
"""

import os
import sys
import argparse
import platform

# ======================================================================
# 跨平台 ANSYS 版本检测
# ======================================================================
def detect_ansys_installation():
    """自动检测 ANSYS 安装版本和路径"""
    system = platform.system()
    if system == "Windows":
        try:
            import winreg
            for ver in ["242", "241", "232", "231", "222", "221"]:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                        f"SOFTWARE\\Ansoft\\ElectronicsDesktop\\{ver}\\Desktop")
                    path, _ = winreg.QueryValueEx(key, "InstallDir")
                    winreg.CloseKey(key)
                    # 检查路径是否存在
                    if os.path.isdir(path):
                        version = f"20{ver[:2]}.{ver[2]}"
                        return (version, path)
                except:
                    continue
        except ImportError:
            pass
        
        # 常见安装路径检查
        for ver in ["242", "241", "222"]:
            for drive in ["G:", "F:", "E:", "D:", "C:"]:
                path = os.path.join(drive, f"Ansys{2000+int(ver[:2])}R{ver[2]}", f"v{ver}", "Win64")
                if os.path.isdir(path):
                    return (f"20{ver[:2]}.{ver[2]}", path)
    return (None, None)

_version, _path = detect_ansys_installation()
AEDT_VERSION = _version if _version else "2024.2"

if _path:
    v_code = AEDT_VERSION.replace(".", "")[:3]
    os.environ[f"ANSYSEM_ROOT{v_code}"] = _path
    print(f"[INFO] 使用 ANSYS Electronics Desktop {AEDT_VERSION}")
    print(f"[INFO] 路径: {_path}")
else:
    print(f"[WARN] 未检测到安装路径，将尝试默认检测")

# PyAEDT 设置
from pyaedt import settings
# 如果是较新版本则优先使用 gRPC
settings.use_grpc_api = tuple(map(int, AEDT_VERSION.split("."))) >= (2022, 2)
settings.enable_error_handler = False

from pyaedt import Maxwell3d

# ======================================================================
# 配置参数
# ======================================================================
MODEL_FILE = r"F:\MULTI\drawings\SeismicAnalysis_In.igs"
PROJECT_NAME = "KYN28_Electrostatic"
DESIGN_NAME = "ElectrostaticField"
# 12kV 系统的峰值电压 (12kV * sqrt(2))
PEAK_VOLTAGE = 16970 

def main(voltage=None, analyze=False, non_graphical=False):
    if voltage is None:
        voltage = PEAK_VOLTAGE
    
    print("\n" + "="*70)
    print(f"KYN28 开关柜静电场仿真设置")
    print(f"模型: {os.path.basename(MODEL_FILE)}")
    print(f"激励: ±{voltage/1000:.2f}kV")
    print("="*70)
    
    if not os.path.exists(MODEL_FILE):
        print(f"✗ 错误: 模型文件不存在: {MODEL_FILE}")
        return False

    # [1] 启动 Maxwell
    print("\n[1] 启动 Maxwell 设计环境...")
    try:
        m3d = Maxwell3d(
            projectname=PROJECT_NAME,
            designname=DESIGN_NAME,
            solution_type="Electrostatic",
            specified_version=AEDT_VERSION,
            new_desktop_session=True,
            non_graphical=non_graphical
        )
        print(f"  ✓ 已连接: {m3d.project_name}/{m3d.design_name}")
    except Exception as e:
        print(f"  ✗ 启动失败: {e}")
        return False

    # [2] 导入几何模型
    print("\n[2] 导入三维模型...")
    try:
        # 清除现有对象以便重复运行
        if m3d.modeler.object_names:
            m3d.modeler.delete(m3d.modeler.object_names)
            
        m3d.modeler.import_3d_cad(MODEL_FILE, healing=True)
        m3d.modeler.refresh_all_ids()
        
        objs = [n for n in m3d.modeler.solid_names if "Region" not in n]
        print(f"  ✓ 成功导入 {len(objs)} 个实体零件")
    except Exception as e:
        print(f"  ✗ 导入失败: {e}")
        m3d.release_desktop(False, False)
        return False

    # [3] 自动分类与材质分配
    print("\n[3] 物理属性配置...")
    busbars = []
    frames = []
    
    for name in objs:
        try:
            obj = m3d.modeler[name]
            bb = obj.bounding_box # [xmin, ymin, zmin, xmax, ymax, zmax]
            dx = abs(bb[3]-bb[0])
            dy = abs(bb[4]-bb[1])
            dz = abs(bb[5]-bb[2])
            dims = [dx, dy, dz]
            
            # 简单的母排识别逻辑: 细长且体积较小
            if max(dims)/min(dims) > 6 and max(dims) > 100:
                busbars.append(name)
                obj.material_name = "copper"
                obj.color = (200, 100, 0)
            else:
                frames.append(name)
                # 构架默认为普通钢材或铝锌板基材
                obj.material_name = "steel_1008" 
                obj.color = (128, 128, 128)
                obj.transparency = 0.5
        except:
            pass

    print(f"  ✓ 母排识别: {len(busbars)} 个 (铜)")
    print(f"  ✓ 构架识别: {len(frames)} 个 (钢)")

    # [4] 创建仿真区域
    print("\n[4] 创建仿真区域 (Region)...")
    try:
        m3d.modeler.create_region(pad_percent=30)
        print("  ✓ 已添加 30% 边界裕量")
    except:
        pass

    # [5] 设置激励 (三相电压)
    print("\n[5] 设置电压激励...")
    # 这里根据识别出的母排数量，尝试分配 A(+V), B(0), C(-V)
    # 也可以根据位置 Y 坐标排序
    busbars_sorted = sorted(busbars, key=lambda x: m3d.modeler[x].position[1])
    
    for i, name in enumerate(busbars_sorted):
        # 简化的分配: 依次为 正、零、负
        v_val = [voltage, 0, -voltage][i % 3]
        m3d.assign_voltage([name], v_val, name=f"Voltage_{name}")
        print(f"  {name:20}: {v_val/1000:+.1f} kV")

    # [6] 设置接地
    print("\n[6] 设置接地边界...")
    # 将体积较大的构架选为接地
    gnd_objs = [n for n in frames if m3d.modeler[n].volume > 1e6]
    if gnd_objs:
        m3d.assign_voltage(gnd_objs, 0, name="Base_GND")
        print(f"  ✓ 已将 {len(gnd_objs)} 个主要构架零件设为 0V 接地")

    # [7] 网格与求解设置
    print("\n[7] 求解器配置...")
    try:
        # 细化母排网格
        if busbars:
            m3d.mesh.assign_length_mesh(busbars, maximum_length=15, name="Mesh_Busbars")
            
        setup = m3d.create_setup("Setup1")
        setup.props["MaximumPasses"] = 10
        setup.props["PercentError"] = 1.0
        print("  ✓ Setup1: MaxPasses=10, Error=1%")
    except Exception as e:
        print(f"  ⚠ 求解器设置警告: {e}")

    # [8] 保存项目
    try:
        m3d.save_project()
        print(f"\n✓ 项目已保存: {m3d.project_path}")
    except:
        pass

    # [9] 自动分析
    if analyze:
        print("\n[8] 开始执行仿真计算...")
        try:
            m3d.analyze_nominal()
            print("  ✓ 仿真完成")
        except Exception as e:
            print(f"  ✗ 仿真运行异常: {e}")

    # 释放但不关闭图形界面
    m3d.release_desktop(close_projects=False, close_desktop=False)
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Maxwell 静电场仿真快速设置")
    parser.add_argument("--voltage", "-v", type=float, help="设置测试电压(V)")
    parser.add_argument("--analyze", "-a", action="store_true", help="自动开始分析")
    parser.add_argument("--non-graphical", "-ng", action="store_true", help="静默模式运行")
    
    args = parser.parse_args()
    
    try:
        if main(args.voltage, args.analyze, args.non_graphical):
            print("\n✅ 环境部署成功！")
        else:
            print("\n❌ 脚本运行中止")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n用户中断运行")
    except Exception as e:
        print(f"\n运行时错误: {e}")
        sys.exit(1)
