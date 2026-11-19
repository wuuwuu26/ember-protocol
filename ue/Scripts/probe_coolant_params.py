# -*- coding: utf-8 -*-
"""查 CoolantSpill_0（长方形水渠）的物理模拟参数当前值。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

out = []
PROPS = ["b_inflow", "inflow_local", "inflow_strength", "inflow_interval",
         "inflow_radius", "b_stagnant", "pool_radius", "grid_cells",
         "base_z", "wave_speed_sq", "damping", "max_height",
         "surface_material", "heat_cool_per_second"]

for a in sub.get_all_level_actors():
    if a.get_class().get_name() != "RobotCoolantField":
        continue
    loc = a.get_actor_location()
    out.append("═══ %s (%.0f,%.0f,%.1f) ═══" % (
        a.get_actor_label(), loc.x, loc.y, loc.z))
    for p in PROPS:
        try:
            v = a.get_editor_property(p)
            out.append("  %-24s = %s" % (p, v))
        except Exception:
            pass
    try:
        org, ext = a.get_actor_bounds(False)
        out.append("  包围盒尺寸 = %.0f x %.0f x %.0f cm" % (
            ext.x * 2, ext.y * 2, ext.z * 2))
    except Exception:
        pass
    out.append("")

with open(r"C:\Users\25227\Documents\robot_game\docs\coolant_params.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("COOLANT_PARAMS_DONE")
