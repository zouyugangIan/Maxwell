' ----------------------------------------------------------------------
' Maxwell 16.0 Script: View Ohmic Loss (Heat)
' ----------------------------------------------------------------------
Dim oAnsoftApp, oDesktop, oDesign, oEditor, oFields

On Error Resume Next
Set oAnsoftApp = CreateObject("AnsoftMaxwell.MaxwellScriptInterface")
Set oDesktop = oAnsoftApp.GetAppDesktop()
Set oDesign = oDesktop.GetActiveProject().GetActiveDesign()
Set oEditor = oDesign.SetActiveEditor("3D Modeler")
Set oFields = oDesign.GetModule("FieldsReporter")
On Error GoTo 0

' 1. 隐藏铜排
On Error Resume Next
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:Geometry3DAttributeTab", Array("NAME:PropServers", "Busbar_A", "Busbar_B", "Busbar_C"), Array("NAME:ChangedProps", Array("NAME:Transparent", "Value:=", 1))))
On Error GoTo 0

' 2. 清理旧图
On Error Resume Next
oFields.DeleteFieldPlot Array("Loss_Plate")
On Error GoTo 0

' 3. 创建 Ohmic Loss 云图
oFields.CreateFieldPlot Array("NAME:Loss_Plate", "SolutionName:=", "Setup1 : LastAdaptive", "QuantityName:=", "Ohmic Loss", "PlotFolder:=", "Other", "UserSpecifyName:=", 0, "UserSpecifyFolder:=", 0, "Faces:=", Array(), "Objects:=", Array("Isolation_Plate"), "IntrinsicVar:=", "Phase='0deg'", "PlotGeomInfo:=", Array(1, "Surface", "Faces", 0))

MsgBox "✅ 损耗云图已生成！" & vbCrLf & "红色的区域就是发热最严重（涡流最大）的地方。" & vbCrLf & "如果要恢复显示铜排，请按 Ctrl + Shift + H。", 64, "View Loss"