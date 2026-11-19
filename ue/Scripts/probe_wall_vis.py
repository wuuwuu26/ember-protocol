import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)

out = []
n = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    comps = a.get_components_by_class(unreal.StaticMeshComponent)
    if not comps:
        continue
    m = comps[0].get_editor_property("static_mesh")
    if not m or "wall" not in m.get_name().lower():
        continue
    smc = comps[0]
    loc = a.get_actor_location()
    sc = a.get_actor_scale3d()
    try:
        hidden = a.get_editor_property("hidden")
    except Exception:
        hidden = "?"
    out.append(
        "%-24s x=%7.1f y=%7.1f z=%6.1f scale=(%.2f,%.2f,%.2f) "
        "actorHidden=%s compVisible=%s"
        % (m.get_name(), loc.x, loc.y, loc.z, sc.x, sc.y, sc.z,
           hidden, smc.is_visible()))
    n += 1
    if n >= 12:
        break

open(r"C:\Users\25227\AppData\Local\Temp\opencode\wallvis.txt", "w",
     encoding="utf-8").write("\n".join(out))
unreal.log("WALLVIS_OK")
