# -*- coding: utf-8 -*-
"""重新导入正确尺度的 SM_Env_SludgePool。"""
import unreal

ENV_DIR = "/Game/RobotGame/Art/Environment"
FBX_PATH = r"C:\Users\25227\Documents\robot_game\assets\out\env_sludge_pool.fbx"

tools = unreal.AssetToolsHelpers.get_asset_tools()
fbx_task = unreal.AssetImportTask()
fbx_task.filename = FBX_PATH
fbx_task.destination_path = ENV_DIR
fbx_task.destination_name = "SM_Env_SludgePool"
fbx_task.automated = True
fbx_task.save = True
fbx_task.replace_existing = True

fbx_ui = unreal.FbxImportUI()
fbx_ui.import_mesh = True
fbx_ui.import_materials = False
fbx_ui.import_textures = False
fbx_ui.import_animations = False
fbx_ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
fbx_task.options = fbx_ui

tools.import_asset_tasks([fbx_task])

sm = unreal.EditorAssetLibrary.load_asset(f"{ENV_DIR}/SM_Env_SludgePool")
if sm:
    box = sm.get_bounds()
    unreal.log(f"Reimported Bounds: Origin={box.origin}, Extent={box.box_extent}, Radius={box.sphere_radius}")

with open(r"C:\Users\25227\Documents\robot_game\docs\sludge_reimported.txt", "w", encoding="utf-8") as f:
    f.write(f"Extent: {box.box_extent}\nSLUDGE_REIMPORT_DONE\n")
