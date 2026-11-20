> Language: **English** | [简体中文](./README.md)
# Blender Procedural Modeling Pipeline

Generate mech models headlessly with Blender's Python API, outputting assets that UE5 can import directly.

## Quick Start

```bash
# Generate a single chassis variant (with preview render)
"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background \
  --python build_robot.py -- --chassis medium --out ../../assets/out

# Batch-generate all three chassis variants
... --chassis all

# Skip rendering, model only (much faster for batch iteration)
... --chassis all --no-render
```

Verified environment: **Blender 5.2.2 LTS** (built 2026-09-15), about 6 seconds per chassis including render.

## Output

| File | Purpose |
|---|---|
| `robot_<variant>.blend` | Blender project, for artists to take over and modify |
| `robot_<variant>.fbx` | **For UE5 import**, units converted to centimeters by a factor of 100 |
| `robot_<variant>.glb` | General exchange format, for other toolchains |
| `preview_robot_<variant>.png` | 1280×1280 preview render |

## Three Chassis Variants

| Variant | Height | Width | Cooling fins | Design correspondence |
|---|---|---|---|---|
| Light scout | 2.50 m | 1.25 m | 5 (large) | Narrow, thin, best cooling |
| Medium general | 2.46 m | 1.47 m | 3 | Balanced |
| Heavy assault | 2.37 m | 1.86 m | 2 (small) | Wide, thick, heaviest armor |

**The geometry itself carries the design constraints** — the light mech is narrow with many fins, the heavy mech is wide with few.
This isn't decoration: it lets the player read at a glance in the modding UI "does this machine run fast or take a beating".

## Naming Conventions (Consistent with Production Plan Appendix A)

**Part objects** (after import into UE correspond to independently destructible parts):

```
chassis_torso / chassis_pelvis / chassis_head      mech frame
part_core                                          core (destructible, emissive)
part_shoulder_L / _R                               shoulder armor
part_upperarm_L / _R                               upper arm
part_forearm_L / _R                                forearm
part_muzzle_L / _R                                 weapon muzzle
part_thruster_L / _R                               thruster
part_foot_L / _R                                   foot
part_backpack                                      backpack
part_hip_L / _R / part_knee_L / _R / part_ankle_L / _R   joints
part_fin_L_01 …                                    cooling fins
```

**Socket empty objects** (after import into UE serve as socket positioning references):

```
socket_head      socket_arm_L      socket_arm_R
socket_back      socket_aux_01     socket_aux_02
socket_core      socket_root
```

## Coordinate and Unit Conventions

- In Blender, **−Y is the mech's front, the Z axis points up** (Blender's standard front-view convention)
- FBX export `global_scale=100`, converting Blender's meters to UE's centimeters
- Expected result: on UE import, **Uniform Scale stays 1.0** and the mech height is about 2.4–2.5 meters

> ⚠️ **The first UE import must verify two things**: ① does the mech face +X forward; ② is the height 2.4–2.5 meters. If not, adjust the import settings or change `axis_forward` / `global_scale` on the Blender side. This step must be working before the formal asset pipeline is set up.

## Script Structure

| Function | Responsibility |
|---|---|
| `variant_params(v)` | Variant parameter table (size, color scheme, fin count) — **change numbers here** |
| `make_material(...)` | Create Principled BSDF materials, with version compatibility for slot names |
| `add_box / add_cyl` | Beveled primitives, bevels are the key to the hard-surface mechanical feel |
| `add_socket(...)` | Create socket empty objects |
| `build_robot(P, mats)` | Assemble the mech, returns (part list, socket list) |
| `world_bounds(objs)` | World-space bounding box, for checking size |
| `setup_render(...)` | Camera, three-point lighting, color management |
| `export_fbx / export_glb` | Export, with parameters filtered by the fields actually supported by RNA |

## Current Limitations (Honest List)

This version is at the **blockout level (placeholder models)**, not finished assets:

| Missing | Impact | How to fill |
|---|---|---|
| **No UV unwrapping** | Can't apply textures, only material slots | The script can do Smart UV Project, but seams need artistic adjustment |
| **No rigging** | Can't be animated, imports into UE as static meshes | Need to add an Armature + vertex weights, or use UE skeletal retargeting |
| **No LOD** | High-poly goes straight into the game, over budget | The script can generate Decimated LOD1–3 |
| **No collision** | Needs to be generated manually on the UE side | UE's automatic Physics Asset generation is good enough |
| **Topology is assembled primitives** | High face count, irregular edge flow, not suitable for deformation | Would need retopology for deformation animation |

## Possible Next Steps

By priority:

1. **Add UV + LOD** (the script can do 80%, the remaining seams need manual work)
2. **Add skeletal rigging** (the key step to making the models truly usable)
3. **Hook `variant_params` up to Excel/CSV** so designers can change a sheet to produce new variants
4. **Build a part module library**: 3–5 variants each for arms, backpacks, thrusters, sharing the same sockets, mapping directly to the game's 40 modules
