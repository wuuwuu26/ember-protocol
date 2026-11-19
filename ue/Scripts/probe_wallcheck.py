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
    if "wall" in nm:
        rot = a.get_actor_rotation()
        loc = a.get_actor_location()
        crot = comps[0].get_editor_property("relative_rotation")
        walls.append((nm, loc.x, loc.y, rot.yaw, crot.pitch))

out.append("walls=%d" % len(walls))
for w in sorted(walls, key=lambda t: (t[1], t[2]))[:40]:
    out.append("%-20s x=%7.1f y=%7.1f yaw=%5.1f compPitch=%5.1f" % w)

open(r"C:\Users\25227\AppData\Local\Temp\opencode\wallcheck.txt", "w",
     encoding="utf-8").write("\n".join(out))
unreal.log("WALLCHECK_OK")
