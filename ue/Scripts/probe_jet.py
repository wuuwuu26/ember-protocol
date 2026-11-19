"""诊断冷却液供水构件：水柱/立管/横臂/竖管的位置与材质。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ELL = unreal.EditorLevelLibrary
ELL.load_level(LEVEL)

for a in ELL.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl.startswith(("Jet_", "Pipe_", "Inlet_")) and "Coolant" in lbl:
        loc = a.get_actor_location()
        sc = a.get_actor_scale3d()
        comp = a.get_component_by_class(unreal.StaticMeshComponent)
        mat = comp.get_material(0) if comp else None
        print("[jet] %-26s loc=(%.0f,%.0f,%.0f) scale=(%.2f,%.2f,%.2f) mat=%s"
              % (lbl, loc.x, loc.y, loc.z, sc.x, sc.y, sc.z,
                 mat.get_name() if mat else "None"))
print("JET_PROBE_OK")
