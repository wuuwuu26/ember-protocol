"""
FBX 导出尺寸验证器（往返测试）
================================================
把每个导出的 FBX 重新导入 Blender 并量出真实尺寸。

为什么必须做往返测试：直接读 FBX 里的顶点数据会得出错误结论 ——
Blender 会把缩放写在 Model 节点的 `Lcl Scaling` 上，几何数据本身仍是米。
只有走一遍完整的「导入 → 量世界包围盒」，才能得到导入器实际看到的结果。

用法:
    blender --background --python verify_fbx.py -- --dir ../../assets/out
"""

import bpy
import mathutils
import os
import sys

# 每类资产的高度期望区间（米）。超出即报错。
EXPECTED = {
    "chassis":  (2.0, 3.2),
    "module":   (0.10, 1.60),
    "enemy":    (0.40, 9.00),
    "prop":     (0.10, 3.00),
    "env":      (0.20, 6.00),
    "landmark": (14.0, 30.0),
    "robot":    (2.0, 3.2),
}


def clear():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def measure(path):
    clear()
    try:
        bpy.ops.import_scene.fbx(filepath=path)
    except Exception as e:
        return None, str(e)

    mn = [1e9] * 3
    mx = [-1e9] * 3
    found = False
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        for c in ob.bound_box:
            w = ob.matrix_world @ mathutils.Vector(c)
            for i in range(3):
                mn[i] = min(mn[i], w[i])
                mx[i] = max(mx[i], w[i])
            found = True
    if not found:
        return None, "未导入任何网格"
    return (mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2]), None


def expected_range(name):
    for prefix, rng in EXPECTED.items():
        if name.startswith(prefix):
            return rng
    return None


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    out_dir = None
    i = 0
    while i < len(argv):
        if argv[i] == "--dir" and i + 1 < len(argv):
            out_dir = argv[i + 1]; i += 2
        else:
            i += 1

    if out_dir is None:
        here = os.path.dirname(os.path.abspath(__file__))
        out_dir = os.path.abspath(os.path.join(here, "..", "..", "assets", "out"))
    out_dir = os.path.abspath(out_dir)

    files = sorted(f for f in os.listdir(out_dir) if f.lower().endswith(".fbx"))
    print("验证目录: %s" % out_dir)
    print("待验证: %d 个 FBX" % len(files))
    print("")

    ok, bad, skipped = 0, 0, 0
    rows = []
    for f in files:
        path = os.path.join(out_dir, f)
        size, err = measure(path)
        if size is None:
            rows.append((f, None, err, "SKIP"))
            skipped += 1
            continue

        # 导入后 Blender 是 Z 轴向上，Z 即高度
        height = size[2]
        rng = expected_range(f)
        if rng is None:
            verdict = "?"
        elif rng[0] <= height <= rng[1]:
            verdict = "OK"
            ok += 1
        else:
            verdict = "FAIL"
            bad += 1
        rows.append((f, size, None, verdict))

    print("%-34s %8s %8s %8s   %s" % ("文件", "宽 X", "深 Y", "高 Z", "判定"))
    print("-" * 74)
    for f, size, err, verdict in rows:
        if size is None:
            print("%-34s %s  (%s)" % (f, verdict, err))
        else:
            mark = {"OK": "✅", "FAIL": "❌", "?": "  "}.get(verdict, "  ")
            print("%-34s %8.3f %8.3f %8.3f   %s %s"
                  % (f, size[0], size[1], size[2], mark, verdict))

    print("")
    print("=" * 74)
    print("通过 %d  失败 %d  跳过 %d  合计 %d" % (ok, bad, skipped, len(files)))
    if bad:
        print("")
        print("失败项的高度与期望区间不符。若全部偏大/偏小 100 倍，")
        print("检查 robotlib.export_fbx() 的 global_scale 是否被改成了非 1.0 的值。")


if __name__ == "__main__":
    main()
