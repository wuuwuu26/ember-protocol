import unreal

out = []
reg = unreal.AssetRegistryHelpers.get_asset_registry()
EAL = unreal.EditorAssetLibrary
found = []
for ad in reg.get_assets_by_path("/Game", recursive=True):
    n = str(ad.asset_name)
    if n.startswith("BP_Enemy"):
        found.append((n, str(ad.package_name)))
for n, pkg in sorted(found):
    try:
        bp = EAL.load_asset(pkg)
        cdo = unreal.get_default_object(bp.generated_class())
        comp = cdo.get_component_by_class(unreal.SkeletalMeshComponent)
        mesh = comp.get_skeletal_mesh_asset() if comp else None
        out.append("%-14s %-40s -> %s" % (n, pkg, mesh.get_name() if mesh else "None"))
    except Exception as e:
        out.append("%-14s %-40s err %s" % (n, pkg, e))

open(r"C:\Users\25227\AppData\Local\Temp\opencode\bpmap.txt", "w",
     encoding="utf-8").write("\n".join(out))
unreal.log("BPMAP_OK")
