' ======================================================================
' ElectrostaticField.vbs - Switchgear Electric Field Simulation Analysis
' 开关柜电场仿真分析
' ======================================================================

Dim oAnsoftApp, oDesktop, oProject, oDesign, oEditor, oModule
Dim oMeshModule, oAnalysisModule

On Error Resume Next
Set oAnsoftApp = CreateObject("AnsoftMaxwell.MaxwellScriptInterface")
If Err.Number <> 0 Then
    MsgBox "无法连接 Maxwell。请先打开 Maxwell 16.0 软件。", 16, "错误"
    WScript.Quit
End If
On Error GoTo 0

Set oDesktop = oAnsoftApp.GetAppDesktop()
oDesktop.RestoreWindow
Set oProject = oDesktop.NewProject
' 1. Insert Electrostatic Design
oProject.InsertDesign "Maxwell 3D", "KYN28_Electrostatic", "Electrostatic", ""
Set oDesign = oProject.GetActiveDesign()
Set oEditor = oDesign.SetActiveEditor("3D Modeler")

' 2. Geometry (Simplified for Demo: Busbar + Ground Wall)
' 铜排 (High Voltage)
oEditor.CreateBox Array("NAME:BoxParameters", "XPosition:=", "-5mm", "YPosition:=", "-50mm", "ZPosition:=", "-300mm", "XSize:=", "10mm", "YSize:=", "100mm", "ZSize:=", "600mm"), Array("NAME:Attributes", "Name:=", "Busbar_HV", "Color:=", "(255 0 0)", "MaterialValue:=", "" & Chr(34) & "copper" & Chr(34) & "")

' 柜体 (Ground)
oEditor.CreateBox Array("NAME:BoxParameters", "XPosition:=", "-200mm", "YPosition:=", "-200mm", "ZPosition:=", "-300mm", "XSize:=", "400mm", "YSize:=", "400mm", "ZSize:=", "600mm"), Array("NAME:Attributes", "Name:=", "Cabinet_GND", "Color:=", "(128 128 128)", "Transparent:=", true)

' 空气域 (Region)
oEditor.CreateRegion Array("NAME:RegionParameters", "+XPaddingType:=", "Percentage Offset", "+XPadding:=", "20", "-XPaddingType:=", "Percentage Offset", "-XPadding:=", "20", "+YPaddingType:=", "Percentage Offset", "+YPadding:=", "20", "-YPaddingType:=", "Percentage Offset", "-YPadding:=", "20", "+ZPaddingType:=", "Percentage Offset", "+ZPadding:=", "0", "-ZPaddingType:=", "Percentage Offset", "-ZPadding:=", "0"), Array("NAME:Attributes", "Name:=", "Region", "MaterialValue:=", "" & Chr(34) & "vacuum" & Chr(34) & "", "Transparent:=", true)

' 3. Excitations (Voltage)
Set oModule = oDesign.GetModule("BoundarySetup")
' Busbar = 10kV
oModule.AssignVoltage Array("NAME:Volt_HV", "Objects:=", Array("Busbar_HV"), "Voltage:=", "10kV")
' Cabinet = 0V
oModule.AssignVoltage Array("NAME:Volt_GND", "Objects:=", Array("Cabinet_GND"), "Voltage:=", "0V")

' 4. Analysis Setup
Set oAnalysisModule = oDesign.GetModule("AnalysisSetup")
oAnalysisModule.InsertSetup "Electrostatic", Array("NAME:Setup1", "MaximumPasses:=", "10", "PercentError:=", "1")

' 5. Field Plot (Electric Field Vector)
Set oFieldsReporter = oDesign.GetModule("FieldsReporter")
On Error Resume Next
oFieldsReporter.CreateFieldPlot Array("NAME:Plot_E_Vector", "SolutionName:=", "Setup1 : LastAdaptive", "QuantityName:=", "Vector_E", "PlotFolder:=", "E_Field", "PlotGeomInfo:=", Array(1, "Objects", "Region", false), "PlotOnSurfaceOnly:=", false), "Field"
On Error GoTo 0

MsgBox "✅ 电场分析脚本运行完成！" & vbCrLf & "Solver: Electrostatic" & vbCrLf & "Excitations: 10kV on Busbar, 0V on Cabinet.", 64, "Electrostatic Ready"