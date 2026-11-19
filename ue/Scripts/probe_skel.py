# -*- coding: utf-8 -*-
import unreal
L = "[骨骼资产]"
unreal.log(L + " 开始")
ar = unreal.AssetRegistryHelpers.get_asset_registry()
for ad in ar.get_assets_by_path("/Game/RobotGame/Art/Characters", recursive=False):
    if str(ad.asset_class_path.asset_name) != "SkeletalMesh":
        continue
    m = ad.get_asset()
    if not m:
        continue
    sk = m.get_editor_property("skeleton")
    nm = sk.get_name() if sk else "无"
    n_mat = len(m.get_editor_property("materials"))
    verts = m.get_num_vertices(0) if hasattr(m, "get_num_vertices") else -1
    unreal.log("%s  %-26s 骨骼=%s 材质槽=%d 顶点=%d" % (L, str(ad.asset_name), nm, n_mat, verts))
