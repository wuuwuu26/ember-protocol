import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)

out = []
walls = []
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    comps = a.get_components_by_class(unreal.StaticMeshComponent)
    if not comps:
        continue
    m = comps[0].get_editor_property("static_mesh")
    if not m:
        continue
    nm = m.get_name().lower()
    if "wall" not in nm and "floor" not in nm:
        continue
    loc = a.get_actor_location()
    rot = a.get_actor_rotation()
    sc = a.get_actor_scale3d()
    walls.append((m.get_name(), loc.x, loc.y, loc.z, rot.yaw, sc.x))

out.append("wall/floor actors=%d" % len(walls))
# 找内侧朝向场地的墙：背墙 x 最小、远墙 x 最大、两侧 y 极值
xs = [w[1] for w in walls]
ys = [w[2] for w in walls]
out.append("x range %.0f..%.0f   y range %.0f..%.0f" % (min(xs), max(xs), min(ys), max(ys)))

for name in set(w[0] for w in walls):
    sel = [w for w in walls if w[0] == name]
    out.append("--- %s : %d" % (name, len(sel)))
    for w in sorted(sel, key=lambda t: (t[1], t[2]))[:8]:
        out.append("   x=%8.1f y=%8.1f z=%6.1f yaw=%6.1f scale=%.2f" % w[1:])

open(r"C:\Users\25227\AppData\Local\Temp\opencode\walls.txt", "w",
     encoding="utf-8").write("\n".join(out))
unreal.log("WALLPROBE_OK")
