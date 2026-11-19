# -*- coding: utf-8 -*-
"""系统测试 UE5.8 Python 创建可用 NiagaraSystem 的所有路径（第一百一十五轮）。

目标：找到一条能 "创建 -> 落盘 -> 重新加载仍有效" 的自动化路径。
方法：
  A) AssetTools.create_asset + NiagaraSystemFactoryNew（空系统）
  B) duplicate_asset 引擎模板 + 显式 save_loaded_asset
  C) duplicate_asset 后 save_directory
  D) NiagaraClipboardEditorScriptingUtilities（官方脚本化）
  E) 检查 NiagaraSystemFactoryNew 能否指定 emitter 模板
"""
import unreal
import os

EAL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
out = []

DIR = "/Game/RobotGame/FX"
DISK = r"C:\Users\25227\Documents\robot_game\ue\Content\RobotGame\FX"
if not EAL.does_directory_exist(DIR):
    EAL.make_directory(DIR)


def report(tag, path):
    """验证资产是否真正落盘且可重新加载。"""
    disk = os.path.join(DISK, path.split("/")[-1] + ".uasset")
    exists_disk = os.path.exists(disk)
    size = os.path.getsize(disk) if exists_disk else -1
    # 强制重新加载
    reloaded = EAL.load_asset(path)
    valid = reloaded is not None
    out.append("  [%s] disk=%s(%s B)  reload=%s  class=%s" % (
        tag, exists_disk, size, valid,
        reloaded.get_class().get_name() if reloaded else "None"))
    return exists_disk and valid


# ── A) 空系统工厂 ──
out.append("=== A) NiagaraSystemFactoryNew 空系统 ===")
try:
    p = DIR + "/NS_TestA"
    if EAL.does_asset_exist(p):
        EAL.delete_asset(p)
    fac = unreal.NiagaraSystemFactoryNew()
    a = AT.create_asset("NS_TestA", DIR, unreal.NiagaraSystem, fac)
    out.append("  create_asset -> %s" % (a.get_name() if a else "None"))
    if a:
        EAL.save_loaded_asset(a)
    report("A", p)
except Exception as e:
    out.append("  !! %s: %s" % (type(e).__name__, str(e)[:120]))

# ── B) 复制引擎模板 + 显式保存 ──
out.append("")
out.append("=== B) duplicate FountainLightweight + save_loaded_asset ===")
try:
    SRC = "/Niagara/DefaultAssets/Templates/Systems/FountainLightweight.FountainLightweight"
    p = DIR + "/NS_TestB"
    if EAL.does_asset_exist(p):
        EAL.delete_asset(p)
    dup = EAL.duplicate_asset(SRC, p)
    out.append("  duplicate -> %s" % (dup.get_name() if dup else "None"))
    if dup:
        ok = EAL.save_loaded_asset(dup)
        out.append("  save_loaded_asset -> %s" % ok)
    report("B", p)
except Exception as e:
    out.append("  !! %s: %s" % (type(e).__name__, str(e)[:120]))

# ── C) 复制后 save_directory ──
out.append("")
out.append("=== C) duplicate + save_directory ===")
try:
    SRC = "/Niagara/DefaultAssets/Templates/Systems/FountainLightweight.FountainLightweight"
    p = DIR + "/NS_TestC"
    if EAL.does_asset_exist(p):
        EAL.delete_asset(p)
    dup = EAL.duplicate_asset(SRC, p)
    EAL.save_directory(DIR, only_if_is_dirty=False, recursive=True)
    out.append("  save_directory done")
    report("C", p)
except Exception as e:
    out.append("  !! %s: %s" % (type(e).__name__, str(e)[:120]))

# ── D) 官方脚本化工具 ──
out.append("")
out.append("=== D) NiagaraClipboardEditorScriptingUtilities ===")
try:
    lib = unreal.NiagaraClipboardEditorScriptingUtilities
    out.append("  方法: %s" % [n for n in dir(lib) if not n.startswith("_")][:20])
except Exception as e:
    out.append("  !! %s" % str(e)[:80])

# ── E) 工厂是否有可设置的模板属性 ──
out.append("")
out.append("=== E) NiagaraSystemFactoryNew 属性 ===")
try:
    fac = unreal.NiagaraSystemFactoryNew()
    for n in dir(fac):
        if not n.startswith("_") and not callable(getattr(fac, n, None)):
            try:
                out.append("  %-36s = %s" % (n, fac.get_editor_property(n)))
            except Exception:
                out.append("  %-36s (读不了)" % n)
except Exception as e:
    out.append("  !! %s" % str(e)[:80])

# ── F) NiagaraSystem 的可编辑属性 ──
out.append("")
out.append("=== F) NiagaraSystem 实例属性（找 emitter/参数）===")
try:
    sysm = EAL.load_asset(DIR + "/NS_TestB") or EAL.load_asset(
        "/Niagara/DefaultAssets/Templates/Systems/FountainLightweight.FountainLightweight")
    for n in dir(sysm):
        if any(k in n.lower() for k in ("emitter", "expose", "param", "script", "compile")):
            out.append("  " + n)
except Exception as e:
    out.append("  !! %s" % str(e)[:80])

# 列出磁盘
out.append("")
out.append("=== 磁盘 FX 目录 ===")
if os.path.isdir(DISK):
    for f in sorted(os.listdir(DISK)):
        out.append("  %s  %d B" % (f, os.path.getsize(os.path.join(DISK, f))))

with open(r"C:\Users\25227\Documents\robot_game\docs\niagara_methods.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("NIAGARA_METHODS_DONE")
