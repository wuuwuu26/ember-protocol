# -*- coding: utf-8 -*-
"""
为弹丸新建两个专用 Unlit 自发光材质：M_Bolt_Player（青白）/ M_Bolt_Enemy（橙金）。

为什么不能用现成的 M_Core_light / M_Core_enemy_guard：
    那两个是**机体核心**的材质，自发光要靠机体网格的 UV 去采样自发光遮罩
    （只有核心那一小块有值）。套到引擎球体上，UV 采到的基本全是黑的 ——
    实测弹丸在夜景里是一根**暗紫色扁平椭圆**，只有月光的高光边，
    完全没有"曳光弹"的亮度。这正是前几轮"弹丸像紫药丸"的真正原因：
    不是尺寸问题，是材质根本不发光。

做法：
    Unlit + EmissiveColor 直接输出线性颜色，不参与光照。
    亮度取 3~4（线性），经 ACES 后接近白，泛光会给一圈同色光晕 ——
    这就是"能量弹"该有的读法。
"""
import unreal

MAT_DIR = "/Game/RobotGame/Art/Materials"

BOLTS = [
    # (资产名, 颜色线性值, 说明)
    # ★ 2026-10-25 根因大突破：
    #   物理曝光下场景亮度基准是数百 nit（地面在光池 120,000cd 下超 300 nit，
    #   天空穹顶都用了 75.0 倍乘数才从死黑变深蓝）。
    #   之前弹丸设 (0.5, 6.0, 8.0) 只有 8 nit —— 刚好等于夜空的深蓝亮度！
    #   在物理相机看来，8 nit 就是深色剪影，所以在夜空背景里是一团暗红/暗蓝污迹。
    #   曳光弹核心必须远超地面光照（500~800 nit），才能压穿色调映射下趾、
    #   逼出纯白内核并在周围炸开一圈耀眼的青白 / 橙金泛光（Bloom）。
    ("M_Bolt_Player", (150.0, 550.0, 750.0), "玩家：极亮青白曳光"),
    ("M_Bolt_Enemy", (750.0, 300.0, 35.0), "敌人：极亮橙金曳光"),
]


def log(m):
    unreal.log("[弹丸材质] %s" % m)


def make_bolt(name, color, desc):
    path = "%s/%s" % (MAT_DIR, name)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        mat = unreal.EditorAssetLibrary.load_asset(path)
        # 清掉旧表达式，避免反复叠加
        for e in unreal.MaterialEditingLibrary.get_material_expressions(mat):
            unreal.MaterialEditingLibrary.delete_material_expression(mat, e)
        log("更新 %s" % name)
    else:
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
        log("新建 %s" % name)

    mat.set_editor_property("shading_model",
                            unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("two_sided", False)

    # ★ 关键根因修复：
    # 之前用 MaterialExpressionVectorParameter，在没有材质实例（MIC）的情况下，
    # 基础材质直接挂到 StaticMesh 上时，参数的 DefaultValue 并不一定被编译进
    # 常量缓冲区（实测 Uniform 参数在基础材质直接渲染时全按 0 算，导致弹丸全黑）。
    # 改用 MaterialExpressionConstant3Vector，数值作为硬常量直接写进 HLSL，
    # 任何情况下都不可能被置零！
    col = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant3Vector, -420, 0)
    col.set_editor_property(
        "constant",
        unreal.LinearColor(color[0], color[1], color[2], 1.0))

    unreal.MaterialEditingLibrary.connect_material_property(
        col, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    log("%s %s color=%s" % (name, desc, color))


for n, c, d in BOLTS:
    make_bolt(n, c, d)

try:
    with open(r"C:\Users\25227\Documents\robot_game\docs\bolt_mats.txt", "w") as f:
        f.write("M_Bolt_Player / M_Bolt_Enemy created\nBOLTMATS_DONE\n")
except Exception as e:
    log("写结果失败 %s" % str(e))
