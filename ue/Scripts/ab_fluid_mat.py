# -*- coding: utf-8 -*-
"""A/B：临时把 ToxicFluid_0 的 SurfaceMaterial 换成 M_Coolant_Fluid，
拍一张看金色是否变化（判断金色来自哪个材质）。可回滚。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
EAL = unreal.EditorAssetLibrary
ELL = unreal.EditorLevelLibrary
ELL.load_level(LEVEL)
alt = EAL.load_asset("/Game/RobotGame/Art/Materials/M_Coolant_Fluid")
for a in ELL.get_all_level_actors():
    if a.get_actor_label() == "ToxicFluid_0":
        a.set_editor_property("surface_material", alt)
        unreal.log("[AB] ToxicFluid_0 SurfaceMaterial -> M_Coolant_Fluid")
ELL.save_current_level()
unreal.log("FLUID_AB_DONE")
