# -*- coding: utf-8 -*-
"""诊断 Cosmos 资产的 Nanite 状态与面数（第一百零四轮）。

编辑器弹出"缺失项目设置：Nanite 需要 SM6"警告。
项目 DefaultEngine.ini 刻意保持渲染默认、不改 SM6（历史全黑教训），
所以优先判断：能否直接关掉这批道具的 Nanite，而不动项目设置。
"""
import unreal

BASE = "/Game/RobotGame/Art/Props/Cosmos"
EAL = unreal.EditorAssetLibrary
ESM = unreal.EditorStaticMeshLibrary
out = []

assets = [p for p in EAL.list_assets(BASE, recursive=True)
          if p.split("/")[-1].startswith("SM_")]
out.append("Cosmos StaticMesh 共 %d 个" % len(assets))
out.append("")

nanite_on = []
for p in sorted(assets):
    m = EAL.load_asset(p)
    if not m:
        continue
    short = p.split("/")[-1]
    # Nanite 设置
    nanite = "?"
    try:
        ns = m.get_editor_property("nanite_settings")
        nanite = str(ns.get_editor_property("enabled"))
        if ns.get_editor_property("enabled"):
            nanite_on.append(p)
    except Exception as e:
        nanite = "err:%s" % e
    # 面数（LOD0）
    tris = "?"
    try:
        tris = str(ESM.get_number_verts(m, 0))
    except Exception:
        try:
            tris = str(m.get_num_triangles(0))
        except Exception:
            pass
    try:
        bb = m.get_bounding_box()
        dims = "(%.0f,%.0f,%.0f)" % (bb.max.x-bb.min.x,
                                      bb.max.y-bb.min.y,
                                      bb.max.z-bb.min.z)
    except Exception:
        dims = "?"
    out.append("%-46s nanite=%-5s verts(LOD0)=%-8s bbox=%s" %
               (short, nanite, tris, dims))

out.append("")
out.append("开启 Nanite 的资产 %d 个：" % len(nanite_on))
for p in nanite_on:
    out.append("  " + p)

with open(r"C:\Users\25227\Documents\robot_game\docs\cosmos_nanite.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("COSMOS_NANITE_DONE")
