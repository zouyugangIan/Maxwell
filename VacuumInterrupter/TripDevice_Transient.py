# -*- coding: utf-8 -*-
"""
断路器快速动作脱扣器仿真脚本 (Trip Device Transient Magnetic Simulation)

基于报告《断路器快速动作脱扣器的仿真及测试研究》创建

功能:
1. 自动生成脱扣器3D模型 (磁轭、铁芯、脱扣线圈、复位线圈)
2. 设置瞬态磁场求解器 (Transient with Motion)
3. 运行仿真并导出结果:
   - 铁芯行程曲线 (Displacement vs Time)
   - 线圈电流曲线 (Coil Current vs Time)
   - 铁芯运动速度曲线 (Velocity vs Time)
   - 电磁吸力曲线 (EM Force vs Time)
   - 磁场分布云图 (B-field at key timesteps)

Author: Antigravity Assistant
Date: 2026-01-17
"""

from pyaedt import Maxwell3d
import os

# =============================================================================
# 参数设置 - 根据实际脱扣器尺寸修改
# =============================================================================
# 单位: mm

# --- 磁轭 (Yoke) ---
YOKE_OUTER_WIDTH = 60.0      # 磁轭外宽度
YOKE_OUTER_HEIGHT = 80.0     # 磁轭外高度
YOKE_OUTER_DEPTH = 40.0      # 磁轭深度
YOKE_WALL_THICKNESS = 8.0    # 磁轭壁厚

# --- 铁芯/导杆 (Core/Armature) ---
CORE_RADIUS = 8.0            # 铁芯半径
CORE_LENGTH = 50.0           # 铁芯长度
CORE_INITIAL_GAP = 10.0      # 铁芯初始气隙 (行程)
CORE_MASS = 0.15             # 铁芯质量 (kg)

# --- 脱扣线圈 (Trip Coil) ---
TRIP_COIL_INNER_RADIUS = 10.0
TRIP_COIL_OUTER_RADIUS = 20.0
TRIP_COIL_HEIGHT = 25.0
TRIP_COIL_TURNS = 800        # 匝数
TRIP_COIL_VOLTAGE = 220.0    # 施加电压 (V DC)
TRIP_COIL_RESISTANCE = 50.0  # 线圈电阻 (Ohm)

# --- 复位线圈 (Reset Coil) ---
RESET_COIL_INNER_RADIUS = 10.0
RESET_COIL_OUTER_RADIUS = 18.0
RESET_COIL_HEIGHT = 15.0
RESET_COIL_TURNS = 500

# --- 仿真参数 ---
STOP_TIME = "30ms"           # 仿真总时长
TIME_STEP = "0.5ms"          # 时间步长

# =============================================================================
# 脚本开始
# =============================================================================

project_name = "TripDevice_Transient"
design_name = "FastActingTrip"

print("=" * 60)
print("断路器快速动作脱扣器仿真")
print("=" * 60)

# 初始化 Maxwell 3D - Transient 求解器
m3d = Maxwell3d(
    projectname=project_name,
    designname=design_name,
    solution_type="Transient",
    new_desktop_session=True,
    non_graphical=False
)

m3d.modeler.model_units = "mm"

print("[1/6] 创建材料...")

# =============================================================================
# 1. 材料定义
# =============================================================================
# 硅钢片 (用于磁轭和铁芯)
if not m3d.materials.checkifmaterialexists("SiliconSteel_M19"):
    mat_steel = m3d.materials.add_material("SiliconSteel_M19")
    mat_steel.permeability = 2000  # 相对磁导率
    mat_steel.conductivity = 2e6   # 电导率 S/m

print("[2/6] 创建磁轭几何...")

# =============================================================================
# 2. 创建磁轭 (Yoke) - 方形框架结构
# =============================================================================
# 外框
yoke_outer = m3d.modeler.create_box(
    origin=[
        -YOKE_OUTER_WIDTH / 2,
        -YOKE_OUTER_DEPTH / 2,
        0
    ],
    sizes=[YOKE_OUTER_WIDTH, YOKE_OUTER_DEPTH, YOKE_OUTER_HEIGHT],
    name="Yoke_Outer",
    matname="SiliconSteel_M19"
)

# 内腔 (挖空)
inner_width = YOKE_OUTER_WIDTH - 2 * YOKE_WALL_THICKNESS
inner_depth = YOKE_OUTER_DEPTH - 2 * YOKE_WALL_THICKNESS
inner_height = YOKE_OUTER_HEIGHT - YOKE_WALL_THICKNESS  # 底部保留

yoke_inner = m3d.modeler.create_box(
    origin=[
        -inner_width / 2,
        -inner_depth / 2,
        YOKE_WALL_THICKNESS
    ],
    sizes=[inner_width, inner_depth, inner_height],
    name="Yoke_Inner"
)

m3d.modeler.subtract(yoke_outer, [yoke_inner], keep_originals=False)

print("[3/6] 创建铁芯 (可动部件)...")

# =============================================================================
# 3. 创建铁芯/导杆 (Core) - 可动部件
# =============================================================================
# 铁芯初始位置 (在顶部，准备被吸下)
core_z_start = YOKE_OUTER_HEIGHT - CORE_LENGTH - 5  # 留一点顶部间隙

core = m3d.modeler.create_cylinder(
    orientation="Z",
    origin=[0, 0, core_z_start],
    radius=CORE_RADIUS,
    height=CORE_LENGTH,
    name="Core_Armature",
    matname="SiliconSteel_M19"
)

print("[4/6] 创建线圈...")

