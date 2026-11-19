# -*- coding: utf-8 -*-
"""诊断 glTF 导入结果：
1) cs1-pipe 网格尺寸为何只有 13.9cm（源 glTF 是米，应是 139cm）
2) 材质/贴图是否接上
3) 查 Interchange glTF 导入器有没有单位缩放设置
"""
import unreal

DEST = "/Game/RobotGame/Art/Props/Cosmos/cs1-pipe"
EAL = unreal.EditorAssetLibrary
out = []

sm = EAL.load_asset(DEST + "/SM_cs1-pipe")
if sm:
    bb = sm.get_bounding_box()
    out.append("SM bbox = (%.2f, %.2f, %.2f) cm   min=(%.2f,%.2f,%.2f) max=(%.2f,%.2f,%.2f)"
               % (bb.max.x-bb.min.x, bb.max.y-bb.min.y, bb.max.z-bb.min.z,
                  bb.min.x, bb.min.y, bb.min.z, bb.max.x, bb.max.y, bb.max.z))
    for i, s in enumerate(sm.get_editor_property("static_materials")):
        mi = s.get_editor_property("material_interface")
        out.append("  slot%d -> %s" % (i, mi.get_path_name() if mi else "None"))

# 列目录资产
out.append("")
out.append("目录资产：")
for p in sorted(EAL.list_assets(DEST, recursive=True)):
    a = EAL.load_asset(p)
    out.append("  %-50s %s" % (p.split("/")[-1], a.get_class().get_name() if a else "?"))

# 材质细节
mat = EAL.load_asset(DEST + "/MI_CS1_Pipe_01a_4096")
if mat:
    out.append("")
    out.append("材质 %s (%s)" % (mat.get_name(), mat.get_class().get_name()))
    if mat.get_class().get_name() == "Material":
        try:
            exprs = unreal.MaterialEditingLibrary.get_material_expressions(mat)
            out.append("  表达式 %d 个：" % len(exprs))
            for e in exprs:
                out.append("    %s" % e.get_class().get_name())
        except Exception as e:
            out.append("  表达式失败 %s" % e)

# 查 glTF 导入相关的 Interchange 设置类
out.append("")
out.append("== 可用 Interchange 导入设置类 ==")
for n in dir(unreal):
    if "Interchange" in n and ("gltf" in n.lower() or "Generic" in n or "Pipeline" in n or "Translator" in n):
        out.append("  %s" % n)

with open(r"C:\Users\25227\Documents\robot_game\docs\cosmos_diag.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("COSMOS_DIAG_DONE")
