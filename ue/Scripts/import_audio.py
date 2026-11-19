# -*- coding: utf-8 -*-
"""
导入程序化音效（tools/make_sfx.py 生成的 WAV）到 UE。
================================================================

为什么单独写导入而不是走 FBX 管线：WAV 是引擎一等公民，
AssetImportTask 的 automated 模式会直接落到 SoundWave 工厂，不需要指定。

命名：小写下划线（sfx_fire_player.wav）→ PascalCase（SFX_Fire_Player）。
命名规则不重要，重要的是**所有 C++ 引用点和这里保持一字不差** ——
C++ 侧在 Private/RobotSfx.h 里按 "/Game/RobotGame/Audio/<名>.<名>" 加载，
改名字要两边一起改。

用法: bash tools/ue_py.sh ue/Scripts/import_audio.py "音效导入"
"""
import os
import unreal

SRC = r"C:\Users\25227\Documents\robot_game\assets\audio"
DEST = "/Game/RobotGame/Audio"

# 文件名 → 资产名
FILES = {
    "sfx_fire_player.wav": "SFX_Fire_Player",
    "sfx_fire_enemy.wav": "SFX_Fire_Enemy",
    "sfx_impact.wav": "SFX_Impact",
    "sfx_destroy.wav": "SFX_Destroy",
    "sfx_dash.wav": "SFX_Dash",
    "sfx_overheat.wav": "SFX_Overheat",
    "sfx_pickup.wav": "SFX_Pickup",
    "sfx_ui_click.wav": "SFX_UI_Click",
}

unreal.log("[音效导入] 开始")


def log(m):
    unreal.log("[音效导入] %s" % m)


tools = unreal.AssetToolsHelpers.get_asset_tools()
ok = fail = 0
for fname, asset_name in FILES.items():
    path = os.path.join(SRC, fname)
    if not os.path.exists(path):
        log("❌ 源文件不存在：%s（先跑 tools/make_sfx.py）" % path)
        fail += 1
        continue

    task = unreal.AssetImportTask()
    task.filename = path
    task.destination_path = DEST
    task.destination_name = asset_name
    task.automated = True
    task.save = True
    task.replace_existing = True
    try:
        tools.import_asset_tasks([task])
    except Exception as e:
        log("❌ %s 导入异常: %s" % (fname, str(e)[:100]))
        fail += 1
        continue

    sw = unreal.EditorAssetLibrary.load_asset("%s/%s" % (DEST, asset_name))
    if sw:
        try:
            dur = sw.get_editor_property("duration")
        except Exception:
            dur = -1.0
        log("  [ok] %-22s 时长=%.2fs" % (asset_name, dur))
        ok += 1
    else:
        log("  [!!] %s 导入后读不到" % asset_name)
        fail += 1

log("完成：成功 %d 失败 %d" % (ok, fail))
unreal.EditorAssetLibrary.save_directory(DEST, only_if_is_dirty=False,
                                         recursive=True)
log("目录已保存 %s" % DEST)
