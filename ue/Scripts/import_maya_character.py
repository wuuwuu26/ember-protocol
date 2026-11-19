# -*- coding: utf-8 -*-
"""在 UE 5.8 中将 Maya 2027 导出的精细人物模型导入为 SK_Pilot_Maya。"""
import unreal

CHAR_DIR = "/Game/RobotGame/Art/Characters"
FBX_PATH = r"C:\Users\25227\Documents\robot_game\assets\out\maya_pilot_hero_clean.fbx"

sub = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
mp = f"{CHAR_DIR}/SK_Pilot_Maya"
if unreal.EditorAssetLibrary.does_asset_exist(mp):
    sub.delete_asset(mp)

ui = unreal.FbxImportUI()
ui.set_editor_property("import_mesh", True)
ui.set_editor_property("import_materials", True)
ui.set_editor_property("import_textures", False)
ui.set_editor_property("import_animations", False)
ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
ui.set_editor_property("import_as_skeletal", True)

data = getattr(ui, "skeletal_mesh_import_data", None)
if data:
    data.set_editor_property("import_uniform_scale", 1.0)
    data.set_editor_property("convert_scene", True)

task = unreal.AssetImportTask()
task.filename = FBX_PATH
task.destination_path = CHAR_DIR
task.destination_name = "SK_Pilot_Maya"
task.automated = True
task.save = True
task.replace_existing = True
task.options = ui

unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

sk = unreal.EditorAssetLibrary.load_asset(mp)
num_slots = 0
if sk:
    mats = sk.get_editor_property("materials")
    num_slots = len(mats)
    unreal.log(f"SK_Pilot_Maya 导入成功! 材质槽数量: {num_slots}")
    for idx, sm in enumerate(mats):
        unreal.log(f"  Slot {idx}: {sm.get_editor_property('material_slot_name')}")

with open(r"C:\Users\25227\Documents\robot_game\docs\maya_imported.txt", "w", encoding="utf-8") as f:
    f.write(f"SK_Pilot_Maya slots={num_slots}\nMAYA_IMPORT_DONE\n")
