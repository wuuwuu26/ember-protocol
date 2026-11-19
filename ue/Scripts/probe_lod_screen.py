import unreal

EAL = unreal.EditorAssetLibrary
out = []
for nm in ("SK_Enemy_Patrol", "SK_Enemy_Guard", "SK_Enemy_Hauler",
           "SK_Enemy_Gardener", "SK_Enemy_Colossus"):
    p = "/Game/RobotGame/Art/Characters/%s" % nm
    if not EAL.does_asset_exist(p):
        continue
    m = EAL.load_asset(p)
    try:
        n = m.get_num_lods()
    except Exception:
        n = -1
    out.append("%-22s lods=%s" % (nm, n))
    try:
        src = m.get_editor_property("lod_info")
        for i, li in enumerate(src):
            out.append("    LOD%d screen=%.4f tris=%d" % (
                i, li.get_editor_property("screen_size"),
                li.get_editor_property("num_triangles")))
    except Exception as e:
        out.append("    lod_info err %s" % str(e)[:50])

open(r"C:\Users\25227\AppData\Local\Temp\opencode\lodinfo.txt", "w",
     encoding="utf-8").write("\n".join(out))
unreal.log("LODINFO_OK")
