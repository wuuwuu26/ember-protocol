"""
FBX 单位与坐标轴验证器
================================================
直接解析 FBX 二进制文件，读出 GlobalSettings，算出 UE 会如何解读它。

为什么不用打开 UE：FBX 的 GlobalSettings 节点里就记录了 UnitScaleFactor
与 UpAxis/FrontAxis/CoordAxis，而 UE 的导入行为完全由这几个值决定。
解析出来就能提前判断，不必等装完引擎。

用法:
    python check_fbx.py <file.fbx> [更多文件...]
"""

import os
import struct
import sys
import zlib

_ITEMSIZE = {"f": 4, "d": 8, "l": 8, "i": 4, "b": 1}


# ─────────────────────────────────────────────
# FBX 二进制解析
# ─────────────────────────────────────────────

class Node(object):
    __slots__ = ("name", "props", "children")

    def __init__(self, name):
        self.name = name
        self.props = []
        self.children = []

    def find(self, name):
        for c in self.children:
            if c.name == name:
                return c
        return None

    def find_all(self, name, out=None):
        if out is None:
            out = []
        for c in self.children:
            if c.name == name:
                out.append(c)
            c.find_all(name, out)
        return out


def read_property(f, ver):
    t = f.read(1)
    if not t:
        raise EOFError
    t = t.decode("ascii", "replace")
    if t == "Y":
        return struct.unpack("<h", f.read(2))[0]
    if t == "C":
        return struct.unpack("<B", f.read(1))[0] != 0
    if t == "I":
        return struct.unpack("<i", f.read(4))[0]
    if t == "F":
        return struct.unpack("<f", f.read(4))[0]
    if t == "D":
        return struct.unpack("<d", f.read(8))[0]
    if t == "L":
        return struct.unpack("<q", f.read(8))[0]
    if t in "fdlib":
        arr_len, encoding, comp_len = struct.unpack("<III", f.read(12))
        if encoding == 0:
            raw = f.read(_ITEMSIZE[t] * arr_len)
        else:
            # encoding 1 = zlib/deflate。Blender 默认压缩数组，
            # 不解压的话顶点数会全部读成 0。
            raw = f.read(comp_len)
            try:
                raw = zlib.decompress(raw)
            except Exception:
                return ("array", t, None)
        if t == "d":
            return ("array", t, struct.unpack("<%dd" % arr_len, raw[:_ITEMSIZE[t] * arr_len]))
        if t == "f":
            return ("array", t, struct.unpack("<%df" % arr_len, raw[:_ITEMSIZE[t] * arr_len]))
        if t == "l":
            return ("array", t, struct.unpack("<%dq" % arr_len, raw[:_ITEMSIZE[t] * arr_len]))
        if t == "i":
            return ("array", t, struct.unpack("<%di" % arr_len, raw[:_ITEMSIZE[t] * arr_len]))
        return ("array", t, raw)
    if t in "SR":
        ln = struct.unpack("<I", f.read(4))[0]
        data = f.read(ln)
        if t == "S":
            return data.decode("utf-8", "replace")
        return "<raw %d>" % ln
    raise ValueError("未知属性类型 %r" % t)


def read_node(f, ver):
    if ver >= 7500:
        end_off, num_props, prop_len = struct.unpack("<QQQ", f.read(24))
        name_len = struct.unpack("<B", f.read(1))[0]
        header = 25
    else:
        end_off, num_props, prop_len = struct.unpack("<III", f.read(12))
        name_len = struct.unpack("<B", f.read(1))[0]
        header = 13

    if end_off == 0:
        return None

    name = f.read(name_len).decode("utf-8", "replace")
    node = Node(name)
    for _ in range(num_props):
        node.props.append(read_property(f, ver))

    while f.tell() < end_off:
        child = read_node(f, ver)
        if child is None:
            break
        node.children.append(child)
    f.seek(end_off)
    return node


def parse_fbx(path):
    with open(path, "rb") as f:
        head = f.read(23)
        if not head.startswith(b"Kaydara FBX Binary"):
            raise ValueError("不是 FBX 二进制文件（可能是 ASCII 格式）")
        # 头部结构：20 字节 "Kaydara FBX Binary  " + 3 字节 00 1A 00 = 23 字节 magic，
        # 版本号（uint32 LE）紧跟其后。多跳 2 字节会把版本读成垃圾值。
        ver = struct.unpack("<I", f.read(4))[0]

        root = Node("root")
        while True:
            node = read_node(f, ver)
            if node is None:
                break
            root.children.append(node)
    return ver, root


# ─────────────────────────────────────────────
# 分析
# ─────────────────────────────────────────────

