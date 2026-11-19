# -*- coding: utf-8 -*-
"""微调 M_Splash_Foam：降低过曝、让气泡纹理可见（第一百一十二轮）。

第一版重建后圆盘变成刺眼纯白：Emissive 系数 0.35 太高，
场景曝光又偏亮，气泡点全被淹没。

调整：
  Emissive × 0.35 -> 0.06   （几乎不发光，只留极轻高光）
  BaseColor 气泡叠加 0.18 -> 0.40  （气泡点明暗更明显）
  浅色底 0.55/0.75/0.80 -> 0.32/0.48/0.55（偏深一点，贴近水色，不刺眼）
"""
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
MAT = "/Game/RobotGame/Art/Materials/M_Splash_Foam"
REPORT = r"C:\Users\25227\Documents\robot_game\docs\splash_tune.txt"

lines = []


def log(s):
    unreal.log("[SplashTune] %s" % s)
    lines.append(str(s))


def main():
    m = EAL.load_asset(MAT)
    if not m:
        log("!! 材质缺失")
        return
    exprs = MEL.get_material_expressions(m)

    n = 0
    for e in exprs:
        cls = e.get_class().get_name()
        if cls == "MaterialExpressionConstant3Vector":
            c = e.get_editor_property("constant")
            # 浅色底（第一个常量，接近 0.55/0.75/0.80 的那个）
            if abs(c.r - 0.55) < 0.02 and abs(c.g - 0.75) < 0.02:
                e.set_editor_property("constant",
                    unreal.LinearColor(0.32, 0.48, 0.55, 1.0))
                log("浅色底 -> (0.32, 0.48, 0.55)")
                n += 1
        elif cls == "MaterialExpressionConstant":
            r = e.get_editor_property("r")
            if abs(r - 0.18) < 0.01:
                e.set_editor_property("r", 0.40)
                log("BaseColor 气泡叠加 0.18 -> 0.40")
                n += 1
            elif abs(r - 0.35) < 0.01:
                e.set_editor_property("r", 0.06)
                log("Emissive 系数 0.35 -> 0.06")
                n += 1

    MEL.recompile_material(m)
    EAL.save_asset(MAT, only_if_is_dirty=False)
    log("调整 %d 个常量，已保存" % n)


main()
with open(REPORT, "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("SPLASH_TUNE_DONE")
