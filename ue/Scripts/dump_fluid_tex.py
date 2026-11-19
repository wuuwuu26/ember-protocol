# -*- coding: utf-8 -*-
"""导出液体相关贴图，检查内容（找黄褐色来源）。"""
import unreal
import os

EAL = unreal.EditorAssetLibrary
out = r"C:\Users\25227\Documents\robot_game\docs\ue_tex_dump"
os.makedirs(out, exist_ok=True)
for name in ("T_Coolant_F", "T_Toxic_Bub", "T_WaterRipple_N"):
    obj = EAL.load_asset("/Game/RobotGame/Art/Materials/" + name)
    if not obj:
        unreal.log("[FluidTexDump] %s 缺失" % name)
        continue
    dst = os.path.join(out, name + ".png")
    t = unreal.AssetExportTask()
    t.object = obj
    t.filename = dst
    t.automated = True
    t.exporter = unreal.TextureExporterPNG()
    ok = unreal.Exporter.run_asset_export_task(t)
    unreal.log("[FluidTexDump] %s -> %s ok=%s" % (name, dst, ok))
unreal.log("FLUID_TEX_DUMP_DONE")
