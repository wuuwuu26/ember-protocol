# -*- coding: utf-8 -*-
import unreal

sm = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Environment/SM_Env_SludgePool")
if sm:
    box = sm.get_bounds()
    unreal.log(f"SM_Env_SludgePool Bounds: Origin={box.origin}, Extent={box.box_extent}, Radius={box.sphere_radius}")

actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
for a in actors:
    if "sludge" in a.get_actor_label().lower():
        loc = a.get_actor_location()
        scale = a.get_actor_scale3d()
        unreal.log(f"Actor {a.get_actor_label()}: loc={loc}, scale={scale}")

with open(r"C:\Users\25227\Documents\robot_game\docs\sludge_debug_size.txt", "w") as f:
    f.write("SLUDGE_SIZE_DONE\n")
