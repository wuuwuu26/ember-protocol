# -*- coding: utf-8 -*-
"""查地面块的实际 XY 位置，找重叠/空隙。
SM_Env_Floor 是 400x400，中心对齐 400 整数倍时应当正好铺满。
若存在 199.5 或 200.5 这种偏移，就会出现 Z-fighting 或缝。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)

pos = set()
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    c = a.static_mesh_component
    m = c.get_editor_property("static_mesh") if c else None
    if not m or "floor" not in m.get_name().lower():
        continue
    loc = a.get_actor_location()
    pos.add((round(loc.x, 2), round(loc.y, 2)))

xs = sorted(set(p[0] for p in pos))
ys = sorted(set(p[1] for p in pos))
out = ["unique X: %s" % xs, "unique Y: %s" % ys, "count %d" % len(pos)]

# 检查 X 间距是否都是 400
gaps = sorted(set(round(xs[i + 1] - xs[i], 2) for i in range(len(xs) - 1)))
out.append("X gaps: %s" % gaps)
gaps_y = sorted(set(round(ys[i + 1] - ys[i], 2) for i in range(len(ys) - 1)))
out.append("Y gaps: %s" % gaps_y)

with open(r"C:\Users\25227\Documents\robot_game\docs\ext_floor2.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("EXT_FLOOR2_DONE")
