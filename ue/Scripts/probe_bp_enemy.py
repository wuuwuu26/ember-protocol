"""打开 BP_Enemy 蓝图，列出 SimpleConstructionScript 里的组件节点与网格资产。"""
import unreal

EAL = unreal.EditorAssetLibrary
bp = EAL.load_asset("/Game/RobotGame/Blueprints/BP_Enemy")
gen = unreal.load_class(None, "/Game/RobotGame/Blueprints/BP_Enemy.BP_Enemy_C")
cdo = unreal.get_default_object(gen)
print("[bp] cdo=%s" % cdo.get_name())
for c in cdo.get_components():
    mesh = ""
    for attr in ("static_mesh", "skeletal_mesh"):
        try:
            v = c.get_editor_property(attr)
            if v:
                mesh = v.get_path_name()
        except Exception:
            pass
    print("[bp]   %-30s %-26s %s" % (c.get_name(), c.get_class().get_name(), mesh))
print("BP_ENEMY_OK")
