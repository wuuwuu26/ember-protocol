# -*- coding: utf-8 -*-
"""查圆形水池 CoolantField 的 SurfaceMaterial 指向 + 液面材质编译状态。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
MAT_DIR = "/Game/RobotGame/Art/Materials"
EAL = unreal.EditorAssetLibrary
ELL = unreal.EditorLevelLibrary
lines = []


def log(s):
    unreal.log("[FluidMatDiag] %s" % s)
    lines.append(str(s))


ELL.load_level(LEVEL)
for a in ELL.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl in ("ToxicFluid_0", "CoolantSpill_0", "HazardSludge_0"):
        log("=== %s  class=%s ===" % (lbl, a.get_class().get_name()))
        for prop in ("surface_material", "SurfaceMaterial",
                     "glow_color", "GlowColor", "pool_radius", "b_stagnant"):
            try:
                v = a.get_editor_property(prop)
                log("  %s = %s" % (prop, v.get_name() if hasattr(v, "get_name") else v))
            except Exception as e:
                pass
        # 列出所有 UObject 类型的材质属性
        try:
            for p in ("surface", "Surface"):
                comp = a.get_editor_property(p)
                if comp:
                    log("  %s mat = %s" % (p,
                        comp.get_material(0).get_name()
                        if comp.get_material(0) else "None"))
        except Exception:
            pass

log("=== 液面材质资产 ===")
for name in ("M_Coolant_Fluid", "M_Toxic_Fluid", "M_Toxic_Bed",
             "MI_Basin_Coolant", "M_GeoCache_Water"):
    p = "%s/%s" % (MAT_DIR, name)
    log("  %-20s exists=%s" % (name, EAL.does_asset_exist(p)))
    if EAL.does_asset_exist(p):
        o = EAL.load_asset(p)
        log("      class=%s" % o.get_class().get_name())

with open(r"C:\Users\25227\Documents\robot_game\docs\fluid_mat_diag.txt", "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("FLUID_MAT_DIAG_DONE")
