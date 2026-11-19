#!/usr/bin/env bash
# 在编辑器里跑一个 Python 脚本，**带自动重试**。
#
# 为什么需要重试：`-ExecutePythonScript` 是挂在
#   FEditorDelegates::PostLoadingStartupAssets 上的，而 `-unattended` 会在
#   启动流程结束后立刻 QUIT_EDITOR。两者偶尔会撞车 —— 编辑器先退出，
#   脚本一次都没跑，日志里干干净净、退出码还是 0。
#   这个"静默不执行"极难和"脚本自己没输出"区分开，所以这里统一：
#     跑 → 在日志里找脚本自己打的标记 → 找不到就重跑（最多 3 次）。
#
# 用法:  bash tools/ue_py.sh <脚本路径> <日志标记关键词> [超时秒]
#
# 约定：脚本必须用 unreal.log 打一行含 <标记关键词> 的日志，
#       否则无法判断它到底跑没跑。

set -u

UE_ROOT="${UE_ROOT:-/c/Program Files/Epic Games/UE_5.8}"
PROJ="${PROJ:-/c/Users/25227/Documents/robot_game/ue}"
EDITOR="$UE_ROOT/Engine/Binaries/Win64/UnrealEditor-Cmd.exe"
UPROJECT="C:/Users/25227/Documents/robot_game/ue/RobotGame.uproject"

SCRIPT="${1:?需要脚本路径}"
MARKER="${2:?需要日志标记关键词}"
TRIES="${3:-3}"

# ⚠️ 路径必须转成**绝对**的 Windows 路径。
#    编辑器会把 -ExecutePythonScript 的相对路径按它自己的工作目录展开
#    （引擎的 Binaries/Win64），于是变成
#    "C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/ue/Scripts/xxx.py"
#    —— 报 "Could not load Python file"，而且退出码依然是 0。
SCRIPT_ABS=$(cd "$(dirname "$SCRIPT")" && pwd)/$(basename "$SCRIPT")
SCRIPT_WIN=$(cygpath -m "$SCRIPT_ABS")

for i in $(seq 1 "$TRIES"); do
  LOG="$PROJ/ue_py_$i.log"
  rm -f "$LOG"
  LOG_WIN=$(cygpath -m "$LOG")

  # 上一轮残留的编辑器会锁住 DLL / 资产，先清干净
  "$EDITOR" "$UPROJECT" \
    -unattended -nopause -nosplash -DDC-ForceMemoryCache \
    -abslog="$LOG_WIN" \
    -ExecutePythonScript="$SCRIPT_WIN" >/dev/null 2>&1

  if grep -aq "$MARKER" "$LOG" 2>/dev/null; then
    echo "[ue_py] 第 $i 次执行成功（标记 '$MARKER' 已出现）"
    grep -a "$MARKER" "$LOG" | sed 's/.*LogPython: //'
    exit 0
  fi

  echo "[ue_py] 第 $i 次没有产出标记 '$MARKER'，重试……"
done

echo "[ue_py] ❌ $TRIES 次都没跑起来。最后一次日志：$PROJ/ue_py_$TRIES.log"
grep -a -i "LogPython\|error" "$PROJ/ue_py_$TRIES.log" | tail -10
exit 1
