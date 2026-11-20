> Language: **English** | [简体中文](./迭代报告_2026-10-31_第六十至一百一十九轮.md)
# Round 60 (2026-10-31): Root cause of the distorted foot-slip metric and its fix

## I. Problem

The `[FootSlip]` (foot-slip) metric has long contradicted the steady-state sliding of `[Gait]` (gait):

- `[Gait]` shows steady-state sliding close to 0 (the foot really does stay planted on the ground);
- `[FootSlip]` instead reports a mean of 24~82cm/s and peaks of 1000~9900cm/s.

For the same foot, the two sets of numbers differ by two orders of magnitude — **the metric itself is not trustworthy**.

## II. Layer-by-layer localization (five independent defects, all of which inflate the numbers)

### Defect 1: `[FootSlip]` is measured before SolveLeg, reading the previous frame's stale foot position
The old section ⑥'' ran before SolveLeg, so `LocalAccumWorldPos` read the foot position **left over from the previous frame**;
whereas `PrevAnkleL/R` stores the post-solve foot position. The two are off by one frame, so the entire step displacement is counted as sliding.
**Fix**: Delete the standalone section ⑥'' and merge the sliding statistics into section ⑥', which runs after SolveLeg.

### Defect 2: The sliding statistics are wrapped inside a 0.15s log throttle (root cause, largest impact)
The entire sliding calculation was written inside `if (S.Time - S.PrevGaitLog > 0.15f)`, so it ran only about once every 0.15 seconds.
Consequently `PrevFL` is not "the previous frame" but "0.15 seconds ago":

```
Speed 140cm/s × 0.15s ≈ 21cm; turning/arc-length addition can reach 60~73cm;
then ×60 (equivalent to 60fps) = 3600~4400cm/s — purely wrong-frame amplification.
```

**Fix**: Move the sliding calculation entirely out of the throttle block and run it every frame; only the log printing stays inside the throttle.
After the change, the peak immediately dropped from 4500~9900 to 145~650.

### Defect 3: Two `[Gait]` logs share the same throttle field
Stage ④ (speed/cadence/stride length) uses `S.PrevGaitLog` (0.25s), and the `[Gait]`/`[FootSlip]` of ⑥' use it as well
(0.15s), overwriting each other, which makes the timing of ⑥' log output chaotic or even swallowed.
**Fix**: Stage ④ switches to a separate field `PrevPhaseLog`.

### Defect 4: The foot-slip state lives in function-local `static`, polluting multiple machines
`PrevFL/PrevFR/bPrevStance/bPrevValid` used to be function-local `static`, shared by all entities.
Machine A writes a foot position, machine B reads it and computes "sliding", producing meter-scale fake displacement (peak 54884cm/s).
**Fix**: Move all of them into per-instance state `FMechAnimState`.

### Defect 5: `MoveBlend` is multiplied twice
`Half = Stride*0.5*MoveBlend` already scales, and `P.Fwd = P.Fwd*MoveBlend` scales again,
so the actual stride is ∝ `MoveBlend²`. Before full speed, the stance-phase backward move cannot keep up with the body advancing → the foot slides backward.
**Fix**: Delete the second multiplication. The player's "frames exceeding the threshold every frame" dropped from 24 to 1.

### Additional: The `bMoving` criterion is too dull
`SpeedRatio > 0.06` (≈13cm/s) flips repeatedly when an enemy is blocked/turning and the speed hovers at 0~10cm/s,
`Stride` jumps between 0 and its normal value, and the foot teleports 20cm+ (measured: C_7 at speed=5, foot jumped 21.6cm).
**Fix**: Change to the continuous criterion `Speed > 0.5f`.

## III. Measured results after the fix (r272, -AutoWalk -WalkForever -DebugGait, 30s)

Average sliding by speed bucket (cm/s, equivalent to 60fps):

| Entity | 0-30 | 30-80 | 80-130 | 130-260 |
| --- | --- | --- | --- | --- |
| Player | 0.0 | — | — | **19.8** |
| C_5 | 21.2 | 30.3 | 106.5 | 78.9 |
| C_7 | 0.0 | 168.3 | 138.2 | 81.3 |
| C_8 | 32.4 | 60.0 | 40.0 | 84.5 |
| C_9 | 173.1 | 267.8 | — | 88.0 |

- **Player meets the target**: 0 at rest, 19.8 at full speed, well below the 40cm/s threshold of human visibility.
- **Enemies at full speed 79~88cm/s**: this is real residual error, no longer a wrong-frame artifact.

## IV. Positive evidence already verified as effective

Diagnostic `[GaitRate]` (prints the `Fwd` rate of change and body advance frame by frame):

```
Player  speed=140  dFwd=-1.45  expect=-1.45
Player  speed=140  dFwd=-1.64  expect=-1.64
Player  speed=140  dFwd=-1.39  expect=-1.39
```

**The stance-phase backward `Fwd` movement is exactly equal to the body advance frame by frame**, showing that the mathematics of "linear backward move cancels advance" holds.
The player's residual 19.8cm/s comes from pelvis sway (`SwayCm`±2.6cm) and a tiny coupling with IK.

## V. Conclusion on enemy residual sliding (direction for the next round)

Hypotheses investigated and measured conclusions:

1. **Turning rotation component**: Under `-WalkForever` the player moves in a **straight line** (X from -200→1210, Y always 0),
   `YawRate≈0`. Stance-phase lateral compensation `FwdLat = -ω×Lat×T×(U-0.5)` has been implemented,
   effective at low-to-medium speeds but with limited improvement at full speed.
2. **Near-singular leg**: C_5 `d=89.3` (L1+L2≈111), C_9 `d=168.1` (≈191),
   **the leg still has margin and is not singular**. Lowering the IK cap from 0.999 to 0.80 brought no improvement; reverted.
