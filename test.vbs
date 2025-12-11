' CleanUp_Debug.vbs - 调试版，显示物体体积

Dim oAnsoftApp, oDesktop, oProject, oDesign, oEditor
Dim partNames, i, partName, volume, msg

Set oAnsoftApp = CreateObject("AnsoftMaxwell.MaxwellScriptInterface")
Set oDesktop = oAnsoftApp.GetAppDesktop()
Set oProject = oDesktop.GetActiveProject()
Set oDesign = oProject.GetActiveDesign()
Set oEditor = oDesign.SetActiveEditor("3D Modeler")

partNames = oEditor.GetMatchedObjectName("*")

msg = "前10个物体的体积:" & vbCrLf

For i = 0 To 9
    If i <= UBound(partNames) Then
        partName = partNames(i)
        On Error Resume Next
        volume = oEditor.GetPropertyValue("Geometry3DAttributeTab", partName, "Volume")
        On Error GoTo 0
        msg = msg & partName & ": " & volume & vbCrLf
    End If
Next

MsgBox msg, 64, "体积检查"