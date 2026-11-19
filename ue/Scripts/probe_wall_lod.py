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
    vals = []
    for prop in ("forced_lod_model", "min_lod", "override_min_lod",
                 "cast_shadow", "visible_in_scene", "render_in_main_pass",
                 "detail_mode", "bounds_scale", "lod_data"):
        try:
            vals.append("%s=%s" % (prop, smc.get_editor_property(prop)))
        except Exception as e:
            vals.append("%s=<%s>" % (prop, str(e)[:30]))
    out.append("%s @ (%.0f,%.0f)\n    %s" % (
        m.get_name(), a.get_actor_location().x, a.get_actor_location().y,
        "\n    ".join(vals)))
    n += 1
    if n >= 2:
        break

open(r"C:\Users\25227\AppData\Local\Temp\opencode\walllod.txt", "w",
     encoding="utf-8").write("\n".join(out))
unreal.log("WALLLOD_OK")
