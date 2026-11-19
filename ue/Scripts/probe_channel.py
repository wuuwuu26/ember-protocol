# -*- coding: utf-8 -*-
"""定位长方形水渠（RobotBasin 里 BuildChannel 生成的方渠）的位置与尺寸。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

out = []
for a in sub.get_all_level_actors():
    if a.get_class().get_name() != "RobotBasin":
        continue
    loc = a.get_actor_location()
    out.append("=== %s  (%.0f,%.0f,%.0f) ===" % (
        a.get_actor_label(), loc.x, loc.y, loc.z))

    # 读 Basin 的关键属性判断是方渠还是圆环
    for p in ("channel_mode", "bChannel", "half_length", "half_width",
              "wall_thickness", "inner_radius", "outer_radius",
              "segments", "top_z", "bottom_z", "rim_material", "fluid_material"):
        try:
            v = a.get_editor_property(p)
            out.append("  %-18s = %s" % (p, v))
        except Exception:
            pass

    # 包围盒（推断形状）
    try:
        org, ext = a.get_actor_bounds(False)
        out.append("  包围盒 extent=(%.0f, %.0f, %.0f)  -> 尺寸 %.0f x %.0f x %.0f cm" % (
            ext.x, ext.y, ext.z, ext.x * 2, ext.y * 2, ext.z * 2))
        # 方渠特征：长宽比明显不等；圆环：XY 接近相等
        ratio = max(ext.x, ext.y) / max(min(ext.x, ext.y), 1.0)
        out.append("  长宽比 = %.2f  -> %s" % (
            ratio, "方渠" if ratio > 1.4 else "圆环/方形池"))
    except Exception as e:
        out.append("  包围盒失败 %s" % str(e)[:50])
    out.append("")

with open(r"C:\Users\25227\Documents\robot_game\docs\channel_locate.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("CHANNEL_LOCATE_DONE")
