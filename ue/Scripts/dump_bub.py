# -*- coding: utf-8 -*-
"""把 UE 的 T_Toxic_Bub 贴图导出，检查 R 通道对比度（水柱条纹来源）。"""
import unreal
import os

EAL = unreal.EditorAssetLibrary
obj = EAL.load_asset("/Game/RobotGame/Art/Materials/T_Toxic_Bub")
out = r"C:\Users\25227\Documents\robot_game\docs\ue_tex_dump"
os.makedirs(out, exist_ok=True)
dst = os.path.join(out, "T_Toxic_Bub.png")
t = unreal.AssetExportTask()
t.object = obj
t.filename = dst
t.automated = True
t.exporter = unreal.TextureExporterPNG()
ok = unreal.Exporter.run_asset_export_task(t)
unreal.log("[BubDump] export ok=%s" % ok)
unreal.log("BUB_DUMP_DONE")
