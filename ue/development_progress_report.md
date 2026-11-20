> Language: **English** | [简体中文](./开发进度报告.md)
# "Ember Protocol" Development Progress Report

**Update date**: 2026-10-14 (second major overhaul)
**Theme of this round**: from "looks like it runs" to "actually playable" — fix three **silently failing** core systems,
and complete the overheat pacing, modding system, sound effects and results loop.

---

## I. The Most Important Discovery: Three Core Systems Never Actually Worked

Last round's validation (60/60) checked "whether assets were configured", while this round did **real in-game behavior validation**
for the first time (auto-fire + logs + screenshots) and found three systems that produced no errors at all but whose entire chains were broken:

| # | System | Symptom | Root cause |
|---|---|---|---|
| 1 | **Player shooting** | Never spawned a projectile, consumed no power, generated no heat | The ability was granted directly from the C++ class, while `ProjectileClass` was only set in Blueprint → every activation silently returned |
| 2 | **Part damage** | Hit an enemy 100 times, no damage at all | Projectiles hit the **capsule**, and the hit result had no bone name → part routing never matched |
| 3 | **Overheat and power** | Heat only rose never fell, overheat never cleared, power only dropped never recovered | The `cooling rate`/`power recovery` attributes had data but **no code consumed them** |

### How They Were Fixed

1. **Projectile class fallback**: `GA_Fire` loads `BP_Projectile` at construction, falling back to the C++ class on failure.
2. **Nearest-bone fallback**: when the capsule is hit, find on the skeletal mesh "the nearest bone whose part table can route it"
   (measured: core→Part.Core, leg_L→Part.Leg.L all correct).
3. **Cooling/power recovery implemented + overheat latch**: aligned with the browser prototype's 2-second lock rule —
   overheat → lock 2 seconds (rapid heat venting during the lock) → unlock and reset; normally heat falls at the mech's cooling rate.

**Measured after the fix**: 45-second auto-battle = 72 hits, all 5 enemies disabled, 8 overheat cycles with no deadlock.

---

## II. Systems Added/Reworked This Round

### 1. Weapon Tiers (Aligned with the Loadout Table Validated in the Prototype)

Weapon stats changed from "globally fixed" to **configured per mech** (data lives in the mech asset):

| Mech | Damage | Fire rate | Heat per shot | Trait |
|---|---|---|---|---|
| Light scout | 8 | 0.115s | 6.5 | Fast low-damage, long burst (~4.4s to overheat) |
| Medium general | 15 | 0.19s | 11.5 | Balanced (~2.6s to overheat) |
| Heavy assault | 27 | 0.30s | 18 | Slow high-damage, short burst (~2.1s to overheat) |

**Shooting no longer consumes power** — power is the mobility resource (dash + module idle drain), heat is the constraint on shooting cadence.
(Lesson from testing: when two costs press on the same action, the numbers cancel each other out and both mechanics fail at once.)

### 2. Modding System (Design Pillar P1) — From Zero to Usable

- **Data**: 3 mechs × 9 slots (head/core/left & right arm/left & right thruster/backpack/auxiliary ×2)
  + **22 module data assets** (numbers designed around "mass/power/cooling pulling against each other")
- **UI**: press **M** in-game to open the modding bench (pause world + mouse control)
  - 9 slots listed row by row, `<` `>` cycle through candidate modules
  - Top bar shows **live**: speed / mass / power margin / cooling / heat capacity
  - Assembly failure gives a player-readable reason (e.g. "Power overload: need 68, cap 60")
- **Constraints really take effect**: mount a module → mass↑ speed↓, power draw eats recovery, cooling/heat capacity affect shooting cadence
- Left/right arm and thruster slots are treated as the same kind and modules are interchangeable (the art setting is "standard mount interface")

### 3. Sound System (Procedurally Generated, Zero External Assets)

`tools/make_sfx.py` uses oscillators + noise + envelopes to synthesize 8 sounds (shoot / enemy shoot / hit /
part destroy / dash / overheat alarm / pickup / UI), with 3D falloff and random pitch jitter.

### 4. Mission Objective and Results Loop

- Objective: **clear the area** (live remaining-enemy count top right, changes to "Area cleared" when empty)
- All dead → **mission complete** results (time / salvage recovered / kills), Enter to redeploy
- Player disabled → failure results

### 5. Others

- **Camera pitch restored**: can aim up and down again (previously the view was locked horizontal, couldn't shoot legs/core)
- **HUD combat feedback**: hit markers (corner brackets, turn red on kill), red flash when hit,
  low-power warning, crosshair with outline + hit color change
- **Enemies**: shooting adds 2.4° spread (previously a no-spread laser cannon), fired from the weapon arm;
  skeletons of all 6 enemy types got foot bones added (hovering types' "legs" are thrusters, no feet by design)
- **Build toolchain**: full-chain manual build script (Core→Combat→Game + import library generation),
  freeing us from the broken UBA

---

## III. Validation Evidence (2026-10-14 In-Game)

| Item | Result |
|---|---|
| Auto-battle | 72 hits / all 5 enemies killed / results display correct |
| Overheat cadence | burst ~4.6s → lock 2s → reset, 8 consecutive cycles with no deadlock |
| Modding bench | open → mount heavy head → mount scout head → close; panel values change live (speed 232→172→…) |
| Drops and pickups | part destruction produces salvage (confirmed in log); pickup logic pending walk-over verification |
| Picture | mean brightness 0.34, 2% overexposed pixels (cinematic range); materials/specular normal |

---

## IV. Next Steps

1. **Playtest feedback** (most important): open `ue/启动游戏.bat` and just play.
   Key things to feel:
   - Is the overheat "burst—pause" cadence comfortable? (light mech is about 4.4s per cycle now)
   - Does the trade-off of shooting parts vs. core work (dismantle limbs for more salvage but take damage longer)?
   - Are the three mechs' weapon feels different enough?
   - Do the trade-offs in the modding bench (M key) feel meaningful?
2. Known points that can be polished further:
   - Weapon-arm modules (cannon arm/mining arm) currently only affect the three constraints, they don't actually rewrite weapon stats yet
   - Enemy AI is still the simple "approach—fire" behavior, could add cover/movement
   - Player failure path (mech disabled → results) logic is wired but hasn't been run in-game yet
   - Sound effects are wired but need a real listening test to confirm volume balance
