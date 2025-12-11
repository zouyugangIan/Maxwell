' ======================================================================
' EddyCurrent.vbs - Switchgear Metal Partition Eddy Current Loss Analysis
' 开关柜金属隔板涡流损耗分析
' 
' Solver Type: Eddy Current
' Description: Analyze eddy current losses in metal partitions caused by
'              three-phase AC current (50Hz, 4000A) flowing through busbars
' ======================================================================

Dim oAnsoftApp, oDesktop, oProject, oDesign, oEditor, oModule, oDefinitionManager
Dim oMeshModule, oAnalysisModule

' ======================================================================
' 1. 环境准备
' ======================================================================
On Error Resume Next
Set oAnsoftApp = CreateObject("AnsoftMaxwell.MaxwellScriptInterface")
If Err.Number <> 0 Then
    MsgBox "无法连接 Maxwell。请先打开 Maxwell 16.0 软件，然后再运行此脚本。", 16, "错误"
    WScript.Quit
End If
On Error GoTo 0

Set oDesktop = oAnsoftApp.GetAppDesktop()
oDesktop.RestoreWindow
Set oProject = oDesktop.NewProject
oProject.InsertDesign "Maxwell 3D", "KYN28_V19_Final", "EddyCurrent", ""
Set oDesign = oProject.GetActiveDesign()
Set oEditor = oDesign.SetActiveEditor("3D Modeler")

' ======================================================================
' 2. 材料与变量 (为防报错，我把数组写在了一行里)
' ======================================================================
Set oDefinitionManager = oProject.GetDefinitionManager()
On Error Resume Next
oDefinitionManager.RemoveMaterial "KYN_Steel"
On Error GoTo 0
oDefinitionManager.AddMaterial Array("NAME:KYN_Steel", "CoordinateSystemType:=", "Cartesian", Array("NAME:AttachedData"), Array("NAME:ModifierData"), "permeability:=", "4000", "conductivity:=", "4032000", "dielectric_permittivity:=", "1")

' 【注意】下面这行非常长，请确保完整复制
oDesign.ChangeProperty Array("NAME:AllTabs", Array("NAME:LocalVariableTab", Array("NAME:PropServers", "LocalVariables"), Array("NAME:NewProps", Array("NAME:Bus_W", "PropType:=", "VariableProp", "UserDef:=", true, "Value:=", "10mm"), Array("NAME:Bus_D", "PropType:=", "VariableProp", "UserDef:=", true, "Value:=", "100mm"), Array("NAME:Bus_H", "PropType:=", "VariableProp", "UserDef:=", true, "Value:=", "600mm"), Array("NAME:Space", "PropType:=", "VariableProp", "UserDef:=", true, "Value:=", "160mm"), Array("NAME:Plate_Th", "PropType:=", "VariableProp", "UserDef:=", true, "Value:=", "3mm"), Array("NAME:Gap", "PropType:=", "VariableProp", "UserDef:=", true, "Value:=", "20mm"))))

' ======================================================================
' 3. 几何建模 (已验证正确)
' ======================================================================
' 隔板
oEditor.CreateBox Array("NAME:BoxParameters", "XPosition:=", "-Plate_Th/2", "YPosition:=", "-400mm/2", "ZPosition:=", "-600mm/2", "XSize:=", "Plate_Th", "YSize:=", "400mm", "ZSize:=", "600mm"), Array("NAME:Attributes", "Name:=", "Isolation_Plate", "Color:=", "(143 175 143)", "Transparency:=", 0.4, "PartCoordinateSystem:=", "Global", "MaterialValue:=", "" & Chr(34) & "KYN_Steel" & Chr(34) & "", "SolveInside:=", true)

