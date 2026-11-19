# -*- coding: utf-8 -*-
"""恢复默认玩家机体网格为之前的 SK_Chassis_Light 与 SK_Chassis_Medium"""
import unreal

LIGHT_DATA = "/Game/RobotGame/Data/Chassis/DA_Chassis_Light"
MEDIUM_DATA = "/Game/RobotGame/Data/Chassis/DA_Chassis_Medium"

sk_light = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Characters/SK_Chassis_Light")
sk_medium = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Characters/SK_Chassis_Medium")

da_light = unreal.EditorAssetLibrary.load_asset(LIGHT_DATA)
da_medium = unreal.EditorAssetLibrary.load_asset(MEDIUM_DATA)

if da_light and sk_light:
    da_light.set_editor_property("chassis_mesh", sk_light)
    unreal.EditorAssetLibrary.save_loaded_asset(da_light)
    unreal.log(f"DA_Chassis_Light 成功恢复为 {sk_light.get_name()}")

if da_medium and sk_medium:
    da_medium.set_editor_property("chassis_mesh", sk_medium)
    unreal.EditorAssetLibrary.save_loaded_asset(da_medium)
    unreal.log(f"DA_Chassis_Medium 成功恢复为 {sk_medium.get_name()}")

with open(r"C:\Users\25227\Documents\robot_game\docs\chassis_restored.txt", "w", encoding="utf-8") as f:
    f.write("CHASSIS_RESTORED_DONE\n")
