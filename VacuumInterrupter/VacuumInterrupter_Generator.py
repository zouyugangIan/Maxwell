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
import glob
import subprocess


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

# --- AMF 触头结构参数 (最佳实践：多槽、均匀分布、保留足够筋宽) ---
AMF_CUP_HEIGHT = CONTACT_THICKNESS * 1.4  # 杯深
AMF_WALL_THICKNESS = 3.0  # 杯壁厚度
AMF_BASE_THICKNESS = 3.0  # 杯底厚度
AMF_PLATE_THICKNESS = 4.0  # 触头片厚度
AMF_SLOT_COUNT = 8  # 杯壁斜槽数量
AMF_SLOT_WIDTH = 2.5  # 槽宽
AMF_SLOT_ANGLE = 30  # 槽倾角(度)
AMF_SLOT_PITCH = AMF_CUP_HEIGHT * 2.2  # 螺旋节距(近似)
AMF_PLATE_HOLE_RATIO = 0.10  # 触头片中心孔比例
AMF_GROOVE_COUNT = 8  # 触头片径向槽数量
AMF_GROOVE_WIDTH = 1.5  # 径向槽宽
AMF_GROOVE_LENGTH_RATIO = 0.80  # 径向槽长度比例

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

# --- 触头开距 - 参考 Eaton: 8.5±0.5mm ---
CONTACT_GAP = 8.5  # 触头开距

# --- 运动参数 ---
CONTACT_GAP_MAX = 9.0  # 最大开距
GAP_TRAVEL = max(0.0, CONTACT_GAP_MAX - CONTACT_GAP)  # 运动行程
MOTION_TIME = 0.015  # 仿真时间 15ms
OPEN_DIRECTION = "positive"  # "positive" 表示开闸向 +X 运动
ARC_ENABLE = True
ARC_RADIUS = CONTACT_RADIUS * 0.6
ARC_CONDUCTIVITY = 1e5
LEAD_ENABLE = False
LEAD_RADIUS = ROD_RADIUS * 0.6
LEAD_CLEARANCE = 2.0
LEAD_LENGTH_DEFAULT = 12.0
TIME_STEP = min(0.0001, MOTION_TIME / 300.0)
REGION_X_POS = 0.0
REGION_X_NEG = 0.0
REGION_YZ_MARGIN = 12.0
EXCITATION_MODE = (
    "face_current"  # "winding" | "face_current" | "current_density" | "solid_current"
)

# --- 电流参数 ---
RATED_CURRENT = 4000
PEAK_CURRENT = RATED_CURRENT * 1.414
FREQUENCY = 50
PEAK_TIME = 0.25 / FREQUENCY  # 工频峰值时刻 (s)
ZERO_TIME = 0.5 / FREQUENCY  # 首个过零点 (s)
CENTER_POINT = [0.0, 0.0, 0.0]


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


def _dataset_exists(m3d, dataset_name):
    try:
        return dataset_name in (m3d.project_datasets or [])
    except Exception:
        return False


def _export_solution_data_csv(solution_data, csv_path):
    if not solution_data:
        return False
    try:
        if hasattr(solution_data, "export_data_to_csv"):
            solution_data.export_data_to_csv(csv_path)
            return True
        if hasattr(solution_data, "export_to_csv"):
            solution_data.export_to_csv(csv_path)
            return True
    except Exception:
        return False
    return False


def _parse_two_columns(csv_path):
    import csv

    rows = []
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                values = []
                for cell in row:
                    try:
                        values.append(float(cell))
                    except Exception:
                        continue
                if len(values) >= 2:
                    rows.append((values[0], values[1]))
    except Exception:
        return []
    return rows


def _interp_value(data_rows, target_x):
    if not data_rows:
        return None
    data_rows = sorted(data_rows, key=lambda item: item[0])
    if target_x <= data_rows[0][0]:
        return data_rows[0][1]
    if target_x >= data_rows[-1][0]:
        return data_rows[-1][1]
    for i in range(len(data_rows) - 1):
        x0, y0 = data_rows[i]
        x1, y1 = data_rows[i + 1]
        if x0 <= target_x <= x1:
            if x1 == x0:
                return y0
            return y0 + (y1 - y0) * (target_x - x0) / (x1 - x0)
    return None


def _find_face_by_extreme_x(m3d, obj_name, pick="max"):
    try:
        faces = m3d.modeler.get_object_faces(obj_name)
    except Exception:
        return None
    best_face = None
    best_x = None
    for fid in faces:
        center = m3d.modeler.get_face_center(fid)
        if not center or not isinstance(center, (list, tuple)) or len(center) < 3:
            continue
        x = center[0]
        if best_x is None:
            best_x = x
            best_face = fid
            continue
        if pick == "max" and x > best_x:
            best_x = x
            best_face = fid
        if pick == "min" and x < best_x:
            best_x = x
            best_face = fid
    return best_face


