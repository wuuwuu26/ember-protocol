> Language: **English** | [简体中文](./迭代报告_2026-10-19.md)
# Iteration Report · 2026-10-19

This round targets three known problems: **broken locomotion animation / textures that don't fit the scene / modeling that isn't detailed enough**.
None of the three can be solved by "tweaking a few parameters" — each one hides a structural error underneath.

---

## I. Locomotion Animation: From "Sine-Wave Leg Swing" to "Two-Bone IK + Foot Locking"

### Three Root Causes (all only discovered through investigation)

**① The feet were never "placed on the ground", only "swung back and forth".**
The old implementation wrote an empirical curve for the hip angle and the knee angle separately (hip = amplitude·cos, knee = 6°+42°·sin),
and the foot position was the composite result of the two — mathematically it **could not guarantee** that the support foot stayed still in world space.
Measurements showed the support foot sliding on the ground at 40–80 cm/s, which from a distance looks like "walking on ice".

**② The pelvis bob was amplified 100× (the most expensive pitfall of this round).**
After the FBX came in, the bone local translation unit was **meters** (shin 0.43) while the world unit was **centimeters** (shin 43cm),
with a 100× skeleton scale sitting in between. And `OffsetBoneAxis` adds "centimeters" directly into the bone's local coordinates,
so a 3cm pelvis bob became a 3-meter sink — the mech sank right through the floor when walking.
The old screenshots where "the robot grew and shrank and drifted while walking" were caused by this, but had been attributed to the camera at the time.
Fix: when caching, measure the conversion factor from "shin local translation length / shin actual centimeter length", and multiply all translations by it.

**③ The debug side-view camera never took effect at all.**
`APlayerController` defaults to `bAutoManageActiveCameraTarget = true`, which grabs the ViewTarget back to the Pawn after Possess.
The debug camera was created before Possess, so the log said "view taken over" while the picture was still the third-person behind-the-back view —
this was also one of the reasons last round "still felt wrong even after changing the axis": the evaluation view itself was wrong. Fix: disable auto-management and re-assert every frame.

### New Implementation (`MechProceduralAnim.cpp`)

| Module | Approach |
|---|---|
| Gait cycle | Duty factor 0.62 (support 62% / swing 38%), phase offset 0.5 |
| Stride | Solved in reverse from speed `S = v·Duty·T`; if it exceeds 92% of leg length, automatically raise the cadence (to prevent foot sliding) |
| Foot target trajectory | During support, **moves backward at constant speed relative to the body** (exactly cancelling body forward motion); during swing, smoothstep forward push + sine foot-lift arc |
| Two-bone IK | Law of cosines to solve hip/knee: `α=acos((L1²+d²−L2²)/2L1d)`, `K=π−acos((L1²+L2²−d²)/2L1L2)`, knee bends forward |
| Foot pitch | Support −7°→+14° (heel strike → push-off), swing +16°→−8° |
| Pelvis height | Derived from the **support leg** `h=√(dMax²−fwd²)`, take the larger of the two legs → the support foot lands exactly, no clipping, no floating |
| Pelvis sway | Center of mass shifts 2.6cm toward the support leg, with **smooth interpolation** (a hard cut makes the whole machine jump 5cm sideways in one frame) |
| Upper body | Torso leans forward 5°, shoulders and hips counter-twist ±4.5°, arms swing in antiphase with the same-side leg (0.85× the leg) with elbow flex/extend following the swing |

### Validation (logs + burst shots)

- Support foot world coordinates stay **frame-by-frame constant** during support (e.g. left foot X = −166.7 for three consecutive frames)
- Sliding metric (support foot world displacement speed) dropped from 4000+ cm/s to the 0–20 cm/s range;
  the remaining spikes come from the leg-switch frame and are invisible to the eye
- Stride 71.8cm, cadence 7.6 rad/s (≈2.4 steps/sec), full cycle of hip −53°…+3°, knee 15°…72°
- Side-view burst shots (`docs/shots/f_*.png`) show the three states "lift — land — switch legs"

---

## II. Textures Don't Fit the Scene: Materials **Weren't Attached At All**

### The Real Root Cause

There were **146 static mesh components in the scene (floor / walls / catwalks / pillars) all still using the engine's
`BasicShapeMaterial`** — a piece of plain light-gray plastic with no detail whatsoever.

Reason: the arena was rebuilt by script (`rebuild_arena.py`); after generating the StaticMeshActors it never re-pointed the materials back,
and the material overrides were left on the components. So:

