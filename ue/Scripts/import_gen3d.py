# -*- coding: utf-8 -*-
"""导入 Hunyuan3D 生成的资产到 UE（第一百一十轮）。

产物位于 C:\\AI\\Hunyuan3D\\output\\<name>.glb，
导入到 /Game/RobotGame/Art/Props/Gen3D/<name>/SM_<name>。

⚠️ Hunyuan3D 输出是**归一化单位**（约 ±1），导入后需要按目标尺寸缩放。
   这里记录导入后的包围盒，由摆放脚本决定缩放。
⚠️ 单图版没有 UV/贴图（只有几何），导入后是纯色材质，需要给一个
   工业钢材材质（复用项目已有的 M_Steel / M_Joint 等）。
"""
import unreal
import os
import glob

SRC = r"C:\AI\Hunyuan3D\output"
DEST = "/Game/RobotGame/Art/Props/Gen3D"
REPORT = r"C:\Users\25227\Documents\robot_game\docs\gen3d_import.txt"

EAL = unreal.EditorAssetLibrary
lines = []


def log(s):
    unreal.log("[Gen3D] %s" % s)
    lines.append(str(s))


if not EAL.does_directory_exist(DEST):
    EAL.make_directory(DEST)

glbs = sorted(glob.glob(os.path.join(SRC, "*.glb")))
# 优先用带投影贴图的 _tex 版本；只有在没有 _tex 时才用白模
tex_names = {os.path.basename(g)[:-8] for g in glbs if g.endswith("_tex.glb")}
imported_names = set()
todo = []
for g in glbs:
    base = os.path.basename(g)[:-4]
    if base.endswith("_tex"):
        todo.append((g, base[:-4]))          # airlock_tex.glb -> airlock
    else:
        if base in tex_names:
            continue                          # 有贴图版，跳过白模
        todo.append((g, base))

log("待导入 %d 个：%s" % (len(todo), [n for _, n in todo]))

for path, name in todo:
    # ⚠️ 只跳过真正的历史产物（mech_hunyuan / mech_textured 等），
    #    不能用 startswith("mech_") —— 会把本次生成的 mech_core 一起误杀。
    if name in ("mech_hunyuan", "mech_hunyuan_hi", "mech_textured") \
            or name.startswith("compare"):
        continue
    has_tex = name in tex_names
    sub = "%s/%s" % (DEST, name)
    target = "%s/SM_%s" % (sub, name)

    if EAL.does_directory_exist(sub):
        EAL.delete_directory(sub)
    EAL.make_directory(sub)

    task = unreal.AssetImportTask()
    task.filename = path
    task.destination_path = sub
    task.destination_name = "SM_%s" % name
    task.automated = True
    task.save = True
    task.replace_existing = True

    ui = unreal.FbxImportUI()
    ui.import_mesh = True
    ui.import_materials = True
    ui.import_textures = True
    ui.import_animations = False
    ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    ui.automated_import_should_detect_type = False
    task.options = ui

    try:
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        m = EAL.load_asset(target)
        if m:
            bb = m.get_bounding_box()
            log("%-14s 导入 OK  bbox=(%.1f, %.1f, %.1f)cm  min=(%.1f,%.1f,%.1f)  %s" % (
                name, bb.max.x - bb.min.x, bb.max.y - bb.min.y, bb.max.z - bb.min.z,
                bb.min.x, bb.min.y, bb.min.z,
                "带投影贴图" if has_tex else "白模"))
            # 只有白模（无贴图）才换成项目工业材质；带贴图的保留投影材质
            if not has_tex:
                steel = EAL.load_asset("/Game/RobotGame/Art/Environment/M_Steel")
                if steel:
                    try:
                        n = max(1, len(m.get_editor_property("static_materials")))
                        for i in range(n):
                            m.set_material(i, steel)
                        EAL.save_asset(target, only_if_is_dirty=False)
                        log("    材质槽 -> M_Steel")
                    except Exception as e:
                        log("    材质替换失败：%s" % str(e)[:70])
        else:
            log("%-14s !! 导入后找不到资产" % name)
    except Exception as e:
        log("%-14s !! %s: %s" % (name, type(e).__name__, str(e)[:80]))

with open(REPORT, "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("GEN3D_IMPORT_DONE")