def _assign_current_raw(
    m3d, name, current, objects=None, faces=None, is_solid=True, point_out=False
):
    try:
        if not m3d.oboundary:
            return False
        if faces:
            m3d.oboundary.AssignCurrent(
                [
                    f"NAME:{name}",
                    "Faces:=",
                    faces,
                    "Current:=",
                    current,
                    "IsSolid:=",
                    is_solid,
                    "Point out of terminal:=",
                    point_out,
                ]
            )
        elif objects:
            m3d.oboundary.AssignCurrent(
                [
                    f"NAME:{name}",
                    "Objects:=",
                    objects,
                    "Current:=",
                    current,
                    "IsSolid:=",
                    is_solid,
                    "Point out of terminal:=",
                    point_out,
                ]
            )
        else:
            return False
        return True
    except Exception:
        return False


def _get_boundary_names(m3d):
    try:
        if m3d.oboundary and "GetBoundaries" in m3d.oboundary.__dir__():
            return list(m3d.oboundary.GetBoundaries())
    except Exception:
        return []
    return []


def _set_winding_terminal_order(m3d, winding_name, terminal_names):
    if m3d.oboundary:
        for method_name in (
            "OrderWindingTerminals",
            "SetWindingTerminalOrder",
            "SetWindingTerminalOrder2",
        ):
            if hasattr(m3d.oboundary, method_name):
                try:
                    getattr(m3d.oboundary, method_name)(winding_name, terminal_names)
                    return True
                except Exception:
                    pass
    if hasattr(m3d, "order_coil_terminals"):
        try:
            m3d.order_coil_terminals(winding_name, terminal_names)
            return True
        except Exception:
            pass
    return False


def _ensure_terminal_pad(m3d, name, x_pos, half_size, y_offset=0.0, z_offset=0.0):
    if name in m3d.modeler.object_names:
        return name
    created = None
    try:
        created = m3d.modeler.create_rectangle(
            position=[x_pos, y_offset - half_size, z_offset - half_size],
            dimension_list=[2 * half_size, 2 * half_size],
            name=name,
            matname="copper",
            cs_axis="X",
        )
    except Exception:
        try:
            created = m3d.modeler.create_rectangle(
                position=[x_pos, y_offset - half_size, z_offset - half_size],
                dimension_list=[2 * half_size, 2 * half_size],
                name=name,
                plane="YZ",
            )
        except Exception:
            created = None
    if not created:
        created = m3d.modeler.create_box(
            origin=[x_pos, y_offset - half_size, z_offset - half_size],
            sizes=[0.2, 2 * half_size, 2 * half_size],
            name=name,
            material="copper",
        )
    if hasattr(created, "name"):
        return created.name
    if isinstance(created, str):
        return created
    return name if name in m3d.modeler.object_names else None


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
solution_type = "TransientAPhiFormulation"

project_dir = os.environ.get("VI_PROJECT_DIR", r"D:\AnsysProducts\results")
project_file = os.path.join(project_dir, f"{project_name}.aedt")
project_lock = project_file + ".lock"
os.makedirs(project_dir, exist_ok=True)


def _is_ansysedt_running():
    try:
        output = subprocess.check_output(["tasklist"], text=True, errors="ignore")
        return "ansysedt.exe" in output.lower()
    except Exception:
        return False


def _cleanup_results_files(base_project_file):
    results_dir = base_project_file + "results"
    if not os.path.isdir(results_dir):
        return
    patterns = [
        os.path.join(results_dir, "**", "*.asol*"),
        os.path.join(results_dir, "**", "*.prv"),
        os.path.join(results_dir, "**", "*.lock"),
    ]
    targets = []
    for pattern in patterns:
        targets.extend(glob.glob(pattern, recursive=True))
    if not targets:
        return
    for path in targets:
        try:
            os.remove(path)
            print(f"  [提示] 已清理结果锁/缓存: {path}")
        except Exception as e:
            print(f"  [警告] 无法删除结果文件 {path}: {e}")


if os.path.exists(project_lock):
    try:
        os.remove(project_lock)
        print(f"  [提示] 已删除旧项目锁: {project_lock}")
    except Exception as e:
        print(f"  [警告] 无法删除项目锁 {project_lock}: {e}")

if _is_ansysedt_running():
    print("  [警告] 检测到 ansysedt.exe 正在运行，跳过结果文件清理以避免锁冲突")
else:
    _cleanup_results_files(project_file)

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

if ARC_ENABLE and not m3d.materials.exists_material("Arc_Column"):
    mat = m3d.materials.add_material("Arc_Column")
    mat.permittivity = 1.0
    mat.conductivity = ARC_CONDUCTIVITY

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
    cup_height = AMF_CUP_HEIGHT
    wall_thickness = AMF_WALL_THICKNESS
    base_thickness = AMF_BASE_THICKNESS
    plate_thickness = AMF_PLATE_THICKNESS

    slot_count = AMF_SLOT_COUNT
    slot_width = AMF_SLOT_WIDTH
    slot_angle = AMF_SLOT_ANGLE
    slot_pitch = AMF_SLOT_PITCH

    center_hole_radius = max(2.5, cup_radius * AMF_PLATE_HOLE_RATIO)
    groove_count = AMF_GROOVE_COUNT
    groove_width = AMF_GROOVE_WIDTH
    groove_length = cup_radius * AMF_GROOVE_LENGTH_RATIO

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
        material="CuCr_Alloy",
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
                origin=[
                    origin[0] + base_thickness * direction,
                    -cup_radius * 1.2,
                    -slot_width / 2,
                ],
                sizes=[
                    (cup_height - base_thickness) * direction * 1.2,
                    cup_radius * 2.4,
                    slot_width,
                ],
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
# AMF总长: cup_h + plate_h
amf_total_len = AMF_CUP_HEIGHT + AMF_PLATE_THICKNESS
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

