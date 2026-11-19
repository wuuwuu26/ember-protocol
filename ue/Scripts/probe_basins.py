# -*- coding: utf-8 -*-
"""检查水池/注水参数是否真的写进了场景。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)

fields = []
basins = []
inlets = []
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    n = a.get_class().get_name()
    label = a.get_actor_label()
    if n == "RobotCoolantField":
        fields.append(a)
    elif n == "RobotBasin":
        basins.append(a)
    elif label.startswith("Inlet_"):
        inlets.append(a)

for f in fields:
    label = f.get_actor_label()
    vals = []
    for prop in ("inflow", "b_inflow", "inflow_strength", "inflow_radius",
                 "inflow_interval", "inflow_local", "flow_velocity",
                 "stagnant", "pool_radius"):
        try:
            vals.append("%s=%s" % (prop, f.get_editor_property(prop)))
        except Exception:
            pass
    loc = f.get_actor_location()
    unreal.log("[探针] %s loc=(%.1f,%.1f,%.1f) %s"
               % (label, loc.x, loc.y, loc.z, " ".join(vals)))

for b in basins:
    loc = b.get_actor_location()
    unreal.log("[探针] %s loc=(%.1f,%.1f,%.1f) inner=%.1f outer=%.1f top=%.1f"
               % (b.get_actor_label(), loc.x, loc.y, loc.z,
                  b.get_editor_property("inner_radius"),
                  b.get_editor_property("outer_radius"),
                  b.get_editor_property("top_z")))

unreal.log("PROBE_OK fields=%d basins=%d inlets=%d"
           % (len(fields), len(basins), len(inlets)))
