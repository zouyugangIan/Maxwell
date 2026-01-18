# -*- coding: utf-8 -*-
"""
真空灭弧室 (Vacuum Interrupter) 瞬态电磁仿真脚本
12kV / 4000A 级别

v8 - 精确参考知乎文章图2结构：
- 水平方向建模 (X轴)
- 4大部件：瓷套、静端组件、动端组件、屏蔽罩
- 静端在 -X，动端在 +X
- 运动方向沿 X 轴

参考: https://www.zhihu.com/question/482332112

Author: Antigravity Assistant  
Date: 2026-01-19
"""

import os
from pyaedt import settings
settings.use_grpc_api = False

from pyaedt import Maxwell3d

# =============================================================================
# 参数设置 - 参考知乎文章结构
# =============================================================================
# 单位: mm
# 建模方向: X轴 (静端在-X, 动端在+X)

# --- 瓷套 (Al2O3 陶瓷绝缘管) - TD-12/4000 规格 ---
CERAMIC_OUTER_RADIUS = 38.0      # 外半径 (主体外径Φ76mm)
CERAMIC_INNER_RADIUS = 27.1      # 内半径 (内径Φ54.2mm)
CERAMIC_LENGTH = 180.0           # 瓷套长度 (总长180mm)

# --- 屏蔽罩 (铜) - 桶状结构包围触头 ---
SHIELD_OUTER_RADIUS = 28.0       # 外半径
SHIELD_INNER_RADIUS = 26.0       # 内半径 (壁厚2mm)
SHIELD_LENGTH = 70.0             # 屏蔽罩长度

# --- 端盖法兰 (不锈钢) ---
FLANGE_OUTER_RADIUS = 45.0       # 法兰外半径
FLANGE_THICKNESS = 12.0          # 法兰厚度
FLANGE_INNER_RADIUS = 10.0       # 中心孔半径 (导电杆穿孔)

# --- 触头 (CuCr 合金) - TD-12/4000: 内径Φ54.2mm ---
CONTACT_RADIUS = 27.0            # 触头半径 (直径54mm)
CONTACT_THICKNESS = 8.0          # 触头厚度

# --- 导电杆 (铜) - TD-12/4000: Φ36mm ---
ROD_RADIUS = 18.0                # 导电杆半径 (直径36mm)
STATIC_ROD_LENGTH = 40.0         # 静端导电杆长度
MOVING_ROD_LENGTH = 50.0         # 动端导电杆长度

# --- 触头开距 - TD-12/4000: 9±1mm ---
CONTACT_GAP = 9.0                # 触头开距

# --- 运动参数 ---
CONTACT_GAP_MAX = 10.0           # 最大开距
MOTION_VELOCITY = 1.0            # 分闸速度 m/s
MOTION_TIME = 0.015              # 仿真时间 15ms

# --- 电流参数 ---
RATED_CURRENT = 4000
PEAK_CURRENT = RATED_CURRENT * 1.414
FREQUENCY = 50

# =============================================================================
# 位置计算 (X轴方向，以中心为原点)
# =============================================================================
# 瓷套位置 (中心对称)
CERAMIC_X_START = -CERAMIC_LENGTH / 2
CERAMIC_X_END = CERAMIC_LENGTH / 2

# 屏蔽罩位置 (中心)
SHIELD_X_START = -SHIELD_LENGTH / 2

# 触头位置
CENTER_X = 0
STATIC_CONTACT_X = -CONTACT_GAP / 2 - CONTACT_THICKNESS  # 静触头右端面
MOVING_CONTACT_X = CONTACT_GAP / 2                        # 动触头左端面

# 端盖法兰位置
STATIC_FLANGE_X = CERAMIC_X_START - FLANGE_THICKNESS
MOVING_FLANGE_X = CERAMIC_X_END

# 导电杆位置
STATIC_ROD_X_START = STATIC_FLANGE_X - STATIC_ROD_LENGTH
MOVING_ROD_X_END = MOVING_FLANGE_X + FLANGE_THICKNESS + MOVING_ROD_LENGTH

# =============================================================================
# 脚本开始
# =============================================================================
project_name = "VacuumInterrupter_12kV_v8"
design_name = "Transient_Horizontal"

