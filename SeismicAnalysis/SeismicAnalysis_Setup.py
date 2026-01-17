"""
SeismicAnalysis_Setup.py - KYN28 开关柜抗震分析计算器
================================================================================
【功能说明】
本脚本计算地震载荷参数，并输出 Workbench Mechanical 操作指南。

【KYN28 抗震设计参数】
- Standard (GB 50011-2010): 水平 0.40g / 竖向 0.26g
- Nuclear (高烈度): 水平 7.80g / 竖向 5.07g

【高性能计算配置】
- CPU: 8核 Distributed 并行
- GPU: NVIDIA 加速

【使用方法】
python SeismicAnalysis_Setup.py
"""

import os

# ======================================================================
# 配置
# ======================================================================
GRAVITY = 9806.6  # mm/s^2 (1g)

# HPC 配置
CPU_CORES = 8
GPU_TYPE = "NVIDIA"

# ======================================================================
# 载荷计算
# ======================================================================
def get_seismic_loads(mode="Standard"):
    """计算不同模式下的等效加速度 (单位: mm/s^2)"""
    if mode == "Nuclear":
        h_g = 7.8
        v_g = 7.8 * 0.65
        desc = "Nuclear High-G (SSE Limit)"
    else:
        h_g = 0.4
        v_g = 0.4 * 0.65
        desc = "Standard GB50011 (8度烈度)"
    
    return {
        "description": desc,
        "H_G": h_g,
        "V_G": v_g,
        "Accel_H": h_g * GRAVITY,
        "Accel_V": v_g * GRAVITY
    }

# ======================================================================
# 主程序
# ======================================================================
if __name__ == "__main__":
    print("="*70)
    print(" KYN28 开关柜抗震分析 - 载荷计算器")
    print("="*70)
    
    # 用户选择模式
    print("\n请选择载荷模式:")
    print("  1. Standard (0.4g) - 民用 8度烈度")
    print("  2. Nuclear (7.8g)  - 核电极限工况")
    choice = input("\n输入选项 [1/2] (默认1): ").strip()
    
    mode = "Nuclear" if choice == "2" else "Standard"
    loads = get_seismic_loads(mode)
    
    print(f"\n" + "="*70)
    print(f" 载荷计算结果: {loads['description']}")
    print("="*70)
    print(f"\n  水平加速度: {loads['H_G']} g = {loads['Accel_H']:.1f} mm/s^2")
    print(f"  竖向加速度: {loads['V_G']:.2f} g = {loads['Accel_V']:.1f} mm/s^2")
    
    # 操作指南
    print("\n" + "="*70)
    print("【Workbench 操作步骤】")
    print("="*70)
    print("""
1. 创建分析: 拖拽 "静态结构" 到项目窗口
2. 导入几何: 右键 "几何" → Browse
3. 进入 Mechanical: 双击 "模型"
4. 划分网格: Mesh → 右键 → Generate Mesh
5. 施加载荷:""")
    print(f"   - Standard Earth Gravity: -Z")
    print(f"   - Acceleration: X = {loads['Accel_H']:.1f}, Z = {loads['Accel_V']:.1f} mm/s^2")
    print(f"   - Fixed Support: 柜体底面")
    
    print("\n" + "="*70)
    print("【高性能计算设置 (Distributed + GPU)】")
    print("="*70)
    print(f"""
路径: Tools → Solve Process Settings → My Computer → Advanced...

┌──────────────────────────────────────────────┐
│ Solver Process Settings                      │
│                                              │
│ ☑ Distribute Solution (if possible)         │
│                                              │
│ Max number of utilized cores: {CPU_CORES}              │
│                                              │
│ Additional Command Line Arguments:           │
│   -acc nvidia -na 1                          │
│                                              │
│ (上述参数启用 {GPU_TYPE} GPU 加速)              │
└──────────────────────────────────────────────┘

注意事项:
- Distributed 模式需要 ANSYS HPC 许可证
- 无 HPC 许可证时最多使用 4 核
- GPU 加速需要 NVIDIA CUDA 兼容显卡
- 参数 -acc nvidia 启用 GPU, -na 1 表示使用 1 块 GPU
""")
    print("="*70)
    print(" 完成! 按上述步骤操作，然后 Solve 求解。")
    print("="*70)
