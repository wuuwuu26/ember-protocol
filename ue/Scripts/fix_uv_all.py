# -*- coding: utf-8 -*-
"""批量修复所有 Poly Haven 材质的 UV 拉伸（第一百一十一轮）。

同一问题的普适修法：Poly Haven 贴图是真实尺度扫描（约 2m 一张），
而场景构件是 400cm 级（地面块/墙段），默认 UV(0-1) 直接铺满
→ 纹理被放大 2 倍，细节糊成一片。

给每个 TextureSample 接 TextureCoordinate × N：
  - 地面：N=2（400cm / 2 = 200cm 一张）
  - 墙面：N=2.5（412cm / 2.5 ≈ 165cm，墙面细节要更密）
  - 金属/格栅：N=3（小物件，纹理更细）

⚠️ 幂等：已有 TextureCoordinate 的跳过。
"""
import unreal

PH = "/Game/RobotGame/Art/Materials/PolyHaven"
REPORT = r"C:\Users\25227\Documents\robot_game\docs\uvfix_all.txt"

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
lines = []


def log(s):
    unreal.log("[UVFixAll] %s" % s)
    lines.append(str(s))


TILE = {
    "M_concrete_floor_02": 2.0,
    "M_concrete_wall_001": 2.5,
    "M_factory_wall": 2.5,
    "M_corrugated_iron": 3.0,
    "M_rusty_metal": 3.0,
    "M_metal_grate_rusty": 3.0,
}


def fix(path, tile):
    mat = EAL.load_asset(path)
    if not mat:
        log("!! 加载失败 %s" % path)
        return
    name = mat.get_name()
    exprs = MEL.get_material_expressions(mat)
    if any("TextureCoordinate" in e.get_class().get_name() for e in exprs):
        log("%-26s 已有 TC，跳过" % name)
        return

    samples = [e for e in exprs if "TextureSample" in e.get_class().get_name()]
    tc = MEL.create_material_expression(
        mat, unreal.MaterialExpressionTextureCoordinate, -1100, 0)
    mul = MEL.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, -950, 0)
    const = MEL.create_material_expression(
        mat, unreal.MaterialExpressionConstant2Vector, -1100, 160)
    const.set_editor_property("r", tile)
    const.set_editor_property("g", tile)
    MEL.connect_material_expressions(tc, "UVs", mul, "A")
    MEL.connect_material_expressions(const, "", mul, "B")

    ok = 0
    for s in samples:
        try:
            MEL.connect_material_expressions(mul, "", s, "UVs")
            ok += 1
        except Exception as e:
            log("  %s 连接失败: %s" % (name, str(e)[:50]))
    MEL.recompile_material(mat)
    EAL.save_asset(path, only_if_is_dirty=False)
    log("%-26s UV×%.1f  接入 %d/%d 个贴图" % (name, tile, ok, len(samples)))


for mat_name, tile in TILE.items():
    fix("%s/%s" % (PH, mat_name), tile)

with open(REPORT, "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("UVFIX_ALL_DONE")
