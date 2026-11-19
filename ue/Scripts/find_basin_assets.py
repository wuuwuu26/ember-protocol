# -*- coding: utf-8 -*-
"""查找水渠相关材质的真实资产路径。"""
import unreal

EAL = unreal.EditorAssetLibrary
out = []

WANT = ("M_Basin_Concrete", "MI_Basin_Coolant", "M_GeoCache_Water",
        "T_ConcreteDetail", "T_ConcreteDetail_N")

for p in EAL.list_assets("/Game/RobotGame", recursive=True):
    n = p.split("/")[-1].split(".")[0]
    if n in WANT:
        out.append("%-24s -> %s" % (n, p))

out.insert(0, "找到 %d 个" % (len(out)))
with open(r"C:\Users\25227\Documents\robot_game\docs\basin_paths.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("BASIN_PATHS_DONE")
