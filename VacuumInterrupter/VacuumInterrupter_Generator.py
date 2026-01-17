# -*- coding: utf-8 -*-
"""
真空灭弧室 (Vacuum Interrupter) 瞬态电磁仿真脚本
12kV / 4000A 级别

v5 - Transient版本：
1. 连续的陶瓷绝缘外壳（整体圆筒）
2. 主屏蔽罩（在内部包围触头区域）
3. 动/静端盖板（金属法兰在两端）
4. 动/静触头 + 导电杆（从陶瓷管中心穿出）
5. 动触头运动设置（模拟开断过程）

Author: Antigravity Assistant
Date: 2026-01-17
"""

from pyaedt import Maxwell3d
import os

# =============================================================================
# 参数设置 - 12kV/4000A 真空灭弧室
# =============================================================================
# 单位: mm

# --- 整体尺寸 ---
VI_TOTAL_LENGTH = 360.0      # 真空灭弧室总高度
VI_OUTER_DIAMETER = 120.0    # 陶瓷管外径

# --- 陶瓷绝缘管（连续整体） ---
CERAMIC_THICKNESS = 8.0      # 陶瓷壁厚
CERAMIC_LENGTH = 280.0       # 陶瓷管长度（中间主体部分）

# --- 端盖板（动/静端金属法兰） ---
END_CAP_OUTER_DIAMETER = 130.0  # 端盖外径
END_CAP_THICKNESS = 20.0        # 端盖厚度
END_CAP_INNER_RADIUS = 20.0     # 端盖中心孔半径（导电杆穿过）

# --- 主屏蔽罩 (Shield) ---
SHIELD_OUTER_RADIUS = 48.0     # 屏蔽罩外半径
SHIELD_THICKNESS = 1.5         # 壁厚
SHIELD_LENGTH = 180.0          # 长度（包围触头区域）

# --- 触头 (Contacts) ---
CONTACT_DISC_RADIUS = 42.0     # 触头盘半径 (接近屏蔽罩内径)
CONTACT_DISC_THICKNESS = 12.0  # 触头盘厚度

# --- 导电杆 (Conductive Rod) ---
CONTACT_ROD_RADIUS = 16.0      # 导电杆半径

# --- 触头开距 ---
CONTACT_GAP = 0.0              # 初始开距(闭合状态)
CONTACT_GAP_MAX = 16.0         # 最大开距

# --- 运动参数 ---
MOTION_VELOCITY = 1.0          # 分闸速度 m/s (1000 mm/s)
MOTION_TIME = 0.016            # 分闸时间 s (16ms达到最大开距)

# =============================================================================
# 计算关键位置
# =============================================================================
# 中心点
CENTER_Z = VI_TOTAL_LENGTH / 2

# 陶瓷管位置（居中）
CERAMIC_Z_START = (VI_TOTAL_LENGTH - CERAMIC_LENGTH) / 2

# 端盖位置
LOWER_END_CAP_Z = CERAMIC_Z_START - END_CAP_THICKNESS  # 动端盖板（下方）
UPPER_END_CAP_Z = CERAMIC_Z_START + CERAMIC_LENGTH      # 静端盖板（上方）

# =============================================================================
# 脚本开始
# =============================================================================

project_name = "VacuumInterrupter_12kV_4000A_v5_Transient"
design_name = "Transient_VI_Model"

print("=" * 60)
print("真空灭弧室瞬态仿真 - 12kV/4000A (v5 - Transient)")
print("=" * 60)

m3d = Maxwell3d(
    projectname=project_name,
    designname=design_name,
    solution_type="Transient",
    new_desktop_session=True,
    non_graphical=False
)

m3d.modeler.model_units = "mm"

print("[1/7] 创建材料...")

# =============================================================================
# 1. 材料定义
# =============================================================================
if not m3d.materials.checkifmaterialexists("Alumina_Ceramic"):
    mat = m3d.materials.add_material("Alumina_Ceramic")
    mat.permittivity = 9.4