- The floor was a uniform light gray, which under the 4200K warm light turned into a "desert color"
- All the color tuning, panel seams and metallic adjustments targeting `M_RobotSurface` had **zero effect** on it
- The mechs (with materials) and the scene (without materials) weren't in the same art system at all — that's the source of "not matching"

Fix (`ue/Scripts/fix_env_materials.py`): fill the empty slots on the mesh assets + clear the 690 material overrides on the 146
Actors, falling back to the materials that ship with the meshes.

### The Second Pitfall: The Wear Color "Bleached" Dark Surfaces White

The parent material's wear color was hard-coded as `base*0.5 + 0.45` — for a dark surface (0.10),
the wear color is 0.50, **5× brighter**; and the wear channel of the environment detail texture was already broadly bright,
so the whole floor was "worn" into pale gray-white, and changing the base color had no response at all (measured: changing the environment steel from
0.15 to 0.105, the picture brightness didn't change one bit).

Changed to `base*1.45 + 0.015` (relative to the base color), so wear is actually "wear" instead of "brightening".

### Color Unification (`FORCE_COLOR` Table)

No longer relying on the DiffuseColor in the FBX (on re-import the importer reuses old materials and the color doesn't update),
instead specified explicitly in the material script:

| Purpose | Color | Reason |
|---|---|---|
| Mech painted armor | 0.30 / 0.31 / 0.34 | Cool gray-blue, "pops" against the warm scene |
| Mech bare steel plate | 0.40 / 0.41 / 0.43 | One step brighter than the armor, edge reads as layers |
| Mech frame/joints | 0.075 / 0.052 | Keeps the seam between armor plates black so the block-out is visible |
| Environment steel structure | 0.105 / 0.165 | Dark steel gray, yields the visual center of gravity to the subject |
| Environment safety color | 0.56 / 0.36 / 0.07 | Safety yellow, the identification color of an industrial site |

### Lighting

The aim point of the spotlights was raised from "the floor" to Z=170 (mech chest height) — originally the center of the light cone all smashed into the floor,
the floor was overexposed and the mech's vertical faces got no light. Also added 4 × 5600K cool-white fill lights (3.2m high, no shadows),
specifically lighting the mech's vertical faces, forming a warm/cool opposition with the 4200K warm spotlights.

---

## III. Modeling: Structural Rebuild (v4)

The old version's problem wasn't "not enough detail", it was that **the structure didn't read**: all the main blocks were axis-aligned boxes,
and adding more greebles just made "a stack of cardboard boxes with parts glued on".

| Change | Description |
|---|---|
| Trapezoidal prisms (`R.prism`) | Chest wide on top narrow on bottom, thigh thick on top thin on bottom, shoulder armor flared out, shin tilted forward — get the silhouette right first |
| Frame / armor two layers | The dark inner frame is always a size smaller than the armor, gaps between armor plates, hydraulic rods and cable harnesses visible from the side |
| Leg length 38% → 42% | The old version was short and stout; now hip 134 / knee 91 / ankle 28, standing proportions are normal |
| Radiator tucked into the shell | Old fins stuck out 5cm like a "fallen-out comb"; now a recessed frame + inset fins |
| Joint armor covers | Knee pads, ankle guards, elbow caps, hip guards — no seams exposed when rotating |
| Weapon detail | Receiver / feed / barrel / three cooling rings / muzzle brake / muzzle |
| Left arm changed to a mechanical claw + sensor pod | Both arms being cannons was monotonous; also fits the "standard mount interface" setting |
| Three-part foot | Heel (counterweight) + sole + toes, with anti-slip treads |

LOD0 triangle count 28.8k (identical for the three mechs), LOD1/LOD2 auto-generated.

---

## IV. Verification and Evidence

| Item | Result |
|---|---|
| Compile | Three modules fully rebuilt through the chain (Core → Combat → Game) |
| Asset re-import | 9 FBX (3 mechs + 6 enemies) deleted and rebuilt, three mechs have 9 material slots / complete skeletons |
| Gait | Support foot locked frame-by-frame; sliding 0–20 cm/s; side-view burst shots show the full cycle |
| Picture | 146 scene components' materials fixed; floor/walls have panel detail; warm/cool separation |
| Combat | `-AutoFire` killed remaining enemies 5→2 within 7 seconds, shooting/overheat/part-damage chain works |

Screenshots: `docs/shots/` (`hero.png` combat, `close_mech.png` close-up detail,
`f_*.png` gait burst shots, `new_look6.png` new color-scheme panorama)

---

## V. Next Steps (by priority)

1. **Enemy models** are still the old blocky version (6 types), need rebuilding with the v4 structural language — they make up half the "mechs" in the picture
2. **Animation layer**: procedural poses for sprint (forward lean + legs tucked in), hit stagger, reload/overheat shake
3. **Floor detail**: the environment detail texture is flat (R channel mean 246/255), needs stronger panel seams and oil-stain contrast
4. Hand/weapon attachment points: change the muzzle from "bone + hard-coded offset" to a socket, so changing the weapon arm follows automatically

---

## VI. Addendum: Walling Off the Map (Preventing Falling Out)

### Diagnosis

The walls actually existed (`rebuild_arena.py` placed 30 segments of `SM_Env_Wall` around the perimeter),
but "having walls" and "can't fall out" are two different things; three layers were added here:

1. **Collision confirmation**: `SM_Env_Wall` has 1 convex collision body and physically does block the player;
   but the auto-generated FBX collision changes with import settings and can't be the only safeguard.
2. **Code-level hard boundary** (`ARobotCharacter::ClampToArena`, executed every frame):
   clamps the character to `x ∈ [-1232, 1732]`, `y ∈ [-1312, 1312]`,
   and zeroes the **outward** velocity component while preserving the tangential velocity — sliding along the wall stays smooth.
   The numbers = the inner faces of the walls (−1277 / 1777 / ±1357) minus the capsule radius 45.
3. **Fall-back catch**: Z < −300 counts as falling out, pull back to the last stable standing position;
   same for enemies (if they fall they can never be hit and the mission soft-locks), pull back to the spawn point.

### Validation (measured logs)

```
# Walking toward the +Y side wall
[Walk] t=8s pos=(1102,1236,122) speed=139
[Boundary] hit fence: pos=(1179,1313,122) vel=(99,0)     <- lateral velocity preserved
[Walk] t=10s pos=(1179,1312,122) speed=140

# Walking toward the +X far wall
[Boundary] hit fence: pos=(1733,-138,122) vel=(0,0)
[Walk] t=4s pos=(1732,-138,122) speed=0
```

Both directions were stably stopped at the boundary, and sliding along the wall doesn't get stuck.

### Debug Parameters Added Along the Way

| Parameter | Purpose |
|---|---|
| `-WalkForever` | Walk forever (originally only walked 7 seconds, couldn't reach the walls) |
| `-WalkBack` | Walk toward −X (validate the back wall) |
| `-SpawnAt=x,y` | Change the spawn point (for wall-hugging tests; ⚠️ measured as ineffective, ultimately used `move_spawn.py` to change PlayerStart) |
| `ue/Scripts/move_spawn.py` | Temporarily move PlayerStart (env vars SPAWN_X/Y/Z/YAW) |

⚠️ `-SpawnAt` didn't take effect in BeginPlay (reason unknown, the log didn't even enter the branch),
   so ultimately used the "move PlayerStart via script → run → move it back" approach for validation. Needs investigation before using it later.

---

## VII. Addendum: Real Walls / Curved-Surface Modeling / Texture Pipeline Repair

### 1. Real Walls (New Assets + Re-laying the Walls)

The old walls were 4m square panels (46 thick, two face plates), which from a distance looked like a row of gray boxes. New:

| Asset | Contents |
|---|---|
| `SM_Wall_Segment` | Base → wall body (two recessed panels / four outward-leaning buttresses / access hatch / ventilation grille / rivets) → overhanging rounded coping → top pipes and clamps → bottom safety-color band |
| `SM_Wall_Corner` | 90×90 corner pillar: cylindrical corner wrap + coping + warning band + top warning light |

`rebuild_walls.py`: deleted the 30 old wall segments, re-laid 30 segments at 4.0m spacing (segment length 4.12m, 12cm overlap, no gaps),
and added corner pillars at the four corners. Orientation rotated so the "inside faces the arena" (back wall yaw=90 / far wall −90 / south wall 180 / north wall 0).

### 2. Textures: Two Hard Failures (These Are the Real Root Cause of "Unrealistic Textures")

**① The detail textures were actually 32×32 placeholders.**
`T_MechDetail / T_EnvDetail` both had `blueprint_get_size` = 32 — meaning the import failed and UE left a placeholder texture,
and `replace_existing=True` skips rebuilding assets whose "source file hasn't changed", so it could never be fixed. After deleting the four textures and re-importing, they returned to 1024×1024.

**② The triplanar material function chain completely failed.**
Changing `TextureSize` 120→40, `SeamDarken` 0.46→0.02, `WearTint` to pure red,
**didn't change a single pixel on screen**. The function node's pin connections couldn't be read from Python, so there was no way to confirm whether they were connected.
→ Switched to UV sampling, and on the Blender side changed the UV to **world-aligned cubic projection**
(`robotlib.cube_uv`, 1 UV unit = 1.2m): faces with the same orientation share continuous UVs,
panel seams no longer tear — the problem triplanar was meant to solve was solved at the modeling stage.

### 3. Curved-Surface Modeling

`robotlib` added `ellipsoid` (can be halved), `torus`, `tube` (Bezier round tube),
`capsule`, `rounded_box`; `build_chassis` fully replaced:

| Part | Before | Now |
|---|---|---|
| Shoulder armor | Three stacked slanted flat plates | Half dome + curved shell + identification-color trim ring |
| Head | Box | Rounded skull + dome on top + curved brow guard |
| Limbs | Box | Cylinders (mechanical parts) + curved armor shells |
| Joints | Cylinder | Ball-and-socket + copper rings (shoulder / elbow / hip / knee / ankle) |
| Foot | Box | Rounded sole + half-ellipsoid toes |
| Backpack | Box | Cylindrical tanks (capsules) |

Triangle count 28.8k → 48.9k (LOD0), identical for the three mechs.

### 4. Lighting: Discovered "Firefighting Code" Overriding the Formal Lighting

`FixLevelLighting()` was firefighting code written during an early black-screen period: it pushed the sun down to **6 lux**, sky light 0.22,
and post-processing to manual exposure bias 8.8. It overrode all the formal lighting from `relight.py` (30000 lux / 2.2 / EV13.6) —
no matter how the materials were tuned they looked gray and washed out; that was the root.

Added a check: sun intensity ≥ 1000 lux counts as "formally lit", skip the override, only force the PPV to unbounded.
⚠️ **But the exposure in the formal-lighting path still isn't right** (at EV13.6 the picture overexposes to yellow),
so the old path is still used for now (bias changed from 8.8 to 6.6). This is the first thing to finish next round.

### 5. Validation

- Walls: 30 segments + 4 corner pillars in the level; close-up shows recessed panels / buttresses / coping / safety color band
- Textures: panel seams and wear visible on the mech surface (`docs/shots/final_close.png`)
- Curved surfaces: shoulder domes, spherical joints, cylindrical limbs (same as above)
- Compile: all three modules pass through the full chain

---

## VIII. Addendum: Lighting Root Cause (2026-10-22)

For several rounds there was an inexplicable problem: **materials looked gray and orange no matter how they were made**. This round found the root cause:

### 1. Sky Light Can't Capture the Sky

The engine printed a line of red text directly on the picture:

> A sky light with real-time capture enable is in the scene. It requires at least
> a SkyAtmosphere component, a VolumetricCloud component **or a mesh with a
> material tagged as IsSky**. Otherwise it will be black.

That is: SkyLight had real-time capture on, but **nothing in the scene was tagged as "sky"** —
the self-built dome material only had `used_with_sky` set, not `is_sky`.
As a result the sky light captured black → ambient light near 0 → the whole scene only had a few warm lights shining directly,
no cool fill in the shadows, so it was "flat and orange".

Fix: set `is_sky = True` on `M_SkyDome`. After the change the sky actually appeared,
ambient light had a source, and the picture immediately gained directionality and shadow layers (see `11_布光修复后.png`).

### 2. All Lights Are Sodium-Orange

The 15 point lights were built early with 2000K sodium lamps, and `relight.py` only changed intensity not color temperature,
together dyeing the floor, mechs and walls orange.
→ `fix_light_color.py`: point lights unified to 5200K / 1400cd, spotlights 5000K.

### 3. Bloom Threshold Is Negative

`BloomThreshold = -0.35` means **even mid-gray blooms**, and bright surfaces blur into a white fog.
→ Changed to 1.0, intensity 0.45.

### 4. Sun Intensity Adjustable

The hard-coded 6 lux in `FixLevelLighting()` (the firefighting-era magnitude) changed to adjustable `-SunLux=`,
still conservative by default. Exposure `-Bias=` is also adjustable (manual exposure is the only path that works in practice).

### 5. Still Unresolved

- The dome's **sun glow** still isn't tuned right: the sky is clean and dark now, but the "dusk" atmosphere is weaker
- Backlit faces are too white (material albedo 0.30 + strong key light), need another 0.5 stop of exposure reduced
- These all need a **dedicated lighting iteration**, not something to fix in passing

### 6. Next Step (Gameplay)

The art line is parked in a "usable" state for now; switching to gameplay next:
enemy AI is still "approach in a straight line + fire", needs strafing/cover; plus hit feedback and death presentation.
