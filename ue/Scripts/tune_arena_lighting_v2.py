# -*- coding: utf-8 -*-
"""布光 v2：提亮天空穹顶，降低局部灯，避免机体纯白。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
MAT_PATH = "/Game/RobotGame/Art/Materials/M_SkyDome"
log = lambda m: unreal.log("[布光v2] %s" % m)

def g(o, a, d=None):
    try:
        return o.get_editor_property(a)
    except Exception:
        return d

def setp(o, a, v, tag=""):
    try:
        o.set_editor_property(a, v)
        return True
    except Exception as e:
        log("  ❌ %s%s: %s" % (tag, a, str(e)[:90]))
        return False

def col(r, g, b, a=255):
    return unreal.Color(int(r), int(g), int(b), int(a))

mat = unreal.EditorAssetLibrary.load_asset(MAT_PATH)
mel = unreal.MaterialEditingLibrary
exprs = mel.get_material_expressions(mat)
remap = [
    ((0.120, 0.160, 0.280), (0.300, 0.420, 0.850)),
    ((0.450, 0.320, 0.220), (1.050, 0.750, 0.500)),
    ((0.060, 0.090, 0.200), (0.220, 0.320, 0.620)),
    ((0.550, 0.300, 0.140), (1.100, 0.600, 0.280)),
    ((2.000, 1.400, 0.800), (4.000, 2.800, 1.600)),
]
for e in exprs:
    if e.get_class().get_name() != "MaterialExpressionConstant3Vector":
        continue
    c = e.get_editor_property("constant")
    for old, new in remap:
        if abs(c.r-old[0]) < 0.02 and abs(c.g-old[1]) < 0.02 and abs(c.b-old[2]) < 0.02:
            e.set_editor_property("constant", unreal.LinearColor(*new, 1.0))
            log("天空常量 %s -> (%.3f,%.3f,%.3f)" % (e.get_name(), *new))
            break
setp(mat, "is_sky", True, "SkyMat.")
mel.recompile_material(mat)
unreal.EditorAssetLibrary.save_loaded_asset(mat)

unreal.EditorLevelLibrary.load_level(LEVEL)
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    cn = a.get_class().get_name()
    lbl = a.get_actor_label()
    if cn == "DirectionalLight":
        c = g(a, "directional_light_component") or g(a, "light_component")
        setp(c, "intensity", 4000.0, "Sun.")
        setp(c, "temperature", 7000.0, "Sun.")
        setp(c, "use_temperature", True, "Sun.")
        setp(c, "atmosphere_sun_light", False, "Sun.")
    elif cn == "SkyLight":
        c = g(a, "sky_light_component") or g(a, "light_component")
        setp(c, "intensity", 1.0, "Sky.")
        setp(c, "light_color", col(210, 225, 255), "Sky.")
        c.recapture_sky()
    elif cn == "SpotLight" and lbl.startswith("FloodLight"):
        c = g(a, "spot_light_component") or g(a, "light_component")
        setp(c, "intensity", 1200.0, "Flood.")
        setp(c, "temperature", 5500.0, "Flood.")
        setp(c, "use_temperature", True, "Flood.")
    elif cn == "PointLight" and lbl.startswith("FillLight"):
        c = g(a, "point_light_component") or g(a, "light_component")
        setp(c, "intensity", 600.0, "Fill.")
        setp(c, "temperature", 6500.0, "Fill.")
        setp(c, "use_temperature", True, "Fill.")
    elif cn == "PointLight" and lbl.startswith("AccentLight"):
        c = g(a, "point_light_component") or g(a, "light_component")
        setp(c, "intensity", 500.0, "Accent.")
        setp(c, "temperature", 6500.0, "Accent.")
        setp(c, "use_temperature", True, "Accent.")

unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_all_dirty_levels()
log("完成")