if ARC_ENABLE and CONTACT_GAP > 0:
    try:
        arc_origin_x = STATIC_CONTACT_FACE_X
        arc = m3d.modeler.create_cylinder(
            orientation="X",
            origin=[arc_origin_x, 0, 0],
            radius=ARC_RADIUS,
            height=CONTACT_GAP,
            name="Arc_Column",
            material="Arc_Column",
        )
        if arc:
            print(f"  [信息] 弧柱已创建: 半径={ARC_RADIUS}mm, 长度={CONTACT_GAP}mm")
    except Exception as e:
        print(f"  [警告] 弧柱创建失败: {e}")

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
            x_pos=max(0.0, REGION_X_POS),
            x_neg=max(0.0, REGION_X_NEG),
            y_pos=REGION_YZ_MARGIN,
            y_neg=REGION_YZ_MARGIN,
            z_pos=REGION_YZ_MARGIN,
            z_neg=REGION_YZ_MARGIN,
            is_percentage=False,
        )
        print("  Region 创建完成")
except Exception:
    print("  使用默认 Region")

terminal_pad_in = None
terminal_pad_out = None
lead_in_name = None
lead_out_name = None
region_x_min = None
region_x_max = None
use_terminal_pads = LEAD_ENABLE or EXCITATION_MODE in ("winding", "face_current")
if use_terminal_pads:
    try:
        if "Region" in m3d.modeler.object_names:
            region_box = m3d.modeler["Region"].bounding_box
            if region_box and len(region_box) == 6:
                x_min, y_min, z_min, x_max, y_max, z_max = region_box
                region_x_min = x_min
                region_x_max = x_max
                y_half = max(2.0, min(ROD_RADIUS * 1.5, abs(y_max - y_min) / 2 - 1.0))
                z_half = max(2.0, min(ROD_RADIUS * 1.5, abs(z_max - z_min) / 2 - 1.0))
                half_size = min(y_half, z_half)
                if LEAD_ENABLE:
                    for obj_name in (
                        "Terminal_In_Pad",
                        "Terminal_Out_Pad",
                        "Terminal_In_Sheet",
                        "Terminal_Out_Sheet",
                        "Lead_In",
                        "Lead_Out",
                    ):
                        if obj_name in m3d.modeler.object_names:
                            try:
                                m3d.modeler.delete(obj_name)
                            except Exception:
                                pass
                    band_clearance = 2.0
                    moving_max_x = MOVING_ROD_X_END
                    if OPEN_DIRECTION == "positive":
                        band_x_end = moving_max_x + GAP_TRAVEL + band_clearance
                    else:
                        band_x_end = moving_max_x + band_clearance
                    lead_len_in = min(LEAD_LENGTH_DEFAULT, x_max - x_min - 2.0)
                    lead_in_start = x_min
                    lead_in_len = max(0.0, lead_len_in)
                    if lead_in_len >= 0.5:
                        lead_in = m3d.modeler.create_cylinder(
                            orientation="X",
                            origin=[lead_in_start, 0, 0],
                            radius=LEAD_RADIUS,
                            height=lead_in_len,
                            name="Lead_In",
                            material="copper",
                        )
                        if lead_in:
                            lead_in_name = "Lead_In"
                    lead_out_start = max(
                        x_max - LEAD_LENGTH_DEFAULT, band_x_end + LEAD_CLEARANCE
                    )
                    lead_out_len = x_max - lead_out_start
                    if lead_out_len >= 0.5:
                        lead_out = m3d.modeler.create_cylinder(
                            orientation="X",
                            origin=[lead_out_start, 0, 0],
                            radius=LEAD_RADIUS,
                            height=lead_out_len,
                            name="Lead_Out",
                            material="copper",
                        )
                        if lead_out:
                            lead_out_name = "Lead_Out"
                    terminal_pad_in = None
                    terminal_pad_out = None
                    print(f"  [信息] 引线体: In={lead_in_name}, Out={lead_out_name}")
                else:
                    terminal_pad_in = _ensure_terminal_pad(
                        m3d,
                        "Terminal_In_Pad",
                        x_min,
                        half_size,
                    )
                    terminal_pad_out = _ensure_terminal_pad(
                        m3d,
                        "Terminal_Out_Pad",
                        x_max,
                        half_size,
                    )
                    print(
                        f"  [测试] 端子片: {terminal_pad_in} @ X={x_min:.2f}, {terminal_pad_out} @ X={x_max:.2f}"
                    )
    except Exception as e:
        print(f"  [警告] 端子片创建失败: {e}")

