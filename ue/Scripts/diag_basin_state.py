# -*- coding: utf-8 -*-
"""诊断圆形水池：池壁/池底/液面 actor 及其材质 + 编译错误细节。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
MAT_DIR = "/Game/RobotGame/Art/Materials"
EAL = unreal.EditorAssetLibrary
ELL = unreal.EditorLevelLibrary
lines = []


def log(s):
    unreal.log("[BasinDiag] %s" % s)
    lines.append(str(s))


ELL.load_level(LEVEL)

log("===== 圆形水池相关 actor（池心约 -200,350）=====")
for a in ELL.get_all_level_actors():
    lbl = a.get_actor_label()
    loc = a.get_actor_location()
    # 圆形池在 x -400..0, y 200..500 附近
    if -420 < loc.x < 20 and 180 < loc.y < 520:
        comp = a.get_component_by_class(unreal.StaticMeshComponent)
        mats = []
        if comp:
            for i in range(comp.get_num_materials()):
                mi = comp.get_material(i)
                mats.append(mi.get_name() if mi else "None")
        log("%-30s loc=(%.0f,%.0f,%.0f) sc=(%.2f,%.2f,%.2f) mats=%s"
            % (lbl, loc.x, loc.y, loc.z,
               a.get_actor_scale3d().x, a.get_actor_scale3d().y,
               a.get_actor_scale3d().z, mats))
        # 若是 CoolantField（液面），读参数
        if "Coolant" in a.get_class().get_name() or "Field" in a.get_class().get_name():
            for prop in ("pool_radius", "b_stagnant", "b_inflow"):
                try:
                    log("    %s = %s" % (prop, a.get_editor_property(prop)))
                except Exception:
                    pass

log("===== 液体/池材质清单 =====")
for name in ("M_Toxic_Bed", "M_Coolant_Fluid", "M_Basin_Concrete",
             "M_GeoCache_Water", "M_Sludge", "MI_Basin_Coolant"):
    p = "%s/%s" % (MAT_DIR, name)
    if EAL.does_asset_exist(p):
        obj = EAL.load_asset(p)
        cls = obj.get_class().get_name() if obj else "?"
        log("  %-22s [%s]" % (name, cls))
    else:
        log("  %-22s 不存在" % name)

with open(r"C:\Users\25227\Documents\robot_game\docs\basin_diag.txt", "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("BASIN_DIAG_DONE")
