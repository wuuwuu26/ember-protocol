# -*- coding: utf-8 -*-
"""水珠最终放大 + 提高自发光（让飞沫明确可见）。"""
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
# 1. 材质自发光调亮
m = EAL.load_asset("/Game/RobotGame/Art/Materials/M_SplashDroplet")
out = []
if m:
    for e in MEL.get_material_expressions(m):
        if e.get_class().get_name() == "MaterialExpressionConstant3Vector":
            c = e.get_editor_property("constant")
            # Emissive 那个是 (0.15,0.55,0.75)
            if abs(c.r - 0.15) < 0.02 and abs(c.g - 0.55) < 0.02:
                e.set_editor_property("constant",
                    unreal.LinearColor(0.35, 0.95, 1.30, 1.0))
                out.append("自发光 (0.15,0.55,0.75) -> (0.35,0.95,1.30)")
    MEL.recompile_material(m)
    EAL.save_asset("/Game/RobotGame/Art/Materials/M_SplashDroplet",
                   only_if_is_dirty=False)

# 2. 关卡参数
LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in sub.get_all_level_actors():
    if a.get_class().get_name() == "RobotCoolantField" and a.get_actor_label() == "CoolantSpill_0":
        a.set_editor_property("bSplashDroplets", True)
        a.set_editor_property("DropletsPerPulse", 3)
        a.set_editor_property("DropletLaunchSpeed", 300.0)
        a.set_editor_property("DropletSpread", 85.0)
        a.set_editor_property("DropletGravity", 980.0)
        a.set_editor_property("DropletRadius", 9.0)
        a.set_editor_property("MaxDroplets", 54)
        out.append("水珠：每脉冲3、上抛300、散开85、重力980、半径9、上限54")
        break
les.save_current_level()
out.append("已保存")
with open(r"C:\Users\25227\Documents\robot_game\docs\droplet_big2.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("DROPLET_BIG2_DONE")
