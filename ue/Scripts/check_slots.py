import unreal

EAL = unreal.EditorAssetLibrary
CODES = ("Gardener", "Weather", "Guard", "Hauler", "Colossus")
lines = []
for c in CODES:
    p = "/Game/RobotGame/Art/Characters/SK_Enemy_%s" % c
    m = EAL.load_asset(p)
    if not m:
        lines.append("%s MISSING" % p)
        continue
    mats = []
    for i in range(len(m.get_editor_property("materials"))):
        slot = m.get_editor_property("materials")[i]
        try:
            nm = slot.get_editor_property("material_interface").get_name()
        except Exception:
            nm = "?"
        mats.append(nm)
    lines.append("SK_Enemy_%s slots=%d : %s" % (c, len(mats), ",".join(mats)))
open(r"C:\Users\25227\AppData\Local\Temp\opencode\slots.txt", "w", encoding="utf-8").write("\n".join(lines))
unreal.log("SLOTS_OK")