if not m3d.materials.checkifmaterialexists("CuCr_Alloy"):
    mat = m3d.materials.add_material("CuCr_Alloy")
    mat.conductivity = 2.9e7

print("[2/7] 创建连续陶瓷绝缘外壳...")

# =============================================================================
# 2. 连续陶瓷绝缘外壳 (Ceramic Insulator - 整体)
# =============================================================================
ceramic_inner_radius = (VI_OUTER_DIAMETER / 2) - CERAMIC_THICKNESS

ceramic_shell = m3d.modeler.create_cylinder(
    orientation="Z",
    origin=[0, 0, CERAMIC_Z_START],
    radius=VI_OUTER_DIAMETER / 2,
    height=CERAMIC_LENGTH,
    name="Ceramic_Insulator",
    material="Alumina_Ceramic"
)

ceramic_void = m3d.modeler.create_cylinder(
    orientation="Z",
    origin=[0, 0, CERAMIC_Z_START],
    radius=ceramic_inner_radius,
    height=CERAMIC_LENGTH,
    name="Ceramic_Void"
)

m3d.modeler.subtract(ceramic_shell, [ceramic_void], keep_originals=False)

print("[3/7] 创建动端盖板（下方）...")

# =============================================================================
# 3. 动端盖板 (Moving End Cap - 下方)
# =============================================================================
lower_end_cap = m3d.modeler.create_cylinder(
    orientation="Z",
    origin=[0, 0, LOWER_END_CAP_Z],
    radius=END_CAP_OUTER_DIAMETER / 2,
    height=END_CAP_THICKNESS,
    name="Moving_End_Cap",
    material="steel_stainless"
)

lower_cap_void = m3d.modeler.create_cylinder(
    orientation="Z",
    origin=[0, 0, LOWER_END_CAP_Z],
    radius=END_CAP_INNER_RADIUS,
    height=END_CAP_THICKNESS,
    name="Lower_Cap_Void"
)

m3d.modeler.subtract(lower_end_cap, [lower_cap_void], keep_originals=False)

print("[4/7] 创建静端盖板（上方）...")

# =============================================================================
# 4. 静端盖板 (Fixed End Cap - 上方)
# =============================================================================
upper_end_cap = m3d.modeler.create_cylinder(
    orientation="Z",
    origin=[0, 0, UPPER_END_CAP_Z],
    radius=END_CAP_OUTER_DIAMETER / 2,
    height=END_CAP_THICKNESS,
    name="Fixed_End_Cap",
    material="steel_stainless"
)

upper_cap_void = m3d.modeler.create_cylinder(
    orientation="Z",
    origin=[0, 0, UPPER_END_CAP_Z],
    radius=END_CAP_INNER_RADIUS,
    height=END_CAP_THICKNESS,
    name="Upper_Cap_Void"
)

m3d.modeler.subtract(upper_end_cap, [upper_cap_void], keep_originals=False)

print("[5/7] 创建屏蔽罩...")

# =============================================================================
# 5. 屏蔽罩 (Shield) - 在法兰内部，包围触头区域
# =============================================================================
shield_z = CENTER_Z - SHIELD_LENGTH / 2

shield_outer = m3d.modeler.create_cylinder(
    orientation="Z",
    origin=[0, 0, shield_z],
    radius=SHIELD_OUTER_RADIUS,
    height=SHIELD_LENGTH,
    name="Shield",
    material="copper"  # 实际可能是不锈钢或铜
)

shield_inner = m3d.modeler.create_cylinder(
    orientation="Z",
    origin=[0, 0, shield_z],
    radius=SHIELD_OUTER_RADIUS - SHIELD_THICKNESS,
    height=SHIELD_LENGTH,
    name="Shield_Inner_Void"
)

m3d.modeler.subtract(shield_outer, [shield_inner], keep_originals=False)

print("[6/7] 创建触头和导电杆...")

# =============================================================================
# 6. 静触头 (Fixed Contact) - 上方
# =============================================================================
fixed_disc_z = CENTER_Z + CONTACT_GAP / 2

