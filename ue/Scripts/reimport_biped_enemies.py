# -*- coding: utf-8 -*-
"""只重导双足敌人（园丁 / 气象 / 护卫）的骨骼网格，换成带 thigh/shin/foot 三段腿骨的新骨架。

与 reimport_rigged.py 同一套做法：先删旧资产（同名不同骨架 UE 会拒绝合并），再导入。
导入后材质槽可能丢失，需再跑 fix_enemy_materials.py 补齐。
"""
import os
import unreal

FBX_DIR = r"C:\Users\25227\Documents\robot_game\assets\out"
DEST = "/Game/RobotGame/Art/Characters"
CODES = ("gardener", "weather", "guard", "hauler", "colossus")


def log(m):
    unreal.log("[双足重导] %s" % m)
    print("[双足重导] %s" % m)


def _try_set(obj, attr, value):
    try:
        setattr(obj, attr, value)
        return True
    except Exception:
        return False


def build_ui():
    ui = unreal.FbxImportUI()
    _try_set(ui, "import_mesh", True)
    _try_set(ui, "import_materials", True)
    _try_set(ui, "import_textures", False)
    _try_set(ui, "import_animations", False)
    _try_set(ui, "mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    _try_set(ui, "import_as_skeletal", True)
    data = getattr(ui, "skeletal_mesh_import_data", None)
    if data:
        _try_set(data, "import_uniform_scale", 1.0)
        _try_set(data, "convert_scene", True)
        _try_set(data, "import_content_type", unreal.FBXImportContentType.FBXICT_ALL)
    return ui


def delete_old(stems):
    sub = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    prefixes = ["SK_Enemy_" + c.capitalize() for c in CODES]
    removed = 0
    for ad in ar.get_assets_by_path(DEST, recursive=False):
        name = str(ad.asset_name)
        if any(name.startswith(p) for p in prefixes):
            pkg = str(ad.package_name)
            if sub.delete_asset(pkg):
                removed += 1
            else:
                log("  删除返回 false: %s" % pkg)
    log("删除旧资产 %d 个" % removed)


def main():
    files = ["enemy_%s.fbx" % c for c in CODES]
    delete_old(files)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    ok = 0
    for f in files:
        task = unreal.AssetImportTask()
        task.filename = os.path.join(FBX_DIR, f)
        task.destination_path = DEST
        task.destination_name = os.path.splitext(f)[0]
        task.automated = True
        task.save = True
        task.replace_existing = True
        task.options = build_ui()
        tools.import_asset_tasks([task])
        if task.imported_object_paths:
            ok += 1
            log("  [ok] %s -> %s" % (f, task.imported_object_paths[0]))
        else:
            log("  [!!] %s 无导入结果" % f)
    log("完成：成功 %d / %d" % (ok, len(files)))
    sub = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    sub.save_directory(DEST, only_if_is_dirty=False, recursive=True)


main()
unreal.log("BIPED_REIMPORT_OK")
