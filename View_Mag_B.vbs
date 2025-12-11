' ----------------------------------------------------------------------
' Maxwell 16.0 Script: View B Field (Auto Scale & Hide Busbars)
' ----------------------------------------------------------------------
Dim oAnsoftApp, oDesktop, oDesign, oEditor, oFields

On Error Resume Next
Set oAnsoftApp = CreateObject("AnsoftMaxwell.MaxwellScriptInterface")
Set oDesktop = oAnsoftApp.GetAppDesktop()
Set oDesign = oDesktop.GetActiveProject().GetActiveDesign()
Set oEditor = oDesign.SetActiveEditor("3D Modeler")
Set oFields = oDesign.GetModule("FieldsReporter")
On Error GoTo 0

' 1. 隐藏铜排 (设置透明度为 1)
' 这样你可以直接看清隔板，不用手动按 Ctrl+H
On Error Resume Next
oEditor.ChangeProperty Array("NAME:AllTabs", Array("NAME:Geometry3DAttributeTab", Array("NAME:PropServers", "Busbar_A", "Busbar_B", "Busbar_C"), Array("NAME:ChangedProps", Array("NAME:Transparent", "Value:=", 1))))
On Error GoTo 0

' 2. 清理旧图 (防止重叠)
On Error Resume Next
oFields.DeleteFieldPlot Array("Mag_B_Plate")
On Error GoTo 0

' 3. 创建 Mag_B 云图
oFields.CreateFieldPlot Array("NAME:Mag_B_Plate", "SolutionName:=", "Setup1 : LastAdaptive", "QuantityName:=", "Mag_B", "PlotFolder:=", "B Field", "UserSpecifyName:=", 0, "UserSpecifyFolder:=", 0, "Faces:=", Array(), "Objects:=", Array("Isolation_Plate"), "IntrinsicVar:=", "Phase='0deg'", "PlotGeomInfo:=", Array(1, "Surface", "Faces", 0))

' 4. 尝试自动调整标尺 (0 ~ 0.5T)
' 如果版本兼容性允许，这一步会自动把红色设为 0.5T，蓝色设为 0
On Error Resume Next
oFields.SetFieldPlotSettings "Mag_B_Plate", Array("Color Map", "Scale 3D", "Auto Scale:=", false, "Min:=", "0", "Max:=", "0.5")
On Error GoTo 0

MsgBox "✅ 磁场云图已生成！" & vbCrLf & "1. 铜排已自动隐藏。" & vbCrLf & "2. 如果云图还是全红/全蓝，请双击左上角彩条手动调整 Max 值为 0.5。", 64, "View B"