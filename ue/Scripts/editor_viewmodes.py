"""
在编辑器里切换视口显示模式并各截一张图
================================================================
在编辑器 Output Log 的 Cmd 输入框执行：
    py exec(open(r'C:/Users/25227/Documents/robot_game/ue/Scripts/editor_viewmodes.py').read())

依次用 Unlit（无光照）和 Wireframe（线框）模式截图，
用于判断：
  Unlit 下能看到网格体 → 几何体管线正常，问题在光照计算
  Unlit 下也看不到     → 几何体根本没进渲染管线

截图存到 Saved/Screenshots/WindowsEditor/。
"""

import os
import time
import unreal


def log(m):
    unreal.log("[视口模式] %s" % m)
    print("[视口模式] %s" % m)


def cmd(c):
    try:
        unreal.SystemLibrary.execute_console_command(None, c)
        return True
    except Exception as e:
        log("  命令失败 %s: %s" % (c, str(e)[:50]))
        return False


def shot_dir():
    return "C:/Users/25227/Documents/robot_game/ue/Saved/Screenshots/WindowsEditor"


def list_shots():
    d = shot_dir()
    if not os.path.isdir(d):
        return []
    return sorted(os.path.join(d, f) for f in os.listdir(d)
                  if f.lower().endswith(".png"))


def main():
    log("=" * 50)

    before = set(list_shots())
    log("截图前已有 %d 张" % len(before))

    # ── 1. Unlit 无光照模式 ──
    log("切换到 Unlit 无光照模式……")
    cmd("viewmode unlit")
    time.sleep(1.5)
    cmd("HighResShot 1280x720")
    time.sleep(2.0)

    # ── 2. Wireframe 线框模式 ──
    log("切换到 Wireframe 线框模式……")
    cmd("viewmode wireframe")
    time.sleep(1.5)
    cmd("HighResShot 1280x720")
    time.sleep(2.0)

    # ── 3. 切回 Lit ──
    log("切回 Lit 光照模式")
    cmd("viewmode lit")
    time.sleep(1.0)

    # ── 报告新增的截图 ──
    after = list_shots()
    new = [p for p in after if p not in before]
    log("本次新增 %d 张截图：" % len(new))
    for p in new:
        log("  %s  (%d 字节)" % (os.path.basename(p), os.path.getsize(p)))

    log("=" * 50)
    log("完成")


main()
