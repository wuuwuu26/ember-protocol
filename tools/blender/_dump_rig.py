"""临时：打开 .blend 并打印骨骼原点/父子关系，用于验证关节支点。"""
import bpy
import sys
import os

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
path = argv[0] if argv else ""

bpy.ops.wm.open_mainfile(filepath=path)

for ob in bpy.data.objects:
    if ob.type != 'ARMATURE':
        continue
    print("=== ARMATURE %s ===" % ob.name)
    for b in ob.data.bones:
        h = b.head_local
        t = b.tail_local
        p = b.parent.name if b.parent else "-"
        print("  %-14s head=(%7.3f,%7.3f,%7.3f) tail=(%7.3f,%7.3f,%7.3f) parent=%s"
              % (b.name, h[0], h[1], h[2], t[0], t[1], t[2], p))

for ob in bpy.data.objects:
    if ob.type == 'MESH' and 'LOD' not in ob.name:
        print("MESH %s  verts=%d  groups=%s"
              % (ob.name, len(ob.data.vertices),
                 sorted(g.name for g in ob.vertex_groups)))
        break
