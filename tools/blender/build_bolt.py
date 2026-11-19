# -*- coding: utf-8 -*-
"""
余火协议 · 弹丸重建
================================================================
把"拉伸的引擎球体"换成一颗真正有形状的**等离子穿甲弹**：

    · 30cm 长 / 7cm 粗，卵形弹头 + 圆柱弹体 + 船尾（boat-tail）
    · 弹体上有车削凹槽、驱动环带，近看有金属加工的层次
    · 后段一圈**凹陷的曳光带**、腰部一圈细发光缝、尾部发光底碟
      —— 发光面单独占一个材质槽，不依赖贴图 UV，永远不会错位
    · 自定义圆柱投影 UV：U 绕一圈，V 沿弹轴，贴图不会撕裂

坐标约定（踩过坑，别改）：
    Blender 里沿 +Z 建，弹头朝 +Z → 绕 X 轴 +90° 变成朝 -Y
    → export_fbx 再绕 Z +90°，-Y 落到 UE 的 +X。
    最终 UE 里弹头朝 +X，正好等于 ProjectileMovement 的前向。

用法:
    blender --background --python build_bolt.py -- --out ../../assets/out
"""

import bpy
import bmesh
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import robotlib as R   # noqa: E402


# ══════════════════════════════════════════════════════════
# 尺寸（米）
# ══════════════════════════════════════════════════════════
Z_TAIL = -0.150
Z_NOSE = 0.148

# 弹壳轮廓 (r, z)。z 必须单调递增；r=0 会自动收成极点。
SHELL_PROFILE = [
    # ── 船尾：从底面向后收 ──
    (0.0240, -0.1500),
    (0.0282, -0.1450),
    (0.0318, -0.1380),
    (0.0342, -0.1290),
    (0.0354, -0.1200),
    # ── 后曳光带凹槽 ──
    (0.0360, -0.1170),
    (0.0360, -0.1040),
    (0.0330, -0.1022),
    (0.0330, -0.0798),
    (0.0360, -0.0780),
    (0.0360, -0.0500),
    # ── 驱动环带（略微凸起，给出金属层次）──
    (0.0382, -0.0475),
    (0.0382, -0.0360),
    (0.0389, -0.0352),
    (0.0389, -0.0300),
    (0.0362, -0.0282),
    (0.0362, -0.0240),
    # ── 腰部发光缝的凹槽 ──
    (0.0336, -0.0226),
    (0.0336, -0.0196),
    (0.0362, -0.0182),
    # ── 前段弹体 ──
    (0.0362, 0.0180),
    (0.0358, 0.0300),
    # ── 卵形弹头 ──
    (0.0352, 0.0420),
    (0.0348, 0.0500),
    (0.0342, 0.0600),
    (0.0333, 0.0700),
    (0.0320, 0.0800),
    (0.0302, 0.0900),
    (0.0280, 0.1000),
    (0.0253, 0.1100),
    (0.0218, 0.1200),
    (0.0175, 0.1300),
    (0.0124, 0.1380),
    (0.0080, 0.1440),
    (0.0058, 0.1472),
    (0.0055, 0.1480),
]


def hard_edges(ob, angle_deg=30.0):
    """按角度拆分法线 —— 车削件的棱线要硬，弧面要顺。"""
    R.activate(ob)
    m = ob.modifiers.new("es", 'EDGE_SPLIT')
    m.split_angle = math.radians(angle_deg)
    m.use_edge_angle = True
    m.use_edge_sharp = True
    try:
        bpy.ops.object.modifier_apply(modifier=m.name)
    except Exception as e:
        print("    [warn] edge split: %s" % e)
    return ob


def cyl_uv(ob, z0, z1):
    """圆柱投影 UV：U = 绕轴角度（0~1 一圈），V = 沿轴位置（0~1）。"""
    me = ob.data
    while len(me.uv_layers) > 1:
        me.uv_layers.remove(me.uv_layers[-1])
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uvl = me.uv_layers[0]
    span = max(z1 - z0, 1e-6)

    for poly in me.polygons:
        angs = []
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            a = math.atan2(v.y, v.x) / (2.0 * math.pi) + 0.5
            angs.append(a)
        # 跨接缝的面：把小于 0.5 的角度整体 +1，避免 UV 反折
        if max(angs) - min(angs) > 0.5:
            angs = [(a + 1.0 if a < 0.5 else a) for a in angs]
        for li, a in zip(poly.loop_indices, angs):
            z = me.vertices[me.loops[li].vertex_index].co.z
            uvl.data[li].uv = (a, (z - z0) / span)


