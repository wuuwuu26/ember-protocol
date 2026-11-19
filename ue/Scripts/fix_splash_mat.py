# -*- coding: utf-8 -*-
"""修复注水落点泡沫圆盘的纹理（第一百一十二轮）。

根因：M_Splash_Foam 的 BaseColor 接的是**纯色常量**
(0.55,0.75,0.80)，贴图 T_Toxic_Bub 只接到 Emissive；
且该贴图 srgb=False（颜色贴图错误）。
→ Splash_FoamRing / Splash_FoamDisc 两个圆盘显示成纯浅色无纹理，
   与波光水面脱节，就是用户说的"注入与水面接触处没有纹理"。

修法：
  1) T_Toxic_Bub 的 srgb 改 True（颜色贴图）
  2) 把贴图采样接到 BaseColor（保留原 Emissive 不变，仍有微光）
  3) 断开 BaseColor 上原来的纯色常量

⚠️ 幂等：若 BaseColor 已是 TextureSample 则跳过。
"""
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
MAT = "/Game/RobotGame/Art/Materials/M_Splash_Foam"
TEX = "/Game/RobotGame/Art/Materials/T_Toxic_Bub"
REPORT = r"C:\Users\25227\Documents\robot_game\docs\splash_fix.txt"

MP = unreal.MaterialProperty
lines = []


def log(s):
    unreal.log("[SplashFix] %s" % s)
    lines.append(str(s))


def main():
    m = EAL.load_asset(MAT)
    if not m:
        log("!! 材质加载失败")
        return

    # 1. 贴图 sRGB
    t = EAL.load_asset(TEX)
    if t:
        was = t.get_editor_property("srgb")
        if not was:
            t.set_editor_property("srgb", True)
            EAL.save_asset(TEX, only_if_is_dirty=False)
            log("%s: srgb False -> True" % t.get_name())
        else:
            log("%s: srgb 已为 True" % t.get_name())

    # 2. 找贴图采样节点 & 当前 BaseColor 输入
    exprs = MEL.get_material_expressions(m)
    tex_sample = None
    for e in exprs:
        if "TextureSample" in e.get_class().get_name():
            tex_sample = e
            break
    if not tex_sample:
        log("!! 找不到贴图采样节点")
        return

    cur = MEL.get_material_property_input_node(m, MP.MP_BASE_COLOR)
    cur_cls = cur.get_class().get_name() if cur else "None"
    log("BaseColor 当前输入 = %s" % cur_cls)

    if cur and "TextureSample" in cur_cls:
        log("BaseColor 已接贴图，跳过（幂等）")
        return

    # 3. 断开旧连接，把贴图接到 BaseColor
    MEL.disconnect_material_property(m, MP.MP_BASE_COLOR)
    MEL.connect_material_property(tex_sample, "RGB", MP.MP_BASE_COLOR)
    log("BaseColor <- %s (贴图 RGB)" % tex_sample.get_name())

    # 4. 贴图太暗时给个轻微提亮：把原纯色常量乘上去（可选，先不加，
    #    因为贴图本身有气泡明暗，纯色会冲淡纹理）

    MEL.recompile_material(m)
    EAL.save_asset(MAT, only_if_is_dirty=False)
    log("材质已重编译保存")

    # 复核
    m2 = EAL.load_asset(MAT)
    chk = MEL.get_material_property_input_node(m2, MP.MP_BASE_COLOR)
    log("复核 BaseColor <- %s" % (chk.get_class().get_name() if chk else "未连接"))


main()
with open(REPORT, "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("SPLASH_FIX_DONE")
