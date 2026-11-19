# -*- coding: utf-8 -*-
"""把落水点圆盘改成水面材质，融入水面（第一百一十二轮最终修复）。

判定结论：浅色半圆 = Splash_FoamRing / Splash_FoamDisc（换 M_Copper 后
立刻变成有纹理的铜片，证明几何与 UV 都正常）。之前纯白是
M_Splash_Foam / V2 材质在场景高曝光下被 Emissive 拉爆所致。

修法：不再用自制泡沫材质，直接让圆盘复用**水面材质**
M_GeoCache_Water（带波纹法线/反光），落水点与周围水面浑然一体，
"没有纹理"的问题彻底消失。

⚠️ 用 override_materials，不动资产；保存关卡。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
MAT = "/Game/RobotGame/Art/Materials/M_GeoCache_Water"
REPORT = r"C:\Users\25227\Documents\robot_game\docs\splash_final.txt"

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EAL = unreal.EditorAssetLibrary
lines = []


def log(s):
    unreal.log("[SplashFinal] %s" % s)
    lines.append(str(s))


water = EAL.load_asset(MAT)
if not water:
    log("!! 水面材质缺失 %s" % MAT)
else:
    log("水面材质 = %s (%s)" % (water.get_name(), water.get_class().get_name()))
    n = 0
    for a in sub.get_all_level_actors():
        if a.get_actor_label() not in ("Splash_FoamRing", "Splash_FoamDisc",
                                       "Splash_SprayCone"):
            continue
        if a.get_class().get_name() != "StaticMeshActor":
            continue
        c = a.static_mesh_component
        c.set_editor_property("override_materials", [water])
        c.set_visibility(True)
        n += 1
        log("  %s -> 水面材质" % a.get_actor_label())
    log("应用 %d 个落水点装饰" % n)
    les.save_current_level()
    log("已保存关卡")

with open(REPORT, "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("SPLASH_FINAL_DONE")
