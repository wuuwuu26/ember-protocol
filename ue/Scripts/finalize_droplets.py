# -*- coding: utf-8 -*-
"""恢复水珠并调成少而集中的落点飞溅（第一百一十五轮）。"""
import unreal
LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = []
for a in sub.get_all_level_actors():
    if a.get_class().get_name() == "RobotCoolantField" and a.get_actor_label() == "CoolantSpill_0":
        a.set_editor_property("bSplashDroplets", True)
        a.set_editor_property("DropletsPerPulse", 2)
        a.set_editor_property("DropletLaunchSpeed", 130.0)
        a.set_editor_property("DropletSpread", 42.0)
        a.set_editor_property("DropletGravity", 950.0)
        a.set_editor_property("DropletRadius", 3.2)
        a.set_editor_property("MaxDroplets", 40)
        out.append("CoolantSpill_0 -> 水珠：每脉冲2、上抛130、散开42、重力950、半径3.2、上限40")
        break
les.save_current_level()
out.append("已保存")
with open(r"C:\Users\25227\Documents\robot_game\docs\droplet_final.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("DROPLET_FINAL_DONE")