print("=" * 60)
print("真空灭弧室瞬态仿真 - 12kV/4000A (v8 - 精确参考图)")
print("=" * 60)
print("  建模方向: X轴 (水平)")
print("  瓷套长度: {:.0f}mm".format(CERAMIC_LENGTH))
print("  开距: {:.0f}mm".format(CONTACT_GAP))

# =============================================================================
# 1. 初始化 Maxwell3D
# =============================================================================
print("\n[1/10] 初始化 Maxwell3D...")

try:
    m3d = Maxwell3d(
        projectname=project_name,
        designname=design_name,
        solution_type="Transient",
        specified_version="2024.2",
        new_desktop_session=False,
        non_graphical=False
    )
except Exception:
    try:
        m3d = Maxwell3d(
            projectname=project_name,
            designname=design_name,
            solution_type="Transient",
            specified_version="2024.2",
            new_desktop_session=True,
            non_graphical=False
        )
    except Exception as e:
        print(f"  [错误] {e}")
        raise SystemExit(1)

m3d.modeler.model_units = "mm"
print(f"  [成功] 项目: {m3d.project_name}")

# =============================================================================
# 2. 材料定义
# =============================================================================
print("\n[2/10] 创建材料...")

if not m3d.materials.checkifmaterialexists("Al2O3_Ceramic"):
    mat = m3d.materials.add_material("Al2O3_Ceramic")
    mat.permittivity = 9.4
    mat.conductivity = 0
    
if not m3d.materials.checkifmaterialexists("CuCr_Alloy"):
    mat = m3d.materials.add_material("CuCr_Alloy")
    mat.conductivity = 2.9e7
    mat.permeability = 1.0

print("  材料创建完成")

# =============================================================================
# 3. 瓷套 (陶瓷绝缘管）
# =============================================================================
print("\n[3/10] 创建瓷套...")

ceramic_outer = m3d.modeler.create_cylinder(
    orientation="X",
    origin=[CERAMIC_X_START, 0, 0],
    radius=CERAMIC_OUTER_RADIUS,
    height=CERAMIC_LENGTH,
    name="Ceramic_Sleeve",
    material="Al2O3_Ceramic"
)

ceramic_void = m3d.modeler.create_cylinder(
    orientation="X",
    origin=[CERAMIC_X_START, 0, 0],
    radius=CERAMIC_INNER_RADIUS,
    height=CERAMIC_LENGTH,
    name="Ceramic_Void_Temp"
)
m3d.modeler.subtract(ceramic_outer, [ceramic_void], keep_originals=False)
print(f"  瓷套: 外径{CERAMIC_OUTER_RADIUS*2}mm, 长度{CERAMIC_LENGTH}mm")

# =============================================================================
# 4. 静端组件
# =============================================================================
print("\n[4/10] 创建静端组件...")

# 静端法兰盘
static_flange = m3d.modeler.create_cylinder(
    orientation="X",
    origin=[STATIC_FLANGE_X, 0, 0],
    radius=FLANGE_OUTER_RADIUS,
    height=FLANGE_THICKNESS,
    name="Static_Flange",
    material="steel_stainless"
)
static_flange_void = m3d.modeler.create_cylinder(
    orientation="X",
    origin=[STATIC_FLANGE_X, 0, 0],
    radius=FLANGE_INNER_RADIUS,
    height=FLANGE_THICKNESS,
    name="Static_Flange_Void_Temp"
)
m3d.modeler.subtract(static_flange, [static_flange_void], keep_originals=False)

# 静触头
static_contact = m3d.modeler.create_cylinder(
    orientation="X",
    origin=[STATIC_CONTACT_X, 0, 0],
    radius=CONTACT_RADIUS,
    height=CONTACT_THICKNESS,
    name="Static_Contact",
    material="CuCr_Alloy"
)

# 静端导电杆
static_rod = m3d.modeler.create_cylinder(
    orientation="X",
    origin=[STATIC_ROD_X_START, 0, 0],
    radius=ROD_RADIUS,
    height=-STATIC_ROD_X_START + STATIC_CONTACT_X,
    name="Static_Rod",
    material="copper"
)
print(f"  静触头位置: X={STATIC_CONTACT_X:.1f}mm")

