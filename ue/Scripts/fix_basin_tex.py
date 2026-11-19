# -*- coding: utf-8 -*-
"""修复水渠纹理（第一百一十二轮）。

根因：T_ConcreteDetail 是**颜色贴图**（BaseColor），但 srgb=False。
颜色贴图必须以 sRGB 解码，否则颜色被当线性数据 → 显示成灰白发暗、
颜色错乱的"怪纹理"。法线贴图 T_ConcreteDetail_N 的 srgb=False 是对的。

修法：T_ConcreteDetail 的 srgb 改回 True，重编译引用它的材质。
"""
import unreal

EAL = unreal.EditorAssetLibrary
REPORT = r"C:\Users\25227\Documents\robot_game\docs\basin_texfix.txt"
lines = []


def log(s):
    unreal.log("[BasinTex] %s" % s)
    lines.append(str(s))


BASE_TEX = "/Game/RobotGame/Art/Materials/T_ConcreteDetail"
NORMAL_TEX = "/Game/RobotGame/Art/Materials/T_ConcreteDetail_N"
MATERIALS = [
    "/Game/RobotGame/Art/Materials/M_Basin_Concrete",
]


def main():
    # 1. 颜色贴图 -> sRGB True
    t = EAL.load_asset(BASE_TEX)
    if not t:
        log("!! 找不到 %s" % BASE_TEX)
        return
    before = t.get_editor_property("srgb")
    if before:
        log("%s 已经是 sRGB=True，无需修改" % t.get_name())
    else:
        t.set_editor_property("srgb", True)
        EAL.save_asset(BASE_TEX, only_if_is_dirty=False)
        log("%s: sRGB False -> True（颜色贴图必须 sRGB）" % t.get_name())

    # 2. 法线贴图确认 srgb=False（正确状态）
    tn = EAL.load_asset(NORMAL_TEX)
    if tn:
        log("%s: sRGB=%s（法线贴图应为 False，保持）" % (
            tn.get_name(), tn.get_editor_property("srgb")))

    # 3. 重编译引用它的材质（贴图设置改动后需要重编译才生效）
    MEL = unreal.MaterialEditingLibrary
    for mp in MATERIALS:
        m = EAL.load_asset(mp)
        if not m:
            log("!! 材质缺失 %s" % mp)
            continue
        MEL.recompile_material(m)
        EAL.save_asset(mp, only_if_is_dirty=False)
        log("重编译 %s" % m.get_name())

    # 4. 复核
    t2 = EAL.load_asset(BASE_TEX)
    log("复核 T_ConcreteDetail sRGB = %s" % t2.get_editor_property("srgb"))


main()
with open(REPORT, "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("BASIN_TEXFIX_DONE")
