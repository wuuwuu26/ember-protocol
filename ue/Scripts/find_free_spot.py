"""找一块空地：检查候选点附近 250cm 内没有 StaticMeshActor。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ELL = unreal.EditorLevelLibrary
ELL.load_level(LEVEL)

cands = [(0, 900), (0, 1100), (-600, 900), (300, 1100), (900, 1100), (-600, 1100)]
obstacles = []
for a in ELL.get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    loc = a.get_actor_location()
    obstacles.append((loc.x, loc.y))

for cx, cy in cands:
    near = [(x, y) for x, y in obstacles if abs(x - cx) < 250 and abs(y - cy) < 250]
    print("[free] (%d,%d) 附近障碍=%d" % (cx, cy, len(near)))
print("FREE_SPOT_OK")
