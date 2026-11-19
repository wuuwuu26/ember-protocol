# -*- coding: utf-8 -*-
"""导入 AI 细节贴图 + 法线，并接到各材质实例的 DetailTex / NormalTex。

材质本身已经是参数化的（DetailTex / NormalTex / TextureSize / Metallic /
Roughness / WearAmount ...），所以这里**不改材质图**，只换贴图和调参 ——
风险最小，而且随时能换回旧贴图。
"""
import os
import unreal

SRC = r"C:\Users\25227\Documents\robot_game\art_src\textures"
TEX_DIR = "/Game/RobotGame/Art/Materials/AIDetail"
L = "[贴图]"

sub = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()
MEL = unreal.MaterialEditingLibrary

# 材质实例 -> (细节贴图, 法线贴图, TextureSize)
# TextureSize 是"一张贴图覆盖的世界尺寸(cm)"：角色件小、环境件大。
ASSIGN = {
    # ── 角色 ──
    "/Game/RobotGame/Art/Characters/M_Steel":       ("tex_mech_armor", 190.0),
    "/Game/RobotGame/Art/Characters/M_SteelLight":  ("tex_mech_armor", 190.0),
    "/Game/RobotGame/Art/Characters/M_Joint":       ("tex_mech_joint", 130.0),
    "/Game/RobotGame/Art/Characters/M_Copper":      ("tex_mech_copper", 150.0),
    "/Game/RobotGame/Art/Characters/M_Frame":       ("tex_mech_joint", 120.0),
    # ── 环境 ──
    "/Game/RobotGame/Art/Environment/M_Steel":      ("tex_env_concrete", 520.0),
    "/Game/RobotGame/Art/Environment/M_SteelLight": ("tex_env_paint", 480.0),
    "/Game/RobotGame/Art/Environment/M_Joint":      ("tex_mech_joint", 260.0),
    "/Game/RobotGame/Art/Props/M_Steel":            ("tex_env_paint", 420.0),
    "/Game/RobotGame/Art/Props/M_Copper":           ("tex_mech_copper", 260.0),
}

# 所有机型/敌人的强调色材质：用装甲贴图，只是基色不同
ACCENT_GLOB = ["/Game/RobotGame/Art/Characters/M_Accent_"]
ACCENT_TEX = ("tex_mech_armor", 200.0)


def log(m):
    unreal.log("%s %s" % (L, m))


def ensure_dir(d):
    if not unreal.EditorAssetLibrary.does_directory_exist(d):
        unreal.EditorAssetLibrary.make_directory(d)


def import_tex(name, normal=False):
    src = os.path.join(SRC, name + ".png")
    path = "%s/%s" % (TEX_DIR, name)
    if not os.path.exists(src):
        log("缺源图 %s" % src)
        return None
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        sub.delete_asset(path)
    task = unreal.AssetImportTask()
    task.filename = src
    task.destination_path = TEX_DIR
    task.destination_name = name
    task.automated = True
    task.save = True
    task.replace_existing = True
    tools.import_asset_tasks([task])
    t = unreal.EditorAssetLibrary.load_asset(path)
    if not t:
        log("导入失败 %s" % name)
        return None
    if normal:
        t.set_editor_property("srgb", False)
        t.set_editor_property("compression_settings",
                              unreal.TextureCompressionSettings.TC_NORMALMAP)
    else:
        t.set_editor_property("srgb", True)
        t.set_editor_property("compression_settings",
                              unreal.TextureCompressionSettings.TC_DEFAULT)
    unreal.EditorAssetLibrary.save_asset(path)
    return t


def main():
    ensure_dir(TEX_DIR)

    # 1) 导入全部贴图（颜色 + 法线）
    names = set(v[0] for v in ASSIGN.values()) | {ACCENT_TEX[0]}
    tex_cache = {}
    for n in sorted(names):
        tex_cache[n] = import_tex(n)
        tex_cache[n + "_N"] = import_tex(n + "_N", normal=True)
        log("导入 %s" % n)

    # 2) 汇总要处理的材质实例（含所有 Accent_*）
    targets = dict(ASSIGN)
    accent_names = [
        "M_Accent_heavy", "M_Accent_light", "M_Accent_medium",
        "M_AccentDark_heavy", "M_AccentDark_light", "M_AccentDark_medium",
        "M_Accent_enemy_colossus", "M_Accent_enemy_gardener",
        "M_Accent_enemy_guard", "M_Accent_enemy_hauler",
        "M_Accent_enemy_patrol", "M_Accent_enemy_weather",
        "M_AccentDark_enemy_guard", "M_AccentDark_enemy_hauler",
    ]
    for nm in accent_names:
        targets.setdefault("/Game/RobotGame/Art/Characters/%s" % nm, ACCENT_TEX)

    applied = 0
    for path, (tex_name, size) in sorted(targets.items()):
        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            continue
        mi = unreal.EditorAssetLibrary.load_asset(path)
        if not isinstance(mi, unreal.MaterialInstanceConstant):
            continue
        color = tex_cache.get(tex_name)
        nrm = tex_cache.get(tex_name + "_N")
        if not color:
            continue
        MEL.set_material_instance_texture_parameter_value(mi, "DetailTex", color)
        if nrm:
            MEL.set_material_instance_texture_parameter_value(mi, "NormalTex", nrm)
        try:
            MEL.set_material_instance_scalar_parameter_value(mi, "TextureSize", size)
            MEL.set_material_instance_scalar_parameter_value(mi, "NormalStrength", 0.55)
            MEL.set_material_instance_scalar_parameter_value(mi, "DetailAmount", 1.0)
        except Exception:
            pass
        unreal.EditorAssetLibrary.save_asset(path)
        applied += 1

    log("已更新 %d 个材质实例" % applied)


main()
unreal.log("TEXTURES_OK")
