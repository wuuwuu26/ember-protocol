# -*- coding: utf-8 -*-
"""导入 4 个机甲碎骸到 UE（第一百一十九轮：优先用修复黑洞的 texgen 贴图）。

优先级：<name>_texgen_fixed.glb（黑洞修复）> <name>_texgen_final.glb >
        <name>_tex.glb（投影贴图版回退）。
texgen 多视图扩散在自遮挡面留下 25~36% 纯黑烘焙空洞，_fixed 版用
cv2.inpaint 补全。不动已有 6 个 Gen3D 资产，每个资产单独目录。
"""
import unreal
import os

SRC = r"C:\AI\Hunyuan3D\output"
DEST = "/Game/RobotGame/Art/Props/Gen3D"
REPORT = r"C:\Users\25227\Documents\robot_game\docs\mechwreck_import.txt"
NAMES = ["mech_torso_wreck", "severed_mech_arm",
         "mech_head_wreck", "armor_debris"]

EAL = unreal.EditorAssetLibrary
lines = []


def log(s):
    unreal.log("[MechWreckImport] %s" % s)
    lines.append(str(s))


if not EAL.does_directory_exist(DEST):
    EAL.make_directory(DEST)

for name in NAMES:
    # 优先"黑洞修复"版 texgen，其次原 texgen，最后投影贴图版
    fixed = os.path.join(SRC, name + "_texgen_fixed.glb")
    texgen = os.path.join(SRC, name + "_texgen_final.glb")
    proj = os.path.join(SRC, name + "_tex.glb")
    if os.path.exists(fixed):
        glb = fixed
    elif os.path.exists(texgen):
        glb = texgen
    else:
        glb = proj
    if not os.path.exists(glb):
        log("!! 缺 %s / %s / %s" % (fixed, texgen, proj))
        continue
    log("%s <- %s" % (name, os.path.basename(glb)))
    sub = "%s/%s" % (DEST, name)
    target = "%s/SM_%s" % (sub, name)
    if EAL.does_directory_exist(sub):
        EAL.delete_directory(sub)
    EAL.make_directory(sub)

    task = unreal.AssetImportTask()
    task.filename = glb
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
            slots = m.get_editor_property("static_materials")
            mats = [s.get_editor_property("material_interface").get_name()
                    if s.get_editor_property("material_interface") else "None"
                    for s in slots]
            log("%-20s OK  bbox=(%.0f,%.0f,%.0f)cm  mat=%s" % (
                name, bb.max.x-bb.min.x, bb.max.y-bb.min.y, bb.max.z-bb.min.z,
                mats))
        else:
            log("%-20s !! 导入后找不到" % name)
    except Exception as e:
        log("%-20s !! %s" % (name, str(e)[:80]))

with open(REPORT, "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("MECHWRECK_IMPORT_DONE")
