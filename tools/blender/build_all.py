"""
余火协议 · 全量资产生成
================================================
一次跑完所有建模脚本，并输出资产清单。

用法:
    blender --background --python build_all.py -- --out ../../assets/out
    blender --background --python build_all.py -- --only chassis modules
    blender --background --python build_all.py -- --out ../../assets/out --no-render

注意: Blender 一次只能加载一个 .blend 场景，所以这里用「重新执行子进程」的方式
串联各个脚本，而不是在同一个进程里 import 它们 —— 后者会互相污染场景。
"""

import os
import subprocess
import sys
import time

import bpy


SCRIPTS = [
    # (键, 脚本, 说明, 额外参数)
    # 额外参数必须显式传 —— build_chassis.py 默认只建 medium，
    # 不传 --chassis all 的话另外两个机型不会被重建，而旧文件会留在原地，
    # 造成"看起来重建成功、实际用的是旧资产"的隐蔽问题。
    ("chassis", "build_chassis.py", "玩家机体（3 种，带骨骼 / UV / LOD）",
     ["--chassis", "all"]),
    ("modules", "build_modules.py", "模块库（22 个可换装模块）", []),
    ("enemies", "build_enemies.py", "敌人（6 种，含具名单位与巨像）", []),
    ("props", "build_props.py", "道具 / 环境构件 / 移动基地", []),
]


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    out_dir, no_render, only = None, False, None
    i = 0
    while i < len(argv):
        if argv[i] == "--out" and i + 1 < len(argv):
            out_dir = argv[i + 1]; i += 2
        elif argv[i] == "--no-render":
            no_render = True; i += 1
        elif argv[i] == "--only":
            only = []
            i += 1
            while i < len(argv) and not argv[i].startswith("--"):
                only.append(argv[i]); i += 1
        else:
            i += 1

    here = os.path.dirname(os.path.abspath(__file__))
    if out_dir is None:
        out_dir = os.path.join(here, "..", "..", "assets", "out")
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    blender = bpy.app.binary_path
    if not blender or not os.path.exists(blender):
        # 兜底：binary_path 在某些嵌入场景下可能为空
        blender = sys.executable
    print("Blender : %s" % blender)
    print("输出目录 : %s" % out_dir)
    print("")

    targets = [s for s in SCRIPTS if (only is None or s[0] in only)]
    t0 = time.time()
    results = []

    for key, script, desc, extra in targets:
        path = os.path.join(here, script)
        if not os.path.exists(path):
            print("[skip] 找不到 %s" % script)
            continue
        print("=" * 60)
        print(">>> %s  —— %s" % (key, desc))
        print("=" * 60)
        cmd = [blender, "--background", "--python", path, "--", "--out", out_dir]
        if no_render:
            cmd.append("--no-render")
        cmd.extend(extra)
        t1 = time.time()
        proc = subprocess.run(cmd, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)
        dt = time.time() - t1
        ok = proc.returncode == 0
        text = proc.stdout.decode("utf-8", errors="replace")
        # 只回显关键行，避免刷屏
        for line in text.splitlines():
            s = line.strip()
            if (s.startswith("[ok]") or s.startswith("[FAIL]")
                    or s.startswith("[warn]") or s.startswith("完成")
                    or "Traceback" in s or "Error" in s):
                print("    " + s)
        results.append((key, ok, dt))
        print("    -> %s  (%.1fs)\n" % ("OK" if ok else "FAILED", dt))

    print("=" * 60)
    print("汇总")
    print("=" * 60)
    for key, ok, dt in results:
        print("  %-10s %-8s %6.1fs" % (key, "OK" if ok else "FAIL", dt))
    print("  总计 %.1fs" % (time.time() - t0))

    # 统计产出
    files = sorted(os.listdir(out_dir))
    counts = {}
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        counts[ext] = counts.get(ext, 0) + 1
    print("\n产出文件: %s" % ", ".join("%s x%d" % (e, n)
                                        for e, n in sorted(counts.items())))


if __name__ == "__main__":
    main()
