# -*- coding: utf-8 -*-
"""找 severed_mech_arm GLB 里"背景平面"的特征：按 Z 分层面数/顶点分布。

背景平面通常是：Z 在最高/最低处、X/Y 跨度接近满宽、法线近竖直的大面。
按 Z 分桶统计面中心，找出离群的两层。结果写文件。
"""
import bpy
import sys
import mathutils

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
GLB = argv[0]
REPORT = argv[1]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
o = [x for x in bpy.context.scene.objects if x.type == "MESH"][0]
me = o.data
me.calc_loop_triangles()

# 全局 Z 范围
zs = [(o.matrix_world @ v.co).z for v in me.vertices]
zmin, zmax = min(zs), max(zs)
lines = ["Z 范围 %.3f .. %.3f  顶点 %d  三角面 %d" % (
    zmin, zmax, len(me.vertices), len(me.loop_triangles))]

# 按 Z 分 20 桶，统计三角面中心
NB = 20
buckets = [0]*NB
big_area = [0.0]*NB
for tri in me.loop_triangles:
    c = (o.matrix_world @ me.vertices[tri.vertices[0]].co +
         o.matrix_world @ me.vertices[tri.vertices[1]].co +
         o.matrix_world @ me.vertices[tri.vertices[2]].co) / 3.0
    b = int((c.z - zmin) / max(zmax-zmin, 1e-6) * NB)
    b = min(NB-1, max(0, b))
    buckets[b] += 1
    big_area[b] += tri.area
lines.append("桶  Z区间                 面数     总面积")
med = sorted(buckets)[NB//2]
for b in range(NB):
    lo = zmin + (zmax-zmin)*b/NB
    hi = zmin + (zmax-zmin)*(b+1)/NB
    mark = "  <<< 离群" if buckets[b] > med*8 and big_area[b] > 0.3 else ""
    lines.append("%2d  %6.3f..%6.3f   %7d  %8.3f%s" % (
        b, lo, hi, buckets[b], big_area[b], mark))

with open(REPORT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("ZLAYER_DONE")
