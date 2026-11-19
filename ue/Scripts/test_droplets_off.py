# -*- coding: utf-8 -*-
"""判定：临时关 bSplashDroplets，看白色带是否消失（区分水珠 vs 水面泡沫）。"""
import unreal
LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in sub.get_all_level_actors():
    if a.get_class().get_name() == "RobotCoolantField" and a.get_actor_label() == "CoolantSpill_0":
        a.set_editor_property("bSplashDroplets", False)
        break
les.save_current_level()
unreal.log("DROPLET_OFF_DONE")
