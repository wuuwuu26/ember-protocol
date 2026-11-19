# -*- coding: utf-8 -*-
t = open(r"C:\Users\25227\Documents\robot_game\docs\overlap_diag.txt", encoding="utf-8").read()
print("=== 全部剩余重叠对 ===")
for l in t.splitlines():
    if "重叠(" in l:
        print(l)
print()
print("=== 涉及 MechWreck 碎骸的相交 段 ===")
i = t.find("涉及 MechWreck")
seg = t[i:].splitlines()
rest = "\n".join(seg[1:]).strip()
print(rest if rest else "(空) —— 碎骸穿模已彻底消除")
