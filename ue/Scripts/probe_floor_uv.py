# -*- coding: utf-8 -*-
"""专门拍地面特写，诊断纹理问题（第一百一十一轮）。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)

out = []

# 1. 检查 UV 缩放：地面块 400x400，材质 UV 默认 0-1 拉伸到整块
#    如果贴图是 2m 的扫描件，400cm 块上 0-1 会拉伸 2 倍 —— 纹理"糊"
#    正确做法：材质里给 TexCoord 一个乘数，让纹理平铺
mat = unreal.EditorAssetLibrary.load_asset(
    "/Game/RobotGame/Art/Materials/PolyHaven/M_concrete_floor_02")
if mat:
    MEL = unreal.MaterialEditingLibrary
    exprs = MEL.get_material_expressions(mat)
    has_texcoord = any("TextureCoordinate" in e.get_class().get_name() for e in exprs)
    out.append("材质里有 TextureCoordinate 节点: %s" % has_texcoord)
    out.append("节点数: %d" % len(exprs))
    # 列出贴图采样节点的 UV 输入是否连了东西
    for e in exprs:
        if "TextureSample" in e.get_class().get_name():
            t = e.get_editor_property("texture")
            out.append("  贴图 %s" % (t.get_name() if t else "None"))

# 2. 地面网格的 UV 情况（SM_Env_Floor 是 400x400 块）
mesh = unreal.EditorAssetLibrary.load_asset(
    "/Game/RobotGame/Art/Environment/SM_Env_Floor")
if mesh:
    out.append("")
    out.append("SM_Env_Floor:")
    try:
        bb = mesh.get_bounding_box()
        out.append("  bbox = %.0f x %.0f x %.0f cm" % (
            bb.max.x - bb.min.x, bb.max.y - bb.min.y, bb.max.z - bb.min.z))
    except Exception:
        pass

with open(r"C:\Users\25227\Documents\robot_game\docs\floor_uv.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("FLOOR_UV_DONE")
