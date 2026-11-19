# -*- coding: utf-8 -*-
"""打印关键静态网格的包围盒与 pivot 偏移，供布景精确摆放。"""
import unreal

paths = [
    "/Game/RobotGame/Art/Environment/SM_Env_Piperun",
    "/Game/RobotGame/Art/Environment/SM_Env_SludgePool",
    "/Game/RobotGame/Art/Props/SM_Prop_PipeSegment",
    "/Game/RobotGame/Art/Props/SM_Prop_FuelBarrel",
    "/Game/RobotGame/Art/Props/SM_Prop_Container",
    "/Game/RobotGame/Art/Props/SM_Prop_ScrapCrate",
]
lines = []
for p in paths:
    m = unreal.EditorAssetLibrary.load_asset(p)
    if not m:
        lines.append(f"{p}: missing")
        continue
    b = m.get_bounds()
    o, e = b.origin, b.box_extent
    lines.append(f"{p.split('/')[-1]}: origin=({o.x:.1f},{o.y:.1f},{o.z:.1f}) extent=({e.x:.1f},{e.y:.1f},{e.z:.1f}) bottom={o.z-e.z:.1f}")

with open(r"C:\Users\25227\Documents\robot_game\docs\mesh_bounds.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\nBOUNDS_OK\n")
unreal.log("BOUNDS_OK")
for l in lines:
    unreal.log("BOUNDS " + l)