# 8.1 基础几何校验
print("  [测试] 几何校验与验证...")
try:
    validation_dir = os.path.join(os.getcwd(), "VacuumInterrupter", "post")
    os.makedirs(validation_dir, exist_ok=True)
    validation_log = os.path.join(validation_dir, "model_validation.log")
    m3d.change_validation_settings(
        entity_check_level="Basic",
        ignore_unclassified=True,
        skip_intersections=False,
    )
    validation_result = m3d.validate_simple(validation_log)
    print(f"  [测试] ValidateDesign = {validation_result}, log: {validation_log}")
except Exception as e:
    print(f"  [警告] 几何验证失败: {e}")


def _log_object_volume(obj_name):
    try:
        if obj_name in m3d.modeler.object_names:
            obj = m3d.modeler[obj_name]
            volume = getattr(obj, "volume", None)
            print(f"  [测试] {obj_name} volume = {volume}")
        else:
            print(f"  [测试] {obj_name} 不存在")
    except Exception as e:
        print(f"  [警告] 读取 {obj_name} 体积失败: {e}")


_log_object_volume("Vacuum_Region")
_log_object_volume("Region")

# =============================================================================
# 9. Motion Band (只包围动端组件)
# =============================================================================
print("\n[9/10] 创建 Motion Band...")

# Band 范围：只包围动端组件 (Moving_Rod)
# 以当前几何为基准，按行程扩展，避免与静触头与屏蔽罩干涉
band_clearance = 2.0
moving_min_x = MOVING_CONTACT_FACE_X
moving_max_x = MOVING_ROD_X_END
if OPEN_DIRECTION == "positive":
    band_x_start = moving_min_x - band_clearance
    band_x_end = moving_max_x + GAP_TRAVEL + band_clearance
else:
    band_x_start = moving_min_x - GAP_TRAVEL - band_clearance
    band_x_end = moving_max_x + band_clearance

static_safe_x = STATIC_CONTACT_FACE_X + band_clearance
if band_x_start < static_safe_x:
    print(
        f"  [警告] Motion Band 左端接近静触头: {band_x_start:.2f}mm < {static_safe_x:.2f}mm"
    )
    band_x_start = static_safe_x

band_length = band_x_end - band_x_start
if band_length <= 0:
    raise ValueError("Motion Band 长度无效，请检查开距与行程设置")

max_band_radius = SHIELD_INNER_RADIUS - 0.3
band_radius = min(CONTACT_RADIUS + 0.5, max_band_radius)

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

# 避免 Motion_Band 与移动部件相交
try:
    band_cut_targets = [moving_conductor_name]
    if ARC_ENABLE and "Arc_Column" in m3d.modeler.object_names:
        band_cut_targets.append("Arc_Column")
    m3d.modeler.subtract("Motion_Band", band_cut_targets, keep_originals=True)
except Exception as e:
    print(f"  [警告] Motion_Band 挖空失败: {e}")

print(f"  X范围: {band_x_start:.1f}mm ~ {band_x_end:.1f}mm")
print(f"  静触头右端面: X={STATIC_CONTACT_X + CONTACT_THICKNESS:.1f}mm")
print(f"  Band 不与静触头重叠: CHECKED")
_log_object_volume("Motion_Band")

# =============================================================================
# 9.5 创建速度时程曲线 Dataset
# =============================================================================
print("\n[9.5/10] 创建速度时程曲线 Dataset...")

# 时间-速度数据点 (指数衰减模型)
velocity_data_x = [0.0, 0.001, 0.002, 0.003, 0.005, 0.008, 0.010, 0.015]
velocity_data_y = [1.25, 1.2, 1.1, 1.05, 1.0, 1.0, 1.0, 1.0]

dataset_name = "Velocity_Profile"
try:
    dataset_created = False
    if dataset_name not in m3d.project_datasets:
        created = m3d.create_dataset1d_design(
            dataset_name,
            velocity_data_x,
            velocity_data_y,
            x_unit="s",
            y_unit="m_per_sec",
        )
        print(f"  [成功] 创建 Dataset: {dataset_name}")
        dataset_created = bool(created) or True
    else:
        print(f"  [信息] Dataset {dataset_name} 已存在")
    # 部分版本不会立即刷新 project_datasets，这里不做硬性判定
    if velocity_data_x[-1] < MOTION_TIME:
        print("  [警告] 速度曲线末时刻小于仿真 StopTime，末段将保持常值")
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
            maximum_length=20.0,
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
    moving_parts = [moving_conductor_name]
    if ARC_ENABLE and "Arc_Column" in m3d.modeler.object_names:
        moving_parts.append("Arc_Column")

    # 分配运动带 (Motion Band)
    # PyAEDT method to assign translation motion
    if OPEN_DIRECTION == "positive":
        positive_limit = GAP_TRAVEL
        negative_limit = 0
        velocity_profile = f"pwl({dataset_name}, Time)"
    else:
        positive_limit = 0
        negative_limit = GAP_TRAVEL
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
    motion_enabled = True
    try:
        props = getattr(motion_setup, "props", {}) or {}
        props_text = " ".join([str(v) for v in props.values()])
        if abs(positive_limit - GAP_TRAVEL) > 1e-6 or abs(negative_limit) > 1e-6:
            print("  [警告] 运动行程与 GAP_TRAVEL 不一致")
        if "Motion_Band" not in m3d.modeler.object_names:
            print("  [警告] Motion_Band 未找到")
        print(f"  [信息] 速度配置: {velocity_profile}")
    except Exception as e:
        print(f"  [警告] 运动设置校验失败: {e}")
