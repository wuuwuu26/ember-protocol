import unreal

EAL = unreal.EditorAssetLibrary
names = ["SK_Enemy_Guard", "SK_Enemy_Patrol", "SK_Enemy_Hauler",
         "SK_Enemy_Weather", "SK_Enemy_Colossus", "SK_Enemy_Gardener"]
lines = []
reg = unreal.AssetRegistryHelpers.get_asset_registry()

for nm in names:
    for suffix in ("", "_LOD1", "_LOD2"):
        a = "/Game/RobotGame/Art/Characters/%s%s" % (nm, suffix)
        m = EAL.load_asset(a)
        if not m:
            lines.append("%s MISSING" % a)
            continue
        b = m.get_bounds()
        # 通过 data 接口拿三角形数
        try:
            stats = m.get_editor_property("lod_info")
        except Exception:
            stats = None
        n_lod = m.get_num_lods() if hasattr(m, "get_num_lods") else -1
        lines.append("%-28s lods=%s origin=(%.1f,%.1f,%.1f) ext=(%.1f,%.1f,%.1f)" % (
            nm + suffix, n_lod, b.origin.x, b.origin.y, b.origin.z,
            b.box_extent.x, b.box_extent.y, b.box_extent.z))

# 检查 asset registry 里 SK 的三角数
try:
    for ad in reg.get_assets_by_path("/Game/RobotGame/Art/Characters", recursive=False):
        n = str(ad.asset_name)
        if not n.startswith("SK_Enemy"):
            continue
        tag = ad.get_tag_value("Triangles")
        lines.append("REG %-28s tris=%s" % (n, tag))
except Exception as e:
    lines.append("reg_err %s" % e)

open(r"C:\Users\25227\AppData\Local\Temp\opencode\lod_report.txt", "w", encoding="utf-8").write("\n".join(lines))
unreal.log("LOD_OK")
