# -*- coding: utf-8 -*-
"""修复地面纹理被拉伸（第一百一十一轮）。

问题：Poly Haven 贴图是真实尺度扫描（约 2m 一张），而地面块
SM_Env_Floor 是 400×400cm，材质用默认 UV(0-1) 铺满整块
→ 纹理被放大 2 倍，细节全糊，看起来像"没加载"。

修法：给每个 TextureSample 的 UV 输入接 TextureCoordinate × 2.0，
让 1 张贴图覆盖约 200cm（符合真实尺度），细节密度翻倍。

⚠️ 幂等：已接 TextureCoordinate 的跳过，不重复叠加。
⚠️ 只改地面材质 M_concrete_floor_02；墙面是竖直的，UV 情况不同，暂不动。
"""
import unreal

PH = "/Game/RobotGame/Art/Materials/PolyHaven"
REPORT = r"C:\Users\25227\Documents\robot_game\docs\floor_uvfix.txt"

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
lines = []


def log(s):
    unreal.log("[FloorUV] %s" % s)
    lines.append(str(s))


TILE = 2.0          # 平铺倍数：400cm 块 / 2 = 200cm 一张贴图


def main():
    path = PH + "/M_concrete_floor_02"
    mat = EAL.load_asset(path)
    if not mat:
        log("!! 材质加载失败")
        return

    exprs = MEL.get_material_expressions(mat)
    samples = [e for e in exprs if "TextureSample" in e.get_class().get_name()]
    log("贴图采样节点 %d 个" % len(samples))

    # 幂等：已有 TextureCoordinate 就不重复加
    if any("TextureCoordinate" in e.get_class().get_name() for e in exprs):
        log("已存在 TextureCoordinate 节点，跳过（避免重复叠加）")
        return

    # 建 TextureCoordinate + Multiply（缩放）
    tc = MEL.create_material_expression(
        mat, unreal.MaterialExpressionTextureCoordinate, -1100, 0)
    mul = MEL.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, -950, 0)
    const = MEL.create_material_expression(
        mat, unreal.MaterialExpressionConstant2Vector, -1100, 160)
    const.set_editor_property("r", TILE)
    const.set_editor_property("g", TILE)

    MEL.connect_material_expressions(tc, "UVs", mul, "A")
    MEL.connect_material_expressions(const, "", mul, "B")

    # 把缩放后的 UV 接到每个 TextureSample 的 UVs 输入
    ok = 0
    for s in samples:
        try:
            MEL.connect_material_expressions(mul, "", s, "UVs")
            ok += 1
        except Exception as e:
            log("  连接失败 %s: %s" % (s.get_name(), str(e)[:50]))
    log("已给 %d/%d 个贴图采样接上 UV×%.1f" % (ok, len(samples), TILE))

    MEL.recompile_material(mat)
    EAL.save_asset(path, only_if_is_dirty=False)

    # 复核
    exprs2 = MEL.get_material_expressions(mat)
    has = any("TextureCoordinate" in e.get_class().get_name() for e in exprs2)
    log("复核：TextureCoordinate 存在 = %s，节点总数 %d" % (has, len(exprs2)))


main()
with open(REPORT, "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("FLOOR_UVFIX_DONE")
