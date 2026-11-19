# -*- coding: utf-8 -*-
"""诊断：确认冷却液场景（池体 / 断管 / 两盏冷光）仍在 L_TestArena 里，并打印位置。"""
import unreal

MAP = "/Game/RobotGame/Maps/Persistent/L_TestArena"
sub = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
sub.load_level(MAP)

rows = []
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    cn = a.get_class().get_name()
    label = a.get_actor_label()
    if cn in ("RobotCoolantField", "RobotHazardSludge") or label.startswith("Coolant"):
        loc = a.get_actor_location()
        sc = a.get_actor_scale3d()
        rows.append(f"{cn} | {label} | ({loc.x:.0f},{loc.y:.0f},{loc.z:.0f}) | scale {sc.x:.2f}")

unreal.log(f"DIAG_COUNT {len(rows)}")
for r in rows:
    unreal.log(f"DIAG {r}")

with open(r"C:\Users\25227\Documents\robot_game\docs\diag_coolant.txt", "w", encoding="utf-8") as f:
    f.write(f"DIAG_COUNT {len(rows)}\n" + "\n".join(rows) + "\n")
unreal.log("DIAG_OK")
