import unreal
cands = ["/Game/RobotGame/Art/Materials/M_SkyDome","/Engine/EngineSky/M_Sky_Panning","/Engine/EngineSky/M_Sky","/Engine/EngineSky/SkySphere/M_Sky","/Engine/EngineMaterials/EmissiveMeshMaterial","/Engine/EngineMaterials/DefaultMaterial"]
for p in cands:
    a = unreal.EditorAssetLibrary.load_asset(p)
    unreal.log('[资产探针] %s -> %s' % (p, a.get_name() if a else 'None'))
unreal.log('[资产探针] 完成')