def analyze(path):
    print("=" * 66)
    print(os.path.basename(path))
    print("=" * 66)

    try:
        ver, root = parse_fbx(path)
    except Exception as e:
        print("  [失败] %s" % e)
        return None

    print("  FBX 版本: %d" % ver)

    gs = root.find("GlobalSettings")
    if gs is None:
        print("  [警告] 找不到 GlobalSettings，无法判断单位")
        return None

    props = gs.find("Properties70")
    values = {}
    if props:
        for p in props.children:
            if p.name == "P" and len(p.props) >= 5:
                values[p.props[0]] = p.props[4]

    usf = values.get("UnitScaleFactor", None)
    up_axis = values.get("UpAxis", None)
    front_axis = values.get("FrontAxis", None)
    coord_axis = values.get("CoordAxis", None)
    up_sign = values.get("UpAxisSign", 1)
    front_sign = values.get("FrontAxisSign", 1)
    coord_sign = values.get("CoordAxisSign", 1)

    axis_names = {0: "X", 1: "Y", 2: "Z"}
    print("  UnitScaleFactor : %s" % usf)
    print("  坐标轴          : Up=%s%s  Front=%s%s  Coord=%s%s" % (
        axis_names.get(up_axis, "?"), "+" if up_sign > 0 else "-",
        axis_names.get(front_axis, "?"), "+" if front_sign > 0 else "-",
        axis_names.get(coord_axis, "?"), "+" if coord_sign > 0 else "-"))

    # 统计网格顶点，并量出真实包围盒 ——
    # 只有量出几何数据本身的尺寸，才能判断 UnitScaleFactor=1.0 到底是
    # 「几何已按厘米存」还是「几何仍是米，需要靠 USF 换算」。
    geos = root.find_all("Geometry")
    total_verts = 0
    bmin = [1e30, 1e30, 1e30]
    bmax = [-1e30, -1e30, -1e30]
    for g in geos:
        v = g.find("Vertices")
        if v is None or not v.props:
            continue
        arr = v.props[0]
        if not (isinstance(arr, tuple) and len(arr) == 3) or arr[2] is None:
            continue
        data = arr[2]
        n = len(data) // 3
        total_verts += n
        for i in range(n):
            for k in range(3):
                val = data[i * 3 + k]
                if val < bmin[k]:
                    bmin[k] = val
                if val > bmax[k]:
                    bmax[k] = val

    if total_verts > 0:
        size = [bmax[k] - bmin[k] for k in range(3)]
        print("  网格数          : %d（顶点合计 %d）" % (len(geos), total_verts))
        print("  几何包围盒      : X %.2f  Y %.2f  Z %.2f  （FBX 单位）"
              % (size[0], size[1], size[2]))
        print("  注意 FBX 是 Y 轴向上，所以 Y 方向是高度")
    else:
        print("  网格数          : %d（顶点合计 %d）" % (len(geos), total_verts))
        size = None

    # 骨骼
    models = root.find_all("Model")
    print("  模型节点数      : %d" % len(models))

    # ── 换算 ──
    # FBX 的 UnitScaleFactor 语义：1 FBX 单位 = USF 厘米。
    # UE 的 FBX 导入器默认按「1 单位 = 1 厘米」读取几何数据。
    if usf and size:
        height_units = size[1]           # Y 轴向上
        print("")
        print("  ── UE 导入换算 ──")
        print("  几何高度 %.2f FBX 单位 × USF %.1f = %.2f 厘米 = %.3f 米"
              % (height_units, usf, height_units * usf, height_units * usf / 100.0))
        print("")
        print("  判读：")
        meters = height_units * usf / 100.0
        if 2.0 <= meters <= 3.0:
            print("    ✅ 高度 %.2f 米，符合设计（机体 2.4—2.6 米）。" % meters)
            print("       导入 UE 时 Uniform Scale 保持 1.0 即可。")
        elif 0.02 <= meters <= 0.03:
            print("    ❌ 高度只有 %.3f 米 —— 小了一百倍。" % meters)
            print("       导入 UE 时把 Uniform Scale 设为 100。")
        elif 200.0 <= meters <= 300.0:
            print("    ❌ 高度达 %.1f 米 —— 大了一百倍。" % meters)
            print("       导入 UE 时把 Uniform Scale 设为 0.01。")
        else:
            print("    ⚠️ 高度 %.3f 米，不在预期区间，需实际导入确认。" % meters)

    print("")
    return {"usf": usf, "up": up_axis, "front": front_axis, "coord": coord_axis,
            "verts": total_verts, "geos": len(geos), "ver": ver,
            "size": size}


def main():
    files = sys.argv[1:]
    if not files:
        here = os.path.dirname(os.path.abspath(__file__))
        default = os.path.abspath(os.path.join(here, "..", "assets", "out"))
        files = [os.path.join(default, f)
                 for f in ("chassis_medium.fbx", "module_head_scout.fbx",
                           "enemy_colossus.fbx")]
        files = [f for f in files if os.path.exists(f)]
        if not files:
            print("用法: python check_fbx.py <file.fbx> ...")
            return

    results = [analyze(f) for f in files]

    print("=" * 66)
    print("汇总")
    print("=" * 66)
    for f, r in zip(files, results):
        if r:
            print("  %-28s USF=%-7s 网格=%-3d 顶点=%d"
                  % (os.path.basename(f), r["usf"], r["geos"], r["verts"]))


if __name__ == "__main__":
    main()
