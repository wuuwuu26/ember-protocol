"""把 FLIP 烘焙的水渠水面 Alembic 导入 UE 成 Geometry Cache，并确认资产类型。"""
import unreal

ABC = r"C:\Users\25227\AppData\Local\Temp\opencode\flip_channel_v2.abc"
DEST = "/Game/RobotGame/Art/Fluids"

EAL = unreal.EditorAssetLibrary
if not EAL.does_directory_exist(DEST):
    EAL.make_directory(DEST)

# 清掉旧的导入资产，幂等
for name in ("flip_channel_full",):
    for suffix in ("", "_GeometryCache", "_geo"):
        p = f"{DEST}/{name}{suffix}"
        if EAL.does_asset_exist(p):
            EAL.delete_asset(p)

task = unreal.AssetImportTask()
task.filename = ABC
task.destination_path = DEST
task.destination_name = "flip_channel_full"
task.automated = True
task.replace_existing = True
task.save = True

# 关键：默认会导成单帧 StaticMesh；显式指定 Geometry Cache 才有动画
opts = unreal.AbcImportSettings()
opts.import_type = unreal.AlembicImportType.GEOMETRY_CACHE
task.options = opts

at = unreal.AssetToolsHelpers.get_asset_tools()
at.import_asset_tasks([task])

# 列出导入产物
print("[abc] 导入完成，目录内容：")
paths = EAL.list_assets(DEST, recursive=False)
gc = None
for p in paths:
    obj = EAL.load_asset(p)
    cls = obj.get_class().get_name() if obj else "?"
    print("[abc]   %s  (%s)" % (p, cls))
    if obj and "GeometryCache" in cls:
        gc = obj
print("[abc] GeometryCache 资产:", gc.get_name() if gc else "NONE",
      gc.get_path_name() if gc else "")
print("ABC_IMPORT_OK gc=%s" % (gc.get_name() if gc else "NONE"))
