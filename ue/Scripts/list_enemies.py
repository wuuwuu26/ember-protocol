import unreal

EAL = unreal.EditorAssetLibrary
ELL = unreal.EditorLevelLibrary
lines = []

# 关卡里的敌人与玩家
for a in ELL.get_all_level_actors():
    label = a.get_actor_label()
    if not (label.startswith("Enemy_") or label.startswith("RobotCharacter") or "Enemy" in label):
        continue
    lines.append("ACTOR %s" % label)
    try:
        mesh_comp = a.get_component_by_class(unreal.SkinnedMeshComponent)
        if mesh_comp:
            asset = mesh_comp.get_skeletal_mesh_asset()
            if asset:
                lines.append("   skeletal=%s" % asset.get_name())
    except Exception as e:
        lines.append("   err %s" % e)

# 所有 SK_Enemy_* 资产
ar = unreal.AssetRegistryHelpers.get_asset_registry()
for ad in ar.get_assets_by_path("/Game/RobotGame/Art/Characters", recursive=False):
    n = str(ad.asset_name)
    if n.startswith("SK_"):
        lines.append("ASSET %s" % n)

open(r"C:\Users\25227\AppData\Local\Temp\opencode\enemy_list.txt", "w", encoding="utf-8").write("\n".join(lines))
unreal.log("ENEMY_LIST_OK")
