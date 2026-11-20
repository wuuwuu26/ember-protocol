> Language: **English** | [简体中文](./首次导入步骤.md)
# First Asset Import

**Status: complete** (2026-10-08) ｜ 51/51 imported successfully ｜ orientation and size verified

---

## Automated Flow Already Done

Nothing needs to be clicked by hand. Everything is executed through the headless editor:

```bash
BL="/c/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe"
PROJ="C:/Users/25227/Documents/robot_game/ue/RobotGame.uproject"

# Create directories + import all FBX + create the default level
"$BL" "$PROJ" -unattended -nopause -nosplash \
  -ExecutePythonScript="C:/Users/25227/Documents/robot_game/ue/Scripts/setup_project.py" -log

# Verify size and orientation
"$BL" "$PROJ" -unattended -nopause -nosplash \
  -ExecutePythonScript="C:/Users/25227/Documents/robot_game/ue/Scripts/verify_import.py" -log
```

> **Note**: Python's `print` output goes into `Saved/Logs/RobotGame.log` (with the `LogPython:` prefix),
> **not to stdout**. To check the results: `grep "余火协议" Saved/Logs/RobotGame.log`.
>
> Also: in headless mode the editor automatically issues `QUIT_EDITOR` after the script finishes, so the script must complete synchronously.

## Import Results

| Category | Count | Location |
|---|---|---|
| Skeletal meshes | 54 | `Art/Characters/` (9 characters × body/LOD1/LOD2/skeleton) |
| Static meshes | 126 | `Art/Modules/` `Art/Environment/` `Art/Props/` |
| Default level | 1 | `Maps/Persistent/L_Persistent` |
| **Total uassets** | **238** | |

## Verification Results

### Size ✅

| Asset | UE measured X front-back | Y left-right | Z height | Verdict |
|---|---|---|---|---|
| `SK_Chassis_Light` | 1.076 | 1.435 | 2.637 | OK |
| `SK_Chassis_Medium` | 1.141 | 1.670 | 2.719 | see note below |
| `SK_Chassis_Heavy` | 1.441 | 1.976 | 2.480 | OK |
| `SM_Landmark_Lighthouse` | 20.800 | 16.540 | 21.000 | OK |

All static meshes match exactly.

### Orientation ✅

```
SM_Module_ArmCannon   origin=( 0.198, -0.012, 0.378)  OK  barrel faces forward
SM_Module_ArmMining   origin=( 0.115, -0.011, 0.378)  OK  drill faces forward
```

Both the barrel and the drill point toward **+X**, matching UE's "+X is forward" convention.

### Axis Mapping (After Correction)

```
Blender X (left-right width) → UE Y (left-right)
Blender Y (front-back depth) → UE X (front-back)
Blender Z (height)           → UE Z (height)
```

---

## ⚠️ Two Pitfalls You Must Know

### Pitfall 1: Orientation Was Off by 90° Once

**Symptom**: the size was exactly right, but the mech faced sideways in UE.

**Why it was hard to find**: bounding-box extents are always positive, so an axis flip isn't visible.
Just comparing "whether width and height are right" will never find this problem.

**Correct check method**: compare **Blender's and UE's `bounds.origin`**.
Which side the geometric center leans toward reveals the axis:

| Asset | Blender center | UE center (before fix) |
|---|---|---|
| arm_cannon | (0.012, **−0.198**, 0.378) | (0.012, **+0.198**, 0.378) |

→ The mapping was `Blender (x,y,z) → UE (x,−y,z)`, **the Y axis was flipped**.
→ The mech's front was −Y in Blender; after the flip it landed on UE **+Y**, while UE wants **+X**.

**Fix**: `robotlib.export_fbx()` rotates **+90°** about the Z axis before export (−Y → +X) and restores afterwards.
This only applies to the export process; the `.blend` file isn't modified.

### Pitfall 2: LOD0 Bounds Are Too Large in UE

`SK_Chassis_Medium` (LOD0)'s `get_bounds()` reports a height of **2.718 m**,
but **the same asset's LOD1 reports 2.590 m, exactly matching the FBX**.

`bounds_extension` and `physics_asset` are both empty, ruling those two out.
Judged to be UE's bounds calculation behavior for LOD0 skeletal meshes, **only affecting how loose culling is, not asset correctness**.

**The authoritative criterion is the FBX itself**: `tools/blender/verify_fbx.py` round-trip tests confirm
`chassis_medium.fbx` = 1.142 × 1.670 × 2.590 m, and all 51 passed.

---

## Asset Naming Correspondence

Imported asset names are taken from the mesh object names inside the FBX, **not the file names**:

| FBX file | UE asset name |
|---|---|
| `chassis_medium.fbx` | `SK_Chassis_Medium` |
| `module_arm_cannon.fbx` | `SM_Module_ArmCannon` |
| `prop_fuel_barrel.fbx` | `SM_Prop_FuelBarrel` |
| `env_wall.fbx` | `SM_Env_Wall` |
| `landmark_lighthouse.fbx` | `SM_Landmark_Lighthouse` |

Materials were imported along with them into the directories (`M_Steel` / `M_Accent_*` / `M_Core_*`, etc.),
because the FBX carries material slots. These need to be replaced with UE material instances later.

---

## Next Steps

Import validation has all passed. Next: write the first GAS ability **`GA_Dash`**,
opening up the chain "consume power → generate heat → heat lock" —
this is the only part of the core loop not yet validated in the engine.