except Exception as e:
    print(f"  [警告] 设置运动失败: {e}")
    motion_enabled = False

# 10.2 Excitations
print("  配置电流激励...")
assigned_excitations = []
try:
    try:
        m3d.modeler.refresh()
        for conductor_name in [static_conductor_name, moving_conductor_name]:
            if conductor_name in m3d.modeler.object_names:
                obj = m3d.modeler[conductor_name]
                faces = m3d.modeler.get_object_faces(conductor_name)
                print(
                    f"  [测试] {conductor_name}: material={obj.material_name}, "
                    f"type={obj.object_type}, faces={len(faces)}"
                )
            else:
                print(f"  [测试] {conductor_name} 不存在")
    except Exception as e:
        print(f"  [警告] 导体信息读取失败: {e}")
    excitation_mode = EXCITATION_MODE
    excitation_done = False
    if motion_enabled and excitation_mode == "winding":
        print("  [信息] 使用边界端子片创建 Coil/Winding 激励")
    try:
        m3d.modeler.refresh()
        for conductor_name in [static_conductor_name, moving_conductor_name]:
            if conductor_name in m3d.modeler.object_names:
                obj = m3d.modeler[conductor_name]
                if hasattr(obj, "solve_inside"):
                    obj.solve_inside = True
    except Exception as e:
        print(f"  [警告] 导体求解设置失败: {e}")
    # 这里的电流是正弦波: 4000*1.414 * sin(2*pi*50*Time)
    current_expression = f"{PEAK_CURRENT:.2f}*sin(2*pi*{FREQUENCY}*Time)A"

    def _assign_face_current(use_pads=False):
        if use_pads and terminal_pad_in and terminal_pad_out:
            in_obj = lead_in_name or terminal_pad_in
            out_obj = lead_out_name or terminal_pad_out
            static_in_face = None
            moving_out_face = None
            try:
                if in_obj in m3d.modeler.object_names:
                    in_type = m3d.modeler[in_obj].object_type
                    if in_type == "Sheet":
                        static_in_face = in_obj
            except Exception:
                pass
            if static_in_face is None:
                if lead_in_name and region_x_min is not None:
                    static_in_face = m3d.modeler.get_faceid_from_position(
                        [region_x_min, 0, 0], obj_name=in_obj
                    )
                else:
                    static_in_face = _find_face_by_extreme_x(m3d, in_obj, pick="min")
            try:
                if out_obj in m3d.modeler.object_names:
                    out_type = m3d.modeler[out_obj].object_type
                    if out_type == "Sheet":
                        moving_out_face = out_obj
            except Exception:
                pass
            if moving_out_face is None:
                if lead_out_name and region_x_max is not None:
                    moving_out_face = m3d.modeler.get_faceid_from_position(
                        [region_x_max, 0, 0], obj_name=out_obj
                    )
                else:
                    moving_out_face = _find_face_by_extreme_x(m3d, out_obj, pick="max")
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
        if not static_in_face:
            static_in_face = _find_face_by_extreme_x(
                m3d, static_conductor_name, pick="min"
            )
        if not moving_out_face:
            moving_out_face = _find_face_by_extreme_x(
                m3d, moving_conductor_name, pick="max"
            )

        if static_in_face and moving_out_face:
            pre_boundaries = set(_get_boundary_names(m3d))
            print(f"  [测试] Pre-boundaries: {sorted(pre_boundaries)}")
            ex_in = m3d.assign_current(
                assignment=[static_in_face],
                amplitude=current_expression,
                solid=False,
                name="Phase_A_In",
            )
            ex_out = m3d.assign_current(
                assignment=[moving_out_face],
                amplitude=current_expression,
                solid=False,
                swap_direction=True,
                name="Phase_A_Out",
            )
            if ex_in is not False:
                assigned_excitations.append(ex_in)
            if ex_out is not False:
                assigned_excitations.append(ex_out)
            post_boundaries = set(_get_boundary_names(m3d))
            print(f"  [测试] Post-boundaries: {sorted(post_boundaries)}")
            if ex_in is False or ex_out is False:
                print("  [警告] Face Current 创建失败")
                return False
            print(f"  [成功] 设置电流激励 (Face In/Out): {current_expression}")
            return True
        else:
            print("  [警告] 未找到合适的端面，跳过电流激励")
        return False

    if excitation_mode == "winding":
        if terminal_pad_in and terminal_pad_out:
            pad_in_assignment = [terminal_pad_in]
            pad_out_assignment = [terminal_pad_out]
            try:
                pad_in_obj = m3d.modeler[terminal_pad_in]
                pad_out_obj = m3d.modeler[terminal_pad_out]
                print(
                    f"  [测试] 端子片类型: In={pad_in_obj.object_type}, Out={pad_out_obj.object_type}"
                )
                if pad_in_obj.object_type != "Sheet":
                    pad_in_face = _find_face_by_extreme_x(
                        m3d, terminal_pad_in, pick="min"
                    )
                    if pad_in_face:
                        pad_in_assignment = [pad_in_face]
                if pad_out_obj.object_type != "Sheet":
                    pad_out_face = _find_face_by_extreme_x(
                        m3d, terminal_pad_out, pick="max"
                    )
                    if pad_out_face:
                        pad_out_assignment = [pad_out_face]
            except Exception as e:
                print(f"  [警告] 端子片类型读取失败: {e}")
            try:
                coil_in = m3d.assign_coil(
                    assignment=pad_in_assignment,
                    conductors_number=1,
                    polarity="Positive",
                    name="PhaseA_Coil_In",
                )
                coil_out = m3d.assign_coil(
                    assignment=pad_out_assignment,
                    conductors_number=1,
                    polarity="Negative",
                    name="PhaseA_Coil_Out",
                )
            except Exception as e:
                coil_in = coil_out = None
                print(f"  [警告] 绕组端子创建失败: {e}")
            if coil_in and coil_out:
                print(f"  [测试] Coil terminals: {coil_in.name}, {coil_out.name}")
                try:
                    winding = m3d.assign_winding(
                        winding_type="Current",
                        is_solid=True,
                        current=current_expression,
                        name="PhaseA_Winding",
                        coil_terminals=[coil_in.name, coil_out.name],
                    )
                except TypeError:
                    winding = m3d.assign_winding(
                        winding_type="Current",
                        is_solid=True,
                        current=current_expression,
                        name="PhaseA_Winding",
                    )
                if winding:
                    try:
                        if m3d.oboundary:
                            m3d.oboundary.AddWindingTerminals(
                                winding.name, [coil_in.name, coil_out.name]
                            )
                        m3d.add_winding_coils(
                            winding.name, [coil_in.name, coil_out.name]
                        )
                        ordered = _set_winding_terminal_order(
                            m3d, winding.name, [coil_in.name, coil_out.name]
                        )
                        if not ordered:
                            print("  [警告] 绕组端子顺序设置失败")
                    except Exception as e:
                        print(f"  [警告] 绕组端子绑定失败: {e}")
                    print("  [成功] 设置绕组电流激励 (Coil/Winding)")
                    excitation_done = True
                else:
                    print("  [警告] 绕组激励创建失败，未生成 Winding")
            else:
                print("  [警告] 绕组激励创建失败，未生成线圈端子")
        else:
            print("  [警告] 端子片未创建，无法设置绕组激励")
        if not excitation_done:
            print("  [错误] 绕组激励失败，终止求解")
            raise SystemExit(1)

    if excitation_mode == "current_density":
        rod_area_m2 = math.pi * (ROD_RADIUS / 1000.0) ** 2
        current_density_x = f"({current_expression}) / ({rod_area_m2})"
        current_density_x_neg = f"-({current_expression}) / ({rod_area_m2})"
        target_in = lead_in_name or static_conductor_name
        target_out = lead_out_name or moving_conductor_name
        if (
            target_in in m3d.modeler.object_names
            and target_out in m3d.modeler.object_names
        ):
            ex_j1 = m3d.assign_current_density(
                assignment=[target_in],
                current_density_x=current_density_x,
                current_density_y="0",
                current_density_z="0",
                current_density_name="Phase_A_J_In",
            )
            ex_j2 = m3d.assign_current_density(
                assignment=[target_out],
                current_density_x=current_density_x_neg,
                current_density_y="0",
                current_density_z="0",
                current_density_name="Phase_A_J_Out",
            )
            if ex_j1:
                assigned_excitations.append(ex_j1)
            if ex_j2:
                assigned_excitations.append(ex_j2)
            excitation_done = bool(ex_j1 or ex_j2)
            if excitation_done:
                print(
                    "  [成功] 设置电流密度激励: Jx=+{0}, Jx=-{0}".format(
                        current_density_x
                    )
                )
            else:
                print("  [警告] 电流密度激励创建失败")
        elif target_in in m3d.modeler.object_names:
            ex_j = m3d.assign_current_density(
                assignment=[target_in],
                current_density_x=current_density_x,
                current_density_y="0",
                current_density_z="0",
                current_density_name="Phase_A_J",
            )
            if ex_j:
                assigned_excitations.append(ex_j)
            excitation_done = bool(ex_j)
            if excitation_done:
                print(f"  [成功] 设置电流密度激励: Jx={current_density_x}")
            else:
                print("  [警告] 电流密度激励创建失败")
        else:
            print("  [警告] 未找到导体对象，跳过电流激励")
            excitation_done = False
    elif excitation_mode == "face_current":
        excitation_done = _assign_face_current(use_pads=True)
    elif excitation_mode == "solid_current":
        target_in = lead_in_name or static_conductor_name
        target_out = lead_out_name or moving_conductor_name
        if (
            target_in in m3d.modeler.object_names
            and target_out in m3d.modeler.object_names
        ):
            pre_boundaries = set(_get_boundary_names(m3d))
            ex_in = m3d.assign_current(
                assignment=[target_in],
                amplitude=current_expression,
                solid=True,
                name="Phase_A_In",
            )
            ex_out = m3d.assign_current(
                assignment=[target_out],
                amplitude=current_expression,
                solid=True,
                swap_direction=True,
                name="Phase_A_Out",
            )
            post_boundaries = set(_get_boundary_names(m3d))
            if (
                ex_in is not False
                and ex_out is not False
                and pre_boundaries != post_boundaries
            ):
                assigned_excitations.extend([ex_in, ex_out])
                print(f"  [成功] 设置电流激励 (Solid): {current_expression}")
                excitation_done = True
            else:
                print("  [警告] Current 激励创建失败 (Solid)")
                excitation_done = False
        else:
            print(
                "  [警告] 未找到导体对象，跳过电流激励: "
                f"in={target_in in m3d.modeler.object_names}, "
                f"out={target_out in m3d.modeler.object_names}"
            )
            excitation_done = False

    if not excitation_done and excitation_mode == "face_current":
        print("  [信息] 尝试使用端子片 Face Current 兜底")
        excitation_done = _assign_face_current(use_pads=True)

