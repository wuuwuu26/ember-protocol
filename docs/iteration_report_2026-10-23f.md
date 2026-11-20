> Language: **English** | [简体中文](./迭代报告_2026-10-23f_UV修复.md)
# Iteration Report · 2026-10-23 (Sixth Round): UV Normalization Bug

Goal for this round: fix "the mech surface is all covered in a grid".

---

## I. The Real Cause: `cube_project` Normalizes UV to 0~1

After last round switched the textures to 4K, the mech surface instead became a field of fine grid lines. Checking the UV range:

```
UV range  u: 0.000 ~ 1.000    v: 0.000 ~ 1.000
```

The mech is 2.7m tall, but the UV is only 0~1 — meaning **`bpy.ops.uv.cube_project(cube_size=1.2)`
didn't compute UV by world scale at all, it normalized the result** (`scale_to_bounds=False` didn't help either; this operator always projects first then fits to 0~1).

Consequence: one 4K texture was stretched over the whole mech. The 3×3 panel-seam grid in the texture was stretched to
**90cm per panel** — from a distance a flat color ("no texture"), up close coarse grid lines.

This also explains last round's confusion: after switching to 4K it got "worse", because the 1024-era panel seams were already coarse,
and 4K rendered the same grid more sharply.

---

## II. The Fix

### 1. Hand-Written Cubic Projection

Stop using `cube_project`; compute it per face ourselves:

```python
for poly in me.polygons:
    ax = principal axis (axis with the largest absolute normal component)
    for li in poly.loop_indices:
        v = world_matrix @ vertex.co
        u, w = pick two components by the principal axis (X->YZ, Y->XZ, Z->XY)
        uv[li] = (u / size_m, w / size_m)
```

Also **remove the extra UV layers** (after join there were 2 layers, the material used UV0 but its content was stale).

After the fix:
```
UV range  u: -0.707 ~ 0.707    v: -0.392 ~ 2.243
UV layers: 1
```

2.2 texture units in the height direction — that's "texture repeating at real scale".

### 2. UV Scale 1.2m → 3.2m

One 4K per 1.2m repeats 1.4 times across a 1.7m-wide mech, panel seams too dense.
Changing to 3.2m gives about 1280 px/m, panel seam spacing about 1m — comparable to real armor plate size.

### 3. Seam Darkening 0.46 → 0.16

`SeamDarken=0.46` pressed seams to pure black, looking like "grid paper pasted on".
Real armor panel seams are **shadows**, not black lines; 0.16 is just right.

---

## III. Before and After

| | Before | After |
|---|---|---|
| UV range | 0 ~ 1 (normalized) | v: -0.39 ~ 2.24 (by scale) |
| UV layers | 2 (material used the stale one) | 1 |
| Texture scale | one stretched over the whole mech (90cm seams) | one cycle per 3.2m (seams about 1m) |
| Seam darkening | 0.46 (pure black) | 0.16 (shadow) |
| Look | dense mosaic grid | large armor faces + slight color variation |

---

## IV. Validation

- UV values: measured in-script (see table above)
- Close-up: mech surface is continuous armor faces, only subtle color variation and very faint seams,
  no more dense grid
- Scene view: floor keeps its industrial flooring grid (that's by design, not a bug),
  mechs and enemies are clean

---

## V. Remaining

1. **The picture is too orange** (noted in round 3, never resolved). Fog directional scattering + 5200K low-angle
   sun stacked. Next step should be dedicated tuning: fog inscattering color, try 6500K sun color temperature,
   PPV ColorGain.
2. **Cubic projection still has UV breaks on curved surfaces**. With principal-axis projection, faces whose normals switch
   between X/Y/Z have a UV seam. Not noticeable at the current scale (3.2m), but if we later need patterns with clear direction
   (numbers, warning stripes), we must switch to material-side triplanar sampling
   (pure node implementation, not MaterialFunction — that path couldn't be verified).
3. Floor grid seam width is 5cm (64px/4096×3.2m), slightly coarse. Could reduce to 32px.
