# -*- coding: utf-8 -*-
"""列出 FBX 里的 Model（骨骼/网格）名，用来确认骨架是否已更新。

为什么要这个：FBX 是二进制，grep 看不到骨骼名。重建骨架后必须确认
资产里真的是 thigh_L/shin_L/foot_L 三段腿，否则 UE 里程序化动画
按名字找不到骨骼会静默退回单段腿 —— 表现就是"腿还是一根棍"。

用法: python tools/_list_fbx_bones.py <file.fbx> [...]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_fbx  # noqa: E402


def main():
    for fn in sys.argv[1:]:
        ver, root = check_fbx.parse_fbx(fn)
        names = []
        for m in root.find_all("Model"):
            if len(m.props) >= 2 and isinstance(m.props[1], str):
                # FBX 把名字和类名用 \x00\x01 连在一起
                names.append(m.props[1].split("\x00")[0])
        skel = [n for n in names if not n.startswith("SK_")]
        print("=== %-28s ver%d  共 %d Model / %d 骨骼"
              % (os.path.basename(fn), ver, len(names), len(skel)))
        print("    " + ", ".join(skel))


main()