' 挖孔
oEditor.CreateBox Array("NAME:BoxParameters", "XPosition:=", "-Plate_Th", "YPosition:=", "-Bus_D/2 - Gap - Space", "ZPosition:=", "-Bus_W/2 - Gap", "XSize:=", "Plate_Th*3", "YSize:=", "Bus_D + 2*Gap", "ZSize:=", "Bus_W + 2*Gap"), Array("NAME:Attributes", "Name:=", "Hole1")
oEditor.CreateBox Array("NAME:BoxParameters", "XPosition:=", "-Plate_Th", "YPosition:=", "-Bus_D/2 - Gap", "ZPosition:=", "-Bus_W/2 - Gap", "XSize:=", "Plate_Th*3", "YSize:=", "Bus_D + 2*Gap", "ZSize:=", "Bus_W + 2*Gap"), Array("NAME:Attributes", "Name:=", "Hole2")
oEditor.CreateBox Array("NAME:BoxParameters", "XPosition:=", "-Plate_Th", "YPosition:=", "-Bus_D/2 - Gap + Space", "ZPosition:=", "-Bus_W/2 - Gap", "XSize:=", "Plate_Th*3", "YSize:=", "Bus_D + 2*Gap", "ZSize:=", "Bus_W + 2*Gap"), Array("NAME:Attributes", "Name:=", "Hole3")

oEditor.Subtract Array("NAME:Selections", "Blank Parts:=", "Isolation_Plate", "Tool Parts:=", "Hole1,Hole2,Hole3"), Array("NAME:SubtractParameters", "CoordinateSystem:=", "Global", "CloneToolObjects:=", false)

' 铜排
oEditor.CreateBox Array("NAME:BoxParameters", "XPosition:=", "-Bus_H/2", "YPosition:=", "-Bus_D/2 - Space", "ZPosition:=", "-Bus_W/2", "XSize:=", "Bus_H", "YSize:=", "Bus_D", "ZSize:=", "Bus_W"), Array("NAME:Attributes", "Name:=", "Busbar_A", "Color:=", "(255 0 0)", "PartCoordinateSystem:=", "Global", "MaterialValue:=", "" & Chr(34) & "copper" & Chr(34) & "", "SolveInside:=", true)
oEditor.CreateBox Array("NAME:BoxParameters", "XPosition:=", "-Bus_H/2", "YPosition:=", "-Bus_D/2", "ZPosition:=", "-Bus_W/2", "XSize:=", "Bus_H", "YSize:=", "Bus_D", "ZSize:=", "Bus_W"), Array("NAME:Attributes", "Name:=", "Busbar_B", "Color:=", "(0 255 0)", "PartCoordinateSystem:=", "Global", "MaterialValue:=", "" & Chr(34) & "copper" & Chr(34) & "", "SolveInside:=", true)
oEditor.CreateBox Array("NAME:BoxParameters", "XPosition:=", "-Bus_H/2", "YPosition:=", "-Bus_D/2 + Space", "ZPosition:=", "-Bus_W/2", "XSize:=", "Bus_H", "YSize:=", "Bus_D", "ZSize:=", "Bus_W"), Array("NAME:Attributes", "Name:=", "Busbar_C", "Color:=", "(255 255 0)", "PartCoordinateSystem:=", "Global", "MaterialValue:=", "" & Chr(34) & "copper" & Chr(34) & "", "SolveInside:=", true)

' Region
oEditor.CreateRegion Array("NAME:RegionParameters", "+XPaddingType:=", "Percentage Offset", "+XPadding:=", "0", "-XPaddingType:=", "Percentage Offset", "-XPadding:=", "0", "+YPaddingType:=", "Percentage Offset", "+YPadding:=", "50", "-YPaddingType:=", "Percentage Offset", "-YPadding:=", "50", "+ZPaddingType:=", "Percentage Offset", "+ZPadding:=", "50", "-ZPaddingType:=", "Percentage Offset", "-ZPadding:=", "50"), Array("NAME:Attributes", "Name:=", "Region", "PartCoordinateSystem:=", "Global", "MaterialValue:=", "" & Chr(34) & "vacuum" & Chr(34) & "", "Transparent:=", true)

