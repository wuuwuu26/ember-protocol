"""取每个 SK_Enemy_* 的 LOD0 三角面数与材质槽数，与 Blender 源对比判断是否缺件。"""
import unreal

EAL = unreal.EditorAssetLibrary
codes = ["Weather", "Patrol", "Hauler", "Guard", "Gardener", "Colossus"]
for c in codes:
    p = f"/Game/RobotGame/Art/Characters/SK_Enemy_{c}"
    m = EAL.load_asset(p)
    if not m:
        print("[em] %s 不存在" % c)
        continue
    try:
        n_lod = m.get_num_lods()
    except Exception:
        n_lod = -1
    tris = -1
    try:
        # LOD0 三角面数
        tris = m.get_num_triangles(0)
    except Exception as e:
        tris = "err:%s" % e
    mats = -1
    try:
        mats = len(m.get_editor_property("materials"))
    except Exception:
        pass
    print("[em] %-9s lods=%s lod0_tris=%s mats=%s" % (c, n_lod, tris, mats))
print("ENEMY_MESH_PROBE_OK")