def build():
    R.new_scene()

    shell_mat = R._mat("M_BoltShell", (0.165, 0.178, 0.198), 0.86, 0.30)
    trim_mat = R._mat("M_BoltTrim", (0.400, 0.425, 0.455), 0.95, 0.16)
    glow_mat = R._mat("M_BoltGlow", (0.020, 0.028, 0.034), 0.0, 0.12,
                      emission=(0.30, 0.95, 1.00), strength=14.0)

    parts = []

    # ── 1. 弹壳 ──
    shell = R.lathe("bolt_shell", SHELL_PROFILE, seg=48, mat=shell_mat,
                    smooth=True)
    hard_edges(shell, 34.0)
    parts.append(shell)

    # ── 2. 后曳光带（凹槽里的一圈，略低于弹体表面）──
    band = R.lathe("bolt_tracer", [
        (0.0334, -0.1018),
        (0.0346, -0.1006),
        (0.0346, -0.0808),
        (0.0334, -0.0796),
    ], seg=48, mat=glow_mat, smooth=True)
    parts.append(band)

    # ── 3. 腰部细发光缝 ──
    seam = R.lathe("bolt_waist_seam", [
        (0.0338, -0.0224),
        (0.0352, -0.0220),
        (0.0352, -0.0200),
        (0.0338, -0.0196),
    ], seg=48, mat=glow_mat, smooth=True)
    parts.append(seam)

    # ── 4. 尾部底碟：从正后方看是一颗发光的"推进器"──
    base = R.lathe("bolt_base_glow", [
        (0.0000, -0.1512),
        (0.0120, -0.1510),
        (0.0190, -0.1504),
        (0.0232, -0.1496),
    ], seg=40, mat=glow_mat, smooth=True)
    parts.append(base)

    # ── 5. 弹头风帽环：一圈抛光钢，压住卵形与弹体的分界 ──
    cap = R.lathe("bolt_nose_ring", [
        (0.0360, 0.0296),
        (0.0367, 0.0302),
        (0.0367, 0.0326),
        (0.0358, 0.0332),
    ], seg=48, mat=trim_mat, smooth=True)
    parts.append(cap)

    # ── 合并 + UV ──
    mesh = R.join_objects(parts, "SM_Bolt_Round")
    cyl_uv(mesh, Z_TAIL, Z_NOSE)

    # ── 弹轴转到 UE 的 +X（Blender -Y → UE +X）──
    mesh.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    R.activate(mesh)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    # ── 预览：临时横过来（弹头朝 +X），导出前必须归零 ──
    mesh.rotation_euler = (0.0, 0.0, math.radians(90.0))
    bpy.context.view_layer.update()

    print("  bolt: %d tris  dims=%s"
          % (R.tri_count(mesh), tuple(round(v, 3) for v in mesh.dimensions)))
    print("  slots: %s" % [m.name for m in mesh.data.materials])
    return mesh


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    out_dir = "../../assets/out"
    i = 0
    while i < len(argv):
        if argv[i] == "--out" and i + 1 < len(argv):
            out_dir = argv[i + 1]
            i += 2
        else:
            i += 1
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    mesh = build()

    # 预览图（横放，3/4 机位）
    png = os.path.join(out_dir, "preview_bolt.png")
    R.setup_render(png, (0, 0, 0.0), res=1000, wide=True,
                   span=(0.40, 0.22), lens=72, flat=False)
    R.render_to(png)
    print("  [ok] preview_bolt.png")

    # 第二张：从尾部斜后方看，检查发光底碟与曳光带
    png2 = os.path.join(out_dir, "preview_bolt_rear.png")
    R.setup_render(png2, (0, 0, 0.0), res=1000, wide=True,
                   span=(0.36, 0.24), lens=72, flat=False)
    cam = bpy.context.scene.camera
    dist = 0.72
    cam.location = (-dist * 0.90, dist * 0.42, dist * 0.30)
    R.render_to(png2)
    print("  [ok] preview_bolt_rear.png")

    # 还原成导出姿态（弹头 -Y），否则 export_fbx 的 +90° Z 会叠加
    R.activate(mesh)
    mesh.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    base = os.path.join(out_dir, "bolt_round")
    R.save_blend(base + ".blend")
    try:
        R.export_fbx(base + ".fbx")
        print("  [ok] bolt_round.fbx")
    except Exception as e:
        print("  [FAIL] fbx: %s" % e)


if __name__ == "__main__":
    main()