# 静触头盘
fixed_disc = m3d.modeler.create_cylinder(
    orientation="Z",
    origin=[0, 0, fixed_disc_z],
    radius=CONTACT_DISC_RADIUS,
    height=CONTACT_DISC_THICKNESS,
    name="Fixed_Contact_Disc",
    material="CuCr_Alloy"
)

# 静触头导电杆（向上延伸穿出陶瓷管）
fixed_rod_start = fixed_disc_z + CONTACT_DISC_THICKNESS
fixed_rod_length = VI_TOTAL_LENGTH - fixed_rod_start + 30  # 延伸到外部

fixed_rod = m3d.modeler.create_cylinder(
    orientation="Z",
    origin=[0, 0, fixed_rod_start],
    radius=CONTACT_ROD_RADIUS,
    height=fixed_rod_length,
    name="Fixed_Rod",
    material="copper"
)

m3d.modeler.unite([fixed_disc, fixed_rod])

# =============================================================================
# 7. 动触头 (Moving Contact) - 下方
# =============================================================================
moving_disc_z = CENTER_Z - CONTACT_GAP / 2 - CONTACT_DISC_THICKNESS

# 动触头盘
moving_disc = m3d.modeler.create_cylinder(
    orientation="Z",
    origin=[0, 0, moving_disc_z],
    radius=CONTACT_DISC_RADIUS,
    height=CONTACT_DISC_THICKNESS,
    name="Moving_Contact_Disc",
    material="CuCr_Alloy"
)

# 动触头导电杆（向下延伸穿出陶瓷管）
moving_rod_start = -30  # 从底部外开始
moving_rod_length = moving_disc_z - moving_rod_start

moving_rod = m3d.modeler.create_cylinder(
    orientation="Z",
    origin=[0, 0, moving_rod_start],
    radius=CONTACT_ROD_RADIUS,
    height=moving_rod_length,
    name="Moving_Rod",
    material="copper"
)

m3d.modeler.unite([moving_disc, moving_rod])

print("[7/8] 创建真空区域...")

# =============================================================================
# 8. 真空区域 (内部空腔 - 整体)
# 需要从真空区域中减去触头和导电杆，避免几何体重叠
# =============================================================================
vacuum_region = m3d.modeler.create_cylinder(
    orientation="Z",
    origin=[0, 0, CERAMIC_Z_START],
    radius=ceramic_inner_radius - 1,
    height=CERAMIC_LENGTH,
    name="Vacuum_Region",
    material="vacuum"
)

# 创建用于减法的触头和导电杆副本（避免破坏原始对象）
# 静触头+导电杆挖空区域
fixed_cutout = m3d.modeler.create_cylinder(
    orientation="Z",
    origin=[0, 0, fixed_disc_z],
    radius=CONTACT_DISC_RADIUS + 0.5,  # 略大于触头，确保完全挖空
    height=fixed_rod_length + CONTACT_DISC_THICKNESS + 10,
    name="Fixed_Cutout"
)

# 动触头+导电杆挖空区域
moving_cutout = m3d.modeler.create_cylinder(
    orientation="Z",
    origin=[0, 0, moving_rod_start],
    radius=CONTACT_DISC_RADIUS + 0.5,
    height=moving_disc_z + CONTACT_DISC_THICKNESS - moving_rod_start + 10,
    name="Moving_Cutout"
)

# 从真空区域中减去触头区域
m3d.modeler.subtract(vacuum_region, [fixed_cutout, moving_cutout], keep_originals=False)
print("  [信息] 已从真空区域中排除触头和导电杆区域")

print("[8/8] 设置激励和分析...")

# =============================================================================
# 9. 动触头运动设置 (Motion Setup)
# 注意：运动设置需要在Maxwell GUI中手动配置，步骤如下：
# 1. 创建Band对象（包围动触头的区域）
# 2. 右键Band -> Assign Motion -> Translational
# 3. 设置：Velocity = 1000 mm/s, 方向 = -Z
# =============================================================================
print("  [提示] 运动设置需在Maxwell GUI中手动配置")

