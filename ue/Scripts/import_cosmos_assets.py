# -*- coding: utf-8 -*-
"""把 Cosmos GLB 批量导入 UE（第一百零四轮）。

导入路径：/Game/RobotGame/Art/Props/Cosmos/<slug>/SM_<slug>
导入器：UE 5.8 内置 glTF(Interchange)。上一轮 IdolMech.glb 走的就是它，
        能保住 PBR 贴图与 Nanite。

⚠️ 幂等：每个 slug 单独一个目录，重跑前先删该目录。
⚠️ GLB 里贴图已缩到 1024，几何是 LOD0（部分资产名字带 Nanite，
        面数到 15 万，导入时开 Nanite 由 UE 自行处理）。
"""
import unreal
import os
import glob

GLB_DIR = r"C:\Users\25227\Documents\robot_game\art_src\cosmos\glb"
DEST = "/Game/RobotGame/Art/Props/Cosmos"
REPORT = r"C:\Users\25227\Documents\robot_game\docs\cosmos_import.txt"

EAL = unreal.EditorAssetLibrary
lines = []


def log(s):
    unreal.log("[CosmosImport] %s" % s)
    lines.append(str(s))


if not EAL.does_directory_exist(DEST):
    EAL.make_directory(DEST)
    log("创建目录 %s" % DEST)

glbs = sorted(glob.glob(os.path.join(GLB_DIR, "*.glb")))
log("待导入 GLB %d 个" % len(glbs))

for path in glbs:
    slug = os.path.splitext(os.path.basename(path))[0]
    sub = "%s/%s" % (DEST, slug)
    name = "SM_%s" % slug
    target = "%s/%s" % (sub, name)

    # 幂等：删掉旧目录
    if EAL.does_directory_exist(sub):
        EAL.delete_directory(sub)
        log("清理旧目录 %s" % sub)
    EAL.make_directory(sub)

    task = unreal.AssetImportTask()
    task.filename = path
    task.destination_path = sub
    task.destination_name = name
    task.automated = True
    task.save = True
    task.replace_existing = True

    ui = unreal.FbxImportUI()          # glTF 也走 ImportUI 的通用部分
    ui.import_mesh = True
    ui.import_materials = True
    ui.import_textures = True
    ui.import_animations = False
    ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    ui.automated_import_should_detect_type = False
    task.options = ui

    try:
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        imported = [str(p) for p in task.imported_object_paths]
        log("%-38s -> %s" % (slug, imported))
    except Exception as e:
        log("%-38s !! %s: %s" % (slug, type(e).__name__, e))

    # 复核
    m = EAL.load_asset(target)
    if m:
        try:
            bb = m.get_bounding_box()
            log("      bbox=(%.1f, %.1f, %.1f)cm  mats=%d" %
                (bb.max.x-bb.min.x, bb.max.y-bb.min.y, bb.max.z-bb.min.z,
                 len(m.get_editor_property("static_materials"))))
        except Exception as e:
            log("      复核失败 %s" % e)
    else:
        # 名字可能不是 SM_ 前缀，列一下目录
        got = [a.split("/")[-1] for a in EAL.list_assets(sub, recursive=False)]
        log("      !! 目标名未命中，目录里有: %s" % got)

with open(REPORT, "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("COSMOS_IMPORT_DONE")
