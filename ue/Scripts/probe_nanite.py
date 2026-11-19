import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)

out = []
# 1) 材质是否真的被换成 M_Core_wall
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    comps = a.get_components_by_class(unreal.StaticMeshComponent)
    if not comps:
        continue
    m = comps[0].get_editor_property("static_mesh")
    if m and "wall" in m.get_name().lower():
        mi = comps[0].get_material(0)
        out.append("slot0 of %s = %s" % (m.get_name(), mi.get_name() if mi else "None"))
        break

# 2) Nanite / LOD 设置
p = "/Game/RobotGame/Art/Environment/sm_wall_segment"
mesh = unreal.EditorAssetLibrary.load_asset(p)
for prop in ("nanite_settings", "lod_group", "enable_material_slot_overrides"):
    try:
        v = mesh.get_editor_property(prop)
        if prop == "nanite_settings":
            try:
                out.append("nanite enabled=%s" % v.get_editor_property("enabled"))
            except Exception as e:
                out.append("nanite obj=%s (%s)" % (v, str(e)[:40]))
        else:
            out.append("%s=%s" % (prop, v))
    except Exception as e:
        out.append("%s=<%s>" % (prop, str(e)[:40]))

open(r"C:\Users\25227\AppData\Local\Temp\opencode\nanite.txt", "w",
     encoding="utf-8").write("\n".join(out))
unreal.log("NANITE_OK")
