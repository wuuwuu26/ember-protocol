# -*- coding: utf-8 -*-
"""查关键 mesh 的局部 bbox 尺寸，判断层高/悬空。"""
import unreal
EAL = unreal.EditorAssetLibrary
lines = []
def log(s):
    unreal.log("[MeshSize] %s" % s); lines.append(str(s))

NAMES = ["met-wooden-crate01a", "ww2-sandbag-stack-02b-smoked",
         "met-barrel01-set01", "ww2-heater-smoked", "ww2-fridge",
         "ww2-field-fences-01a", "ww2-drawer-smoked",
         "pipe_junction", "crane_arm", "generator", "mech_core"]
BASE = "/Game/RobotGame/Art/Props"
# 在 Cosmos / Gen3D 目录下找 SM_ 资产
for root in ("%s/Cosmos" % BASE, "%s/Gen3D" % BASE):
    for a in EAL.list_assets(root, recursive=True):
        nm = a.rsplit("/", 1)[-1]
        if not nm.startswith("SM_"):
            continue
        o = EAL.load_asset(a)
        if not o or "StaticMesh" not in o.get_class().get_name():
            continue
        bb = o.get_bounding_box()
        log("%-34s size=(%.0f,%.0f,%.0f) min=(%.0f,%.0f,%.0f) max=(%.0f,%.0f,%.0f)"
            % (nm[:34], bb.max.x-bb.min.x, bb.max.y-bb.min.y, bb.max.z-bb.min.z,
               bb.min.x, bb.min.y, bb.min.z, bb.max.x, bb.max.y, bb.max.z))
with open(r"C:\Users\25227\Documents\robot_game\docs\mesh_sizes.txt","wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("MESH_SIZE_DONE")
