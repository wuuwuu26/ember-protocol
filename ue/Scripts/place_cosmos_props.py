# -*- coding: utf-8 -*-
"""把 12 个 Cosmos 工业道具摆进新战斗区域（第一百零四轮）。

布局原则（新区域 X 2400..5400, Y ±900）：
  - 龙门架在 x=3200/4400、y=0；雕像在 x=4750、y=0 —— 中轴要留空
  - 掩体错落放在中前段两侧（x 2600..4200, |y| 350..700），
    形成"进门 → 掩体交错 → 雕像"的战斗动线，两两之间留 ≥200cm 通道
  - 贴墙件（壁灯/风扇/管道/灭火器）挂南北墙 y≈±860 或立柱旁
  - 街灯做垂直焦点，放在掩体群外侧

⚠️ 关键：这些 glTF 网格**脚底已对齐 z=0**（导入诊断 minZ=0.00），
   所以 actor Z 直接用地面顶面高度 0 即可，不用像 IdolMech 那样补半高。
⚠️ 材质由导入器自动生成，不需要手动 override。
⚠️ 全部打 CosmosProp tag，幂等可重跑。

坐标是"中心"，尺寸来自导入诊断 bbox（cm）。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
BASE = "/Game/RobotGame/Art/Props/Cosmos"
TAG = "CosmosProp"
REPORT = r"C:\Users\25227\Documents\robot_game\docs\cosmos_place.txt"

EAL = unreal.EditorAssetLibrary
lines = []


def log(s):
    unreal.log("[CosmosPlace] %s" % s)
    lines.append(str(s))


def mesh(slug):
    return EAL.load_asset("%s/%s/SM_%s" % (BASE, slug, slug))


# ────────────────────────────────────────────────────────────
# 布局（第一百零九轮第三版：消穿模）
#
# 前两版问题：
#   1. 掩体偏小偏散（v1）→ 木箱叠放、沙袋成组（v2）
#   2. 贴墙件夹在墙/立柱缝里看不见（v1）→ 挂到立柱空档（v2）
#   3. 第一百零九轮诊断出 5 对包围盒真穿模（v2）：
#        沙袋 A1×A2 / B1×B2 各自几乎完全重叠（中心仅差 130/40cm）
#        沙袋 A2 × 街灯 A、栅栏 B × 火炉 B、栅栏 B × 灭火器 B 边缘互蹭
#      修法：同组沙袋沿 X 拉开 ≥420cm；街灯外移；把栅栏 B 与右侧
#        火炉/灭火器错开 x。
#   - 冰柜偏白，作为每侧一个"亮色锚点"刻意保留，形成节奏
# ────────────────────────────────────────────────────────────
LAYOUT = [
    # ── 左侧掩体群（y 负方向）──
    # 沙袋两条 157×375，沿 X 拉开 460cm，不再重叠
    ("ww2-sandbag-stack-02b-smoked", 2620, -560, 0, 10, 1.0, "沙袋掩体 A1"),
    ("ww2-sandbag-stack-02b-smoked", 3080, -560, 0, -15, 1.0, "沙袋掩体 A2"),
    ("met-barrel01-set01",           3400, -640, 0, 25, 1.2, "油桶组 A"),
    ("ww2-fridge",                   2680, -300, 0, 90, 1.0, "旧冰柜 A（亮色锚点）"),
    ("met-wooden-crate01a",          3250, -390, 0, 15, 3.0, "木箱堆 A-底"),
    ("met-wooden-crate01a",          3250, -390, 63, 35, 3.0, "木箱堆 A-中"),
    ("met-wooden-crate01a",          3270, -380, 126, 10, 2.4, "木箱堆 A-顶"),
    ("ww2-drawer-smoked",            3700, -600, 0, 90, 1.1, "抽屉柜 A"),
    ("ww2-field-fences-01a",        4050, -560, 0, 0, 1.0, "野战栅栏 A"),

    # ── 右侧掩体群（y 正方向）──
    # 沙袋两条沿 X 拉开，且整组比左侧前移，避免与后面贴墙件挤在一起
    ("ww2-sandbag-stack-02b-smoked", 2620,  560, 0, 170, 1.0, "沙袋掩体 B1"),
    ("ww2-sandbag-stack-02b-smoked", 3080,  560, 0, 195, 1.0, "沙袋掩体 B2"),
    ("met-barrel01-set01",           3400,  640, 0, -20, 1.2, "油桶组 B"),
    ("ww2-fridge",                   2680,  340, 0, -90, 1.0, "旧冰柜 B（亮色锚点）"),
    # 木箱 B 组沿 +X 挪到 3500：第一百零九轮诊断里 3250 时与沙袋 B2(3080,560)
    # 边缘互蹭（重叠 X64 Y155）—— 拉开后两者 X 差 420，彻底分开。
    ("met-wooden-crate01a",          3500,  400, 0, 40, 3.0, "木箱堆 B-底"),
    ("met-wooden-crate01a",          3500,  400, 63, 55, 3.0, "木箱堆 B-中"),
    ("met-wooden-crate01a",          3520,  390, 126, 30, 2.4, "木箱堆 B-顶"),
    ("ww2-drawer-smoked",            3700,  600, 0, -90, 1.1, "抽屉柜 B"),
    # 栅栏 B 往前挪到 x=3850，避开 x=4300 的火炉/灭火器
    ("ww2-field-fences-01a",        3850,  560, 0, 90, 1.0, "野战栅栏 B"),

    # ── 街灯：外移出沙袋/掩体包围盒，做两侧照明/视觉焦点 ──
    ("pad-street-lamp-overgrown",    2450, -780, 0, -20, 1.0, "街灯 A"),
    ("pad-street-lamp-overgrown",    4150,  780, 0, 160, 1.0, "街灯 B"),

    # ── 贴墙工业件：挂到立柱之间的空档（从中央可见）──
    ("cs1-wallfanhatch",            3100, -790, 230, 0, 1.0, "墙面风扇格栅"),
    ("cs1-wall-light-6",            3700, -790, 250, 0, 1.0, "壁灯 A"),
    ("cs1-wall-light-6",            3700,  790, 250, 180, 1.0, "壁灯 B"),
    ("cs1-wall-light-6",            4500, -790, 250, 0, 1.0, "壁灯 C"),
    ("ww2-heater-smoked",           2650, -760, 0, 0, 1.0, "火炉 A（墙角）"),
    ("ww2-heater-smoked",           4300,  760, 0, 180, 1.0, "火炉 B（墙角）"),
    ("rps-fire-extinguisher-02",    3100, -780, 0, 0, 1.3, "灭火器 A"),
    ("rps-fire-extinguisher-02",    4500,  780, 0, 180, 1.3, "灭火器 B"),

    # ── 管道小装饰（贴立柱脚，成组放大）──
    ("cs1-pipe",                    3400, -790, 20, 0, 3.0, "管道 A"),
    ("cs1-pipe",                    3400,  790, 20, 0, 3.0, "管道 B"),
    ("cs1-pipe",                    4600, -790, 20, 0, 3.0, "管道 C"),
]


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level(LEVEL)
    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    # 幂等：清理旧的 Cosmos 道具
    killed = 0
    for a in list(actor_sub.get_all_level_actors()):
        try:
            tags = [str(t) for t in a.get_editor_property("tags")]
        except Exception:
            continue
        if TAG in tags:
            actor_sub.destroy_actor(a)
            killed += 1
    log("清理旧道具 %d 个" % killed)

    placed = 0
    missing = []
    for (slug, x, y, z, yaw, scale, desc) in LAYOUT:
        m = mesh(slug)
        if not m:
            missing.append(slug)
            continue
        a = actor_sub.spawn_actor_from_class(
            unreal.StaticMeshActor,
            unreal.Vector(float(x), float(y), float(z)),
            unreal.Rotator(roll=0.0, pitch=0.0, yaw=float(yaw)))
        if not a:
            log("!! spawn 失败 %s" % desc)
            continue
        c = a.static_mesh_component
        c.set_mobility(unreal.ComponentMobility.MOVABLE)  # 未烘焙光照，必须 Movable
        c.set_static_mesh(m)
        a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
        a.set_editor_property("tags", [TAG, slug])
        a.set_actor_label(desc)
        placed += 1

    log("摆放 %d 个道具；缺失资产 %s" % (placed, missing))
    les.save_current_level()
    log("已保存关卡")
    with open(REPORT, "wb") as f:
        f.write("\n".join(lines).encode("utf-8"))
    unreal.log("COSMOS_PLACE_DONE")


main()
