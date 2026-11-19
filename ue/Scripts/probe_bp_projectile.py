# -*- coding: utf-8 -*-
"""检查 BP_Projectile_C 的实际组件：是不是蓝本自己还有一层网格/材质/缩放。"""
import unreal

BP = "/Game/RobotGame/Blueprints/BP_Projectile"
bp = unreal.load_asset(BP)
if bp is None:
    # 找不到就全局搜一次
    for p in unreal.EditorAssetLibrary.list_assets("/Game/RobotGame", recursive=True):
        if p.split("/")[-1].startswith("BP_Projectile"):
            BP = p
            bp = unreal.load_asset(p)
            break

out = ["BP=%s class=%s" % (BP, bp.get_class().get_name() if bp else "None")]
try:
    gen = bp.generated_class() if hasattr(bp, "generated_class") else None
    cdo = unreal.get_default_object(gen) if gen else None
    out.append("CDO=%s" % (cdo.get_name() if cdo else "None"))
    if cdo:
        for c in cdo.get_components_by_class(unreal.ActorComponent):
            row = "  %s (%s)" % (c.get_name(), c.get_class().get_name())
            for prop in ("relative_scale3d", "static_mesh", "override_materials",
                         "relative_location"):
                try:
                    row += " %s=%s" % (prop, c.get_editor_property(prop))
                except Exception:
                    pass
            out.append(row)
except Exception as e:
    out.append("CDO 读取失败: %s" % str(e)[:200])

with open(r"C:\Users\25227\Documents\robot_game\docs\bp_proj.txt", "w") as f:
    f.write("\n".join(out))
    f.write("\nBPPROJ_DONE\n")
