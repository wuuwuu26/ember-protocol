# -*- coding: utf-8 -*-
"""
定向重导入「带骨架」的资产（机体 + 敌人）。
================================================================
为什么要单独写一个而不是跑 setup_project.py：那个脚本会重导全部 51 个
FBX（含模块/道具/环境），几十秒且没有必要。这里只重导骨架变过的两类。

背景：2026-10-14 重建了骨架 —— 骨骼原点从"部件质心"移到"关节"
（thigh 在髋、shin 在膝、foot 在踝、upperarm 在肩、forearm 在肘），
并把单段 leg_L 拆成 thigh/shin/foot 三段。旧资产必须整体替换。

⚠️ 必须**先删除旧资产再导入**：UE 的 FBX 导入器遇到"骨骼层级不同"的
同名骨架时会拒绝合并（报 Failed to merge skeleton），结果还是旧骨架。
删掉再建，路径不变，关卡与蓝图里的引用会自动重新解析到新资产。

用法（编辑器命令行）：
    UnrealEditor-Cmd.exe <项目> -ExecutePythonScript="<本文件>"
"""

import os
import unreal

PROJECT_DIR = r"C:\Users\25227\Documents\robot_game"
FBX_DIR = os.path.join(PROJECT_DIR, "assets", "out")
DEST = "/Game/RobotGame/Art/Characters"
PREFIXES = ("chassis_", "enemy_")


def log(m):
    unreal.log("[重导入] %s" % m)
    print("[重导入] %s" % m)


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
    _try_set(ui, "mesh_type_to_import",
             unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    _try_set(ui, "import_as_skeletal", True)
    data = getattr(ui, "skeletal_mesh_import_data", None)
    if data:
        _try_set(data, "import_uniform_scale", 1.0)
        _try_set(data, "convert_scene", True)
        _try_set(data, "import_content_type",
                 unreal.FBXImportContentType.FBXICT_ALL)
    return ui


def delete_old(files):
    """删掉旧的骨骼网格 / 骨架 / LOD 资产。

    必须删干净：UE 的 FBX 导入器遇到同名但骨骼层级不同的骨架时会拒绝
    合并，结果是"网格换了、骨架还是旧的" —— 资产检查会报
    「此骨骼网格体资产拥有一个不兼容的骨架」，运行时程序化动画
    按名字找不到 thigh_L/shin_L，静默退回单段腿。
    """
    sub = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    prefixes = []
    for f in files:
        stem = os.path.splitext(f)[0]           # chassis_light
        parts = stem.split("_")                 # ['chassis','light']
        prefixes.append("SK_" + "_".join(p.capitalize() for p in parts))

    removed = 0
    for ad in ar.get_assets_by_path(DEST, recursive=False):
        name = str(ad.asset_name)
        if any(name.startswith(p) for p in prefixes):
            pkg = str(ad.package_name)
            try:
                if sub.delete_asset(pkg):
                    removed += 1
                else:
                    log("  删除返回 false: %s" % pkg)
            except Exception as e:
                log("  删除失败 %s: %s" % (pkg, e))
    log("删除旧资产 %d 个（匹配前缀 %s）" % (removed, prefixes))


def main():
    files = sorted(f for f in os.listdir(FBX_DIR)
                   if f.lower().endswith(".fbx")
                   and f.lower().startswith(PREFIXES))
    log("待重导入 %d 个：%s" % (len(files), ", ".join(files)))

    delete_old(files)

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    ok = fail = 0
    for f in files:
        task = unreal.AssetImportTask()
        task.filename = os.path.join(FBX_DIR, f)
        task.destination_path = DEST
        task.destination_name = os.path.splitext(f)[0]
        task.automated = True
        task.save = True
        task.replace_existing = True
        task.options = build_ui()
        try:
            tools.import_asset_tasks([task])
            paths = task.imported_object_paths
            if paths:
                ok += 1
                log("  [ok] %-28s -> %s" % (f, paths[0]))
            else:
                fail += 1
                log("  [!!] %-28s 无导入结果" % f)
        except Exception as e:
            fail += 1
            log("  [!!] %-28s 失败: %s" % (f, e))

    log("完成：成功 %d 失败 %d" % (ok, fail))
    sub = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    sub.save_directory(DEST, only_if_is_dirty=False, recursive=True)
    log("已保存 %s" % DEST)


main()

unreal.log("REIMPORT_ALL_OK")
