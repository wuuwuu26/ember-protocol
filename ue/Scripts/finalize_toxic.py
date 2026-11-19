# -*- coding: utf-8 -*-
"""最终方案：圆形毒液池液面用已验证干净的 M_Coolant_Fluid，
删除试验性的 M_Toxic_Fluid_Fixed（SM5 编译失败的坏资产）。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
MAT_DIR = "/Game/RobotGame/Art/Materials"
EAL = unreal.EditorAssetLibrary
ELL = unreal.EditorLevelLibrary
lines = []
def log(s):
    unreal.log("[ToxicFinal] %s" % s); lines.append(str(s))

cool = EAL.load_asset("%s/M_Coolant_Fluid" % MAT_DIR)
ELL.load_level(LEVEL)
for a in ELL.get_all_level_actors():
    if a.get_actor_label() == "ToxicFluid_0":
        a.set_editor_property("surface_material", cool)
        log("ToxicFluid_0.SurfaceMaterial -> M_Coolant_Fluid（已验证无金色斑驳）")
ELL.save_current_level()
log("关卡已保存")

# 删掉编译失败的试验材质
bad = "%s/M_Toxic_Fluid_Fixed" % MAT_DIR
if EAL.does_asset_exist(bad):
    EAL.delete_asset(bad)
    log("删除试验材质 M_Toxic_Fluid_Fixed")
with open(r"C:\Users\25227\Documents\robot_game\docs\toxic_final.txt", "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("TOXIC_FINAL_DONE")
