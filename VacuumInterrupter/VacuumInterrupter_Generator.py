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

Date: 2026-01-19
"""

import os
import sys
import re
import math


def _force_utf8_stdio():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")


_force_utf8_stdio()


# =============================================================================
# 0. 环境配置 (针对自定义安装路径)
# =============================================================================
# 如果提供了命令行参数 (例如 .bat 启动脚本路径)，则尝试从中提取 AEDT 路径
def _normalize_aedt_root(path):
    if not path:
        return None
    if os.path.isfile(os.path.join(path, "ansysedt.exe")):
        return path
    win64_path = os.path.join(path, "Win64")
    if os.path.isfile(os.path.join(win64_path, "ansysedt.exe")):
        return win64_path
    return path


if len(sys.argv) > 1:
    arg_path = sys.argv[1]
    ansys_path = None

    print(f"[INFO] 检测到输入参数: {arg_path}")

    if os.path.isfile(arg_path) and arg_path.lower().endswith(".bat"):
        try:
            with open(arg_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                # 寻找包含 ansysedt.exe 的路径
                match = re.search(
                    r'["\']?([a-zA-Z]:\\.*?\\v\d+\\Win64)\\ansysedt\.exe["\']?',
                    content,
                    re.IGNORECASE,
                )
                if match:
                    ansys_path = match.group(1)
                    print(f"  从脚本中提取 Ansys 路径: {ansys_path}")
        except Exception as e:
            print(f"  [警告] 读取 Bat 文件失败: {e}")

    elif os.path.isdir(arg_path):
        # 如果直接给了目录
        if os.path.exists(os.path.join(arg_path, "ansysedt.exe")):
            ansys_path = arg_path
        elif os.path.exists(os.path.join(arg_path, "Win64", "ansysedt.exe")):
            ansys_path = os.path.join(arg_path, "Win64")

    if ansys_path:
        ansys_path = _normalize_aedt_root(ansys_path)
    if ansys_path:
        # 设置环境变量，强制 PyAEDT 使用此路径
        # 假设是 2024 R2 (v242)
        os.environ["ANSYSEM_ROOT242"] = ansys_path
        os.environ["ANSYSEM_ROOT20242"] = ansys_path
        os.environ["AWP_ROOT242"] = ansys_path
        print(f"  设置环境变量 ANSYSEM_ROOT242 = {ansys_path}")

existing_root = os.environ.get("ANSYSEM_ROOT242")
normalized_root = _normalize_aedt_root(existing_root) if existing_root else None
if normalized_root and normalized_root != existing_root:
    os.environ["ANSYSEM_ROOT242"] = normalized_root
    os.environ["AWP_ROOT242"] = normalized_root
    print(f"  修正环境变量 ANSYSEM_ROOT242 = {normalized_root}")

from ansys.aedt.core import settings, Maxwell3d
from ansys.aedt.core.internal.aedt_versions import AedtVersions
# settings.use_grpc_api = True  # 2026 Best Practice (Disabled to fix AttributeError)

# =============================================================================
# 参数设置 - 参考知乎文章结构
# =============================================================================
# 单位: mm
# 建模方向: X轴 (静端在-X, 动端在+X)

# --- 瓷套 (Al2O3 陶瓷绝缘管) - TD-12/4000 规格 ---
CERAMIC_OUTER_RADIUS = 38.0  # 外半径 (主体外径Φ76mm)
CERAMIC_INNER_RADIUS_BASE = 27.1  # 基准内半径 (内径Φ54.2mm)
CERAMIC_LENGTH = 180.0  # 瓷套长度 (总长180mm)

# --- 端盖法兰 (不锈钢) ---
FLANGE_OUTER_RADIUS = 45.0  # 法兰外半径
FLANGE_THICKNESS = 12.0  # 法兰厚度
FLANGE_INNER_RADIUS_REAL = 20.0  # 真实中心孔半径 (导电杆穿孔)

# --- 触头 (CuCr 合金) - TD-12/4000: 内径Φ54.2mm ---
CONTACT_RADIUS = 27.0  # 触头半径 (直径54mm)
CONTACT_THICKNESS = 8.0  # 触头厚度

# --- 法兰孔径 (仿真修正) ---
FLANGE_INNER_RADIUS = max(FLANGE_INNER_RADIUS_REAL, CONTACT_RADIUS + 1.5)

# --- 屏蔽罩 (铜) - 桶状结构包围触头 ---
SHIELD_THICKNESS = 2.0
SHIELD_CLEARANCE = 1.0  # 触头与屏蔽罩内壁的径向间隙
SHIELD_INNER_RADIUS = CONTACT_RADIUS + SHIELD_CLEARANCE
SHIELD_OUTER_RADIUS = SHIELD_INNER_RADIUS + SHIELD_THICKNESS
SHIELD_LENGTH = 70.0  # 屏蔽罩长度

# --- 真空/瓷套间隙 ---
CERAMIC_CLEARANCE = 1.0  # 屏蔽罩外壁到瓷套内壁的间隙
CERAMIC_INNER_RADIUS = max(
    CERAMIC_INNER_RADIUS_BASE, SHIELD_OUTER_RADIUS + CERAMIC_CLEARANCE
)

# --- 导电杆 (铜) - TD-12/4000: Φ36mm ---
ROD_RADIUS = 18.0  # 导电杆半径 (直径36mm)
STATIC_ROD_LENGTH = 40.0  # 静端导电杆长度
MOVING_ROD_LENGTH = 120.0  # 动端导电杆长度 (伸出到 Region 边界)

# --- 触头开距 - TD-12/4000: 9±1mm ---
CONTACT_GAP = 9.0  # 触头开距

# --- 运动参数 ---
CONTACT_GAP_MAX = 10.0  # 最大开距
MOTION_TIME = 0.015  # 仿真时间 15ms
OPEN_DIRECTION = "negative"  # "positive" 表示开闸向 +X 运动
EXCITATION_MODE = "face_current"  # "face_current" 或 "current_density"

# --- 电流参数 ---
RATED_CURRENT = 4000
PEAK_CURRENT = RATED_CURRENT * 1.414
FREQUENCY = 50


def _pick_first_matching(values, keywords):
    if not values:
        return None
    for keyword in keywords:
        keyword_lower = keyword.lower()
        for value in values:
            if keyword_lower in value.lower():
                return value
    return values[0]


def _select_report_quantity(
    post, setup_name, report_category, display_type, preferred_keywords
):
    try:
        categories = post.available_quantities_categories(
            report_category=report_category,
            display_type=display_type,
            solution=setup_name,
        )
    except Exception:
        categories = []
    if not categories:
        categories = [None]
    for category in categories:
        try:
            quantities = post.available_report_quantities(
                report_category=report_category,
                display_type=display_type,
                solution=setup_name,
                quantities_category=category,
            )
        except Exception:
            quantities = []
        selected = _pick_first_matching(quantities, preferred_keywords)
        if selected:
            return selected
    return None


def _pick_report_category(post, preferred_categories):
    try:
        available = post.available_report_types
    except Exception:
        available = []
    for category in preferred_categories:
        if category in available:
            return category
    return available[0] if available else None


def _safe_setup_sweep_name(m3d, setup):
    try:
        if getattr(m3d, "nominal_adaptive", None):
            return m3d.nominal_adaptive
    except Exception:
        pass
    return setup.name if setup else None


def _reset_design(m3d, name, solution):
    try:
        if name not in m3d.design_list:
            m3d.insert_design(name, solution_type=solution)
            print(f"  [提示] 创建新设计: {name}")
        m3d.set_active_design(name)
        print(f"  [提示] 复用现有设计: {name}")

        if m3d.solution_type != solution:
            m3d.oproject.DeleteDesign(name)
            m3d.insert_design(name, solution_type=solution)
            m3d.set_active_design(name)
            print(f"  [提示] 重建设计为 {solution}: {name}")
    except Exception as e:
        print(f"  [警告] 设计切换失败: {e}")

    try:
        boundaries = list(m3d.boundaries)
        for boundary in boundaries:
            try:
                boundary.delete()
            except Exception:
                pass
        if boundaries:
            print(f"  [提示] 清理旧边界/激励: {len(boundaries)}")
    except Exception as e:
        print(f"  [警告] 清理旧边界失败: {e}")

    try:
        existing_objects = list(m3d.modeler.object_names)
        if existing_objects:
            m3d.modeler.delete(existing_objects)
            print(f"  [提示] 清理旧模型对象: {len(existing_objects)}")
    except Exception as e:
        print(f"  [警告] 清理旧模型失败: {e}")

    try:
        for plot_name in list(m3d.post.field_plot_names):
            m3d.post.delete_field_plot(plot_name)
        if m3d.post.plots:
            m3d.post.delete_report()
    except Exception as e:
        print(f"  [警告] 清理旧结果失败: {e}")


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
MOVING_CONTACT_X = CONTACT_GAP / 2  # 动触头左端面

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
solution_type = "Transient"

project_dir = r"D:\AnsysProducts\results"
project_file = os.path.join(project_dir, f"{project_name}.aedt")
project_lock = project_file + ".lock"
for path in [project_lock, project_file]:
    if os.path.exists(path):
        try:
            os.remove(path)
            print(f"  [提示] 已删除旧项目文件: {path}")
        except Exception as e:
            print(f"  [警告] 无法删除项目文件 {path}: {e}")

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

aedt_versions = AedtVersions()
installed_versions = aedt_versions.installed_versions
if not installed_versions:
    print(
        "  [ERROR] No AEDT installation detected. Set ANSYSEM_ROOTxxx/AWP_ROOTxxx or install AEDT."
    )
    raise SystemExit(1)

aedt_version = "2024.2"
if aedt_version not in installed_versions:
    fallback_version = aedt_versions.current_version or aedt_versions.latest_version
    if fallback_version:
        print(
            f"  [INFO] Requested AEDT {aedt_version} not found. Using {fallback_version}."
        )
        aedt_version = fallback_version
    else:
        print(
            "  [ERROR] No usable AEDT version detected. Check ANSYSEM_ROOTxxx/AWP_ROOTxxx."
        )
        raise SystemExit(1)


def _create_maxwell(desktop_new):
    return Maxwell3d(
        project=project_name,
        design=design_name,
        solution_type=solution_type,
        version=aedt_version,
        new_desktop=desktop_new,
        non_graphical=False,
    )


def _init_maxwell_with_fallback():
    try:
        return _create_maxwell(True)
    except Exception as e:
        print(f"  [错误] {e}")
        raise SystemExit(1)


m3d = _init_maxwell_with_fallback()

# 避免重复叠加几何，复用同名设计并清理旧模型
_reset_design(m3d, design_name, solution_type)

if not getattr(m3d, "_odesign", None):
    print(
        "  [ERROR] AEDT not detected. Install AEDT and set ANSYSEM_ROOTxxx/AWP_ROOTxxx or adjust 'version'."
    )
    raise SystemExit(1)

m3d.modeler.model_units = "mm"
print(f"  [成功] 项目: {m3d.project_name}")

# =============================================================================
# 2. 材料定义
# =============================================================================
print("\n[2/10] 创建材料...")

if not m3d.materials.exists_material("Al2O3_Ceramic"):
    mat = m3d.materials.add_material("Al2O3_Ceramic")
    mat.permittivity = 9.4
    mat.conductivity = 0

if not m3d.materials.exists_material("CuCr_Alloy"):
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
    material="Al2O3_Ceramic",
)

ceramic_void = m3d.modeler.create_cylinder(
    orientation="X",
    origin=[CERAMIC_X_START, 0, 0],
    radius=CERAMIC_INNER_RADIUS,
    height=CERAMIC_LENGTH,
    name="Ceramic_Void_Temp",
)
m3d.modeler.subtract(ceramic_outer, [ceramic_void], keep_originals=False)
print(f"  瓷套: 外径{CERAMIC_OUTER_RADIUS * 2}mm, 长度{CERAMIC_LENGTH}mm")


# =============================================================================
# 4. AMF 触头几何生成函数 (杯状纵磁结构)
# =============================================================================
def create_amf_contact(m3d, origin, is_static=True):
    """
    创建一个杯状纵磁(AMF)触头组件。
    包含：触头杯(Cup)、斜槽(Slots)、触头片(Plate)。

    参数:
    - origin: [x, y, z] 触头组件的基准点（杯底与导电杆连接处）
    - is_static: True表示静触头(向+X延伸), False表示动触头(向-X延伸)
    """

    # 局部参数定义
    cup_radius = CONTACT_RADIUS
    cup_height = CONTACT_THICKNESS * 1.5  # 杯深略大于原厚度
    wall_thickness = 4.0  # 杯壁厚度
    base_thickness = 4.0  # 杯底厚度
    plate_thickness = 3.0  # 触头片厚度

    slot_count = 6  # 开槽数量
    slot_width = 3.0  # 槽宽
    slot_angle = 25  # 开槽倾角 (度)
    slot_pitch = cup_height * 2.0  # 螺旋节距(近似), 值越大螺旋越缓

    center_hole_radius = max(2.5, cup_radius * 0.08)  # 触头片中心孔
    groove_count = 6  # 触头片径向槽数量
    groove_width = 2.0  # 径向槽宽
    groove_length = cup_radius * 0.85  # 径向槽长度

    prefix = "Static" if is_static else "Moving"
    # 方向系数：静触头沿+X生长，动触头沿-X生长
    direction = 1.0 if is_static else -1.0

    # 1. 创建触头杯 (实心圆柱)
    cup_name = f"{prefix}_Cup"
    cup = m3d.modeler.create_cylinder(
        orientation="X",
        origin=origin,
        radius=cup_radius,
        height=cup_height * direction,
        name=cup_name,
        material="copper",
    )

    # 2. 挖空内部 (形成杯状)
    cup_void_name = f"{prefix}_Cup_Void"
    void_height = cup_height - base_thickness
    void_origin = [origin[0] + base_thickness * direction, origin[1], origin[2]]

    cup_void = m3d.modeler.create_cylinder(
        orientation="X",
        origin=void_origin,
        radius=cup_radius - wall_thickness,
        height=void_height * direction,
        name=cup_void_name,
    )
    m3d.modeler.subtract(cup_name, [cup_void_name], keep_originals=False)

    # 3. 切割斜槽 (关键：产生圆周电流)
    # 优先尝试螺旋槽，不支持时退化为斜槽
    for i in range(slot_count):
        slot_cutter_name = f"{prefix}_Slot_{i}"

        helix_supported = hasattr(m3d.modeler, "create_helix")
        helix_done = False
        if helix_supported:
            try:
                helix_path = m3d.modeler.create_helix(
                    origin=[origin[0] + base_thickness * direction, 0, 0],
                    radius=cup_radius - wall_thickness * 0.6,
                    pitch=slot_pitch * direction,
                    height=(cup_height - base_thickness) * direction,
                    name=f"{slot_cutter_name}_Path",
                )
                profile = m3d.modeler.create_rectangle(
                    position=[origin[0] + base_thickness * direction, 0, 0],
                    dimension_list=[slot_width, wall_thickness * 1.2],
                    name=f"{slot_cutter_name}_Profile",
                    material="vacuum",
                    plane="YZ",
                )
                sweep = m3d.modeler.sweep_along_path(
                    profile, helix_path, name=slot_cutter_name
                )
                if sweep:
                    helix_done = True
            except Exception:
                helix_done = False

        if not helix_done:
            # 退化为斜槽：通过倾斜刀具形成轴向倾角
            cutter = m3d.modeler.create_box(
                origin=[origin[0], -cup_radius * 1.2, -slot_width / 2],
                sizes=[cup_height * direction * 1.2, cup_radius * 2.4, slot_width],
                name=slot_cutter_name,
            )

            # 绕Y轴倾斜形成轴向倾角
            m3d.modeler.rotate(slot_cutter_name, axis="Y", angle=slot_angle)

            # 绕X轴分布 (分布在圆周上)
            m3d.modeler.rotate(
                slot_cutter_name,
                axis="X",
                angle=i * (360.0 / slot_count),
            )

        # 执行减法
        m3d.modeler.subtract(cup_name, [slot_cutter_name], keep_originals=False)

    # 4. 创建触头片 (CuCr合金，焊接在杯口)
    plate_name = f"{prefix}_Contact_Plate"
    plate_origin = [origin[0] + cup_height * direction, origin[1], origin[2]]

    plate = m3d.modeler.create_cylinder(
        orientation="X",
        origin=plate_origin,
        radius=cup_radius,
        height=plate_thickness * direction,
        name=plate_name,
        material="CuCr_Alloy",
    )

    # 4.1 触头片中心孔
    hole_name = f"{prefix}_Plate_Center_Hole"
    hole = m3d.modeler.create_cylinder(
        orientation="X",
        origin=plate_origin,
        radius=center_hole_radius,
        height=plate_thickness * direction,
        name=hole_name,
    )
    m3d.modeler.subtract(plate_name, [hole_name], keep_originals=False)

    # 4.2 触头片径向槽
    for i in range(groove_count):
        groove_name = f"{prefix}_Plate_Groove_{i}"
        groove = m3d.modeler.create_box(
            origin=[plate_origin[0], 0, -groove_width / 2],
            sizes=[plate_thickness * direction * 1.2, groove_length, groove_width],
            name=groove_name,
        )
        m3d.modeler.rotate(groove_name, axis="X", angle=i * (360.0 / groove_count))
        m3d.modeler.subtract(plate_name, [groove_name], keep_originals=False)

    # 返回最后的接触面X坐标，用于定位下一级
    final_x = origin[0] + (cup_height + plate_thickness) * direction
    return final_x, plate_name, cup_name


# =============================================================================
# 5. 静端组件生成
# =============================================================================
print("\n[4/10] 创建静端组件 (AMF)...")

# 静端法兰盘
static_flange = m3d.modeler.create_cylinder(
    orientation="X",
    origin=[STATIC_FLANGE_X, 0, 0],
    radius=FLANGE_OUTER_RADIUS,
    height=FLANGE_THICKNESS,
    name="Static_Flange",
    material="steel_stainless",
)
static_flange_void = m3d.modeler.create_cylinder(
    orientation="X",
    origin=[STATIC_FLANGE_X, 0, 0],
    radius=FLANGE_INNER_RADIUS,
    height=FLANGE_THICKNESS,
    name="Static_Flange_Void_Temp",
)
m3d.modeler.subtract(static_flange, [static_flange_void], keep_originals=False)

# 静端导电杆 (先画导电杆，直至触头杯底)
# 修正：导电杆终点应为触头杯底位置
# 假设触头总厚度(含杯+片) 约为 CONTACT_THICKNESS * 2 左右
# 我们反推基准点: 静触头表面就在 STATIC_CONTACT_X + CONTACT_THICKNESS
# 此处简化：让 AMF 结构向右(+X)生长，直至接触面

# 计算AMF起始点X (杯底)
# 目标接触面: STATIC_CONTACT_X
# AMF总长: cup_h + plate_h = 12 + 3 = 15mm (估算)
amf_total_len = (CONTACT_THICKNESS * 1.5) + 3.0
amf_start_x = STATIC_CONTACT_X - amf_total_len

# 也就是现在的静触头表面在: STATIC_CONTACT_X
# 我们重新定义:
#   STATIC_CONTACT_FACE_X = -CONTACT_GAP / 2
#   AMF_STATIC_ORIGIN = STATIC_CONTACT_FACE_X - amf_total_len
STATIC_CONTACT_FACE_X = -CONTACT_GAP / 2
amf_static_origin = [STATIC_CONTACT_FACE_X - amf_total_len, 0, 0]

# 调用函数生成静触头
_, static_plate, static_cup = create_amf_contact(m3d, amf_static_origin, is_static=True)

# 静端导电杆 (连接法兰与杯底)
static_rod_end = amf_static_origin[0]
static_rod = m3d.modeler.create_cylinder(
    orientation="X",
    origin=[STATIC_ROD_X_START, 0, 0],
    radius=ROD_RADIUS,
    height=static_rod_end - STATIC_ROD_X_START,
    name="Static_Rod",
    material="copper",
)

# 组合导体
m3d.modeler.unite(["Static_Rod", static_cup, static_plate])
static_conductor_name = "Static_Rod"  # 合并后名称通常为第一个
print(f"  静触头(AMF)生成完毕")


# =============================================================================
# 6. 动端组件生成
# =============================================================================
print("\n[5/10] 创建动端组件 (AMF)...")

# 动端法兰盘
moving_flange = m3d.modeler.create_cylinder(
    orientation="X",
    origin=[MOVING_FLANGE_X, 0, 0],
    radius=FLANGE_OUTER_RADIUS,
    height=FLANGE_THICKNESS,
    name="Moving_Flange",
    material="steel_stainless",
)
moving_flange_void = m3d.modeler.create_cylinder(
    orientation="X",
    origin=[MOVING_FLANGE_X, 0, 0],
    radius=FLANGE_INNER_RADIUS,
    height=FLANGE_THICKNESS,
    name="Moving_Flange_Void_Temp",
)
m3d.modeler.subtract(moving_flange, [moving_flange_void], keep_originals=False)

# 动触头 (AMF)
# 动触头接触面: MOVING_CONTACT_X = CONTACT_GAP / 2
# 动触头向左(-X)生长，杯底在右侧
# AMF Origin应在: MOVING_CONTACT_X + amf_total_len
MOVING_CONTACT_FACE_X = CONTACT_GAP / 2
amf_moving_origin = [MOVING_CONTACT_FACE_X + amf_total_len, 0, 0]

# 调用函数生成动触头 (is_static=False)
_, moving_plate, moving_cup = create_amf_contact(
    m3d, amf_moving_origin, is_static=False
)

# 动端导电杆 (连接杯底与法兰外)
moving_rod_start = amf_moving_origin[0]
moving_rod = m3d.modeler.create_cylinder(
    orientation="X",
    origin=[moving_rod_start, 0, 0],
    radius=ROD_RADIUS,
    height=MOVING_ROD_X_END - moving_rod_start,
    name="Moving_Rod",
    material="copper",
)

# 组合导体
m3d.modeler.unite(["Moving_Rod", moving_cup, moving_plate])
moving_conductor_name = "Moving_Rod"
print(f"  动触头(AMF)生成完毕")

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
    material="copper",
)

shield_void = m3d.modeler.create_cylinder(
    orientation="X",
    origin=[SHIELD_X_START, 0, 0],
    radius=SHIELD_INNER_RADIUS,
    height=SHIELD_LENGTH,
    name="Shield_Void_Temp",
)
m3d.modeler.subtract(shield_outer, [shield_void], keep_originals=False)
print(f"  屏蔽罩: 外径{SHIELD_OUTER_RADIUS * 2}mm, 长度{SHIELD_LENGTH}mm")

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
    material="vacuum",
)
all_solid_objects = [
    obj
    for obj in m3d.modeler.object_names
    if obj != "Vacuum_Region" and "Region" not in obj
]
try:
    m3d.modeler.subtract("Vacuum_Region", all_solid_objects, keep_originals=True)
    print(f"  [成功] 真空域已挖空 {len(all_solid_objects)} 个实体")
except Exception as e:
    print(f"  [警告] 真空域挖空失败: {e}")
print("  真空区域创建完成")

# =============================================================================
# 8. Region (求解域)
# =============================================================================
print("\n[8/10] 创建求解域...")

try:
    if "Region" in m3d.modeler.object_names:
        print("  Region 已存在，跳过创建")
    else:
        region = m3d.modeler.create_air_region(
            x_pos=0,
            x_neg=0,
            y_pos=20,
            y_neg=20,
            z_pos=20,
            z_neg=20,
            is_percentage=False,
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
band_clearance = 2.0
if OPEN_DIRECTION == "positive":
    band_x_start = MOVING_CONTACT_X - band_clearance
    band_x_end = MOVING_ROD_X_END + CONTACT_GAP_MAX + band_clearance
else:
    band_x_start = MOVING_CONTACT_X - CONTACT_GAP_MAX - band_clearance
    band_x_end = MOVING_ROD_X_END

# 确保不与静触头重叠
band_x_start = max(band_x_start, STATIC_CONTACT_X + CONTACT_THICKNESS + band_clearance)

band_length = band_x_end - band_x_start
band_radius = CONTACT_RADIUS + 0.5  # 略大于触头，避免与屏蔽罩干涉

motion_band = m3d.modeler.create_cylinder(
    orientation="X",
    origin=[band_x_start, 0, 0],
    radius=band_radius,
    height=band_length,
    name="Motion_Band",
    material="vacuum",
)

# 避免 Motion_Band 与 Vacuum_Region 发生几何重叠
try:
    m3d.modeler.subtract("Vacuum_Region", ["Motion_Band"], keep_originals=True)
except Exception as e:
    print(f"  [警告] Vacuum_Region 减去 Motion_Band 失败: {e}")

print(f"  X范围: {band_x_start:.1f}mm ~ {band_x_end:.1f}mm")
print(f"  静触头右端面: X={STATIC_CONTACT_X + CONTACT_THICKNESS:.1f}mm")
print(f"  Band 不与静触头重叠: CHECKED")

# =============================================================================
# 9.5 创建速度时程曲线 Dataset
# =============================================================================
print("\n[9.5/10] 创建速度时程曲线 Dataset...")

# 时间-速度数据点 (指数衰减模型)
velocity_data_x = [0.0, 0.001, 0.002, 0.003, 0.005, 0.008, 0.010, 0.015]
velocity_data_y = [1.2, 1.15, 1.0, 0.9, 0.75, 0.65, 0.60, 0.60]

dataset_name = "Velocity_Profile"
try:
    if dataset_name not in m3d.project_datasets:
        m3d.create_dataset1d_design(
            dataset_name,
            velocity_data_x,
            velocity_data_y,
            x_unit="s",
            y_unit="m_per_sec",
        )
        print(f"  [成功] 创建 Dataset: {dataset_name}")
    else:
        print(f"  [信息] Dataset {dataset_name} 已存在")
except Exception as e:
    print(f"  [警告] 创建 Dataset 失败: {e}")

# =============================================================================
# 9.8 Mesh - 最细划分
# =============================================================================
print("  设置最细网格...")
try:
    m3d.mesh.delete_mesh_operations()
    all_objects = list(m3d.modeler.object_names)
    if all_objects:
        m3d.mesh.assign_length_mesh(
            all_objects,
            inside_selection=True,
            maximum_length=0.2,
            maximum_elements=200000,
            name="FineMesh",
        )
        print("  [成功] 已设置最细网格")
    else:
        print("  [警告] 未找到对象，跳过网格设置")
except Exception as e:
    print(f"  [警告] 网格设置失败: {e}")

# =============================================================================
# 10. 分析设置 (Motion & Setup)
# =============================================================================
print("\n[10/10] 创建分析设置与激励...")

# 10.1 Motion Setup
print("  配置运动设置...")
try:
    # 定义运动部件
    moving_parts = ["Moving_Contact", "Moving_Rod"]

    # 分配运动带 (Motion Band)
    # PyAEDT method to assign translation motion
    if OPEN_DIRECTION == "positive":
        positive_limit = CONTACT_GAP_MAX
        negative_limit = 0
        velocity_profile = f"pwl({dataset_name}, Time)"
    else:
        positive_limit = 0
        negative_limit = CONTACT_GAP_MAX
        velocity_profile = f"-pwl({dataset_name}, Time)"

    motion_setup = m3d.assign_translate_motion(
        band_object="Motion_Band",
        moving_objects=moving_parts,
        velocity_profile=velocity_profile,
        axis="X",
        mechanic_mass=1.0,  # 这里的质量不影响速度驱动的运动，给个默认值
        positive_limit=positive_limit,
        negative_limit=negative_limit,
        motion_name="MovingMotion",
    )
    print("  [成功] 设置运动 (Translational)")
except Exception as e:
    print(f"  [警告] 设置运动失败: {e}")

# 10.2 Excitations
print("  配置电流激励...")
try:
    # 这里的电流是正弦波: 4000*1.414 * sin(2*pi*50*Time)
    current_expression = f"{PEAK_CURRENT:.2f}A * sin(2 * pi * {FREQUENCY} * Time)"

    if solution_type == "Transient":
        if (
            static_conductor_name in m3d.modeler.object_names
            and moving_conductor_name in m3d.modeler.object_names
        ):
            m3d.assign_current(
                assignment=[static_conductor_name],
                amplitude=current_expression,
                solid=True,
                name="Phase_A_In",
            )
            m3d.assign_current(
                assignment=[moving_conductor_name],
                amplitude=current_expression,
                solid=True,
                swap_direction=True,
                name="Phase_A_Out",
            )
            print(f"  [成功] 设置电流激励 (Solid): {current_expression}")
        else:
            print("  [警告] 未找到导体对象，跳过电流激励")

    elif EXCITATION_MODE == "current_density":
        rod_area_m2 = math.pi * (ROD_RADIUS / 1000.0) ** 2
        current_density_x = f"({current_expression}) / ({rod_area_m2})"
        if static_conductor_name in m3d.modeler.object_names:
            m3d.assign_current_density(
                assignment=[static_conductor_name],
                current_density_x=current_density_x,
                current_density_y="0",
                current_density_z="0",
                current_density_name="Phase_A_J",
            )
            print(f"  [成功] 设置电流密度激励: Jx={current_density_x}")
        else:
            print("  [警告] 未找到静端导体，跳过电流激励")
    else:
        static_in_face = m3d.modeler.get_faceid_from_position(
            [STATIC_ROD_X_START, 0, 0], obj_name=static_conductor_name
        )
        moving_out_face = m3d.modeler.get_faceid_from_position(
            [MOVING_ROD_X_END, 0, 0], obj_name=moving_conductor_name
        )

        def find_face_by_x(obj_name, target_x, tol=0.2):
            faces = m3d.modeler.get_object_faces(obj_name)
            best_face = None
            best_dx = None
            for fid in faces:
                center = m3d.modeler.get_face_center(fid)
                if (
                    not center
                    or not isinstance(center, (list, tuple))
                    or len(center) < 3
                ):
                    continue
                dx = abs(center[0] - target_x)
                if dx < tol:
                    return fid
                if best_dx is None or dx < best_dx:
                    best_dx = dx
                    best_face = fid
            return best_face

        if not static_in_face:
            static_in_face = find_face_by_x(static_conductor_name, STATIC_ROD_X_START)
        if not moving_out_face:
            moving_out_face = find_face_by_x(moving_conductor_name, MOVING_ROD_X_END)

        if static_in_face and moving_out_face:
            m3d.assign_current(
                assignment=[static_in_face],
                amplitude=current_expression,
                solid=False,
                name="Phase_A_In",
            )
            m3d.assign_current(
                assignment=[moving_out_face],
                amplitude=current_expression,
                solid=False,
                swap_direction=True,
                name="Phase_A_Out",
            )
            print(f"  [成功] 设置电流激励 (Face In/Out): {current_expression}")
        else:
            print("  [警告] 未找到合适的端面，跳过电流激励")

except Exception as e:
    print(f"  [警告] 设置激励失败: {e}")

# 10.3 Analysis Setup
print("  创建求解 Setup...")
try:
    if "Transient_Analysis" in m3d.setup_names:
        setup = m3d.get_setup("Transient_Analysis")
    else:
        setup = m3d.create_setup(name="Transient_Analysis")

    setup.props["StopTime"] = f"{MOTION_TIME}s"
    setup.props["TimeStep"] = "0.0005s"
    # 确保保存场数据
    setup.props["SaveFieldsType"] = "Every step"
    setup.update()
    print(f"  仿真时间: {MOTION_TIME * 1000:.0f}ms,步长 0.5ms")
except Exception as e:
    print(f"  [警告] Setup 设置失败: {e}")

# 10.4 求解
print("  启动求解...")
try:
    success = m3d.analyze(setup.name)
    solved_ok = bool(success)
    if solved_ok:
        print("  [成功] 求解完成")
    else:
        print("  [错误] 求解返回失败状态")
    try:
        try:
            messages = m3d.odesktop.GetMessages(project_name, m3d.design_name, 2)
        except Exception:
            messages = m3d.odesktop.GetMessages("", "", 2)
        if messages:
            print("  [信息] Message Manager 错误:")
            for msg in messages:
                print(f"    {msg}")
    except Exception as e:
        print(f"  [警告] 无法读取 Message Manager: {e}")
except Exception as e:
    print(f"  [错误] 求解失败: {e}")
    solved_ok = False

# 10.5 Results & Field Overlays
print("  创建 Results/Field Overlays 输出...")
try:
    if not solved_ok:
        print("  [提示] 求解失败，跳过 Results/Field Overlays 创建")
        raise RuntimeError("Solve failed")
    export_dir = os.path.join(os.getcwd(), "VacuumInterrupter", "post")
    os.makedirs(export_dir, exist_ok=True)

    setup_sweep = _safe_setup_sweep_name(m3d, setup)
    report_category = _pick_report_category(
        m3d.post, ["Transient", "Fields", "Standard"]
    )
    display_type = "Rectangular Plot"
    report_targets = [
        ("Time_Current", ["Current", "InputCurrent", "WindingCurrent"]),
        ("Time_Force", ["Force", "LorentzForce"]),
        ("Time_Torque", ["Torque"]),
        ("Time_Loss", ["Loss", "EddyCurrentLoss", "TotalLoss", "OhmicLoss"]),
    ]
    created_reports = 0
    used_quantities = set()
    if report_category and setup_sweep:
        for report_name, keywords in report_targets:
            report_quantity = _select_report_quantity(
                m3d.post,
                setup_sweep,
                report_category,
                display_type,
                keywords,
            )
            if not report_quantity or report_quantity in used_quantities:
                continue
            report = m3d.post.create_report(
                expressions=report_quantity,
                setup_sweep_name=setup_sweep,
                domain="Time",
                primary_sweep_variable="Time",
                variations={"Time": ["All"]},
                report_category=report_category,
                plot_name=f"{report_name}_{report_quantity}",
            )
            if report:
                created_reports += 1
                used_quantities.add(report_quantity)
                print(f"  [成功] Results 已创建: {report.plot_name}")
    if not created_reports:
        print("  [警告] 未找到可用的 Results 报表量")

    field_category = _pick_report_category(
        m3d.post, ["Fields", "DC R/L Fields", "AC R/L Fields"]
    )
    field_quantity = None
    if field_category and setup_sweep:
        field_quantity = _select_report_quantity(
            m3d.post,
            setup_sweep,
            field_category,
            display_type,
            ["Mag_B", "B", "Mag_H", "H", "J", "E"],
        )
    field_target = None
    if "Vacuum_Region" in m3d.modeler.object_names:
        field_target = "Vacuum_Region"
    elif "Region" in m3d.modeler.object_names:
        field_target = "Region"

    if field_quantity and field_target:
        plot = m3d.post.create_fieldplot_surface(
            field_target,
            field_quantity,
            setup=setup_sweep,
            intrinsics={"Time": f"{MOTION_TIME}s"},
            plot_name=f"Field_{field_quantity}_{field_target}",
        )
        if plot:
            m3d.post.export_field_plot(
                plot.name, export_dir, file_name=plot.name, file_format="aedtplt"
            )
            m3d.post.export_field_jpg(
                os.path.join(export_dir, f"{plot.name}.jpg"),
                plot.name,
                plot.plot_folder,
                orientation="isometric",
                width=1920,
                height=1080,
                display_wireframe=False,
                show_axis=True,
                show_grid=True,
                show_ruler=False,
                show_region=False,
            )
            print(f"  [成功] Field Overlays 已创建: {plot.name}")

        cut_plane = m3d.modeler.create_plane(
            name="Field_Cutplane_Y",
            plane_base_x="0mm",
            plane_base_y="0mm",
            plane_base_z="0mm",
            plane_normal_x="0mm",
            plane_normal_y="1mm",
            plane_normal_z="0mm",
        )
        cut_plot = m3d.post.create_fieldplot_cutplane(
            [cut_plane.name],
            field_quantity,
            setup=setup_sweep,
            intrinsics={"Time": f"{MOTION_TIME}s"},
            plot_name=f"Field_{field_quantity}_Cutplane",
        )
        if cut_plot:
            m3d.post.export_field_plot(
                cut_plot.name,
                export_dir,
                file_name=cut_plot.name,
                file_format="aedtplt",
            )
            m3d.post.export_field_jpg(
                os.path.join(export_dir, f"{cut_plot.name}.jpg"),
                cut_plot.name,
                cut_plot.plot_folder,
                orientation="isometric",
                width=1920,
                height=1080,
                display_wireframe=False,
                show_axis=True,
                show_grid=True,
                show_ruler=False,
                show_region=False,
            )
            print(f"  [成功] Field Overlays 已创建: {cut_plot.name}")
    else:
        print("  [警告] Field Overlays 创建失败")
except Exception as e:
    print(f"  [警告] Results/Field Overlays 输出失败: {e}")

# 10.6 Post-Processing Exports
print("  导出后处理数据...")
try:
    export_dir = os.path.join(os.getcwd(), "VacuumInterrupter", "post")
    os.makedirs(export_dir, exist_ok=True)

    # 以输入时程作为开闸运动后处理导出
    dt = 0.0005
    steps = int(MOTION_TIME / dt) + 1
    times = [i * dt for i in range(steps)]

    # 速度插值
    def interp_velocity(t):
        if t <= velocity_data_x[0]:
            return velocity_data_y[0]
        if t >= velocity_data_x[-1]:
            return velocity_data_y[-1]
        for i in range(len(velocity_data_x) - 1):
            t0 = velocity_data_x[i]
            t1 = velocity_data_x[i + 1]
            if t0 <= t <= t1:
                v0 = velocity_data_y[i]
                v1 = velocity_data_y[i + 1]
                if t1 == t0:
                    return v0
                return v0 + (v1 - v0) * (t - t0) / (t1 - t0)
        return velocity_data_y[-1]

    sign = 1.0 if OPEN_DIRECTION == "positive" else -1.0
    velocities = [sign * interp_velocity(t) for t in times]

    # 位置积分
    positions = [0.0]
    for i in range(1, len(times)):
        positions.append(positions[-1] + 0.5 * (velocities[i - 1] + velocities[i]) * dt)

    # 电流波形
    currents = [PEAK_CURRENT * math.sin(2.0 * math.pi * FREQUENCY * t) for t in times]

    motion_csv = os.path.join(export_dir, "motion_profile.csv")
    with open(motion_csv, "w", encoding="utf-8") as f:
        f.write("Time(s),Velocity(m/s),Position(m)\n")
        for t, v, p in zip(times, velocities, positions):
            f.write(f"{t},{v},{p}\n")
    print(f"  [成功] 导出运动时程 -> {motion_csv}")

    current_csv = os.path.join(export_dir, "current_waveform.csv")
    with open(current_csv, "w", encoding="utf-8") as f:
        f.write("Time(s),Current(A)\n")
        for t, i in zip(times, currents):
            f.write(f"{t},{i}\n")
    print(f"  [成功] 导出电流时程 -> {current_csv}")
except Exception as e:
    print(f"  [警告] 后处理导出失败: {e}")

# =============================================================================
# 保存
# =============================================================================
print("\n" + "=" * 60)
m3d.save_project()
print(f"项目保存: {m3d.project_path}")

print("\n" + "=" * 60)
print("模型创建与设置完成!")
print("=" * 60)
print("提示: 如果 Dataset 或 运动设置有误，请按以下步骤手动检查:")
print(f"1. Project > Datasets: 检查 '{dataset_name}' 是否存在")
print("2. Model > Motion Setup: 检查是否为 Translational, 速度是否引用 Dataset")
print("3. Excitations: 检查是否有 Current 激励")
