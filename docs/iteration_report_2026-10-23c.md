> Language: **English** | [简体中文](./迭代报告_2026-10-23c_缺陷修复.md)
# Iteration Report · 2026-10-23 (Third Round): Defect Investigation and Fixes

Goal for this round: **self-inspect the problems left over from last round's lofting refactor**, no new features.

---

## 1. Inspection Method

Last round we only looked at a **single 3/4-view** preview image, and ended up missing half the problems. This round we added two tools:

| Tool | Purpose |
|---|---|
| `inspect_chassis.py` | Render one image each of the same mech from 6 angles: front / side / back / 3/4 / bottom-up / top-down |
| `probe_parts.py` | Print each part's bounding box (dX / dY / dZ / Z range), sorted by a given dimension |

The second tool was the key. In side view there was a "turtle shell covering the upper body"; we changed the pauldron parameters three times and it didn't change —
because that wasn't the pauldron at all, it was the **old ellipsoid shell `pauldron_shell` that we forgot to delete**.
Sorting the bounding boxes by dY put it first (0.45 > the lofted bowl's 0.40), obvious at a glance.

---

## 2. The 7 Problems Fixed

### 1. The knees were broken (most severe)

The thigh loft's lower end stopped at `knee_z + 0.03`, the shin's upper end started at `knee_z - 0.03` —
there was a **6cm gap** in between, making the knee look like "two sticks stuck end to end".

> Fix: push the thigh's lower end down to `knee_z - 0.03`, raise the shin's upper end to `knee_z + 0.04`, so the two overlap.

### 2. The ankles were broken too

The foot (lofted boot shape) had its top at `zFT + 0.10`, the ankle joint ball was at `zFT + 0.22` — a gap in between.

> Fix: raise the foot to `zFT + 0.16`, extend the shin's lower end down to `ankle_z - 0.06`.

### 3. The pauldrons didn't cover the shoulder joints

Originally the span was only `xS ± 0.4·SW` (about 0.39 ~ 0.60), while **the upper arm is at x = 0.68**.
So the pauldrons looked like "two balls stuck to the sides of the chest", with the arms growing out of thin air from outside the pauldrons.

> Fix: change the span to run from the edge of the chest cavity all the way to the outside of the upper arm (`xS - 0.46·SW` ~ `xS + 1.34·SW`).

### 4. The pauldron was first made into a flat wing, then into a turtle shell

**Flat wing**: the loft's Z axis is the stacking direction; in my first version I placed all 5 cross-sections at the same height,
so it spread out 0.5m horizontally but was only 5cm tall — a "bat wing".
→ Changed to an inverted bowl running along Z from "bowl rim → bowl top".

**Turtle shell**: the bowl's Y radius was set to `SD * 0.78` (front-to-back diameter 0.56 > chest depth 0.44),
so in side view the entire upper body was covered by a semicircular dome.
→ Reduced to `SD * 0.42` (diameter 0.30) and moved outward overall.

### 5. The old ellipsoid shell wasn't deleted (the real culprit behind "changes had no effect")

`pauldron_shell` was still in the code, dY=0.45, Z 1.98~2.14, sitting right on top of the lofted bowl.
We changed the pauldron parameters three times with no change on screen, precisely because this thing was blocking it from outside.

> Fix: delete it. The lofted bowl already has the "rim → top" layering, no need to stack another shell.

### 6. The collar ring was a hat brim

`torso_collar` radius `0.30 · TW` = 0.19m, twice as thick as the neck —
in side view it was a ring of brim sticking out horizontally below the head, and together with the pauldrons created the illusion of a "turtle shell".

> Fix: reduce to `0.17 · TW`.

### 7. The left hand was three square bars, like a fork

`claw_*` were 5×22×5cm straight rectangular bars, three of them jutting out at an angle.

> Fix: change to **lofted tapered fingers** (thick at the root, thin at the tip, converging to a point) + ball joints at the finger roots.

---

## 3. Before and After

| | Before | After |
|---|---|---|
| Knees | 6cm gap | overlapping, continuous |
| Ankles | gap | enclosing the ankle joint |
| Pauldron span | 0.39~0.60 (couldn't reach the arm) | 0.35~0.86 (covering the shoulder joint) |
| Pauldron side view | semicircle covering the upper body | front-to-back 0.30 < chest 0.44 |
| Collar | diameter 0.44 (hat brim) | diameter 0.25 |
| Left hand | three square bars | three tapered fingers + ball joints |

Triangle count: 46.7k → 46.8k (essentially unchanged).

---

## 4. Still Unresolved

1. **There is still a thin gap between the arms and the pauldrons**. To avoid turning into a turtle shell, the pauldron's Y radius was reduced to 0.30,
   while the arm root's Y span is 0.28 — only 1cm of wrapping margin remains, so black gaps show at some angles.
   The proper fix is to add an "inward-folded lower lip" skirt to the pauldron (fold the last loft layer outward), but that wasn't done this round.
2. **The backpack sits too low**, with a visible gap between it and the back of the chest cavity.
3. **Overexposure in close-up inside the engine**: material albedo 0.30 + sun 22000lux, the mech blows out white in close-up.
   This is a material/lighting problem, not a model problem; need to lower albedo on the material side or reduce exposure separately for close-ups.
4. **The legs are too thin and long**: thigh/shin radii are small relative to the torso, proportionally like "bamboo-pole legs".
   This is a design choice, not a bug, but doesn't quite match the "heavy mech" setting.

---

## 5. New Reusable Debug Scripts

```
tools/blender/inspect_chassis.py   # six-angle inspection render
tools/blender/probe_parts.py       # part bounding-box probe (locating "invisible large objects")
```

These should be run after every model change from now on — looking at just one 3/4 view misses far too much.
