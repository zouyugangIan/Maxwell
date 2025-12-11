' ======================================================================
' TransientTrip.vbs - Circuit Breaker Fast-Acting Trip Simulation
' 断路器快速动作脱扣器的仿真及测试研究
' ======================================================================

Dim oAnsoftApp, oDesktop, oProject, oDesign, oEditor, oModule
Dim oAnalysisModule

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
' 1. Insert Transient Design
oProject.InsertDesign "Maxwell 3D", "Breaker_Trip_Demo", "Transient", ""
Set oDesign = oProject.GetActiveDesign()
Set oEditor = oDesign.SetActiveEditor("3D Modeler")

' 2. Geometry (Simple Solenoid Demo)
' 线圈 (Coil)
oEditor.CreateCylinder Array("NAME:CylinderParameters", "XCenter:=", "0mm", "YCenter:=", "0mm", "ZCenter:=", "0mm", "Radius:=", "20mm", "Height:=", "50mm", "WhichAxis:=", "Z"), Array("NAME:Attributes", "Name:=", "Coil", "MaterialValue:=", "" & Chr(34) & "copper" & Chr(34) & "", "Transparent:=", true)
' 动铁芯 (Plunger / Moving Part)
oEditor.CreateCylinder Array("NAME:CylinderParameters", "XCenter:=", "0mm", "YCenter:=", "0mm", "ZCenter:=", "10mm", "Radius:=", "10mm", "Height:=", "40mm", "WhichAxis:=", "Z"), Array("NAME:Attributes", "Name:=", "Plunger", "MaterialValue:=", "" & Chr(34) & "iron" & Chr(34) & "")

' Region
oEditor.CreateRegion Array("NAME:RegionParameters", "+XPaddingType:=", "Percentage Offset", "+XPadding:=", "100", "-XPaddingType:=", "Percentage Offset", "-XPadding:=", "100", "+YPaddingType:=", "Percentage Offset", "+YPadding:=", "100", "-YPaddingType:=", "Percentage Offset", "-YPadding:=", "100", "+ZPaddingType:=", "Percentage Offset", "+ZPadding:=", "100", "-ZPaddingType:=", "Percentage Offset", "-ZPadding:=", "100"), Array("NAME:Attributes", "Name:=", "Region", "MaterialValue:=", "" & Chr(34) & "vacuum" & Chr(34) & "")

' 3. Excitations (Winding)
Set oModule = oDesign.GetModule("BoundarySetup")
' Creating a section to apply current
oEditor.CreateRectangle Array("NAME:RectangleParameters", "IsCovered:=", true, "XStart:=", "0mm", "YStart:=", "0mm", "ZStart:=", "0mm", "Width:=", "20mm", "Height:=", "50mm", "WhichAxis:=", "Y"), Array("NAME:Attributes", "Name:=", "Coil_Section")
oModule.AssignWindingGroup Array("NAME:Winding1", "Type:=", "Current", "IsSolid:=", true, "Current:=", "100A")
oModule.AssignCoilTerminal Array("NAME:CoilTerminal1", "Objects:=", Array("Coil_Section"), "Conductor number:=", "100", "Point out of terminal:=", false, "Winding:=", "Winding1")

' 4. Motion Setup (Band) - Maxwell Transient Requires a Motion Band for moving parts
' Note: This is an advanced feature. For this demo, we just set up the solver without motion band to avoid band errors if geometry is not perfect.
' The user can add Band in Maxwell GUI: Model -> Motion Setup -> Assign Band.

' 5. Analysis Setup
Set oAnalysisModule = oDesign.GetModule("AnalysisSetup")
oAnalysisModule.InsertSetup "Transient", Array("NAME:Setup1", "StopTime:=", "0.02s", "TimeStep:=", "0.001s")

MsgBox "✅ 瞬态分析模板已建立！" & vbCrLf & "Solver: Transient" & vbCrLf & "Model: Simplified Solenoid (Coil + Plunger)." & vbCrLf & "注意：'运动(Motion)'设置较复杂，请在图形界面中手动添加 Band (Motion Region)。", 64, "Transient Ready"