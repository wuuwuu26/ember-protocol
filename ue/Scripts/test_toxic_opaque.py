# -*- coding: utf-8 -*-
"""隔离实验 2：把 M_Toxic_Fluid 临时改成不透明，判断斜纹来自透射背景还是表面着色。"""
import unreal

EAL = unreal.EditorAssetLibrary
mat = EAL.load_asset("/Game/RobotGame/Art/Materials/M_Toxic_Fluid")
mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
unreal.MaterialEditingLibrary.recompile_material(mat)
EAL.save_loaded_asset(mat)
unreal.log("TOXIC_OPAQUE_TEST_OK")
