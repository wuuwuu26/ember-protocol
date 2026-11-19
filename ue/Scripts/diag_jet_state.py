# -*- coding: utf-8 -*-
"""诊断：水柱 actor 现在挂的材质 + 所有 jet/water 材质的 SM5 编译状态。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
MAT_DIR = "/Game/RobotGame/Art/Materials"
EAL = unreal.EditorAssetLibrary
ELL = unreal.EditorLevelLibrary
lines = []


def log(s):
    unreal.log("[JetDiag] %s" % s)
    lines.append(str(s))


ELL.load_level(LEVEL)

log("===== 水柱/供水 actor =====")
for a in ELL.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl.startswith(("Jet_", "Pipe_", "Inlet_", "Splash_", "Spray_")):
        loc = a.get_actor_location()
        sc = a.get_actor_scale3d()
        comp = a.get_component_by_class(unreal.StaticMeshComponent)
        mat = comp.get_material(0) if comp else None
        log("%-26s loc=(%.0f,%.0f,%.0f) sc=(%.2f,%.2f,%.2f) mat=%s"
            % (lbl, loc.x, loc.y, loc.z, sc.x, sc.y, sc.z,
               mat.get_name() if mat else "None"))

log("===== jet/water 相关材质资产 =====")
for name in ("M_WaterJet_Coolant", "M_WaterJet_Toxic",
             "M_Jet_Coolant_Stream", "M_GeoCache_Water",
             "M_Splash_Foam", "M_Splash_Spray", "M_SplashDroplet",
             "T_Toxic_Bub"):
    p = "%s/%s" % (MAT_DIR, name)
    if EAL.does_asset_exist(p):
        obj = EAL.load_asset(p)
        cls = obj.get_class().get_name() if obj else "?"
        extra = ""
        if obj and "Material" in cls:
            try:
                extra = " blend=%s" % str(obj.get_editor_property("blend_mode"))
                # 材质表达式数量
                exprs = unreal.MaterialEditingLibrary.get_num_material_expressions(obj) \
                    if hasattr(unreal.MaterialEditingLibrary, "get_num_material_expressions") else "?"
                extra += " exprs=%s" % exprs
            except Exception as e:
                extra = " err=%s" % str(e)[:40]
        elif obj and "Texture" in cls:
            try:
                extra = " %dx%d" % (obj.blueprint_get_size_x(),
                                    obj.blueprint_get_size_y())
            except Exception:
                pass
        log("  %-26s [%s]%s" % (name, cls, extra))
    else:
        log("  %-26s !! 不存在" % name)

with open(r"C:\Users\25227\Documents\robot_game\docs\jet_diag.txt", "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("JET_DIAG_DONE")
