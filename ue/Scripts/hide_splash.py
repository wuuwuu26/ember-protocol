# -*- coding: utf-8 -*-
"""判定测试：临时隐藏 Splash_FoamRing/Disc，看浅色块是否消失。

如果隐藏后浅色块仍在 -> 是别的 actor（Jet 水柱 / Spray 锥）造成的；
如果消失 -> 就是这两个圆盘。测完立即恢复（不改保存）。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

out = []
for a in sub.get_all_level_actors():
    label = a.get_actor_label()
    if label in ("Splash_FoamRing", "Splash_FoamDisc"):
        c = a.static_mesh_component
        c.set_visibility(False)
        out.append("隐藏 %s" % label)
    elif label == "Splash_SprayCone":
        c = a.static_mesh_component
        c.set_visibility(False)
        out.append("隐藏 %s" % label)

with open(r"C:\Users\25227\Documents\robot_game\docs\splash_hide.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("SPLASH_HIDE_DONE")
