# -*- coding: utf-8 -*-
"""导入 Poly Haven 贴图并建 UE 材质（第一百零六轮）。

⚠️ 幂等：先删 /Game/RobotGame/Art/Materials/PolyHaven 下的旧资产。

建材质方式：用 MaterialEditingLibrary 创建 Material + 节点连线。
  BaseColor -> BaseColor
  Normal    -> Normal（Texture 设 sRGB=False / TC_Normalmap）
  ARM(jpg)  -> R=AO, G=Roughness, B=Metallic（UE 的 ORM 顺序）
              用 ComponentMask 分别取通道

⚠️ 第一百零二轮踩过的坑：关卡里 StaticMeshActor 的地面是**显式
   override_materials**，不是网格默认材质。要改地面外观，必须改 actor 的
   override，不能只改网格资产。所以这个脚本只建材质资产，应用放到
   apply_polyhaven.py 里做（分两步，便于单独重跑）。
"""
import unreal
import os
import glob

SRC = r"C:\Users\25227\Documents\robot_game\art_src\polyhaven"
DEST = "/Game/RobotGame/Art/Materials/PolyHaven"
REPORT = r"C:\Users\25227\Documents\robot_game\docs\polyhaven_import.txt"

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
lines = []


def log(s):
    unreal.log("[PolyImport] %s" % s)
    lines.append(str(s))


if not EAL.does_directory_exist(DEST):
    EAL.make_directory(DEST)
    log("创建目录 %s" % DEST)

texture_assets = {}   # (aid, suffix) -> Texture2D

# ── 1. 导入所有贴图 ──
for folder in sorted(glob.glob(os.path.join(SRC, "*"))):
    if not os.path.isdir(folder):
        continue
    aid = os.path.basename(folder)
    sub = "%s/%s" % (DEST, aid)
    if EAL.does_directory_exist(sub):
        EAL.delete_directory(sub)
    EAL.make_directory(sub)

    for jpg in sorted(glob.glob(os.path.join(folder, "*.jpg"))):
        name = os.path.splitext(os.path.basename(jpg))[0]
        task = unreal.AssetImportTask()
        task.filename = jpg
        task.destination_path = sub
        task.destination_name = name
        task.automated = True
        task.save = True
        task.replace_existing = True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        p = "%s/%s" % (sub, name)
        tex = EAL.load_asset(p)
        if tex:
            suffix = name.split("_")[-1]
            texture_assets[(aid, suffix)] = tex
            # 法线与 ARM 不是颜色：关 sRGB
            if suffix in ("Normal", "ARM"):
                try:
                    tex.set_editor_property("srgb", False)
                    EAL.save_asset(p, only_if_is_dirty=False)
                except Exception as e:
                    log("  srgb 设置失败 %s: %s" % (name, e))
            log("  导入 %s" % name)
        else:
            log("  !! 导入失败 %s" % name)

# ── 2. 为每套建材质 ──
MAT_DESC = {
    "concrete_floor_02": "工业混凝土地面",
    "concrete_wall_001": "风化混凝土墙",
    "factory_wall": "工厂金属墙",
    "rusty_metal": "锈铁",
    "corrugated_iron": "波纹铁皮",
    "metal_grate_rusty": "锈金属格栅",
}

for aid, desc in MAT_DESC.items():
    mat_path = "%s/M_%s" % (DEST, aid)
    if EAL.does_asset_exist(mat_path):
        EAL.delete_asset(mat_path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        aid and ("M_%s" % aid), DEST,
        unreal.Material, unreal.MaterialFactoryNew())
    if not mat:
        log("!! 材质创建失败 %s" % aid)
        continue

    def tex_node(suffix, x, y, srgb):
        t = texture_assets.get((aid, suffix))
        if not t:
            log("  !! %s 缺 %s 贴图" % (aid, suffix))
            return None
        n = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, x, y)
        n.set_editor_property("texture", t)
        return n

    bc = tex_node("BaseColor", -600, -200, True)
    nm = tex_node("Normal", -600, 100, False)
    arm = tex_node("ARM", -600, 400, False)

    if bc:
        MEL.connect_material_property(bc, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    if nm:
        MEL.connect_material_property(nm, "RGB", unreal.MaterialProperty.MP_NORMAL)
    if arm:
        # R=AO / G=Roughness / B=Metallic
        for chan, prop, yy in (
            ("R", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION, 380),
            ("G", unreal.MaterialProperty.MP_ROUGHNESS, 480),
            ("B", unreal.MaterialProperty.MP_METALLIC, 580),
        ):
            mask = MEL.create_material_expression(
                mat, unreal.MaterialExpressionComponentMask, -350, yy)
            mask.set_editor_property(chan.lower(), True) if False else None
            # 用 properties 设置（ComponentMask 的 r/g/b 是 bool 属性）
            try:
                mask.set_editor_property({"R": "r", "G": "g", "B": "b"}[chan], True)
            except Exception:
                pass
            MEL.connect_material_expressions(arm, chan, mask, "Input")
            MEL.connect_material_property(mask, "", prop)

    MEL.recompile_material(mat)
    EAL.save_asset(mat_path, only_if_is_dirty=False)
    log("材质 M_%s (%s) 已建" % (aid, desc))

with open(REPORT, "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("POLYHAVEN_IMPORT_DONE")
