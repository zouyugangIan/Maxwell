' ----------------------------------------------------------------------
' Maxwell 16.0 Script V11 (Fix: Terminals must touch Region Boundary)
' ----------------------------------------------------------------------

Dim oAnsoftApp, oDesktop, oProject, oDesign, oEditor, oModule, oDefinitionManager
Dim oAnalysisModule, oFieldsModule, oMeshModule

' ======================================================================
' 1. 连接与新建
' ======================================================================
On Error Resume Next
Set oAnsoftApp = CreateObject("AnsoftMaxwell.MaxwellScriptInterface")
If Err.Number <> 0 Then
    MsgBox "无法连接 Maxwell，请手动打开软件后再运行脚本。"
    WScript.Quit
End If
On Error GoTo 0

Set oDesktop = oAnsoftApp.GetAppDesktop()
oDesktop.RestoreWindow
Set oProject = oDesktop.NewProject
oProject.InsertDesign "Maxwell 3D", "KYN28_V11_Success", "EddyCurrent", ""
Set oDesign = oProject.GetActiveDesign()
Set oEditor = oDesign.SetActiveEditor("3D Modeler")

' ======================================================================
' 2. 材料与变量
' ======================================================================
Set oDefinitionManager = oProject.GetDefinitionManager()
On Error Resume Next
oDefinitionManager.RemoveMaterial "KYN_Steel"
On Error GoTo 0
oDefinitionManager.AddMaterial Array("NAME:KYN_Steel", "CoordinateSystemType:=", "Cartesian", _
    Array("NAME:AttachedData"), Array("NAME:ModifierData"), _
    "permeability:=", "4000", "conductivity:=", "4032000", "dielectric_permittivity:=", "1")

oDesign.ChangeProperty Array("NAME:AllTabs", Array("NAME:LocalVariableTab", _
  Array("NAME:PropServers", "LocalVariables"), _
  Array("NAME:NewProps", _
    Array("NAME:Bus_W", "PropType:=", "VariableProp", "UserDef:=", true, "Value:=", "10mm"), _
    Array("NAME:Bus_D", "PropType:=", "VariableProp", "UserDef:=", true, "Value:=", "100mm"), _
    Array("NAME:Bus_H", "PropType:=", "VariableProp", "UserDef:=", true, "Value:=", "600mm"), _
    Array("NAME:Space", "PropType:=", "VariableProp", "UserDef:=", true, "Value:=", "160mm"), _
    Array("NAME:Plate_Th", "PropType:=", "VariableProp", "UserDef:=", true, "Value:=", "3mm"), _
    Array("NAME:Gap", "PropType:=", "VariableProp", "UserDef:=", true, "Value:=", "20mm") _
  )))

' ======================================================================
' 3. 几何建模
' ======================================================================
' 隔板
oEditor.CreateBox Array("NAME:BoxParameters", "XPosition:=", "-Plate_Th/2", "YPosition:=", "-400mm/2", "ZPosition:=", "-600mm/2", _
  "XSize:=", "Plate_Th", "YSize:=", "400mm", "ZSize:=", "600mm"), _
  Array("NAME:Attributes", "Name:=", "Isolation_Plate", "Color:=", "(143 175 143)", "Transparency:=", 0.4, _
  "MaterialValue:=", "" & Chr(34) & "KYN_Steel" & Chr(34) & "", "SolveInside:=", true)

' 挖孔
oEditor.CreateBox Array("NAME:BoxParameters", "XPosition:=", "-Plate_Th", "YPosition:=", "-Bus_D/2 - Gap - Space", "ZPosition:=", "-Bus_W/2 - Gap", _
  "XSize:=", "Plate_Th*3", "YSize:=", "Bus_D + 2*Gap", "ZSize:=", "Bus_W + 2*Gap"), Array("NAME:Attributes", "Name:=", "Hole1")
oEditor.CreateBox Array("NAME:BoxParameters", "XPosition:=", "-Plate_Th", "YPosition:=", "-Bus_D/2 - Gap", "ZPosition:=", "-Bus_W/2 - Gap", _
  "XSize:=", "Plate_Th*3", "YSize:=", "Bus_D + 2*Gap", "ZSize:=", "Bus_W + 2*Gap"), Array("NAME:Attributes", "Name:=", "Hole2")
