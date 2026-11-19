# -*- coding: utf-8 -*-
"""诊断：UE 里 SM_mech_torso_wreck 的材质到底引用了哪张贴图、贴图是否含黑区。"""
import unreal

EAL = unreal.EditorAssetLibrary
lines = []
def log(s):
    unreal.log("[WreckDiag] %s" % s)
    lines.append(str(s))

TARGET = "/Game/RobotGame/Art/Props/Gen3D/mech_torso_wreck/SM_mech_torso_wreck"
m = EAL.load_asset(TARGET)
log("mesh=%s" % (m.get_name() if m else "None"))
if m:
    slots = m.get_editor_property("static_materials")
    for i, s in enumerate(slots):
        mi = s.get_editor_property("material_interface")
        log("slot%d mat=%s" % (i, mi.get_name() if mi else "None"))
        if mi:
            # 列出材质里所有 texture 参数/引用
            try:
                tex_exprs = unreal.MaterialEditingLibrary.get_material_property_input_node(mi, unreal.MaterialProperty.MP_BASE_COLOR)
            except Exception:
                pass
# 列出子目录里的所有 Texture2D 资产
d = "/Game/RobotGame/Art/Props/Gen3D/mech_torso_wreck"
for a in EAL.list_assets(d, recursive=True):
    obj = EAL.load_asset(a)
    cls = obj.get_class().get_name() if obj else "?"
    extra = ""
    if obj and "Texture2D" in cls:
        try:
            extra = " %dx%d" % (obj.blueprint_get_size_x(), obj.blueprint_get_size_y())
        except Exception:
            pass
    log("  %s  [%s]%s" % (a.rsplit('/',1)[-1], cls, extra))

with open(r"C:\Users\25227\Documents\robot_game\docs\wreck_diag.txt", "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("WRECK_DIAG_DONE")
