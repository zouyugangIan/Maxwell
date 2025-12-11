import os
from pyaedt import Maxwell3d

# ==========================================
# 1. 初始化设置
# ==========================================
project_name = "KYN28_Busbar_Analysis"
design_name = "EddyCurrent_Sim"

# non_graphical=False 表示启动 Maxwell 图形界面
# specified_version 可以指定版本，如 "2023.1"，不填默认最新
m3d = Maxwell3d(projectname=project_name, designname=design_name, solution_type="EddyCurrent", non_graphical=False)

# ==========================================
# 2. 定义参数 (变量化建模)
# ==========================================
# 铜排尺寸 (估算值，你可以根据实际修改)
busbar_width = "10mm"     # 铜排厚度
busbar_depth = "100mm"    # 铜排宽度
busbar_height = "600mm"   # 铜排高度
phase_spacing = "160mm"   # 相间距离

# 隔板尺寸
plate_thickness = "3mm"
plate_x = "600mm"         # 隔板总长
plate_y = "400mm"         # 隔板总宽
hole_clearance = "20mm"   # 铜排穿过隔板的开孔间隙

# 电流参数
current_mag = "4000A"
freq = "50Hz"

# 将变量应用到 Maxwell
m3d["Bus_W"] = busbar_width
m3d["Bus_D"] = busbar_depth
m3d["Bus_H"] = busbar_height
m3d["Space"] = phase_spacing
m3d["Plate_Th"] = plate_thickness
m3d["Gap"] = hole_clearance

# ==========================================
# 3. 创建自定义材料 (参考你的表格)
# ==========================================
# 1. 结构钢 (Structural Steel) - 高导磁
if not m3d.materials.checkifmaterialexists("Steel_Plate_KYN"):
    mat_steel = m3d.materials.add_material("Steel_Plate_KYN")
    mat_steel.conductivity = 4.032e6
    mat_steel.permeability = 4000  # 相对磁导率
    mat_steel.mass_density = 7850

# 2. 铜 (Copper) - 使用库中现有的，或者自定义
# 库里的 copper 导电率约为 5.8e7，接近你表格的 5.998e7，这里直接用库里的即可

# ==========================================
# 4. 几何建模
# ==========================================
m3d.modeler.delete_all_objects() # 清空当前设计

# --- A. 创建金属隔板 ---
# 先画板子
plate = m3d.modeler.create_box(
    origin=["-Plate_Th/2", "-plate_y/2", "-plate_x/2"],
    sizes=["Plate_Th", "plate_y", "plate_x"],
    name="Isolation_Plate",
    material="Steel_Plate_KYN"
)

# 画3个挖孔用的盒子 (Busbar尺寸 + 间隙)
hole_names = []
for i, offset in enumerate(["-Space", "0mm", "Space"]):
    hole = m3d.modeler.create_box(
        origin=["-Plate_Th", f"-Bus_D/2 - Gap + {offset}", "-Bus_W/2 - Gap"],
        sizes=["Plate_Th*3", "Bus_D + 2*Gap", "Bus_W + 2*Gap"], # 稍微长一点以确保完全贯穿
        name=f"Hole_Tool_{i}"
    )
    hole_names.append(hole.name)

# 布尔运算：板子 - 孔
m3d.modeler.subtract(tool_list=hole_names, blank_list=[plate.name], keep_originals=False)

# --- B. 创建三相铜排 ---
# 注意：方向要和孔对应。根据上面的坐标，铜排是细长的，穿过板子
phases = ["A", "B", "C"]
busbar_objs = []
offsets = ["-Space", "0mm", "Space"]

for i, phase in enumerate(phases):
    # 铜排是立着的，穿过板子
    # 坐标系调整以匹配之前的开孔位置
    bb = m3d.modeler.create_box(
        origin=["-Bus_H/2", f"-Bus_D/2 + {offsets[i]}", "-Bus_W/2"],
        sizes=["Bus_H", "Bus_D", "Bus_W"],
        name=f"Busbar_{phase}",
        material="Copper"
    )
    busbar_objs.append(bb)
    
    # 稍微给个颜色区分
    if phase == "A": bb.color = (255, 0, 0)
    if phase == "B": bb.color = (0, 255, 0)
    if phase == "C": bb.color = (255, 255, 0)

# ==========================================
# 5. 边界条件与求解域
# ==========================================
# 创建空气包围盒 (Padding 50%)
region = m3d.modeler.create_region(pad_percent=50)

# ==========================================
# 6. 施加激励 (电流)
# ==========================================
# 三相电流，互差120度
# Phase A: 0 deg
# Phase B: -120 deg
# Phase C: 120 deg

# 获取铜排的端面用于加电流 (通常取 Z 最大的面或者 X 最大的面，取决于上面的画法)
# 上面画法 Bus_H 是沿着 X轴的 (origin x = -Bus_H/2, size = Bus_H)
# 所以电流进出面是 X 的正负面

m3d.assign_current(busbar_objs[0].bottom_face_x, amplitude=current_mag, phase="0deg", name="Current_A", swap_direction=False)
m3d.assign_current(busbar_objs[1].bottom_face_x, amplitude=current_mag, phase="-120deg", name="Current_B", swap_direction=False)
m3d.assign_current(busbar_objs[2].bottom_face_x, amplitude=current_mag, phase="120deg", name="Current_C", swap_direction=False)

# ==========================================
# 7. 网格划分 (Meshing)
# ==========================================
# 根据图片，对关键部位进行网格加密

# 1. 铜排网格 (Inside Selection)
m3d.mesh.assign_length_mesh(
    busbar_objs,
    maxlength="20mm",
    maxel=None,
    name="Mesh_Busbars"
)

# 2. 隔板网格 (因为有涡流，需要细一点，特别是开孔附近)
m3d.mesh.assign_length_mesh(
    [plate.name],
    maxlength="10mm",
    maxel=None,
    name="Mesh_Plate"
)

# 3. 趋肤深度 (Skin Depth) 设置 - 可选，对于涡流分析很重要
# 也可以让 Maxwell 自适应去跑，但手动指定更好
m3d.mesh.assign_skin_depth(
    [plate.name],
    skin_depth="0.5mm", # 钢在50Hz下的趋肤深度大概在这个量级
    name="SkinDepth_Plate"
)

# ==========================================
# 8. 求解设置 (Setup)
# ==========================================
setup = m3d.create_setup(setupname="Setup1")
setup.props["Frequency"] = freq
setup.props["PercentError"] = 1     # 1% 能量误差
setup.props["Passes"] = 10          # 最大迭代步数
setup.props["Refine"] = 30          # 每次迭代增加 30% 网格

# 保存项目
m3d.save_project()

print("建模完成！模型已生成，电流已施加，网格已设置。请在 Maxwell 中检查并点击 Analyze。")

# 释放对象（不关闭窗口）
m3d.release_desktop(close_projects=False, close_desktop=False)
