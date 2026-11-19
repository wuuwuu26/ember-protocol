# -*- coding: utf-8 -*-
"""检查 IdolMechMat 的贴图连接情况：
GLB 转 FBX 时贴图是"嵌入"的，UE 会把它导出成 Texture2D 资产。
若材质里没连上贴图，表面就会是纯色（这里看到的是发白）。"""
import unreal

DEST = "/Game/RobotGame/Art/Props/IdolMech"
out = []

# 目录里有什么
assets = unreal.EditorAssetLibrary.list_assets(DEST, recursive=True)
out.append("目录资产 %d 个：" % len(assets))
for p in sorted(assets):
    a = unreal.EditorAssetLibrary.load_asset(p)
    cls = a.get_class().get_name() if a else "?"
    out.append("  %-40s %s" % (p.split("/")[-1], cls))

# 材质细节
mat = unreal.EditorAssetLibrary.load_asset(DEST + "/IdolMechMat")
if mat:
    out.append("")
    out.append("== IdolMechMat ==")
    out.append("class=%s" % mat.get_class().get_name())
    try:
        out.append("blend_mode=%s" % mat.get_editor_property("blend_mode"))
        out.append("shading_model=%s" % mat.get_editor_property("shading_model"))
    except Exception as e:
        out.append("props err %s" % e)
    # 尝试列出表达式（材质图节点）
    try:
        lib = unreal.MaterialEditingLibrary
        exprs = lib.get_material_expressions(mat)
        out.append("表达式节点 %d 个：" % len(exprs))
        for e in exprs:
            out.append("  %s" % e.get_class().get_name())
    except Exception as e:
        out.append("读取表达式失败: %s" % e)
    # 试参数
    try:
        names = [n for n in dir(mat) if "param" in n.lower()]
        out.append("参数相关属性: %s" % names[:10])
    except Exception:
        pass
else:
    out.append("!! 材质加载失败")

with open(r"C:\Users\25227\Documents\robot_game\docs\idol_mat.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("IDOL_MAT_DONE")
