# -*- coding: utf-8 -*-
"""探查扩建要用的资产：地面块、墙段、门洞、立柱的包围盒尺寸。"""
import unreal

OUT = r"C:\Users\25227\Documents\robot_game\docs\ext_assets.txt"
ENV = "/Game/RobotGame/Art/Environment"
PROPS = "/Game/RobotGame/Art/Props"

names = [
    (ENV, "SM_Env_Floor"),
    (ENV, "SM_Wall_Segment"),
    (ENV, "SM_Wall_Corner"),
    (ENV, "SM_Env_Pillar"),
    (ENV, "SM_Env_Catwalk"),
    (PROPS, "SM_Prop_Crate"),
]

lines = []


def log(s):
    lines.append(str(s))


for folder, nm in names:
    path = "%s/%s" % (folder, nm)
    a = unreal.EditorAssetLibrary.load_asset(path)
    if not a:
        log("%-22s MISSING" % nm)
        continue
    try:
        bb = a.get_bounding_box()
        mn = bb.min
        mx = bb.max
        log("%-22s size=(%.1f, %.1f, %.1f)  min=(%.1f,%.1f,%.1f)"
            % (nm, mx.x - mn.x, mx.y - mn.y, mx.z - mn.z, mn.x, mn.y, mn.z))
    except Exception as e:
        log("%-22s err %s" % (nm, e))

# 列出 Environment 下所有资产名，便于挑
try:
    all_assets = unreal.EditorAssetLibrary.list_assets(ENV, recursive=False)
    log("")
    log("== Environment assets ==")
    for p in all_assets:
        log("  " + p.split("/")[-1])
except Exception as e:
    log("list fail %s" % e)

with open(OUT, "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("EXT_ASSETS_DONE")