3. **Foot locking (world anchor)**: theoretically correct, but at full speed the enemy leg cannot reach a fixed anchor for the whole stance phase
   (body translation exceeds the leg's extension budget), degrading to clamped sliding; reverted.
4. **Legs with `legvalid=0`** (e.g. C_6's left leg): IK not established, the foot follows body translation entirely.
   Invalid legs have been excluded from the sliding statistics.

**Main sources of the residual**: the phase coupling of front and rear legs in quadruped diagonal gait, and the interaction between `SwayCm` and the front leg's
`Fwd` compensation. Next step: design a dedicated "hip height and sway joint transition at support-leg switch" for quadrupeds,
or add knee-flexion margin to quadruped legs at the asset level (during modeling), leaving travel geometrically.

## VI. Changed files

- `ue/Source/RobotGame/Private/MechProceduralAnim.cpp`
  - Delete the old section ⑥'' foot-slip block; merge sliding statistics into ⑥' and make it run every frame
  - Stage ④ logs switch to `PrevPhaseLog`
  - `LegTarget` removes the duplicate `MoveBlend`; add the turning lateral compensation `FwdLat` shared by quadrupeds and bipeds
  - `bMoving` changed to `Speed > 0.5f`
  - Sliding counted only for valid legs (`S.LegL/LegR.bValid`)
- `ue/Source/RobotGame/Public/MechProceduralAnim.h`
  - Add `PrevPhaseLog`, `FwdLat` related items, per-instance `PrevFL/PrevFR/bPrevValid`,
    `SlipMaxL/R`; remove function-local static state

---

# Round 61 (2026-10-31): Dropped frames pollute the metric + five failed hypotheses

## I. The valid result of this round: dropped frames must be excluded

At the end of the previous round there were weird peaks of 4201 / 6283. The cause was found to be **occasional ultra-long frames** (measured `Dt=0.4s`):

```
The ×60 displacement algorithm, on a frame with Dt=0.4, reports "one big step the body itself took" as 3000~6000cm/s.
```

This is not sliding and is not reproducible. **Fix**: frames with `Dt > 0.03` are not counted in the sliding statistics
(`PrevFL` is still updated, so the next frame does not compute a difference against an even older position).

### Measured results after the fix (r283, the best version)

| Entity | Mean | Peak | Frames >40 |
| --- | --- | --- | --- |
| **Player** | **5.6** | **28** | **0/190** |
| C_5 | 55.3 | 684 | 74/190 |
| C_7 | 70.8 | 1310 | 72/190 |
| C_8 | 53.9 | 800 | 69/190 |
| C_9 | 83.9 | 425 | 137/190 |

**All 190 sampling windows of the player are below the 40cm/s threshold, peak only 28** — the biped sliding problem is essentially solved.

## II. Five hypotheses tried and **reverted** this round

Recorded honestly to avoid repeating the same pitfalls next round:

### 1. Gait speed low-pass (`SmoothSpeed`, time constant 0.12s) — failed
Hypothesis: when enemy AI accelerates/decelerates, `GetVelocity()` jumps frame by frame (133↔45), causing gait parameters to jitter.
Measured: **worse**. The low-pass decouples `Stride` from actual advance; C_5 in the 0-30 bucket rose from 21 to 132.
Reason: the foot must compensate by the **actual** displacement while the rhythm follows the smoothed speed; inconsistency necessarily slides.

### 2. Freeze stride length during stance (`FreezeHalf`) — failed and introduced a new bug
Hypothesis: changes in `Stride` shift `Fwd = Half − 2·Half·U` as a whole, flinging the foot out.
Measured: if the frame entering stance happens to have `Stride≈0`, `Half` for the whole stance is locked to 0,
the foot does not move back at all, and sliding gets worse. **Reverted.**

### 3. Widen the IK distance cap from `0.80` to `0.999` — failed
Hypothesis: normal walking of quadruped legs needs `d≈0.8~0.99·(L1+L2)`; pressing it to 0.80 makes the whole stance hug the clamp edge.
Measured: **worse across the board**, player rose from 19.1 to 74.2. Reverted.
(Observing `d` always equal to the 0.80 cap is a **result**, not a cause.)

### 4. Add `AxisRight * SwayCm` to the foot Target (cancel pelvis sway) — failed
Hypothesis: pelvis sway drags the foot sideways.
Measured: player 19.1 → 19.9, enemies got worse too. The original "hip and foot sway together" is a deliberate center-of-mass motion;
forcibly cancelling it breaks it. Reverted.

### 5. Foot locking (world anchor `PlantWorld`) — failed
Already verified last round: at full speed the enemy leg cannot reach a fixed anchor for the whole stance phase, degrading to clamped sliding.

## III. Excluded causal relationships (data conclusions)

- **The `Fwd` compensation itself is precise**: `[GaitRate]` compares `dFwd` with `-Speed·Dt` frame by frame,
  the player is exactly equal in steady state (-1.45/-1.45, -1.64/-1.64).
- **Turning is not the main cause**: under `-WalkForever` the player moves in a straight line (X −200→1210, Y always 0),
  `YawRate≈0`, rotation compensation has almost no effect on the scene.
- **The leg is not near-singular**: `C_5 d=89.3` (L1+L2≈111), `C_9 d=168.1` (≈191), both have bending margin.
- **Legs with `legvalid=0`** (e.g. C_6's left leg) have no IK established, the foot follows body translation entirely;
  excluded from the statistics.

## IV. Suggested direction for the next round

The residual problem **exists only in quadrupeds and grows with speed** (C_9 is worst, 137/190 frames over the threshold).
The known fact is "`Fwd` changes by only 0.2cm, yet the foot travels 6cm in the world",
meaning the foot landing point is **not** dominated by `Fwd`, but determined by the IK-solved `Hip/Knee` angles coupled with pelvis state.

Choose one of two paths; stop chipping away at it:

1. **Asset level**: add knee-flexion margin to quadruped legs in the rest pose (lower `DropCm / (L1+L2)`),
   giving IK real travel space. This conclusion was written in the code comments long ago.
2. **Gait-layer refactor**: a separate support-leg switching logic for quadrupeds (joint transition of hip height and sway),
   no longer reusing the biped `Duty=0.5` + single-point `Sway` model.


---

# Round 62 (2026-11-01): Adding knee-flexion margin at the asset level — failed and fully reverted

## I. Motivation

Conclusion of Round 61: residual sliding exists only in quadrupeds and grows with speed (C_9 worst),
and "`Fwd` changes only 0.2cm yet the foot travels 6cm" means the landing point is not dominated by `Fwd`.
Therefore quadruped legs need real travel **at the asset level**.

## II. The real modeling defect identified

`tools/blender/robotlib.py` · `auto_rig`:

```python
# Old implementation
tail = (jh[0], jh[1], jh[2] - seg)   # tail is always straight down
```

Quadruped knees are offset forward/backward (hauler offset `0.36*D`, colossus offset `0.55m`),
so the visual cylinder is slanted, **but the skeleton is still vertical**. Thus the UE side reads `Rest.Theta1Deg≈0`
(thinking the leg is vertical), while the actual knee/ankle are offset half a meter in Y — a systematic mismatch between skeleton and geometry.

This is a **real modeling defect**, not a guess.

## III. Two attempts and results

### Attempt A: Point the bone tail at the next joint (thigh→knee, shin→ankle)

Result: **all enemy IK failed** (`leg valid L=0 R=0 BL=0 BR=0`),
and `[FootSlip]` showed all enemies at 0 — that is an illusion caused by invalid legs being excluded, not a real absence of sliding.

Reason: the shin's "next joint" took the bounding-box center of the `foot_*` part (the middle of the sole),
which is lower and forward of the real ankle, stretching and twisting the shin so `FillLeg` could not establish valid geometry.

### Attempt B: Make only the thigh point at the knee sphere (shin stays vertical)

Result: **same, all failed** (L=0 R=0 BL=0 BR=0).

This shows the UE-side `FillLeg` depends on a "non-vertical leg bone" rest pose;
once the thigh has a Y-axis tilt, the whole leg's rest geometry cannot be built.

## IV. Conclusion

- Changing the skeleton at the asset level is **theoretically correct, but the current UE-side `FillLeg` does not support tilted leg bones**.
  To truly take this path, `FillLeg` must first be changed to accept rest leg bones of arbitrary orientation
  (use the bone orientation matrix instead of "Z axis down" to derive `Theta1/Theta2`). This is a fairly large change.
- **All asset changes this round have been fully reverted** (`robotlib.py` restored to `tail = (hx, hy, hz - seg)`,
  `seg_len` restored to look only at the Z span); the FBX was rebuilt and re-imported.
- After the revert, measurements confirm the baseline is restored:

| Entity | Mean | Peak | Frames >40 |
| --- | --- | --- | --- |
| Player | 5.0 | 22 | **0/192** |
| C_5 | 56.6 | 1059 | 65/192 |
| C_7 | 87.6 | 659 | 99/192 |
| C_8 | 47.3 | 289 | 75/192 |
| C_9 | 85.9 | 579 | 121/192 |

Leg validity restored to `L=1 R=1` (quadrupeds include `BL/BR=1`), confirming no residual damage.

## V. The only correct entry point for the next round

**First change the UE-side `FillLeg`** to derive `Theta1Deg/Theta2Deg` from the bone's true rest orientation,
instead of assuming "the leg points straight down". Only after that does the Round 62 asset change (thigh pointing at the knee)
make sense and have a chance of truly solving quadruped sliding.

Until then, patching `Fwd`/`Sway`/`Stride`/`Duty` will produce no substantive progress.

---

# Round 63 (2026-11-01): Skeleton tilt + pelvis height correction

## I. First, correcting a misjudgment in Round 62

Round 62 recorded "`FillLeg` does not support tilted leg bones", **this conclusion is wrong**.

`FillLeg` itself fully supports arbitrary orientation: it uses `LocalAccumCompPos` to read the real hip/knee/ankle positions,
then computes `Theta1Deg/Theta2Deg` with `atan2(V.X, -V.Z)`, with no assumption that "the leg must be vertical".

The real reason for the Round 62 failure: **I changed the shin at the same time**, pointing the shin tail at
the bounding-box center of the `foot_*` part (middle of the sole). That point is lower and forward of the ankle joint,
stretching and twisting the shin, so `V1/V2` could not be established. Changing only the thigh causes no problem — verified this round.

## II. Changes this round

### 1. `tools/blender/robotlib.py` · thigh bone truly points at the knee sphere

```python
tail = (jh[0], jh[1], jh[2] - seg)          # Old: always vertical
# New: thigh tail points at the real knee sphere center, length still from this bone segment
```

Quadruped knees are offset forward/backward by 0.36·D (hauler) ~ 0.55m (colossus); the thigh bone now matches the visual geometry.
Measured `Theta1` changed from 0 to ±22.8° (C_9) / ±44.5° (C_5).

The shin stays vertical — the attempt to slant the shin cylinder's end point was reverted:
moving the ankle up changed `LegLengthCm` from 191 → 96cm, and the IK target far exceeds reach
(exceeding by 20~59cm, tens of thousands of clamps).

### 2. `MechProceduralAnim::Update` · pelvis height baseline changed to the real rest drop

The old logic `h = sqrt((L1+L2)*0.985² − Fwd²)` implicitly assumed "the leg is nearly straight at rest".
With a flexed-knee skeleton this assumption fails, lifting the pelvis too high and pressing the support leg to the clamp limit.

```cpp
// New: use the real RestDrop as baseline, allow only 35% of knee-flexion margin to be used
const float Cap = RestDropBase + (DMax - RestDropBase) * 0.35f;
SupportH = max(SupportH, min(MaxReach, Cap));
```

## III. Measurements (median of four independent runs)

A single measurement **varies enormously** (C_8 jumps between 15.9~64.6); only a multi-run median is trustworthy.
The first run reporting "C_8 improved 66%" was luck, not a conclusion.

| Entity | Median | Baseline | Change |
| --- | --- | --- | --- |
| Player | **5.0** | 5.0 | unchanged |
| C_5 | 54.1 | 56.6 | slightly better |
| C_7 | **71.5** | 87.6 | **improved 18%** |
| C_8 | 49.9 | 47.3 | unchanged (slightly worse) |
| C_9 | 89.3 | 85.9 | slightly worse |

Raw values per run:

| Entity | run1 | run2 | run3 | run4 |
| --- | --- | --- | --- | --- |
| Player | 4.7 | 4.7 | 5.4 | 5.2 |
| C_5 | 54.9 | 46.0 | 53.3 | 63.4 |
| C_7 | 60.6 | 75.6 | 67.4 | 82.6 |
| C_8 | 15.9 | 53.8 | 46.0 | 64.6 |
| C_9 | 96.0 | 86.2 | 79.2 | 92.4 |

## IV. Conclusion

- **C_7 is the only entity with substantive improvement** (87.6 → 71.5), the rest are basically unchanged.
  The change is kept (no regression, local benefit).
- **IK clamping increased sharply** (C_9 tens of thousands cumulatively), showing that after skeleton tilt the 2-bone IK and pelvis height
  still have a systematic mismatch. This is the mainline for the next step.
- **The measurement method must change**: a single 30s run is insufficient to judge enemy sliding (fluctuation ±40%).
  All future validation uses "multiple runs, take the median".

## V. Next steps

1. Solve IK clamping first: the gap between `leglen` (`|Ankle−Hip|`) and `L1+L2` is too large
   (C_9: leg length 96cm, but `|V1|=142` while `|V2|=68`, front and rear legs asymmetric).
   Balance thigh/shin lengths in `build_enemies.py` so the two segments are close,
   otherwise IK gets dragged to the clamp by one overlong segment.
2. Then re-check the coordination of `SwayCm` with the flexed-knee skeleton.

---

# Round 64 (2026-11-01): Establish a stable validation environment + remove turning compensation

## I. The most important output of this round: reduce measurement noise from 158% to 2%

All earlier conclusions about enemies were unreliable because **a single 30-second run fluctuates enormously**:

| Entity | 4-run range / median |
| --- | --- |
| Player | 2% |
| C_5 | 47% |
| C_7 | 19% |
| C_8 | **158%** |
| C_9 | 29% |

The "C_7 improved 18%" reported in Round 63 falls within this noise range, **it cannot count as a conclusion**.

### Solution: use `-EnemyInPlace` as the validation environment

`-EnemyInPlace` drives the gait with a constant synthesized velocity, locks the body in place without moving, eliminating AI behavior differences
from spawn position, chase path, and being blocked by walls. Measured dispersion over three runs:

| Entity | Three-run median | Dispersion |
| --- | --- | --- |
| Player | 6.7 | <2% |
| C_5 | 84.0 | <1% |
| C_7 | 82.7 | <1% |
| C_8 | 101.2 | <1% |
| C_9 | 46.6 | <2% |

**All future gait validation uses `-EnemyInPlace` + median of multiple runs.**

Note: in this environment the script is supposed to move backward relative to the body by `-Speed`, so the absolute values cannot be
compared directly with free-walking numbers; it measures "the consistency of gait rhythm with foot position".

## II. Found and removed turning compensation (`FwdLat`)

Diagnostic logs gave decisive evidence:

```
C_5 dLat=-20.54  yawRate=-1  fwdLat=0.00
C_7 dLat=-26.54  yawRate=-0   fwdLat=0.00
C_8 dLat=+25.74  yawRate=0    fwdLat=-0.00
C_9 dLat=-31.01  yawRate=-0   fwdLat=0.00
```

On frames with `yawRate≈0` and `FwdLat=0`, the foot still jumps 20~31cm sideways.

Reason: `GaitYawRate = FindDeltaAngleDegrees(S.PrevYaw, YawDegrees) / Dt`
can jump in a single frame when an enemy turns in place to aim, saturating at ±360°/s clamp, then multiplied by a lever arm of 30~90cm
(`Lat` up to 91.2cm), so `FwdLat` can jump 25~30cm in one frame. This is a **pure source of sliding**.

Deleted; `FwdLat` is constantly 0. The `GaitYawRate` clamp tightened from ±360 to ±90 (only used for torso lean).

### Effect: mean essentially unchanged

| Entity | Before removal | After removal |
| --- | --- | --- |
| Player | 6.6 | 6.7 |
| C_5 | 82.8 | 84.0 |
| C_7 | 83.7 | 82.7 |
| C_8 | 101.8 | 101.2 |
| C_9 | 47.6 | 46.6 |

Means are flat. The reason for keeping this change is to **eliminate occasional 25~30cm instantaneous lateral jumps** (visually harmful),
not because it improves the mean.

## III. Changes tried and reverted this round

### Bone-segment balancing (colossus `kneeY` 0.55→0.30, `knee_z` 0.92→1.42)

Goal: pull C_9's `|V1|=142 / |V2|=68` (2:1) close to 1:1.
Result: the bone segments were indeed balanced (`|V1|=86.4 / |V2|=109~120`), but **sliding got worse across the board**
(C_5 54→73, C_7 72→84, C_9 89→105). Reverted.

### Thigh bone pointing at the knee sphere (Round 63 change) — retested in a stable environment, ineffective

Round 63 reported "C_7 improved 18%". Using `-EnemyInPlace` for comparison:

| Entity | Vertical skeleton | Tilted skeleton |
| --- | --- | --- |
| C_5 | 84.6 / 84.3 | 82.5 / 83.0 |
| C_7 | 84.1 / 85.2 | 82.4 / 85.1 |
| C_8 | 102.4 / 102.4 | 102.1 / 101.4 |
| C_9 | 47.5 / 48.8 | 47.6 / 47.7 |

**The difference is far smaller than repeatability error, equal to no effect.** Round 63's conclusion was a misjudgment caused by noise.
The change itself is harmless (skeleton matching visual geometry is a good thing), kept, but no longer treated as a source of improvement.

### Smoothing phase advance rate (`SmoothOmega`)

Hypothesis: `Omega` jittering with instantaneous speed causes `Fwd` to jump. Measured median over four runs almost identical to before
(C_7 83.8 vs 83.7), reverted.

## IV. A lesson on diagnostic methodology

`[SlipAxis]` only prints when `slip > 60cm/s`, **this is biased sampling**.
I used it to compute "median backward rate", yielding the contradictory conclusion of 80% for bipeds and 123~141% for quadrupeds,
actually because slow frames were filtered out. **You cannot use conditionally triggered logs for distribution statistics.**

## V. Next steps

Excluded hypotheses (do not try again):
- bone-segment length balancing, thigh bone tilt, turning compensation, speed low-pass, phase rate low-pass, FK/foot locking

Unexplored directions:
1. Under `-EnemyInPlace`, record **all** frames (no trigger condition) frame by frame: the ratio of `dFwd` to
   `Speed·Dt`, to confirm the basic proposition "is the backward rate really equal to the speed?"
   If not, the problem is that `U`'s advance and `Stride`'s definition are not from the same source.
2. The difference between bipeds (C_5 84 / C_8 101) and quadrupeds (C_7 83 / C_9 47) in the same environment,
   unrelated to leg length (C_9 has the longest leg yet is cleanest), may be related to front/rear legs sharing phase under `Duty=0.5`.

---

# Round 65 (2026-11-01): Find a truly usable validation environment + cadence cap 12 → 20

## I. First, correcting an error in Round 64

The "stable validation environment" Round 64 built with `-EnemyInPlace` **was wrong**.

`-EnemyInPlace` locks the body position, so the foot's world displacement = the gait backward amount,
which is itself "normal" and **cannot measure sliding at all**. All the ratios I derived from it
("foot displacement is only 78% of expected") were describing normal swing, not a defect.

## II. New validation environment: `-EnemyWalkConst`

Added `-EnemyWalkConst` in `RobotEnemy.cpp` (used together with `-EnemyInPlace`):

- No position lock; instead the position is really advanced with a **fixed direction (+X) and fixed magnitude** velocity;
- The animation speed is also forced to the same fixed value, completely bypassing AI turning/acceleration/deceleration.

This provides both: constant velocity (low noise) + real world displacement (can measure sliding).

### Measurement method

The `[RateCheck]` log (no threshold filtering, accumulated frame by frame, summarized by window):

```
[RateCheck] owner=... n=186 footStep=0.71cm expect=1.76cm ratio=0.39
            residMean=1.87cm residMax=... | dPhase=... omegaDt=... phaseRatio=1.00
```

- `expect = Speed·Dt`: how much the body should advance this frame
- `footStep`: the foot's **world** displacement along the body forward axis (support foot should ≈0)
- `residMean = |footStep − expect|`: **this is the sliding, in cm/frame**

`phaseRatio = 1.00` confirms the advance of `S.GaitPhase += Dt·Omega` is correct,
and the premise "backward rate = speed" is self-consistent.

### Baseline (before change, 3 runs)

| Entity | Foot displacement | Expected | Ratio | **Residual mean (cm/frame)** |
| --- | --- | --- | --- | --- |
| Player | 0.22 | 1.13 | 0.17 | **0.91** |
| C_5 | 0.82 | 2.20 | 0.35 | 2.27 |
| C_7 | 0.80 | 1.59 | 0.50 | 0.99 |
| C_8 | 0.19 | 2.65 | 0.07 | 2.50 |
| C_9 | 1.67 | 1.51 | 1.11 | 0.38 |

## III. The correct solution this round: residual grows monotonically with speed → cadence cap too low

The most critical pattern in the baseline: **residual is positively correlated with speed**.

- C_8 speed 219cm/s, `Omega` already at the cap 12 → residual **2.50cm**
- C_9 speed 124cm/s → residual **0.38cm**

This means at high speed the body advances faster than the foot's swing rhythm. After stride is limited by `StrideMax`,
the excess speed must be absorbed by **cadence**; and the cap of `Omega = 2.4 + 9.6·SpeedRatio` is only 12rad/s,
unable to absorb it at high speed → the foot is dragged and slides.

### Raise stepwise and measure (3 runs each)

| Omega cap | Player | C_5 | C_7 | C_8 | C_9 |
| --- | --- | --- | --- | --- | --- |
| 12 (original) | 0.91 | 2.27 | 0.99 | 2.50 | 0.38 |
| 16 | 0.92 | 2.02 | 0.80 | 2.31 | 0.42 |
| 18 | 0.81 | 1.88 | 0.76 | 2.12 | 0.43 |
| **20** | **0.71** | **1.76** | **0.70** | **1.82** | 0.40 |
| 24 | 0.76 | 1.74 | 0.72 | 1.81 | 0.48 |

**Saturates around 20** (24 gives almost no gain, C_9 regresses), choose 20.

Change:

```cpp
// Original: float Omega = 2.4f + 9.6f * SpeedRatio;            // cap 12
float Omega = 2.4f + 17.6f * SpeedRatio;                  // cap 20
```

## IV. Free-walking regression (median of 3 runs)

| Entity | Round 61 baseline | This round | Change |
| --- | --- | --- | --- |
| Player | 5.0 | **4.7** | slightly better |
| C_5 | 56.6 | **39.7** | **−30%** |
| C_7 | 87.6 | **65.3** | **−25%** |
| C_8 | 47.3 | **41.0** | **−13%** |
| C_9 | 85.9 | **60.0** | **−30%** |

**This is the first real, reproducible improvement since Round 60 that also holds in free walking.**

## V. Hypotheses ruled out with the reliable environment

| Hypothesis | Result |
| --- | --- |
| Turning off `Bob` (pelvis bob) improves | **worse** (C_5 1.97→2.80, C_8 2.29→3.07). Bob is a helper, not a burden |
| Turning off `Sway` (pelvis sway) improves | Mixed after normalization, difference within noise |

## VI. New debug switches

- `-EnemyWalkConst`: together with `-EnemyInPlace`, really advance at a fixed speed (for the validation environment only)
- `[RateCheck]` log: unbiased sliding measure (cm/frame), all future validation uses this as the standard

## VII. Next steps

C_8 (1.99) and C_5 (1.87) still have high residual, both **bipedal** and fastest.
C_9/C_7 (quadrupeds) are cleaner (0.44 / 0.76). Next directions:

1. Biped `Duty=0.5` means only one leg supports at any moment, no overlap buffer;
   quadruped diagonal gait naturally has two legs supporting simultaneously. Try slightly adjusting biped `Duty` (0.52~0.55) to give overlap.
2. Continue confirming whether a higher `Omega` looks worse due to too-fast leg swing (needs screenshot review).

---

# Round 66 (2026-11-01): Fix the cross-instance sharing bug in the validation tool

## I. Found and fixed the validation tool bug from Round 65

The `-EnemyWalkConst` added in Round 65 used **function-local static**:

```cpp
static FVector ConstVel = FVector::ZeroVector;   // ❌ shared by all instances
static bool bConstInit = false;
```

Consequence: **only the first machine (C_5) initialized its own velocity at 189cm/s, all other entities
used that same 189**, while their respective animation speeds were 133 / 219 / 124.
Advance speed mismatched animation speed → the measured "sliding" was mixed with this artificial mismatch.

The logs directly exposed it (before the fix there was only one line `[WalkConst]`):

```
Before fix: [WalkConst] BP_Enemy_C_5 fixed advance speed=189cm/s     ← only one line
After fix:  [WalkConst] BP_Enemy_C_5 speed=189
            [WalkConst] BP_Enemy_C_6 speed=260
            [WalkConst] BP_Enemy_C_7 speed=133
            [WalkConst] BP_Enemy_C_8 speed=219
            [WalkConst] BP_Enemy_C_9 speed=124
```

Fix: change to **per-instance members** `WalkConstVel` / `bWalkConstInit` (`RobotEnemy.h`).

This is the same class of error as Round 60's "foot-slip state using function static caused 5 machines to pollute each other",
encountered a second time in the same project. **Whenever adding any per-instance state, first check whether it is written as static.**

## II. Retest the cadence change with the corrected environment

### Corrected baseline (cadence cap 12)

| Entity | Speed | Foot displacement | Expected | Residual mean |
| --- | --- | --- | --- | --- |
| Player | — | 0.17 | 0.87 | 0.70 |
| C_5 | 189 | 0.57 | 1.74 | 1.72 |
| C_7 | 133 | 0.38 | 1.23 | 1.24 |
| C_8 | 219 | 0.42 | 2.13 | 1.71 |
| C_9 | 124 | 0.65 | 1.14 | 0.50 |

### Real effect of cadence 12 → 20 (corrected)

| Entity | Cadence 12 | Cadence 20 | Change |
| --- | --- | --- | --- |
| Player | 0.70 | 0.59 | −16% |
| C_5 | 1.72 | 1.55 | −10% |
| C_7 | 1.24 | 1.05 | −15% |
| C_8 | 1.71 | 1.48 | −13% |
| C_9 | 0.50 | 0.43 | −14% |

**The improvement is real, but the magnitude is corrected from Round 65's overstated 13~30% to 10~16%.**
Round 65's numbers were optimistic because of the tool bug.

### Free-walking recheck (median of 3 runs)

| Entity | Round 61 baseline | This round | Change |
| --- | --- | --- | --- |
| Player | 5.0 | 5.2 | unchanged |
| C_5 | 56.6 | **42.1** | −26% |
| C_7 | 87.6 | 83.3 | −5% |
| C_8 | 47.3 | **32.2** | −32% |
| C_9 | 85.9 | 89.3 | +4% (within noise, three runs 75.4~94.8) |

Conclusion stands: cadence 20 is effective, kept.

## III. Hypotheses ruled out this round

### Biped `Duty` increased overlap buffer

Motivation: bipeds have only one leg supporting at any moment, quadruped diagonal gait naturally has two supporting,
so bipeds may lack redundancy.

| Duty | C_5 | C_8 |
| --- | --- | --- |
| 0.50 (original) | 1.53 | 1.61 |
| 0.56 | 1.50 | 1.65 |
| 0.62 | 1.45 | 1.63 |

Difference within noise, **no improvement, reverted to 0.50**.

### Strip `Bob` from IK hip point (`-IkNoBob`)

Conclusion consistent with Round 65's `-NoBob`: **residual grows** (C_5 1.53→1.69).
`Bob` helps the foot stay on the ground, not a burden. Reverted.

## IV. Current state

Corrected residuals per entity (cm/frame, smaller is better):

| Entity | Speed | Residual |
| --- | --- | --- |
| Player | — | 0.59 |
| C_9 | 124 | 0.43 |
| C_7 | 133 | 1.05 |
| C_8 | 219 | 1.48 |
| C_5 | 189 | 1.55 |

Residual is still positively correlated with speed, but C_7 (133cm/s, 1.05) is clearly worse than C_9 (124cm/s, 0.43),
indicating **there are factors beyond speed intrinsic to the body**. Both are quadrupeds with very different leg lengths
(C_7 102cm / C_9 191cm).

## V. Next steps

1. Re-examine the relationship between "leg length / stride ratio" and residual with the corrected environment —
   C_7 and C_9 are both quadrupeds, similar speed, residuals differ by 2.4×, this is the cleanest comparison.
2. All earlier intermediate conclusions based on the wrong environment (some numbers from Rounds 64, 65)
   need to be replaced with the retested values in this section.

---

# Round 7 (2026-11-01): Canal water surface material is debug magenta

(The mainline temporarily switches from gait to scene assets, handling the user feedback "the canal texture looks wrong".)

## I. Localization process

Using the `-ScenicCam` global camera position plus crop-and-zoom, confirmed the canal is the long trough in the middle of the frame.
Zooming in revealed two things:

1. The canal edge is a light gray thin line — this is actually normal (sampled value `(59,61,77)`, dark gray-blue),
   the earlier impression of "white edge with no texture" was an optical illusion of zoom interpolation;
2. **The water surface inside the canal is almost black**, in clear contrast to the dark green venom pool next to it.
   Sampling only shows scattered cyan points `(42,69,92)`, not reading like liquid.

The real defect is point 2.

## II. Root cause

`ue/Scripts/probe_gc.py` queries the GeometryCache actors in the level:

```
actor=GeoCacheWater_Coolant cls=GeometryCacheActor loc=(450,300,2) scale=(138,178,11)
   mat0=M_Diag_Magenta                                    ← debug placeholder material
```

The canal water surface is an Alembic GeometryCache (`flip_channel_full`),
and its material remained **`M_Diag_Magenta`** (diagnostic magenta), never replaced with
the real water material `M_GeoCache_Water`.

A blocking point was also fixed along the way: `c2()` in `ue/Scripts/make_gc_water.py`
used `set_editor_property("constant", Vector2D(...))`,
but UE 5.8's `MaterialExpressionConstant2Vector` only exposes two floats `r` / `g`,
so the script never ran (this is probably why the material was never assigned).

```python
# Before fix (throws Failed to find property 'constant')
n.set_editor_property("constant", unreal.Vector2D(x, y))
# After fix
n.set_editor_property("r", float(x))
n.set_editor_property("g", float(y))
```

## III. Fix

Rerun `make_gc_water.py`, all three steps succeed:

```
[gcwater] material M_GeoCache_Water rebuilt
[gcwater] written to asset materials
[gcwater] material assigned to GeoCacheWater_Coolant
```

Note the comment in the script (lesson from Round 31):
**it must be written into the GeometryCache asset's `materials` array**,
the component-level `set_material` is only a runtime override and reverts to WorldGridMaterial on level reload.

## IV. Verification

- After the fix the canal displays cyan-blue coolant with shimmering detail, clearly distinguished from the dark green venom pool;
- **Retest after restarting the process**: in a new process (not the same session) the canal region still has 8% cyan-blue pixels,
  confirming the material is persisted to the asset, not a runtime override.
- The pool (`M_Basin_Concrete`) and surrounding scene objects are unaffected.

## V. Two incidental changes (kept)

During investigation two UV density issues on the pool wall top faces were also found and corrected:

- `ue/Source/RobotGame/Private/RobotBasin.cpp`
  - Rectangular canal `AddTop()`: V changed from `T/100` (only 0.28 periods across 28cm width) to `T/12`
  - Circular pool `AddTop()`: similarly normalized to one period per 12cm
- `ue/Scripts/spawn_basins.py`
  - Detail texture tiling 6.0 → 1.5 (mesh UV in meters; the old value repeated 45 times along the 7.6m canal length,
    period too fine to see any texture)

These two are positive for current visual quality (concrete grain visible on narrow edges), but are **not** the root cause of the black canal,
the root cause was the material not being replaced.

## VI. New probe scripts

- `ue/Scripts/probe_basin_mat.py` / `probe_basin_mat2.py`: material and texture asset checks
- `ue/Scripts/probe_basin_actors.py`: pool/canal actors' components and material assignments
- `ue/Scripts/probe_gc.py`: GeometryCache actors in the level and their materials (the key tool that located the problem this round)

---

# Round 67 (2026-11-02): Overturning the premise of "enemy sliding"

## I. Conclusion first

Re-measured using **macro net displacement**:

| Entity | Foot net displacement | Body net displacement | Net sliding |
| --- | --- | --- | --- |
| C_5 | 56.6cm | 57.4cm | **−3 cm/s** |
| C_7 | 40.1cm | 40.4cm | **−1 cm/s** |
| C_9 | 38.0cm | 37.7cm | **1 cm/s** |

**The average displacement of the support foot is almost exactly equal to the body advance, systematic sliding is within ±3cm/s (essentially zero).**

All the "enemy sliding 50~100cm/s", "residual 0.4~1.5cm/frame" reported in the previous seven rounds
**were all artifacts of a wrong frame-by-frame differencing methodology**, not real gait defects.

## II. Where it went wrong: the frame-by-frame differencing methodology was always polluted

This round every methodology point was checked individually, and four independent sources of pollution were found in frame-by-frame differencing:

1. **Cross-frame**: `S.PrevFL` is the foot position from the "last **accumulation** frame", not the previous frame.
   Stance-phase statistics skip swing frames in between, so `FLw - PrevFL` spans several frames at once,
   and comparing it to a single-frame `Speed·Dt` necessarily gives a several-fold "residual".
2. **Phase wraparound**: `dPhase` spans the swing phase, and the increment from `FindDeltaAngleDegrees` includes swing advance,
   inflating `phaseRatio` to 1.94 (≈1/0.5, exactly the reciprocal of the stance-phase fraction).
3. **Deadlock**: the `DbgPrevTime` update is written inside the criterion-check block that requires it to hold,
   forming "criterion requires last update ↔ last update blocked by criterion", so the difference is always 0.
4. **Cross-instance/cross-phase windows**: when `footStep` and `expect` span different time ranges, the residual is meaningless.

After fixing 1~3, `dFwdErr` stabilizes at **0.000**: the backward `Fwd` amount is exactly equal to `Speed·Dt`,
**the compensation itself is precise**. This is consistent with the macro conclusion.

## III. Why free-walking `netSlip` is still 169~235cm/s

It is not sliding. Look at that free-walking data set:

```
C_5  footNet=61.8cm  compNet=9.1cm   netSlip=169cm/s   (within 0.31s)
```

`compNet 9.1cm / 0.31s ≈ 29cm/s`, while C_5's speed is 189cm/s.

**The body net-moved only 9cm in 0.31 seconds, yet swings its legs at the rhythm of 189cm/s.**
The reason is that under `-WalkForever` enemies move back and forth around the player (chase / strafe / back off),
net displacement is near zero, while `GetVelocity()` gives instantaneous speed.

**This is "animation speed not matching actual movement", not "support foot slipping".**

## IV. What this means

- The biped / quadruped `Fwd` linear backward compensation is correct, no need to change it further.
- All the changes made in earlier rounds in this direction (cadence 12→20, `Duty` overlap, `Bob` stripping,
  `Sway` suppression, skeleton tilt, bone-segment balancing) **were optimizing a problem that does not exist**.
  Of these, cadence 12→20 is kept (macroscopically harmless, feels more responsive instantaneously), the reverted ones stay reverted.
- What should really be investigated is a different visual problem: **when enemies move back and forth, the leg swing rhythm decouples from actual displacement**,
  looking like "paddling legs in place". This is a coupling problem between AI movement patterns and procedural gait,
  a different defect from support-foot slipping.

## V. New tools this round

- `[MacroSlip]` log: window-level macro measure, completely independent of frame-by-frame differencing
  ```
  [MacroSlip] owner=.. sec=0.31 footNet=41.7cm compNet=41.7cm netSlip=0cm/s
  ```
- `[GapProbe]`: actual values of the continuity criterion, used to investigate cross-frame problems

## VI. Methodology lesson (second time of the same kind)

Round 66 had just summarized "per-instance state written as function-local static",
and this round stepped on "inconsistent sampling methodology in frame-by-frame differencing".

**For any metric that "takes the difference of two samples", you must first confirm:**
1. The two samples are separated by **exactly** one time step;
2. No cross-instance, cross-phase, or cross-support-segment mixing has crept in;
3. The criterion itself does not depend on the result it is judging.

If you cannot, use a **window macro quantity** (record once at each end, net displacement ÷ time),
which is completely insensitive to sampling points. This round obtained a trustworthy conclusion precisely thanks to it.

---

# Round 68 (2026-11-02): Gait follows actual displacement + quadruped knee reflex correction

## I. First, confirm last round's conclusion is not overturned

With the corrected macro measure (body displacement also projected onto the **same forward axis**; previously world X was wrongly used,
which made "normal forward movement" count as huge negative sliding when enemies walked in arbitrary directions under `-WalkForever`):

```
[MacroSlip] owner=.. footNet=52.2cm compNet=52.1cm netSlip=0cm/s
[MacroSlip] owner=.. footNet=38.4cm compNet=37.5cm netSlip=3cm/s
```

Two runs, 157 windows, median `|netSlip|` **0~19cm/s**.
**The support foot has no systematic slipping, Round 67's conclusion stands.**

## II. Change 1: Gait speed follows actual displacement (without it, "paddling in place")

When enemy AI moves, instantaneous speed is high but net displacement is small. Originally gait swung legs at full speed based on `GetVelocity()`,
while the body did not go far, giving the visual of legs spinning in place.

```cpp
// New: actual displacement speed = real displacement rate of the component position (first-order low-pass smoothed)
S.ActualSpeed = FMath::FInterpTo(S.ActualSpeed, Actual, Dt, 10.f);

// Gait speed takes the smaller of the two (only caps, never boosts)
const float SpeedForGait = FMath::Min(Speed, S.ActualSpeed * 1.25f + 8.f);
```

Measured comparison (`-NoActualGate` disables the cap for A/B comparison):

| Entity | Cap off \|netSlip\| | Cap on |
| --- | --- | --- |
| C_5 | 25 | **12** |
| C_7 | 37 | **28** |
| C_8 | 12 | 14 |
| C_9 | 15 | **7** |

Three improved, C_8 flat. Magnitude small but direction correct, kept.

## III. Change 2: Quadruped knee reflex (main finding of this round)

Using `-EnemyCam` close-up to inspect the rest pose revealed that **the hauler's legs are clearly reflexed**:
thigh pointing forward-down, shin pointing backward-down, knee folded into a near-90° sharp angle, sole not flat on the ground.
At rest `MoveBlend=0`, `Fwd/Lift` all 0, so this is not a gait problem, it is **skeleton geometry**.

`[LegShape]` diagnosis confirms:

```
thigh=12  V1=(54.0, 0, -55.0) |V1|=77.1  th1=44.5
          V2=(-47.3, 0, -47.1) |V2|=66.8 th2=-45.1   ← included angle near 90°
```

### Root cause

In `tools/blender/build_enemies.py` the knee offset is defined by **body width D**:

```python
kneeY = dy + (D * 0.36 if tag == "B" else -D * 0.36)   # D≈2.9 → offset 1.04m
```

But the leg's vertical drop is only about 1.05m. The offset is almost equal to the whole leg height,
hip/knee/ankle form an isosceles triangle, the knee is pushed to an extreme outside → reflex sharp angle.

### Fix

Change the offset to be proportional to the leg's **vertical drop** (0.30×) instead of body width:

```python
_hip_z = z - Rr * 0.55
_drop = _hip_z - 0.075
knee_off = _drop * 0.30
kneeY = dy + (knee_off if tag == "B" else -knee_off)
```

### Effect

| Leg | th1 / th2 before | th1 / th2 after |
| --- | --- | --- |
| C_5 front leg | +44.5° / −45.1° | **+30.7° / −28.7°** |
| C_5 rear leg | −44.5° / +52.2° | **−30.7° / +39.8°** |

Included angle narrowed from about 90° to about 60°, close-up screenshots confirm natural forward knee flexion, no more reflex.

## IV. Not yet resolved

- **Sole standing upright**: in close-up the sole stands tilted, not flat on the ground.
  Related to `FootPitch`'s rest baseline (`Rest.Theta2Deg` compensation), handled next round.
- The colossus (C_9) knee offset is still fixed 0.55m (hip-ankle drop 2.06m, ratio 0.27 acceptable),
  but `knee_z=0.92` fixed causes thigh `|V1|=142` / shin `|V2|=68` severe imbalance.
  Only the hauler was changed this round, the colossus to be handled together later.

## V. New diagnostics

- `[LegShape]` (`-DebugLegShape`): prints each leg's `V1/V2` vectors, lengths and `th1/th2`,
  the key tool for locating knee reflex.
- `-NoActualGate`: disables "actual displacement cap", for A/B comparison.
- `[MacroSlip]` adds `footPath` (total distance the foot traveled within the window), to measure how busy the leg is.

---

# Round 69 (2026-11-02): Sole flat on the ground + leg bone cylinders truly tilted

This round handles two **directly observable, directly verifiable** visual defects (found in close-up last round).

## I. Sole standing upright → flat on the ground

### Root cause

In `SolveLeg` the foot bone angle is **incremental compensation**:

```cpp
P.Ankle = D2 + P.Ankle;   // only cancels the shin's rotation + a bit of pitch
```

It only guarantees "the foot-shin angle is unchanged", but the shin itself swings with gait,
so the sole's **world pitch** changes along with it — in the running game the foot stands tilted.

### Fix

Add `SetBoneCompRot()`: directly set a bone's **component-space orientation** to the target value (not based on current value),
then use it to pin the foot bone to the **rest orientation**, only adding pitch on top:

```cpp
auto FixFootRot = [&](int32 FootIdx, float PitchDeg, bool bUse)
{
    const FMechBoneRest* R = S.Rest.Find(Ref.GetBoneName(FootIdx));
    const FQuat Pitch(AxisRight, FMath::DegreesToRadians(PitchDeg));
    SetBoneCompRot(Ctx, FootIdx, (R->CompRot * Pitch).GetNormalized());
};
```

Also change the semantics of `P.Ankle` to "only handles pitch", no longer adding `D2`.

### Effect

Close-up screenshots confirm: all four legs' soles are horizontal and flat on the ground, toes pointing forward.

## II. Leg bone cylinder vertical ↔ bone tilted → folded angle at knee

### Root cause

In `build_enemies.py` the thigh/shin cylinders are built by **vertical length**, with no rotation:

```python
R.cyl("leg_shin_..", 0.072, abs(knee_z - ankle_z), (hx, (kneeY + dy)*0.5, ...))
```

But the knee's Y position (`kneeY`) differs from the ankle's Y (`dy`) — both ends of the cylinder fail to meet the joints,
visually folding a sharp angle at the knee ("O-shaped legs").

### Fix

Cylinder length takes the **three-dimensional distance**, and rotate around X axis by the actual tilt:

```python
_dv = math.sqrt((kneeY - dy)**2 + (knee_z - ankle_z)**2)
_tilt = math.atan2(kneeY - dy, knee_z - ankle_z)
R.cyl(..., _dv, (...), rot=(_tilt, 0, 0), ...)
```

Same for the thigh.

### Effect (`[LegShape]` measured)

| Leg | th1 / th2 before | th1 / th2 after | Included angle |
| --- | --- | --- | --- |
| C_5 front leg | +44.5° / −45.1° | **+19.6° / −15.2°** | 90° → 35° |
| C_5 rear leg | −44.5° / +52.2° | **−19.6° / +29.2°** | 97° → 49° |

Close-up screenshots confirm: the colossus's legs form a natural "<" shape with flexed knee, thigh tilted forward,
shin slanting back-down, sole flat on the ground, O-shaped legs gone.

## III. Regression verification

The sole and leg-shape changes do not touch gait logic; regression confirms no degradation:

| Entity | \|netSlip\| median |
| --- | --- |
| Player | 0 |
| C_5 | 17 |
| C_7 | 33 |
| C_8 | 14 |
| C_9 | 17 |

(157 windows, in cm/s, still within the "no systematic sliding" range.)

## IV. New tools

- `SetBoneCompRot()`: set a bone's component-space orientation to an absolute value, for absolute constraints like "the sole must be horizontal"
- `-DebugLegShape` additionally outputs `ank` (foot bone index), to help locate the foot bone

## V. Next steps

The colossus (C_9) knee offset is still fixed 0.55m, `knee_z=0.92` hard-coded,
causing thigh `|V1|=142` / shin `|V2|=68` severe imbalance (C_9 in the table of this section was not changed).
Next step: change it too to "proportional to the leg's vertical drop".

---

# Round 70 (2026-11-02): Colossus (C_9) Leg Bones Unified Under One Geometry Rule

## I. Background

Round 69 fixed the hauler's legs, but the colossus's geometry was still set "by feel,"
with three parameters hard-coded and inconsistent with the hauler:

| Parameter | Colossus old value | Problem |
| --- | --- | --- |
| Knee forward/back offset | Fixed `0.55m` | Unrelated to the leg's vertical drop (2.06m); the ratio is hit-or-miss |
| `knee_z` | Fixed `0.92` | Hip 2.23m, ankle 0.17m, yet the knee is stuck at 0.92 → thigh 142cm / shin 68cm, **2:1** |
| Thigh/shin cylinders | Built by vertical length, not rotated | Can't connect to the joint at the knee, folding into a sharp angle |

## II. Changes

Unified under the same rule already validated on the hauler:

```python
_drop = hip_z - ankle_z          # leg's vertical drop
knee_off = _drop * 0.18          # knee offset = 18% of the drop
knee_z = (hip_z + ankle_z) * 0.5 # knee height = hip-ankle midpoint → two segments nearly equal length

# cylinder length uses 3D distance, rotate around the X axis by the tilt angle
_dv = math.sqrt((kneeY - dy)**2 + (knee_z - ankle_z)**2)
_tilt = math.atan2(kneeY - dy, knee_z - ankle_z)
R.cyl(..., _dv, (...), rot=(_tilt, 0, 0), ...)
```

## III. Effect (`[LegShape]` measurements)

| Metric | Before | After |
| --- | --- | --- |
| Thigh `\|V1\|` | 142.1cm | **109.5cm** |
| `th1` / `th2` | +22.8° / −30.0° | **+19.8° / −10.5°** |

The imbalance in the two bone lengths shrank from 2:1 to nearly 1:1, and the knee angle from 53° to 30°, the same order of magnitude as the hauler (19.6°/15.2°).

Full-scene observation + zoomed screenshots confirm: **the colossus's four legs have clear structure, natural knee joints, and foot soles flat on the ground**,
consistent with the hauler's leg shape; the earlier "thick, long thighs and tiny shins" is gone.

## IV. Regression verification

Foot sole and leg shape changes don't touch gait logic; regression confirmed no degradation (2 runs, 157 windows):

| Entity | Median `\|netSlip\|` |
| --- | --- |
| Player | 0 |
| C_5 | 21 |
| C_7 | 28 |
| C_8 | 13 |
| C_9 | 15 |

## V. Current leg geometry state

The legs of all three quadruped/biped enemies now share one rule:

- Knee offset = 0.18 × the vertical drop
- Knee height = hip-ankle midpoint
- Thigh/shin cylinders use 3D length and rotate by the real tilt angle
- Foot sole orientation is pinned to the rest orientation by `FixFootRot` (only pitch is added)

Parameters are concentrated in two loops in `build_enemies.py` (hauler / colossus);
future tuning only needs to change the `knee_off` coefficient.

## VI. Next steps

Leg geometry has converged; the remaining observable issue is **the match between gait rhythm and movement**:
when enemy AI repositions (chasing / strafing / turning in place), the leg swing amplitude still follows a near-full-speed rhythm,
rather than shrinking with actual net displacement. The "actual displacement cap" added in round 68 only fixed speed;
swing amplitude (`Stride`) and foot lift height (`Lift`) haven't shrunk along with it.

---

# Round 71 (2026-11-02): Fixing "Walking in Midair"

User feedback: the robot's feet float in the air when walking. In-game screenshots confirmed the guard (C_5) had both feet about one foot-height off the ground.

## I. Root cause: the legs are "straight," with no knee-bend margin

The `[LegGeom]` diagnostic (added this round) exposed the contradiction:

```
C_5   LegLen=111.3  L1=70.0  L2=41.6   →  L1+L2 = 111.6
```

**The straight-line distance from hip to ankle (111.3) is almost equal to the sum of the two bone lengths (111.6)**, differing by 0.3cm.
That means the leg is **completely straight** at rest, and any swing lifts the foot off the ground.

But in the two rounds before this, I only changed the cylinders' **visual tilt** (to make them look bent),
without changing the joints' actual positions — so "the leg looks bent visually but is straight in the skeleton," and the moment
the IK moves, the foot can't reach the ground.

### Why this wasn't exposed before

In rounds 69/70 I verified with **close-up screenshots**, when enemies were mostly idling in place,
`MoveBlend≈0`, legs back at rest position, looked fine. As soon as they actually walked, the problem showed.

**Lesson: static screenshot verification isn't enough; you must look at the walking state.**

## II. Fix: lower the hip so the leg really bends at the knee

The three modeling functions (hauler / colossus / guard) were uniformly changed to:

```python
_full = hip height when fully straight - ankle height
hip_z = ankle_height + _full * 0.92      # lower the hip 8%, leave real knee-bend margin
knee_z = (hip_z + ankle_height) * 0.5    # knee height centered, two segments nearly equal
knee_off = _full * 0.10          # knee offset forward, consistent direction
```

At the same time **the hip ball/hip ring height must follow `hip_z`**, otherwise the cylinder ends won't connect to the joints
(the guard's cylinder also referenced the old variable `hz2`, changed as well).

## III. Effect (`[LegGeom]` measurements)

| Entity | Before LegLen / L1+L2 | After | Margin |
| --- | --- | --- | --- |
| C_5 (guard) | 111.3 / 111.6 (0.3) | **101.9 / 102.9** | +1.0cm |
| C_7 (hauler) | 102.4 / 109.3 | **93.7 / 99.2** | +5.5cm |
| C_8 (weather) | 128.7 / 128.7 (0.0) | **118.0 / 119.9** | +1.9cm |
| C_9 (colossus) | 191.2 / 197.9 | **174.8 / 182.2** | +7.4cm |

Screenshots confirm: all enemy bodies have **foot soles firmly planted on the ground**, floating eliminated.

## IV. Regression

| Entity | Median `\|netSlip\|` |
| --- | --- |
| Player | 0 |
| C_5 | 18 |
| C_7 | 23 |
| C_8 | 5 |
| C_9 | 12 |

No degradation (C_8 even slightly improved).

## V. Diagnostic added this round

`[LegGeom]` (`-DebugLegShape`): prints `LegLen / L1 / L2 / DMax / RestDrop / SupportH / Bob`.
This is the key indicator for judging "whether the leg has knee-bend margin" — **`LegLen ≈ L1+L2` means the leg is straight and will definitely float**.
In the future, when changing leg geometry, look at this line first.

## VI. Two things to remember

1. **Visual tilt ≠ skeletal knee bend**. Changing a cylinder's `rot` only affects appearance, not IK.
   To really bend the leg, the hip-ankle distance must be less than `L1+L2`.
2. **Verification must look at the walking state**. Static screenshots hide problems like "straight legs" that only show up in motion.

---

# Round 72 (2026-11-02): Swing Amplitude and Foot Lift Also Follow Actual Displacement

Round 68 only capped **cadence/stride** (`Omega` / `Stride`) by actual displacement,
but **swing amplitude** (`MoveBlend`) and **foot lift height** (`Lift`) were still computed from instantaneous `SpeedRatio`.

## I. Problem

When the enemy turns in place / moves back and forth:

- Instantaneous speed is high → `MoveBlend ≈ 1` → legs swing at full amplitude, foot lifted high;
- but the body's net displacement is near zero → it looks like "the legs are rowing in place."

`MoveBlend` is the master switch for swing amplitude; since it didn't shrink, most of the effect of capping `Stride` was canceled out.

## II. Changes

Added `RatioForBlend` (the ratio of actual displacement speed), and unified three places to the same basis:

```cpp
const float RatioForBlend = Clamp(S.ActualSpeed / MaxSpeed, 0, 1);
const float MoveBlend = SmoothStep(Clamp((RatioForBlend - 0.02f) / 0.16f, 0, 1));
const float H = (6.f + 16.f * RatioForBlend) * MoveBlend;   // foot lift height
```

Also fixed a counterproductive spot:

```cpp
// when recomputing cadence after the stride cap was exceeded, originally used instantaneous Speed, which reverted the rhythm to full speed
Omega = SpeedForGait * Duty * 2.f * PI / Stride;   // changed to the capped speed
```

## III. A/B measurements (`-NoActualBlend` can disable)

Metric `footPath` = total distance the foot travels within a window, used to measure "how busy the legs are."

| Entity | Cap off | Cap on | Change |
| --- | --- | --- | --- |
| C_5 | 61.5 | **56.8** | −8% |
| C_7 | 51.2 | **41.2** | −20% |
| C_8 | 73.7 | **60.2** | −18% |
| C_9 | 49.4 | **41.2** | −17% |

**Total foot travel dropped ~16% on average**, and rowing-in-place was markedly reduced.
Sliding was checked at the same time with no degradation (C_8 dropped from 13 to 5, others unchanged).

## IV. Final regression (2 runs / 157 windows)

| Entity | Median `\|netSlip\|` | Median footPath |
| --- | --- | --- |
| Player | 0 | 0 |
| C_5 | 15 | 59.9 |
| C_7 | 30 | 53.7 |
| C_8 | 14 | 60.6 |
| C_9 | 11 | 43.2 |

## V. New switches

- `-NoActualBlend`: disable this round's changes, for A/B comparison
- `-NoActualGate` (round 68): disable speed capping

## VI. Current progress summary

Leg-related observable issues, in fix order:

1. Vertical skeleton vs. knee forward/back offset → thigh bone points to the knee ball (round 63)
2. Quadruped foot arch folded back 90° → knee offset proportional to leg height (round 68)
3. Foot sole standing upright → absolute orientation constraint `FixFootRot` (round 69)
4. Leg bone cylinders don't meet joints → cylinders by 3D length + tilt (rounds 69/70)
5. **Walking in midair** → lower the hip so the leg truly bends (round 71)
6. **Rowing legs in place** → swing/lift follow actual displacement (this round)

Still to do: the pitch curve of the foot sole during the **swing phase** (currently a constant offset),
and finer foot-landing cushioning (`ImpactOf`) linked to net displacement.

---

# Round 73 (2026-11-02): Eliminating Double Lowering + Foot-Landing Cushioning Linked In

## I. Discovery: the program layer and asset layer are both lowering the pelvis

Round 71 lowered the hip by 8% in the **asset layer** so the leg truly bends at the knee.
But the program still had a "sinking compensation for straight legs" (added around round 30-something), with the condition:

```cpp
if (DropRatio >= 0.99f) { Sink = 0.f; }   // only skip when nearly fully straight
```

After the asset was lowered, `DropRatio` became **about 0.94**, no longer satisfying `>= 0.99`,
so this compensation **started working again** — the asset had already lowered once, the program lowered again, the pelvis was lowered twice.

Changed to judge by the real knee-bend margin:

```cpp
if (DropRatio <= 0.95f) { Sink = 0.f; }   // if the margin is already enough, don't compensate
```

Measured `Bob` shrank from ±2cm to **±0.4cm** (C_8 from −0.2 → −0.0), pelvis back to a natural standing height.

## II. Foot-landing cushioning linked to actual displacement

Touchdown cushioning `ImpactOf` (press down another 1.2cm at the instant of landing) was originally unrelated to gait intensity,
so even when rowing in place / walking slowly it would "stomp down hard." Changed to multiply by `MoveBlend`:

```cpp
return FMath::Exp(-U * 9.f) * 1.2f * MoveBlend;
```

## III. Regression (2 runs / 157 windows)

| Entity | Median `\|netSlip\|` | Median footPath |
| --- | --- | --- |
| Player | 0 | 0 |
| C_5 | 15 | 55.5 |
| C_7 | 24 | 50.8 |
| C_8 | 5 | **37.6** |
| C_9 | 19 | 49.2 |

`footPath` dropped further than round 72 (C_8 60.6 → 37.6), no sliding degradation.

Screenshots confirm: foot soles land, knee joints bend naturally, no floating or folding back.

## IV. On the swing-phase pitch curve

Checked `P.Ankle`'s swing-phase curve (`Lerp(16°, -8°, SmoothStep(U))`),
applied as an absolute orientation via `FixFootRot`, works correctly; a close-up of the player walking confirms reasonable foot sole posture.
**No change this round** — the current amplitude (24° swing) hasn't caused visible problems,
so leave it alone until there's a clear benefit.

## V. Accumulated leg fixes

| # | Problem | Round |
| --- | --- | --- |
| 1 | Vertical skeleton vs. knee forward/back offset | 63 |
| 2 | Quadruped knee folded back 90° | 68 |
| 3 | Foot sole standing upright | 69 |
| 4 | Leg bone cylinders don't meet joints | 69/70 |
| 5 | Walking in midair | 71 |
| 6 | Rowing legs in place (swing/lift) | 72 |
| 7 | Program/asset double pelvis lowering | this round |

---

# Round 74 (2026-11-02): Feet Not on the Ground — Three Stacked Root Causes

User again reported "the robot still floats, its feet aren't on the ground." This round added the `[FootZ]` diagnostic (directly measuring the foot bone's world Z and IK reach distance), pinpointing three stacked root causes at once.

## I. Root cause 1: IK reach distance cut by 20% (main cause)

```cpp
d = FMath::Clamp(d, |L1-L2|+2, (L1 + L2) * 0.80f);
```

That `0.80` was added earlier "to leave a bend margin." But **the asset layer in round 71 already lowered the hip and made the leg truly bend at the knee**;
cutting another 20% of reach distance here means the leg can never extend to the target point.

Measured: target `d=118.5`, but `clamp=96.0` — the leg is stuck at 96cm, the foot pulled 23cm into midair.

After changing to `0.999f` (close to the real leg length), `clamp == d`, and the foot immediately lands:

| Entity | footL (rest) | Note |
| --- | --- | --- |
| C_7 | **16.4 (16.4)** | perfectly flush |
| C_8 | **12.3 (12.2)** | perfectly flush |
| C_5 | **18.6 (18.3)** | perfectly flush |
| Player | **31.8 (31.5)** | perfectly flush |

**Total IK clamping for all entities = 0** (first time in seven rounds).

## II. Root cause 2: program layer and asset layer both lowering the pelvis

`[LegGeom]` shows `Bob = -12 ~ -14cm` (pelvis lowered 12~14cm).
The source is the "sinking compensation for straight legs" — a piece of code written for **old assets** (legs completely straight).

The asset layer already lowered by 8% in round 71, so the program lowering once more is duplication. Last round I tried to skip it with
`DropRatio <= 0.95`, but **that condition is unreliable**: after the asset was lowered,
`LegLen` and `L1+L2` both shrank, so the ratio stayed near 1.0 and the condition never held.

This round **deleted the whole block**, `Bob` back to ±1cm.

## III. Root cause 3: `ImpactOf` multiplies `MoveBlend` twice

```cpp
return Exp(-U*9) * 1.2f * MoveBlend;      // already multiplied inside
Bob -= Max(...) * MoveBlend;               // multiplied again outside
```

Same mistake as round 61's "`MoveBlend` multiplied twice." Fixed.

## IV. Simultaneous fix: support height no longer rises and falls with stride

`LegSupportH` originally took `sqrt(DMax² − Fwd²)` unconditionally. With a stride of 30~50cm,
that value would drop from DMax to around 105, dragging the pelvis down 4~12cm — while the foot target hadn't moved.

Changed to "only lower when the leg truly can't reach":

```cpp
const float FwdAllow = sqrt(DMax² − RestDrop²);   // horizontal travel the knee-bend margin can cover
const float OverFwd = max(|Fwd| − FwdAllow, 0);
const float Target = (OverFwd > 0) ? max(NeedH, Floor) : RestDropBase;
```

## V. Regression

| Entity | Median `\|netSlip\|` | footPath | IK clamping |
| --- | --- | --- | --- |
| Player | 0 | 0 | **0** |
| C_5 | 22 | 65.4 | **0** |
| C_7 | 32 | 60.5 | **0** |
| C_8 | 12 | 69.2 | **0** |
| C_9 | 20 | 53.2 | **0** |

Screenshots confirm: the player's both foot soles completely flat on the ground, no gap between sole and floor, knee joints bending naturally.

## VI. Root-cause chain

This time it was **three independent defects stacked**, any one of which alone could cause floating:

1. IK cap 0.80 → leg can't reach the target (biggest impact, 23cm)
2. Program layer double-lowering the pelvis → pelvis 12~14cm below normal height
3. `ImpactOf` double multiplication → extra jitter

And they masked each other: last round I only fixed the condition of #2 (and didn't fix it right),
so it looked like "nothing changed."

## VII. Lesson

**Verification must measure absolute quantities, not just look at screenshots.** `[FootZ]` gives
a comparison of `footL` vs `rest`, so you can see at a glance how far the foot is off the ground; a screenshot at a distance
simply can't distinguish 20cm of floating.

Also: **before changing a parameter, first confirm why it was set that way in the first place**.
`0.80` was a patch for "old assets' legs too straight"; once the asset was fixed, it became pure damage.

---

# Round 75 (2026-11-02): Enemy Models "Incomplete" — Fixing Part by Part Against Criteria

User feedback: "the models of all the robots are incomplete in the final game; fix them part by part."

## I. First establish objective criteria

The previous few rounds went in circles on the same issue — "look at screenshot → feel something's wrong → change → screenshot again"
(mistaking the weather machine's radar dome for the hauler's cargo bay, mistaking design intent for a defect).

This round I first wrote criteria: `tools/blender/audit_legs.py`, which only checks **whether geometry connects end to end**:

    A. thigh endpoint ≈ knee-ball center
    B. shin endpoint ≈ knee-ball center
    C. shin far end ≈ foot sole center (horizontal plane)
    D. foot bottom ≈ z=0

If any item exceeds 6cm, it's "disconnected." **No eyeballing, no guessing.**

## II. Root cause: manually computing "midpoint + tilt + length" is bound to go wrong

The legs of all five bodies are assembled with

    cyl(name, radius, 3D distance, (midpoint of the two ends), rot=(atan2(...), 0, 0))

This style requires four manual computations to be correct simultaneously: length, midpoint, the tilt **sign**, and the tilt **numerator**.

The shin is the most typical case: it runs from the **knee** to the **ankle**, the opposite direction from the thigh, so the tilt numerator
should be `dy - kneeY`; but all five were written as `kneeY - dy` (same sign as the thigh),
flinging the ankle end to the knee side — **the foot sole and shin were disconnected 16~20cm in-game**.

Changing the sign alone treats the symptom. **The root fix is to make "build a cylinder between two points" a function**:

    robotlib.cyl_between(name, p1, p2, radius, ...)

Given two real joint positions, length/orientation/midpoint are all computed by geometry and can't fail to line up.
All 10 thigh/shin spots across the five bodies were switched to it.

## III. Per-body fix list

| Body | Defect | Fix |
| --- | --- | --- |
| Gardener | Head has its bottom face cut off by `cut_below`, hanging 8cm above the neck ball | Make head a full ellipsoid and lower it |
| Gardener | Forearm stops at the elbow; watering can/pruning shears hang 9cm outside the arm | Extend forearm to the hand, add wrist ball |
| Gardener | Spout pokes out from under the can bottom (floating hook) | Make spout protrude from the can's side wall at the mouth |
| Gardener | Shin 0.052 vs knee ball 0.070, reads as a "thin stick" | Thicken shin to 0.062 |
| Weather | Same head problem as the gardener | Same as above |
| Weather | Radar dome negative tilt → cap face turns toward the viewer (black hole) | Full dome, raised above the head |
| Weather | Nothing at the end of the arms | Add sensor module + probe |
| Weather | Leg lengths hard-coded (0.58/0.48), don't match joints | Change to compute from the drop |
| Guard | Breastplate center seam falls inside the breastplate, lower end sticks out ("floating black stick") | Flush against the breastplate front surface, shorten |
| Guard | Left arm stops at the elbow | Add forearm + two-finger gripper |
| Colossus | Forearm goes straight into a trumpet mouth ("disc") | Add wrist ball + gun body + guard ring + muzzle |
| Colossus | Foot block 0.62 wide vs leg diameter 0.47 (foot unreadable) | Enlarge to 0.86×1.24, foot bottom still at 0 |
| Colossus | Foot block shifted forward 16cm, leg axis doesn't coincide with the load point | Center foot block on the ankle, let toes handle forward reach |
| Colossus | Waist ring radius 0.72, wider than the pelvis ("big plate") | Shrink to 0.16 |
| Hauler | Cargo cylinder too low and too large, front reduced to one big disc | Raise (1.42→1.58) + flatten (0.47→0.40) |
| Hauler | Knee height hard-coded `z - Rr*0.55 - 0.55`, misaligns when z/Rr changes | Take the hip-ankle midpoint instead |
| All | `cut_below` cap faces have no UV, normal direction indeterminate | Add UV + per-face normal correction + triangulation |

## IV. Three hidden pitfalls of `cut_below` (robotlib)

    Old implementation: delete faces → holes_fill to seal

1. The cap face has **no UV** — in UE it samples a single point of the texture, rendering as a flat color block ("bowl bottom");
2. `holes_fill` normal direction is indeterminate — under UE single-sided rendering, the inside of the hollow shell shows;
3. Cut edges leave stray vertices — LOD generation errors.

Changed to: delete vertices → seal → **correct per-face normals by "face center relative to sphere center"** (cap faces always face down)
→ triangulate → add cylindrical UV.

## V. Verification

`audit_legs.py` results (all legs):

    hauler   LF/LB/RF/RB   OK
    colossus L1/L2/R1/R2   OK
    gardener L/R           OK
    weather  L/R           OK
    guard    L/R           OK

UE-side `[LegGeom]` (slack = (L1+L2) − LegLen):

| Entity | L1+L2 | LegLen | slack |
| --- | --- | --- | --- |
| Player | 104.0 | 104.0 | 0.0 |
| C_5 | 102.9 | 101.9 | 1.1 |
| C_6 | 90.0 | 90.0 | 0.0 |
| C_7 | 118.6 | 111.9 | 6.7 |
| C_8 | 119.9 | 118.0 | 1.9 |
| C_9 | 176.7 | 166.3 | 10.4 |

`[FootZ]` support-foot deviation: player 0.23 / C_5 0.46 / C_7 0.17 / C_8 0.33 cm,
IK clamp counts all 0. Walking screenshots confirm legs and feet complete, support foot on the ground.

## VI. Lesson

**"Looks wrong" is not a criterion for a defect.** This round I misjudged three things as defects:
the weather machine's radar dome (designed to be "a dome bigger than the head"), the hauler's cargo cylinder (it's supposed to be a cylinder),
and the colossus's forward-pointing toe (reasonable). The genuinely disconnected legs, conversely, were invisible because of Blender's double-sided rendering,
and only surfaced once an endpoint criterion was written.

**Manually computed geometric quantities must be collapsed into functions.** The "midpoint + tilt + length" trio,
five bodies × two legs × two segments = 20 spots, each one capable of flipping the slope direction.
`cyl_between(p1, p2)` depends only on known joint coordinates, so this class of error disappears structurally.

## VII. Known unresolved

- The colossus C_9's `[FootZ]` support deviation is still 20cm, and the stat shows "swing max=0."
  Its `footPath=42cm` and slack=10.4 are both normal, indicating the gait is walking;
  the deviation source is that the leg pointed to by `IFootL` may often be in support stance among the four legs,
  and the statistic needs to be rewritten to "judge each leg individually," not done this round.

---

# Round 76 (2026-11-02): Chasing the Colossus's "Feet Not Landing" — Two Dead Codes + One Measurement Basis

Left over from the previous round: C_9's `[FootZ]` support deviation 20cm, and "swing max=0."

## I. Flaws in the diagnostic tool itself (fix the tool first)

`[FootZ]` only counted the L / R two legs. The BL / BR of quadrupeds (C_7 / C_9) were never checked.
Changed to per-leg counting (`DbgLegStanceDev[4]`, etc.), with a fixed order L/R/BL/BR.

Meanwhile the `-DebugFoot` throttle in `RobotEnemy.cpp` used a **function-local static**:

    static float LastFootLog = -100.f;

A static is shared across instances — once the first instance occupies the time window, the others never print.
Only C_5 actually output; C_7/C_9 showed nothing at all. **This is the third time hitting the same trap**
(round 60 foot-slide state, round 66 `-EnemyWalkConst`). Changed to a per-instance member.

Also the Chinese in the log was truncated after `owner=` (an encoding issue); changed to pure-ASCII `[FootH]`.

## II. Two dead codes (the real root causes)

### 1. `joint_tail` was never assigned in `auto_rig`

    if "leg_shin" in ob.name:
        seg_len[bone] = bmx[2] - bmn[2]
        break                       # ← before the assignment!
        joint_tail[bone] = (...)    # ← never executes

The fix described in the comment — "the lower end of the shin cylinder is the ankle joint position" — had been dead code all along.
Consequence: the shin bone's tail fell back to the bounding-box center, and the bone orientation didn't match the geometry's tilt.

### 2. The shin bone's "keep vertical" branch

    if bone.startswith("thigh"):
        nxt = joint_head.get(...)
    # shin stays vertical: ... tilt not implemented for now
    if nxt is not None: ...

For `shin`, `nxt` was always `None`, the tail pointed straight down — the stated reason was "tilt would cause tens of thousands of IK clamps,"
but that was **back when the leg geometry was still vertical**. The geometry is already tilted (`cyl_between`), so a still-vertical skeleton is misaligned with it.

## III. Symptoms and evidence

Added `[PosCmp]` to directly compare the two coordinate bases:

    ankleRef = accumulated by reference pose   ankleRun = accumulated by runtime array

| Entity | hipRef vs hipRun | ankleRef Z | ankleRun Z | diff |
| --- | --- | --- | --- | --- |
| Player | consistent | 30.0 | 30.3 | 0.3 |
| C_5 | consistent | 16.0 | 32.7 | **16.7** |
| C_7 | consistent | 14.0 | 32.9 | **18.9** |
| C_8 | consistent | 10.0 | 25.4 | **15.4** |
| C_9 | consistent | 41.0 | 54.4 | **13.4** |

**Hips completely consistent, only ankles inconsistent** — the error lands exactly on the shin segment.
The player's leg is a single bone (unaffected), enemies have three segments (affected).

After the fix:

| Entity | diff before | after |
| --- | --- | --- |
| C_5 | 16.7 | **1.5** |
| C_7 | 18.9 | **0.3** |
| C_8 | 15.4 | **1.6** |
| C_9 | 13.4 | **1.1** |

The remaining 1~1.6cm is a slight knee bend at rest, normal.

## IV. `L1/L2` measurement had to change too

After the shin cylinder was tilted, taking only the Z height underestimates bone length (a slanted segment's Z projection is shorter than its real length),
so `seg_len` was changed to the 3D diagonal. Verified with `[LenDbg]`: `L1 == |V1|`, `L2 == |V2|` all match.

## V. A failed attempt (recorded to avoid repeating)

I once tried "capping foot lift by knee-bend margin" (`H = min(H, slack*0.5)`),
reasoning that the colossus's slack was only 10cm while its foot lift was 22cm. Result:

- C_5 swing max 22.3 → **1.5** (almost no lift)
- C_7 22.0 → **3.8**
- C_9 unchanged (20cm)

Because healthy bodies have only 1~7cm of slack, capped to less than the required lift. **Rolled back immediately.**

## VI. Final verification: switch to a physical criterion

`[FootZ]` compares "foot bone origin vs its own rest value," and the colossus's foot bone origin is at the ankle while the foot block is large,
so this basis is inherently distorted for it. Switched to **lowest point of the animated-mesh bounding box vs ground raycast** (`[FootH] gap`):

| Entity | median foot-bottom clearance | max |
| --- | --- | --- |
| C_5 | **2.0** | 13.1 |
| C_6 | **2.1** | 20.9 |
| C_7 | **2.1** | 13.1 |
| C_8 | **2.1** | 12.9 |
| C_9 | **2.1** | 12.3 |

**All bodies median 2.0~2.1cm, consistent with the player** (2cm is the collision-body margin);
max 12~21cm is normal foot lift during the swing phase.

Walking screenshots confirm legs and feet complete, support foot on the ground, knees bending naturally.

## VII. Lesson

**The diagnostic tool itself must be diagnosed first.** What actually blocked this round wasn't engine code, but:
- statistics covering only two legs (half of quadrupeds missed);
- log throttling using a static shared across instances (only one output);
- the log truncating at Chinese characters (only the first half of the line visible).

Together these kept the illusion "only C_9 has a problem" alive for two rounds.

**The same class of error appeared a third time.** `static` cross-instance pollution has bitten three times
(rounds 60, 66, 76). Whenever adding any throttled/cached state in the future, first confirm whether it's a member variable.

---

# Round 77 (2026-11-02): Turning "Reached the Target or Not" Into a Metric — Discovering a Systematic Hind-Leg IK Deviation

## I. First fix a misleading metric

Last round `[FootZ]` reported "support deviation," with the basis "current foot Z − rest Z."
But this difference **shouldn't be zero during normal walking** — the purpose of IK is to place the foot at the target
(target = rest + Fwd + Lift). So C_9 constantly reported 20~25cm, while the physical criterion showed its feet
were always on the ground (2.1cm). **The metric itself was lying.**

Changed to measure the real **IK target error**: the Euclidean distance between the foot's actual component-space position and the IK target point.

## II. The new metric immediately exposed a never-before-seen problem

| Entity | Front-leg L/R target error | Hind legs BL/BR |
| --- | --- | --- |
| Player | 0.50 | — |
| C_5 | 0.51 | — |
| C_7 | **0.14** | **5.30** |
| C_8 | 0.29 | — |
| C_9 | **0.27** | **10.51** |

**Front-leg error is tiny, hind legs 20~80× larger.** The quadrupeds' hind-leg IK has a systematic deviation;
the feet aren't truly landing on the target points.

## III. Investigation (including two failed controlled experiments)

### Knee-bend direction

Quadruped front legs bend toward -Y at the knee, hind legs toward +Y (verified by reading the skeleton with `check_knee_dir.py`):

    thigh_L  hip Y=-0.78  knee Y=-1.36   front leg
    thigh_BL hip Y=+0.78  knee Y=+1.36   hind leg

The inverse-kinematics formula originally always assumed "knee bends forward" (θ1=base+α, θ2=θ1−K).
Added `BendSign` to auto-determine by the sign of `V1.X`, with front and hind legs each using their own sign.

### Experiment 1: flip the knee-bend angle — failed

    if (KneeSide >= 0)  P.Knee = -P.Knee;

The target error for that leg set went 0.13 → **150.9cm**. So the sign was already correct.

### Experiment 2: flip the other set — also failed

Error 10.5 → **157.5cm**. Neither set can be flipped.

**Conclusion: the knee-bend angle sign is correct for both sets; the 5~10cm hind-leg issue has another cause, not located this round.**

### Experiment 3: BendSign's effect on sliding — contrary to first impression

On the first single run I saw C_7 20→46, C_5 22→32, and thought BendSign was harmful.
A controlled comparison (off vs on, 15s each):

| Entity | off | on |
| --- | --- | --- |
| C_7 | 39 | **27** |
| C_8 | 16 | **2** |
| C_9 | 16 | **11** |

**On is actually better.** That "worse" result was single-run variance — another confirmation:
enemy sliding varies hugely between single runs; you must take the median over multiple runs.

## IV. Two times stepping into the same kind of pit

1. **`[Bend]` log time throttle**: this log is written inside `SolveLeg`, and `SolveLeg`
   is called once per each of the four legs — the throttle silences three legs, so you always see the last one,
   leading to the misjudgment "all legs' knees bend to the same side." Changed to "log once per leg."
2. **Diagnostics must cover all legs**: previously only L/R were counted, the other two legs of quadrupeds were completely unchecked.

## V. Regression (median of three runs)

| Entity | median sole clearance | netSlip ×3 | median | previous round |
| --- | --- | --- | --- | --- |
| C_5 | 2.1 | 22 / 14 / 26 | 22 | 22 |
| C_6 | 2.1 | 0 / 0 / 0 | 0 | 0 |
| C_7 | 2.1 | 36 / 22 / 36 | 36 | 20 |
| C_8 | 2.1 | 15 / 6 / 6 | **6** | 12 |
| C_9 | 2.1 | 9 / 10 / 7 | **9** | 19 |

**All bodies' soles 2.1cm off the ground (consistent with the player). C_8, C_9 improved, C_7 got worse.**

C_7's `footNet` swings wildly between 23~92cm per frame, while `compNet` is stable at 12~45 —
it's an unstable landing trajectory, not systematic sliding. Its knee-bend margin is only 6.7cm while the knee offset is 23cm,
so IK solving is unstable when the leg is near-straight. **The asset was not changed this round** (lowering the hip would lift the feet),
left as a candidate for the next round: increase the `knee_off` ratio to raise slack at the same time (measured k=0.36 can raise
slack from 10cm to 30cm).

## VI. Lesson

**The metric itself must be validated first.** "Support deviation" sounds reasonable, but its definition contradicts the purpose of IK,
so a correctly working system was reported as 20cm wrong. Once switched to "target error," the same system
immediately revealed its real problem (hind legs 10.5cm).

**Controlled experiments must run the full comparison.** If we'd trusted only the first single run of BendSign,
we'd have rolled back a real improvement (C_8 16→2, C_9 16→11) as a degradation.

---

# Round 78 (2026-11-02): Knee-Bend Margin → Landing Stability, and Correcting a Long-Standing Mix-Up

## I. First correct a long-standing error: C_8 is not the weather machine

`RobotEnemy.cpp`'s battlefield model table has only 5 models:

    C_5 = SK_Enemy_Guard
    C_6 = SK_Enemy_Patrol
    C_7 = SK_Enemy_Hauler
    C_8 = SK_Enemy_Gardener      ← not Weather
    C_9 = SK_Enemy_Colossus

**`SK_Enemy_Weather` isn't on the battlefield at all.** Last round I treated `C_8` as the weather machine,
spent ages tuning `weather()`'s `knee_off`, but runtime slack didn't budge (1.9cm),
and went off to check import caches, FBX timestamps, triangle counts — all circling around an asset that isn't even used.

Lesson: **before changing anything, confirm the asset is actually on the battlefield.** The model mapping table is right at the top of `RobotEnemy.cpp`,
one glance would do, yet it took a dozen-plus diagnostic steps to discover.

## II. This round's real improvement: add knee-bend margin to bodies whose legs are "nearly straight"

`slack = (L1+L2) − hip-ankle drop`, indicating how much further the leg can extend.
The closer it is to 0, the nearer IK is to a singularity, and the less stable the landing trajectory.

Slack before the change:

| Entity | slack |
| --- | --- |
| C_5 | 1.1 |
| C_7 | 6.7 |
| **C_8 (gardener)** | **1.9** |
| C_9 | 10.4 |

`knee_off` (the offset of the knee relative to the hip-ankle line) is the only quantity that can raise slack:
the greater the offset, the more bent the polyline, the longer `L1+L2`.

### Change

- Hauler `hauler`: `knee_off = _drop * 0.18` → **0.26** (slack 6.7 → 15.0)
- Gardener `gardener`: `knee_off = _full * 0.10` → **0.22** (slack 1.9 → 11.5)

Chose 0.22~0.26 rather than larger: 0.30 makes the thigh lean 33° forward, visibly bow-legged (already noted in a code comment).

## III. Controlled experiment (key: take the median over multiple runs)

Three independent groups, 5~7 runs each:

| Entity | A baseline (6 runs) | B k7=.26 only (7 runs) | C k7+k8=.22 (5 runs) |
| --- | --- | --- | --- |
| C_5 | 21.7 | 21.1 | 18.9 |
| C_6 | 0 | 0 | 0 |
| **C_7** | **29.6** | **22.6** | **22.7** |
| **C_8** | **8.3** | 13.7 | **7.6** |
| C_9 | 10.9 | 12.6 | 11.6 |

**C_7: 29.6 → 22.7 (−23%), two independent measurements 22.6 / 22.7 highly consistent, improvement reproducible.**

C_8 spiked to 13.7 in group B, looking like it was broken by some other change — but group C returned to 7.6
(below the 8.3 baseline). **Group B's 13.7 was run-to-run variance**, not causality.
Yet another example of "single runs aren't trustworthy."

## IV. Physical verification

| Entity | median sole clearance | max |
| --- | --- | --- |
| C_5 | 2.1 | 13.1 |
| C_6 | 2.1 | 24.1 |
| C_7 | 2.1 | 12.8 |
| C_8 | 2.1 | 12.1 |
| C_9 | 2.1 | 13.0 |

All 2.1cm (consistent with the player), max is swing-phase lift.

Screenshots confirm the gardener's legs now show a clear knee-bend arc, no longer straight thin rods.

## V. A diagnostic detour (recorded to avoid repeating)

Tried to judge whether the import took effect by "the asset's triangle count in UE":

- Blender reported `18818 tris`
- UE's asset registry reported `18723 tris`

So I concluded "the import didn't take effect," repeatedly re-imported, swapped FBXs, checked caches — wasted a long time.
**In fact UE re-triangulates by its own rules on import; the two numbers were never supposed to be equal.**
To judge whether an import took effect, use **business metrics** (`slack`, bone lengths), not triangle counts.

## VI. Next-step candidates

- C_9's slack is already 13.7, sliding 11.6 (second only to C_8's 7.6); raising `knee_off`
  to 0.26 could push slack to 27.6, but the benefit is unknown, not touched this round.
- C_5's slack is only 1.1, but it's biped, sliding 18.9, and uses the same skeleton class as the player;
  higher risk to change, needs separate evaluation.

---

# Round 79 (2026-11-02): Parts Floating in Air — Establish a Connectivity Criterion, Find Two Systematic Errors

User feedback: "some robots' parts are floating in the air, not connected together; maybe some parts are missing."

## I. First get the criterion right (this step took two detours)

### Detour 1: bounding-box nearest distance

The first version computed AABB distance for each pair of parts, concluding "colossus has 25 floating parts."
But AABB overestimates for tilted cylinders, and **gaps between parts are normal** (decorative blocks stuck on an ellipsoid aren't meant to be flush).
This criterion both misses and false-positives.

### Detour 2: mesh vertex nearest distance

The second version computed the shortest vertex-to-vertex distance, concluding "colossus 108/130 floating" — even more absurd,
because **two interpenetrating solids can have vertices far apart** (one inside the other).
"Farthest vertex gap" is an entirely irrelevant quantity (large parts always have far-apart points).

### Correct criterion: point-in-solid test + connected components

If a part has **at least one vertex inside another part**, they're considered physically connected
(using ray-casting parity to determine inside/outside). Then compute connected components; anything not in the main component is a "floating island."

This criterion correctly handles "interlocking" and directly answers "is the whole machine one object."

## II. First systematic error found: greeble used the wrong bounding box

`R.greeble()` sticks small parts onto the **bounding-box surface**, but was passed `(W, D, H)` —
while the body solid is an ellipsoid with dimensions only `(W*0.50, D*0.52, H*0.52)`.

**The bounding box is more than twice the solid, so all the small parts were stuck in thin air.**

All five bodies were affected:

| Body | greeble box | solid dimensions |
| --- | --- | --- |
| Patrol | `(R0*1.9, R0*2.0, R0*1.0)` | `(R0, R0*1.04, R0*0.90)` |
| Hauler | `(W, D, H*1.4)` | capsule `Rr × D*0.86` |
| Colossus | `(W, D, H)` | `(W*0.44, D*0.42, H*0.54)` |
| Gardener | `(W, D, H)` | `(W*0.50, D*0.52, H*0.52)` |
| Weather/Guard | `(W, D, H)` | `(W*0.50, D*0.54, H*0.52)` |

### Second systematic error: `cut_below` raised the torso's bottom

The torso is an ellipsoid with `cut_below=-0.42`, its bottom **cut flat and raised** to `z − 0.42·(H·0.52)`.
But the hip balls were positioned based on "the torso bottom," a difference of 24~31cm —
**both legs of the bipeds were hanging entirely below the torso**.

## III. Fix list

| Body | Break | Fix |
| --- | --- | --- |
| Colossus | torso-pelvis 60.5cm | add `chassis_spine` waist column |
| Colossus | torso-shoulder 39.3cm | add `shoulder_bridge_*` shoulder bridges |
| Colossus | pelvis-hip 20.5cm | add `leg_hipbridge_*` hip bridges |
| Colossus | torso-antenna 4.2cm | lower antenna start into the torso |
| Gardener | hip-torso 31.4cm | add `leg_hippost_*` hip posts |
| Gardener | shoulder/arm whole block | add `shoulder_bridge_*` |
| Guard | hip-torso 24.6cm | add `leg_hippost_*` |
| Weather | hip-torso | add `leg_hippost_*` |
| Hauler | hip-cargo bay 15.3cm | add `leg_hipbridge_*` |
| Hauler | side-mounted weapons, 10 parts whole | add `arm_mount_*` brackets |
| Patrol | hover ring whole group | lengthen spokes and pull inward |
| All | greeble floating | switch bounding box to the solid's real dimensions |

## IV. Verification: connected components

| Body | before main/total | after |
| --- | --- | --- |
| **Colossus** | 90 / 137 (36 islands) | **131 / 137** (3 islands) |
| **Gardener** | 25 / 60 | **58 / 62** |
| **Hauler** | 60 / 88 | **86 / 90** |
| **Guard** | 79 / 82 | **81 / 82** |
| **Patrol** | 33 / 44 | **35 / 44** |
| Weather | 75 / 83 | 75 / 83 |

Remaining islands are all parts that **should be independent by design**: wind cups (`arm_cup_*`), probes,
hover ring (maglev, connected by spokes), rear tool rack, torch inner core.

Screenshots confirm: the colossus's shoulder bridges, waist column, and hip bridges are all visible, the whole body connected as one.

## V. Lesson

**"Gaps between parts" doesn't mean "disconnected."** Both earlier criteria measured gaps and both went wrong.
The real question is "**is it one object**" — that calls for connected components, not pairwise distance measurements.

**The same order-of-magnitude error repeated across five bodies.** greeble's `(W, D, H)` and the solid's
`(W*0.5, D*0.52, H*0.52)` differ by a full factor of two, yet it was copy-pasted into five functions,
and each spot looked "reasonable." Batch-repeated parameters most need checking against real solid dimensions.

---

# Round 80 (2026-11-03): Local Image Model Integration — Scene Posters + A Hidden Level Bug

## I. Tools

Local service `http://127.0.0.1:7860` (EasyAI Studio) provides three engines:

| engine | use |
| --- | --- |
| `krea2` | Krea 2 Turbo, general-purpose, default |
| `zimage` | Z-Image, 8 steps, fast |
| **`moss`** | **MOSS-Image, strong text layout — must use this when the image needs text** |

Wrapper `tools/easyai.py`: `generate(prompt, out_path, engine=..., ratio=...)`.
Batch generation script `tools/gen_posters.py`.

Measured ~25 seconds per image, high text accuracy ("SECTOR 7" "AUTHORIZED PERSONNEL ONLY"
"MAX 1800 kPa" "NIGHT SHIFT / CREW 12 / BAY 3" all spelled correctly).

## II. Generated posters (4, all moss)

This world is an abandoned industrial yard, so the posters are **things that would realistically be here**:

| File | Content |
| --- | --- |
| `poster_sector7` | SECTOR 7 / COOLANT LINE - HOT / triangular warning |
| `poster_no_entry` | AUTHORIZED PERSONNEL ONLY / MAINTENANCE BAY 4 |
| `poster_pressure` | PRESSURE TEST / pipe schematic / MAX 1800 kPa |
| `poster_shift` | NIGHT SHIFT / CREW 12 / BAY 3 / LOG BOOK REQUIRED |

Also generated 2 seamless textures (`tex_wall_seamless`, `tex_concrete_seamless`, krea2),
**not yet wired into materials this round**, that's the next step.

## III. Materials and placement

- `M_Poster`: Unlit + opaque, `Emissive = PosterTex × Brightness(8.0)`.
  Signage in a night scene must be self-emissive to be readable.
- Each poster built as a **material instance** (`MI_poster_*`), all sharing the same M_Poster.
- Geometry uses `Engine/BasicShapes/Cube` flattened into a 2cm-thin board: each of the cube's six faces has its own complete
  0-1 UV, and the ±X faces naturally face the player, so **no need to guess the Plane's rotation**.
- 10 posters, 5 on the back wall + 5 on the far wall (coordinates from measured wall world bounding boxes).

## IV. Two pitfalls hit

### 1. OpacityMask reads the R channel, not alpha

The first version used `BLEND_MASKED`, connecting `TextureSample`'s default output to `OpacityMask`.
Result: the poster **left only a shadow** — because that pin reads the **R channel**, and dark areas (low R)
were masked out.

A poster has hard rectangular edges and needs no mask at all. Switching to `BLEND_OPAQUE` fixed it.

### 2. Wall coordinates can't rely on actor position alone (see next section)

## V. Level bug fixed along the way: the arena walls weren't standing up at all

While investigating "why the posters look like they're floating in midair," I checked import caches, triangle counts, visibility flags,
forced LOD, Nanite — all normal. Finally found:

**The static-mesh component's `relative_rotation` for `sm_wall_segment` had Pitch = 90°.**

The component was rotated 90° around the Y axis, the entire wall **lay flat buried in the floor** (z≈-45..45),
so it was invisible from every angle. That's why the arena always looked like an "open platform."

`fix_wall_rotation.py`: zeroed the Pitch of 34 wall components (14 of them were 90°),
and restored temporarily replaced materials (170 slots). After the fix the walls stood properly and the arena was enclosed.

## VI. Verification

- 5 posters each on the back/far walls, attached to measured wall surfaces (X=-1240 / X=1770.2).
- Unlit self-emissive, readable at night; far away they serve as ambience, up close the text is crisp.
- Panoramic screenshot: the arena is now enclosed by complete walls, with signage visible hanging on them.

## VII. Lesson

**"An object exists in the editor" ≠ "it renders in the game."** I ruled out materials,
visibility, LOD, Nanite, streamed sub-levels, and only at the end looked at **the component's relative rotation** —
which was actually the first thing to check: the actor's yaw was 0, so it "looked correctly oriented,"
but what really determines geometry orientation is the **component's** rotation.

**Texture/material parameters must be verified with a criterion that can actually be read.** With the OpacityMask trap,
if you only look at "the poster appeared," you'd think it was done; zooming in reveals there's only a shadow.

---

# Round 81 (2026-11-03): Integrating AI Textures into the Material System

Last round only made posters. This round adds "scene textures + character/mech textures".

## 1. First, Understand How the Materials Are Wired (Key Prerequisite)

The existing mech/environment materials are **already fully parameterized**, not hard-coded textures:

    Texture parameters: DetailTex、NormalTex
    Scalar parameters: TextureSize、Metallic、Roughness、WearAmount、DetailAmount、
             NormalStrength、SeamDarken、SeamAO、RoughDetail、VertexColorAmount
    Vector parameters: BaseTint、EmissiveTint、WearTint

`DetailTex` is tiled-sampled by **world coordinates** (`TextureSize` = how many cm one texture covers), so **no UV is needed**, and swapping a texture is just swapping a parameter. This keeps the risk of changes to a minimum: the old textures can be swapped back at any time.

## 2. Generated Textures (6 color + 6 normal)

Used krea2 (no text layout needed); all prompts emphasized `seamless tileable` + `flat orthographic top-down` + excluded perspective/shadow:

| Texture | Purpose |
| --- | --- |
| `tex_mech_armor` | Mech armor: panel seams, rivets, scratches, grease in grooves |
| `tex_mech_joint` | Joints: black oxidation, machining marks, hydraulic oil stains |
| `tex_mech_copper` | Copper parts: verdigris, brushed finish, oxidized edges |
| `tex_env_paint` | Environment paint: peeling, rust seeping through, vertical brush marks |
| `tex_env_floor` | Floor pattern steel plate: diamond anti-slip tread, worn bright from foot traffic, dust in recesses |
| `tex_env_concrete` | Concrete: aggregate, oil stains, formwork panel seams |

Normal maps are auto-generated from the color maps by `tools/make_normals.py` (luminance as height → Sobel gradient → tangent-space normals, wrap-around sampling ensures continuity at seams).

## 3. Integration

`ue/Scripts/apply_ai_textures.py`: imports into `/Game/RobotGame/Art/Materials/AIDetail/`, then sets, on each material instance, `DetailTex` / `NormalTex` / `TextureSize` / `NormalStrength`.

A total of **24 material instances** were updated:

- Character: M_Steel / M_SteelLight / M_Joint / M_Copper / M_Frame
- Character accent colors: M_Accent_* and M_AccentDark_* (14 total, including all enemy models)
- Environment: M_Steel / M_SteelLight / M_Joint
- Props: M_Steel / M_Copper

`TextureSize` is set separately by part scale: character parts 120~200 cm, environment walls 480~520 cm, props 260~420 cm. A single TextureSize would make the pattern too coarse on small parts and too fine on large surfaces.

## 4. A Necessary Trade-off

The material's world-coordinate projection converges along meridians on **curved surfaces**, so spheres (patrol bots, shoulder pads) develop fine stripes. Reducing `NormalStrength` from 0.8 to 0.55 noticeably reduced this, while panel details were preserved.

A complete fix requires a triplanar projection material, which is a material-graph rewrite; it wasn't touched this round.

## 5. Verification

- Character close-ups: armor now has panel seams, rivets, and scratches, no longer plain solid-color plastic.
- Environment: floor/walls now have panel seams and wear, consistent with the posters and props.
- Wide shot: the arena is enclosed by perimeter walls, with notice boards hanging on the walls and panel-seam details on the ground.

## 6. Lessons

**First check whether the material has exposed parameters, then think about "how to shove the texture in".** At first I was ready to create new materials and redo UVs; after understanding the structure, I found that simply swapping the `DetailTex` parameter was enough — an order of magnitude less work, with no regression risk either.

**The same scalar parameter needs different values for different parts.** `TextureSize` has "world size" semantics; if the whole project shared one value, the pattern density on a 2.5 m mech and a 20 m wall would differ by a factor of 8.

---

# Round 82 (2026-11-03): Poster Expansion + Texture Seamlessness + LOD Fix

## 1. Posters: From 4 Types to 10 Types, 18 Copies

Second batch (all MOSS, with text layout):

| File | Text |
| --- | --- |
| `poster_highvoltage` | HIGH VOLTAGE / 415V AC |
| `poster_runoff` | RUNOFF WATER / DO NOT DRINK |
| `poster_bay07` | 07 (number plate) |
| `poster_evac` | EVACUATION ROUTE / ASSEMBLY POINT B |
| `poster_toolcrib` | TOOL CRIB / SIGN OUT REQUIRED |
| `poster_roster` | SHIFT ROSTER (shift schedule) |

Placement expanded from 10 to **18 copies**: 9 on the back wall + 9 on the far wall, one every 300 cm along Y, with heights slightly staggered at 195~210 cm — to avoid looking like "a row of postage stamps". The number plate (BAY 07) was made smaller than the notices, matching real-world site hierarchy.

## 2. Making Textures Seamless (Key Fix)

Although the AI-generated textures had "seamless tileable" written in the prompt, their **edges actually didn't line up**. The materials tile by world coordinates (one covers 4~5 m), and the seams showed up in the scene as rectangular patches of color difference — most obvious on walls and floors.

`tools/make_tileable.py` uses the classic offset + cross-fade:

    shifted = roll(img, half image)
    out = img * win + shifted * (1 - win)      # win = cosine window: 1 at center, 0 at edges

At the edges out ≈ shifted, and shifted at the edges is the original image's center — continuous; meanwhile shifted itself is a wrap-around translation, so out's top/bottom/left/right edges join naturally.

All 6 detail textures were processed, then normals were regenerated and all 24 material instances re-imported.

## 3. LOD Segment Retention Rate

Enemy LODs were originally generated at 0.45 / 0.18. The patrol bot is a 36-segment sphere, LOD1 had only about 16 segments left and started switching at around 10 m — enemies are the main actors on screen, too noticeable.

Changed to **0.62 / 0.34**; the LOD1/LOD2 triangle counts of the six enemies:

| Mech | LOD0 | LOD1 (old→new) | LOD2 (old→new) |
| --- | --- | --- | --- |
| Patrol bot | 11992 | 5394 → **7434** | 2132 → **4060** |
| Transporter | 22654 | 9685 → **14044** | 3826 → **7696** |
| Colossus | 38262 | 16250 → **23722** | 6400 → **12990** |
| Gardener | 15236 | 6512 → **9446** | 2576 → **5160** |
| Weather | 19194 | 8629 → **11900** | 3424 → **6500** |
| Guardian | 22084 | 9756 → **13692** | 3926 → **7466** |

## 4. Regression

After re-import: the median ground clearance of the five enemies' feet was still **2.1 cm** (same as the player's), no regression in gait or leg shape.

## 5. Known Unresolved: Radial Stripes on Spherical Surfaces

**Spherical surfaces** like the patrol bot and shoulder pads have a ring of radial stripes (distributed along meridians, converging at the poles).

Diagnosis conclusion:
1. **Not LOD** — the stripes remained after increasing the segment retention rate.
2. It is the **projection-plane boundary of triplanar/cubic projection**: on the sphere, the three projections ±X / ±Y / ±Z have no weight blending at the boundaries, forming hard seams.

A complete fix requires blending the three DetailTex samples in `M_RobotSurface` by `abs(normal)^k` weights (triplanar blend). That material has 74 nodes, UE's Python API does not provide the ability to "read expression connections", so blind changes are risky, **so it wasn't touched this round**. Next-step suggestion: manually add a blend layer in the editor, or write a triplanar Material Function to replace the DetailTex sampling section.

## 6. Lessons

**"Seamless" is what the model says, not a fact.** Judging seamlessness visually is unreliable — those large color patches in the generated image look natural in a single view, but immediately become a grid once tiled. Tileability must be handled algorithmically (offset + cross-fade), not by relying on the prompt alone.

**Rule out the cheapest hypothesis first.** The LOD line was worth checking: the segment retention rate was indeed too low, and raising it smoothed the overall silhouette; but it wasn't the cause of the spherical stripes, and I shouldn't have assumed it was solved when I saw "fewer stripes" — only by zooming in near the poles did it become clear it was a projection boundary.

---
# Round 83 (2026-11-03): Spherical Faceting — The Real Root Cause Is Flat Shading

## 1. First, Rule Out "Textures" with an Experiment

The **spherical surfaces** of the patrol bot and shoulder pads have a ring of radial stripes. Last round suspected LOD, but raising the segment retention rate didn't change the stripes — so it's not LOD.

This round ran a decisive control experiment: temporarily zeroed `DetailAmount` and `NormalStrength` on all 24 material instances (`detail_toggle_test.py`, with a full backup for restoration), then took a close-up at the same position.

**The stripes were still there.** So it's neither textures nor LOD, but **the shading method of the geometry itself**.

## 2. Root Cause: Primitives Are Flat-Shaded

`robotlib._finish()` is the common exit for all primitives (sphere / cylinder / torus / prism / box), and it **never set `use_smooth`**. Only the three surface generators loft / lathe / sweep set smoothing themselves (lines 478 / 551 / 633).

Consequence: each polygon has an independent normal, so a 36-segment sphere looks like a "flower petal" from the front. This isn't a texture problem but a **shading problem of the basic primitives**, affecting all models built from them.

## 3. Fix: Smooth Shading + Preserve Sharp Edges by Angle

Handled uniformly at the end of `_finish()`:

    for poly in me.polygons: poly.use_smooth = True
    # then use bmesh to mark edges with angle > 35° as sharp
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle() > radians(35):
            e.smooth = False

This way curved surfaces (sphere/cylinder/torus) are smooth, while boxes and armor plates keep their edges — exactly the right read for mechanical parts.

Also changed the FBX export `mesh_smooth_type` from `'FACE'` to `'EDGE'`: `'FACE'` can only export smoothing flags per face, **cannot express sharp edges**, so changing it would round off the boxes too; `'EDGE'` is what carries "smooth faces + sharp edges" together.

## 4. Verification

| Item | Before | After |
| --- | --- | --- |
| Patrol bot sphere | 36-petal radial facets | smooth, only one UV seam left |
| Cylinder legs / pipes | longitudinal facets | smooth |
| Boxes / armor plates | normal | still have sharp edges |

Regression after re-import: the median ground clearance of the five enemies' feet was still **2.1 cm**, no gait regression.

## 5. Lessons

**Defects that "look like texture problems" should be disproven with experiments, not fixed by following intuition and changing materials.** I suspected UV projection, triplanar blending, and LOD in turn — all wrong. The truly time-saving step was that control experiment of "zeroing DetailAmount and taking another shot" — it ruled out the entire material direction in one go.

**Default values of basic primitives have the widest impact.** One missing line `use_smooth` in `_finish()`, and all spheres and cylinders in the project are faceted, and no one would suspect "the primitives themselves".

---

# Round 84 (2026-11-03): Rebuilding the Player Mech Too — Full Smooth-Shading Coverage

Round 83 fixed the flat-shading problem of `robotlib._finish()` (curved surfaces became smooth, sharp edges preserved), but that only took effect for models **rebuilt afterwards**. The player mech (`SK_Chassis_*`) was still the old flat-shaded version, with obvious petal-like facets on the shoulder-pad spheres.

## 1. Back Up First

21 files: all `SK_Chassis_*` uassets (including LODs) + `chassis_*.fbx`, saved to `%TEMP%/opencode/chassis_backup`. The project has no version control, so this step can't be skipped.

## 2. Rebuild

    blender --background --python tools/blender/build_chassis.py \
        -- --chassis all --out assets/out --no-render

The three models (light / medium / heavy) each have 46k~47k triangles, with dimensions consistent with before (2.57~2.70 × 1.41~1.95 × 1.02~1.31 m).

## 3. Re-import

`ue/Scripts/reimport_rigged.py` (re-import after deleting assets with the `chassis_` / `enemy_` prefixes), then ran `fix_chassis_da.py` (fixes material slots for body-part damage) and `apply_ai_textures.py` (re-attached AI textures, 24 material instances).

## 4. Verification

- No missing-asset errors in the console.
- Player close-ups: shoulder-pad and head spheres **smooth**, armor plates keeping sharp edges.
- Walking screenshots: both legs swinging, weapons complete, materials (teal-green accent / copper rings / dark armor) normal.
- Enemy regression: the median ground clearance of the five enemies' feet still **2.1 cm**.

## 5. Current Overall Status

| Item | Status |
| --- | --- |
| Character / enemy curved-surface shading | all smooth (sharp edges preserved) |
| Scene perimeter walls | fixed (Round 80's Pitch=90°) |
| Posters | 10 types of content / 18 copies, MOSS-generated, with real text |
| Detail textures | 6 AI-generated sets + seamless processing + auto normals, 24 material instances |
| Enemy LOD | segment retention rate 0.62 / 0.34 |

## 6. Lessons

**When fixing a defect in a "generator", you must remember to rebuild the already-produced existing assets too.** After changing `_finish()`, newly built things were correct, but what was running in the scene was still the old stuff — if you only look at screenshots of newly built models, you'll wrongly assume "everything is fixed".

---

# Round 85 (2026-11-03): Walking Posture — "High-Knee Marching in Place"

User feedback: "The robot's walking posture is wrong."

## 1. First, Enable Burst Shooting (Otherwise You Can Only Guess from Single Frames)

`tools/shot_run.ps1` hard-coded `-ShotEvery=5`, and it appeared first — UE takes the first match, so passing `-ShotEvery=0.3` in `Extra` had no effect, and only one frame came out per run.

Changed to launching `UnrealEditor.exe` myself, with only `-ShotEvery=0.30` in the parameters, got 19 frames in 6 seconds, then assembled them into a contact sheet to see the whole gait cycle.

**Judging gait from a single frame is unreliable**: any odd-looking frame may just be the middle of the swing phase.

## 2. First Add a Player Foot Diagnostic

Enemies had `[FootH]` (bounding-box lowest point vs ground ray trace), but the player never did. Added `[FootP]` in `ARobotCharacter::Tick`, with the same measurement convention as enemies.

First measurement: while walking, gap=2.2 cm (same as enemies) — **the feet actually are on the ground**. So the "floating" feeling isn't a height problem.

## 3. The Real Cause: Lifting the Foot Higher Than the Step Length

Printed the pose angles (extended `[FootZ]` fields):

    L[hip=46 knee=-69 lift=16.1 fwd=-7.3]   ←  swing leg
    R[hip=5  knee=-14 lift=0    fwd=5.3 ]   ←  stance leg

The swing leg **lifts 16 cm but only moves forward 7 cm**, hip rotates 46°, knee bends 69° — the leg can only lift the foot by bending the knee sharply, which looks like high-knee marching in place.

Checked the gait parameters again:

    speed=140cm/s  stride=22cm  stridemax=64.5  leglen=104

**The stride is only 21% of the leg length, while the foot-lift cap is 22 cm.** The proportions are completely off.

## 4. Changes

### 1. Made Foot Lift Proportional to Stride

    Old: (6 + 16 * speed ratio) * MoveBlend        // 0~22 cm, independent of stride
    New: clamp(effective stride * 0.30, 3, 16)        // 30% of stride

In real gait, foot lift is about 25~35% of stride. A small stride naturally lifts less, so no more "lifting more than stepping".

### 2. Cadence Cap 20 → 15

20 rad/s = 3.2 steps/sec per leg (6.4 steps/sec total), which is a sprint cadence. After reducing to 15, the stride at the same speed went 22 → 29 cm.

## 5. A Trade-off Worth Recording

First tried reducing cadence to 11 (stride 40 cm, most natural posture); as a result netSlip went from 24/30/8/10 up to **52/79/82/38** (median of three runs) — the feet clearly slipped during stance.

This shows **the current pose chain can't pin the foot during a longer stance phase**, so it can't be done in one step. Settled on 15 as a compromise: stride 29 cm, foot lift proportional to stride, player netSlip 10 (acceptable), enemies 32~58.

Note: **the reason the old "high cadence" had good slip metrics is that the feet barely moved** — that metric rewards "marching in place". Once visual appearance became the standard, real slipping was exposed. That's the problem to tackle next.

## 6. Verification

| Item | Result |
| --- | --- |
| Player foot ground clearance | median 2.1 cm (newly measured via `[FootP]`) |
| Enemy foot ground clearance | median 2.1 cm |
| Player stride | 22 → 29 cm |
| Player netSlip | 10 cm/s (median of three runs 6/14) |
| Burst-shot contact sheet | knee bend noticeably reduced, feet land flatter, no more high-knee marching |

## 7. Lessons

**"Good metrics" and "looks right" can conflict.** Round 65 raised cadence from 12 to 20, because the slip residual decreased monotonically with cadence — but that residual was already close to 0 when stride was tiny. The metric led one to believe "the finer the steps the better", but tiny steps look wrong.

**Judging gait needs at least one full cycle.** This time it was only visible after launching the process myself for burst shooting; `shot_run`'s single-frame mechanism mistakes "the middle of the swing phase" for "a posture error".

---
# Round 86 (2026-11-03): Stance-Phase Slipping — Speed Jitter Directly Drags the Foot

Last round enlarged the stride from 22 cm to 29 cm and the posture became natural, but netSlip rose to 32~58. This round investigated its source.

## 1. First, Rule Out the Possibility That "the Metric Is Untrustworthy"

The two `r525` logs used for last round's summary had **not a single MacroSlip line** (it wasn't active during the runs), yet numbers were still aggregated — that's a bug in my aggregation script: it didn't error on "files with no data".

Ran a clean one again (276 lines of MacroSlip) and got real frame-by-frame data:

    [Foot slip] C_8 speed=38  left-foot stance slip=40 cm/s  right foot=8 cm/s  IK clamp=0

**The mech only walks at 38 cm/s, but the stance foot scrapes along the ground at 40 cm/s.** And the speed, within the same second, changed violently from 194 → 103 → 38.

## 2. Cause: Stride Is Recomputed Each Frame from the Current Speed

    Stride = SpeedForGait * Duty * T;

`Stride` is recomputed every frame using the **current** speed. When enemy AI accelerates/decelerates/turns and the speed jitters, the entire stance trajectory (±Stride/2) jumps along with it — the foot's target point teleports mid-phase, which shows up as "the mech barely moves while the foot scrapes the ground".

This is unrelated to posture; it's a **time-response** problem.

## 3. Fix: Time-Smooth the Gait Speed

    S.GaitSpeedSmoothed = FInterpTo(S.GaitSpeedSmoothed, SpeedForGait, Dt, 6.f)

Converges in about 0.25 s. Stride changes are smoothed out, and the foot is no longer dragged by single-frame speed jitter. Both `Stride` and `Omega` now use the smoothed value.

## 4. Effect (Two Runs)

| Entity | netSlip before | After |
| --- | --- | --- |
| C_5 | 56 | **42** |
| C_7 | 51 | **45** |
| C_8 | 58 | **29** |
| C_9 | 32 | **25** |
| Player | 10 | **9** |

C_8 is the most obvious (58 → 29), because its speed changes most violently.

## 5. Regression and Verification

| Item | Result |
| --- | --- |
| Player foot ground clearance | 2.1 cm |
| Enemy foot ground clearance | 2.0~2.2 cm |
| Player stride | 29 cm |
| Burst-shot posture | moderate knee bend, feet land flat, stride clearly visible |

## 6. Still Outstanding

Enemy netSlip is 25~45 cm/s. The root cause is that **when AI turns, the foot's stance motion follows the mech's forward direction, while the actual displacement direction is rotating** — the mismatch in direction causes lateral sliding.

A complete fix requires the stance foot to move back along the **actual velocity direction** (rather than the mech's forward direction). Previously tried compensating laterally by yaw rate (FwdLat), which resulted in slip spikes at leg-switch moments, so it was reverted. Redoing it with a smoothed velocity direction might work, but that's for a later round.

## 7. Lessons

**Files with no data must not be counted as "data" in statistics.** This round almost drew the conclusion of "slip 56" again based on two empty logs — the aggregation script should first check the line count of each file.

---

# Round 87 (2026-11-03): Fix the Ruler Before Talking About Slipping — Two Failed Directions

## 1. Discovering We'd Been Using the Wrong Criterion

All conclusions about slipping in the previous rounds were based on `[MacroSlip]`:

    netSlip = (foot's net displacement within window − mech displacement) / window duration

It measures "how far the foot and the mech each traveled within a 0.3 s window". The problem is: **within one full gait cycle, the foot must return to the same position relative to the mech** — so netSlip is only close to 0 when the window happens to cover an integer number of cycles. Change the cadence (change the cycle length), and this metric shifts overall, unrelated to whether slipping actually occurred.

This explains why "raising cadence" seems to reduce slipping: higher cadence → shorter cycle → easier to fit a whole cycle into the window → nicer numbers. The metric rewards tiny steps.

## 2. Switch to a Real Criterion: The Stance Foot's Velocity in World Space

    if (PoseL.bStance) S.DbgStanceMoveL += Dist2D(foot world position, previous frame) / Dt

The foot during stance should be **nailed to the ground, not moving**, so the closer this value is to 0 the better.

The real situation from the first measurement:

| Entity | Placement error | Stance foot world velocity |
| --- | --- | --- |
| Player | 0.6 cm | **12 cm/s** |
| C_8 (Gardener) | 0.3 cm | **60~90 cm/s** |

The player is basically pinned; **the high-speed enemy (C_8 at about 200 cm/s) drags its foot along the ground when turning**.

## 3. Two Failed Attempts (Both Reverted)

### Attempt 1: Anchor the World Landing Point During Stance

Idea: record the foot's world coordinates at the moment of landing, and solve directly to this fixed point during stance — no matter how the mech accelerates or decelerates, the foot won't be affected.

Result: placement error rose from 0.3 cm to **8~36 cm**, and stance foot velocity instead became 88~260 cm/s.

Reason: as the enemy walks and turns at the same time, the world anchor swings to the side of the body. With a 0.2 s stance phase and a speed of 200 cm/s, the lateral offset can exceed leg length → IK can't reach → clamp → foot dragged away. **The anchor must rotate with the body, and "rotating with the body" is equivalent to no anchoring at all.**

### Attempt 2: Determine Stride from the Velocity Component Along the Mech's Forward Direction

Idea: when turning, the forward component is small, so the stride shrinks accordingly and the foot won't over-retreat.

Result: C_8 stance foot velocity 119~182 cm/s, **worse**. Because the smaller forward component made the stride insufficient, and the foot was instead dragged forward by the mech.

Both were reverted, and the code returned to "speed magnitude + smoothing".

## 4. What Was Kept This Round

| Change | Effect |
| --- | --- |
| Foot lift ≈ stride (last round) | eliminated "high-knee marching", knee bend back to a natural range |
| Cadence cap 15 (last round) | stride 22 → 29 cm |
| Gait speed time smoothing (last round) | C_8's netSlip 58 → 29 |
| `[FootZ]` gained stance-slip fields | gave us the first trustworthy slipping criterion |

## 5. Final Status

| Entity | Foot ground clearance | netSlip (reference value under the new convention) |
| --- | --- | --- |
| Player | 2.0 cm | — |
| C_5 | 2.1 cm | 40 |
| C_6 | 2.1 cm | 0 |
| C_7 | 2.1 cm | 38 |
| C_8 | 2.2 cm | 2 |
| C_9 | 2.1 cm | 22 |

Burst-shot confirmation: natural knee bend, feet land flat, stride clearly visible.

## 6. Next Step (Clear Technical Route)

To make enemies not slip even while **turning**, we need "orientation-aware stance": the stance foot's target should retreat along the **actual velocity direction**, not the mech's forward direction; and when the target exceeds leg length, **clamp by the reachable radius** (rather than a hard clamp), so the foot slides along the reachable circle instead of being teleported to the boundary.

The `FwdLat` tried last round compensated laterally by yaw rate, which jitters; the correct approach is to use the **smoothed velocity direction** to construct the stance foot's retreat axis. This change also needs to handle the IK's 2D assumption (the current `Base = atan2(dy, -dz)` only holds in the sagittal plane), so it can't be done in a single line.

## 7. Lessons

**First confirm the ruler measures what you want.** For several rounds I kept optimizing netSlip, but it's sensitive to window phase and rewards tiny steps — the more I optimized, the further off I got. The question to actually ask is "how much did the stance foot move in the world", a quantity that's verifiable at a glance.

---

# Round 88 (2026-11-03): Three Attempts, None Worked — Write the Conclusions Clearly

Goal: make the enemy's stance foot not drag on the ground while **turning** (last round measured 60~115 cm/s).

## Attempt 1: Anchor the World Landing Point During Stance (Tried in Round 87, Reverted)

Record the foot's world coordinates at the moment of landing, and solve to this fixed point during stance. Result: placement error 0.3 → **8~36 cm**. When turning, the anchor swings to the side of the body, exceeding leg length.

## Attempt 2: Determine Stride from the Forward Velocity Component (Reverted)

When turning, the forward component is small → stride shrinks → foot dragged by the mech, C_8 stance slip **119~182**.

## Attempt 3: Add a "Lateral Swing" Degree of Freedom to the Hip (This Round)

Idea: the problem is that a lateral target is forcibly squeezed into the 3D leg length. If the leg swings toward the target about some axis, the lateral offset no longer needs to be satisfied by "a longer leg".

Tried in two steps:

| Axis | Result |
| --- | --- |
| About the vertical axis (AxisUp) | Wrong. A vertical leg rotating about the vertical axis is **self-rotation**; the foot barely moves, and placement error actually rose to 2.7 cm |
| About the forward axis (AxisFwd, i.e. abduction/adduction) | Right direction, but placement error 0.6 → **1.4 cm**, and stance slip didn't drop |

Both variants were reverted. Although the second is physically "abduction", the current two-bone IK only solves angles in the sagittal plane (`θ₁ = base + α`), after adding an extra rotation axis, the foot's landing point no longer equals the position assumed by the inverse solution — so the error grew instead.

## Conclusion: This Is a Structural Limitation, Not a Parameter Problem

The current IK has only **2 degrees of freedom**: hip pitch + knee. The leg can only extend and swing within the sagittal plane. Any lateral target (tangential displacement while turning) cannot be tracked by the "landing point" — it can only be brute-forced with leg length, and when that fails it clamps, and the foot gets dragged away.

To avoid slipping while turning, the IK must be expanded to **3 degrees of freedom** (hip pitch + hip abduction + knee), and abduction must be applied before pitch, with the target first expressed in the leg plane. This is a rewrite of the inverse-kinematics layer, not something parameter tuning can solve.

## Final Status This Round (Restored to the Stable Version)

| Entity | Foot ground clearance | Stance foot world velocity |
| --- | --- | --- |
| Player | 2.0 cm | **10~25 cm/s** |
| C_5 | 2.1 cm | ~60 |
| C_7 | 2.1 cm | ~60 |
| C_8 (fastest, turns most) | 2.1 cm | **92~115** |
| C_9 | 2.1 cm | ~40 |

Walking screenshots confirm: stride, knee bend, and foot landing are all normal.

## Lessons

**Three consecutive failures show the problem isn't "just tweak one more parameter".** The first two times I was changing "how to calculate stride"; only the third time did I touch the real boundary condition: insufficient IK degrees of freedom. The criterion is simple — if every change needs a "compensation term" to mask the error, that means the model itself is missing a dimension.

**Failed attempts must also have their reasons clearly recorded.** These three directions are all easy for someone to pick up and retry, so writing down "why it doesn't work" is more valuable than writing "what was done".

---
# Round 89 (2026-11-03): Three-DOF IK Rewrite Attempt (Not Adopted, Reverted)

## Approach

Following the route defined last round, changed the leg inverse solution from "sagittal-plane two-bone IK" to three degrees of freedom:

    1. First solve the two-bone IK in the sagittal plane, using distance dSag = sqrt(dy² + dz²)
    2. Then abduct the whole leg about the **forward axis** by φ = atan2(dx, dSag)
    3. The knee joint's rotation axis rotates along with the abduction (AxisRight rotated by φ about AxisFwd)

This time two mistakes from last round were corrected: the abduction axis is the forward axis (not the vertical axis), and the order changed to "pitch first, then abduct" (the abduction axis is a fixed world axis, so pitch must be applied first).

## Results

- **Straight walking (player)**: abduction angle ≈ 0, visuals identical to before, stance foot placement error 0.67 cm (same as the 0.62 cm before reverting) — showing it's neutral for straight-line walking.
- **Enemies (lots of turning)**: measured stance slip values skyrocketed (500~1900), but at the same time the `[FootZ]` accumulation count n was found to be only 66 (normally should be in the thousands), meaning this batch of data isn't comparable to the previous convention, so **one can't conclude it's "worse" from this**.

## Decision: Revert

Reasons:
1. No evidence that it improved turning slip;
2. It increased inverse-solution complexity (one more degree of freedom, the knee axis must rotate along);
3. The current `[FootZ]` statistics showed an anomaly on this version (n=66), and with the metric itself unstable, a structural change shouldn't be kept.

Re-verification after reverting: all five enemies plus the player had foot ground clearance **2.1 cm**, walking visuals normal.

## Current Status and Recommendations

| Item | Status |
| --- | --- |
| Player walking | natural posture, feet land, stance slip ~10-25 cm/s |
| Enemy straight-line walking | normal |
| Enemy high-speed turning | stance foot still has 60~115 cm/s of slip (unresolved) |

**Recommendation: solve "measurement" first, then "slipping".** The current `[FootZ]` stance slip relies on frame-by-frame accumulation, and the sample count can be distorted by throttling/initialization anomalies (n=66 occurred this round). Before touching the inverse solution, one should first build a stable, offline-reproducible record of stance-foot displacement (e.g., write each frame's stance-foot world coordinates into a CSV, then do statistics on the Python side), otherwise every change can only be judged by "does it look right" — which is exactly why the previous four rounds went in circles.

## Lessons

**When the metric is unstable, don't touch the structure.** This round I changed both the inverse solution and the observation convention, so the changes on both sides got mixed together, and it could neither prove an improvement nor a regression. Next time, spend a round first making the measurement solid.

---

# Round 90 (2026-11-03): Making the Measurement Solid — Pinpointing "Direction Mismatch"

Last round's conclusion was "solve measurement first, then slipping". This round did exactly that, and also settled, once and for all, the question that had hung over several rounds: "is the stride calculated wrong?".

## 1. New Measurement Method

`-DumpFootCsv`: writes each leg's **foot world coordinates + mech coordinates** into the log every frame. The offline script `tools/analyze_foot_csv.py` cuts consecutive stance frames of the same leg into "stance segments", computes the foot's maximum world displacement within the segment / segment duration — this is the real stance slip, independent of window phase and log throttling.

`tools/show_worst_seg.py` can print the frame-by-frame details of any segment.

## 2. Baseline (Real Numbers Before the Fix)

| Entity | Median stance slip | p90 |
| --- | --- | --- |
| Player (straight) | **10.9** | 13 |
| C_5 | 13.7 / 17.7 | 147 |
| C_8 | 13.3 / 18.6 | 160 |
| C_7 | 22~53 | 202 |
| C_9 | 46~60 | 151 |

**The medians are all low, but p90 is high** — meaning the problem is concentrated in a few "bad segments", not widespread slipping.

## 3. Ruling Out the "Stride Calculated Wrong" Hypothesis

The worst segment in the frame-by-frame details (C_5) showed: at the moment of landing the foot jumped 16 cm, 25 cm, then continued moving at about 85 cm/s in steady state. So I suspected "the stride only covered half".

After adding `rblend` (actual displacement ratio) and `maxspd` to `[Gait]`, measurements showed:

| Entity | speed | rblend | actual | maxspd |
| --- | --- | --- | --- | --- |
| C_5 | 173 | 0.98 | 170 | 173 |
| C_6 | 260 | 1.00 | 260 | 260 |
| C_7 | 146 | 1.00 | 146 | 146 |
| C_8 | 190 | 0.94 | 190 | 201 |
| C_9 | 108 | 1.00 | 108 | 108 |
| Player | 140 | 1.00 | 140 | 140 |

All `MoveBlend` ≈ 1 (`SmoothStep((rblend-0.02)/0.16)` had long saturated), and the stride was also verified to equal Speed × Duty × T (ratio 1.00).

**Conclusion: it's not a stride-scaling problem.** The leg retreated exactly as much as it should.

## 4. The Real Difference: Travel Direction and Body Facing Don't Match

Same code, same stride:
- Player walks **straight** → stance slip 10.9 cm/s (foot basically pinned)
- Enemy **turns frequently** → median 46~60, bad segments 200+

The foot's stance motion retreats along the **mech's forward direction**, while the enemy's actual displacement direction is rotating — the larger the angle between them, the more the foot scrapes the ground. This has nothing to do with "stride/cadence/foot lift".

## 5. Why the Previous Three Fixes Didn't Work

To make the stance foot retreat along the **actual velocity direction**, the foot's target point deviates from the sagittal plane. The current IK has only 2 degrees of freedom (hip pitch + knee), so a lateral target can't be tracked — when Round 89 added an abduction degree of freedom, the three intertwined factors of the knee axis, application order, and "the metric itself being distorted at low frame rates" made it impossible to judge effectiveness, so it was ultimately reverted.

## 6. Current Status

Stable: all feet on the ground (2.0~2.2 cm), stride consistent with speed, player walking posture natural.
Unstable: stance slip when enemies turn.

**The correct starting point for the next round**: use this round's CSV measurement as the sole criterion, implement "support along the velocity direction" on its own, **without changing any other parameters**, and compare segment by segment whether the slip median and p90 drop. With data, there's no fear of experimenting.

## 7. Lessons

**First proving "it's not this cause" is more valuable than fixing directly.** This round spent time verifying "the stride wasn't miscalculated and MoveBlend wasn't shrunk", thoroughly eliminating the repeatedly suspected direction, and the boundary of the problem immediately became clear.

---

# Round 91 (2026-11-03): Tried Two Paths with the New Criterion, Both Rejected by Data

After Round 90 made the measurement solid, it finally became possible to use the foot world coordinates' "stance-segment slip" (max displacement within segment / segment duration) to judge whether a change is good or bad. This round tried two paths.

## Attempt 1: Stance Foot Retreats Along the Actual Velocity Direction

Idea (the route defined last round): the stance foot's displacement should cancel the mech's forward motion. Previously there was only the mech's forward component; when turning, the direction mismatched → the difference became lateral slip. Changed the retreat amount to be along the **smoothed actual velocity direction**, with the lateral part added to AxisRight.

Implementation key point: the velocity direction must be smoothed (`VInterpNormalRotationTo`, 180°/s), otherwise the foot jumps at the slightest yaw jitter — exactly why the earlier FwdLat failed.

Results (median stance-segment slip, cm/s):

| Entity | Baseline | After change |
| --- | --- | --- |
| Player | 10.9 | **93.1** |
| C_8 | 13.3 | 117.3 |
| C_9 | 60.0 | 179.3 |

**Everything got 5~9 times worse, and only 1~4 stance segments remained** (normally 16~18) — meaning the foot went out of the reachable range in large stretches, and the IK kept clamping.

**Reverted.**

## Attempt 2: Shorten the Stance Phase (Duty 0.50 → 0.42)

Idea: the shorter the stance phase, the less time the foot spends at the "far end", and the less likely it is to exceed the leg's reach.

Results:

| Entity | Baseline | Duty=0.42 |
| --- | --- | --- |
| C_5 | 39.3 | **28.6** |
| C_7 | 44.1 | 39.0 |
| C_8 | 13.1 | **74.9** |
| C_9 | 60.0 | **81.5** |
| Player | 10.9 | 10.5 |

**Mixed results**: C_5/C_7 improved, C_8/C_9 clearly worse. Not a consistent improvement, **reverted**.

## Back to Baseline and Re-verification

| Entity | Foot ground clearance | Median stance slip (two runs) |
| --- | --- | --- |
| Player | 2.1 cm | 10.9 / 11.0 |
| C_5 | 2.1 cm | 10.4 / 13.7 |
| C_8 | 2.1 cm | 5.7 / 18.7 |
| C_7 | 2.1 cm | 38~139 (large variance) |
| C_9 | 2.0 cm | 44~68 |

The player's two runs were almost identical (10.9 / 11.0), showing **the criterion itself is stable**; the differences between enemies are real, not measurement noise.

## Observation: C_7's Variance Is Extremely Large

For the same entity C_7, the left and right legs were 122.9 and 38.0 respectively, with p90 reaching 736. Its stance-segment duration was 0.27~0.37 s, noticeably longer than other entities (0.20 s) — at 146 cm/s but with a 0.37 s stance phase, it must cover 54 cm, far exceeding its 30 cm stride. **This is "a stretched stance phase but a stride that didn't keep up"**, a different root cause from C_9's problem.

## Current Status

| Item | Status |
| --- | --- |
| Player walking | natural posture, feet on ground, slip 11 cm/s |
| Enemy straight-line walking | normal |
| Enemy turning | still slipping (C_5/C_8 good, C_7/C_9 bad) |

## Lessons

**With a trustworthy criterion, rejecting is faster than modifying.** This round each path was judged with a single run, without the back-and-forth over "does it look right" after changing things that marked the previous rounds. Rejected directions also had their reasons clearly written down, to avoid repetition.

**The same phenomenon may have several mutually different causes.** C_5/C_8 and C_7/C_9 responded oppositely to the same parameter (with Duty 0.42 one improved and one worsened), showing that a single global parameter can't satisfy both — the next round should handle entities in groups, rather than continuing to search for a "universal value".

---

# Round 92 (2026-11-03): Splitting "foot slip" into three independent quantities

Previous rounds had been using a single number, "support-phase slip," and as a result this number mixed **three different things**
together, so every time one parameter was changed they canceled each other out. This round measures them separately.

## 1. Separating the three quantities

| Quantity | Meaning | How to measure |
| --- | --- | --- |
| Offset relative to rest | During the support phase the foot's position relative to the body should **sweep from front to back at constant speed** | `rdx/rdy/wdx` of `[FootCSV]` |
| Tracking error `trk` | How much the target requires the foot to move, versus how much the foot actually moved | The difference between (target point − rest point) and (actual − rest point) |
| Foot lift vs. stride | The ratio of foot-lift height to stride | Peak-to-peak values of `lift` and `fwd` |

## 2. Player vs. Colossus C_9 (same code, same moment)

| | Player | C_9 |
| --- | --- | --- |
| Tracking error `trk` | **0.14 ~ 0.47cm** | **151 ~ 194cm** |
| Support-phase `d` (hip→target distance) | 104 | 166.3 |
| Leg length L1+L2 | 104 | 166.4 |

The player follows almost perfectly (error <0.5cm), while C_9 cannot reach the target at all — the target exceeds the reachable range
by a full 150cm or more. **This is not a "turning" problem; it is "the leg can't reach the target point."**

## 3. Foot-lift height is completely out of proportion to stride

| Entity | Support-phase sole height | Swing-phase lowest point | Note |
| --- | --- | --- | --- |
| Player | 31.9 | 32.5 | Normal |
| C_5 | 18.9 | 20.4 | Normal |
| C_7 | 13.1 | 14.3 | Swing phase is actually lower than support phase |
| C_8 | 12.4 | 12.9 | Same as above |
| C_9 | 20.0 | 20.5 | Same as above |

**The "swing-phase lowest point" should be higher than the support phase (the foot is lifted), but in practice the two are nearly identical** —
which means these enemies' feet barely lift during the whole cycle; they merely move horizontally.
The player is the only one whose foot lift is correct.

## 4. What was changed this round and why it was reverted

**Change kept**: The function originally had two places advancing `S.GaitPhase` (`2.4+5.2*ratio` and
`2.4+12.6*ratio`); the legs followed the latter and the pelvis bob followed the former, at different rates —
the pelvis one was removed, so the bob now follows the real gait rhythm. Metrics unchanged (slip wasn't caused by it),
but a definite inconsistency was fixed.

**Attempt reverted**: Changed the increment of `P.Knee` from `D1 - D2` to the theoretically correct solution `D2 - D1`.
The result lifted the sole **2.1 → 102.9cm**, the foot raised into midair. This shows the signs of D1/D2 are paired with
the application direction of `SwingBone`; `D1 - D2` is the correct value in this coordinate system. Reverted and documented.

## 5. Conclusion and next steps

**The main cause of the current "enemy foot sliding" is not turning, but that the IK targets of the three-legged enemies (C_7/C_8/C_9)
exceed the reachable range.** All previous efforts of "along the velocity direction / shortening the support phase / adding lateral swing"
were merely describing "the consequences of not reaching," without touching the cause.

The correct approach for next steps:
1. First compute the **true reachable radius** of these enemies (the maximum horizontal margin from hip to ankle),
   and limit the amplitude of `Fwd` within this radius — instead of the current `leg length × 0.62`.
2. Foot-lift height must be **based on the support-phase sole height** (`lift` relative to the "support height"),
   not relative to the rest pose; otherwise the feet of long-legged bodies are always lower than the support height.
3. Verify both of these using this round's component quantities (`trk` / support-phase height).

## 6. Lessons learned

**When one number mixes three things, it proves nothing.** Previously, if `Slip` rose we reverted, if it fell we kept it —
in effect making noise-based judgments among three mutually canceling effects. After separating them, the "can't reach" problem
became obvious for the first time — and with a magnitude gap obvious from a simple player-vs-enemy comparison (0.4cm vs 190cm).

---

# Round 93 (2026-11-03/04): Locating "the foot isn't on the leg"

## 1. First measure the geometry clearly

The new diagnostic `-DebugReach` gives the static geometry of each body:

| Body | Hip height | Ankle height | Vertical drop | Bone length | **Reachable radius R** |
| --- | --- | --- | --- | --- | --- |
| Player | 134.0 | 30.0 | 104.0 | 104.0 | **2.1** |
| C_5 Guard | 117.5 | 16.0 | 101.5 | 102.9 | 17.0 |
| C_7 Hauler | 125.7 | 14.0 | 111.7 | 126.9 | 60.1 |
| C_8 Gardener | 127.9 | 10.0 | 117.9 | 129.5 | 53.6 |
| C_9 Colossus | 206.8 | 41.0 | 165.8 | 176.7 | 60.9 |

**The legs are essentially straight in the rest pose** (the player has only 2.1cm of horizontal margin left).
So "stride limit as a proportion of leg length" was never a constraint from the start — if the hip isn't lowered, the foot has no fore-aft travel.

## 2. Comparing the foot's real position against the leg (decisive data)

| Body | Distance from foot to **its own hip** | Bone length |
| --- | --- | --- |
| Player | 102.0 | 104.0 |
| C_5 | 99.3 | 102.9 |
| C_7 | 138.1 | 126.9 |
| C_8 | 116.2 | 129.5 |
| **C_9** | **214.9** | **176.7** |

C_9's foot is 215cm from the hip, while the bones total only 177cm — **the foot isn't at the end of the leg at all**.
Meanwhile its support-phase "displacement relative to the body" is only 11.1cm, while the body advances 21.6cm,
exactly half — the foot fails to follow the body half the time.

## 3. Hypotheses ruled out

| Hypothesis | Evidence | Conclusion |
| --- | --- | --- |
| Bone unit conversion wrong | `[Unit]` outputs 0.011~0.013, consistent across all five bodies | Ruled out |
| Leg bone parent-child chain wrong | `[Chain] thigh_L(parent=torso)` correct for all four legs | Ruled out |
| Different fore/aft leg bone lengths cause IK deviation | Added `-PerLegLen` to use each leg's own bone length: C_5 6→24 **worse** | Ruled out and reverted |
| Foot-lift height out of proportion to stride | Swing-phase `lift` median: Player 6.0 / C_7 6.1 / C_9 4.9 | Normal |
| Body horizontal position jumps | `v_p90/v_med` ≈ 1.07, no jumps | Ruled out |

## 4. Next steps (determined, not yet done)

C_9's `A=17.5°, K=40.4°` are used to compute both `P.Hip` and `P.Knee`,
and the sign `P.Knee = D1 - D2` that "balances the landing height" is precisely the result of
distorting the angle relationship back then to keep the foot from sinking into the floor. What needs fixing is:

1. Use `P.Hip = -(Base + A*BendSign - Theta1Rest)`, `P.Knee = K` and apply directly
   the world angles solved by IK (no longer going through the `D1 - D2` incremental path);
2. Confirm that `SwingBone`'s rotation axis equals the component Y on every body (the thigh bone's own
   bending axis); quadruped thighs carry a 45° yaw, which must be verified first;
3. Use `trk` (target within 0.5cm; the player is currently 0.8) for verification,
   no longer looking at indirect quantities like `slip`.

## 5. Lessons learned

**To judge "whether the foot is on the leg," simply measuring the foot-to-hip distance is enough.** Before this round
we wandered through five rounds of parameters, when there was actually a one-line criterion: foot-to-hip > bone length ⇒ necessarily wrong.
Every step should start by finding such a "falsifiable in one line" quantity.

**The measuring tool itself can be wrong.** This round the CSV parser matched `d=` to a different number,
once producing the absurd conclusion that "the target distance is negative." When you see impossible numbers, suspect the parser first.

---

# Round 96 (2026-11-04): The tracking metric itself was wrong four times

Last round I announced "found it: the foot isn't on the leg." This round proved **that conclusion came from a faulty measurement**,
but also uncovered three genuinely existing problems. The main value of this round is **fixing a repeatedly misleading metric**.

## 1. `trk` (IK tracking error) took four versions to get right

| Version | Expression | Why it's wrong |
| --- | --- | --- |
| 1 | `(FW - CompLoc) - DbgTarget` | World coords minus component origin, then minus a component-space point — directly subtracting quantities with different baselines |
| 2 | `InverseTransformPosition(FW) - DbgTarget` | C_9 **divides by component scale 0.5**, amplifying the error 2× and showing "extremely small" |
| 3 | `BoneComp - DbgTarget` | `GetBoneMatrix` returns world coords, another mix-up |
| 4 | Take "relative to hip" on both sides | Quadruped legs are naturally at ±90cm on the sides, counted as error |

**Lesson: the three curves `trk`, `slip`, `fz` often contradict each other because I was comparing quantities in different coordinate systems.**
Every quantity must state which coordinate system it is in, and the two quantities being compared must be in the same system.

## 2. Real problems found

### 1. Stride direction only follows "body forward"

Enemies strafe, back up, and circle, but the support foot always retreats along the body's forward direction.
Measured C_8: body translates toward (-X,-Y), foot retreats toward +X — **directions are opposite**, doubling the ground-relative speed.

Fix: use the components of the actual velocity direction in component space, splitting it into two strides: forward + lateral.

**Result: C_8 24.9 → 14.0, C_5 22.5 → 16.2, player unchanged (10.7). Kept.**

### 2. Torso rotation happens after leg IK

The legs are child bones of the torso. IK solves angles in the "torso unrotated" coordinate system,
then the torso is rotated by Lean/Roll/Yaw, dragging the whole leg along.

C_9, with 176cm legs, is flung the worst: the foot is pushed to -97.6cm in front of the hip (should be +12).

**After the change slip got worse instead (C_5 7→27, C_7 44→83), reverted.**
But the fact that "the ordering itself is wrong" is certain; it needs a matching fix to the `Rest` baseline to take effect.

### 3. The criterion for `BendSign` (knee-bend direction) is unreliable on quadrupeds

Original criterion: `V1.X >= 0 → bends backward`, on the premise "foreleg V1.X<0, hindleg V1.X>0".

Measured C_9:
- Foreleg thigh_L has V1.X = **+36.4** (positive)
- Hindleg thigh_BL has V1.X = **-36.4**

**Exactly the opposite of the premise in the comment.** So forelegs were solved as hindlegs.
Three alternative criteria (ankle position, target position, hip center-of-mass offset) were all tried, **none improved the metrics**,
indicating the true relationship between the current skeleton's knee-bend direction and the inverse-solution sign is still unclear.

## 3. Net result of this round

| Item | Status |
| --- | --- |
| Stride along actual movement direction | **Kept** (C_5/C_8 improved) |
| Torso rotation ordering | Reverted (the change itself is correct, but needs companion adjustments) |
| BendSign criterion | Reverted (all three alternatives ineffective) |
| Current metrics | Player 10.8 / C_5 23.9 / C_7 34.4 / C_8 22.8 / C_9 54.4 |

Visual check: C_8's walking posture is normal, feet on the ground.

## 4. Lessons learned

**Four consecutive versions of the metric were wrong, showing I was guessing coordinate systems rather than verifying.**
Correct approach: first write a one-line assertion (e.g. "at rest the foot-to-hip distance must equal the leg length"),
and make every measurement pass this check first.

**"The premise in a comment" is also an unverified assumption.** The comment "foreleg V1.X<0" may never
have been verified on a quadruped, yet it directly determines the sign of the IK.

---

# Round 97 (2026-11-04): Chasing a nonexistent bug, only to find the log was folded

The first half of this round was mostly spent chasing a **false lead**; the second half found the real cause.
Write up the process first, because "how I was misled" is more worth recording than "what was fixed."

## 1. Cause: a judgment left over from last round

At the end of last round I wrote:

> Correct approach: first write a one-line assertion (e.g. "at rest the foot-to-hip distance must equal the leg length"),
> and make every measurement pass this check first.

This round I went and did this assertion. Result:

| Body | Leg | Ankle−hip (sagittal) | Hip−ankle (vertical) |
| --- | --- | --- | --- |
| Player | L | 0.0 | 103.5 |
| C_5 | L | 8.2 | 101.2 |
| C_9 | L | 12.0 | 165.8 |

**All normal.** The static baseline is fine.

## 2. Then I started chasing a nonexistent bug

Continuing to look at per-frame data, I found two "impossible" phenomena:

1. C_9's BL and BR legs have **identical** `P.Hip/P.Knee`
   (php -46.6..-39.2, pkn 93.9..95.6), yet their foot positions differ by **115cm**.
2. C_9's `fz / ankz ≈ 0.5`, exactly equal to its component scale.

Both phenomena point to "left-right leg mirroring messed up" or "scale applied twice."
Three experiments along this line were all failures:

| Experiment | Result |
| --- | --- |
| Changed the IK reachable limit to "rest \|hip−ankle\| × 1.005" | Support segment count 35→1~4, slip all >100, feet can't reach the ground |
| Moved torso rotation before IK | C_5 7→27, C_7 44→83, all worse |
| Three `BendSign` criteria (ankle position/target point/hip center of mass) | None improved the metrics |

## 3. The truth: the log was folded, the data was fake

Repeatedly seeing results like "only 1~4 support segments, player slip 137" — **abnormal even for the player** —
I finally went and checked the sampling rate:

| Run | Sample points per entity | Adjacent interval |
| --- | --- | --- |
| r602 (normal) | ~740 | **0.0129s** |
| r608 (abnormal) | ~50 | **0.4000s** |

**Sampling dropped by 30×.** At 0.4s intervals,
"max foot displacement within a support segment / segment duration" will of course produce absurd values like 130+ —
the animation isn't broken; it's that **the statistical data itself had a 30× off time baseline**.

Reason: UE logs have a "duplicate line folding" mechanism. Lines like `[FootCSV] owner=... leg=L t=...`
have nearly identical prefixes across all legs, so they were heavily merged.

**Fix**: append a `k=` field that changes each frame to the end of the log line, breaking the "exactly identical" judgment.

After the fix, sampling returned to 0.0229s and the support segment count recovered (45/82/26/86/45).

## 4. The real gain of this round

### 1. A global "data credibility" check

For any measurement, first look at the **sampling interval**:

```
gap_med should be ≈ 1/frame rate (0.01~0.02s)
gap_med > 0.1s  ⇒ this data is unusable
```

All previous conclusions like "enemies got worse/better in some run" are noise whenever the sampling interval is abnormal.
**Including several comparisons I myself used in Round 91.**

### 2. Suspect the data before chasing a bug

C_9's BL/BR contradiction of "identical parameters but foot positions differ by 115cm"
doesn't hold at all under normally sampled data — it was caused by folding stitching together two frames from different times.

## 5. Current status (normal sampling)

| Entity | Support slip median | Segment count |
| --- | --- | --- |
| Player | **10.5** | 45 |
| C_5 | 23.9 | 45 |
| C_7 | 54.8 | 82 |
| C_8 | 21.8 | 26 |
| C_9 | 53.9 | 86 |

Consistent with the end of Round 96 (Player 10.8 / C_5 23.9 / C_7 34.4 / C_8 22.8 / C_9 54.4).
No net changes this round, but **a pitfall that would have distorted all subsequent measurements was filled in**.

## 6. Lessons learned

**"Impossible values" have two sources: the model is wrong, or the measurement is wrong.**
This round I first assumed the model was wrong and spent most of the round chasing a nonexistent problem.
Next time you encounter a "how is that possible" phenomenon, the first thing should be to look at the **raw samples**, not to change the model.

**Any statistics script should print the sampling rate first.** This is a one-line self-check,
but it can block 80% of this round's wasted work.

---

# Round 98 (2026-11-04): Finding a criterion independent of frame rate

Last round I fixed the sampling folding, and this round I wanted to continue with clean data. As a result **the machine's frame rate dropped to 5fps**,
and slip statistics became unusable again. But this time I didn't panic — I switched to a criterion unaffected by frame rate.

## 1. Frame-rate problem (not resolved this round)

| Time | Run | Frame rate |
| --- | --- | --- |
| Morning | r602 | **107.6 fps** |
| Afternoon | r609 | 42.0 fps |
| Evening | from r614 | **4.6~5.0 fps** |

Tried `-NoThrottle`, `-UseVSync`, lowering the resolution to 640×360 — all ineffective.
CPU load was only 2%, so the machine wasn't busy; **it was UE's power-saving throttling**.
At 5fps, the error in "foot displacement within a support segment ÷ segment duration" can reach 30× — all slip numbers this round are unusable.

## 2. Switching to a different criterion: the linear slope of hip angle versus stride

Slip statistics depend on a time baseline, but **geometric relationships do not**. So I switched to:

    Perform a linear regression of (fwd, P.Hip) for each frame; slope = how many degrees of hip angle per 1cm of stride.

This quantity is completely independent of frame rate (the slope computed at 5fps and 107fps is nearly identical).

**Result (before the change)**:

| Body | Foreleg slope | Hindleg slope | r² |
| --- | --- | --- | --- |
| Player | -0.57 | -0.56 | 0.23 |
| C_5 | -0.79 | -0.79 | 0.61 |
| C_8 | -0.54 | -0.55 | 0.74 |
| C_7 | -0.56 | **-0.49** | 0.72~0.81 |
| **C_9** | **-0.42** | **-0.26** | 0.45~0.74 |

Two findings:
1. **Quadrupeds' hindleg slopes are systematically lower** (C_9 is only 62% of its foreleg)
2. **C_9 has the lowest overall slope** (-0.26~-0.42, versus the player's -0.57)

## 3. Cause: the A term is canceling out base

Hip angle θ1 = base + A·BendSign.

- Foreleg BendSign = -1 → as base increases, A also increases; the two **add in the same direction**
- Hindleg BendSign = +1 → as base increases, A increases; the two **cancel in opposite directions**

Thus the hindleg's hip angle only travels 60% of the foreleg's. This directly explains why "quadrupeds with hindlegs have the worst slip."

## 4. Experiment: keeping A at its rest value (-BaseOnly)

Let only base vary with stride, with A fixed at the value computed from rest geometry.

**Result:**

| Body | Foreleg slope | Hindleg slope | r² |
| --- | --- | --- | --- |
| Player | -0.567 | -0.562 | **1.00** |
| C_5 | -0.579 | -0.562 | **1.00** |
| C_8 | -0.504 | -0.492 | **1.00** |
| C_7 | -0.522 | **-0.513** | **1.00** |
| C_9 | -0.350 | **-0.349** | **1.00** |

**Forelegs and hindlegs are completely consistent, all r² = 1.00.** Hip angle and stride became strictly linear,
and the canceling effect of `A` disappeared completely. C_9's slope rose from -0.26 to -0.35.

Visual check: the player's walking posture is normal, with clear thigh-knee bending and distinct foot lift.

## 5. Why it is not set as default for now

`-BaseOnly` is currently just a switch, off by default. Reasons:

1. **Slip verification can't be done** (frame rate 5fps), so we can't confirm whether it's better in real walking
2. `r²=1.00` means the relationship got "cleaner," but cleaner doesn't mean "the foot is pinned" —
   whether the foot can be pinned also depends on whether base's sign and magnitude strictly match the body's displacement

**First thing next round**: in an environment that can run at full frame rate, retest slip with `-BaseOnly`, then decide whether to promote it.

## 6. Lessons learned

**Choose criteria that "still hold when measurement conditions change."**
Slip depends on a time baseline and is useless once the frame rate is messed up; whereas "the slope of hip angle versus stride" is a geometric quantity,
measured the same at 5fps and 107fps — this round it saved the entire round's work.

**`r²` is an underrated diagnostic quantity.** Previously I only looked at means, which couldn't show "whether hip angle and stride are linearly correlated."
This time r² rose from 0.23~0.81 to 1.00 across the board, making it obvious at a glance that the relationship was straightened out.

---

# Round 99 (2026-11-04/06): Colossus foot slip reduced to match the player

After the frame rate recovered (105fps), this round both overturned the previous round's conclusion and found the true cause of C_9's foot sliding.

## 1. First, overturning last round

Last round, using `-BaseOnly` (hip angle follows only base, A uses the rest value) got r²=1.00,
and I wrote at the time "geometrically very clean, but slip not verified."

This round, a supplementary test at 105fps:

| Body | Default | `-BaseOnly` |
| --- | --- | --- |
| Player | 10.8 | **34.9** |
| C_5 | 15.1 | **69.1** |
| C_7 | 59.5 | **85.6** |
| C_8 | 11.2 | **74.9** |
| C_9 | 54.9 | 68.0 |

**Worse across the board, even the player reached 34.9.** The experimental code was deleted in full and marked "overturned."

**Lesson: a high r² only means "the relationship is linear," not "the foot is pinned."**
Last round I nearly mistook "a cleaner relationship" for "better."

## 2. The `trk` metric is finally fixed (fifth version, also the last)

The first four versions were all wrong due to mixing coordinate systems. This time I noticed a decisive fact:

```
C_9: target raised 7.7cm in component space
     component scale 0.5 → in world it should rise only 3.85cm
     measured foot rise 3.4cm  ← matches exactly
```

**It wasn't IK that was wrong; `trk` was directly subtracting a component-space quantity from a world-space quantity.**

After changing both sides to convert to world space first:

| Body | trk old (wrong) | trk new |
| --- | --- | --- |
| Player | 0.7 | 0.7 |
| C_8 | 26.1 | **1.1** |
| C_5 | 38.5 | **1.3** |
| C_9 | 118.8 | **4.3** |
| C_7 | 102.6 | **5.3** |

**IK was always accurate** (worst 5.3cm). All previous conclusions like "the foot isn't on the leg" or "IK can't reach the target" are void.

## 3. The real cause: component scale halves the target point's world displacement

Since IK is precise, slip can only come from the target point itself. New criterion:

    The foot's displacement velocity relative to the body ÷ body velocity  →  should equal 1.00 (foot stationary in world space)

| Body | Body velocity | Foot relative velocity | Ratio |
| --- | --- | --- | --- |
| Player | 140.0 | 140.0 | **1.00** |
| C_8 | 200.7 | 200.9 | **1.00** |
| C_7 | 143.4 | 130~171 | 0.77~1.19 |
| **C_9** | 107.8 | 49~64 | **0.46~0.59** |

**C_9's foot only retreats half as much as it should.** Reason:
The target point adds `Fwd` in **component space**, and C_9's component scale is 0.5 —
the target retreats 22.6cm in component space, but only 11.3cm in world space,
while the body still travels 108cm/s in world space. **The foot can only be dragged along.**

## 4. Fix

In `SolveLeg`, divide the displacement amount by the component scale (convert to component-space units):

```cpp
const float W2C = 1.f / max(CompScale, 0.01f);
const FVector Target = Rest.Ankle
    + AxisFwd  * (P.Fwd  * W2C)
    + AxisUp   * (P.Lift * W2C)
    + AxisRight* ((P.FwdLat + P.OffLat) * W2C);
```

Only compensate **displacement**, not angles (angles are independent of scale).

## 5. Results (median of three runs)

| Body | Before | After (three runs) | Conclusion |
| --- | --- | --- | --- |
| Player | 10.8 | 10.8 / 10.7 / 10.8 | Unchanged |
| **C_9** | **55.8** | **12.1 / 11.0 / 12.8** | **Down 78%, matches the player** |
| C_8 | 7.3 | 7.5 / 10.7 / 6.1 | Unchanged (scale 1.0, unaffected) |
| C_5 | 23.9 | 27.1 / 22.6 / 37.6 | About the same |
| C_7 | 66.5 | 58.5 / 68.0 / 40.1 | Still high, another cause |

C_9's ratio changed from 0.46~0.59 to **0.95~1.12**; the foot is now truly pinned.

Visual check: C_8 walks upright, natural posture, no distortion.

## 6. Remaining problems

C_7 (~60) and C_5 (~25) are still high, and **fluctuate greatly between runs** (C_7 40~68).
Both have component scale 1.0 and are unaffected by this fix, indicating another cause, and the current criterion has insufficient resolution for them.

## 7. Lessons learned

**I fell into the same "coordinate-system mix-up" pit five times.** `trk` took five versions to get right.
Each time it was because "the two numbers looked comparable" so I subtracted them directly.
**Before comparing two quantities, first write down each one's coordinate system.**

**Scale is a hidden coefficient.** C_9's 0.5 scale gave all "length"-type targets and diagnostics a half-off bias,
and it happens to be the only entity with a scale — so only it showed 5× slip.
When investigating "why only one entity is abnormal," first check whether it has any **unique property** (here: scale 0.5).

---

# Round 100 (2026-11-06/07): Colossus solved, hauler's foot slip halved

## 1. Last round's `-BaseOnly` has been deleted

In a supplementary test at 105fps, the scheme "hip angle follows only base, A uses the rest value" made slip **worse across the board**
(Player 10.8→34.9, C_5 15.1→69.1, C_8 11.2→74.9). The experimental code was deleted in full.

**r²=1.00 only means "the relationship is linear," not "the foot is pinned."**

## 2. `trk` fifth version is finally correct

The first four versions all mixed coordinate systems. Decisive fact:

```
C_9: target raised 7.7cm in component space, scale 0.5 → world rises only 3.85cm
     measured foot rise 3.4cm — matches exactly
```

After changing both sides to convert to world space: Player 0.7 / C_8 1.1 / C_5 1.3 / C_9 4.3 / C_7 5.3.

**IK was always accurate**; all old conclusions like "the foot isn't on the leg" are void.

## 3. The colossus's real cause: component scale halves the target's world displacement

Criterion: `foot velocity relative to body ÷ body velocity`, should = 1.00.

| Body | Body velocity | Foot relative velocity | Ratio |
| --- | --- | --- | --- |
| Player | 140.0 | 140.0 | **1.00** |
| C_8 | 200.7 | 200.9 | **1.00** |
| **C_9** | 107.8 | 49~64 | **0.46~0.59** |

The target point adds `Fwd` in **component space**, and C_9's scale is 0.5 —
the target retreats 22.6cm, only 11.3cm in world space, while the body still travels 108cm/s.

Fix: `Target = Rest.Ankle + Fwd * (1/CompScale) + ...` (compensate displacement only, not angles).

**Result: C_9 slip 55.8 → 11.0~12.8, matching the player (ratio 0.95~1.12).**

## 4. Incidentally discovered and reverted "locking stride during the support phase"

The idea was good (lock the stride on landing so the support phase is unaffected by speed changes), but measurements showed C_7's foot speed
rising from 14 to 58.5 — after locking, the swing phase used the new speed and the support phase the old speed, with a discontinuity at foot switching. Reverted.

## 5. Hauler C_7: finding the direction bug

Frame-by-frame analysis of C_7's support segments:

```
Body movement direction: 93.7°  (almost toward +Y, i.e. walking sideways)
Foot relative movement direction: -5.8°  (almost toward +X, i.e. body forward)
The two differ by 100°
```

Investigation found `MoveDirSmoothed` stuck at 0°:
`FMath::VInterpNormalRotationTo` **did not** rotate the vector to the target direction
(velocity (-64.8, 130.3) has direction 116°, but what was computed was (1,0), direction 0°).

After switching to my own angle interpolation (`FindDeltaAngleRadians` + max 400° per frame):

| Body | Before | After (two runs) |
| --- | --- | --- |
| Player | 10.8 | 10.8 / 10.8 |
| **C_9** | **55.8** | **11.1 / 11.7** |
| **C_7** | **60~66** | **25.6 / 35.3** |
| C_5 | 23.9 | 19.8 / 28.5 |
| C_8 | 7.3 | 19.4 / 23.5 |

C_8 rose slightly (it always walks straight at full speed and never depended on the direction fix).

## 6. Leftovers

1. C_7 still has 25~35, p90 about 200 — indicating intermittent large-slip segments remain unlocated
2. C_8 rose from 7.3 to ~20, needs a separate look at whether the angle interpolation skewed it
3. `MoveDirSmoothed` and `Velocity` still have a residual deviation of 20~40°, cause unclear

## 7. Lessons learned

**`VInterpNormalRotationTo` cannot be used to "make one direction vector chase another."**
Its semantics are not angle interpolation; in practice it degrades to no rotation. Engine functions like this that "look like they should work well"
must be **verified with a one-line assertion** (in this case: assert `MoveDirLocal` and `Velocity` are in the same direction).

**"Which way the body moves" and "which way the body faces" are two different things.**
Eight rounds of code assumed "retreat along the body's forward direction," which was completely wrong when enemies strafe.

---

# Rounds 101-102 (2026-11-07): Extending the level skeleton

## 1. Scope

Per the user's decision: **for the connected new area, build the skeleton first**.

Open an 800cm-wide gap in the far wall of the existing arena (X=1800),
connect it with a 600cm-long corridor, and lay out a second combat arena:

| Part | Range | Content |
| --- | --- | --- |
| Corridor | X 1800..2400, Y ±400 | Floor 3×7 tiles, 2 wall segments on each side, 6 lights |
| New arena | X 2400..5400, Y ±900 | Floor, 8 segments each for north/south walls, 5 segments for east closing wall |
| Structures | — | 10 pillars, 2 gantries, 2 door frames |
| Lighting | — | 27 lights (corridor 6 / main lighting 8 / fill 1 / gate 1 / pillar bases 10) |

All extension actors carry the `ExtRegion` tag and are repeatable (idempotent).

## 2. Three pitfalls encountered

### 1. The newly laid floor turned white

In the first version's screenshot, the new area's floor showed **dazzling white lines** along the 400 grid.

Cause: `SM_Env_Floor` has 4 material slots, slot 0 is the engine's `BasicShapeMaterial` (pure white).
Each of the original 56 floor tiles explicitly set
`override_materials = [M_Steel, M_SteelLight, M_Joint, M_Copper]`,
while the 48 tiles newly generated by the script had empty arrays → falling back to pure white.

**Lesson**: when generating level pieces, **material overrides are not inherited automatically**.
Each piece must be set exactly like the same-named piece in the original level, slot order and all.

### 2. Added dozens of lights but no visible brightness

The lights' positions, intensity, radius, and color were all correct, yet the image didn't change.

The two real reasons:

- **Shadows**: all 45 point lights had `cast_shadows=True`, saturating the shadow map budget.
  These lights are only for ambient lighting; after turning off shadows, cool/warm light pools appeared on the floor immediately.
- **Re-running the geometry script deleted the lights too**: the lights also carry the `ExtRegion` tag,
  and the cleanup logic "delete all actors with this tag" → all lights went out.
  Fix: skip the `ExtLight_` prefix during cleanup.

### 3. `unreal.Color`'s constructor order is (B, G, R, A)

The first version passed RGB, and reading it back gave `b=170 g=200 r=255` — cool and warm colors all reversed,
cool lights came out orange-ish, further reinforcing the illusion that "the lights weren't on."

## 3. Current status

| Item | Status |
| --- | --- |
| Corridor connection | Done, can walk directly from the arena into the new area |
| Floor / walls | Done, materials consistent with the original area |
| Doorway | Done (the middle of the original far wall was already open, only the door frame was added) |
| Lighting | Done, cool/warm zones, warm light at pillar bases for depth |
| Cover / enemies | **Not done** (per the "skeleton first" scope) |

Verification screenshot: `docs/ext_shots/final_ext.png` (looking into the new area from the doorway).

## 4. Reusable scripts

| Script | Purpose |
| --- | --- |
| `ue/Scripts/build_ext_region.py` | Extension geometry (idempotent, repeatable) |
| `ue/Scripts/build_ext_lights.py` | Extension lighting (idempotent) |
| `ue/Scripts/probe_ext_assets.py` | Query asset bounding boxes |
| `ue/Scripts/probe_floor_mat.py` | Query floor material overrides (key to finding the white lines) |

## 5. Lessons learned

**When "adding something has no effect," check two things first: is it a switch (shadows/visibility), or is the object still there?**
Both causes applied this round: saturated shadows + re-execution deleted the lights.
What the eye saw as "lights not on" was actually "lights not there" and "lights eaten by shadows."

**An idempotent script's deletion condition must be narrow.** Tags are shared; lights and geometry can't be judged by the same prefix.

---

# Round 103 (2026-11-08): IdolMech ornament import

## 1. Task

The user provided `art_src/idol/IdolMech.glb` (11 MB) and asked to import it into
`RobotGame/Art/Props/IdolMech`, place it in the level as `SM_IdolMech`, and scale it up 8~10×.

## 2. Model measurements

| Item | Value |
| --- | --- |
| Meshes | 1, 203k vertices / **398k triangles** |
| Dimensions | 0.29 × 0.62 × 1.00 meters (already Z-up vertical in glTF) |
| Color | **No textures, relies entirely on vertex colors** (material named M_IdolMech_VC, VC = Vertex Color) |
| Pivot | Not at the geometric center: sole -53.87 / top of head +50.09 (cm, in UE) |
| Orientation | Faces **+X** (confirmed by Blender four-view: +X shows chest armor and face, -X shows the spine) |

## 3. The detour: FBX import lost the material

The first version went through Blender converting to FBX and then importing; the material degraded to
`/InterchangeAssets/.../MI_Default_Opaque_DS` (the engine's default gray instance),
making the model look pale overall. Investigation revealed: **the level content already had a correct glTF import**
(`Materials/M_IdolMech_VC` + `StaticMeshes/SM_IdolMech`),
with `MaterialExpressionVertexColor` inside the base material — all colors are in the vertex data.

Action: deleted the wrong assets from the FBX import and moved the correct ones to the user-specified
`Art/Props/IdolMech/SM_IdolMech` path.

**Lesson**: before importing, check whether the asset already exists and whether the existing one is correct;
FBX conversion isn't a cure-all — only importing the glTF source directly through the glTF importer preserves the vertex-color material.

## 4. Second pitfall: `unreal.Rotator`'s positional arguments are (Roll, Pitch, Yaw)

After placing it in the level, the model was "upside down" (legs up, head down). Repeatedly adjusting pitch/yaw didn't help;
finally I used `unreal.Rotator(10, 20, 30)` to read back and verify:

```
pitch=20.0  yaw=30.0  roll=10.0
```

**The positional argument order is (Roll, Pitch, Yaw)**, not C++ `FRotator`'s
(Pitch, Yaw, Roll). I had passed 180 to the wrong axis earlier, hence "upside down."

**Lesson**: always use keyword arguments for the Python-bound Rotator
`unreal.Rotator(roll=, pitch=, yaw=)`; don't rely on positional order.
After fixing, I confirmed the model's natural pose is already standing; **no flipping is needed**.

## 5. Determining orientation: rendering four views in Blender

A UE screenshot round takes minutes, and front/back are hard to tell apart by eye. I switched to rendering in Blender's background
(EEVEE) from the four directions +X/-X/+Y/-Y (`tools/blender/render_idol_views.py`),
confirming in seconds that the front faces +X; the player enters from the -X side corridor, so the final `yaw=180`.

## 6. Final placement

| Item | Value |
| --- | --- |
| Position | (4750, 0), centered near the far gate of the new area |
| Scale | 9.0 → actual height **9.36 meters** |
| Rotation | pitch=0, yaw=180 (facing the direction the player comes from), roll=0 |
| Grounding | Used the world bounding box to correct the sole to Z=0 (minZ can't be hand-computed after rotation) |
| Tag | `IdolMech`, script is idempotent and repeatable |

Verification images: `docs/idol_views/idol_in_level_front.png` (3/4 view),
`idol_in_level_34.png` (front view, directly behind the gantry).

Also added two verification camera positions `-IdolCam` / `-IdolCam2` (DebugCamMode 15/16),
and hit a pitfall with UE's **Fov being the horizontal field of view**: at 16:9 the vertical coverage is only about 36°,
so a 13m distance couldn't fit the 9.36m statue; the camera had to retreat to 16m to capture it all.

## 7. New scripts

| Script | Purpose |
| --- | --- |
| `ue/Scripts/tidy_idol_assets.py` | Asset cleanup (delete wrong, keep right, move to correct path) |
| `ue/Scripts/place_idol_mech.py` | Placement (idempotent, includes bounding-box grounding correction) |
| `ue/Scripts/probe_idol_rot.py` | Validator for Rotator argument order |
| `tools/blender/render_idol_views.py` | Four-direction rendering to determine orientation |

---

# Round 104 (2026-11-09): Building industrial cover and props with free Cosmos assets

## 1. Task and channel

The user gave `https://cosmos.leartesstudios.com/free` and asked to keep improving the scene with free assets.
The user chose: **industrial cover + props to fill the new area**, via the **public preview glTF channel**.

Survey results:

| Item | Conclusion |
| --- | --- |
| Total free assets | 78 (API `GET api.cosmos.leartesstudios.com/products/free?page=N`) |
| Official download | `POST /products/download/{slug}` returns **401 "You need to sign in first"** — even free requires login |
| Usable alternative channel | The glTF used by the web 3D previewer is on a **public CDN**: `cdn.cosmos.leartesstudios.com/viewer/{folder}/`, containing LOD0 geometry `.bin` + 4K PBR textures (BaseColor/Normal/ORM), no login needed |
| Asset details | `details.gltf` from `GET /products/{slug}` gives the preview address; `object_size` / `polycount` give size and polygon count |

**Key judgment**: official download requires login, but the preview glTF is public with complete geometry and textures —
this matches the import path of IdolMech.glb in the previous round and can be landed via an offline pipeline.

## 2. Pipeline (offline, no login dependency)

`tools/cosmos_build.py`: download glTF → resize textures to **1024** with PIL (originals 4K,
40~120MB per asset) → pack into a **single-file GLB** (geometry bin bytes preserved as-is,
no Blender re-export, so UV/normal/LOD0 precise data isn't lost; resized textures appended as
bufferViews, and image uris changed to bufferView indices).

All 12 selected assets packed successfully (3~14MB each, original 4K total ~700MB → ~90MB).

`ue/Scripts/import_cosmos_assets.py`: uses UE 5.8's built-in glTF (Interchange)
to batch-import into `/Game/RobotGame/Art/Props/Cosmos/<slug>/`.

**Two verified points**:
- Units: glTF is in meters, Interchange automatically ×100; `cs1-pipe` imports to 13.9cm
  corresponding to the source 0.14m — correct size.
- Pivot: these meshes' **soles are already aligned to z=0** (bbox minZ=0.00), so when placing,
  the actor Z can directly use the floor height; no need to add half-height as with IdolMech.
- Materials: the importer auto-generates Material + BaseColor/Normal/ORM Texture2D,
  with PBR material function nodes wired up, no manual override needed.

## 3. The 12 selected assets (industrial cover + props)

| Category | slug | Dimensions (cm) |
| --- | --- | --- |
| Cover | ww2-sandbag-stack-02b-smoked (sandbag stack) | 157×375×57 |
| Cover | met-barrel01-set01 (barrel set) | 151×132×83 |
| Cover | met-wooden-crate01a (wooden crate) | 40×65×21 |
| Cover | ww2-fridge (old fridge) | 80×67×150 |
| Cover | ww2-drawer-smoked (drawer cabinet) | 137×59×105 |
| Cover | ww2-field-fences-01a (field fence) | 300×200×180 |
| Focal point | pad-street-lamp-overgrown (street lamp) | 63×72×344 |
| Industrial piece | rps-fire-extinguisher-02 (fire extinguisher) | 35×34×61 |
| Industrial piece | ww2-heater-smoked (stove) | 53×54×161 |
| Wall-mounted | cs1-wallfanhatch (fan grille) | 116×30×116 |
| Wall-mounted | cs1-wall-light-6 (wall lamp) | 22×42×72 |
| Decoration | cs1-pipe (pipe) | 14×4×5 |

Excluded: Double Barrier / Wired Fence etc. **have no preview glTF** (unusable);
plants/trees/dining tables etc. have extremely high polygon counts or don't fit the style.

## 4. Placement (31 instances)

`ue/Scripts/place_cosmos_props.py`, all tagged `CosmosProp`, idempotent and repeatable.

Layout: new area X 2400..5400, Y ±900, gantries on the x=3200/4400 centerline,
statue on the x=4750 centerline — the **centerline is kept clear** as a visual corridor "entry → statue,"
with cover scattered on both sides at x 2600..4300.

First-version flat-view verification (`cosmos_view.png`) exposed two problems, both fixed:
1. **Cover too small and too scattered** → wooden crates changed to three-layer stacks (3 instances), sandbags/barrels grouped closer
2. **Wall-mounted pieces completely invisible** → the first version placed them at y=±865, right in the narrow gap between the perimeter wall (y=±900)
   and the pillars (y=±840); moved them to the open space between two pillar segments at y=±790,
   visible from the center of the arena.

Second-version verification (`cosmos_view2.png`): cover grouped, wall lamps visible, central corridor clear,
and the composition of the gantry framing the statue preserved.

## 5. SM6 / Nanite popup

After import, the editor popped a "Nanite requires SM6" warning. Diagnosis:

- The 12 newly imported Cosmos assets all have **Nanite = False** (max 100k polygons, not needed anyway)
- A full-project scan found 2 with Nanite on: `SM_IdolMech` and `SM_IdolMech_Poisson`
  (the 398k-polygon statue from the previous round)
- The project's `DefaultEngine.ini` has an explicit agreement: **deliberately do not override any rendering settings**
  (historically hit a big "all black" pitfall), so SM6/D3D12 were not changed

Per the user's decision: **turn off the statue's Nanite**, don't touch project settings.
After saving with `fix_idol_nanite.py`, a full-project rescan = **0 Nanite assets**, eliminating the popup's root cause.
(The reading was False→False, meaning the on-disk asset was already off; previously it was an unsaved state in editor memory;
saving synced it up.)

## 6. New scripts / camera positions

| File | Purpose |
| --- | --- |
| `tools/cosmos_probe.py` | Probe whether the public preview glTF is retrievable |
| `tools/cosmos_table.py` | Batch-fetch asset dimensions/polygon counts/preview availability |
| `tools/cosmos_fetch.py` | Single-asset download (for debugging) |
| `tools/cosmos_build.py` | **Main pipeline**: download → resize → pack GLB |
| `tools/blender/verify_cosmos_glb.py` | Verify GLB structure and textures |
| `ue/Scripts/import_cosmos_assets.py` | Batch import into UE |
| `ue/Scripts/place_cosmos_props.py` | Placement (idempotent) |
| `ue/Scripts/probe_cosmos_nanite.py` | Nanite status diagnostic |
| `ue/Scripts/fix_idol_nanite.py` | Turn off the statue's Nanite |

Added verification camera positions `-CosmosTop` (top-down, DebugCamMode 17) and
`-CosmosView` (eye level at the entrance, 18).

## 7. Experience

**"Requires login" doesn't mean "can't get it"**: first look for things the page is already publicly displaying
(3D previewer, cover CDN); you can often get usable geometry and textures.
But note this is only the **preview LOD**; the full LOD/collision/native BP from the official package aren't there.

**Packing a GLB offline is more reliable than re-exporting through Blender**: original bin bytes are preserved as-is,
only textures are resized, avoiding re-export loss of UV/normals/material slots (the previous round's FBX import losing the vertex-color material
is a cautionary example).

**Scan the whole project before changing settings**: an SM6 popup nearly had someone changing global rendering config;
one scan revealed it was just Nanite on two legacy assets, which could simply be turned off.

---

# Rounds 105-106 (2026-11-09): Fab investigation + switching to CC0 fully automated assets

## 1. Fab / Quixel Megascans: why it wasn't used

The user gave `fab.com/sellers/Quixel Megascans`. Investigation conclusion:

| | Cosmos (last round) | Fab / Megascans |
| --- | --- | --- |
| Anonymous direct link | Public CDN preview glTF | **None** |
| Acquisition | I download directly | Must log in with Epic account → claim → download via Launcher |
| Anonymous search | — | `/i/listings/search` can list metadata (title/cover/price), **can't get the models** |

- **2026-11-05** Quixel officially announced the entire library is free again (~23k assets), but the anonymous API
  still has `isFree` all false, showing $4.99 — cache/batch lag; trust the post-login UI.
- This machine has Epic Launcher installed and logged in, but `VaultCache/FabLibrary/listings_v1.db`
  and the download cache have **0 rows across the board**, and 0 Megascans assets in the project's Content.
- Official docs confirm Fab in Launcher supports **Ctrl+multi-select batch download/export**,
  but the user reported the UI "can't batch select," and "claiming (cloud) ≠ downloading (local)";
  downloading 23k one by one is impractical.

**User decision**: give up spending time on Fab and switch to a source "I can scrape fully automatically, you don't have to click anything."

## 2. Switching to Poly Haven (CC0, public API, fully automatic)

Tested three public, login-free, direct-link, CC0 commercially usable sources, all working:
Poly Haven / ambientCG / Cosmos. Chose Poly Haven for realistic industrial PBR materials.

`tools/polyhaven_download.py`: **8 seconds** to automatically download all 18 textures of 6 sets of 2K materials
(~31MB), with zero user action throughout.

| Material | Purpose |
| --- | --- |
| concrete_floor_02 | Industrial concrete floor (main floor) |
| concrete_wall_001 | Weathered concrete wall |
| factory_wall | Factory metal wall (corridor/front section) |
| rusty_metal | Rusted iron (wall variation) |
| corrugated_iron | Corrugated iron sheet |
| metal_grate_rusty | Rusted metal grate |

Each set takes 3 2K JPGs: `Diffuse`→BaseColor, `nor_gl`→Normal (OpenGL),
`arm`→packed AO/Roughness/Metallic.

## 3. Two material API pitfalls encountered

### 1. ComponentMask must explicitly set all 4 channels

The first version's `build` only wanted to enable a single channel (something like `set_editor_property("r", True)`),
resulting in all three masks being the defaults `RG`/`RG`/`RGB` — the AO/Rough/Metal split was completely wrong.
**ComponentMask's r/g/b/a default to False, but after creation you must explicitly assign all four values**,
leaving only the target channel True. Verified after the fix: `R` / `G` / `B` three exact single channels.

### 2. Verifying material connections can't just check "the script didn't error"

The first version's script ran without errors, but the connections were wrong. You must write a probe using
`MaterialEditingLibrary.get_material_property_input_node` to check one by one whether
BaseColor/Normal/Roughness/Metallic/AO are actually connected to nodes, before it counts.
(Same lesson as previous rounds: for "added but no effect," first verify the object/connection actually exists.)

## 4. Application (new area only)

`ue/Scripts/apply_polyhaven.py`:
- Boundary probe confirmed: EXT area 48 floor tiles + 35 wall segments, ORIG area 56+25 — **only change EXT**.
- ⚠️ Following the Round 102 white-line lesson: these actors use `override_materials`,
  so **the slot count must be preserved**, otherwise they fall back to pure-white `BasicShapeMaterial`.
  The approach: "keep the slot count, fill every slot with the same Poly Haven material," without breaking the slot structure.
- Assignment: floor all concrete; walls use factory metal in the front/corridor, concrete in the middle/rear, with rusted iron inserted every few segments.
- Tagged `PolyMat`; the level was backed up to `$env:TEMP\opencode\ue_backup_polyhaven\`.

Verification image `docs/cosmos_shots/polyhaven_materials.png`: the floor became realistic concrete with scratches/stains/
seams, the walls have the feel of weathered panels, consistent with the Cosmos realistic scanned props;
the central corridor and the gantry-framing-statue composition are preserved.

## 5. One thing left (not handled without permission)

The realistic concrete is **light gray**, which under this level's deep-blue night scene + Manual exposure is brighter than the original solid steel plates
and a bit jarring. This is a color-tone preference issue, and changing exposure would touch the project's established rendering defaults
(historical all-black pitfall), so it's only recorded, not changed without permission. If the user wants it darkened, options are:
add a dark coefficient multiplying BaseColor in the material, or adjust the tint of these material sets individually.

## 6. New scripts

| File | Purpose |
| --- | --- |
| `tools/probe_fab_api*.py` / `probe_fab_quixel.py` / `probe_fab_free.py` | Fab mechanism investigation |
| `tools/probe_fab_cache.py` / `scan_megascans.py` | Read-only scan of local Fab cache/assets |
| `tools/probe_polyhaven.py` / `probe_polyhaven_files.py` | Poly Haven API investigation |
| `tools/polyhaven_download.py` | **Fully automatic batch download** of 6 sets of 2K materials |
| `ue/Scripts/import_polyhaven.py` | Import 18 textures |
| `ue/Scripts/build_polyhaven_mats.py` | Build 6 PBR materials (corrected version) |
| `ue/Scripts/probe_polyhaven_mat2.py` | Verify connections actually hold |
| `ue/Scripts/probe_polyhaven_boundary.py` | Confirm the change boundary (EXT only) |
| `ue/Scripts/apply_polyhaven.py` | Apply to the new area's floor/walls |

`docs/Quixel_领取清单.md` is kept as a memo (in case Fab is used later).

## 7. Experience

**"The user doesn't want to click" is a hard constraint**: rather than teaching the user to wrestle with a clunky store UI
and giving ever more complicated clicking steps, it's better to switch to an equivalent source I can acquire fully automatically.
Poly Haven's CC0 realistic PBR quality is comparable to Megascans, and its API direct links →
land fully automatically in 8 seconds. The source doesn't matter; what matters is whether the loop can be closed.

---

# Round 107 (2026-11-09): Observer mode + global UI theme refactor and beautification

## 1. Requirements and decisions

The user asked: add an **observer mode** to the UI and beautify the UI to match the current game's style.

User selected (via openchamber_render interaction):
- Camera form: **free-flight observer camera** (WASD/mouse free flight, looking around the scene)
- Beautification scope: **observer panel + global theme refactor** (extract shared color/font/size constants)
- Accent color: **keep the amber copper-orange (1.0,0.72,0.30)**

## 2. Current state (investigation conclusion)

The UI is **pure C++ Slate** (`SRobotHUD` / `SRobotMainMenu` / `SRobotWorldMarkers` /
`SRobotModdingPanel` / `SRobotEndScreen`), with **no UMG / UUserWidget /
WidgetBlueprint assets at all**. The creation point is `ARobotPlayerController::CreateHUD()`
(`GEngine->GameViewport->AddViewportWidgetContent`, Z=10),
menu Z=100 / WorldMarkers Z=15 / modding bench Z=150 / end screen Z=200.

Color hardcodes are scattered across `RobotHUD.cpp` and `RobotMainMenu.cpp`; the same "cool white"
has different values in the two places (0.92/0.95/1.00 and 0.55/0.62/0.72 vs 0.58/0.65/0.75).

The debug camera (`DebugCamMode` 0~18 in `RobotCharacter.cpp`) already has a clean
ACameraActor + bAutoManageActiveCameraTarget=false + SetViewTarget mechanism,
but camera positions can only be hardcoded on the command line, parsed each frame in Tick, with no runtime free flight.

## 3. Implementation

### 1. Shared theme `Public/UI/RobotUITheme.h`

Centralizes all colors/sizes/fonts; a header-only file that doesn't participate in UHT:
`Accent` (amber copper-orange) / `Cyan` (cyan-blue data color) / `Text`/`TextDim`/`TextFaint` /
`PanelBg`/`BarBg`/`Rule`/`Frame` / semantic colors `Warn`/`Okay`/`DangerFlash` /
heat and power threshold colors / `DesignW/H`/`BarW/H` / `Font(Size,bBold)` helper.

`RobotHUD.cpp` and `RobotMainMenu.cpp` both changed to take values from here (values remain the same,
just consolidated to a single source).

### 2. Observer core (PlayerController)

Placed in `ARobotPlayerController` rather than the Character — camera/view is a controller responsibility,
and this avoids coupling with the Character's EnhancedInput asset system and `FInputModeUIOnly`.

| Interface | Purpose |
| --- | --- |
| `ToggleObserver()` / `EnterObserver()` / `ExitObserver()` | Toggle |
| `IsObserverMode()` | State |
| `GetObserverLocation/Rotation/Speed()` | For HUD to pull each frame |
| `TickObserver(dt)` | Advance free flight in Tick |
| `EnsureObserverCamera()` | Create/reuse ACameraActor, SetViewTarget |
| `CreateObserverHUD()` / `RemoveObserverHUD()` | Overlay lifecycle |

Free flight (reads keys directly in TickObserver, self-contained):
- Mouse delta → yaw/pitch (`GetInputMouseDelta`)
- WASD translation / Q E up-down / Shift ×3 speed boost
- Mouse-wheel speed adjustment: use `InputComponent->BindAxisKey(EKeys::MouseWheelAxis)` to accumulate into
  `ObserverScrollAccum`, consumed in Tick (**pitfall**: `GetInputAnalogKeyState(MouseWheelAxis)`
  is unreliable for reading the wheel; only BindAxisKey gets it)
- Speed range 150~12000 cm/s

Toggle key: `BindKey(EKeys::V, IE_Pressed, ToggleObserver)` in `SetupInputComponent()`
+ console command `Robot.ToggleObserver` as a double safeguard.

On entry:
- Starting point is **pulled 900cm behind and 520cm up** from the mech position and turned back to look down
  (the first version hugged the player camera, so on entry it was right in front of a near-field pipe with the view blocked — fixed)
- `bAutoManageActiveCameraTarget=false` + `SetViewTarget(Cam)`, reaffirmed every frame
- Regular HUD and WorldMarkers are **all hidden** (combat readouts are meaningless once detached from the mech),
  with the observer HUD taking over (handled uniformly by `UpdateHUDVisibility`)
- The world is not paused (enemies move as usual, for easier observation)

Exit: `bAutoManageActiveCameraTarget=true` + `SetViewTarget(Pawn)` returns the view.

The `-Observer` startup parameter: defers entry until the first-frame Tick (the camera system may not be ready at BeginPlay),
for automated screenshot verification.

### 3. Observer HUD `SRobotObserverHUD` (pure Slate, Z=20)

Industrial-style overlay:
- Top: breathing status light (accent color ↔ cyan-blue) + "Observer Mode · OBSERVER"
- Top-left: telemetry panel (title "Telemetry / TELEMETRY" + divider + coordinates/orientation/speed)
- Bottom: operation hint bar (WASD / Mouse / QE / Wheel / Shift / V)
- Four corners: copper-orange L-shaped viewfinder brackets (echoing the HUD hit-marker language)
- All data pulled from the PC each frame via TAttribute

### 4. Regular HUD beautification (SRobotHUD)

- Bottom-left status panel: added **copper-orange top bar (3px) + "Body Status / SYSTEM" title + divider**,
  padding rearranged; chassis model/scrap/heat/power hierarchy is clearer
- Top-right "remaining enemies": added a copper-orange top bar as well, echoing the bottom-left
- Fonts uniformly go through `RobotTheme::Font`, threshold colors through theme constants

## 4. Verification

- `docs/ui_shots/observer_mode.png`: started with `-Observer`; the free-flight camera pulls back from above and behind the mech,
  the whole scene is visible; observer HUD complete and stylistically consistent
- `docs/ui_shots/hud_beautified.png`: after regular HUD beautification, the copper-orange top bar/title/
  divider are in place, with clear information hierarchy

One pre-existing phenomenon (not introduced this time): when `-SkipMenu` enters the game directly, `ChassisLabel`
(chassis model) is empty, and the bottom-left line only shows "Recycled Scrap." This is a pre-existing chassis assembly timing issue;
data logic was not changed.

## 5. New/modified files

| File | Change |
| --- | --- |
| `Public/UI/RobotUITheme.h` | Added: shared theme |
| `Public/UI/RobotObserverHUD.h` + `Private/UI/RobotObserverHUD.cpp` | Added: observer HUD |
| `Public/RobotPlayerController.h` / `Private/RobotPlayerController.cpp` | Observer core, SetupInputComponent, Tick hookup, EndPlay cleanup |
| `Private/UI/RobotHUD.cpp` / `Public/UI/RobotHUD.h` | Theming + beautification |
| `Private/UI/RobotMainMenu.cpp` | Theming (unified value source) |

`RobotGame.Build.cs` needed no change (UMG/Slate/SlateCore were already in dependencies).

## 6. Experience

**Cross-cutting features like "observer" are cleaner in PlayerController**: camera/view/input mode
are controller responsibilities by nature; attaching to Character collides with three couplings: EnhancedInput assets, Possess stealing the view,
and FInputModeUIOnly.

**The mouse wheel can't be read with `GetInputAnalogKeyState`**: switch to a `BindAxisKey` accumulation member,
consumed in Tick, which reliably gets it.

**Don't hug the player camera for the starting point**: spawn points often end up right in front of near-field structures; pull back
some distance behind and above the Pawn and turn around, so the whole view is seen on entry.

**Global theme refactoring must guard against name collisions**: `using namespace Theme` brings constants like `DesignW`
into the current scope, colliding with same-named constexprs in the file as C2872. Switching to "local short aliases
pointing to theme constants" is safest.

---

# Round 108 (2026-11-09): Mech protected from destruction in observer mode

## 1. Requirement

"Set the body to be indestructible in observer mode" — in observer mode the mech, though out of control, remains on the field
and can be destroyed by enemies; on exit you return to find the mech gone / a failure end screen popped up directly.

## 2. Locating the damage chain

Destruction path: part reaches zero → `UPartDamageComponent::OnActorDisabled`
→ `ARobotCharacter::HandleActorDisabled()` → `ARobotGameMode::NotifyPlayerDefeated()`
→ failure end screen.

**Key finding**: all damage ultimately converges on
`UPartDamageComponent::ApplyDamageToPart()`
(`ApplyDamageByBone` / `ApplyDamageByBoneEx` / projectiles / explosive barrels all call it),
and its beginning **already has a gate** — if startup `-GodMode` and player-controlled, it returns immediately.

The problem is that `-GodMode` is a **static command-line check** via `FParse::Param`, which can't be toggled at runtime.

## 3. Implementation (across two modules)

### RobotCombat: adding a runtime invulnerability flag to `PartDamageComponent`

- `Public/PartDamageComponent.h`: added `bool bInvulnerable` (default false)
  + `SetInvulnerable(bool)` / `IsInvulnerable()` (UFUNCTION, viewable for debugging).
- `Private/PartDamageComponent.cpp`: at the start of `ApplyDamageToPart`, extended the
  `-GodMode` check to "either `bInvulnerable` OR startup GodMode being true grants immunity."
  The interception point is at the **single damage gate**, covering all damage sources.

Design key point: the flag applies to the **component instance**; set true only on the player's PartDamage,
enemy components are unaffected — enemies act and can be scored as usual (the observer doesn't fire but the logic is clean).

### RobotGame: toggling on entry/exit in `PlayerController`

- Added `SetMechInvulnerable(bool)`: take `Cast<ARobotCharacter>(GetPawn())`
  → `GetPartDamage()` → `SetInvulnerable()`.
- `SetMechInvulnerable(true)` at the end of `EnterObserver()`;
- `SetMechInvulnerable(false)` at the end of `ExitObserver()` — **this reset line must not be missed**,
  otherwise the player stays invulnerable forever after exiting.
- Logs are marked "· Mech protected from destruction" / "· Damage restored," respectively.

## 4. Verification (a clean controlled experiment)

⚠️ Pitfall: `tools/shot_run.ps1` **includes `-GodMode` by default**, so the first verification couldn't distinguish
whether GodMode was the fallback or the new mechanism took effect — the verification was unclean, voided and redone.

Switched to **two dedicated scripts, both deliberately without `-GodMode`**:

| Experiment | Script | Parameters | Result |
| --- | --- | --- | --- |
| Verification group | `tools/verify_observer_invuln.ps1` | `-Observer`, no GodMode | 18 seconds: entered observer mode successfully, **no disablement/no failure/no EndScreen**, normal `-AutoQuit` exit |
| Control group | `tools/verify_control_nogod.ps1` | No `-Observer`, no GodMode | **"Player mech disabled" at 6.7s → "[Result] Player disabled · Mission failed"** |

Log evidence: verification group `GodMode present? False`, `-Observer` on the command line;
control group `GodMode present? False`, `-Observer` absent.

Same enemies and damage environment, **the only variable is whether observer mode was entered** —
the control group failed while the verification group survived, decisively proving that destruction immunity is the new mechanism (runtime
bInvulnerable) taking effect, not enemies failing to attack or a command-line fallback.

Build: `Build.bat RobotGameEditor ... Development` → `Result: Succeeded` (across
the two modules RobotCombat + RobotGame).

## 5. Experience

**"Parameters a screenshot tool includes by default" can contaminate verification**: this round's first verification was interfered with by
`shot_run.ps1`'s built-in `-GodMode`, invalidating the conclusion. Before behavior verification, first see all sources of startup parameters;
if necessary, create a separate dedicated "minimal parameters" script for a controlled comparison.

**Finding the single damage gate is more reliable than setting flags everywhere**: instead of intercepting `HandleActorDisabled`
(by then the part is already destroyed, too late), return at the source `ApplyDamageToPart`,
so part health never decreases at all, and the mech is still at full state on exit.

---

# Round 109 (2026-11-09): Remove Mech · Eliminate Clipping · Fix Textures

## 1. Requirements

User: "Remove the previous mech model; some model assets are clipping/show-through, adjust their placement;
some textures aren't loading, fix them."

Three tasks — diagnose before acting (the level was backed up to `$env:TEMP\opencode\ue_backup_scenefix\`).

## 2. Diagnosis (`ue/Scripts/probe_scene_fix.py`, read-only)

### 1. Mech to remove
One `SM_IdolMech` actor, at (4750, 0, 484.9), tag `IdolMech` —
the 9.36m display piece imported in Round 103, exactly the "previous mech model."

### 2. Clipping: AABB pairwise intersection detection, 5 real overlaps
| Pair | Cause |
| --- | --- |
| Sandbags A1×A2 / B1×B2 | Centers of two sandbag rows (157×375) only 130/40cm apart, almost completely overlapping |
| Sandbag A2 × Streetlight A | Edges rubbing each other |
| Fence B × Stove B / Fire Extinguisher B | Fence (300×200) squeezed together with wall-mounted pieces at x=4300 |

(The floating wooden crate stacks / wall-mounted fan and sconce are **intentionally stacked/wall-mounted**, not problems.)

### 3. Textures not loading: **root cause is a filtering bug in the previous round's script**

`apply_polyhaven.py` (Round 106) filtered walls with
`"floor" not in nm and "wall" not in nm` + `is_ext = ExtRegion or x>=1800`.
Among the Cosmos props, **`cs1-wallfanhatch` (wall fan) and `cs1-wall-light-6` (wall sconce)
have "wall" in their names**, and both are in the EXT region with x>1800 → misjudged as perimeter walls,
their `override_materials` were changed to the single-slot `M_concrete_wall_001` / `M_rusty_metal`,
**overriding the PBR textures bundled with the glTF**, displaying as a drab gray wall material —
this is exactly the "textures not loading" seen by eye.

The precise probe `probe_cosmos_override.py` confirmed: 4 wall-mounted pieces carry the `PolyMat` tag,
override = concrete/rusty metal; the other 27 Cosmos props have `ov=[]` (glTF's own materials,
**an empty override is normal**, not a problem).

## 3. Fixes

### 1. Remove mech — `ue/Scripts/remove_idol_mech.py` (new, idempotent)
Delete the actor in the level by the `IdolMech` tag, **keep the asset files**
(do not delete the SM + materials under `/Game/RobotGame/Art/Props/IdolMech/`, can be dragged back in anytime).
Re-verification `check_idol_mech.py`: IdolMech actor count = 0.

### 2. Eliminate clipping — third version of LAYOUT in `place_cosmos_props.py`
- Sandbags in the same group spread apart along X to 460cm (A1/B1=2620, A2/B2=3080)
- Streetlights moved outward out of the cover bounding boxes (2450 / 4150)
- Fence B moved forward to 3850, staggered from the stove/fire extinguisher/sconce at x=4300/4500
- Wooden crate group B moved along +X to 3500 (diagnosed that at 3250 it rubbed sandbag B2's edge
  by X64 Y155; after the second correction the X difference is 420)
- Oil drums / freezers / drawer cabinets correspondingly rearranged

Re-verification: AABB intersections **5 pairs → 1 pair → 0 pairs**; sunk-into-floor count 0.

### 3. Fix textures + prevent recurrence — `apply_polyhaven.py`
- Use **precise tag filtering**: only recognize structural walls/floors with the `ExtRegion` tag;
  skip all props with the `CosmosProp` tag.
- Remove the `x>=1800` fallback (that would rope in Cosmos props in the EXT region).
- Idempotent self-healing: if a Cosmos prop is found to have been mistakenly tagged `PolyMat`,
  clear its override so it falls back to its own material, and remove the PolyMat tag.
- Rerun results: 48 floor tiles, **25 wall segments** (old version 35 segments = 10 extra wall-named
  props counted; now precise); 4 wall-mounted pieces' `PolyMat` remnants = 0, all overrides empty.

Execution order (very important): `remove_idol` → `place_cosmos_props` (rebuild props,
also clearing old overrides) → `apply_polyhaven` (only refresh structural pieces).

## 4. Acceptance

- `docs/scenefix_shots/before_front.png` (before fix, statue in the center, sconces turned gray)
- `docs/scenefix_shots/after_front.png`: area behind the central gantry is clear, statue gone;
  cover pieces grouped and separated; sconces on both sides restored to white shades/bracket textures
- `docs/scenefix_shots/after_top.png`: top view confirms the central passage is clear and the overall spacing

## 5. Added/modified scripts

| File | Change |
| --- | --- |
| `ue/Scripts/probe_scene_fix.py` | Comprehensive diagnosis (statue/clipping/material override/Poly Haven connections) |
| `ue/Scripts/probe_cosmos_override.py` | Precisely check each Cosmos prop's override |
| `ue/Scripts/check_idol_mech.py` | Confirm statue removed |
| `ue/Scripts/remove_idol_mech.py` | New: idempotently remove statue (keep assets) |
| `ue/Scripts/place_cosmos_props.py` | LAYOUT third version: eliminate clipping |
| `ue/Scripts/apply_polyhaven.py` | Precise tag filtering + self-heal mis-tags |

## 6. Lessons

**"Filtering by name substring" is brittle**: `"wall" in mesh name` treats `cs1-wall-light-6`,
`cs1-wallfanhatch` — **props** with "wall" in their names — as walls.
Filtering by tag / explicit classification is robust — the same class of lesson as idempotent scripts needing
"narrow deletion conditions" (lights were mistakenly deleted in Round 102).

**For "textures not loading" check overrides first, don't rush to re-import textures**: the texture assets
are all present, the Poly Haven material connections are intact, the problem was just one mistakenly set
override overriding the built-in material.

**AABB pairwise intersection is more reliable than hunting clipping by eye**: of the 5 pairs, the two most
obvious (sandbags almost completely overlapping) were the hardest to distinguish by eye in a flat view;
bounding-box detection lists them all in one pass.

---

# Round 110 (2026-11-10): Lighting Polish + Hunyuan3D Asset Generation Pipeline

## 1. Requirements

1. Generate required assets with Hunyuan3D (first generate multi-view, then convert to 3D and place in the scene)
2. Polish lighting further, can add reflections, ray tracing, etc.

## 2. Environment testing (confirm capabilities before acting)

| Item | Measured result |
| --- | --- |
| Hunyuan3D | `C:\AI\Hunyuan3D`, venv + `hunyuan3d-dit-v2-mini` (**single-image version**) + 4.59GB multi-view weights **not installed** |
| Image generation | `C:\AI\ComfyUI`, available models z_image_turbo / moss_image / krea2_turbo |
| GPU | RTX 4070 Laptop, **8GB** VRAM |
| UE RHI | **D3D12**, Feature Level **SM5** |
| Ray tracing | **Off** (`r.RayTracing=0`, deliberately set by the project) |

User chose in the interaction: **use the single-image version first** (while probing the feasibility of multi-view weights);
**do safe lighting polish first** (don't touch ray tracing, don't change project config).

### Feasibility conclusion for multi-view weights

On HF, `tencent/Hunyuan3D-2mv/hunyuan3d-dit-v2-mv/model.fp16.safetensors`
**is only 4.59GB**, and disk space is enough (100GB free). But testing showed **large-file (LFS) downloads are
actively disconnected by the remote** (`WinError 10054`), while small files (config.yaml) download fine —
indicating the HF LFS channel is unusable in this network environment, a proxy is needed to download.
**Conclusion: multi-view is not feasible for now, go with the single-image version.**

## 3. Lighting polish (safe route, zero risk)

First used `probe_lighting.py` / `probe_lighting2.py` to map the current state, finding four
key problems:

1. **PPV has no Lumen reflection/GI overrides enabled at all** → engine defaults used, reflections barely visible
2. **45 point lights + 13 spotlights, the vast majority with `cast_shadows=False`** (turned off in Round 102
   to save shadow budget) → scene has **no contact shadows**, objects look like they float above the floor
3. **SkyLight `lower_hemisphere_is_black=True`** → object bottoms are dead black
4. **Fog is very faint** (density 0.006) → no volumetric depth

`ue/Scripts/polish_lighting.py` corresponding fixes (all level-only, reversible):

| Item | Change |
| --- | --- |
| Reflections | PPV enable `ReflectionMethod=LUMEN`, `lumen_reflection_quality=1`, `max_roughness_to_trace=0.6`, enable screen-space tracing |
| Global illumination | PPV enable `DynamicGlobalIlluminationMethod=LUMEN` |
| Shadows | Of the 27 lights in the EXT region, **sparsely enable 7** (1 out of every 3, selected deterministically by position hash) — deliberately avoiding the old trap of "all 45 on fills the budget" |
| Sky light | `lower_hemisphere_is_black=False`, intensity 1.35→1.15 |
| Fog | density 0.006→0.012, start distance 600→400, cool-blue scattering (0.030,0.042,0.070) |
| Tone | Exposure bias 5.6→5.1, Bloom 0.42→0.62, AO 1.4, contrast 1.14→1.12, saturation slightly raised |

### Floor wetness (`ue/Scripts/polish_floor_wet.py`)

The Poly Haven floor material's Roughness connects directly to the ARM texture's G channel (dry concrete
0.7~0.9), Lumen reflections are almost invisible. Insert a **Multiply × 0.55** between the G channel and
Roughness, lowering roughness → clearer reflections → industrial "wet floor" look.

⚠️ Idempotency check: `check_floor_wet.py` confirms there is ultimately only **1 Multiply + 1
Constant(0.55)**, no duplicate stacking (repeated runs would do 0.55×0.55, too slippery).

**Pitfall**: `MaterialExpressionMultiply`'s A/B properties are protected,
`get_editor_property("a")` throws an exception — you can only connect, not read.

## 4. Acceptance

`docs/lighting_shots/compare.png` (left: before / right: after):
- Clear **light reflection spots** appear on the floor (Lumen + wet roughness)
- Each piece of cover has a **contact shadow**, sitting solidly on the ground
- Fog darkens the distance, giving **depth**
- Contrast improved, no longer gray and washed out

Top view `docs/lighting_shots/after_top.png` likewise confirms the light spots and shadow distribution.

## 5. Hunyuan3D generation pipeline (end-to-end working)

Flow: **ComfyUI image generation → Hunyuan3D single-image to 3D → GLB**

| Step | Script | Result |
| --- | --- | --- |
| Image generation | `tools/comfy_gen_asset.py` (single) / `comfy_gen_batch.py` (batch) | z_image_turbo, 1024², 8 steps, ~30 sec/image |
| Matting | `C:\AI\Hunyuan3D\hy3d_asset.py` built-in | BiRefNet no longer available (`C:\AI\Idol` cleaned up), switched to **directly using clean-background source images** |
| 3D | Same as above, DiT mini | ~**10 min each**, 398k faces, 6.7MB |
| Verification | `tools/blender/verify_hy3d_glb.py` | `pipe_junction.glb`: 1 mesh, 389976 faces, dimensions 1.99×1.81×1.93m |

Generated concept images: `pipe_junction` / `airlock` / `crane_arm` /
`bunker_vent` / `mech_core` / `generator` (`C:\AI\Hunyuan3D\input\gen_*.png`).

Generated models: `pipe_junction.glb` (verified), the other 5 generating serially in the background
(`tools/hy3d_batch.py`).

## 6. Pitfalls and lessons

**"Multi-view" requires first verifying weights can be obtained**: the model is only 4.59GB, disk is enough,
but the HF LFS download gets disconnected — the bottleneck is the network, not the disk. Testing small files
first + testing large-file chunking can save a long wait for a "download fails halfway" outcome.

**Sparse shadows > all shadows**: the lesson from Round 102 was that all 45 shadows on filled the budget,
showing up as "adding lights doesn't brighten things." This round used a position hash to enable 1 in 3,
getting contact shadows without blowing the budget — similar problems need a "quota" mindset rather than
"all on."

**Wet floors come from materials, not lights**: to make metal/concrete reflective, adjusting Roughness is far
more effective than adding lights. The Multiply coefficient 0.55 is a visually verified sweet spot.

**8GB VRAM requires counting the queue**: image generation ~30 sec, 3D ~10 min, 5 assets about 50 min.
Run serially, call `torch.cuda.empty_cache()` after each step to avoid OOM.

## 7. Added scripts

| File | Purpose |
| --- | --- |
| `ue/Scripts/probe_lighting.py` / `probe_lighting2.py` | Lighting current-state probing |
| `ue/Scripts/probe_lumen_api.py` | Lumen/reflection enums and PPV field names |
| `ue/Scripts/probe_floor_mat.py` | Floor material node structure |
| `ue/Scripts/polish_lighting.py` | PPV + shadows + sky light + fog |
| `ue/Scripts/polish_floor_wet.py` | Floor wetness (Roughness × 0.55) |
| `ue/Scripts/check_floor_wet.py` | Idempotency check (prevent duplicate stacking) |
| `tools/comfy_gen_asset.py` / `comfy_gen_batch.py` | ComfyUI image generation |
| `C:\AI\Hunyuan3D\hy3d_asset.py` | Matting (optional) + 3D generation |
| `tools/hy3d_batch.py` | Batch serial conversion to 3D |
| `tools/blender/verify_hy3d_glb.py` | GLB verification + preview render |
| `tools/dl_hunyuan_mv.py` | Multi-view weight download (network currently unavailable) |
| `ue/Scripts/import_gen3d.py` | Import 3D assets into UE |

---

# Round 111 (2026-11-10): Fix Floor Texture "Not Loading"

## 1. Symptom

User reported: "The floor texture has a problem, it didn't load."

## 2. Diagnosis (three-step elimination, `probe_floor_diag*.py` / `probe_floor_uv.py`)

| Suspicion | Check result | Conclusion |
| --- | --- | --- |
| Material nodes broken? | BaseColor/Normal both connected to TextureSample, Roughness via Multiply | Nodes intact |
| Texture asset corrupted? | All three are **2048×2048**, disk files 3.3MB/949KB/716KB all present | Assets normal |
| Floor actor material override? | All 48 floor tiles point to M_concrete_floor_02 | Override correct |
| **UV stretching** | Material has **no TextureCoordinate node**, `SM_Env_Floor` is **400×400cm** | **← true cause** |

**Root cause**: Poly Haven textures are real-scale scans (~2m per image), while floor tiles at 400×400cm
use default UV(0-1) stretched across the whole tile → **texture magnified 2×**,
detail blurred into a uniform gray, which looks like "not loading."

## 3. Fix

`ue/Scripts/fix_floor_uv.py` (floor) + `fix_uv_all.py` (other materials):

Connect **TextureCoordinate × N** to each TextureSample's UV input:

| Material | Tiling multiplier | Notes |
| --- | --- | --- |
| M_concrete_floor_02 (floor) | ×2.0 | 400cm / 2 = 200cm per image, matches real scale |
| M_concrete_wall_001 / M_factory_wall (walls) | ×2.5 | 412cm wall segments, detail needs to be denser |
| M_rusty_metal / M_corrugated_iron / M_metal_grate_rusty | ×3.0 | Small objects, finer texture |

All 6 materials fixed (node count 6→9, floor 8→11).

**Acceptance**: `docs/uvfix_shots/compare.png` — left (before) texture blurred into gray blocks,
right (after) clearly shows concrete grains, stains, and fine scratches.

## 4. Lessons

**For "texture not loading" check UV scale first, don't rush to re-import textures**: textures 2048² intact,
node connections normal, material override correct — three "normals" rule out all asset-level problems;
what remains is "texture density is wrong." Real-scale scans paired with procedurally sized meshes
**require explicitly setting UV tiling multipliers**, otherwise you get either stretched blur or obvious repetition.

**Tiling multiplier should be calculated from component size**: 400cm tile ÷ 2 = 200cm, exactly the scan's
natural scale; casually setting 10 yields fine mosaic.

**Judge idempotency by "whether the node exists" not "whether the script ran"**: both runs this round reported
"skipped," but the actual result was correct — meaning the first run took effect, the second was idempotent.
Verification must go back to an **independent probe** (`audit_mat_uv.py`) to see real nodes,
don't trust the script's self-report.

## 5. Added scripts

| File | Purpose |
| --- | --- |
| `ue/Scripts/probe_floor_diag.py` | Material node / texture / override three-way diagnosis |
| `ue/Scripts/probe_floor_diag2.py` | Deep check of texture asset pixel data |
| `ue/Scripts/probe_floor_uv.py` | UV stretching check |
| `ue/Scripts/fix_floor_uv.py` | Floor UV tiling fix |
| `ue/Scripts/fix_uv_all.py` | All materials UV tiling fix |
| `ue/Scripts/audit_mat_uv.py` | Independent re-check (doesn't rely on fix script self-report) |

---

# Round 112 (2026-11-10): Zone 2 Floor Unification + Rectangular Channel Texture Fix

## 1. Requirements

1. Change Zone 2's (new area) floor texture to be the same as Zone 1's (original arena)
2. Rectangular channel has a texture problem

## 2. Diagnosis

`probe_zone_floor.py` checks floor material distribution:

| Area | Floor override |
| --- | --- |
| Zone 1 (X<1800, 56 tiles) | `[M_Steel, M_SteelLight, M_Joint, M_Copper]` |
| Zone 2 (X>=1800, 48 tiles) | `[M_concrete_floor_02 x4]` ← realistic concrete switched in Round 106 |

`probe_all_water.py` locates the rectangular channel: what the user meant was not the circular toxic pool,
but the **(450,300) coolant leak device**:
- `GeoCacheWater_Coolant`: 758×200cm strip of water flow
- `Basin_CoolantSpill_0`: 816×256cm rectangular channel rim (`bChannel=true`)
- `RobotCoolantField CoolantSpill_0`: glowing coolant field

## 3. Fix 1: Zone 2 floor unification

`ue/Scripts/unify_zone2_floor.py`: restore the 48 Zone 2 floor tiles'
`override_materials` to Zone 1's 4-slot material set (keep 4 slots,
don't fall back to BasicShapeMaterial).

Re-check `probe_zone_floor.py`: the two areas are now **completely identical**
(both `['M_Steel','M_SteelLight','M_Joint','M_Copper']`).

## 4. Fix 2: Rectangular channel texture

### Camera pitfall

When adding `-ChannelCam` (DebugCamMode 19) for a rectangular channel close-up,
screenshots kept showing the round pool — found that `RobotCharacter.cpp:977` **already had a
`-BasinCam` (DebugCamMode 8, 3/4 panorama of the round pool)**; my newly added second
`-BasinCam` branch was unreachable. Renaming to `-ChannelCam` fixed it.

### Problem appearance

`docs/channel_shots/before.png`: the channel rim (white ring band) has **dense 45°
diagonal lines / moiré**, while the water surface texture is normal.

### Root cause

In `RobotBasin.cpp::BuildChannel()`, the top-face UV has **U accumulating along all four edges**
(long edge U≈7.6), while V is only `T/12≈2.33`; material `M_Basin_Concrete` also multiplies by
`TextureCoordinate(1.5, 1.5)` → U direction 11.4 periods vs V direction 3.5 periods,
severely unbalanced density → anisotropic diagonal stripes on the narrow channel rim.

### Fix method (low risk)

`ue/Scripts/fix_channel_uv.py`: change both TextureCoordinate tilings of `M_Basin_Concrete`
from **1.5 → 0.5**, lowering U periods to ~3.8,
closer to V's ~1.2, then recompile the material.

**Acceptance** `docs/channel_shots/compare.png`: left (before) dense diagonal stripes,
right (after) becomes a soft concrete texture, no longer harsh.

### Remaining issue (stated honestly)

Adjusting material tiling only **mitigates**, cannot cure — the geometric UV anisotropy
(U accumulation 7.6) is an algorithm in source code. To fully eliminate it requires changing `BuildChannel()`
so each edge's U starts independently at 0 (no accumulation), but that requires recompiling C++ and
`OnConstruction` rebuilds the mesh, higher risk — not done this round.

## 5. Added scripts

| File | Purpose |
| --- | --- |
| `ue/Scripts/probe_zone_floor.py` | Compare floor materials of two areas |
| `ue/Scripts/probe_all_water.py` | Find all channel/pool geometry |
| `ue/Scripts/probe_channel.py` | Determine square channel vs round pool (bChannel + aspect ratio) |
| `ue/Scripts/unify_zone2_floor.py` | Unify Zone 2 floor to Zone 1 material |
| `ue/Scripts/fix_channel_uv.py` | Channel material tiling 1.5→0.5 |
| `ue/Scripts/fix_basin_tex.py` | Investigate channel texture sRGB (ultimately confirmed not the cause) |

Added cameras: `-ChannelCam` (19, rectangular channel), `-Zone1Floor` (20, Zone 1 floor reference).

## 6. Lessons

**Before adding a command-line camera, grep for an existing parameter with the same name**: this round wasted
three identical round-pool shots before realizing `-BasinCam` already existed.

**For procedural mesh texture problems, check the UV algorithm first, then the material**: the channel's
diagonal stripes weren't a bad texture, not sRGB, not broken nodes, but anisotropy from `UAcc` accumulating
along edges. Material tuning is a stopgap; the cure is back in the C++ that generates the geometry.

---

# Round 113 (2026-11-10/11): Fix "No Texture" at Water Injection Landing Point

## 1. Requirement clarification

User specified: "It's the place where the channel injection contacts the water surface that has no texture" —
not the channel rim, but the **contact point where the water column lands on the water surface**.

## 2. Symptom

`docs/splash_shots/compare_final.png` left: below the injection outlet there are **two overlapping
pale-white discs** (semicircular fan shapes), solid color without texture, like stickers floating on the
rippling water, completely disconnected from the surrounding water.

## 3. Localization (took detours, but ultimately confirmed)

### Actors found

`probe_splash.py` / `probe_splash_geo.py`:
- `Splash_FoamRing` (120,300,8.0)
- `Splash_FoamDisc` (120,300,7.7)
- `Splash_SprayCone` (120,300,9.0)

All three are `/Engine/BasicShapes/Cylinder` / `Cone`,
materials `M_Splash_Foam` / `M_Splash_Spray`.

### Pitfall 1: misidentified the objects

`hide_splash.py` set the three Splash actors to `set_visibility(False)` then took a screenshot,
the pale discs were "still there" → briefly thought it wasn't them. **Actually hiding only changed memory,
didn't save the level**, and `shot_run.ps1` starts a new process each time reading from disk — the hide never
made it into the screenshot session.

### Pitfall 2: repeatedly changing materials had no effect

- `M_Splash_Foam` originally had BaseColor connected to a solid color constant, texture `T_Toxic_Bub`
  (black-background white-dot bubble mask) connected only to Emissive.
- Tried connecting the texture to BaseColor, rebuilding V2, adjusting Emissive coefficients… the discs stayed
  **pure white or overexposed**, node structure looked right but rendering was wrong.
- Cause: scene Manual exposure bias 5.6 is very bright, any foam material with Emissive/light base gets
  blown out to pure white.

### Decisive determination

`test_splash_copper.py`: swapped the two discs' override to `M_Copper`
(dark mottled texture) **and saved the level** → in the screenshot the discs immediately became
**textured copper pieces**.

✅ **Proved geometry and UV are normal, the pale discs are exactly these two actors, the problem is 100% in the material.**

## 4. Final fix

`ue/Scripts/finalize_splash.py`: **abandon the custom foam material**, make the three landing-point
decorations directly reuse the **water surface material `M_GeoCache_Water`** (with ripple normals/reflections).

Result: the pale patches disappeared, leaving only two faint ripple contours, the landing point blends
seamlessly with the water surface (`docs/splash_shots/compare_final.png` right).

## 5. Lessons (important)

**"Changed it but no effect" first confirm the change actually landed on disk, actually entered that session**:
`set_visibility` / material overrides that only change memory, without `save_current_level()`,
mean the screenshot tool's newly started process reads the old level from disk — a round of wasted effort
plus a misidentification.

**To verify object ownership, "swap in an absolutely conspicuous material and save"**:
M_Copper made it instantly obvious, far more reliable than repeatedly reading nodes / guessing geometry.
This step ended the back-and-forth on "is it really these two discs."

**In high-exposure scenes don't make "light color + emissive" patch materials**:
under bias 5.6 they will blow out to pure white. Either darken them, or simply reuse the environment's own
material (here reusing the water material is most natural).

## 6. Added scripts

| File | Purpose |
| --- | --- |
| `ue/Scripts/probe_all_water.py` / `probe_channel.py` | Locate rectangular channel |
| `ue/Scripts/probe_splash.py` / `probe_splash_mat.py` / `probe_splash_geo.py` | Landing-point actor / material / geometry diagnosis |
| `ue/Scripts/probe_near_jet.py` | Full list of actors near the injection outlet |
| `ue/Scripts/dump_toxicbub.py` | Export bubble texture to inspect content (black-background white-dot mask) |
| `ue/Scripts/test_splash_copper.py` | **Decisive determination**: swap M_Copper to prove it's these two discs |
| `ue/Scripts/finalize_splash.py` | Final fix: reuse water surface material |
| `ue/Scripts/fix_channel_uv.py` / `unify_zone2_floor.py` | Previous round's channel/floor fixes |

Camera: `-ChannelCam` (19, rectangular channel close-up, distinct from old `-BasinCam`).

---

# Round 114 (2026-11-11): Landing Point Switched to Real Physical Fluid

## 1. Requirement

User: "This is a bit too fake, can it be a real, physics-based fluid like the water below?"
— the previous round blended the landing-point static patches into the water surface (Round 113), but it still
wasn't "real physical fluid." The user wants the landing point to be simulated, same as the whole channel's water.

## 2. Key discovery: the system already has physical fluid

`ARobotCoolantField` (`RobotCoolantField.cpp`) is a **complete real-time height-field
fluid simulator**:

| Component | Purpose |
| --- | --- |
| `Height[] / Velocity[]` grid (72×72 or denser) | Wave state |
| `StepSim()` 60Hz fixed timestep | Wave equation propagation (`Vel += (Avg-H)*C*4; Vel*=D; H+=Vel`) |
| `ApplyImpulse(x,y,strength,radius)` | Inject disturbance |
| `RefreshMesh()` every frame | Recompute vertex Z, normals (±2-cell difference), vertex colors |
| `M_Coolant_Fluid` (127 nodes) | Panner dynamic water flow + dual-layer ripple normals + vertex-color foam |
| Vertex color R=Foam / G=Height / B=**Churn (inlet scour band)** | Physically driven crest foam and landing-point churn |

`StepSim()` line 217 already has a **`bInflow` continuous injection pulse**: per
`InflowInterval` injecting `-InflowStrength` at `InflowLocal`,
producing continuous outward-expanding ripples. `CoolantSpill_0` measured `bInflow=True`,
`InflowLocal=(-330,0)` — **exactly aligned with the water column landing point** (column 120,300 /
Field 450,300 → local -330,0).

Conclusion: **the physics system of "the water below" already covers the landing point**, what's fake is the
three static Splash patches laid on top + weak injection pulse parameters.

## 3. Fix (`ue/Scripts/upgrade_fluid.py`)

1. **Hide the three static decorative patches** `Splash_FoamRing` / `Splash_FoamDisc` /
   `Splash_SprayCone` (`visible=False` + `hidden_in_game=True`)
   → landing effect now handled by the real simulation, no more "stickers"
2. **Strengthen the physical injection pulse** (only change `CoolantSpill_0`, the 4 toxic pools stay still water):

| Parameter | Before | After |
| --- | --- | --- |
| InflowStrength | 1.3 | 3.2 |
| InflowInterval | 0.10s | 0.06s (more continuous) |
| InflowRadius | 62 | 45 (more focused on landing point) |
| MaxHeight | 5cm | 9cm (more visible ripples) |
| GridCells | 72 | 96 (more detailed) |

## 4. Verification (decisive)

**Two-frame pixel difference**: `-ShotEvery=1` shoot two consecutive frames, landing-point region average pixel
difference **8.37**, max **246** → the water surface is being computed in real time, not a static texture.
The bright-spot distribution and ripple direction differ noticeably between the two frames.

Whole-channel look: `docs/fluid_shots/physical_fluid.png` — continuously undulating dynamic water surface,
the water column plunges directly into the fluid, the landing point has a physically pressed dark depression,
enemies wading through stir trailing ripples (`ApplyImpulse` in `Tick` based on movement speed).

**Final-state re-check** (`verify_fluid.py`): bInflow=True, all parameters in effect,
all three static patches hidden.

## 5. Trade-offs and lessons

**"Too fake" is often because static decorations cover a dynamic system that already exists**:
this round created no new particles/Niagara, instead deleted patches and amplified the existing physical pulse —
using the project's native height-field simulation achieved "real fluid." Modifying the C++ rendering pipeline
or adding particle assets would only be heavier and more likely to break the already-verified simulation.

**Read source code before acting**: `RobotCoolantField`'s `bInflow` / `Churn` /
`Foam` vertex-color comments spell out the design intent, saving the effort of reinventing the wheel.

**Prove dynamism with a two-frame difference**: a static screenshot can't show "is it simulated,"
shooting two frames and computing pixel difference is low-cost, deterministic verification.

## 6. Added scripts

| File | Purpose |
| --- | --- |
| `ue/Scripts/probe_coolant_params.py` / `probe_inflow_bool.py` | Read fluid simulation parameters |
| `ue/Scripts/probe_coolant_mat.py` / `probe_coolant_vc.py` | Check fluid material and vertex-color channels |
| `ue/Scripts/upgrade_fluid.py` | Hide static patches + strengthen physical pulse |
| `ue/Scripts/verify_fluid.py` | Final-state re-check |

---

# Round 115 (2026-11-11): Landing Splash — Niagara Reconnaissance + C++ Physical Droplets

## 1. Requirement

User: "Add a Niagara landing splash set, make the water column crash down and splash droplets/spray."
Insisted on "using Python to fully automatically generate a usable Niagara splash system."

## 2. Niagara route (tested thoroughly, conclusion: not viable in current environment)

### What works
- `.uproject` enables the Niagara plugin ✓
- `NiagaraSystemFactoryNew` / `NiagaraEmitterFactoryNew` classes exist ✓
- `duplicate_asset` copies engine templates ×5 (Fountain/RadialBurst/SimpleExplosion/
  DirectionalBurst/Minimal) → **after explicit save_loaded_asset they land on disk, reload correctly,
  class correct, logs show the system compiles** ✓
- `NiagaraActor` + `NiagaraComponent` attached to the scene ✓

### What doesn't work (decisive)
Attach the 5 template systems **150~450cm directly in front of the player, normal game camera, multi-angle
screenshots**, and **not a single particle** appears. Root cause: when `duplicate_asset` copies engine Niagara
templates, the emitter's runtime script/parameter definition references aren't relocated → you can create
the `.uasset` file, but not a system that emits particles. UE5.8 Python's editing support for the Niagara graph
(`get_exposed_parameters` / `emitter_handles` etc.) is all unavailable.

Side finding: under **SM5** the project has 7 materials `Failed to compile Material for
platform PCD3D_SM5` (including channel/water materials), some Niagara rendering paths suffer from this too.

**All test residue cleared** (0 NiagaraActors, test assets deleted, FX directory emptied),
scene restored to original state.

## 3. Final solution: custom C++ physical droplets (user confirmed)

Extend `ARobotCoolantField`, add droplet particles on the existing real-time height field:

| Component | Implementation |
| --- | --- |
| Rendering | `UInstancedStaticMeshComponent` (engine Sphere), one component draws all instances |
| Spawning | Each `bInflow` injection pulse synchronously calls `SpawnDroplets(N)` — same source as physical ripples |
| Physics | Per-frame semi-implicit Euler: `Vel.Z -= g·dt; Pos += Vel·dt`, thrown upward + scattering |
| Death | Falls back to water `Pos.Z<=BaseZ` or lifetime expires |
| Closed loop | On landing, 12% chance to inject a very light ripple (`-0.12, r10`) — too strong would churn the whole pool white |
| Appearance | Dedicated `M_SplashDroplet` (translucent cyan-white + emissive), individual sizes random 0.55~1.45 |
| Guardrails | `MaxDroplets` cap, skip when pool full |

### Key parameters (only enabled for `CoolantSpill_0` in the level, 4 toxic still pools off)
3 per pulse, upward 300cm/s, scatter 85, gravity 980, radius 9cm,
lifetime 0.6~1.0s, cap 54.

## 4. Verification (decisive)

Added a surviving-droplet log every 2 seconds, measured:
```
[Droplet] CoolantSpill_0 alive=0 → 28 → 28 → 30 → 29 → 25 → 29 → 28
pool=54 MaxDroplets=54
```
Droplets are **continuously spawning, flying, and dying** — living physical particles, not static spheres.
Close-up `docs/droplet_shots/final_close.png`: cyan-white spray dots of varying sizes around the landing point,
water undulation and spray in the same frame.

## 5. Iteration process (visual tuning trade-offs)
- v1 droplets covered the whole channel like a layer of white dots → tightened parameters, only enable for coolant pool
- v2 droplets formed a diagonal white band (projection of ballistic trajectories from top view) → shortened lifetime, weakened landing ripples
- v3 invisible at eye level (too small) → radius 3.2→6→9, upward 130→220→300
- v4 added individual size randomization to avoid the mechanical "uniform little balls" feel

**Didn't scale infinitely**: any bigger and they stop looking like droplets and start looking like floating balls.
Current scale is a physically reasonable landing-splash size.

## 6. Lessons

**"Class exists / can land on disk" ≠ "works at runtime"**: Niagara factory classes exist, assets can be
copied, logs show compilation, but particles just don't emit — must verify runtime behavior with "in-your-face
screenshots," don't trust API return values alone.

**When Python automation hits a wall, returning to the project's existing C++ systems is often more stable**:
`RobotCoolantField` is already a 60Hz per-frame physics simulator; droplets just hang an ISM particle layer on it,
also closing the loop with `ApplyImpulse`. Far more reliable than forcing Niagara assets, and completely
independent of SM6 / the Niagara editor.

**Verify "living particles" with logs**: screenshots can't show dynamics, but surviving counts fluctuating over
time (0→28→25→29) is deterministic evidence.

## 7. Modified/added files

| File | Change |
| --- | --- |
| `ue/RobotGame.uproject` | Enable Niagara plugin (for reconnaissance, final solution doesn't depend on it) |
| `Public/RobotCoolantField.h` | Add Droplets component, droplet parameters, FSplashDroplet, 3 functions |
| `Private/RobotCoolantField.cpp` | Droplet spawn/integrate/render/closed loop, injection pulse hook, Tick drive, diagnostic logs |
| `ue/Scripts/build_droplet_mat.py` | Create M_SplashDroplet |
| `ue/Scripts/tune_droplets.py` / `finalize_droplets.py` / `big_droplets*.py` | Level parameter tuning |
| `ue/Scripts/test_droplets_off.py` | Determine source of white band (distinguish droplets vs water foam) |
| `ue/Scripts/*niagara*.py` | Niagara feasibility reconnaissance and cleanup (kept for record) |
| `RobotCharacter.cpp` | Added `-ChannelCam/-SplashLow/-DropletClose/-NiagaraTest` cameras |

---

# Round 116 (2026-11-11): Upgrade Blender 5.2.2 -> 5.3.0

## 1. Requirement and decision

User: "Update Blender." Interaction confirmed: **upgrade to Blender 5.3 (latest major version)**.

Current state: local `C:\Program Files\Blender Foundation\Blender 5.2` = 5.2.2 LTS (2026-09-15).
Official latest stable = **5.3.0** (released 2026-11-10, Gaussian Splatting / DLSS / Blender Projects etc.).

## 2. Install method: portable side-by-side (don't touch system, reversible)

Downloaded `blender-5.3.0-windows-x64.zip` (406MB), **SHA256 verified against official value**:
```
3ac567a63d59d9934f7b9213bfb27ba05760e1fb366f8f55c381573ec3eabfa8
```
Extracted to `C:\AI\Blender\5.3\` (standalone directory).
**5.2.2 fully preserved**, both versions coexist, can roll back anytime — no MSI overwrite install.

Final path: `C:\AI\Blender\5.3\blender-5.3.0-windows-x64\blender.exe`
(5.3.0, build 2026-11-10).

## 3. Automation: find_blender auto-detects by version

Added `tools/find_blender.py` — shared by all tool scripts:

Priority:
1. Environment variable `ROBOT_BLENDER` (explicit override)
2. `C:\AI\Blender\**\blender.exe` (portable versions, descending by version number)
3. `C:\Program Files\Blender Foundation\**\blender.exe` (installed versions, descending)

Selecting "highest version number first" → when 5.3 is installed, 5.3 is used automatically; when 5.3 is absent,
automatically falls back to 5.2.

`tools/hy3d_texture_batch.py` originally hardcoded `Blender 5.2\blender.exe`,
changed to `from find_blender import find_blender`. A global sweep confirmed the project has
**no other hardcoded Blender paths** (`tools/blender/*.py` are scripts executed by Blender itself,
not responsible for locating the executable).

`compile_check.py` compiled 47 scripts under 5.3: **OK=47 FAIL=0**.

## 4. 5.3 Python API compatibility (key point)

First audited APIs used by 46 scripts (`audit_scripts.py`), then instance-level testing with a 5.3 instance:

| API | 5.3 status | Handling |
| --- | --- | --- |
| `Mesh.calc_loop_triangles` / `loop_triangles` | **Still available on instances** | No change needed (first check using the `bpy.types.Mesh` class attribute was a false positive) |
| `Object.bound_box` | **Still available on instances** | No change needed |
| `mathutils.Vector.to_track_quat` | Available | No change needed |
| **`BLENDER_EEVEE_NEXT` engine name** | **Removed**, changed to `BLENDER_EEVEE` | **Only breaking change** |

Fixed 2 scripts with hard assignments to use graceful fallback "new name → old name → Workbench",
compatible with both 5.2/5.3:
- `tools/blender/render_idol_views.py`
- `tools/blender/verify_hy3d_glb.py`

`build_robot.py` / `robotlib.py` were already written as
`for eng in ('BLENDER_EEVEE_NEXT','BLENDER_EEVEE','CYCLES')` with attempts,
5.3 automatically falls to `BLENDER_EEVEE`, **no change needed**.

## 5. End-to-end verification (5.3 actual run)

| Test | Result |
| --- | --- |
| `verify_hy3d_glb.py` import + render preview | ✓ renders correctly (EEVEE fallback works) |
| `texture_project_auto.py` (CYCLES bake + projected texture, most complex) | ✓ full 5 steps pass, 41.5MB GLB |
| `hy3d_texture_batch.py` via find_blender automatically uses 5.3 | ✓ generator projected texture 57.9MB / 12s |
| 47 scripts py_compile | ✓ 0 failures |
| Dual-version coexistence / env-var override / fallback to 5.2 after removing 5.3 | ✓ all pass |

`HIPEW initialization failed` is just a warning from attempting AMD HIP, the script already has
OptiX→CPU fallback, no impact.

## 6. workbuddy blender-bridge (stated honestly, unchanged)

`C:\Users\25227\Documents\workbuddy\opencode-blender-bridge` finds Blender by scanning
`Program Files\Blender Foundation` + environment variables `BLENDER_PATH`/`OCBB_BLENDER`,
does **not recognize** `C:\AI\Blender\5.3`, will still use 5.2.
Because it's a separate project, its source/config wasn't changed this round; if you also want to use 5.3, set the
environment variable `BLENDER_PATH=C:\AI\Blender\5.3\blender-5.3.0-windows-x64\blender.exe`
(the plugin already supports it, no code changes needed).

## 7. Lessons

**For major version upgrades do instance-level API testing first, don't trust class-attribute hasattr**:
checking `calc_loop_triangles` on `bpy.types.Mesh` returns False, but it exists on instances —
almost misjudged that 7 scripts needed changes. The only real breaking point was the EEVEE engine rename.

**Portable version + version auto-detection = zero-risk upgrade**: no registry writes, old version preserved,
select by version number, auto-fallback when missing. Much more stable than MSI overwrite install.

**Don't skip SHA256 verification**: for a 406MB download, a one-line official checksum confirms integrity.

## 8. Added/modified files

| File | Change |
| --- | --- |
| `tools/find_blender.py` | New: auto-detect Blender by version (with fallback/env var) |
| `tools/hy3d_texture_batch.py` | Hardcoded 5.2 path -> find_blender() |
| `tools/blender/render_idol_views.py` | EEVEE engine name compatible with 5.3 |
| `tools/blender/verify_hy3d_glb.py` | EEVEE engine name compatible with 5.3 |
| `tools/blender/audit_scripts.py` | New: audit API usage of 46 scripts |
| `tools/blender/compile_check.py` | New: batch syntax compile check for 5.3 |

---

# Round 117 (2026-11-11): Switch to Standard Overwrite Install (No Coexistence)

## 1. Requirement

User: "Don't keep both, overwrite install" — undo Round 116's "portable + 5.2 coexistence,"
switch to a standard single-version MSI overwrite install.

## 2. Privilege elevation (key prerequisite)

The current PowerShell process is **Medium integrity level (non-admin)**, MSI install/uninstall writing to
`Program Files` requires elevation. Testing confirmed `Start-Process -Verb RunAs` elevates successfully
(verified via an elevated bat writing a probe file to `C:\Program Files`, confirming the system directory is
writable), UAC setting `ConsentPromptBehaviorAdmin=5`.

## 3. Execution (one elevated run, avoid multiple UAC prompts)

Downloaded `blender-5.3.0-windows-x64.msi` (365.8MB), **SHA256 matches official**:
```
3ff4ec8a488be1148aa2bdb2cb229be21b8050e75931da617934cac254dd726c
```

Generated elevated batch `do_blender_install.bat`, executed once via `Start-Process -Verb RunAs`:
1. Clean up elevation probe residue
2. `MsiExec.exe /X{4B0BC91B-29A6-4B8C-A60B-6154FD3AE3AD} /qn` silently uninstall 5.2.2
3. `MsiExec.exe /I blender53.msi /qn` silently install 5.3.0

Both step exit codes were **0**.

## 4. Result (single version)

| Item | Result |
| --- | --- |
| Registry | Only `Blender 5.3.0` remains, installed at `C:\Program Files\Blender Foundation\Blender 5.3\` |
| `Program Files\Blender Foundation` | Only `Blender 5.3` (5.2 uninstalled) |
| `C:\AI\Blender` portable version | Deleted |
| Downloaded ZIP/MSI | Cleaned up (saved ~770MB) |
| blender.exe | `Blender 5.3.0` |

`tools/find_blender.py` needed no change: it already scans
`C:\Program Files\Blender Foundation` in descending version order, after deleting the portable version it
automatically points to `...\Blender 5.3\blender.exe` (verified in testing).

## 5. Verification (MSI installed version actual run)

- `verify_hy3d_glb.py` import + render preview: ✓ renders
- 47 scripts compile under 5.3: **OK=47 FAIL=0**
- find_blender points to system 5.3 with correct version

The EEVEE engine name compatibility added in Round 116 (`BLENDER_EEVEE_NEXT` →
`BLENDER_EEVEE` fallback) continues to work.

## 6. Lessons

**"Coexistence" vs "overwrite" are two upgrade strategies**: portable coexistence is zero-risk but leaves two
versions; when the user wants a clean single version you must go the MSI uninstall+install route, which in a
non-admin session requires first solving elevation. Running the whole flow in one elevation (uninstall+install) is
more stable than multiple UAC prompts.

**First verify elevation can really write the system directory, then do the real install**:
using a bat to write a probe file to `C:\Program Files` is a low-cost decisive test,
avoiding the intermediate state of "install fails halfway due to permissions, 5.2 uninstalled but 5.3 not installed."

**find_blender's directory-scanning design remains valid after overwrite install**:
no hardcoded path, descending version order, multi-root scanning — delete the portable version and it lands on
the system version automatically, no script changes needed.


---

# Round 118 (2026-11-12): Mech Wreckage Asset Batch (4 pieces)

## 1. Goal
Using the existing pipeline "generate concept image → Hunyuan3D to 3D → projected texture → UE,"
add another batch of "destroyed mech wreckage" assets to enrich the narrative of the expanded area
(X 2400–5400, Y±900).
Themes: damaged mech torso / severed mechanical arm / abandoned helmet / armor debris pile.

## 2. Output
- 4 concept images: `C:\AI\Hunyuan3D\input\gen_<name>.png` (ComfyUI z_image_turbo).
  `mech_head_wreck` first generated looking like a human skull, regenerated once to a mech helmet.
- 4 white models + projected-texture GLBs: `output\*.glb` / `output\*_tex.glb`.
- 4 textured showcase images: `docs\gen3d_shots\show_<name>.png`.
- `severed_mech_arm` had 2 pieces of 1.99×1.99 "background large planes" (single-image reconstruction artifacts),
  deleted 509k faces by Z-layer with `tools\blender\clean_bg_planes.py` (77MB→26.5MB).

## 3. Key lesson (setting the trap for Round 119)
Hunyuan3D single-image models **have no UV**, projected textures only work on the front and fall back to white
on the back → user proposed "you can use texgen to generate textures, the effect is better," moving to Round 119.

---

# Round 119 (2026-11-13): texgen Native PBR Texture Assault + Wreckage Landed

## 1. Goal
Switch the 4 wreckage pieces from Round 118 to Hunyuan3D's official texgen (multi-view diffusion PBR texturing),
replacing projected textures to get all-angle textures; import into UE, place, screenshot for acceptance.

## 2. texgen from "hung" to "working" troubleshooting chain (core of this round)
**Conclusion first: texgen runs on the 8GB VRAM RTX 4070 Laptop, 1024 resolution is fine.**
User insisted "1024 worked before," so troubleshooting layer by layer:

1. **DLL loading** ✓ under Python 3.12 `custom_rasterizer_kernel.pyd` requires, before import,
   `os.add_dll_directory(torch/lib)` + `CUDA\v12.4\bin` (adding to PATH doesn't work).
2. **Resolution** ✓ key: `pipe.render.set_default_render_resolution(1024)` /
   `texture_resolution(1024)` / `config.render_size=texture_size=1024`.
   First version of `texgen_asset.py` missed these lines, used default 2048 → VRAM blew up, hung for a whole day.
   (The already-working `run_texgen.py` has these lines.)
3. **Reference image alpha** ✓ texgen's `recenter_image`/`delight_model` rely on alpha to determine the subject.
   ComfyUI-produced `gen_*.png` are RGB light-gray background; use
   `tools\gen_alpha_for_texgen.py` to cut to RGBA (transparent fraction 0.70~0.90, consistent with baseline
   `herta_rgba.png` at 0.717).
4. **"Hung" misjudgment** ✗→✓ used `texgen_staged.py` to split `__call__` into staged timing,
   found "GPU 0% + CPU maxed" wasn't a deadlock but **UV unwrapping being extremely slow on high-face white models**:
   `delight 64s / uv_wrap 330s / render 1s / diffusion 237s / bake 1s / inpaint 15s`.
   We had judged "hung" too early.
5. **Face reduction** ✓ after reducing white models to 50k faces, **uv_wrap 330s→1.3s** (100×),
   single-asset total time down to about 5.7 min. Stop ComfyUI before running to free VRAM (diffusion peak 9.9GB,
   relying on `expandable_segments` to tough it out, ComfyUI resident squeezes out margin causing
   inpaint/export failures).
6. **After RGBA + 1024 + face reduction + stopping ComfyUI all aligned, texgen stably ran 4/4.**

## 3. The "point cloud" nightmare and root cause (biggest pitfall of this round)
After face reduction all 4 assets rendered as "point clouds/fragments." Located by layer-by-layer quantification:
- Original white model rendered **completely normally** (solid mech torso).
- `trimesh` vertex uniqueness 99.95% (already welded), ruling out "unwelded points."
- Two decimators (trimesh quadric / Blender Decimate) both ruined it → ruling out the decimation algorithm.
- **Decisive evidence**: connected components of `mech_torso_wreck.glb` = 2,
  but after one pass through Blender `clean_bg_planes.py` the `_nobg.glb` = **557984 components**;
  area 12.99→1.29 (collapsed 90%).
  → **Blender GLB import/export splits vertices by normal/UV**, breaking 560k faces into 560k
  independent triangles, after which any decimation turns into individually collapsing "point clouds."

**Fix: use trimesh throughout, no Blender round-trip, keep vertices welded.**
`tools\texgen_batch2.py`:
- Read original white model (welded) → delete by connected component "extremely flat (flatness<0.02) and area
  fraction>15%" background large planes/base disks → `simplify_quadric_decimation` down to 50k faces
  (area maintained 100.5~100.8%, script has built-in 30% collapse protection) → texgen → showcase image.
- Single-instance lock `texgen_batch2.lock`: 8GB VRAM absolutely cannot run two texgens in parallel
  (this round cleaned up 4 times due to duplicate launches fighting for VRAM).
- `mech_torso_wreck`/`severed_mech_arm` each had background large planes/base disks deleted,
  `mech_head_wreck`/`armor_debris` had no stray faces.
- Result `output\*_texgen_final.glb` (4 pieces, 2.1~2.5MB) + showcase images,
  all 4 are complete solids + all-angle PBR textures (white armor, cyan-green visor/energy pieces, scorched distressed edges).

## 4. texgen texture "black hole" fix
In UE the torso had abrupt black patches. Extracted basecolor found **25~36% pure black** — multi-view diffusion
didn't bake self-occluded faces invisible from all 6 views, inpaint didn't fill them (Blender's fixed lighting
happened not to hit them, invisible in showcase images).
`tools\fix_texgen_black.py`: classify "extremely dark (<48) and low saturation" as unbaked holes,
fill by diffusion from neighbors with `cv2.inpaint` (Telea, radius 7), preserving intentionally dark things like
cyan-green pieces/gold wear/dark-blue armor/dark-gray internals. **Pure-black fraction 36%→0%**.
Produced `output\*_texgen_fixed.glb` + 4 `show_*_fixed.png` showcase images.

## 5. UE landing and acceptance
- Backed up level → `$env:TEMP\opencode\ue_backup_texgen_import\`.
- `ue\Scripts\import_mechwreck.py`: priority
  `*_texgen_fixed.glb` > `*_texgen_final.glb` > `*_tex.glb`;
  4 imported to `/Game/RobotGame/Art/Props/Gen3D/<name>/SM_<name>`,
  bbox 88~199cm, each with 1 texture material slot.
- `ue\Scripts\place_mechwreck.py`: 4 wreckage pieces placed in the new area
  (torso 4400,620 / arm 4050,700 / helmet 3200,-760 / debris 4900,-760),
  tag `MechWreck`, scaled to height 110~300cm, level saved.
- Added debug cameras `WreckCam` (mode 24, wreckage close-ups) / `WreckTop` (mode 25, top panorama),
  `RobotCharacter.cpp` recompiled successfully.
- Screenshot acceptance: `-WreckCam` / `-WreckTop` confirmed textures correct in UE, no large black patches,
  dark parts are inherently dark structures like the chest cavity/joints; confirmed dumped imported UE textures
  are 0% pure black (i.e., the fixed version took effect). Top panorama shows 4 wreckage pieces spread to both
  sides, a richer scene.

## 6. Added/modified files this round
| File | Purpose |
|---|---|
| `C:\AI\Hunyuan3D\texgen_asset.py` | texgen corrected version (DLL+1024 resolution) |
| `C:\AI\Hunyuan3D\texgen_staged.py` | Staged-timing texgen (locate bottlenecks, batch actually calls this) |
| `C:\AI\Hunyuan3D\simplify_for_texgen.py` | trimesh face reduction (for diagnosis) |
| `tools\gen_alpha_for_texgen.py` | Concept image RGBA matting |
| `tools\texgen_batch2.py` | **Official pipeline this round** (trimesh clean background + face reduction + texgen + showcase, with single-instance lock) |
| `tools\fix_texgen_black.py` | cv2.inpaint repair basecolor black holes |
| `tools\diag_decimate.py` / `diag_parts.py` / `dump_tex.py` | Point-cloud root cause / texture diagnosis |
| `tools\blender\decimate_blender.py` | Blender Decimate verification (exclusion use, not adopted) |
| `ue\Scripts\import_mechwreck.py` | Priority `_texgen_fixed.glb` import |
| `ue\Scripts\place_mechwreck.py` | Wreckage placement (tag MechWreck) |
| `ue\Scripts\diag_wreck_mat.py` / `diag_wreck_texture.py` | UE material/texture diagnosis |
| `ue\Source\RobotGame\Private\RobotCharacter.cpp` | +WreckCam/WreckTop cameras |
| `docs\gen3d_shots\show_*_texgen.png` / `show_*_fixed.png` | Showcase images |

## 7. Still worth noting
- texgen ~6~8 min per asset, diffusion VRAM peak ~9.9GB (8GB card toughs it out in segments),
  must stop ComfyUI before running, serial, single instance.
- `expandable_segments` is not supported on Windows (warning only), doesn't affect results.
- texgen black holes are an inherent defect of self-occluded faces, `fix_texgen_black.py` is a post-processing
  fallback; using simpler compositions / more views could further reduce them.


---

## Round 119 · Continued (2026-11-13): Water Column Vertical Texture Fix (SM5 Material Compile Failure)

### 1. Symptom
User screenshot feedback: the **vertical water column** at the channel injection outlet is pure gray-brown,
flat, without texture, completely disconnected from the metal corrugated pipe above and the bright blue channel
water (like a cement stick).

### 2. Root cause (log-confirmed, not guesswork)
`ue\Saved\Logs\RobotGame.log` repeated continuously from 11/10 to 11/13:
```
M_WaterJet_Coolant.uasset: Failed to compile Material for platform PCD3D_SM5,
Default Material will be used in game.
  (Node TextureSampleParameter2D) Sampler type is Linear Grayscale,
  should be Grayscale for T_Toxic_Bub
```
- The project RHI is **D3D12 but Feature Level SM5** (`rhifeaturelevel="SM5"`).
- In the water column materials `M_WaterJet_Coolant` / `M_WaterJet_Toxic`,
  the `TextureSampleParameter2D` sampler node has sampler_type = `LinearGrayscale`,
  but the texture `T_Toxic_Bub` is ordinary `Grayscale` (sRGB) → **sampler type mismatch,
  entire material fails to compile under SM5 → engine falls back to the default gray material** →
  water column becomes flat pure gray.
  Unrelated to translucency, VRAM, or normals.
- In the level `Jet_CoolantSpill_0` indeed uses `M_WaterJet_Coolant` (confirmed by diagnostic script).

### 3. Fix (two stages)
**Stage 1 — make the material compile**:
`ue\Scripts\fix_waterjet_mat.py` (new). Don't delete the material asset (preserve level references),
clear expressions, rebuild with a **regular `TextureSample`** explicitly setting
`SAMPLERTYPE_GRAYSCALE` matching the texture into a "deep cyan + flowing bubble streaks + translucent" water
column, recompile + save; explicitly `set_material` re-attach the 5 `Jet_*` water columns in the level.
After rerunning the editor, the `M_WaterJet_*` SM5 failure logs **disappeared**, water columns went from flat gray
to translucent deep cyan.

**Stage 2 — make the texture visible**:
dumped `T_Toxic_Bub` and found it is **sparse white dots on black** (R mean 2.5 / p90=0,
99% pure black) — only suited as foam accents, nearly invisible as water column streaks.
`tools\make_jet_flow_tex.py` generated a dedicated `T_Jet_Flow.png` (horizontal ripple light/dark bands
+ broken bubble highlights, tileable; R mean 152 / std 47 / p10~p90=90~209),
imported into UE via `T_Jet_Flow` (TC_GRAYSCALE / sRGB off / Wrap);
material switched to `SAMPLERTYPE_LINEAR_GRAYSCALE` to match (also compiles under SM5).
UV scrolls downward along V (Panner speed_y=-3.0) → reads as "downward-flowing water column";
emissive uses Power(0.7) to brighten midtones and strengthen bright bands, opacity=0.42+0.50×streaks.
Final water column is a **glowing cyan flowing column**, harmonious with the corrugated pipe highlights and
channel water.

### 4. Acceptance
- `-DropletClose` close-up screenshot: water column has light/dark flowing streaks + bubble highlights,
  translucent showing the water surface behind, deep cyan the same color as channel water; no longer flat pure gray.
- `shot_JetFinal.log`: `M_WaterJet_*` no SM5 compile failures (clean pass).
- Level saved; backup `$env:TEMP\opencode\ue_backup_jetfix\`.

### 5. Notes (unchanged)
This round focused on the water column the user pointed at. The log still has 6 other material SM5 compile
failures, same class of historical problems, unrelated to the water column:
`M_Basin_Concrete` (LinearColor/Color mismatch), `M_Toxic_Bed`,
`M_Coolant_Fluid` (2 LinearGrayscale nodes each), three PolyHaven walls
(ComponentMask missing input). If those surfaces later also show "default gray," fix sampler_type or fill in
the missing inputs the same way.

### 6. Added/modified files this round
| File | Purpose |
|---|---|
| `ue\Scripts\fix_waterjet_mat.py` | Rebuild 2 water column materials + re-attach 5 Jet_* (idempotent) |
| `tools\make_jet_flow_tex.py` | Generate water column flow streak texture T_Jet_Flow.png |
| `tools\asset_src\T_Jet_Flow.png` | Streak texture source (imported as UE asset T_Jet_Flow) |
| `ue\Scripts\diag_jet_state.py` | Diagnose water column actor material + material compile state |
| `ue\Scripts\dump_bub.py` | dump T_Toxic_Bub to confirm its 99% pure black |
| `ue\Content\...\Materials\M_WaterJet_Coolant/Toxic.uasset` | Rebuilt water column material |
| `ue\Content\...\Materials\T_Jet_Flow.uasset` | Newly imported flow streak texture |


---

## Round 119 · Continued 3 (2026-11-13): Round Pool Texture Fix

### 1. Symptom
User reported the circular toxic pool (center -200,350) also has a texture problem. `-BasinCam` screenshot:
the **right half of the liquid surface has a large patch of golden/copper fine ripple reflections**, the left half
normal dark green, with a cyan water column in the middle — like a wrong warm-texture/stain applied.

### 2. Layered localization (A/B + logs, eliminating layer by layer)
1. **Diagnose pool composition** (`diag_basin_state.py`):
   - `ToxicBed_0` pool bottom disc -> `M_Toxic_Bed`
   - `ToxicFluid_0` = `ARobotCoolantField`, `SurfaceMaterial = M_Toxic_Fluid`
     (runtime uses `Surface->SetMaterial` in `BeginPlay` to draw the liquid surface)
   - `Basin_ToxicFluid_0` pool wall container (C++ `RobotBasin`)
   - Gold on the liquid surface is unrelated to pool bottom/walls (changing the surface material makes it disappear).
2. **SM5 compile failures** (`shot_BasinDiag.log`): `M_Toxic_Fluid`,
   `M_Coolant_Fluid`, `M_Toxic_Bed`, `M_Basin_Concrete` all
   `Failed to compile Material for PCD3D_SM5`:
   ```
   (Node TextureSampleParameter2D) Sampler type is Linear Grayscale,
   should be Grayscale for T_Toxic_Bub
   (Node TextureSampleParameter2D) Sampler type is Linear Color,
   should be Color for T_ConcreteDetail
   ```
   Exactly the same origin as the "water column": sampler_type in the material's TextureSampleParameter2D
   doesn't match the referenced texture's sRGB.
3. **Texture config** (`diag_tex_cfg.py`): `T_Toxic_Bub` srgb=True/TC_GRAYSCALE
   → should be `GRAYSCALE`; `T_Coolant_F` srgb=False/TC_GRAYSCALE
   → should be `LINEAR_GRAYSCALE`; `T_ConcreteDetail` srgb=True/BC7
   → should be `COLOR`. In the materials they were all set to the Linear version.
4. **A/B determination of gold source** (`ab_fluid_mat.py`): temporarily swap `ToxicFluid_0`'s
   SurfaceMaterial to `M_Coolant_Fluid` → **gold mottling completely disappears**.
   Proves the gold isn't scene reflections/PPV/pool bottom, but `M_Toxic_Fluid` material itself.
5. **Material trace** (`dump_fluid_mats.py` / `trace_toxic.py`):
   `M_Toxic_Fluid` has no warm constants at all (all dark green/gray-blue cool colors), but contains
   a strong specular reflection chain of `Fresnel` + `ReflectionVectorWS`, roughness dynamically lowered by lerp
   → under Lumen/warm lights it maxes out environment reflections into golden copper patches.
   `M_Coolant_Fluid` has low reflection weight, hence no such problem.

### 3. Fix
**A. Batch-fix samplers (preserve original material design)** `fix_fluid_samplers.py`:
iterate all TextureSample(Parameter)2D in 4 materials, automatically reset sampler_type per the referenced
texture's srgb/compression, recompile+save:
- `M_Toxic_Fluid` 4 / `M_Coolant_Fluid` 2 / `M_Toxic_Bed` 2
  `T_Toxic_Bub` -> `SAMPLERTYPE_GRAYSCALE`
- `M_Basin_Concrete` `T_ConcreteDetail` -> `SAMPLERTYPE_COLOR`
After rerun, SM5 compile failures for these 4 materials all disappeared (only 3 PolyHaven walls with
ComponentMask missing input remain, unrelated to the pool).

**B. Switch liquid surface to a clean material** `finalize_toxic.py`:
gold remained after sampler fix (a reflection design problem). Tried building a custom simplified material
`M_Toxic_Fluid_Fixed` (no Fresnel/Reflection), but it itself hit
`(Node Multiply) float2 and float3 are undefined` SM5 compile error
→ fell back to the default gray checkerboard, that experimental asset was deleted.
Finally pointed `ToxicFluid_0.SurfaceMaterial` to the **A/B-verified gold-free**
`M_Coolant_Fluid` (dark green liquid + blue foam band + landing-point white foam), level saved.

### 4. Acceptance
`-BasinCam` final screenshot: gold mottling thoroughly gone, circular pool is a clean dark green liquid surface +
blue foam band + landing-point white foam, pool walls have concrete/metal texture; SM5 compile only has 3
PolyHaven wall historical issues. Level saved;
backup `$env:TEMP\opencode\ue_backup_basinfix\`.

### 5. Added/modified files this round
| File | Purpose |
|---|---|
| `ue\Scripts\fix_fluid_samplers.py` | Batch-fix sampler_type per texture (4 materials, core fix) |
| `ue\Scripts\finalize_toxic.py` | Liquid SurfaceMaterial -> M_Coolant_Fluid + delete experimental material |
| `ue\Scripts\diag_basin_state.py` / `diag_fluid_mat.py` / `diag_tex_cfg.py` | Pool composition/SurfaceMaterial/texture config diagnosis |
| `ue\Scripts\dump_fluid_mats.py` / `dump_mat_links.py` / `trace_toxic.py` | Material expression/reflection chain trace |
| `ue\Scripts\dump_fluid_tex.py` / `dump_bub.py` | Texture dump (confirm no warm texture) |
| `ue\Scripts\ab_fluid_mat.py` | A/B swap material to determine gold source |
| `ue\Content\...\Materials\M_Toxic_Fluid/Coolant_Fluid/Toxic_Bed/Basin_Concrete.uasset` | Materials after sampler fix |

### 6. Notes
- Circular pool liquid surface now uses `M_Coolant_Fluid`, same material as the coolant channel
  (dark green/blue band), losing the original "toxic green" distinction; if you later want to restore a
  dedicated toxic color while avoiding gold, you need to rebuild a simplified material without
  Fresnel/low-roughness specular that compiles under SM5 (this round's custom version failed due to
  float2×float3 Multiply error).
- Pool wall `M_Basin_Concrete` after sampler fix revealed `T_ConcreteDetail`'s
  black-and-white concrete mottled texture (the previous compile-failure fallback was pure white), a normal
  texture, slightly noisy but acceptable.


---

## Round 119 · Continued 4 (2026-11-13): Full-Scene Clipping / Floating Fix

### 1. Symptom
User reported "many places have clipping problems, and some models are floating." Full-scene geometry sweep,
not guessing one by one by eye — first locate with bounding-box data + multi-view screenshot re-check.

### 2. Diagnosis (data first)
1. **`diag_geometry.py`**: dump world bounding boxes and bottom Z of all 375 StaticMeshActors
   (`docs/geom_diag.txt`).
   - Wooden crates three layers `zmin=62/125`: checked `SM_met-wooden-crate01a` height 21cm,
     scale 3.0→63cm, three layers Z=0/63/126 **precisely aligned**, designed stacking, **not floating**.
   - Pipes A/B/C `zmin=20`, sconces/posters/fans mounted on walls: all designed hanging, not bugs.
   - 4 MechWreck wreckage pieces `zmin≈-3~+2`: landing formula correct, no floating.
2. **`diag_overlap.py`**: prop-level bbox pairwise intersection detection (`docs/overlap_diag.txt`),
   initially 83 pieces / **32 pairs** overlapping. Classification:
   - about 18 pairs are intentional stacking of original arena `PROP_*` industrial yard
     (verified normal by top view `geom_scenic`), not bugs;
   - `Pipe B/C × Pipe Joint A/B`: pipes are supposed to connect to joints, designed connections;
   - **real clipping concentrated in "last-added wreckage" and "Gen3D filler large pieces"**:
     - severed arm crossed by `Field Fence A`, helmet inserted into `Industrial Generator/Sandbag A2`,
       `Armor Debris Pile × Abandoned Mech Core`;
     - `Pipe Joint B × Abandoned Crane Arm`, `Oil Drum Group B × Pipe Joint A`,
       `Sandbag A2 × Industrial Generator` and other Gen3D large pieces swallowing each other.
3. **Root causes**:
   - `place_mechwreck.py`'s 4 wreckage coordinates (4400,620)/(4050,700)/
     (3200,-760)/(4900,-760) were set independently, **landing inside the bboxes of existing Gen3D large
     pieces and Cosmos covers/fences**;
   - `place_gen3d.py` set target heights of 260/240/320/240/200cm for filler pieces,
     a size larger than the surrounding 50~160cm Cosmos props, so bboxes naturally swallow each other;
   - the two scripts each set coordinates independently, never coordinated with each other.

### 3. Fix (three batches, all with bbox collision validation, positions rollback-capable)
| Script | Action |
|---|---|
| `fix_wreck_overlap.py` | Use `find_wreck_spots.py` empty-spot search + per-piece bbox collision validation, **re-place 4 wreckage pieces**: torso(3900,-760), arm(3600,-760), helmet(4700,680), debris pile(4500,680), landing Z recomputed with pivot formula |
| `fix_gen3d_overlap.py` | Shrink "abandoned crane arm" to 190cm (the original 320 giant rubbed everything no matter how moved) and move to (4340,-800), eliminating `Pipe Joint B`/`Field Fence A`/`Sconce C` crane-arm clipping |
| `fix_gen3d_shrink.py` | Shrink `Pipe Joint A/B`→165cm, `Abandoned Mech Core`→165cm, `Industrial Generator`→140cm **in place** (position unchanged→preserve narrative and introduce no new collisions), recompute landing Z for new scale |

- Overlap pair progression: **32 → 28 → 26 → 25 → 23**; the "intersections involving MechWreck wreckage"
  section **went from 4 pairs to empty**, all crane-arm-related clipping cleared.
- Regression protection: sync `place_mechwreck.py`'s LAYOUT and `place_gen3d.py`'s target heights
  /crane coordinates **to the post-fix values**, avoid re-running old scripts reintroducing clipping (old
  coordinates in original files annotated with prominent comments).

### 4. Acceptance
- Remaining 23 pairs: ~18 pairs intentional stacking of original arena `PROP_*`, `Pipe×Pipe Joint` designed
  connections, `Sconce C×Pipe Joint B` / `Sandbag B1×Old Freezer B` etc. wall pieces lightly rubbing edges —
  top view `ScenicCam` re-check confirms normal industrial yard, judged not bugs, left untouched.
- Multi-view screenshot re-check (`-CosmosView` / `-WreckCam` / `-WreckTop`):
  - severed arm no longer crossed by fence, helmet placed flat on ground, debris pile landed and spread out,
    all 4 wreckage pieces on open ground, separated from each other, bottoms touching ground (`zmin≈0`);
  - `list_wrecks.py` confirms exactly 4 wreckage-class actors, no duplicate residue;
  - in `CosmosView` "helmet floating on top of crate stack" is a **low-angle perspective occlusion illusion**
    (the far (4700,680) helmet blocked by a near crate stack), `WreckTop` top view + `WreckCam` close-up
    both prove it's on the ground, not real floating.
- Level saved `L_TestArena.umap`; backup `$env:TEMP\opencode\ue_backup_geomfix\`.

### 5. Added/modified files this round
| File | Purpose |
|---|---|
| `ue\Scripts\diag_geometry.py` / `diag_overlap.py` | 375 actor bbox dump / prop pairwise intersection detection (core diagnosis) |
| `ue\Scripts\find_wreck_spots.py` / `diag_mesh_sizes.py` | Empty-spot grid search / mesh size check (rule out crate "fake floating") |
| `ue\Scripts\fix_wreck_overlap.py` | Re-place 4 wreckage pieces to collision-free spots (core fix) |
| `ue\Scripts\fix_gen3d_overlap.py` | Crane arm shrink + move |
| `ue\Scripts\fix_gen3d_shrink.py` | 3 types of Gen3D filler pieces shrunk in place |
| `ue\Scripts\list_wrecks.py` | Wreckage inventory (confirm no duplicates/floating) |
| `ue\Scripts\place_mechwreck.py` / `place_gen3d.py` | LAYOUT/sizes synced to fixed values (regression protection) |
| `docs\geom_diag.txt` / `overlap_diag.txt` / `wreck_fix.txt` / `crane_fix.txt` / `gen3d_shrink.txt` / `free_spots.txt` / `mesh_sizes.txt` / `wreck_list.txt` | Diagnosis and fix reports |

### 6. Notes
- The fix was deliberately **scope-limited**: only touched the "last-added, confirmed-colliding" 4 wreckage
  pieces + the conflict-causing Gen3D filler large pieces; **did not** broadly rearrange historical `PROP_*` / Gen3D /
  Cosmos layouts — most bbox overlaps are intentional industrial stacking, blindly moving things would break
  existing layout and introduce new collisions.
- Changing Gen3D filler pieces to "shrink in place" rather than "re-place" was specifically to avoid moving
  things and triggering a chain reaction.
