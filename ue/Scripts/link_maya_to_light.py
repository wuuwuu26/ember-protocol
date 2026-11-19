# -*- coding: utf-8 -*-
"""检查并修正 DA_Chassis_Light 的网格指向"""
import unreal

for name in ("DA_Chassis_Light", "DA_Chassis_Medium", "DA_Chassis_Heavy"):
    da = unreal.EditorAssetLibrary.load_asset(f"/Game/RobotGame/Data/Chassis/{name}")
    if da:
        mesh = da.get_editor_property("chassis_mesh")
        mesh_name = mesh.get_name() if mesh else "None"
        unreal.log(f"{name} -> {mesh_name}")

# 把默认 DA_Chassis_Light 也换上 SK_Pilot_Maya，让开局立刻呈现 Maya 2027 精雕人物！
da_light = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Data/Chassis/DA_Chassis_Light")
sk_maya = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Characters/SK_Pilot_Maya")

if da_light and sk_maya:
    da_light.set_editor_property("chassis_mesh", sk_maya)
    unreal.EditorAssetLibrary.save_loaded_asset(da_light)
    unreal.log("DA_Chassis_Light 成功换装为 SK_Pilot_Maya！")

with open(r"C:\Users\25227\Documents\robot_game\docs\chassis_light_linked.txt", "w", encoding="utf-8") as f:
    f.write("CHASSIS_LIGHT_LINKED_DONE\n")