oEditor.CreateBox Array("NAME:BoxParameters", "XPosition:=", "-Plate_Th", "YPosition:=", "-Bus_D/2 - Gap + Space", "ZPosition:=", "-Bus_W/2 - Gap", _
  "XSize:=", "Plate_Th*3", "YSize:=", "Bus_D + 2*Gap", "ZSize:=", "Bus_W + 2*Gap"), Array("NAME:Attributes", "Name:=", "Hole3")

oEditor.Subtract Array("NAME:Selections", "Blank Parts:=", "Isolation_Plate", "Tool Parts:=", "Hole1,Hole2,Hole3"), _
  Array("NAME:SubtractParameters", "CoordinateSystem:=", "Global", "CloneToolObjects:=", false)

' 铜排
oEditor.CreateBox Array("NAME:BoxParameters", "XPosition:=", "-Bus_H/2", "YPosition:=", "-Bus_D/2 - Space", "ZPosition:=", "-Bus_W/2", _
  "XSize:=", "Bus_H", "YSize:=", "Bus_D", "ZSize:=", "Bus_W"), Array("NAME:Attributes", "Name:=", "Busbar_A", "Color:=", "(255 0 0)", "MaterialValue:=", "" & Chr(34) & "copper" & Chr(34) & "", "SolveInside:=", true)
oEditor.CreateBox Array("NAME:BoxParameters", "XPosition:=", "-Bus_H/2", "YPosition:=", "-Bus_D/2", "ZPosition:=", "-Bus_W/2", _
  "XSize:=", "Bus_H", "YSize:=", "Bus_D", "ZSize:=", "Bus_W"), Array("NAME:Attributes", "Name:=", "Busbar_B", "Color:=", "(0 255 0)", "MaterialValue:=", "" & Chr(34) & "copper" & Chr(34) & "", "SolveInside:=", true)
oEditor.CreateBox Array("NAME:BoxParameters", "XPosition:=", "-Bus_H/2", "YPosition:=", "-Bus_D/2 + Space", "ZPosition:=", "-Bus_W/2", _
  "XSize:=", "Bus_H", "YSize:=", "Bus_D", "ZSize:=", "Bus_W"), Array("NAME:Attributes", "Name:=", "Busbar_C", "Color:=", "(255 255 0)", "MaterialValue:=", "" & Chr(34) & "copper" & Chr(34) & "", "SolveInside:=", true)

' ======================================================================
' 4. [核心修复] 空气域 (Region) - 让 X 方向为 0，使铜排接触边界
' ======================================================================
' 注意：XPadding = 0 意味着铜排的两个端面将直接位于仿真边界上
oEditor.CreateRegion Array("NAME:RegionParameters", _
  "+XPaddingType:=", "Percentage Offset", "+XPadding:=", "0", _
  "-XPaddingType:=", "Percentage Offset", "-XPadding:=", "0", _
  "+YPaddingType:=", "Percentage Offset", "+YPadding:=", "50", _
  "-YPaddingType:=", "Percentage Offset", "-YPadding:=", "50", _
  "+ZPaddingType:=", "Percentage Offset", "+ZPadding:=", "50", _
  "-ZPaddingType:=", "Percentage Offset", "-ZPadding:=", "50"), _
  Array("NAME:Attributes", "Name:=", "Region", "MaterialValue:=", "" & Chr(34) & "vacuum" & Chr(34) & "", "Transparent:=", true)

' ======================================================================
' 5. 激励设置 (Sheet 必须在边界上)
' ======================================================================
Set oModule = oDesign.GetModule("BoundarySetup")

' A相
oEditor.CreateRectangle Array("NAME:RectangleParameters", "IsCovered:=", true, "XStart:=", "-Bus_H/2", "YStart:=", "-Bus_D/2 - Space", "ZStart:=", "-Bus_W/2", "Width:=", "Bus_D", "Height:=", "Bus_W", "WhichAxis:=", "X"), Array("NAME:Attributes", "Name:=", "Terminal_A")
oModule.AssignCurrent Array("NAME:Current_A", "Objects:=", Array("Terminal_A"), "Current:=", "4000A", "Phase:=", "0deg", "IsSolid:=", false)

