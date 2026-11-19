import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)

out = []
seen = {}
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    try:
        outer = a.get_outer()
        pkg = outer.get_outermost().get_name() if outer else "?"
    except Exception:
        pkg = "?"
    lab = a.get_actor_label()
    key = pkg
    seen.setdefault(key, []).append(lab)

for k, v in sorted(seen.items()):
    out.append("LEVEL/OUTER %s : %d actors" % (k, len(v)))
    out.append("    sample: " + ", ".join(v[:6]))

# 墙 actor 的 outer
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    comps = a.get_components_by_class(unreal.StaticMeshComponent)
    if not comps:
        continue
    m = comps[0].get_editor_property("static_mesh")
    if m and "wall" in m.get_name().lower():
        o = a.get_outer()
        out.append("WALL outer=%s  outermost=%s" % (
            o.get_name() if o else "?", o.get_outermost().get_name() if o else "?"))
        break

open(r"C:\Users\25227\AppData\Local\Temp\opencode\levels.txt", "w",
     encoding="utf-8").write("\n".join(out))
unreal.log("LEVELS_OK")
