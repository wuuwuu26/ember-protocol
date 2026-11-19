import unreal

lines = []
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    label = a.get_actor_label()
    if "Enemy_C_9" not in label and "Enemy_C_7" not in label:
        continue
    comp = a.get_component_by_class(unreal.SkeletalMeshComponent)
    if not comp:
        lines.append("%s no skel comp" % label)
        continue
    b = comp.bounds
    origin = b.origin
    ext = b.box_extent
    lines.append("%-18s actor_z=%.1f bounds_min_z=%.1f origin_z=%.1f ext_z=%.1f"
                 % (label, a.get_actor_location().z, origin.z - ext.z, origin.z, ext.z))
    # 逐骨骼位置（组件空间）
    try:
        names = comp.get_editor_property("bone_names") if hasattr(comp, "get_editor_property") else []
    except Exception:
        names = []
    for bn in ("foot_L", "foot_R", "foot_BL", "foot_BR"):
        try:
            loc = comp.get_socket_location(bn)
            lines.append("    socket %-8s = (%.1f, %.1f, %.1f)" % (bn, loc.x, loc.y, loc.z))
        except Exception as e:
            lines.append("    socket %s err %s" % (bn, e))

open(r"C:\Users\25227\AppData\Local\Temp\opencode\feet_world.txt", "w", encoding="utf-8").write("\n".join(lines))
unreal.log("FEETWORLD_OK")
