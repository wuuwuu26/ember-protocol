# -*- coding: utf-8 -*-
"""水珠放大：让平视也能看到抛射弧线。"""
import unreal
LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = []
for a in sub.get_all_level_actors():
    if a.get_class().get_name() == "RobotCoolantField" and a.get_actor_label() == "CoolantSpill_0":
        a.set_editor_property("bSplashDroplets", True)
        a.set_editor_property("DropletsPerPulse", 3)
        a.set_editor_property("DropletLaunchSpeed", 220.0)
        a.set_editor_property("DropletSpread", 70.0)
        a.set_editor_property("DropletGravity", 900.0)
        a.set_editor_property("DropletRadius", 6.0)
        a.set_editor_property("MaxDroplets", 54)
        out.append("水珠：每脉冲3、上抛220、散开70、重力900、半径6、上限54")
        break
les.save_current_level()
out.append("已保存")
with open(r"C:\Users\25227\Documents\robot_game\docs\droplet_big.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("DROPLET_BIG_DONE")