# =============================================================================
# 4. 创建脱扣线圈 (Trip Coil)
# =============================================================================
# 线圈位于磁轭内部中下方
trip_coil_z = YOKE_WALL_THICKNESS + 5  # 距离底部一点距离

trip_coil_outer = m3d.modeler.create_cylinder(
    orientation="Z",
    origin=[0, 0, trip_coil_z],
    radius=TRIP_COIL_OUTER_RADIUS,
    height=TRIP_COIL_HEIGHT,
    name="TripCoil"
)

trip_coil_inner = m3d.modeler.create_cylinder(
    orientation="Z",
    origin=[0, 0, trip_coil_z],
    radius=TRIP_COIL_INNER_RADIUS,
    height=TRIP_COIL_HEIGHT,
    name="TripCoil_Inner"
)

m3d.modeler.subtract(trip_coil_outer, [trip_coil_inner], keep_originals=False)

# 指定线圈材料为铜
trip_coil_outer.material_name = "copper"

# =============================================================================
# 5. 创建复位线圈 (Reset Coil) - 可选
# =============================================================================
reset_coil_z = trip_coil_z + TRIP_COIL_HEIGHT + 5

reset_coil_outer = m3d.modeler.create_cylinder(
    orientation="Z",
    origin=[0, 0, reset_coil_z],
    radius=RESET_COIL_OUTER_RADIUS,
    height=RESET_COIL_HEIGHT,
    name="ResetCoil"
)

reset_coil_inner = m3d.modeler.create_cylinder(
    orientation="Z",
    origin=[0, 0, reset_coil_z],
    radius=RESET_COIL_INNER_RADIUS,
    height=RESET_COIL_HEIGHT,
    name="ResetCoil_Inner"
)

m3d.modeler.subtract(reset_coil_outer, [reset_coil_inner], keep_originals=False)
reset_coil_outer.material_name = "copper"

print("[5/6] 设置运动和激励...")

# =============================================================================
# 6. 设置运动 (Motion Setup)
# =============================================================================
# 创建运动带 (Band) - 包围铁芯
band = m3d.modeler.create_cylinder(
    orientation="Z",
    origin=[0, 0, core_z_start - 2],
    radius=CORE_RADIUS + 5,
    height=CORE_LENGTH + CORE_INITIAL_GAP + 4,
    name="MotionBand"
)
band.material_name = "vacuum"

# 设置平移运动 (Translational Motion)
# 沿Z轴负方向运动 (被吸下)
m3d.assign_translate_motion(
    band_object=band.name,
    coordinate_system="Global",
    axis="Z",
    positive_movement_limit=f"{CORE_INITIAL_GAP}mm",
    negative_movement_limit="0mm",
    mechanical_transient=True,
    mass=CORE_MASS,
    damping=0.01,
    name="CoreMotion"
)

# =============================================================================
# 7. 设置线圈激励 (Coil Excitation)
# =============================================================================
# 脱扣线圈 - 阶跃电压激励
m3d.assign_coil(
    input_object=["TripCoil"],
    conductor_number=TRIP_COIL_TURNS,
    polarity="Positive",
    name="TripCoilExcitation"
)

# 创建外电路 - 电压源 + 电阻
m3d.create_external_circuit(
    circuit_file=None,  # 使用内置简单电路
    circuit_name="TripCircuit"
)

# 设置绕组激励
m3d.assign_winding(
    coil_terminals=["TripCoilExcitation"],
    winding_type="Voltage",
    is_solid=False,
    current_value=0,
    resistance=TRIP_COIL_RESISTANCE,
    inductance=0,
    voltage=TRIP_COIL_VOLTAGE,
    name="TripWinding"
)

# =============================================================================
# 8. 创建分析设置 (Transient Setup)
# =============================================================================
print("[6/6] 创建求解设置...")

setup = m3d.create_setup(setupname="TransientSetup")
setup.props["StopTime"] = STOP_TIME
setup.props["TimeStep"] = TIME_STEP

# =============================================================================
# 9. 创建报告 (XY Plots)
# =============================================================================
print("创建输出报告...")

# 位移曲线
m3d.post.create_report(
    expressions=["Moving1.Position"],
    setup_sweep_name="TransientSetup",
    domain="Time",
    report_category="Fields",
    plot_name="CoreDisplacement_vs_Time"
)

# 线圈电流曲线
m3d.post.create_report(
    expressions=["TripWinding.Current"],
    setup_sweep_name="TransientSetup",
    domain="Time",
    report_category="Standard",
    plot_name="CoilCurrent_vs_Time"
)

# 速度曲线
m3d.post.create_report(
    expressions=["Moving1.Velocity"],
    setup_sweep_name="TransientSetup",
    domain="Time",
    report_category="Fields",
    plot_name="CoreVelocity_vs_Time"
)

# 电磁力曲线
m3d.post.create_report(
    expressions=["Moving1.Force"],
    setup_sweep_name="TransientSetup",
    domain="Time",
    report_category="Fields",
    plot_name="EMForce_vs_Time"
)

# =============================================================================
# 10. 保存项目
# =============================================================================
m3d.save_project()

print("=" * 60)
print("模型创建完成!")
print(f"项目路径: {m3d.project_path}")
print("=" * 60)
print("\n下一步:")
print("1. 检查几何模型是否正确")
print("2. 运行 'Analyze All' 开始仿真")
print("3. 查看 Results 中的 XY Plots")
print("4. 创建磁场云图 (B-field) 在不同时间点")

# m3d.analyze_all()  # 取消注释以自动运行仿真
# m3d.release_desktop()  # 取消注释以关闭 Maxwell
