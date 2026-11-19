"""审计底盘 FBX：列出每个网格对象的顶点组（骨骼绑定）与包围盒，找未绑定或位置异常的部件。"""
import bpy
import sys
import os
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
fbx = argv[0]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)

meshes = [o for o in bpy.context.scene.objects
          if o.type == 'MESH' and not o.name.endswith(("_LOD1", "_LOD2"))]
print("AUDIT_FILE", os.path.basename(fbx), "meshes", len(meshes))
unbound = []
for ob in sorted(meshes, key=lambda o: o.name):
    groups = [g.name for g in ob.vertex_groups]
    me = ob.data
    # 是否所有顶点都有权重
    weighted = sum(1 for v in me.vertices if v.groups)
    total = len(me.vertices)
    mn = [1e9] * 3
    mx = [-1e9] * 3
    for c in ob.bound_box:
        w = ob.matrix_world @ Vector(c)
        for i in range(3):
            mn[i] = min(mn[i], w[i])
            mx[i] = max(mx[i], w[i])
    tag = ""
    if total > 0 and weighted < total:
        tag = " UNWEIGHTED(%d/%d)" % (weighted, total)
        unbound.append(ob.name)
    if not groups:
        tag += " NOGROUP"
        unbound.append(ob.name)
    print("AUDIT %-26s grp=%-10s verts=%5d pos=(%.2f,%.2f,%.2f)%s"
          % (ob.name, (groups[0] if groups else "-"), total,
             (mn[0] + mx[0]) * 0.5, (mn[1] + mx[1]) * 0.5, (mn[2] + mx[2]) * 0.5, tag))
print("AUDIT_UNBOUND", unbound)
print("AUDIT_DONE")
