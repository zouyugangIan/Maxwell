#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MeshTest_Setup.py - 复杂几何模型网格测试脚本

目的：
  - 快速验证导入的几何模型是否能成功划分网格
  - 统一赋 Copper 材料到所有零件
  - 使用简单激励条件进行测试
  - 验证网格后可决定是否继续详细仿真

用法：
  python MeshTest_Setup.py                    # 使用已打开的 Maxwell 项目
  python MeshTest_Setup.py --project MyProj   # 指定项目名称
"""

import os
import sys
import argparse
import platform

# ======================================================================
# 跨平台 ANSYS 版本检测 (必须在导入 pyaedt 之前)
# ======================================================================
def detect_ansys_installation():
    """自动检测 ANSYS 安装版本和路径"""
    system = platform.system()
    
    if system == "Windows":
        # Windows: 检查常见安装路径
        for ver in ["241", "232", "231", "222", "221"]:
            for base in [f"E:\\Program Files\\ANSYSMaxwell\\v{ver}\\Win64",
                         f"C:\\Program Files\\AnsysEM\\v{ver}\\Win64",
                         f"C:\\Program Files\\ANSYS Inc\\v{ver}\\Win64"]:
                if os.path.isdir(base):
                    version = f"20{ver[:2]}.{ver[2]}"
                    return (version, base)
        
        # 尝试注册表
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

print(f"[INFO] 检测到 ANSYS Electronics Desktop {AEDT_VERSION}")

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
# 网格测试核心函数
# ======================================================================

def run_mesh_test(project_name=None, design_name=None):
    """
    执行网格测试
    
    步骤:
    1. 连接到已打开的 Maxwell 项目
    2. 获取所有实体对象
    3. 统一赋 Copper 材料
    4. 创建 Region
    5. 设置简单激励 (Voltage 激励)
    6. 创建网格操作
    7. 运行 Validation Check
    8. 尝试生成初始网格
    """
    
    print("\n" + "=" * 70)
    print("Maxwell 网格测试脚本")
    print("=" * 70)
    
    # -------------------------
    # Step 1: 连接 Maxwell
    # -------------------------
    print("\n[Step 1] 连接 Maxwell...")
    
    try:
        if project_name:
            m3d = Maxwell3d(
                projectname=project_name,
                designname=design_name,
                solution_type="Electrostatic",
                specified_version=AEDT_VERSION,
                new_desktop_session=False,
                non_graphical=False
            )
        else:
            # 连接到当前活动的 Maxwell 项目
            m3d = Maxwell3d(
                solution_type="Electrostatic",
                specified_version=AEDT_VERSION,
                new_desktop_session=False,
                non_graphical=False
            )
        print(f"  ✓ 已连接: {m3d.project_name} / {m3d.design_name}")
    except Exception as e:
        print(f"  ✗ 连接失败: {e}")
        print("\n请确保已打开 Maxwell 并导入了几何模型!")
        return False
    
    # -------------------------
    # Step 2: 获取所有实体对象
    # -------------------------
    print("\n[Step 2] 获取几何对象...")
    
    all_objects = m3d.modeler.solid_names
    print(f"  发现 {len(all_objects)} 个实体对象")
    
    if len(all_objects) == 0:
        print("  ✗ 没有找到任何实体对象!")
        print("  请先导入几何模型 (Modeler → Import...)")
        m3d.release_desktop(close_projects=False, close_desktop=False)
        return False
    
    # 显示前 10 个对象名
    for i, name in enumerate(all_objects[:10]):
        print(f"    {i+1}. {name}")
    if len(all_objects) > 10:
        print(f"    ... 还有 {len(all_objects) - 10} 个对象")
    
    # -------------------------
    # Step 3: 统一赋 Copper 材料
    # -------------------------
    print("\n[Step 3] 赋材料 (统一使用 Copper)...")
    
    success_count = 0
    for obj_name in all_objects:
        try:
            m3d.modeler[obj_name].material_name = "copper"
            success_count += 1
        except Exception as e:
            print(f"  ⚠ {obj_name}: 赋材料失败 - {e}")
    
    print(f"  ✓ 成功赋材料: {success_count}/{len(all_objects)} 个对象")
    
    # -------------------------
    # Step 4: 创建 Region
    # -------------------------
    print("\n[Step 4] 创建求解域 (Region)...")
    
    try:
        # 检查是否已有 Region
        if "Region" in all_objects:
            print("  Region 已存在，跳过创建")
        else:
            region = m3d.modeler.create_region(pad_percent=100)
            if region:
                print(f"  ✓ Region 创建成功: {region.name}")
            else:
                print("  ⚠ Region 创建返回 None，尝试继续...")
    except Exception as e:
        print(f"  ⚠ Region 创建异常: {e}")
        print("  尝试继续执行...")
    
    # -------------------------
    # Step 5: 设置简单激励 (电压激励)
    # -------------------------
    print("\n[Step 5] 设置激励条件...")
    
    try:
        # 选择第一个对象作为高电位
        first_obj = all_objects[0]
        
        # 尝试获取第一个对象的面
        try:
            faces = m3d.modeler[first_obj].faces
            if faces and len(faces) > 0:
                face_id = faces[0].id
                # 设置电压激励
                m3d.assign_voltage(
                    assignment=[face_id],
                    amplitude=1000,  # 1000V
                    name="Voltage_Test"
                )
                print(f"  ✓ 电压激励设置成功 (1000V on {first_obj})")
        except Exception as e:
            print(f"  ⚠ 激励设置失败: {e}")
            print("  测试将继续，但需要手动设置激励")
    except Exception as e:
        print(f"  ⚠ 激励设置跳过: {e}")
    
    # -------------------------
    # Step 6: 网格设置
    # -------------------------
    print("\n[Step 6] 设置网格操作...")
    
    try:
        # 对所有对象设置基于长度的网格
        mesh_length = 20  # 20mm，较粗网格用于测试
        
        m3d.mesh.assign_length_mesh(
            names=all_objects,
            maxlength=mesh_length,
            maxelements=None,
            meshop_name="LengthMesh_Test"
        )
        print(f"  ✓ 网格操作设置成功 (最大边长 {mesh_length}mm)")
    except Exception as e:
        print(f"  ⚠ 网格设置失败: {e}")
        print("  将使用默认网格设置")
    
    # -------------------------
    # Step 7: 创建分析设置
    # -------------------------
    print("\n[Step 7] 创建分析设置...")
    
    try:
        setup = m3d.create_setup(name="MeshTest_Setup")
        setup.props["MaximumPasses"] = 3  # 仅 3 次迭代，快速测试
        setup.props["PercentError"] = 5   # 5% 误差容限
        print("  ✓ 分析设置创建成功 (MaxPasses=3, Error=5%)")
    except Exception as e:
        print(f"  ⚠ 分析设置失败: {e}")
    
    # -------------------------
    # Step 8: Validation Check
    # -------------------------
    print("\n[Step 8] 运行验证检查...")
    
    try:
        validation = m3d.validate_full_design()
        if validation:
            print("  ✓ 验证通过！几何模型可以进行网格划分")
        else:
            print("  ✗ 验证失败！请检查几何模型")
            print("  常见问题:")
            print("    - 实体之间存在重叠")
            print("    - 存在微小间隙或尖角")
            print("    - 缺少 Region 或激励设置")
    except Exception as e:
        print(f"  ⚠ 验证异常: {e}")
    
    # -------------------------
    # Step 9: 生成初始网格
    # -------------------------
    print("\n[Step 9] 生成初始网格...")
    print("  ⏳ 正在生成网格，请稍候...")
    
    try:
        # 尝试生成网格
        mesh_result = m3d.mesh.generate_mesh()
        if mesh_result:
            print("  ✓ 网格生成成功！")
            
            # 获取网格统计信息
            try:
                mesh_stats = m3d.mesh.get_mesh_statistics()
                if mesh_stats:
                    print(f"  网格统计: {mesh_stats}")
            except:
                pass
        else:
            print("  ✗ 网格生成失败")
    except Exception as e:
        print(f"  ✗ 网格生成错误: {e}")
        print("\n可能的原因:")
        print("  1. 几何模型包含无效实体")
        print("  2. 存在极小/极薄的几何特征")
        print("  3. 实体之间存在布尔运算问题")
        print("\n建议:")
        print("  - 在 SpaceClaim 中进一步简化模型")
        print("  - 使用 Heal 工具修复几何")
        print("  - 删除小于 1mm 的特征")
    
    # -------------------------
    # 完成
    # -------------------------
    print("\n" + "=" * 70)
    print("网格测试完成")
    print("=" * 70)
    
    print("\n下一步:")
    print("  - 如果网格成功: 可以继续设置完整的仿真")
    print("  - 如果网格失败: 需要回到 SpaceClaim 进一步简化模型")
    
    # 释放但不关闭 Maxwell
    m3d.release_desktop(close_projects=False, close_desktop=False)
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Maxwell 网格测试脚本")
    parser.add_argument(
        "--project", "-p",
        default=None,
        help="项目名称 (不指定则使用当前活动项目)"
    )
    parser.add_argument(
        "--design", "-d",
        default=None,
        help="设计名称 (不指定则使用当前活动设计)"
    )
    
    args = parser.parse_args()
    
    success = run_mesh_test(project_name=args.project, design_name=args.design)
    
    if success:
        print("\n✅ 测试完成，请在 Maxwell 中查看结果")
    else:
        print("\n❌ 测试失败，请检查模型或错误信息")
        sys.exit(1)


if __name__ == "__main__":
    main()