except Exception as e:
    print(f"  [警告] 设置激励失败: {e}")

excitation_names = []
exc_list = []
# 激励校验
try:
    excitation_names = [b.name for b in m3d.boundaries] if m3d.boundaries else []
    if not excitation_names and not assigned_excitations:
        print("  [警告] 未检测到任何激励/边界，请在 AEDT 中确认电流激励是否生效")
    if assigned_excitations:
        print(
            "  [信息] 已创建激励: "
            + ", ".join([ex.name for ex in assigned_excitations])
        )
    elif excitation_names:
        print(f"  [信息] 边界列表: {excitation_names}")
    try:
        if m3d.oboundary and "GetExcitations" in m3d.oboundary.__dir__():
            exc_list = list(m3d.oboundary.GetExcitations())
            if exc_list:
                print(f"  [信息] Excitations: {exc_list}")
    except Exception as e:
        print(f"  [警告] Excitation 列表读取失败: {e}")
except Exception as e:
    print(f"  [警告] 激励校验失败: {e}")

has_excitation = False
if exc_list:
    has_excitation = True
else:
    has_excitation = bool(assigned_excitations) or bool(excitation_names)

if not has_excitation:
    print("  [错误] 未创建任何激励，终止求解以避免 Validation Error")
    raise SystemExit(1)

