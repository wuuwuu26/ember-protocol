# -*- coding: utf-8 -*-
"""把机体 FBX 以**静态网格**导入临时目录，查 UV 通道数。
用来判断 UV 是在 FBX 里就没了，还是骨骼网格导入时丢的。"""
import unreal
L = "[静态UV]"
DEST = "/Game/_TempUV"
tools = unreal.AssetToolsHelpers.get_asset_tools()
ui = unreal.FbxImportUI()
ui.set_editor_property("import_mesh", True)
ui.set_editor_property("import_materials", False)
ui.set_editor_property("import_textures", False)
ui.set_editor_property("import_animations", False)
ui.set_editor_property("mesh_type_to_import",
                       unreal.FBXImportType.FBXIT_STATIC_MESH)
ui.set_editor_property("import_as_skeletal", False)

task = unreal.AssetImportTask()
task.filename = r"C:/Users/25227/Documents/robot_game/assets/out/chassis_medium.fbx"
task.destination_path = DEST
task.destination_name = "SM_UVTest"
task.automated = True
task.save = True
task.replace_existing = True
task.options = ui
tools.import_asset_tasks([task])
paths = task.imported_object_paths
unreal.log("%s 导入结果 %d 个: %s" % (L, len(paths), [str(p) for p in paths][:4]))
for p in paths:
    m = unreal.EditorAssetLibrary.load_asset(str(p))
    if not isinstance(m, unreal.StaticMesh):
        continue
    nl = unreal.EditorStaticMeshLibrary.get_lod_count(m)
    for i in range(nl):
        n = unreal.EditorStaticMeshLibrary.get_num_uv_channels(m, i)
        unreal.log("%s %s LOD%d UV通道=%d" % (L, m.get_name(), i, n))
