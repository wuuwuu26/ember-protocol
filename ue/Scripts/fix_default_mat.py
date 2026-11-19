# -*- coding: utf-8 -*-
"""把还在用引擎默认 BasicShapeMaterial 的构件换成项目材质。"""
import unreal
L = "[默认材质]"
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")

steel = unreal.EditorAssetLibrary.load_asset(
    "/Game/RobotGame/Art/Environment/M_Steel")
light = unreal.EditorAssetLibrary.load_asset(
    "/Game/RobotGame/Art/Environment/M_SteelLight")
if not steel:
    unreal.log("%s ❌ 找不到 M_Steel" % L)
else:
    n = 0
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if a.get_class().get_name() != "StaticMeshActor":
            continue
        c = a.static_mesh_component
        try:
            mesh = c.get_editor_property("static_mesh")
        except Exception:
            continue
        try:
            nslots = max(1, len(mesh.get_editor_property("static_materials")))
        except Exception:
            nslots = 1
        for i in range(nslots):
            try:
                m = c.get_material(i)
            except Exception:
                m = None
            nm = m.get_name() if m else ""
            if nm in ("BasicShapeMaterial", "WorldGridMaterial", "DefaultMaterial"):
                # 面积大且低的当"地面"用混凝土钢，其余用涂装钢板
                b = a.get_actor_bounds(False)
                use = steel if b[1].z < 60 else light
                c.set_material(i, use)
                n += 1
                unreal.log("%s 替换 %s 槽%d → %s" % (L, a.get_actor_label(), i, use.get_name()))
    unreal.EditorLevelLibrary.save_current_level()
    unreal.log("%s 共替换 %d 个槽" % (L, n))
