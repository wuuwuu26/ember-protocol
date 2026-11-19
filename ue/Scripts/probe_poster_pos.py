import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)

out = []
posters = []
walls = []
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    lab = a.get_actor_label()
    if lab.startswith("POSTER_"):
        loc = a.get_actor_location()
        sc = a.get_actor_scale3d()
        posters.append((lab, loc.x, loc.y, loc.z, sc.y * 100, sc.z * 100))
    comps = a.get_components_by_class(unreal.StaticMeshComponent)
    if comps:
        m = comps[0].get_editor_property("static_mesh")
        if m and "wall" in m.get_name().lower():
            loc = a.get_actor_location()
            walls.append((m.get_name(), loc.x, loc.y))

out.append("posters=%d walls=%d" % (len(posters), len(walls)))
for p in sorted(posters, key=lambda t: (t[1], t[2])):
    out.append("%-22s x=%8.1f y=%8.1f z=%6.1f  w=%.0f h=%.0f" % p)

out.append("--- 背墙段（X=-1300）覆盖的 Y ---")
for w in sorted([w for w in walls if abs(w[1] + 1300) < 1], key=lambda t: t[2]):
    out.append("   locY=%7.1f  covers %.0f..%.0f" % (w[2], w[2] - 206, w[2] + 206))

open(r"C:\Users\25227\AppData\Local\Temp\opencode\poster_pos.txt", "w",
     encoding="utf-8").write("\n".join(out))
unreal.log("POSTERPOS_OK")
