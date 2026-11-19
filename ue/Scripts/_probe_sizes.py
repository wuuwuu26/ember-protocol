import unreal

def L(s):
    print("[尺寸] %s" % s)

ENV = "/Game/RobotGame/Art/Environment"
PROPS = "/Game/RobotGame/Art/Props"
LAND = "/Game/RobotGame/Art/Environment"

def dump(path, label):
    m = unreal.EditorAssetLibrary.load_asset(path)
    if not m:
        L("  %-26s ❌ 不存在" % label)
        return
    try:
        b = m.get_bounds()
        o = b.origin
        e = b.box_extent
        L("  %-26s 尺寸=(%d, %d, %d)  原点z=%d  底z=%d" % (
            label, round(e.x*2), round(e.y*2), round(e.z*2),
            round(o.z), round(o.z - e.z)))
    except Exception as ex:
        L("  %-26s 读取失败: %s" % (label, str(ex)[:50]))

L("========== 环境构件 ==========")
for n in ("Floor", "Platform", "Catwalk", "Gantry", "Pillar", "Wall",
          "Stairs", "Piperun", "Doorframe"):
    dump("%s/SM_Env_%s" % (ENV, n), "SM_Env_" + n)
dump("%s/SM_Landmark_Lighthouse" % LAND, "SM_Landmark_Lighthouse")

L("========== 道具 ==========")
for n in ("Container", "Shelf", "Beacon", "Crate", "FuelBarrel", "Terminal",
          "Debris", "SalvagePod", "SupplyBox", "PipeSegment", "ScrapCrate"):
    dump("%s/SM_Prop_%s" % (PROPS, n), "SM_Prop_" + n)

L("========== 当前关卡布局 ==========")
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    cn = a.get_class().get_name()
    if cn in ("PlayerStart", "RobotEnemy", "DirectionalLight", "SkyLight"):
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        L("  %-16s @ (%.0f, %.0f, %.0f) yaw=%.0f" % (cn, loc.x, loc.y, loc.z, rot.yaw))
