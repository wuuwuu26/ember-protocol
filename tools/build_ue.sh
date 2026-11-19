#!/usr/bin/env bash
# 手动编译 + 链接项目的三个模块（绕过坏掉的 UBA）
#
# 背景：本机 UBT 的 Unreal Build Accelerator 在执行
#   SetFileInformationByHandle(FileDispositionInfo) 时被系统拒绝
#   （C:\ProgramData\Epic\UnrealBuildAccelerator\memgroups → Access is denied），
#   导致所有源文件被标记为 "Exited with error code 1"（且没有任何错误信息）。
#   这是机器权限问题，不是代码问题。
#
# ⚠️ 为什么现在要按模块链重建（2026-10-14 修复）：
#   UBT 每次跑（Build.bat，用于重生成 UHT 反射代码）都会把**改过头文件的模块**
#   的导入库（.lib）删掉、等重编 —— 但编译阶段死在 UBA 上，.lib 就消失了。
#   于是 RobotGame 的链接报 LNK1181 找不到 UnrealEditor-RobotCore.lib。
#   解决：改成 Core → Combat → Game 的顺序全链路重建，任何模块的头文件
#   变更都能自愈，不再依赖 UBT 的中间产物是否完整。
#
# ⚠️ 手动编译**没有依赖追踪**：动了头文件必须全量重编，否则结构体布局
#    不一致 → 关卡加载时在引擎里崩（栈里看不到自己的模块，极难查）。
#    所以本脚本永远全量编译，不做增量。
#
# ⚠️ 新增 UPROPERTY / UFUNCTION 必须重跑 UHT。本脚本不跑 UHT ——
#    改反射声明请先跑一次 Build.bat（UHT 成功、编译失败即可），再跑本脚本。

set -u

UE_ROOT="${UE_ROOT:-/c/Program Files/Epic Games/UE_5.8}"
PROJ="${PROJ:-/c/Users/25227/Documents/robot_game/ue}"
MSVC_BIN="/c/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64"
CL="$MSVC_BIN/cl.exe"
LINK="$MSVC_BIN/link.exe"
LIB="$MSVC_BIN/lib.exe"
BUILD_ROOT="$PROJ/Intermediate/Build/Win64/x64/UnrealEditor/Development"

# 1) 编译前请确保 UnrealEditor 已退出 —— 它占着 DLL，链接会报 LNK1104。

# 2) 按依赖顺序编译 + 链接（Combat 需要 Core 的 lib，Game 需要两者的 lib）
#
# ⚠️ 工作目录必须是 Engine/Source —— rsp 里的相对路径（如 SharedPCH 头、
#    引擎模块的 .lib）是相对它展开的。
cd "$UE_ROOT/Engine/Source" || exit 1

for M in RobotCore RobotCombat RobotGame; do
  D="$BUILD_ROOT/$M"
  if [ ! -d "$D" ]; then
    echo "[错误] 找不到模块目录：$D"
    exit 1
  fi

  echo "===== 编译 $M ====="
  FAIL=0
  N=0
  for f in "$D"/*.cpp.obj.rsp; do
    N=$((N + 1))
    name=$(basename "$f" .obj.rsp)
    out=$("$CL" @"$f" 2>&1)
    if [ $? -ne 0 ]; then
      echo "  [失败] $name"
      echo "$out" | iconv -f GBK -t UTF-8 2>/dev/null \
        | grep -a -E "error C|error LNK|fatal error" | head -15 \
        || echo "$out" | grep -a -E "error C|error LNK|fatal error" | head -15
      FAIL=1
    else
      echo "  [ok]   $name"
    fi
  done
  echo "  $M 共 $N 个编译单元"
  if [ $FAIL -ne 0 ]; then
    echo "===== $M 编译失败，停止 ====="
    exit 1
  fi

  echo "===== 链接 $M ====="
  # 必须先删旧 pdb，否则 LNK1104
  rm -f "$PROJ/Binaries/Win64/UnrealEditor-$M.pdb"
  "$LINK" @"$D/UnrealEditor-$M.dll.rsp" 2>&1 \
    | iconv -f GBK -t UTF-8 2>/dev/null \
    | grep -a -iE "error|LNK" | head -10

  OUT_DLL="$PROJ/Binaries/Win64/UnrealEditor-$M.dll"
  if [ -f "$OUT_DLL" ]; then
    echo "  完成：$OUT_DLL"
  else
    echo "===== $M 链接失败 ====="
    exit 1
  fi

  # ⚠️ 导入库（.lib）不是 dll 链接的副产品 —— dll.rsp 里写着 /NOIMPLIB，
  #    UBT 用**独立的 lib 步骤**（lib.exe + .lib.rsp）生成它，
  #    供下游模块（Combat 依赖 Core、Game 依赖两者）链接时使用。
  #    漏掉这一步 → 下游报 LNK1181 找不到 UnrealEditor-RobotXXX.lib。
  echo "===== 生成 $M 导入库 ====="
  "$LIB" @"$D/UnrealEditor-$M.lib.rsp" >/dev/null 2>&1
  if [ -f "$D/UnrealEditor-$M.lib" ]; then
    echo "  完成：$D/UnrealEditor-$M.lib"
  else
    echo "===== $M 导入库生成失败 ====="
    exit 1
  fi
done

echo "===== 全部完成 ====="
ls -la "$PROJ/Binaries/Win64/"UnrealEditor-Robot*.dll
