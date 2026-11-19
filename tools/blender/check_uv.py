import os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import bpy
import robotlib as R
import build_chassis as BC

P = BC.variant_params("medium")
pal = R.Palette(P["accent"], P["glow"], P["code"])
R.new_scene()
pal = R.Palette(P["accent"], P["glow"], P["code"])
A = BC.build(P, pal)
mesh = R.join_objects(A.all, "TEST")
R.cube_uv(mesh, size_m=3.2)   # 模拟 build_one 的流程
print("UV 层数:", len(mesh.data.uv_layers))
if mesh.data.uv_layers:
    uv = mesh.data.uv_layers[0].data
    us = [d.uv[0] for d in uv]
    vs = [d.uv[1] for d in uv]
    print("UV 范围 u: %.3f ~ %.3f   v: %.3f ~ %.3f" % (min(us), max(us), min(vs), max(vs)))
    print("顶点循环数:", len(uv))
