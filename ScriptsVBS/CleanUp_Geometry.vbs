' CleanUp_v2.vbs - 使用包围盒估算体积

Dim oAnsoftApp, oDesktop, oProject, oDesign, oEditor
Dim partNames, i, partName, bbox, volume, deletedCount, thresholdVolume

thresholdVolume = 5000.0 ' mm^3

Set oAnsoftApp = CreateObject("AnsoftMaxwell.MaxwellScriptInterface")
Set oDesktop = oAnsoftApp.GetAppDesktop()
Set oProject = oDesktop.GetActiveProject()
Set oDesign = oProject.GetActiveDesign()
Set oEditor = oDesign.SetActiveEditor("3D Modeler")

partNames = oEditor.GetMatchedObjectName("*")
deletedCount = 0

For i = 0 To UBound(partNames)
    partName = partNames(i)
    
    On Error Resume Next
    ' 获取包围盒 [xmin, ymin, zmin, xmax, ymax, zmax]
    bbox = oEditor.GetModelBoundingBox()
    
    ' 如果能获取单个物体的包围盒
    oEditor.FitAll()
    bbox = oEditor.GetObjectBoundingBox(partName)
    
    If IsArray(bbox) Then
        ' 估算体积 = 长 x 宽 x 高
        volume = Abs(bbox(3) - bbox(0)) * Abs(bbox(4) - bbox(1)) * Abs(bbox(5) - bbox(2))
        
        If volume > 0 And volume < thresholdVolume Then
            oEditor.Delete Array("NAME:Selections", "Selections:=", partName)
            deletedCount = deletedCount + 1
        End If
    End If
    On Error GoTo 0
Next

MsgBox "删除了 " & deletedCount & " 个微小物体。", 64, "Done"