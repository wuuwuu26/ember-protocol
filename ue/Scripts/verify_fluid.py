# -*- coding: utf-8 -*-
"""最终状态复核：确认流体升级的四项改动都在。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = []

for a in sub.get_all_level_actors():
    if a.get_class().get_name() == "RobotCoolantField" and a.get_actor_label() == "CoolantSpill_0":
        out.append("CoolantSpill_0:")
        for k in ("bInflow", "InflowStrength", "InflowInterval", "InflowRadius",
                  "MaxHeight", "GridCells", "InflowLocal"):
            try:
                out.append("  %-16s = %s" % (k, a.get_editor_property(k)))
            except Exception:
                pass
    if a.get_actor_label() in ("Splash_FoamRing", "Splash_FoamDisc", "Splash_SprayCone"):
        c = a.static_mesh_component
        try:
            out.append("%s: visible=%s hidden_in_game=%s" % (
                a.get_actor_label(), c.is_visible(),
                c.get_editor_property("hidden_in_game")))
        except Exception:
            pass

with open(r"C:\Users\25227\Documents\robot_game\docs\fluid_verify.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("FLUID_VERIFY_DONE")
