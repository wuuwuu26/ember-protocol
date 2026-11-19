# -*- coding: utf-8 -*-
"""调整落水水珠：只在冷液池开、聚焦落点、参数收敛（第一百一十五轮）。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = []

for a in sub.get_all_level_actors():
    if a.get_class().get_name() != "RobotCoolantField":
        continue
    label = a.get_actor_label()
    is_coolant = (label == "CoolantSpill_0")
    try:
        a.set_editor_property("bSplashDroplets", is_coolant)
        if is_coolant:
            a.set_editor_property("DropletsPerPulse", 2)
            a.set_editor_property("DropletLaunchSpeed", 150.0)
            a.set_editor_property("DropletSpread", 55.0)
            a.set_editor_property("DropletGravity", 880.0)
            a.set_editor_property("DropletRadius", 2.0)
            a.set_editor_property("MaxDroplets", 48)
            out.append("%s -> 开水珠（每脉冲2、散开55、重力880、上限48）" % label)
        else:
            out.append("%s -> 关水珠（死水）" % label)
    except Exception as e:
        out.append("%s !! %s" % (label, str(e)[:60]))

les.save_current_level()
out.append("已保存")
with open(r"C:\Users\25227\Documents\robot_game\docs\droplet_tune.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("DROPLET_TUNE_DONE")
