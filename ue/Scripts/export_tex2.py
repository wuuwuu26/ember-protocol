# -*- coding: utf-8 -*-
"""用 AssetTools.export_assets 导出关键贴图。"""
import unreal

L = "[导出贴图2]"
OUT = r"C:\Users\25227\Documents\robot_game\docs\tmp"
AT = unreal.AssetToolsHelpers.get_asset_tools()

items = [
    "/Game/RobotGame/Art/Materials/T_MechDetail",
    "/Game/RobotGame/Art/Materials/T_MechDetail_N",
    "/Game/RobotGame/Art/Materials/T_EnvDetail",
    "/Game/RobotGame/Art/Materials/T_BoltMetal",
]
for p in items:
    try:
        ok = AT.export_assets([p], OUT)
        unreal.log("%s %s ok=%s" % (L, p, ok))
    except Exception as e:
        unreal.log("%s %s fail %s" % (L, p, str(e)[:120]))
unreal.log("EXPORTTEX2_OK")