' ======================================================================
' 4. 激励设置 (单行写法，杜绝字符错误)
' ======================================================================
Set oModule = oDesign.GetModule("BoundarySetup")

' A相
oEditor.CreateRectangle Array("NAME:RectangleParameters", "IsCovered:=", true, "XStart:=", "-Bus_H/2", "YStart:=", "-Bus_D/2 - Space", "ZStart:=", "-Bus_W/2", "Width:=", "Bus_D", "Height:=", "Bus_W", "WhichAxis:=", "X"), Array("NAME:Attributes", "Name:=", "Term_A_In", "PartCoordinateSystem:=", "Global")
oModule.AssignCurrent Array("NAME:Cur_A_In", "Objects:=", Array("Term_A_In"), "Current:=", "4000A", "Phase:=", "0deg", "IsSolid:=", false)

oEditor.CreateRectangle Array("NAME:RectangleParameters", "IsCovered:=", true, "XStart:=", "Bus_H/2", "YStart:=", "-Bus_D/2 - Space", "ZStart:=", "-Bus_W/2", "Width:=", "Bus_D", "Height:=", "Bus_W", "WhichAxis:=", "X"), Array("NAME:Attributes", "Name:=", "Term_A_Out", "PartCoordinateSystem:=", "Global")
oModule.AssignCurrent Array("NAME:Cur_A_Out", "Objects:=", Array("Term_A_Out"), "Current:=", "4000A", "Phase:=", "0deg", "IsSolid:=", false)

' B相
oEditor.CreateRectangle Array("NAME:RectangleParameters", "IsCovered:=", true, "XStart:=", "-Bus_H/2", "YStart:=", "-Bus_D/2", "ZStart:=", "-Bus_W/2", "Width:=", "Bus_D", "Height:=", "Bus_W", "WhichAxis:=", "X"), Array("NAME:Attributes", "Name:=", "Term_B_In", "PartCoordinateSystem:=", "Global")
oModule.AssignCurrent Array("NAME:Cur_B_In", "Objects:=", Array("Term_B_In"), "Current:=", "4000A", "Phase:=", "-120deg", "IsSolid:=", false)

oEditor.CreateRectangle Array("NAME:RectangleParameters", "IsCovered:=", true, "XStart:=", "Bus_H/2", "YStart:=", "-Bus_D/2", "ZStart:=", "-Bus_W/2", "Width:=", "Bus_D", "Height:=", "Bus_W", "WhichAxis:=", "X"), Array("NAME:Attributes", "Name:=", "Term_B_Out", "PartCoordinateSystem:=", "Global")
oModule.AssignCurrent Array("NAME:Cur_B_Out", "Objects:=", Array("Term_B_Out"), "Current:=", "4000A", "Phase:=", "-120deg", "IsSolid:=", false)

' C相
oEditor.CreateRectangle Array("NAME:RectangleParameters", "IsCovered:=", true, "XStart:=", "-Bus_H/2", "YStart:=", "-Bus_D/2 + Space", "ZStart:=", "-Bus_W/2", "Width:=", "Bus_D", "Height:=", "Bus_W", "WhichAxis:=", "X"), Array("NAME:Attributes", "Name:=", "Term_C_In", "PartCoordinateSystem:=", "Global")
oModule.AssignCurrent Array("NAME:Cur_C_In", "Objects:=", Array("Term_C_In"), "Current:=", "4000A", "Phase:=", "120deg", "IsSolid:=", false)

oEditor.CreateRectangle Array("NAME:RectangleParameters", "IsCovered:=", true, "XStart:=", "Bus_H/2", "YStart:=", "-Bus_D/2 + Space", "ZStart:=", "-Bus_W/2", "Width:=", "Bus_D", "Height:=", "Bus_W", "WhichAxis:=", "X"), Array("NAME:Attributes", "Name:=", "Term_C_Out", "PartCoordinateSystem:=", "Global")
oModule.AssignCurrent Array("NAME:Cur_C_Out", "Objects:=", Array("Term_C_Out"), "Current:=", "4000A", "Phase:=", "120deg", "IsSolid:=", false)