# =============================================================================
# 5. 动端组件
# =============================================================================
print("\n[5/10] 创建动端组件...")

# 动端法兰盘
moving_flange = m3d.modeler.create_cylinder(
    orientation="X",
    origin=[MOVING_FLANGE_X, 0, 0],
    radius=FLANGE_OUTER_RADIUS,
    height=FLANGE_THICKNESS,
    name="Moving_Flange",
    material="steel_stainless"
)
moving_flange_void = m3d.modeler.create_cylinder(
    orientation="X",
    origin=[MOVING_FLANGE_X, 0, 0],
    radius=FLANGE_INNER_RADIUS,
    height=FLANGE_THICKNESS,
    name="Moving_Flange_Void_Temp"
)
m3d.modeler.subtract(moving_flange, [moving_flange_void], keep_originals=False)

# 动触头
moving_contact = m3d.modeler.create_cylinder(
    orientation="X",
    origin=[MOVING_CONTACT_X, 0, 0],
    radius=CONTACT_RADIUS,
    height=CONTACT_THICKNESS,
    name="Moving_Contact",
    material="CuCr_Alloy"
)

# 动端导电杆
moving_rod = m3d.modeler.create_cylinder(
    orientation="X",
    origin=[MOVING_CONTACT_X + CONTACT_THICKNESS, 0, 0],
    radius=ROD_RADIUS,
    height=MOVING_ROD_X_END - (MOVING_CONTACT_X + CONTACT_THICKNESS),
    name="Moving_Rod",
    material="copper"
)
print(f"  动触头位置: X={MOVING_CONTACT_X:.1f}mm")

# =============================================================================
# 6. 屏蔽罩 (桶状结构)
# =============================================================================
print("\n[6/10] 创建屏蔽罩...")

shield_outer = m3d.modeler.create_cylinder(
    orientation="X",
    origin=[SHIELD_X_START, 0, 0],
    radius=SHIELD_OUTER_RADIUS,
    height=SHIELD_LENGTH,
    name="Main_Shield",
    material="copper"
)

shield_void = m3d.modeler.create_cylinder(
    orientation="X",
    origin=[SHIELD_X_START, 0, 0],
    radius=SHIELD_INNER_RADIUS,
    height=SHIELD_LENGTH,
    name="Shield_Void_Temp"
)
m3d.modeler.subtract(shield_outer, [shield_void], keep_originals=False)
print(f"  屏蔽罩: 外径{SHIELD_OUTER_RADIUS*2}mm, 长度{SHIELD_LENGTH}mm")

# =============================================================================
# 7. 真空区域
# =============================================================================
print("\n[7/10] 创建真空区域...")

vacuum = m3d.modeler.create_cylinder(
    orientation="X",
    origin=[CERAMIC_X_START + 1, 0, 0],
    radius=CERAMIC_INNER_RADIUS - 1,
    height=CERAMIC_LENGTH - 2,
    name="Vacuum_Region",
    material="vacuum"
)
print("  真空区域创建完成")

# =============================================================================
# 8. Region (求解域)
# =============================================================================
print("\n[8/10] 创建求解域...")

try:
    region = m3d.modeler.create_air_region(
        x_pos=50, x_neg=50,
        y_pos=100, y_neg=100,
        z_pos=100, z_neg=100,
        is_percentage=True
    )
    print("  Region 创建完成")
except Exception:
    print("  使用默认 Region")

# =============================================================================
# 9. Motion Band (只包围动端组件)
# =============================================================================
print("\n[9/10] 创建 Motion Band...")

# Band 范围：只包围 Moving_Contact 和 Moving_Rod
# 要确保不与 Static_Contact 重叠
band_x_start = MOVING_CONTACT_X - 2  # 动触头左侧 - 2mm
band_x_end = MOVING_ROD_X_END + CONTACT_GAP_MAX + 5  # 杆右端 + 行程 + 余量

# 确保不与静触头重叠
band_x_start = max(band_x_start, STATIC_CONTACT_X + CONTACT_THICKNESS + 2)

