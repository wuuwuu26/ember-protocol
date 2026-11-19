# -*- coding: utf-8 -*-
"""地面材质"湿感/反射"增强（第一百一十轮）。

思路：Poly Haven 地面材质的 Roughness 直接来自 ARM 贴图 G 通道，
值偏高（干混凝土 0.7~0.9），Lumen 反射几乎看不清。
在 G 通道与 Roughness 之间插入 Multiply 系数 0.55，
拉低整体粗糙度 → 反射变清晰 → 出"湿润工业地面"的观感。

⚠️ 只改 M_concrete_floor_02（地面专用），不动墙面材质。
⚠️ 幂等：已存在同位置 Multiply 节点则复用，不重复生成。
"""
import unreal

PH = "/Game/RobotGame/Art/Materials/PolyHaven"
REPORT = r"C:\Users\25227\Documents\robot_game\docs\floor_wet.txt"
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
lines = []


def log(s):
    unreal.log("[FloorWet] %s" % s)
    lines.append(str(s))


ROUGH_SCALE = 0.55   # 越小越"湿"、反射越清晰


def main():
    path = PH + "/M_concrete_floor_02"
    mat = EAL.load_asset(path)
    if not mat:
        log("!! 材质加载失败")
        return

    # 找到 Roughness 当前的输入节点（应该是 G 通道 mask）
    src = MEL.get_material_property_input_node(
        mat, unreal.MaterialProperty.MP_ROUGHNESS)
    if not src:
        log("!! Roughness 未连接，跳过")
        return
    log("Roughness 当前输入：%s" % src.get_class().get_name())

    # 幂等：如果输入已经是 Multiply，说明改过了，直接更新系数
    mul = None
    if src.get_class().get_name() == "MaterialExpressionMultiply":
        mul = src
        log("已存在 Multiply 节点，复用")
    else:
        mul = MEL.create_material_expression(
            mat, unreal.MaterialExpressionMultiply, -200, 480)
        # A = 原 Roughness 来源 ，B = 系数
        MEL.connect_material_expressions(src, "", mul, "A")
        const = MEL.create_material_expression(
            mat, unreal.MaterialExpressionConstant, -400, 560)
        const.set_editor_property("r", ROUGH_SCALE)
        MEL.connect_material_expressions(const, "", mul, "B")
        # 断开原连接，改为乘完再进 Roughness
        MEL.disconnect_material_property(
            mat, unreal.MaterialProperty.MP_ROUGHNESS)
        MEL.connect_material_property(
            mul, "", unreal.MaterialProperty.MP_ROUGHNESS)
        log("已插入 Multiply（粗糙度 x%.2f）" % ROUGH_SCALE)

    MEL.recompile_material(mat)
    EAL.save_asset(path, only_if_is_dirty=False)

    # 复核
    chk = MEL.get_material_property_input_node(
        mat, unreal.MaterialProperty.MP_ROUGHNESS)
    log("复核 Roughness 输入 = %s" % (chk.get_class().get_name() if chk else "未连接"))


main()
with open(REPORT, "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("FLOOR_WET_DONE")
