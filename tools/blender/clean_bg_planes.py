# -*- coding: utf-8 -*-
"""按 Z 分层删除 Hunyuan3D 白模里的"背景大平面"（第一百一十八轮）。

severed_mech_arm 的贴图 GLB 里，Z 的 [-0.993,-0.899] 和 [0.701,0.796]
两层各有 ~25 万面、面积 7~8（其它层仅几千~3万面），正是投影贴图时
把"背景平面"重建进网格产生的两个白板。删除这两层面即可。

通用判定：把 Z 分 20 桶，删除"面数 > 中位数×8 且总面积 > 3"的离群桶
（不写死坐标，其它资产也能用）。

用法：
  blender -b --python clean_bg_planes.py -- <in.glb> <out.glb>
"""
import bpy
import sys
import os
import bmesh
import mathutils

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC, DST = argv[0], argv[1]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)

objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
lines = []

for o in objs:
    me = o.data
    me.calc_loop_triangles()
    # 用 bmesh 便于删面
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()

    # 世界 Z（模型可能有变换）
    # 收集每个面的中心 Z（用 bmesh 面）
    face_z = []
    for f in bm.faces:
        c = o.matrix_world @ f.calc_center_median()
        face_z.append(c.z)
    zmin, zmax = min(face_z), max(face_z)

    NB = 20
    buckets = [0]*NB
    areas = [0.0]*NB
    for i, f in enumerate(bm.faces):
        b = int((face_z[i]-zmin)/max(zmax-zmin, 1e-6)*NB)
        b = min(NB-1, max(0, b))
        buckets[b] += 1
        areas[b] += f.calc_area()
    med = sorted(buckets)[NB//2]
    bad = [b for b in range(NB)
           if buckets[b] > med*8 and areas[b] > 3.0]

    lines.append("OBJ %s 面数=%d Z=%.3f..%.3f 中位桶=%d 删除桶=%s" % (
        o.name, len(bm.faces), zmin, zmax, med, bad))
    if not bad:
        bm.free()
        continue

    # 删掉落在坏桶里的面
    to_del = []
    for i, f in enumerate(bm.faces):
        b = int((face_z[i]-zmin)/max(zmax-zmin, 1e-6)*NB)
        b = min(NB-1, max(0, b))
        if b in bad:
            to_del.append(f)
    bmesh.ops.delete(bm, geom=to_del, context='FACES')
    lines.append("  删除 %d 个面，剩余 %d" % (len(to_del), len(bm.faces)))

    bm.to_mesh(me)
    bm.free()
    me.update()

# 导出剩下的
bpy.ops.object.select_all(action="DESELECT")
for o in bpy.context.scene.objects:
    if o.type == "MESH":
        o.select_set(True)
bpy.ops.export_scene.gltf(filepath=DST, export_format="GLB",
                          use_selection=True, export_apply=True)

with open(r"C:\Users\25227\Documents\robot_game\docs\clean_bg_log.txt",
          "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("CLEAN_BG_DONE %s %.1f MB" % (DST, os.path.getsize(DST)/1048576.0))
