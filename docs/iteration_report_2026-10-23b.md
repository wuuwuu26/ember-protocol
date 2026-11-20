> Language: **English** | [简体中文](./迭代报告_2026-10-23b_高级建模.md)
# Iteration Report · 2026-10-23 (Second Round): Introducing Advanced Modeling Operations

Goal for this round: **stop assembling geometry primitives, switch to modeling operations such as lofting to make continuous curved surfaces**.

---

## I. Why "Assembly" Ends Here

After the previous rounds replaced boxes with cylinders, ellipsoids and toruses, the mechs really were no longer "a stack of cardboard boxes",
but there was still a lingering **"assembled parts" feel**. The reason wasn't insufficient beveling, it was structural:

Every primitive (box / cyl / ellipsoid) is a **closed, uniform, unchanging** form.
Assembling a chest out of them can only give three segments "box + sphere + cone", and between segments there must be seams
and a sudden change in curvature. In real industrial design, the chest goes from a square section at the waist, through a pinched waist and outward flare,
to a rounded trapezoid at the breast — it's **one continuous loft curve** — it isn't "several parts" at all.

So what this round added was a **modeling method**, not more primitives.

---

## II. Six New Operations (`robotlib.py`)

| Function | What it does | Key point |
|---|---|---|
| `loft` | Multi-section loft | Sections are parameterized as **superellipses**: `n=2` ellipse → `n=3.5` rounded trapezoid → `n=6` near-square. Give each layer a different `n` and the form transitions smoothly from tube-like to armor block. Section centers can be offset arbitrarily → can make **curved** shells. |
| `lathe` | Surface of revolution | A profile line `[(r,z)]` rotated once around the axis, collapsing to a pole where `r=0`. Nozzles, hubs, ball-joint covers — any rotationally symmetric part — are correctly made only this way. |
| `sweep` | Sweep along a path | The section can be any polygon (square edge strip, flat elliptical armor strip), using **parallel transport** for the frame so the section doesn't suddenly flip at sharp turns. |
| `subdivide` | Catmull-Clark subdivision | Low-poly loft + one subdivision = continuous curved surface, still face-efficient. |
| `shell` | Shell extraction | Curved surface + thickness = armor plate. The edges naturally form real plate thickness. |
| `boolean_cut` | Boolean difference | Cooling vents, access hatches, visor slots — must be genuinely recessed. |
| `bend` | Bend deformation | Adds curvature to an otherwise straight part. |

The core is **`_superellipse`**: the parameterization of `|x/a|^n + |y/b|^n = 1`.
A single exponent controls the continuous transition "from circle to square" — the key that lets lofting produce modern industrial forms.

---

## III. Player Mech: 8 Parts Switched to Lofts

| Part | Before | Now |
|---|---|---|
| Chest | Inner frame + abdomen + chest, three prisms | **One loft**: waist (n=5.5 near-square) → pinched waist → chest flare (n=2.7 ellipse) → shoulder closure, 7 sections |
| Breastplate (L/R) | 7cm thick flat plate | **Lofted shell**: bulging in the middle, tapering top and bottom, continuous light/dark gradient on the same armor piece |
| Skull | Rounded box + ellipsoid on top | **One loft**: narrow jaw → widest at cheekbones → tapering crown, 6 sections |
| Visor | A black flat plate stuck on | **Boolean-cut slot** + eyepiece embedded at the slot bottom (slot walls catch the highlight) |
| Shoulder armor | Ellipsoid dome | **Lofted shell shape**: different vertical and horizontal curvature (impossible with an ellipsoid) |
| Thigh | Constant-radius cylinder | **Loft**: hip ellipse (n=2.2) → knee rounded square (n=3.4), radius decreasing |
| Shin | Constant-radius cylinder | **Loft**, section center offset backward (the shin bone is naturally curved) |
| Knee pad | Slanted flat plate | **Lofted arc guard** (the knee is the highest-curvature spot on the leg; a flat plate must lift at the edges) |
| Foot | Heel prism + sole box + toe ellipsoid | **One lofted boot shape**: narrow heel → wide sole → tapering toe |
| Skirt armor | Two prisms | **Lofted curved surface** (hugs the pelvis on top, flares at the bottom) |
| Abdomen cooling vents | A row of thin plates stuck on | **Three real slots boolean-cut** |

Triangles: 48.9k → 46.9k (LOD0, medium). **The face count even went down a bit**, because lofted parts replaced
the three-piece set of "main body + attached plate + seam cover".

---

## IV. Pitfall Hit

**The `loc` parameter of `loft` was left unassigned.** The signature was updated when the parameter was added, but the function body wasn't,
so `loc=` was accepted but ignored — all parts using it (the feet) stayed at the world origin,
and in the preview it looked like "the feet fell off the legs and are lying on the ground".

Lesson: **adding a parameter requires changing both the signature and the function body**, and there must be a call site using that parameter to verify
(the foot was the only place using `loc`, so only it broke).

---

## V. Still Not Done

1. **Arms are still cylinder + ellipsoid**. They're under the shoulder armor and low visual weight, but this round didn't touch them.
   Arms should be lofted for a "thick upper arm → pinched elbow → square forearm" transition.
2. **The 6 enemies haven't been lofted yet**. Last round they were just switched from boxes to curved primitives,
   but that's still "primitive assembly" — the next step is to apply the same lofting language to them.
3. **`subdivide` / `shell` were only verified to work, not actually used**.
   A curved surface + shell extraction would give armor plates real thickness and inner wall at the edges — worth a dedicated round.
4. In-engine close-up screenshots are still overexposed (scene exposure is dialed in for a full-body composition;
   in close-ups the hero fill + the sun stack and blow out) — that's a problem with the review/close-up tooling, it doesn't affect normal gameplay.
