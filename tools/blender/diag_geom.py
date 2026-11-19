# -*- coding: utf-8 -*-
"""诊断 severed_mech_arm_tex.glb 的几何构成（结果写文件，不靠 stdout）。"""
import bpy
import sys
import mathutils
import os

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
GLB = argv[0]
REPORT = argv[1]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)

lines = []
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
lines.append("对象数 %d" % len(meshes))
for o in meshes:
    me = o.data
    # 每个面的面积统计
    areas = []
    for p in me.polygons:
        areas.append(p.area)
    areas.sort(reverse=True)
    mn = [1e9]*3; mx = [-1e9]*3
    for c in o.bound_box:
        w = o.matrix_world @ mathutils.Vector(c)
        for i in range(3):
            mn[i]=min(mn[i],w[i]); mx[i]=max(mx[i],w[i])
    dims = [mx[i]-mn[i] for i in range(3)]
    lines.append("OBJ %s  面数=%d  顶点=%d  尺寸=(%.2f,%.2f,%.2f)" % (
        o.name, len(me.polygons), len(me.vertices), dims[0],dims[1],dims[2]))
    lines.append("  最大10个面面积: %s" % [round(a,3) for a in areas[:10]])
    lines.append("  中位面面积: %.5f" % (areas[len(areas)//2] if areas else 0))
    # 材质
    lines.append("  材质: %s" % [m.name if m else "None" for m in me.materials])

with open(REPORT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("GEOM_DIAG_DONE")
