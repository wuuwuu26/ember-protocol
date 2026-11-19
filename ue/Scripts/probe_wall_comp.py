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
    la = a.get_actor_location()
    lr = a.get_actor_rotation()
    ls = a.get_actor_scale3d()
    out.append("%s" % m.get_name())
    out.append("   actor loc=(%.1f,%.1f,%.1f) yaw=%.1f scale=(%.2f,%.2f,%.2f)" % (
        la.x, la.y, la.z, lr.yaw, ls.x, ls.y, ls.z))
    for prop in ("relative_location", "relative_rotation", "relative_scale3d",
                 "absolute_location", "absolute_scale3d"):
        try:
            v = smc.get_editor_property(prop)
            out.append("   %-18s = %s" % (prop, v))
        except Exception as e:
            out.append("   %-18s <%s>" % (prop, str(e)[:35]))
    n += 1
    if n >= 2:
        break

open(r"C:\Users\25227\AppData\Local\Temp\opencode\wallcomp.txt", "w",
     encoding="utf-8").write("\n".join(out))
unreal.log("WALLCOMP_OK")
