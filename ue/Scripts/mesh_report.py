import unreal

EAL = unreal.EditorAssetLibrary
names = ["SK_Enemy_Guard", "SK_Enemy_Patrol", "SK_Enemy_Hauler",
         "SK_Enemy_Weather", "SK_Enemy_Colossus", "SK_Enemy_Gardener"]
lines = []

for nm in names:
    path = "/Game/RobotGame/Art/Characters/%s" % nm
    m = EAL.load_asset(path)
    if not m:
        lines.append("%s MISSING" % nm)
        continue
    b = m.get_bounds()
    lines.append("=== %s origin=(%.1f,%.1f,%.1f) r=%.1f ext=(%.1f,%.1f,%.1f)" % (
        nm, b.origin.x, b.origin.y, b.origin.z, b.sphere_radius,
        b.box_extent.x, b.box_extent.y, b.box_extent.z))
    try:
        sk = m.get_editor_property("skeleton")
        lines.append("   skeleton=%s" % sk.get_name())
    except Exception as e:
        lines.append("   skel_err %s" % e)
    try:
        src = m.get_editor_property("lod_info")
        for i, li in enumerate(src):
            lines.append("   LOD%d verts=%d tris=%d screen=%s" % (
                i, li.get_editor_property("num_vertices"),
                li.get_editor_property("num_triangles"),
                li.get_editor_property("screen_size")))
    except Exception as e:
        lines.append("   lodinfo_err %s" % e)

open(r"C:\Users\25227\AppData\Local\Temp\opencode\mesh_report.txt", "w", encoding="utf-8").write("\n".join(lines))
unreal.log("MESH_REPORT_OK")