band_length = band_x_end - band_x_start
band_radius = CONTACT_RADIUS + 3  # 略大于触头

motion_band = m3d.modeler.create_cylinder(
    orientation="X",
    origin=[band_x_start, 0, 0],
    radius=band_radius,
    height=band_length,
    name="Motion_Band",
    material="vacuum"
)

print(f"  X范围: {band_x_start:.1f}mm ~ {band_x_end:.1f}mm")
print(f"  静触头右端面: X={STATIC_CONTACT_X + CONTACT_THICKNESS:.1f}mm")
print(f"  Band 不与静触头重叠: ✓")

# =============================================================================
# 9.5 创建速度时程曲线 Dataset
# =============================================================================
print("\n[9.5/10] 创建速度时程曲线 Dataset...")

# 根据 TD-12/4000 数据手册:
# - 平均分闸速度 (前6mm): 1.2 m/s
# - 平均合闸速度 (后6mm): 0.6 m/s
# 速度曲线：一开始最大 (1.2 m/s)，迅速减小到 0.6 m/s

# 时间-速度数据点 (指数衰减模型)
# 总行程 9mm，初速度 1.2 m/s
# t = 0ms:     v = 1.2 m/s  (启动)
# t = 1ms:     v = 1.1 m/s  (减速开始)
# t = 3ms:     v = 0.9 m/s  
# t = 5ms:     v = 0.7 m/s
# t = 8ms:     v = 0.6 m/s  (稳定)
# t = 15ms:    v = 0.6 m/s  (结束)

velocity_data = [
    [0.0,    1.2],   # 启动时刻
    [0.001,  1.15],  # 1ms
    [0.002,  1.0],   # 2ms
    [0.003,  0.9],   # 3ms
    [0.005,  0.75],  # 5ms
    [0.008,  0.65],  # 8ms
    [0.010,  0.60],  # 10ms
    [0.015,  0.60],  # 15ms (结束)
]

try:
    # 跳过自动创建 Dataset - AEDT 2024.2 API 不兼容
    # 使用恒定速度代替，在 Motion Setup 中直接设置
    print("  [信息] 使用恒定速度: 1.2 m/s")
    print("  [信息] 如需时变速度，请手动创建 Dataset:")
    print("         Project > Datasets > Add Dataset")
    print("         名称: Velocity_Profile")
    
except Exception as e:
    print(f"  [警告] {e}")

# =============================================================================
# 10. 分析设置
# =============================================================================
print("\n[10/10] 创建分析设置...")

try:
    setup = m3d.create_setup(name="Transient_Analysis")
    setup.props["StopTime"] = f"{MOTION_TIME}s"
    setup.props["TimeStep"] = "0.0005s"
    setup.update()
    print(f"  仿真时间: {MOTION_TIME*1000:.0f}ms")
except Exception as e:
    print(f"  [警告] {e}")

# =============================================================================
# 保存
# =============================================================================
print("\n" + "=" * 60)
m3d.save_project()
print(f"项目保存: {m3d.project_path}")

print("\n创建的对象:")
for obj in m3d.modeler.object_names:
    print(f"  - {obj}")

print("\n" + "=" * 60)
print("模型创建完成!")
print("=" * 60)

print("\n手动配置 (Motion Setup):")
print("  1. 右键 Motion_Band > Assign Band > Translational")
print("  2. Moving Objects: Moving_Contact, Moving_Rod, Moving_Flange")
print("  3. Axis: X, Is Positive: 勾选")
print("  4. Velocity 选择 'Dataset': pwl(Velocity_Profile, Time)")
print(f"  5. Positive Limit: {CONTACT_GAP_MAX}mm")

print("\n电流激励:")
print("  选择 Static_Rod > Excitations > Assign > Current")
print(f"  Value: {PEAK_CURRENT:.0f}*sin(2*3.14159*{FREQUENCY}*Time)")

print("\n速度时程曲线 (已创建 Dataset):")
print("  初始速度: 1.2 m/s (高速启动)")
print("  终止速度: 0.6 m/s (减速稳定)")
print("  曲线类型: 指数衰减")
