"""逐个渲染敌人，多角度，用于体检建模完整性。

用法：blender --background --python render_enemy_audit.py -- --out <dir> --only <code>
"""
import bpy
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import robotlib as R
import build_enemies as B
from mathutils import Vector


def render_view(png, target, distance, yaw_deg, elev_deg, res=900):
    R.setup_render(png, target, distance=distance, res=res, flat=True)
    scene = bpy.context.scene
    cam = scene.camera
    a = math.radians(yaw_deg)
    e = math.radians(elev_deg)
    h = distance * math.sin(e)
    r = distance * math.cos(e)
    cam.location = (r * math.sin(a), -r * math.cos(a), target[2] + h)
    bpy.context.view_layer.update()
    scene.render.filepath = png
    scene.render.resolution_x = res
    scene.render.resolution_y = res
    bpy.ops.render.render(write_still=True)


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    out_dir, only = "./out_audit", ""
    i = 0
    while i < len(argv):
        if argv[i] == "--out" and i + 1 < len(argv):
            out_dir = argv[i + 1]; i += 2
        elif argv[i] == "--only" and i + 1 < len(argv):
            only = argv[i + 1]; i += 2
        else:
            i += 1
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    for code, fn, accent, glow in B.CATALOG:
        if only and code != only:
            continue
        R.new_scene()
        R.SPLIT_LEGS = code in ("gardener", "weather", "guard")
        R.SPLIT_QUAD = code in ("hauler", "colossus")
        pal = R.Palette(accent, glow, "enemy_%s" % code)
        objs, label, height = fn(pal)
        print("\n[AUDIT] %s label=%s objects=%d" % (code, label, len(objs)))
        flat_objs = []
        for ob in objs:
            if isinstance(ob, (list, tuple)):
                flat_objs.extend(ob)
            else:
                flat_objs.append(ob)
        for ob in flat_objs:
            try:
                print("   OBJ %-30s tris=%d" % (ob.name, R.tri_count(ob)))
            except Exception as e:
                print("   OBJ ? %s" % e)

        mesh, arm, lods = R.auto_rig(objs, "Enemy_%s" % code.capitalize())
        mn, mx = R.world_bounds([mesh])
        print("[AUDIT] %s tris=%d bones=%d bounds z=%.2f..%.2f x=%.2f..%.2f y=%.2f..%.2f" % (
            code, R.tri_count(mesh), len(arm.data.bones), mn[2], mx[2],
            mn[0], mx[0], mn[1], mx[1]))
        print("[AUDIT] bones: %s" % ",".join(b.name for b in arm.data.bones))

        hgt = mx[2] - mn[2]
        dist = max(hgt * 2.2, 2.4)
        tgt = (0, 0, (mn[2] + mx[2]) * 0.5)
        for vname, yaw, elev in (("front", 0, 6), ("side", 90, 6),
                                 ("back", 180, 6), ("q34", 38, 16),
                                 ("top", 0, 62)):
            render_view(os.path.join(out_dir, "audit_%s_%s.png" % (code, vname)),
                        tgt, dist, yaw, elev)
    print("[AUDIT] DONE")


main()
