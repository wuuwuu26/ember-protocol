# -*- coding: utf-8 -*-
"""检查其它 Poly Haven 材质（墙/金属）是否也需要 UV 平铺修复。"""
import unreal

PH = "/Game/RobotGame/Art/Materials/PolyHaven"
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
out = []

for p in sorted(EAL.list_assets(PH, recursive=True)):
    a = EAL.load_asset(p)
    if not a or a.get_class().get_name() != "Material":
        continue
    exprs = MEL.get_material_expressions(a)
    has_tc = any("TextureCoordinate" in e.get_class().get_name() for e in exprs)
    n_tex = sum(1 for e in exprs if "TextureSample" in e.get_class().get_name())
    out.append("%-30s 贴图%d  TC节点=%s  总节点=%d" %
               (a.get_name(), n_tex, has_tc, len(exprs)))

with open(r"C:\Users\25227\Documents\robot_game\docs\mat_uv_audit.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("MAT_UV_AUDIT_DONE")
