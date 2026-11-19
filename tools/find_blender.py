# -*- coding: utf-8 -*-
"""定位可用的 Blender 可执行文件（供各工具脚本共用）。

优先级：
  1) 环境变量 ROBOT_BLENDER（显式指定，最高优先）
  2) C:\\AI\\Blender\\<版本>\\blender.exe（便携版解压位置，按版本号倒序）
  3) C:\\Program Files\\Blender Foundation\\Blender <版本>\\blender.exe（安装版，按版本倒序）

按"版本号从高到低"选，这样装了新版本会自动用新的；
旧版本保留作为回退，不会因为升级失败就找不到 Blender。

用法：
  from find_blender import find_blender
  exe = find_blender()
"""
import os
import re
import glob


def _ver_key(path):
    """从路径里抽 (major, minor, patch) 用于排序，越大越新。

    要能识别这些形式：
      C:\\AI\\Blender\\5.3\\blender-5.3.0-windows-x64\\blender.exe
      C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe
    优先取 "Blender <数字>.<数字>" 或 "Blender\\<数字>.<数字>"，
    再退回路径里任意 x.y.z 版本号。
    """
    # 形式一：Blender 后面跟版本号（空格/点/反斜杠/下划线均可）
    m = re.search(r"[Bb]lender[ ._\\/]+(\d+)\.(\d+)(?:\.(\d+))?", path)
    if not m:
        # 形式二：目录名 blender-5.3.0-... 里的版本号
        m = re.search(r"blender[ -](\d+)\.(\d+)(?:\.(\d+))?", path)
    if not m:
        # 形式三：路径中任意独立版本号段
        m = re.search(r"[\\/](\d+)\.(\d+)(?:\.(\d+))?[\\/]", path)
    if not m:
        return (0, 0, 0)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))


def find_blender():
    # 1) 环境变量
    env = os.environ.get("ROBOT_BLENDER")
    if env and os.path.isfile(env):
        return env

    candidates = []

    # 2) 便携版目录（C:\AI\Blender 下按版本分的子目录）
    portable = r"C:\AI\Blender"
    if os.path.isdir(portable):
        for p in glob.glob(os.path.join(portable, "**", "blender.exe"),
                           recursive=True):
            candidates.append(p)
        # 也可能直接解压在 C:\AI\Blender\blender.exe
        direct = os.path.join(portable, "blender.exe")
        if os.path.isfile(direct):
            candidates.append(direct)

    # 3) 安装版
    inst = r"C:\Program Files\Blender Foundation"
    if os.path.isdir(inst):
        for p in glob.glob(os.path.join(inst, "**", "blender.exe"),
                           recursive=True):
            candidates.append(p)

    # 去重 + 按版本倒序
    seen = set()
    uniq = []
    for p in candidates:
        rp = os.path.normcase(os.path.abspath(p))
        if rp not in seen:
            seen.add(rp)
            uniq.append(p)
    uniq.sort(key=lambda p: (_ver_key(p), p), reverse=True)

    if not uniq:
        raise FileNotFoundError("找不到 blender.exe（已查 C:\\AI\\Blender 与 "
                                "C:\\Program Files\\Blender Foundation）")
    return uniq[0]


if __name__ == "__main__":
    print(find_blender())
