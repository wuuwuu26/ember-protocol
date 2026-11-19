import unreal

reg = unreal.AssetRegistryHelpers.get_asset_registry()
out = []
for ad in reg.get_assets_by_path("/Game/RobotGame/Art/Environment", recursive=False):
    n = str(ad.asset_name)
    if "wall" not in n.lower():
        continue
    tri = ad.get_tag_value("Triangles")
    verts = ad.get_tag_value("Vertices")
    out.append("%-26s tris=%s verts=%s" % (n, tri, verts))

# 同时看网格资产本身
for nm in ("sm_wall_segment", "sm_wall_corner"):
    p = "/Game/RobotGame/Art/Environment/%s" % nm
    if unreal.EditorAssetLibrary.does_asset_exist(p):
        m = unreal.EditorAssetLibrary.load_asset(p)
        try:
            nb = m.get_num_lods()
        except Exception:
            nb = "?"
        b = m.get_bounds()
        out.append("%-26s lods=%s bounds ext=(%.0f,%.0f,%.0f)" % (
            nm, nb, b.box_extent.x, b.box_extent.y, b.box_extent.z))
        try:
            mats = m.get_editor_property("materials")
            out.append("    material slots=%d" % len(mats))
        except Exception as e:
            out.append("    mat err %s" % e)

open(r"C:\Users\25227\AppData\Local\Temp\opencode\wallmesh.txt", "w",
     encoding="utf-8").write("\n".join(out))
unreal.log("WALLMESH_OK")
