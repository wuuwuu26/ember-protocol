# -*- coding: utf-8 -*-
"""许可证整改：清理关卡里所有带 CosmosProp tag 的 actor（因其引用的
第三方商业模型要从仓库移除）。幂等：运行两次第二次删 0 个。

只删 actor，不删资产文件（资产文件用 git rm 单独删）。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ELL = unreal.EditorLevelLibrary
ELL.load_level(LEVEL)

removed = 0
survivors = []
for a in list(ELL.get_all_level_actors()):
    try:
        tags = [str(t) for t in a.get_editor_property("tags")]
    except Exception:
        tags = []
    if "CosmosProp" in tags:
        ELL.destroy_actor(a)
        removed += 1
    else:
        survivors.append(a.get_actor_label())

ELL.save_current_level()
with open(r"C:\Users\25227\Documents\robot_game\docs\cosmos_actor_cleanup.txt", "wb") as f:
    f.write(("删除 CosmosProp actor: %d\n" % removed).encode("utf-8"))
    f.write(("剩余 actor 总数: %d\n" % len(survivors)).encode("utf-8"))
unreal.log("COSMOS_ACTOR_CLEANUP_DONE removed=%d" % removed)
