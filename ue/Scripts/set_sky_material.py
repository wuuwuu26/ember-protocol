# -*- coding: utf-8 -*-
"""给天空穹顶材质打上 IsSky 标记。"""
import unreal

MAT_PATH = "/Game/RobotGame/Art/Materials/M_SkyDome"
LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
mat = unreal.EditorAssetLibrary.load_asset(MAT_PATH)
unreal.log("[IsSky] 材质=%s" % (mat.get_name() if mat else "None"))
if not mat:
    raise SystemExit(1)

candidates = ("is_sky", "b_is_sky", "bIsSky", "b_used_with_sky", "used_with_sky")
for name in candidates:
    try:
        mat.set_editor_property(name, True)
        unreal.log("[IsSky] 设置成功: %s" % name)
    except Exception as e:
        unreal.log("[IsSky] 设置失败: %s -> %s" % (name, str(e)[:100]))
for name in candidates:
    try:
        unreal.log("[IsSky] 回读 %s = %s" % (name, mat.get_editor_property(name)))
    except Exception:
        pass

unreal.EditorAssetLibrary.save_loaded_asset(mat)
unreal.log("[IsSky] 材质已保存")

unreal.EditorLevelLibrary.load_level(LEVEL)
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() == "SkyLight":
        c = None
        for p in ("sky_light_component", "light_component"):
            try:
                c = a.get_editor_property(p)
                if c:
                    break
            except Exception:
                pass
        if c:
            c.set_editor_property("real_time_capture", True)
            c.recapture_sky()
            unreal.log("[IsSky] 天光已重捕获")
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_all_dirty_levels()
unreal.log("[IsSky] 完成")