# =============================================================================
# 10. 设置瞬态激励 - 使用原生AEDT API (面选择)
# =============================================================================
RATED_CURRENT = 4000  # 额定电流 A

try:
    oDesign = m3d.odesign
    
    # 获取导电杆对象的面
    fixed_obj = m3d.modeler["Fixed_Contact_Disc"]
    moving_obj = m3d.modeler["Moving_Contact_Disc"]
    
    # 获取面ID - 顶面和底面
    fixed_faces = fixed_obj.faces
    moving_faces = moving_obj.faces
    
    # 找到最顶部的面 (静触头顶端)
    fixed_top_face = max(fixed_faces, key=lambda f: f.center[2])
    # 找到最底部的面 (动触头底端)
    moving_bottom_face = min(moving_faces, key=lambda f: f.center[2])
    
    # 创建线圈终端 - 静触头 (Positive)
    oDesign.AssignCoil(
        [
            "NAME:Coil_Input",
            "Objects:=", [],
            "Faces:=", [fixed_top_face.id],
            "Conductor number:=", "1",
            "PolarityType:=", "Positive"
        ]
    )
    
    # 创建线圈终端 - 动触头 (Negative)  
    oDesign.AssignCoil(
        [
            "NAME:Coil_Output",
            "Objects:=", [],
            "Faces:=", [moving_bottom_face.id],
            "Conductor number:=", "1",
            "PolarityType:=", "Negative"
        ]
    )
    
    # 创建绕组并设置电流
    oDesign.AssignWinding(
        [
            "NAME:Main_Winding",
            "Type:=", "Current",
            "IsSolid:=", True,
            "Current:=", f"{RATED_CURRENT}A",
            "Resistance:=", "0ohm",
            "Inductance:=", "0nH",
            "Voltage:=", "0mV",
            "ParallelBranchesNum:=", "1",
            "Phase:=", "0deg"
        ],
        ["Coil_Input", "Coil_Output"]
    )
    
    print(f"  [信息] 已设置绕组激励: 电流 = {RATED_CURRENT}A (通过面选择)")
except Exception as e:
    print(f"  [警告] 激励设置遇到问题: {str(e)[:80]}")
    print(f"  [提示] 请在Maxwell GUI中手动配置激励:")
    print(f"         1. 选择导电杆端面 -> Assign Excitation -> Coil")
    print(f"         2. 创建绕组: Excitations -> Add Winding")
    print(f"         3. 设置电流 = {RATED_CURRENT}A")

# =============================================================================
# 11. 创建瞬态分析设置 (简化版)
# =============================================================================
setup = m3d.create_setup(name="Transient_Setup")
setup.props["StopTime"] = f"{MOTION_TIME}s"
setup.props["TimeStep"] = "0.0005s"  # 0.5ms时间步长

# 添加参数化变量（便于后续扫描）
m3d["contact_gap"] = f"{CONTACT_GAP}mm"
m3d["max_gap"] = f"{CONTACT_GAP_MAX}mm"

m3d.save_project()

print("=" * 60)
print("瞬态仿真模型创建完成! (v5 - Transient)")
print(f"项目路径: {m3d.project_path}")
print("=" * 60)
print("\n结构说明:")
print("  1. 静端盖板 (上方金属盖)")
print("  2. 主屏蔽罩 (内部包围触头)")
print("  3. 动/静触头 + 导电杆 (触头盘φ84mm)")
print("  4. 动端盖板 (下方金属盖)")
print("  5. 绝缘外壳 (连续整体陶瓷管)")
print("  6. 真空区域 (内部空腔)")
print("\n仿真参数:")
print(f"  额定电流: {RATED_CURRENT} A")
print(f"  分闸速度: {MOTION_VELOCITY} m/s")
print(f"  分闸时间: {MOTION_TIME * 1000} ms")
print(f"  最大开距: {CONTACT_GAP_MAX} mm")

# m3d.analyze_all()
# m3d.release_desktop()


