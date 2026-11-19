"""把躺在水渠占地里的道具挪走：渠是液体容器，里面不能泡着油桶。

水渠占地（world）：x 42..858 / y 172..428。只挪"不该泡在水里"的道具
（油桶/箱子/残骸），池壁、水管、水柱、灯光、场本身不动。
"""
import unreal

ELL = unreal.EditorLevelLibrary

X0, X1 = 20.0, 880.0
Y0, Y1 = 150.0, 450.0
MOVE_LABELS = {"ExplosiveBarrel_3": (980.0, 520.0)}

moved = 0
for a in ELL.get_all_level_actors():
    label = a.get_actor_label()
    if label not in MOVE_LABELS:
        continue
    loc = a.get_actor_location()
    if not (X0 <= loc.x <= X1 and Y0 <= loc.y <= Y1):
        continue
    tx, ty = MOVE_LABELS[label]
    a.set_actor_location(unreal.Vector(tx, ty, loc.z), False, False)
    moved += 1
    unreal.log("[渠清] %s (%.0f,%.0f) -> (%.0f,%.0f)"
               % (label, loc.x, loc.y, tx, ty))

# ⚠️ 必须存关卡：ue_py 每次是独立编辑器实例，不存盘移动就随进程一起丢
# （r71 实测：moved=1 但截图里桶还在渠里）。
if moved:
    ELL.save_current_level()

unreal.log("CHANNEL_CLEAR moved=%d" % moved)
