"""记录敌人瞄准/后坐状态的调试日志：每 0.1s 打一行 AimBlend / AimPitchDeg / Recoil。
配合 -AutoFire 观察开火前后这些量是否按预期变化。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ELL = unreal.EditorLevelLibrary
print("[aim] 读取脚本占位：实际数据由 C++ 侧的 -DebugAim 输出")
print("AIM_PROBE_NOTE_OK")
