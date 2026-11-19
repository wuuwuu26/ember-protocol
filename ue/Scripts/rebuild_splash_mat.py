# -*- coding: utf-8 -*-
"""重建 M_Splash_Foam：浅色泡沫底 + 气泡纹理细节（第一百一十二轮）。

现状（错误）：BaseColor 直接接 T_Toxic_Bub（黑底白点遮罩图），
→ 圆盘大部分区域是黑的 / 或编辑器缓存导致显示纯浅色无细节。

正确设计：
  BaseColor = 浅蓝白常量 (0.55,0.75,0.80)
              + 气泡贴图 × 小系数（给表面一点明暗颗粒）
  Emissive  = 气泡贴图 × 亮度（白色气泡点微微发光，模拟水花高光）
  Roughness = 0.6（湿润泡沫）
  Opacity   = 保持不透明（原 blend Opaque）

⚠️ 用 delete_all_material_expressions 清空重建，避免旧连线残留。
"""
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
MAT = "/Game/RobotGame/Art/Materials/M_Splash_Foam"
TEX = "/Game/RobotGame/Art/Materials/T_Toxic_Bub"
REPORT = r"C:\Users\25227\Documents\robot_game\docs\splash_rebuild.txt"
MP = unreal.MaterialProperty

lines = []


def log(s):
    unreal.log("[SplashRebuild] %s" % s)
    lines.append(str(s))


def main():
    m = EAL.load_asset(MAT)
    t = EAL.load_asset(TEX)
    if not m or not t:
        log("!! 材质或贴图缺失")
        return

    # 清空所有旧节点
    MEL.delete_all_material_expressions(m)
    log("已清空旧节点")

    def add(cls, x, y):
        return MEL.create_material_expression(m, cls, x, y)

    # 贴图采样（UV 用默认）
    tex = add(unreal.MaterialExpressionTextureSample, -700, -100)
    tex.set_editor_property("texture", t)

    # ── BaseColor：浅色底 + 气泡纹理轻微叠加 ──
    base = add(unreal.MaterialExpressionConstant3Vector, -700, 150)
    base.set_editor_property("constant", unreal.LinearColor(0.55, 0.75, 0.80, 1.0))

    detail_scale = add(unreal.MaterialExpressionConstant, -450, -20)
    detail_scale.set_editor_property("r", 0.18)   # 气泡贴图对明度的贡献

    tex_mul = add(unreal.MaterialExpressionMultiply, -250, -100)
    MEL.connect_material_expressions(tex, "RGB", tex_mul, "A")
    MEL.connect_material_expressions(detail_scale, "", tex_mul, "B")

    base_final = add(unreal.MaterialExpressionAdd, -50, 0)
    MEL.connect_material_expressions(base, "", base_final, "A")
    MEL.connect_material_expressions(tex_mul, "", base_final, "B")
    MEL.connect_material_property(base_final, "", MP.MP_BASE_COLOR)

    # ── Emissive：气泡白点微光 ──
    emis_scale = add(unreal.MaterialExpressionConstant, -450, 250)
    emis_scale.set_editor_property("r", 0.35)
    emis = add(unreal.MaterialExpressionMultiply, -250, 220)
    MEL.connect_material_expressions(tex, "RGB", emis, "A")
    MEL.connect_material_expressions(emis_scale, "", emis, "B")
    MEL.connect_material_property(emis, "", MP.MP_EMISSIVE_COLOR)

    # ── Roughness ──
    rough = add(unreal.MaterialExpressionConstant, -250, 400)
    rough.set_editor_property("r", 0.6)
    MEL.connect_material_property(rough, "", MP.MP_ROUGHNESS)

    MEL.recompile_material(m)
    EAL.save_asset(MAT, only_if_is_dirty=False)

    # 复核
    m2 = EAL.load_asset(MAT)
    exprs = MEL.get_material_expressions(m2)
    log("重建后节点 %d 个" % len(exprs))
    for pname, prop in [("BaseColor", MP.MP_BASE_COLOR),
                        ("Emissive", MP.MP_EMISSIVE_COLOR),
                        ("Roughness", MP.MP_ROUGHNESS)]:
        node = MEL.get_material_property_input_node(m2, prop)
        log("  %-10s <- %s" % (pname, node.get_class().get_name() if node else "未连接"))


main()
with open(REPORT, "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("SPLASH_REBUILD_DONE")
