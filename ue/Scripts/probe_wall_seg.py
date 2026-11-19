import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)

out = []
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    comps = a.get_components_by_class(unreal.StaticMeshComponent)
    if not comps:
        continue
    m = comps[0].get_editor_property("static_mesh")
    if not m or m.get_name().lower() != "sm_wall_segment":
        continue
    loc = a.get_actor_location()
    rot = a.get_actor_rotation()
    try:
        b = m.get_bounds()
        out.append("x=%8.1f y=%8.1f yaw=%6.1f  mesh ext=(%.0f,%.0f,%.0f) origin=(%.0f,%.0f,%.0f)"
                   % (loc.x, loc.y, rot.yaw,
                      b.box_extent.x, b.box_extent.y, b.box_extent.z,
                      b.origin.x, b.origin.y, b.origin.z))
    except Exception as e:
        out.append("x=%8.1f y=%8.1f err %s" % (loc.x, loc.y, e))

open(r"C:\Users\25227\AppData\Local\Temp\opencode\wallseg.txt", "w",
     encoding="utf-8").write("\n".join(sorted(out)[:24]))
unreal.log("WALLSEG_OK")
