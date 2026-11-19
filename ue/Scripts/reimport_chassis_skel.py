# -*- coding: utf-8 -*-
"""重导入机体：显式指定导入到已有的 Skeleton 资产。

背景：普通重导入之后 SK_Chassis_* 的 skeleton 引用为空，
运行时报 "SK_Chassis_Light missing skeleton"（BoneContainer.cpp:165）直接崩溃。
原因是 FBX 文件名（chassis_light）和网格名（SK_Chassis_Light）不一致，
导入器新建了 Skeleton 却没回填到网格上。显式给 ui.skeleton 可以绕开。
"""
import os
import unreal

L = "[机体导入]"
FBX_DIR = r"C:/Users/25227/Documents/robot_game/assets/out"
DEST = "/Game/RobotGame/Art/Characters"
sub = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)

for code in ("light", "medium", "heavy"):
    fbx = os.path.join(FBX_DIR, "chassis_%s.fbx" % code)
    mesh_name = "SK_Chassis_%s" % code.capitalize()
    skel_path = "%s/chassis_%s_Skeleton" % (DEST, code)
    skel = unreal.EditorAssetLibrary.load_asset(skel_path)

    # 只删网格，保留骨架
    mp = "%s/%s" % (DEST, mesh_name)
    if unreal.EditorAssetLibrary.does_asset_exist(mp):
        sub.delete_asset(mp)

    ui = unreal.FbxImportUI()
    ui.set_editor_property("import_mesh", True)
    ui.set_editor_property("import_materials", True)
    ui.set_editor_property("import_textures", False)
    ui.set_editor_property("import_animations", False)
    ui.set_editor_property("mesh_type_to_import",
                           unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    ui.set_editor_property("import_as_skeletal", True)
    if skel:
        try:
            ui.set_editor_property("skeleton", skel)
            unreal.log("%s 指定骨架 %s" % (L, skel_path))
        except Exception as e:
            unreal.log("%s ⚠️ 指定骨架失败: %s" % (L, str(e)[:70]))
    data = getattr(ui, "skeletal_mesh_import_data", None)
    if data:
        data.set_editor_property("import_uniform_scale", 1.0)
        data.set_editor_property("convert_scene", True)

    task = unreal.AssetImportTask()
    task.filename = fbx
    task.destination_path = DEST
    task.destination_name = mesh_name
    task.automated = True
    task.save = True
    task.replace_existing = True
    task.options = ui
    try:
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        m = unreal.EditorAssetLibrary.load_asset(mp)
        sk = None
        if m:
            try:
                sk = m.get_editor_property("skeleton")
            except Exception:
                pass
        unreal.log("%s %-20s → 骨架=%s" % (L, mesh_name, sk.get_name() if sk else "❌ 空"))
    except Exception as e:
        unreal.log("%s %s 导入失败: %s" % (L, mesh_name, str(e)[:70]))

unreal.get_editor_subsystem(unreal.EditorAssetSubsystem).save_directory(
    DEST, only_if_is_dirty=False, recursive=True)