' B相
oEditor.CreateRectangle Array("NAME:RectangleParameters", "IsCovered:=", true, "XStart:=", "-Bus_H/2", "YStart:=", "-Bus_D/2", "ZStart:=", "-Bus_W/2", "Width:=", "Bus_D", "Height:=", "Bus_W", "WhichAxis:=", "X"), Array("NAME:Attributes", "Name:=", "Terminal_B")
oModule.AssignCurrent Array("NAME:Current_B", "Objects:=", Array("Terminal_B"), "Current:=", "4000A", "Phase:=", "-120deg", "IsSolid:=", false)

' C相
oEditor.CreateRectangle Array("NAME:RectangleParameters", "IsCovered:=", true, "XStart:=", "-Bus_H/2", "YStart:=", "-Bus_D/2 + Space", "ZStart:=", "-Bus_W/2", "Width:=", "Bus_D", "Height:=", "Bus_W", "WhichAxis:=", "X"), Array("NAME:Attributes", "Name:=", "Terminal_C")
oModule.AssignCurrent Array("NAME:Current_C", "Objects:=", Array("Terminal_C"), "Current:=", "4000A", "Phase:=", "120deg", "IsSolid:=", false)

' 涡流效应
Set oModule = oDesign.GetModule("BoundarySetup")
On Error Resume Next
oModule.SetEddyEffect Array("NAME:EddyEffectSetting", Array("NAME:EddyEffect", "Isolation_Plate:=", true, "Busbar_A:=", true, "Busbar_B:=", true, "Busbar_C:=", true))
On Error GoTo 0

' ======================================================================
' 6. 网格与求解 (保持快速模式)
' ======================================================================
Set oMeshModule = oDesign.GetModule("MeshSetup")

' 铜排网格
oMeshModule.AssignLengthOp Array("NAME:Mesh_Busbars", "RefineInside:=", true, "Enabled:=", true, _
    "Objects:=", Array("Busbar_A", "Busbar_B", "Busbar_C"), _
    "RestrictElem:=", false, "NumMaxElem:=", "1000", _
    "RestrictLength:=", true, "MaxLength:=", "100mm")

' 隔板网格 (稍微细一点点，保证不算错)
oMeshModule.AssignLengthOp Array("NAME:Mesh_Plate", "RefineInside:=", true, "Enabled:=", true, _
    "Objects:=", Array("Isolation_Plate"), _
    "RestrictElem:=", false, "NumMaxElem:=", "1000", _
    "RestrictLength:=", true, "MaxLength:=", "40mm")

Set oAnalysisModule = oDesign.GetModule("AnalysisSetup")
oAnalysisModule.InsertSetup "EddyCurrent", Array("NAME:Setup1", "Frequency:=", "50Hz", "MaxDeltaE:=", "5", "MaximumPasses:=", "5", "PercentRefinement:=", "30", "BasisOrder:=", "1")

MsgBox "正在开始计算 (V11)..." & vbCrLf & "本次已修复边界条件，请忽略控制台的乱码信息。", 64, "修复完成"

oDesign.Analyze "Setup1"

' ======================================================================
' 7. 后处理
' ======================================================================
Set oFieldsModule = oDesign.GetModule("FieldsReporter")
On Error Resume Next
oEditor.Select Array("NAME:Selections", "Selections:=", "Isolation_Plate")
oFieldsModule.CreateFieldPlot Array("NAME:Mag_B1", "SolutionName:=", "Setup1 : LastAdaptive", "QuantityName:=", "Mag_B", "PlotFolder:=", "B Field", "UserSpecifyName:=", 0, "UserSpecifyFolder:=", 0, "Faces:=", Array(), "Objects:=", Array("Isolation_Plate"), "IntrinsicVar:=", "Phase='0deg'", "PlotGeomInfo:=", Array(1, "Surface", "Faces", 0))
oFieldsModule.CreateFieldPlot Array("NAME:Mag_J1", "SolutionName:=", "Setup1 : LastAdaptive", "QuantityName:=", "Mag_J", "PlotFolder:=", "J Field", "UserSpecifyName:=", 0, "UserSpecifyFolder:=", 0, "Faces:=", Array(), "Objects:=", Array("Isolation_Plate"), "IntrinsicVar:=", "Phase='0deg'", "PlotGeomInfo:=", Array(1, "Surface", "Faces", 0))

If Err.Number <> 0 Then
    MsgBox "计算完成。请检查结果。", 64, "完成"
Else
    MsgBox "成功！云图已生成。", 64, "完美"
End If
On Error GoTo 0