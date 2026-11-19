# -*- coding: utf-8 -*-
"""dump M_Toxic_Fluid / M_Coolant_Fluid 的表达式与引用贴图，定位黄褐斑驳来源。"""
import unreal

MAT_DIR = "/Game/RobotGame/Art/Materials"
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
lines = []


def log(s):
    unreal.log("[FluidDump] %s" % s)
    lines.append(str(s))


for name in ("M_Toxic_Fluid", "M_Coolant_Fluid", "M_Toxic_Bed"):
    p = "%s/%s" % (MAT_DIR, name)
    m = EAL.load_asset(p)
    if not m:
        log("%s 缺失" % name)
        continue
    log("===== %s  blend=%s =====" % (
        name, str(m.get_editor_property("blend_mode"))))
    try:
        exprs = MEL.get_material_expressions(m)
    except Exception as e:
        log("  取表达式失败 %s" % str(e)[:60])
        continue
    for e in exprs:
        cls = e.get_class().get_name()
        extra = ""
        # 贴图节点 → 打印贴图名与 sampler type
        if "TextureSample" in cls:
            try:
                t = e.get_editor_property("texture")
                extra += " tex=%s" % (t.get_name() if t else "None")
            except Exception:
                pass
            try:
                extra += " sampler=%s" % str(e.get_editor_property("sampler_type"))
            except Exception:
                pass
            try:
                pn = e.get_editor_property("parameter_name")
                extra += " param=%s" % pn
            except Exception:
                pass
        # 参数节点 → 打印参数名
        for prop in ("parameter_name",):
            try:
                extra += " %s=%s" % (prop, e.get_editor_property(prop))
            except Exception:
                pass
        # 常量节点值
        try:
            extra += " r=%s" % e.get_editor_property("r")
        except Exception:
            pass
        try:
            c = e.get_editor_property("constant")
            extra += " c=(%.2f,%.2f,%.2f)" % (c.r, c.g, c.b)
        except Exception:
            pass
        log("  %-42s%s" % (cls, extra))

with open(r"C:\Users\25227\Documents\robot_game\docs\fluid_mat_dump.txt", "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("FLUID_DUMP_DONE")
