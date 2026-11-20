> Language: **English** | [简体中文](./迭代报告_2026-10-23.md)
# Iteration Report · 2026-10-23

Goal for this round: **rework the enemy mechs + refine the scene (including using engine-bundled assets)**.

---

## I. Enemies: From "Boxes Bolted Together" to "Shell + Armor Facets"

### Problem

All 6 enemy types (patrol / transport / colossus / gardener / weather / guard) were assembled from `R.box`.
No matter how many bevels were added, the silhouette stayed straight segments + right angles — from a distance, a stack of cardboard boxes.
The player mech was switched to the curved-surface language last round, so the enemy and player art languages were completely split.

### Approach: Three Rules

1. **The main body silhouette must be curved** (ellipsoid / cylinder / rounded prism). Right angles are only allowed where an
   "armor plate" should genuinely be a plate, and with ≥3 bevel segments.
2. **Every joint = ball-and-socket + copper ring**. The ball is the axle, the ring is the seal — the universal grammar of mechanical parts.
3. **Every enemy type must have a recognizable silhouette feature** (see table below).

| Enemy | Silhouette feature | Main curved parts |
|---|---|---|
| Patrol mech | Hovering sphere + one large light ring + pods hanging from the ring | Perfect sphere shell, ring of radius 1.5R, three flared thrusters |
| Hauler | Horizontal cargo cylinder + three reinforcement rings | Capsule along Y, curved windshield, bent-pipe crane arm |
| Repair colossus | Dome chest + two giant arms hanging below the knees | Ellipsoid chest, three reactor rings, conical welding torch |
| Gardener | Apron hanging to the knees + round hat | Curved apron shell, brim disc, bent-pipe spout |
| Weather mech | Radar dome bigger than its head | Hemisphere bowl (cut 45%), three-cup anemometer |
| Heavy guard | Double-dome shoulder armor + shield wide on top narrow on bottom | Half-dome shoulder armor, shield prism + pointed bottom + shield boss |

Triangles: old ~8k (boxes) → new 12k–34k (LOD0 with three LODs).

### Three Geometry Pitfalls Fixed Along the Way

1. **Thin rods eaten by bevels**: `cyl(radius=0.009, bev=0.002)` has a bevel too large relative to the radius,
   so the whole rod was swallowed in `_finish` — the patrol mech lost 0.4m of height. Thickened to 0.014.
2. **The prism bevel cap**: `w = min(bev, min(size)*0.24)`; with a 9.5cm shield thickness
   the bevel cap is only 2.3cm, so it still looks like a knife-edge right angle. Increasing the thickness to 20cm gives a real round edge.
3. **Discontinuous UV**: `auto_rig` originally used Smart UV (auto-split islands per face),
   so adjacent faces had random UV directions — the procedural panel-seam texture tore on sampling.
   Changed to **world-aligned cubic projection** consistent with the player mech (`cube_uv`, 1 UV = 1.2m).

### New Tool: In-Engine Review Mode

`-ReviewEnemies`: lines up the 5 enemies on the field, freezes AI, hides the player,
fixes the camera, and supplies three-point lighting + turns the sun into a front light.

Why it was necessary: the editor viewport has no post-processing and doesn't represent the game lighting;
and the player's viewpoint (2m high, near the ground, behind the mech) can never show the whole mech.

⚠️ Review mode rotates the sun, so exposure needs a separate step down:
`-ReviewEnemies -Bias=2.6` (normal gameplay is 6.0).

---

## II. Scene: Not Missing Assets, Missing Placement

### Core Discovery

Of the 184 Actors in the level, 150 are floor panels / walls / catwalks / pillars,
**not a single prop was placed**. Yet `/Game/RobotGame/Art/Props` already had
10 kinds of props (containers, shelves, oil drums, scrap, supply crates, pipes, rescue pods, terminals…)
done — modeled through imported, all complete, just never put into the level.

