> Language: **English** | [简体中文](./README.md)
# Ember Protocol · UE5 Project Skeleton

The missing link between "having assets" and "having a game". This is a **compilable C++ skeleton**, not a complete game —
it turns the architecture decisions in sections 2 and 3 of the production plan into code.

---

## Directory

```
ue/
├─ RobotGame.uproject           Engine 5.8, enables GAS / EnhancedInput / StateTree / Mutable
├─ Config/
│  ├─ DefaultGameplayTags.ini   Registry of all GameplayTags
│  └─ DefaultEngine.ini         Rendering / physics / packaging config
└─ Source/
   ├─ RobotGame.Target.cs
   ├─ RobotGameEditor.Target.cs
   ├─ RobotCore/                Base types, data assets (depends on no other game module)
   ├─ RobotCombat/             GAS, damage routing, part system
   └─ RobotGame/                Characters, assembly, input
```

## Dependency Direction of the Three Modules

```
RobotCore  <- depends on no game module
   ^
RobotCombat  ->  RobotCore
   ^
RobotGame    ->  RobotCore + RobotCombat
```

**Hard rule: dependencies only go one way.** When adding `RobotUI` later, it is not allowed to `#include` `RobotCombat`
headers — UI gets data through interfaces or events. This rule prevents UI and gameplay from becoming hopelessly entangled and unrefactorable later.

---

## Core Classes

| Class | Module | Responsibility |
|---|---|---|
| `URobotChassisData` | Core | Mech config: three constraints + slot definitions. **The single source of truth for all tunable values** |
| `URobotModuleData` | Core | Module config: effects on the three constraints, unlock cost, granted abilities |
| `FPartHealth` / `FPartBoneRule` | Core | Data structures for part HP and bone mapping rules |
| `RobotTags` | Core | The single entry point for GameplayTag values, eliminating hard-coded strings |
| `UPartMapData` | Combat | Mapping table: bone name → part tag |
| `UPartDamageComponent` | Combat | **The game's core combat mechanic**: part HP, dismantling, disable state |
| `URobotAttributeSet` | Combat | Power / heat attributes. Heat is a reverse resource that "only rises, never falls" |
| `UAssemblyComponent` | Game | Mech assembly: constraint aggregation + hard power validation + write into GAS |
| `ARobotCharacter` | Game | Player mech, integrating ASC / parts / assembly |

---

## Three Design Decisions Worth Calling Out

### 1. Part HP Does Not Go Into the GAS AttributeSet

The number of parts is dynamic (different enemies have different part counts), while an AttributeSet suits fixed attributes.
`UPartDamageComponent` uses a standalone component to manage `TMap<FGameplayTag, FPartHealth>`,
and GAS is only responsible for delivering damage in via GameplayEffects.

**Benefit**: one component serves the player and all 6 enemy types, just configure a different `UPartMapData`.

### 2. "Fake Dismantling" Instead of Chaos Per-Piece Shattering

`HandlePartDestruction()` hides the bone with `HideBoneByName`,
then the game layer spawns a pre-made part mesh based on the `OnPartDestroyed` event.

**Why**: Chaos per-piece shattering has unpredictable performance with dozens of enemies on screen, and the fragments can't reliably
serve as pickups. Chaos is reserved for scripted set-pieces in the colossus level.

### 3. Power Is a Hard Constraint, Mass Is a Soft Constraint

`CanMount()` performs a **hard check** on power (overload is rejected outright, with a player-facing reason),
while mass is naturally punished through `Speed = BaseWalkSpeed / Mass`.

**Why the asymmetry**: power overload would put the ability system into an undefined state (consumption exceeding the cap) and must be blocked;
excess mass just makes you slower, and the player can weigh that themselves. Two constraints, two mechanisms — more reasonable than universally hard-blocking or universally soft-hinting.

---

## Data Validation Is Already in the Code

`URobotChassisData::IsDataValid()` and `URobotModuleData::IsDataValid()` run in the editor's asset validation to check:

- Whether the mech's three constraints are complete, and whether slot names are empty/duplicated
- **Whether a module "only adds numbers"** — per design pillar P1, a module that grants no ability, no movement capability,
  and changes neither cooling nor power is flagged with a warning

The last item writes a design principle into code. People forget principles when rushing; the compiler doesn't.

---

## Before You Compile

This skeleton **has not yet been compile-verified** (UE and Visual Studio are not installed on this machine). To run it you need to:

1. Install **UE 5.8** + **Visual Studio 2022** (with the "Game development with C++" workload)
2. Right-click `RobotGame.uproject` → **Generate Visual Studio project files**
3. Compile. The first build will have things to fix; check in particular:
   - The signature of `IsDataValid()` (changed from `TArray<FText>&` to `FDataValidationContext&` around UE 5.4)
   - `GetSkeletalMeshAsset()` only replaced `SkeletalMesh` after 5.1
   - Whether `SetReplicationMode` is necessary in a single-player project
4. Create the `Content/RobotGame/` directory structure (see production plan 2.1),
   and import `assets/out/*.fbx` into `Content/RobotGame/Art/Characters/`

### Two Things That Must Be Verified When Importing Assets

- **Orientation**: does the mech face +X forward
- **Size**: is the mech height 2.4–2.6 meters (the FBX `global_scale=100` conversion has not been verified on a real machine)

If not, change `global_scale` / `axis_forward` in `export_fbx()` in `tools/blender/robotlib.py`, or adjust Uniform Scale in the UE import settings.

---

## Next Steps

| Priority | Task | Notes |
|---|---|---|
| 1 | **Get a clean compile** | The skeleton must compile before anything else |
| 2 | Import 3 mechs + verify orientation and size | Open up the asset pipeline |
| 3 | Implement `GA_Dash` (dash ability) | First GAS ability, validates the power-consumption chain |
| 4 | Implement heat lock | Complete the heat lever loop |
| 5 | Modding UI (Common UI + MVVM) | Carries pillar P1, must be done early |
| 6 | Enemy AI (StateTree) | Reuse `UPartDamageComponent` |
| 7 | Save system | Checkpoint-style, versioned from day one |
