# -*- coding: utf-8 -*-
"""探测玩家/敌人 PartMap 资产的实际规则值（失败路径没触发的排查）。"""
import unreal

unreal.log("[探针2] 开始")

for name in ("DA_PartMap_Player", "DA_PartMap_Enemy"):
    path = "/Game/RobotGame/Data/Enemies/%s" % name
    pm = unreal.EditorAssetLibrary.load_asset(path)
    if not pm:
        path = "/Game/RobotGame/Data/%s" % name
        pm = unreal.EditorAssetLibrary.load_asset(path)
    if not pm:
        unreal.log("[探针2] ❌ 读不到 %s（两个路径都试了）" % name)
        continue
    unreal.log("[探针2] %s @ %s" % (name, path))
    try:
        for r in pm.get_editor_property("rules"):
            tag = r.get_editor_property("part_tag")
            try:
                tag_s = str(tag.get_editor_property("tag_name"))
            except Exception:
                tag_s = str(tag)
            unreal.log("[探针2]   %-14s hp=%.0f kills=%s 前缀=%s" % (
                tag_s,
                r.get_editor_property("max_health"),
                r.get_editor_property("destruction_kills"),
                [str(p) for p in r.get_editor_property("bone_prefixes")]))
    except Exception as e:
        unreal.log("[探针2]   规则读取失败: %s" % str(e)[:80])

unreal.log("[探针2] 完成")
