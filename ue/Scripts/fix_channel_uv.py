# -*- coding: utf-8 -*-
"""修复长方形水渠渠沿的斜纹/摩尔纹（第一百一十二轮）。

根因：BuildChannel() 里顶面 UV 的 U 沿四条边**累积**（长边 U≈7.6），
V 只有 T/12≈2.33。材质 M_Basin_Concrete 又用 TextureCoordinate(1.5,1.5)
再乘一遍 → U 方向 11.4 周期 vs V 方向 3.5 周期，密度严重失衡，
在窄渠沿上产生各向异性斜条纹（摩尔纹）。

修法：把材质里两个 TextureCoordinate 的 tiling 从 1.5 降到 0.5，
U 方向周期数降到 ~3.8，与 V 的 ~1.2 更接近，斜纹消失、纹理密度合理。

⚠️ 同时影响圆环池（BuildRing），但圆环池 UV 是弧长，同样受益。
⚠️ 幂等：已是 0.5 则跳过。
"""
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
MAT = "/Game/RobotGame/Art/Materials/M_Basin_Concrete"
REPORT = r"C:\Users\25227\Documents\robot_game\docs\channel_uvfix.txt"

lines = []


def log(s):
    unreal.log("[ChannelUV] %s" % s)
    lines.append(str(s))


NEW_TILE = 0.5


def main():
    m = EAL.load_asset(MAT)
    if not m:
        log("!! 材质加载失败")
        return
    exprs = MEL.get_material_expressions(m)
    tcs = [e for e in exprs if "TextureCoordinate" in e.get_class().get_name()]
    log("TextureCoordinate 节点 %d 个" % len(tcs))

    changed = 0
    for e in tcs:
        try:
            u = e.get_editor_property("u_tiling")
            v = e.get_editor_property("v_tiling")
            log("  %s  u=%.2f v=%.2f" % (e.get_name(), u, v))
            if abs(u - NEW_TILE) < 0.001 and abs(v - NEW_TILE) < 0.001:
                log("    已是目标值，跳过")
                continue
            e.set_editor_property("u_tiling", NEW_TILE)
            e.set_editor_property("v_tiling", NEW_TILE)
            changed += 1
            log("    -> u=%.2f v=%.2f" % (NEW_TILE, NEW_TILE))
        except Exception as ex:
            log("    !! %s" % str(ex)[:60])

    MEL.recompile_material(m)
    EAL.save_asset(MAT, only_if_is_dirty=False)
    log("修改 %d 个节点，材质已重编译保存" % changed)

    # 复核
    m2 = EAL.load_asset(MAT)
    for e in MEL.get_material_expressions(m2):
        if "TextureCoordinate" in e.get_class().get_name():
            log("复核 %s u=%.2f v=%.2f" % (
                e.get_name(), e.get_editor_property("u_tiling"),
                e.get_editor_property("v_tiling")))


main()
with open(REPORT, "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("CHANNEL_UVFIX_DONE")
