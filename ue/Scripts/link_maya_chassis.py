# -*- coding: utf-8 -*-
"""将玩家默认中型机体资产 DA_Chassis_Medium 的网格替换为 Maya 2027 雕刻的 SK_Pilot_Maya。"""
import unreal

DATA_PATH = "/Game/RobotGame/Data/Chassis/DA_Chassis_Medium"
NEW_MESH = "/Game/RobotGame/Art/Characters/SK_Pilot_Maya"

da = unreal.EditorAssetLibrary.load_asset(DATA_PATH)
new_sk = unreal.EditorAssetLibrary.load_asset(NEW_MESH)

if da and new_sk:
    da.set_editor_property("chassis_mesh", new_sk)
    unreal.EditorAssetLibrary.save_loaded_asset(da)
    unreal.log("DA_Chassis_Medium 成功切换为 SK_Pilot_Maya！")

with open(r"C:\Users\25227\Documents\robot_game\docs\chassis_maya_linked.txt", "w", encoding="utf-8") as f:
    f.write("CHASSIS_MAYA_LINKED_DONE\n")