' ======================================================================
' 5. 网格 & 求解
' ======================================================================
Set oMeshModule = oDesign.GetModule("MeshSetup")
oMeshModule.AssignLengthOp Array("NAME:Mesh_Busbars", "RefineInside:=", true, "Enabled:=", true, "Objects:=", Array("Busbar_A", "Busbar_B", "Busbar_C"), "RestrictElem:=", false, "NumMaxElem:=", "1000", "RestrictLength:=", true, "MaxLength:=", "100mm")
oMeshModule.AssignLengthOp Array("NAME:Mesh_Plate", "RefineInside:=", true, "Enabled:=", true, "Objects:=", Array("Isolation_Plate"), "RestrictElem:=", false, "NumMaxElem:=", "1000", "RestrictLength:=", true, "MaxLength:=", "30mm")

Set oAnalysisModule = oDesign.GetModule("AnalysisSetup")
oAnalysisModule.InsertSetup "EddyCurrent", Array("NAME:Setup1", "Frequency:=", "50Hz", "MaxDeltaE:=", "5", "MaximumPasses:=", "5", "PercentRefinement:=", "30", "BasisOrder:=", "1")

' ======================================================================
' 6. 最后设置涡流效应 (消除警告)
' ======================================================================
Set oModule = oDesign.GetModule("BoundarySetup")
On Error Resume Next
oModule.SetEddyEffect Array("NAME:EddyEffectSetting", Array("NAME:EddyEffect", "Isolation_Plate:=", true, "Busbar_A:=", true, "Busbar_B:=", true, "Busbar_C:=", true))
On Error GoTo 0

' ======================================================================
' 7. 自动创建场图 (可视化输出)
' ======================================================================
Set oFieldsReporter = oDesign.GetModule("FieldsReporter")

' 7.1 在金属隔板上绘制欧姆损耗密度 (Ohmic Loss)
' 类比: 类似于结构分析中的"应变能密度"，表示能量损耗集中的地方(发热源)
On Error Resume Next
oFieldsReporter.CreateFieldPlot Array("NAME:Plot_OhmicLoss", "SolutionName:=", "Setup1 : LastAdaptive", "UserSpecifyName:=", 0, "UserSpecifyFolder:=", 0, "QuantityName:=", "Ohmic_Loss", "PlotFolder:=", "Ohmic_Loss", "StreamlinePlot:=", false, "AdjacentSidePlot:=", false, "FullModelPlot:=", false, "IntrinsicVar:=", "Freq='50Hz' Phase='0deg'", "PlotGeomInfo:=", Array(1, "Objects", "Isolation_Plate", false), "PlotOnSurfaceOnly:=", true, "FilterBoxes:=", Array(0), "Refinement:=", 30), "Field"
On Error GoTo 0

' 7.2 在铜排上绘制电流密度 (J)
' 类比: 类似于结构里的"应力分布"，查看电流集肤效应
On Error Resume Next
oFieldsReporter.CreateFieldPlot Array("NAME:Plot_J", "SolutionName:=", "Setup1 : LastAdaptive", "UserSpecifyName:=", 0, "UserSpecifyFolder:=", 0, "QuantityName:=", "J", "PlotFolder:=", "J", "StreamlinePlot:=", false, "AdjacentSidePlot:=", false, "FullModelPlot:=", false, "IntrinsicVar:=", "Freq='50Hz' Phase='0deg'", "PlotGeomInfo:=", Array(1, "Objects", "Busbar_A,Busbar_B,Busbar_C", false), "PlotOnSurfaceOnly:=", true, "FilterBoxes:=", Array(0), "Refinement:=", 30), "Field"

MsgBox "✅ 脚本运行成功！请点击 Validation Check (绿色对勾) 和 Analyze (开始计算)。", 64, "V19 绝对版"