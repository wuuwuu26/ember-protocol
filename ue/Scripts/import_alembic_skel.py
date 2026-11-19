"""把 FLIP 水面 Alembic 以 SKELETAL 模式导入：每帧变形写成 morph target，
得到普通 SkeletalMesh + 动画，材质覆盖走标准骨骼网格路径（绕开 GeometryCache 材质绑定）。"""
import unreal

ABC = r"C:\Users\25227\Documents\robot_game\assets\out\flip_channel_v2.abc"
DEST = "/Game/RobotGame/Art/Fluids"
EAL = unreal.EditorAssetLibrary

if not EAL.does_directory_exist(DEST):
    EAL.make_directory(DEST)

name = "flip_channel_skel"
for suffix in ("", "_Skeleton", "_PhysicsAsset", "_Anim"):
    p = f"{DEST}/{name}{suffix}"
    if EAL.does_asset_exist(p):
        EAL.delete_asset(p)

task = unreal.AssetImportTask()
task.filename = ABC
task.destination_path = DEST
task.destination_name = name
task.automated = True
task.replace_existing = True
task.save = True

opts = unreal.AbcImportSettings()
opts.import_type = unreal.AlembicImportType.SKELETAL
task.options = opts

unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

paths = EAL.list_assets(DEST, recursive=False)
found = []
for p in paths:
    obj = EAL.load_asset(p)
    cls = obj.get_class().get_name() if obj else "?"
    print("[skel] %s (%s)" % (p, cls))
    found.append((p, cls))
print("SKEL_IMPORT_OK n=%d" % len(found))
