# -*- coding: utf-8 -*-
"""查液体相关贴图的 sRGB / compression，决定 sampler 应改成什么。"""
import unreal
EAL = unreal.EditorAssetLibrary
lines = []
def log(s):
    unreal.log("[TexCfg] %s" % s); lines.append(str(s))
for n in ("T_Toxic_Bub", "T_Coolant_F", "T_WaterRipple_N", "T_ConcreteDetail"):
    p = "/Game/RobotGame/Art/Materials/" + n
    if not EAL.does_asset_exist(p):
        log("%s 缺失" % n); continue
    t = EAL.load_asset(p)
    log("%-18s srgb=%s compression=%s" % (
        n, t.get_editor_property("srgb"),
        str(t.get_editor_property("compression_settings"))))
with open(r"C:\Users\25227\Documents\robot_game\docs\tex_cfg.txt","wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("TEX_CFG_DONE")