# 激励兜底：使用 Coil/Winding 方式
if not assigned_excitations and EXCITATION_MODE not in ("current_density", "winding"):
    try:
        if (
            static_conductor_name in m3d.modeler.object_names
            and moving_conductor_name in m3d.modeler.object_names
        ):
            coil_in = m3d.assign_coil(
                assignment=[static_conductor_name],
                conductors_number=1,
                polarity="Positive",
                name="PhaseA_Coil_In",
            )
            coil_out = m3d.assign_coil(
                assignment=[moving_conductor_name],
                conductors_number=1,
                polarity="Negative",
                name="PhaseA_Coil_Out",
            )
            if coil_in and coil_out:
                m3d.assign_winding(
                    winding_type="Current",
                    is_solid=True,
                    current=current_expression,
                    name="PhaseA_Winding",
                )
                print("  [信息] 已创建绕组电流激励 (Coil/Winding)")
    except Exception as e:
        print(f"  [警告] 绕组电流激励创建失败: {e}")

# 10.3 Analysis Setup
print("  创建求解 Setup...")
try:
    if "Transient_Analysis" in m3d.setup_names:
        setup = m3d.get_setup("Transient_Analysis")
    else:
        setup = m3d.create_setup(name="Transient_Analysis")

    setup.props["StopTime"] = f"{MOTION_TIME}s"
    setup.props["TimeStep"] = f"{TIME_STEP}s"
    setup.props["MaxTimeStep"] = f"{TIME_STEP}s"
    setup.props["MinTimeStep"] = f"{TIME_STEP / 5.0}s"
    # 确保保存场数据
    setup.props["SaveFieldsType"] = "Every step"
    setup.update()
    print(f"  [测试] Setup 列表: {m3d.setup_names}")
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
        field_times = [
            ("Peak", PEAK_TIME),
            ("Zero", ZERO_TIME),
            ("End", MOTION_TIME),
        ]

        cut_plane_name = "Field_Cutplane_Y"
        if cut_plane_name in m3d.modeler.object_names:
            cut_plane = m3d.modeler[cut_plane_name]
        else:
            cut_plane = m3d.modeler.create_plane(
                name=cut_plane_name,
                plane_base_x="0mm",
                plane_base_y="0mm",
                plane_base_z="0mm",
                plane_normal_x="0mm",
                plane_normal_y="1mm",
                plane_normal_z="0mm",
            )

        for label, time_value in field_times:
            time_str = f"{time_value}s"
            plot = m3d.post.create_fieldplot_surface(
                field_target,
                field_quantity,
                setup=setup_sweep,
                intrinsics={"Time": time_str},
                plot_name=f"Field_{field_quantity}_{field_target}_{label}",
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

            if cut_plane:
                cut_plot = m3d.post.create_fieldplot_cutplane(
                    [cut_plane.name],
                    field_quantity,
                    setup=setup_sweep,
                    intrinsics={"Time": time_str},
                    plot_name=f"Field_{field_quantity}_Cutplane_{label}",
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

    # AMF 中心点磁场时程与关键指标
    try:
        setup_sweep = _safe_setup_sweep_name(m3d, setup)
        field_category = _pick_report_category(
            m3d.post, ["Fields", "Transient", "Standard"]
        )
        if setup_sweep and field_category:
            axial_quantity = _select_report_quantity(
                m3d.post,
                setup_sweep,
                field_category,
                "Rectangular Plot",
                ["Bx", "B_x", "Mag_B", "B"],
            )
        else:
            axial_quantity = None

        if setup_sweep and field_category and axial_quantity:
            center_context = {"Context": "Point", "Point": CENTER_POINT}
            solution_data = m3d.post.get_solution_data(
                expressions=[axial_quantity],
                setup_sweep_name=setup_sweep,
                domain="Time",
                primary_sweep_variable="Time",
                variations={"Time": ["All"]},
                report_category=field_category,
                context=center_context,
            )
            center_bx_csv = os.path.join(export_dir, "center_bx_vs_time.csv")
            if _export_solution_data_csv(solution_data, center_bx_csv):
                print(f"  [成功] 导出中心点磁场 -> {center_bx_csv}")
                data_rows = _parse_two_columns(center_bx_csv)
                if data_rows:
                    peak_time, peak_value = max(
                        data_rows, key=lambda item: abs(item[1])
                    )
                    residual_value = _interp_value(data_rows, ZERO_TIME)
                    lag_time = peak_time - PEAK_TIME
                    phase_deg = lag_time * 360.0 * FREQUENCY

                    peak_current_ka = PEAK_CURRENT / 1000.0
                    peak_b_mT = abs(peak_value) * 1000.0
                    residual_b_mT = (
                        abs(residual_value) * 1000.0
                        if residual_value is not None
                        else None
                    )
                    peak_b_per_ka = (
                        peak_b_mT / peak_current_ka if peak_current_ka else None
                    )

                    metrics_csv = os.path.join(export_dir, "amf_metrics.csv")
                    with open(metrics_csv, "w", encoding="utf-8") as f:
                        f.write("Metric,Value,Unit\n")
                        f.write(f"Bx_Peak_Time,{peak_time},s\n")
                        f.write(f"Bx_Peak_Value,{peak_value},T\n")
                        if residual_value is not None:
                            f.write(f"Bx_Residual_At_Zero,{residual_value},T\n")
                        f.write(f"Lag_Time,{lag_time},s\n")
                        f.write(f"Lag_Phase,{phase_deg},deg\n")
                        f.write(f"Bx_Peak_mT,{peak_b_mT},mT\n")
                        if residual_b_mT is not None:
                            f.write(f"Bx_Residual_mT,{residual_b_mT},mT\n")
                    if peak_b_per_ka is not None:
                        f.write(f"Bx_Peak_per_kA,{peak_b_per_ka},mT/kA\n")
                    print(f"  [成功] 导出 AMF 指标 -> {metrics_csv}")

                # 触头表面径向分布 (可选)
                try:
                    if hasattr(m3d.modeler, "create_polyline"):
                        radial_name = "AMF_Radial_Line"
                        if radial_name not in m3d.modeler.object_names:
                            m3d.modeler.create_polyline(
                                [[0, 0, 0], [0, CONTACT_RADIUS, 0]],
                                name=radial_name,
                                non_model=True,
                            )
                        radial_context = {
                            "Context": "Polyline",
                            "Polyline": radial_name,
                        }
                        radial_data = m3d.post.get_solution_data(
                            expressions=[axial_quantity],
                            setup_sweep_name=setup_sweep,
                            domain="Distance",
                            primary_sweep_variable="Distance",
                            variations={"Time": [f"{PEAK_TIME}s"]},
                            report_category=field_category,
                            context=radial_context,
                        )
                        radial_csv = os.path.join(export_dir, "amf_radial_bx_peak.csv")
                        if _export_solution_data_csv(radial_data, radial_csv):
                            print(f"  [成功] 导出 AMF 径向曲线 -> {radial_csv}")
                except Exception as e:
                    print(f"  [警告] AMF 径向曲线导出失败: {e}")
            else:
                print("  [警告] 中心点磁场导出失败")
        else:
            print("  [警告] 未找到可用的轴向磁场量，跳过 AMF 指标导出")
    except Exception as e:
        print(f"  [警告] AMF 指标导出失败: {e}")
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
