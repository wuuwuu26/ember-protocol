"""UE 侧核对 SK_Enemy_Patrol：分段数、包围盒，和 FBX 对比定位丢件。"""
import unreal

EAL = unreal.EditorAssetLibrary
SML = unreal.EditorSkeletalMeshLibrary

for code in ("Patrol", "Guard"):
    m = EAL.load_asset(f"/Game/RobotGame/Art/Characters/SK_Enemy_{code}")
    if not m:
        print("[pm] %s 不存在" % code)
        continue
    try:
        nlod = SML.get_lod_count(m)
    except Exception as e:
        nlod = "err:%s" % e
    print("[pm] %s lod_count=%s" % (code, nlod))
    for lod in range(3):
        try:
            ns = SML.get_num_sections(m, lod)
            print("[pm]   LOD%d sections=%s" % (lod, ns))
        except Exception as e:
            print("[pm]   LOD%d sections err: %s" % (lod, e))
    for fn in ("get_bounds", "get_bounding_box", "get_extended_bounds"):
        try:
            b = getattr(m, fn)()
            print("[pm]   %s -> %s" % (fn, b))
            break
        except Exception:
            pass
    try:
        print("[pm]   bounds_extent=%s" % m.get_editor_property("extended_bounds_extent"))
    except Exception:
        pass
print("PATROL_MESH_PROBE_OK")
