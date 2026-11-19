# -*- coding: utf-8 -*-
"""查关卡里地面/墙 actor 的材质覆盖分布，给 Poly Haven 应用脚本定边界。

目标：只改**新区域**（X >= 1800，带 ExtRegion tag）的地面与墙，
绝不动原竞技场（X < 1800）。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)

out = []
stats = {}
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    c = a.static_mesh_component
    m = c.get_editor_property("static_mesh") if c else None
    if not m:
        continue
    nm = m.get_name().lower()
    if "floor" not in nm and "wall" not in nm:
        continue
    loc = a.get_actor_location()
    try:
        tags = [str(t) for t in a.get_editor_property("tags")]
    except Exception:
        tags = []
    zone = "EXT" if "ExtRegion" in tags or loc.x >= 1800 else "ORIG"
    ov = c.get_editor_property("override_materials")
    key = (zone,
           "floor" if "floor" in nm else "wall",
           tuple(x.get_name() if x else "None" for x in ov))
    stats[key] = stats.get(key, 0) + 1

out.append("地面/墙 actor 材质覆盖分布：")
for k, v in sorted(stats.items(), key=lambda t: (t[0][0], t[0][1], -t[1])):
    out.append("  %-5s %-6s %3d 块 -> %s" % (k[0], k[1], v, list(k[2])))

with open(r"C:\Users\25227\Documents\robot_game\docs\polyhaven_boundary.txt",
          "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("POLY_BOUNDARY_DONE")
