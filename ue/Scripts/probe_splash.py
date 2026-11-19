# -*- coding: utf-8 -*-
"""定位注水落点处的"圆盘"几何及其材质（第一百一十二轮）。

从截图看，(450,300) 水渠左上注水口有两个交叠的浅色扇形/圆盘，
纯色无纹理，与水面脱离。查它们是什么 actor、什么材质。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

out = []
# 注水口在 (120,300) 附近（Pipe_Spout_CoolantSpill_0 / Jet_CoolantSpill_0）
# 但落点圆盘可能在水面 (450,300) 附近，或由 RobotCoolantField / GeoCache 生成
KW = ("splash", "ripple", "disc", "disk", "foam", "jet", "impact", "ring",
      "spout", "coolant", "water", "puddle", "wet", "spill")

for a in sub.get_all_level_actors():
    cls = a.get_class().get_name()
    label = a.get_actor_label()
    loc = a.get_actor_location()
    blob = (label + " " + cls).lower()

    # 收集所有在注水口附近的 actor
    near = (abs(loc.x - 250) < 400 and abs(loc.y - 300) < 400)
    if not near:
        continue

    out.append("=== %s  %s  (%.0f,%.0f,%.1f) ===" % (
        cls, label, loc.x, loc.y, loc.z))

    # 组件 + 材质
    try:
        comps = a.get_components_by_class(unreal.PrimitiveComponent)
        for c in comps:
            n = c.get_num_materials()
            out.append("  组件 %s (%s) 材质%d" % (c.get_name(), c.get_class().get_name(), n))
            for i in range(n):
                mat = c.get_material(i)
                if mat:
                    mcls = mat.get_class().get_name()
                    extra = ""
                    if mcls == "Material":
                        MEL = unreal.MaterialEditingLibrary
                        exprs = MEL.get_material_expressions(mat)
                        has_tex = any("TextureSample" in e.get_class().get_name()
                                      for e in exprs)
                        extra = " 贴图节点=%s 总节点=%d" % (has_tex, len(exprs))
                    out.append("    slot%d=%s (%s)%s" % (
                        i, mat.get_name(), mcls, extra))
                else:
                    out.append("    slot%d=None" % i)
    except Exception as e:
        out.append("  组件读取失败 %s" % str(e)[:50])
    out.append("")

with open(r"C:\Users\25227\Documents\robot_game\docs\splash_diag.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("SPLASH_DIAG_DONE")
