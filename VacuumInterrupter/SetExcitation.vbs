Option Explicit

' 真空灭弧室激励设置VBS脚本
' 用于在Maxwell Transient中设置线圈和绕组激励
' 
' 使用方法:
' 1. 在Maxwell中打开项目 VacuumInterrupter_12kV_4000A_v5_Transient
' 2. 选择Tools -> Run Script
' 3. 选择此脚本文件

Dim oAnsoftApp, oDesktop, oProject, oDesign

Set oAnsoftApp = CreateObject("Ansoft.ElectronicsDesktop")
Set oDesktop = oAnsoftApp.GetAppDesktop()
Set oProject = oDesktop.GetActiveProject()
Set oDesign = oProject.GetActiveDesign()

' 设置线圈终端 - 静触头 (Positive)
oDesign.AssignCoil Array( _
    "NAME:Coil_Input", _
    "Objects:=", Array("Fixed_Contact_Disc"), _
    "Conductor number:=", "1", _
    "PolarityType:=", "Positive")

' 设置线圈终端 - 动触头 (Negative)
oDesign.AssignCoil Array( _
    "NAME:Coil_Output", _
    "Objects:=", Array("Moving_Contact_Disc"), _
    "Conductor number:=", "1", _
    "PolarityType:=", "Negative")

' 创建绕组并设置电流
oDesign.AssignWinding Array( _
    "NAME:Main_Winding", _
    "Type:=", "Current", _
    "IsSolid:=", True, _
    "Current:=", "4000A", _
    "Resistance:=", "0ohm", _
    "Inductance:=", "0nH", _
    "Voltage:=", "0mV", _
    "ParallelBranchesNum:=", "1", _
    "Phase:=", "0deg"), _
    Array("Coil_Input", "Coil_Output")

MsgBox "激励设置完成!" & vbCrLf & _
       "Coil_Input: Fixed_Contact_Disc (Positive)" & vbCrLf & _
       "Coil_Output: Moving_Contact_Disc (Negative)" & vbCrLf & _
       "Main_Winding: 4000A Current", vbInformation, "真空灭弧室激励配置"
