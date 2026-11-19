"""
让编辑器视口截一张图（简单版，不阻塞游戏线程）
================================================================
在编辑器 Output Log 的 Cmd 输入框执行：
    py exec(open(r'C:/Users/25227/Documents/robot_game/ue/Scripts/editor_shot.py').read())

⚠️ 不要在脚本里用 time.sleep —— 它会阻塞游戏线程，
   视口不渲染，截出来的图就是过期的/黑的。

正确用法：在编辑器界面上手动切换视口的显示模式，
每切一次跑一次这个脚本。

截图存到 Saved/Screenshots/WindowsEditor/。
"""

import os
import unreal


def log(m):
    unreal.log("[截图] %s" % m)
    print("[截图] %s" % m)


def main():
    d = "C:/Users/25227/Documents/robot_game/ue/Saved/Screenshots/WindowsEditor"
    before = set()
    if os.path.isdir(d):
        before = set(f for f in os.listdir(d) if f.lower().endswith(".png"))

    # 触发截图（异步，不阻塞）
    unreal.SystemLibrary.execute_console_command(None, "HighResShot 1280x720")
    log("已触发 HighResShot 1280x720")
    log("已有截图 %d 张，稍后自动生成新的一张" % len(before))
    log("提示：如果没生成，等一两秒再跑一次这个脚本")


main()
