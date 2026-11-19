# -*- coding: utf-8 -*-
"""删掉旧的水波法线贴图资产，让 build_water_materials_v3.py 重新导入新的 PNG。"""
import unreal

P = "/Game/RobotGame/Art/Materials/T_WaterRipple_N"
EAL = unreal.EditorAssetLibrary
if EAL.does_asset_exist(P):
    EAL.delete_asset(P)
    unreal.log("RIPPLE_TEX_DELETED")
else:
    unreal.log("RIPPLE_TEX_ABSENT")
unreal.log("RIPPLE_RESET_OK")
