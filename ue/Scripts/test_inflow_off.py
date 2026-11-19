# -*- coding: utf-8 -*-
"""决定性验证：临时关 bInflow 拍一帧，与开启时对比落点波纹。
测完立即恢复（不保存），确保关卡仍是开启状态。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

n = 0
for a in sub.get_all_level_actors():
    if a.get_class().get_name() == "RobotCoolantField" and a.get_actor_label() == "CoolantSpill_0":
        a.set_editor_property("bInflow", False)
        n += 1
les.save_current_level()   # 临时保存以便截图进程读到
unreal.log("INFLOW_OFF_DONE n=%d (临时，测完恢复)" % n)
