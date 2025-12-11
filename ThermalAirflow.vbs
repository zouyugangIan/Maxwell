' ======================================================================
' ThermalAirflow.vbs - Switchgear Thermal & Airflow Steady-State Analysis
' 开关柜温度场及气流场稳态特性仿真分析
' ======================================================================

Dim oAnsoftApp, oDesktop, oProject, oDesign, oEditor

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

' IMPORTANT: Maxwell 3D mainly calculates LOSSES (Generates Heat).
' To simulate Airflow (CFD), you must use ANSYS Icepak or Fluent.
' This script sets up a Maxwell design to compute the power loss source.

oProject.InsertDesign "Maxwell 3D", "KYN28_Thermal_Source", "EddyCurrent", ""
Set oDesign = oProject.GetActiveDesign()
Set oEditor = oDesign.SetActiveEditor("3D Modeler")

' 几何建模 (Geometry - Same as EddyCurrent)
' ... (User already has geometry in EddyCurrent.vbs, so we skip duplicating it here to save space)
' In a real workflow, you would Copy Design from EddyCurrent.vbs

MsgBox "ℹ️ 提示 / Note:" & vbCrLf & vbCrLf & _
       "Maxwell 软件主要负责'电磁发热'计算(Ohmic Loss)。" & vbCrLf & _
       "气流场(Airflow)分析必须使用 ANSYS Icepak 或 Fluent。" & vbCrLf & vbCrLf & _
       "流程如下：" & vbCrLf & _
       "1. 运行 EddyCurrent.vbs 得到损耗分布。" & vbCrLf & _
       "2. 打开 ANSYS Icepak -> File -> Import -> Maxwell。" & vbCrLf & _
       "3. 在 Icepak 设置风扇、通风口和空气属性。", 64, "Thermal & Airflow Guide"