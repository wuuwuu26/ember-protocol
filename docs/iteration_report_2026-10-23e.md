> Language: **English** | [简体中文](./迭代报告_2026-10-23e_全场景4K.md)
# Iteration Report · 2026-10-23 (Fifth Round): Full-Scene 4K Textures

Goal for this round: generate 4K textures ourselves, **every object must have them**.

---

## I. First Scan: How Many Objects Actually Lack Textures

```
M_SteelLight     211 uses    M_Accent_prop     60 uses
M_Steel          185 uses    M_Rust            34 uses
M_Copper         184 uses    M_Accent_wall     34 uses
M_Joint          175 uses    M_Core_prop       20 uses
                            M_AccentDark_prop  7 uses
                            BasicShapeMaterial 5 uses  <- engine default material
```

Conclusion: **there are no empty slots** (every object has a material), but **5 use the engine default
`BasicShapeMaterial`** — that gray checker image, instantly recognizable as "no texture".

And the more fundamental problem: **only 2 of the 12 materials had real textures bound**
(mech used T_MechDetail, environment used T_EnvDetail). That means the floor, walls, pillars,
containers and scrap piles **all used the same image**, up close it looked like "the same wallpaper pasted everywhere".

---

## II. Generating 5 Sets of 4K Textures

Added `tools/make_surface_set.py`, which parameterizes the generation of different surfaces. It reuses
`make_detail_texture`'s fbm / seam_grid / smoothstep / shift_noise, keeping the noise language consistent.

| Texture | Purpose | Features | Panel mean | Roughness mean |
|---|---|---|---|---|
| `mech` | Mechs, enemies | 3×3 large panels + sub-panels + rivets + sparse scratches | 0.68 | 0.63 |
| `env` | General environment | Denser grid + large mottled patches | — | — |
| `paint` | Walls, containers, painted shells | 2×2 large panels, flat face, **paint-chipping spots** | 0.84 | 0.62 |
| `concrete` | Floor, bases | 4×4 fine grid, coarse grain, almost no wear | 0.67 | 0.88 |
| `rust` | Scrap, pipes, old structures | 3×3 panels + **lots of rust spots and flaking** | 0.48 | 0.92 |

Each set outputs:
- `<name>_detail.png` (4K RGBA: R=panel mask / G=roughness / B=wear / A=height)
- `<name>_detail_n.png` (4K normal, from wrap-around differences of the height map)

10 textures in total at 4096×4096, 4.5–5.7MB each.

**The key of parameterization**: every "per-pixel" parameter is multiplied by `S = SIZE/1024`.
At 4K the seam width must go from 16px to 64px, otherwise at the 1.2m UV scale it's only 4.7mm and disappears at a distance.

---

## III. Assigning by Material Type

A mapping table was added in `make_surface_materials.py`:

```python
M_Steel      -> concrete (mainly floor/base)
M_SteelLight -> painted steel plate (structural parts)
M_Joint      -> rust
M_Copper     -> rust
M_Rust       -> rust
M_Accent*    -> paint
M_Core       -> paint (emissive parts have DetailAmount=0, texture not involved)
Characters/* -> mech texture
```

Long names match first (`M_AccentDark` must not be grabbed by `M_Accent` first).

Also used `fix_default_mat.py` to replace the 5 `BasicShapeMaterial` uses with project materials
(low, large-area ones use concrete steel for floor, the rest use painted steel).

---

## IV. Found the Real Cause of "Dark Mechs"

After changing the textures the mechs were still black — but the floor was very bright, and the floor's albedo (0.105)
is **lower** than the mech's (0.30). That doesn't make sense unless something's wrong with the material model.

It turned out to be **metallic**:

```
M_SteelLight  metallic 0.42
M_Steel       metallic 0.30
```

A painted armor plate is essentially "paint", so metallic should be near 0.1. At 0.3–0.42,
the material relies almost entirely on **reflecting the environment** — and this scene is a night scene with a dark sky,
so the mech is always black and the texture detail is completely invisible.

> After changing to 0.10 / 0.16 the mech immediately brightened, and panel seams and rivets could be seen clearly.

This explains "why the texture still isn't visible after changing the texture" — **half the reason is a broken texture (32×32),
the other half is that the material never gives diffuse reflection a chance**.

---

## V. Validation

| Check | Result |
|---|---|
| Texture size | All 10 are `4096×4096` |
| Streaming | All `never_stream=True` (avoids loading only low mips) |
| Material bindings | Characters→Mech / Env.M_Steel→Concrete / Env.M_Joint→Rust (confirmed in logs) |
| Default materials | All 5 replaced |
| Close-up | Mech breastplate/leg panel seams and rivets clear; floor tile seams sharp |
| Game view | Floor's large grid + sub-panels + rivet dots all visible |

---

## VI. Remaining

1. **The picture is overall too orange**. The textures are fine now, but the tone is pulled orange-red by the fog and low-angle warm light.
   Next step should be a dedicated tuning round: the fog's directional inscattering color,
   the sun's color temperature (5200K is low, try 6500K), and the PPV's ColorGain.
2. The `env` texture set's seam width parameters are still from the 1024-baseline era and haven't been rechecked at 4K
   (it now overlaps somewhat with concrete, could be merged next round).
3. Emissive parts (M_Core) have no dedicated texture — currently `DetailAmount=0` skips it entirely,
   which is right for light strips, but if we want "emissive panels with internal patterns" later, one needs to be added.
