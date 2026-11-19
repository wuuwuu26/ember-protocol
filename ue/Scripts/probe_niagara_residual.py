# -*- coding: utf-8 -*-
"""查关卡里所有 NiagaraActor 残留（按类，不依赖 tag）。"""
import unreal
LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = []
n = 0
for a in sub.get_all_level_actors():
    if a.get_class().get_name() == "NiagaraActor":
        loc = a.get_actor_location()
        out.append("%s (%.0f,%.0f,%.0f)" % (a.get_actor_label(), loc.x, loc.y, loc.z))
        n += 1
out.insert(0, "NiagaraActor 残留 %d 个" % n)
with open(r"C:\Users\25227\Documents\robot_game\docs\niagara_residual.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("NIAGARA_RESIDUAL_DONE")