`place_props.py` generates a "scrap yard": 12 zones, each with a prop type + density,
grid + fixed-seed jitter (±22cm, random orientation, ±8% scale), containers can stack two high.
**Avoids the player's main path** (nothing placed where |y| < 600). 54 props in total.

### Engine-Bundled Asset: Starfield

`/Engine/EngineSky/T_Sky_Stars` wired directly into `M_SkyDome`:
the XZ projection of the direction vector as UV (horizontal wrap), falling off by `dir.Z^1.6` —
no stars near the horizon automatically (the real night sky is the same, extinguished by the atmosphere).

This was the only place this round that truly "used an engine-bundled asset", and the most direct payoff:
a pure gradient sky in a night scene is "a piece of cloth"; adding a layer of stars immediately gives depth.

### Distant Towers: Modeled, Placement Not Converged

`build_backdrop.py` made three off-field silhouettes (chimney tower 34m / truss tower 26m / tank farm 17m),
but three placement attempts were all wrong:
- At 3000cm → the towers were bigger than the player and blocked half the screen
- At 7000cm → the tower feet floated (no ground outside the walls)
- After adding 280m of outer ground → the towers "lay" on top of the walls, proportions still wrong

**All deleted, the field stays clean.** The modeled assets remain in `assets/out/SM_BG_*.fbx`;
next round redesigns the placement (the key is to work out the relationship between "ground + horizon + tower height" first).

---

## III. Lighting: The Biggest Pitfall of This Round

### Symptom

The picture jumped back and forth between "white out" and "pitch black"; changing any parameter was like rolling dice.

### Root Cause: Two Lighting Code Paths Fighting

| Path | Trigger | Exposure source |
|---|---|---|
| **Formal lighting** (actually in effect) | Level sun ≥ 1000 lux | PPV manual bias, default at `RobotCharacter.cpp:1315` |
| Firefighting path | Sun < 1000 lux | Another bias, in the latter half of `FixLevelLighting` |

I kept changing the value in the **firefighting path** (`SunLux`, `bias -3.0`), while what was actually in effect was
`TargetBias` in the formal lighting path. That's the whole reason for "changed it, nothing happened".

### Final Calibration

```
Sun 22000 lux · sky light 3.2 · point lights 2600cd/1700cm
Fog 0.0055 (inscatter 0.022/0.030/0.046)
PPV: manual exposure bias = 6.0
```

Also reset three early color-compensation groups (`ColorGainShadows` bluish,
`ColorGainHighlights` warm, `ColorSaturation 0.88`) all to neutral —
they were patches from the "gray and orange" period, and now that lighting is fixed they were pushing the picture magenta.

### The Real Source of the Redness

**The sun glow color of the sky dome** `GLOW_COLOR = (0.45, 0.36, 0.28)`.
It was captured by the sky light in real time as ambient light, warming the floor, walls and mechs.
After changing it to `(0.10, 0.12, 0.16)` the picture immediately returned to a cool night scene.

This pitfall is worth remembering: **any color on the sky dome becomes ambient light for the whole scene**,
it isn't a "background image" — it's one of the scene's main light sources.

### New Debug Parameters

| Parameter | Purpose |
|---|---|
| `-ScenicCam` | High angled top-down view, to see the layout of the whole field |
| `-ReviewEnemies` | Enemy review (line up + freeze + fixed camera + review lights) |
| `-Bias=<value>` | Override PPV exposure (for light sweeps) |

---

## IV. Remaining Issues (Next Round)

1. **Distant tower placement**: assets ready, need to redesign the "ground/horizon/tower height" relationship
2. **Review mode exposure**: after rotating the sun, need a separate 3.4-stop reduction, currently passed by command line
3. **Props still too few**: 54 spread over a 3000㎡ field still look sparse from the player's viewpoint
4. **Floor detail**: panel-seam texture contrast is still flat (mean close to 246/255)
5. **Enemy animation**: the new models are rigged (10 bones) but have no dedicated idle/movement animations yet
