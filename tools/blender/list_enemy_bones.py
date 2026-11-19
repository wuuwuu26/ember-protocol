"""列出敌人 FBX 的骨骼名与父子关系，验证步态代码能否找到 thigh/shin/foot。"""
import bpy
import sys
import os

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
path = argv[0]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=path)

print("ENEMY_FILE", os.path.basename(path))
for ob in bpy.context.scene.objects:
    if ob.type != 'ARMATURE':
        continue
    for b in ob.data.bones:
        p = b.parent.name if b.parent else "-"
        print("ENEMY_BONE %-12s parent=%s" % (b.name, p))
print("ENEMY_BONES_DONE")
