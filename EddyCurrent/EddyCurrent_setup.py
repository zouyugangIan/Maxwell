#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
maxwell_setup.py - 开关柜涡流损耗仿真设置脚本

基于可用的 eddy_current_sim.py 添加材料参数化支持

用法:
  python maxwell_setup.py                    # 默认: 钢板材料
  python maxwell_setup.py --material steel   # 钢板材料
  python maxwell_setup.py --material alzn    # 铝锌板材料
  python maxwell_setup.py --all              # 两种材料都仿真
"""

import os
import sys
import time
import argparse
import platform
import subprocess
import inspect
from typing import Optional, Tuple


# ======================================================================
# 跨平台 ANSYS 版本和路径自动检测 (必须在导入 pyaedt 之前执行)
# ======================================================================
def detect_ansys_installation():
    """
    自动检测 ANSYS Electronics Desktop 安装版本和路径 (Windows/Linux)
    返回: (版本号, 安装路径) 例如 ("2022.1", "C:\\Program Files\\AnsysEM\\v221\\Win64")
    """
    _system = platform.system()

    if _system == "Windows":
        # 明确支持 E 盘自定义安装目录 (你当前机器使用)
        e_drive = r"E:\Ansys2024R2\v242\Win64"
        if os.path.exists(e_drive):
            return ("2024.2", e_drive)

        def _try_registry(base: str) -> Tuple[Optional[str], Optional[str]]:
            try:
                import winreg

                base_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base)
                versions = []
                i = 0
                while True:
                    try:
                        ver = winreg.EnumKey(base_key, i)
                        versions.append(ver)
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(base_key)

                if not versions:
                    return (None, None)

                versions.sort(reverse=True)
                detected_version = versions[0]
                try:
                    key = winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        rf"{base}\{detected_version}",
                    )
                    install_path = winreg.QueryValueEx(key, "InstallPath")[0]
                    winreg.CloseKey(key)
                    if install_path and os.path.exists(install_path):
                        return (detected_version, install_path)
                except Exception:
                    return (detected_version, None)

                return (detected_version, None)
            except Exception:
                return (None, None)

        # 64-bit + 32-bit registry view (很多机器装完会在 WOW6432Node)
        for base in (
            r"SOFTWARE\Ansoft\ElectronicsDesktop",
            r"SOFTWARE\WOW6432Node\Ansoft\ElectronicsDesktop",
        ):
            ver, install = _try_registry(base)
            if ver:
                if install and os.path.exists(install):
                    return (ver, install)

                ver_code = ver.replace(".", "")[:3]
                candidates = [
                    rf"C:\Program Files\AnsysEM\v{ver_code}\Win64",
                    rf"C:\Program Files\Ansys Inc\AnsysEM\v{ver_code}\Win64",
                ]
                for path in candidates:
                    if os.path.exists(path):
                        return (ver, path)
                return (ver, None)

        # 最后兜底: 扫描常见安装目录
        candidates = []
        for base in (
            r"C:\Program Files\AnsysEM",
            r"C:\Program Files\Ansys Inc\AnsysEM",
        ):
            if os.path.isdir(base):
                try:
                    for p in os.listdir(base):
                        if p.lower().startswith("v"):
                            win64 = os.path.join(base, p, "Win64")
                            if os.path.isdir(win64):
                                candidates.append(win64)
                except Exception:
                    pass
        # 选最新的一个（按文件夹名排序，v241 > v232）
        candidates.sort(reverse=True)
        if candidates:
            # 无法从目录百分百反推版本号，这里只返回路径
            return (None, candidates[0])

    elif _system == "Linux":
        linux_configs = [
            ("2024.1", "/media/large_disk/ansysLinux/AnsysEM/v241/Linux64"),
            ("2024.1", "/opt/AnsysEM/v241/Linux64"),
            ("2023.2", "/opt/AnsysEM/v232/Linux64"),
            ("2022.1", "/opt/AnsysEM/v221/Linux64"),
        ]
        for ver, path in linux_configs:
            if os.path.exists(path):
                return (ver, path)

    return (None, None)


# 检测版本和路径
_detected_version, _ansys_path = detect_ansys_installation()

if _detected_version:
    AEDT_VERSION = _detected_version
    print(f"[INFO] 检测到 ANSYS Electronics Desktop {AEDT_VERSION}")
else:
    AEDT_VERSION = "2024.1"
    print(f"[WARN] 未检测到 ANSYS 版本，使用默认: {AEDT_VERSION}")

if _ansys_path:
    ver_code = AEDT_VERSION.replace(".", "")[:3]
    os.environ[f"ANSYSEM_ROOT{ver_code}"] = _ansys_path
    os.environ["ANSYSEM_DIR"] = _ansys_path
    print(f"[INFO] ANSYS 安装路径: {_ansys_path}")
else:
    print(f"[INFO] 将使用 PyAEDT 默认路径检测")

# 根据版本决定是否使用 gRPC (2022.2 及以上支持)
_use_grpc = tuple(map(int, AEDT_VERSION.split("."))) >= (2022, 2)
if not _use_grpc:
    print(f"[INFO] AEDT {AEDT_VERSION} 不支持 gRPC，使用 COM 接口")

# 必须在导入 PyAEDT/ansys.aedt.core 之前设置 settings
try:
    # 新架构 (PyAnsys)
    from ansys.aedt.core import settings  # type: ignore
    from ansys.aedt.core import Maxwell3d  # type: ignore
except Exception:
    # 旧包名/兼容别名
    from pyaedt import settings  # type: ignore
    from pyaedt import Maxwell3d  # type: ignore

settings.use_grpc_api = _use_grpc


def _open_maxwell(
    projectname: str,
    designname: str,
    solution_type: Optional[str] = None,
    specified_version: Optional[str] = None,
    new_desktop_session: bool = True,
):
    """稳健打开 Maxwell 设计。

    说明:
    - new_desktop_session=True 更稳: 即使没手动打开 AEDT 也能启动会话
    - 如果 gRPC/版本不匹配导致连接异常, 自动回退到 COM
    """

    def _build_kwargs():
        sig = inspect.signature(Maxwell3d.__init__)
        if "projectname" in sig.parameters:
            kw = dict(
                projectname=projectname,
                designname=designname,
                specified_version=specified_version,
                new_desktop_session=new_desktop_session,
            )
        else:
            kw = dict(
                project=projectname,
                design=designname,
                version=specified_version,
                new_desktop=new_desktop_session,
            )
        if solution_type:
            kw["solution_type"] = solution_type
        return kw

    def _try(use_grpc: bool):
        settings.use_grpc_api = use_grpc
        m = Maxwell3d(**_build_kwargs())
        # 强制触发一次 modeler 初始化，避免后续出现 '_modeler' 这种延迟错误
        _ = m.modeler.object_names
        return m

    # 首选: 按版本推断的 API
    try:
        return _try(_use_grpc)
    except Exception as e1:
        # 回退: 反向尝试
        try:
            return _try(not _use_grpc)
        except Exception as e2:
            raise RuntimeError(
                "无法启动/连接 Maxwell(AEDT)。\n"
                f"- 首次尝试(UseGrpc={_use_grpc})失败: {e1}\n"
                f"- 回退尝试(UseGrpc={not _use_grpc})失败: {e2}\n"
                "建议: 确认本机已安装 Ansys Electronics Desktop, 并传入正确的 --aedt-version 或设置安装路径环境变量。"
            )


def _launch_aedt_from_bat(bat_path: str, wait_seconds: int = 8) -> None:
    """启动 AEDT (通常同时启动许可服务)。"""
    if not os.path.isfile(bat_path):
        print(f"[WARN] 启动脚本不存在: {bat_path}")
        return

    print(f"[INFO] 启动 AEDT: {bat_path}")
    try:
        comspec = os.environ.get("COMSPEC", r"C:\Windows\System32\cmd.exe")
        subprocess.Popen([comspec, "/c", bat_path], close_fds=True)
        time.sleep(max(0, wait_seconds))
    except Exception as e:
        print(f"[WARN] 启动 AEDT 失败: {e}")


# ======================================================================
# 配置参数
# ======================================================================
PROJECT_NAME = "KYN28_V19_Final"
SOLVER_TYPE = "EddyCurrent"

# ======================================================================
# 隔板材料定义 (与参考文献一致)
# ======================================================================
PLATE_MATERIALS = {
    "galvalume": {
        "name": "Structural_Steel",
        "description": "覆铝锌板(结构钢基材,铁磁材料)",
        "conductivity": 4032000,  # S/m (4.032e6)
        "permeability": 4000,  # 相对磁导率 (铁磁)
        "design_suffix": "Galvalume",
    },
    "stainless": {
        "name": "Stainless_Steel",
        "description": "不锈钢板(非铁磁材料)",
        "conductivity": 1137000,  # S/m (1.137e6)
        "permeability": 1,  # 相对磁导率 (非磁性)
        "design_suffix": "Stainless",
    },
}

# 几何参数 (与参考文献一致)
# 铜排规格: 3-TMY (120×10), 截面积 3535.62mm²
# 参考图: 铜排垂直放置，L型框架水平放置在铜排中间
bus_w = 120.0  # 铜排宽度 (沿 X 方向)
bus_d = 10.0  # 铜排厚度 (沿 Y 方向)
bus_h = 600.0  # 铜排高度 (沿 Z 方向，垂直向上)
space_pitch = 160.0  # 铜排中心间距 (沿 Y 方向)

# L 型铁框参数 (水平放置，铜排从中间穿过)
# 框架由顶盖 + 四边立壁组成
frame_length = 300.0  # 框架长度 (沿 X 方向，覆盖铜排宽度)
frame_width = 540.0  # 框架宽度 (沿 Y 方向，容纳3根铜排)
frame_flange = 50.0  # 框架翼缘高度 (沿 Z 方向向下)
frame_th = 3.0  # 框架板厚
gap = 20.0  # 铜排与框架间隙


def create_simulation(material_key: str, *, new_desktop_session: bool = True):
    """创建指定材料的涡流仿真"""

    mat = PLATE_MATERIALS[material_key]
    design_name = f"EddyCurrent_{mat['design_suffix']}"

    print("=" * 70)
    print(f"创建仿真: {design_name}")
    print(f"隔板材料: {mat['description']}")
    print(f"  电导率: {mat['conductivity']} S/m")
    print(f"  相对磁导率: {mat['permeability']}")
    print("=" * 70)

    # 简化设计创建流程
    print("准备设计...")

    # 直接创建设计，使用 designname 参数
    # 如果设计已存在，PyAEDT 会自动激活它
    try:
        m3d = _open_maxwell(
            projectname=PROJECT_NAME,
            designname=design_name,
            solution_type=SOLVER_TYPE,
            specified_version=AEDT_VERSION,
            # 默认开启新会话, 避免“没开 Maxwell 导致连接失败”
            new_desktop_session=new_desktop_session,
        )
        print(f"  设计 '{design_name}' 已就绪")

        # 如果设计已有对象，询问是否清除
        existing_objs = m3d.modeler.object_names
        if existing_objs:
            print(f"  清除 {len(existing_objs)} 个现有对象...")
            m3d.modeler.delete(existing_objs)

        # 清除现有 setup
        for s in list(m3d.setup_names):
            m3d.delete_setup(s)

    except Exception as e:
        print(f"  设计创建失败: {e}")
        print("  请在 Maxwell 中手动删除同名设计后重试")
        return None

    m3d.modeler.model_units = "mm"

    # ======================================================================
    # 同步参数到 Maxwell
    # ======================================================================
    print("  [1/7] 定义参数...")
    params = {
        "Bus_W": f"{bus_w}mm",  # 铜排宽度 120mm (X)
        "Bus_D": f"{bus_d}mm",  # 铜排厚度 10mm (Y)
        "Bus_H": f"{bus_h}mm",  # 铜排高度 600mm (Z)
        "Space": f"{space_pitch}mm",  # 铜排间距 160mm (Y)
        "Frame_L": f"{frame_length}mm",  # 框架长度 (X)
        "Frame_W": f"{frame_width}mm",  # 框架宽度 (Y)
        "Frame_F": f"{frame_flange}mm",  # 框架翼缘高度 (Z)
        "Frame_Th": f"{frame_th}mm",  # 框架板厚
        "Gap": f"{gap}mm",
    }
    for k, v in params.items():
        m3d[k] = v

    # ======================================================================
    # 定义材料
    # ======================================================================
    print("  [2/7] 定义材料...")
    mat_name = mat["name"]
    if mat_name not in m3d.materials.material_keys:
        m = m3d.materials.add_material(mat_name)
    else:
        m = m3d.materials[mat_name]

    m.permeability = mat["permeability"]
    m.conductivity = mat["conductivity"]
    m.dielectric_permittivity = 1

    # ======================================================================
    # 几何建模 - 参考图结构
    # 铜排垂直 (沿 Z 向上)，L 型框架水平放置在铜排中间
    # ======================================================================
    print("  [3/7] 创建几何模型...")

    # --- 母排 (3-TMY 120×10mm，垂直放置) ---
    # 铜排沿 Z 方向 (高度)，宽度沿 X，厚度沿 Y
    # 使用数值坐标确保兼容性

    # A相母排 (Y = -space_pitch)
    bus_a = m3d.modeler.create_box(
        origin=[-bus_w / 2, -bus_d / 2 - space_pitch, -bus_h / 2],
        sizes=[bus_w, bus_d, bus_h],
        name="Busbar_A",
        material="copper",
    )
    bus_a.color = (255, 0, 0)

    # B相母排 (Y = 0)
    bus_b = m3d.modeler.create_box(
        origin=[-bus_w / 2, -bus_d / 2, -bus_h / 2],
        sizes=[bus_w, bus_d, bus_h],
        name="Busbar_B",
        material="copper",
    )
    bus_b.color = (0, 255, 0)

    # C相母排 (Y = +space_pitch)
    bus_c = m3d.modeler.create_box(
        origin=[-bus_w / 2, -bus_d / 2 + space_pitch, -bus_h / 2],
        sizes=[bus_w, bus_d, bus_h],
        name="Busbar_C",
        material="copper",
    )
    bus_c.color = (255, 255, 0)

    # ======================================================================
    # L 型角钢框架 (两条平行角钢，铜排从中间穿过)
    # ======================================================================
    # 参考图结构：
    # - 矩形隔板框架 (口字型，铜排从中间穿过)
    # - 参考原图：四边围成一个矩形框

    # 框架尺寸
    plate_th = 3.0  # 隔板厚度
    plate_height = 50.0  # 隔板高度 (Z 方向)
    plate_z = -plate_height / 2  # 隔板 Z 向居中

    # 框架外边界 (比铜排范围稍大)
    frame_x_outer = bus_w / 2 + gap + 30  # X 方向外边界
    frame_y_outer = space_pitch + bus_d / 2 + 30  # Y 方向外边界

    # 创建矩形框架 (4 条边)
    # 前边 (+Y 侧)
    front = m3d.modeler.create_box(
        origin=[-frame_x_outer, frame_y_outer - plate_th, plate_z],
        sizes=[2 * frame_x_outer, plate_th, plate_height],
        name="Frame_Front",
    )
    # 后边 (-Y 侧)
    back = m3d.modeler.create_box(
        origin=[-frame_x_outer, -frame_y_outer, plate_z],
        sizes=[2 * frame_x_outer, plate_th, plate_height],
        name="Frame_Back",
    )
    # 左边 (-X 侧)
    left = m3d.modeler.create_box(
        origin=[-frame_x_outer, -frame_y_outer, plate_z],
        sizes=[plate_th, 2 * frame_y_outer, plate_height],
        name="Frame_Left",
    )
    # 右边 (+X 侧)
    right = m3d.modeler.create_box(
        origin=[frame_x_outer - plate_th, -frame_y_outer, plate_z],
        sizes=[plate_th, 2 * frame_y_outer, plate_height],
        name="Frame_Right",
    )

    # 合并四边为一个整体
    # unite 在不同版本里返回值略有差异，这里取第一条作为合并后的实体
    united = m3d.modeler.unite([front.name, back.name, left.name, right.name])
    if isinstance(united, (list, tuple)) and united:
        merged_name = united[0]
    else:
        merged_name = front.name

    frame = m3d.modeler[merged_name]
    frame.name = "Plate_Frame"
    frame.material_name = mat_name
    frame.color = (143, 175, 143)
    frame.transparency = 0.4

    # ======================================================================
    # 仿真区域 (以铜排为中心对称，Z 方向铜排端面正好贴到边界)
    # ======================================================================
    print("  [4/7] 创建仿真区域...")

    # 计算 Region 边界 (以模型原点为中心)
    # X 方向: 框架外边界 + padding
    x_half = frame_x_outer + 50  # 额外 50mm padding
    # Y 方向: 加宽至 2 倍
    y_half = (frame_y_outer + 50) * 2  # 原来的 2 倍
    # Z 方向: 铜排端面正好贴到边界
    z_half = bus_h / 2  # 铜排高度的一半

    # 创建 Region (手动创建 box 并设为 vacuum)
    region = m3d.modeler.create_box(
        origin=[-x_half, -y_half, -z_half],
        sizes=[2 * x_half, 2 * y_half, 2 * z_half],
        name="Region",
        material="vacuum",
    )
    region.transparency = 0.9

    # ======================================================================
    # 电流激励 (使用母排 Z 方向端面)
    # ======================================================================
    print("  [5/7] 分配电流激励...")

    phases = ["A", "B", "C"]
    phase_angles = {"A": "0deg", "B": "-120deg", "C": "120deg"}
    y_centers = {"A": -space_pitch, "B": 0.0, "C": space_pitch}
    bus_objs = {"A": bus_a, "B": bus_b, "C": bus_c}

    # 铜排垂直放置，端面在 Z 方向
    def _pick_end_faces(obj):
        faces = getattr(obj, "faces", [])
        if not faces:
            return (None, None)

        z_faces = []
        for f in faces:
            try:
                n = f.normal
                if n and abs(n[2]) > 0.9:
                    z_faces.append(f)
            except Exception:
                pass

        if not z_faces:
            z_faces = faces

        def _zc(face):
            return face.center[2]

        bottom = min(z_faces, key=_zc)
        top = max(z_faces, key=_zc)
        return (bottom.id, top.id)

    z_bottom = -bus_h / 2.0  # 底端
    z_top = bus_h / 2.0  # 顶端
    x_center = 0.0

    for phase in phases:
        bus_obj = bus_objs[phase]
        angle = phase_angles[phase]
        y_c = y_centers[phase]

        face_bottom_id, face_top_id = _pick_end_faces(bus_obj)

        if face_bottom_id and face_top_id:
            m3d.assign_current(
                face_bottom_id,
                amplitude="4000A",
                phase=angle,
                name=f"Cur_{phase}_In",
                solid=False,
            )
            m3d.assign_current(
                face_top_id,
                amplitude="4000A",
                phase=angle,
                name=f"Cur_{phase}_Out",
                solid=False,
                swap_direction=True,
            )
            print(f"    {phase}相: 4000A @ {angle}")
        else:
            print(f"    ERROR: 无法找到 {phase} 相端面")

    # ======================================================================
    # 涡流效应和网格
    # ======================================================================
    print("  [6/7] 配置涡流效应和网格...")

    m3d.eddy_effects_on(
        [frame.name, bus_a.name, bus_b.name, bus_c.name],
        enable_eddy_effects=True,
        enable_displacement_current=False,
    )

    m3d.mesh.assign_length_mesh(
        [bus_a.name, bus_b.name, bus_c.name],
        maximum_length="100mm",
        name="Mesh_Busbars",
    )
    m3d.mesh.assign_length_mesh([frame.name], maximum_length="30mm", name="Mesh_Frame")

    # ======================================================================
    # 求解设置和场图
    # ======================================================================
    print("  [7/7] 配置求解器和场图...")

    setup = m3d.create_setup(name="Setup1")
    setup.props["Frequency"] = "50Hz"
    setup.props["PercentError"] = 2
    setup.props["MaximumPasses"] = 6
    setup.props["PercentRefinement"] = 30
    setup.props["BasisOrder"] = 1

    # 场图 (先删除已有的再创建)
    for plot_name in ["Plot_OhmicLoss", "Plot_J", "Plot_Mag_B"]:
        try:
            m3d.post.delete_field_plot(plot_name)
        except:
            pass

    m3d.post.create_fieldplot_surface(
        [frame.name], "Ohmic_Loss", plot_name="Plot_OhmicLoss"
    )
    m3d.post.create_fieldplot_surface(
        [bus_a.name, bus_b.name, bus_c.name], "J", plot_name="Plot_J"
    )
    m3d.post.create_fieldplot_surface(
        [frame.name, bus_a.name, bus_b.name, bus_c.name],
        "Mag_B",
        plot_name="Plot_Mag_B",
    )

    # 验证
    is_valid = m3d.validate_simple()
    if is_valid:
        print("  OK: 验证通过")
    else:
        print("  WARN: 验证警告，请检查消息")

    # 保存
    m3d.save_project()

    # 释放但不关闭
    m3d.release_desktop(close_projects=False, close_desktop=False)

    print(f"\nOK: 设计 '{design_name}' 创建完成!")
    return design_name


def main():
    parser = argparse.ArgumentParser(description="Maxwell 涡流仿真设置")
    parser.add_argument(
        "--material",
        "-m",
        choices=["galvalume", "stainless"],
        default="galvalume",
        help="隔板材料: galvalume(覆铝锌板) 或 stainless(不锈钢板)",
    )
    parser.add_argument("--all", "-a", action="store_true", help="仿真所有材料")
    parser.add_argument("--analyze", action="store_true", help="创建后自动运行仿真分析")
    parser.add_argument(
        "--aedt-version",
        default=None,
        help="指定 AEDT 版本(如 2024.1/2023.2)。默认自动检测",
    )
    parser.add_argument(
        "--aedt-path",
        default=None,
        help="指定 AEDT 安装路径(如 E:\\Ansys2024R2\\v242\\Win64)",
    )
    parser.add_argument(
        "--attach",
        action="store_true",
        help="附着到已打开的 AEDT 会话(不新开)。默认会新开会话",
    )
    parser.add_argument(
        "--launch-bat",
        default=None,
        help="先运行启动脚本(例如 E:\\Ansys2024R2\\Launch_Maxwell_E_Drive.bat)",
    )
    parser.add_argument(
        "--wait-aedt",
        type=int,
        default=8,
        help="启动 AEDT 后等待秒数(默认 8 秒)",
    )

    args = parser.parse_args()

    # 便捷模式: 直接运行脚本(无参数)时, 默认启动“不锈钢板 + 自动分析”。
    # 如果你更希望保留旧默认行为(覆铝锌板且不自动分析), 把下面两行删掉即可。
    if len(sys.argv) == 1:
        args.material = "stainless"
        args.analyze = True

    # 如果用户显式指定路径或版本, 覆盖自动检测结果
    global AEDT_VERSION
    if args.aedt_path:
        if os.path.isdir(args.aedt_path):
            # 依据路径提取版本号 v242 -> 2024.2
            norm = os.path.normpath(args.aedt_path)
            parent = os.path.basename(os.path.dirname(norm))
            if parent.lower().startswith("v") and len(parent) >= 4:
                ver_code = parent[1:4]
                AEDT_VERSION = f"20{ver_code[0:2]}.{ver_code[2]}"
                os.environ[f"ANSYSEM_ROOT{ver_code}"] = norm
            os.environ["ANSYSEM_DIR"] = norm
        else:
            print(f"[WARN] 指定的 AEDT 路径不存在: {args.aedt_path}")
    if args.aedt_version:
        AEDT_VERSION = args.aedt_version

    if args.launch_bat:
        _launch_aedt_from_bat(args.launch_bat, wait_seconds=args.wait_aedt)
        # 已经启动 AEDT，默认使用附着模式
        args.attach = True

    print("\n" + "=" * 70)
    print("开关柜金属隔板涡流损耗仿真")
    print("=" * 70)

    designs = []
    if args.all:
        print("模式: 材料对比 (钢板 + 铝锌板)")
        for mat_key in PLATE_MATERIALS:
            design = create_simulation(mat_key, new_desktop_session=(not args.attach))
            designs.append(design)
            time.sleep(2)
        print(f"\n创建的设计: {designs}")
    else:
        print(f"材料: {PLATE_MATERIALS[args.material]['description']}")
        design = create_simulation(args.material, new_desktop_session=(not args.attach))
        if design:
            designs.append(design)

    # 自动运行仿真
    if args.analyze and designs:
        print("\n" + "=" * 70)
        print("运行仿真分析...")
        print("=" * 70)

        try:
            m3d = _open_maxwell(
                projectname=PROJECT_NAME,
                designname=designs[0],
                specified_version=AEDT_VERSION,
                new_desktop_session=(not args.attach),
            )

            # 运行所有设计的分析
            for design_name in designs:
                if design_name:
                    print(f"\n分析设计: {design_name}")
                    m3d.set_active_design(design_name)
                    m3d.analyze_setup("Setup1")
                    print(f"  OK: {design_name} 分析完成")

            m3d.save_project()
            m3d.release_desktop(close_projects=False, close_desktop=False)
            print("\nOK: 所有仿真分析完成!")

        except Exception as e:
            print(f"\n✗ 仿真运行出错: {e}")
            print("  请在 Maxwell 中手动运行 Analyze All")

    print("\n" + "=" * 70)
    if args.analyze:
        print("完成! 可运行 maxwell_report.py 生成报告")
    else:
        print("完成! 下一步:")
        print("  1. 在 Maxwell 中点击 'Analyze All' 运行仿真")
        print("     或运行: python maxwell_setup.py --analyze")
        print("  2. 仿真完成后运行 maxwell_report.py 生成报告")
    print("=" * 70)


if __name__ == "__main__":
    main()
