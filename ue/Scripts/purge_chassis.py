# -*- coding: utf-8 -*-
"""彻底删掉三台机体的网格与骨架，然后由 reimport_rigged 全新导入。

不这样做的话，残留的 Skeleton 资产会让重导入出来的网格 skeleton 引用为空
（运行时报 "missing skeleton" 崩溃）。
"""
import unreal
L = "[清理机体]"
sub = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
names = []
for code in ("Light", "Medium", "Heavy"):
    names += ["SK_Chassis_%s" % code]
for code in ("light", "medium", "heavy"):
    names += ["chassis_%s_Skeleton" % code,
              "SK_Chassis_%s_Skeleton" % code]
n = 0
for nm in names:
    p = "/Game/RobotGame/Art/Characters/%s" % nm
    if unreal.EditorAssetLibrary.does_asset_exist(p):
        sub.delete_asset(p)
        n += 1
        unreal.log("%s 删除 %s" % (L, nm))
unreal.log("%s 共删除 %d 个" % (L, n))
