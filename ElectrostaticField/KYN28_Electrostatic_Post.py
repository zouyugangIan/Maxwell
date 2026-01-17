"""
KYN28_Electrostatic_Post.py

用于生成优化的电场云图，辅助判断空气是否击穿。
功能：
1. 连接到当前已打开的 Maxwell 会话 (不启动新窗口)。
2. 创建切面 (CutPlane) 并生成 0-3kV/mm 限制的云图。
3. 创建 3kV/mm 的等值面 (Iso-Surface) 用于 3D 击穿判定。
"""
import os
import sys

# 设置 ANSYS 2024R2 路径 (如果需要)
os.environ["ANSYSEM_ROOT242"] = r"G:\Ansys2024R2\v242\Win64"

from pyaedt import Maxwell3d
from pyaedt import settings

# 禁用 gRPC 以确保能连接到旧的 COM 会话 (视情况而定，但 2024R2 通常支持 gRPC)
# 如果连接失败，可以尝试注释掉下面这行
settings.use_grpc_api = False
settings.enable_error_handler = False

PROJECT_NAME = "KYN28_Electrostatic"
DESIGN_NAME = "ElectrostaticField"

def main():
    print(f"[KYN28 Post] 正在尝试连接到活动会话...")
    try:
        # 核心修改: new_desktop_session=False
        m3d = Maxwell3d(
            projectname=PROJECT_NAME, 
            designname=DESIGN_NAME, 
            specified_version="2024.2",
            new_desktop_session=False # <--- 关键修改：连接现有会话
        )
    except Exception as e:
        print(f"✗ 无法连接到活动会话: {e}")
        print("-> 请确保 Maxwell 界面已打开，并且项目名称为 KYN28_Electrostatic")
        return

    print("✓ 连接成功")
    
    # 1. 创建切面 (XZ Plane)
    print("\n[1] 创建切面...")
    try:
        plane_name = "CutPlane_YZ_Center"
        m3d.modeler.create_coordinate_system(origin=[0,0,0], mode="view", name="CS_View")
        
        # 尝试创建平面，如果已存在则忽略或覆盖
        # 避免使用 .plane_names 属性，该属性在某些版本中可能不存在
        try:
            m3d.modeler.create_plane("YZ", origin=[0,0,0], name=plane_name)
            print(f"  ✓ 切面已创建: {plane_name}")
        except Exception as pe:
            print(f"  ℹ 切面创建跳过 (可能已存在): {pe}")
        
        # 2. 创建 Mag_E 云图
        print("\n[2] 创建云图 (0-3e6 V/m)...")
        plot_name = "E_Field_Check_Air"
        
        # 删除旧图
        try: m3d.post.delete_report(plot_name) 
        except: pass
        
        plot = m3d.post.create_fieldplot_surface(
            assignment=[plane_name],
            quantity="Mag_E",
            plot_name=plot_name
        )
        
        if plot:
            # 3. 修改 Scale
            # 注意: ColorMapSettings 属性访问方式
            try:
                plot.ColorMapSettings.Scale3d.Max = 3.0e6 
                plot.ColorMapSettings.Scale3d.Min = 0.0
                plot.ColorMapSettings.Scale3d.UseAuto = False
                plot.update()
                print(f"  ✓ 云图已生成: {plot_name}")
            except Exception as se:
                 print(f"  ⚠ 无法设置 Scale，请手动在 GUI 中调整: {se}")
        
        # 4. 创建 IsoSurface (等值面)
        print("\n[3] 创建击穿等值面 (IsoSurface @ 3kV/mm)...")
        iso_name = "Breakdown_Envelop_3kVmm"
        try: m3d.post.delete_report(iso_name)
        except: pass
        
        m3d.post.create_fieldplot_iso(
            assignment=m3d.modeler.solid_names, 
            quantity="Mag_E",
            iso_value=3.0e6,
            plot_name=iso_name
        )
        print(f"  ✓ 等值面已生成: {iso_name}")
        
    except Exception as e:
        print(f"  ⚠ 绘图过程出错: {e}")

    # 不要关闭 Desktop
    m3d.release_desktop(False, False)
    print("\n[完成] 请切换回 Maxwell 窗口查看结果。")

if __name__ == "__main__":
    main()
