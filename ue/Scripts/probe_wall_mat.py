import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)

out = []
seen = {}
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    comps = a.get_components_by_class(unreal.StaticMeshComponent)
    if not comps:
        continue
    m = comps[0].get_editor_property("static_mesh")
    if not m or "wall" not in m.get_name().lower():
        continue
    smc = comps[0]
    mats = []
    try:
        n = smc.get_num_materials()
    except Exception:
        n = 1
    for i in range(max(1, n)):
        try:
            mi = smc.get_material(i)
            mats.append("%s(%s)" % (mi.get_name() if mi else "None",
                                    mi.get_class().get_name() if mi else "-"))
        except Exception:
            mats.append("?")
    seen[m.get_name()] = ",".join(mats)

for k, v in sorted(seen.items()):
    out.append("%s -> %s" % (k, v))

open(r"C:\Users\25227\AppData\Local\Temp\opencode\wallmat.txt", "w",
     encoding="utf-8").write("\n".join(out))
unreal.log("WALLMAT_OK")
