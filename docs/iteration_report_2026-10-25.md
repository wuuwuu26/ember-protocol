> Language: **English** | [简体中文](./迭代报告_2026-10-25.md)
# Ember Protocol · Iteration Report 2026-10-25 (Rounds 1–59)

> ⚠️ **This file was overwritten in an editing accident on 2026-10-31.**
> The original ~80,000 characters (the complete record of rounds 1 through 59) was lost, and the project was not under git and had no backup.
> Only **Round 59** content and key data that could be confirmed from the last session are kept below;
> details of the earlier rounds are missing and cannot be fabricated from memory.
> New records from Round 60 onward are in `迭代报告_2026-10-31_第六十轮.md`.

---

## Round 59: Quadruped IK Overextension Zeroed Out

### Changes

**`tools/blender/robotlib.py` · auto_rig**
- Thigh/shin bone lengths now use the **3D distance** — the equivalent of `FVector::Dist(Hip,Knee)` / `FVector::Dist(Knee,Ankle)` —
  instead of taking only the Z-axis projection. When the knee bends, the horizontal component was wrongly discarded and the bone length was systematically
  underestimated, causing the IK-solved leg to "fail to reach the ground".
- The joint root is taken at the hip/knee sphere center, ensuring the bone length matches the visual geometry.

**`tools/blender/build_enemies.py`**
- Re-aligned the knee offsets and z heights of the quadruped legs of the hauler and colossus, so the knee spheres are collinear with the upper/lower bone endpoints.

**`MechProceduralAnim::FillLeg`**
- Leg length is computed by 3D distance, and the overextension check corrected accordingly.

**`MechProceduralAnim` clipping threshold**
- `dRaw > d + 0.5f` → `dRaw > d + 1.0f`.
  Reason: the leg is already nearly straight in the resting pose (vertical drop ≈ leg length, a 0.4% difference); a 0.5cm boundary jitter was miscounted every frame;
  real overextension (e.g. a quadruped at full speed) is all >2cm, so nothing is missed.

### Validation Data (r230, 585 lines of foot-slip data)

| Entity | Leg length fix | Foot slip | IK clipping | Overextension frames |
|---|---|---|---|---|
| Player | — | 0~22 | **0** | 0/117 |
| C_5 (gardener mech) | Yes | 0~212 | **0** | 0/117 |
| C_7 (hauler) | scale 1.155→0.77m | 0~230 | **0** | 0/117 |
| C_8 (weather mech) | Yes | 0~759 | **0** | 0/117 |
| C_9 (colossus) | shin corrected | 0~353 | **0** | 0/117 |

**All 5 entities, 117 frames × 5 = 585 sampled lines, IK clipping = 0, overextension = 0cm.**
Quadruped overextension (the core problem that plagued 58 rounds) was solved at the geometry level, without affecting bipeds.

### Conclusion
- The early judgment that "it wasn't done right at the modeling stage" was correct; the root cause was the logic flaw of **taking the bone length from the Z axis only**.
- The quadruped speed limit (checking `thigh_BL` via AnimMesh to detect quadrupeds, `SpeedK=1.30` quadruped / `1.70` biped)
  is still necessary: it suppresses speed, not bone length; removing it would make the foot-slip metric worse again.

---

## Remaining Rounds (1–58)

The original record is lost. Known topics include:
- Evolution of procedural gait (sine hip swing → two-bone IK reverse solve)
- Part damage / dismemberment and one-leg support compensation
- Enemy modeling rework (shell + armor facets), UV repair, 4K textures
- Player and enemy speed normalization, cadence/stride caps

To reconstruct, the only basis is the comments in `ue/Source/RobotGame/Private/MechProceduralAnim.cpp`
(every generation of changes has Chinese comments with "measured data + why it's done this way") — reverse-engineer from there.
