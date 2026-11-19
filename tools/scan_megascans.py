# -*- coding: utf-8 -*-
"""扫描本地 Megascans 资产（只读，不改任何东西）。

用途：用户在 Epic Launcher / Fab 里「下载 / 导出」资产到本地后，
跑这个脚本，我就能看到实际有哪些文件、什么格式，再决定导入方式。

⚠️ 只扫描，不导入、不移动、不删除。目录不存在时给出明确提示。
"""
import os
import sys
from collections import Counter

ROOTS = [
    r"C:\Users\25227\Documents\robot_game\art_src\megascans",
    r"C:\Users\25227\Documents\Megascans Library",
    r"C:\Users\25227\Documents\Quixel",
]
EXTS = (".uasset", ".fbx", ".obj", ".gltf", ".glb", ".usdz",
        ".png", ".jpg", ".jpeg", ".tga", ".exr", ".tif", ".tiff",
        ".zip", ".7z", ".rar", ".uplugin", ".uproject")


def scan(root):
    print("=== %s ===" % root)
    if not os.path.isdir(root):
        print("  (目录不存在 —— 说明还没有下载/导出到这里)")
        return
    n = 0
    ext_count = Counter()
    dirs = []
    for dp, dnames, fnames in os.walk(root):
        for f in fnames:
            n += 1
            e = os.path.splitext(f)[1].lower()
            ext_count[e] += 1
        if fnames:
            dirs.append((dp.replace(root, "").lstrip("\\") or ".", len(fnames)))
    print("  文件总数 %d" % n)
    print("  扩展名分布：")
    for e, c in ext_count.most_common():
        mark = " <== 几何/资产" if e in EXTS[:6] else (" <== 贴图" if e in EXTS[6:13] else "")
        print("    %-10s %5d%s" % (e or "(无扩展名)", c, mark))
    print("  含文件的子目录（前 40）：")
    for d, c in dirs[:40]:
        print("    %-70s %d 个文件" % (d[:70], c))
    if len(dirs) > 40:
        print("    ... 还有 %d 个" % (len(dirs) - 40))


for r in ROOTS:
    scan(r)

# 也扫一下工作项目 Content 里有没有意外导入的 Megascans 资产
proj = r"C:\Users\25227\Documents\robot_game\ue\Content"
hits = []
for dp, dnames, fnames in os.walk(proj):
    for f in fnames:
        if f.lower().endswith(".uasset") and ("megascans" in dp.lower()
                                              or "quixel" in dp.lower()):
            hits.append(os.path.join(dp, f))
print("\n=== 项目 Content 里的 Megascans/Quixel .uasset：%d 个 ===" % len(hits))
for h in hits[:15]:
    print("  " + h.replace(proj, ""))
print("\nMEGASCANS_SCAN_DONE")
