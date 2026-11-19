"""读取 DA_PartMap_Enemy 里腿部规则的骨骼前缀，确认断腿时隐藏的是哪几根骨。"""
import unreal

EAL = unreal.EditorAssetLibrary
for path in ("/Game/RobotGame/Data/Enemies/DA_PartMap_Enemy",
             "/Game/RobotGame/Data/Enemies/DA_PartMap_Player"):
    pm = EAL.load_asset(path)
    print("[pm] asset =", path)
    rules = pm.get_editor_property("rules")
    print("[pm]   rules count =", len(rules))
    for r in rules:
        tag = r.get_editor_property("part_tag")
        prefixes = r.get_editor_property("bone_prefixes")
        print("[pm]   %-24s prefixes=%s" % (tag, [str(p) for p in prefixes]))
print("PARTMAP_OK")
