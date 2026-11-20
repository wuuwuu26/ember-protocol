> Language: **English** | [简体中文](./余火协议_UE5制作计划.md)
# "Ember Protocol" UE5 Production Plan

> Document version v1.0 | Engine baseline **Unreal Engine 5.8** | Target platform **PC (Windows) single-player**
> All schedules, headcounts and budgets in this plan are **planning models** and must be re-estimated after each milestone acceptance. All unverified values are marked `[PLACEHOLDER]`.

---

## 0. One-Page Overview

### 0.1 Project Baseline (Confirmed)

| Item | Definition |
|---|---|
| Genre | Third-person action-adventure + modular mech customization |
| Platform | PC single-player, keyboard & mouse first, gamepad also supported |
| Target player | Action-exploration players: enjoy customization, exploration and story, accept medium difficulty, not seeking extreme execution |
| Run length | 20–40 minutes to complete one full "prepare → fight → salvage → customize" arc |
| Engine | Unreal Engine 5.8 |
| Business model | Buyout, offline single-player, no microtransactions |

### 0.2 Fun Hypothesis (The Foundation of All Design)

> **The core of what makes this game fun: every time you strip an enemy's body, you are rewriting your own body — and the path you can walk next.**

If you can't state this clearly, don't move forward. The purpose of this sentence is to weld "combat," "customization" and "exploration" into one causal chain, not three parallel systems.

### 0.3 Design Pillars (3; the approval standard for technical decisions)

| # | Pillar | Decision question (cut it if it fails) |
|---|---|---|
| P1 | **Customization changes gameplay, not just numbers** | Does this new mech/module bring a new way to move or a new combat solution? Any module that just adds 5% attack power is cut. |
| P2 | **Dismantling is a costly choice** | Does this salvageable part carry an opportunity cost? (Rescue an ally / keep resources / change route) Salvage without a trade-off is just trash picking. |
| P3 | **One full arc in 20–40 minutes** | Does this mission contain the four beats of preparation, tension, salvage, and customization feedback? If a beat is missing, rework it. |

### 0.4 Timeline Overview

| Phase | Period | One-line goal | Team size (planned) |
|---|---|---|---|
| P0 Pipeline & Pre-research | Month 1–2 | Engine pipeline working, biggest technical risks validated | 6–8 people |
| P1 Core Prototype | Month 3–6 | Prove in gray-box that "changing gear really changes the fighting" | 12–15 people |
| P2 Vertical Slice | Month 7–14 | Build a 20–40 minute quality sample | 20–30 people |
| P3 Mass Production | Month 15–30 | Deliver content by area | 60–100 people |
| P4 Content Lock & Full Clear | Month 31–36 | Full flow playable, systems frozen | 80–100 people |
| P5 Polish & Release | Month 37–42 | Performance, compatibility, certification, launch | 60–80 people |

---

## 1. Engine & Plugin Selection

### 1.1 Why UE 5.8

UE 5.8 was released in June 2026 and is the **last version planned within UE5**, after which Epic moves to UE6. For a 42-month project, this is the most stable choice right now:

- **5.8 is the end of long-term maintenance**: Epic will keep providing bug fixes for UE5, so there's no gap where "the engine stops being supported halfway through the project."
- **Key capabilities are production-ready**: MegaLights (multiple dynamic lights, the core of industrial/neon scenes), Mutable (runtime character assembly), Iris replication, Chaos Cloth, Audio Insights.
- **A UE6 migration window can be reserved**: schedule a 2-month evaluation period in P4, then decide whether to migrate. Don't bet on UE6 now.

**Decisions explicitly NOT made**: don't upgrade the engine major version mid-development. Engine upgrades happen only in the P0 and P4 windows.

### 1.2 Core Plugin Selection Table

| Requirement | Selection | Status | Reason | Risk / Cost |
|---|---|---|---|---|
| Locomotion foundation | **Character Movement Component (CMC)** | Stable | Mover not yet production-ready; CMC has official long-term support commitment | Climbing needs a custom MovementMode; workload moved earlier |
| Locomotion (future) | Mover plugin | Evolving from experimental to stable | Cleaner architecture, better prediction and re-simulation | **Not used now**, re-evaluate at P4; locomotion logic goes through an interface abstraction to reserve migration |
| Mech module assembly | **Mutable** | **Production-ready** | Runtime assembly of modular meshes, automatic LOD, official Epic support | Learning curve; need to write a GameplayTag → parameter bridge layer |
| Abilities & attributes | **Gameplay Ability System (GAS)** | Stable | Power / heat / cooldowns naturally fit AttributeSet + GameplayEffect | Steep learning curve; networking part unused (single-player) can be cut |
| Input | **Enhanced Input** | Stable | Input mapping and context switching, unified gamepad/keyboard & mouse | None |
| Enemy AI | **StateTree** + AI Perception + EQS | Stable | UE5's recommended state-driven AI, better than Behavior Trees for enemies with "phase changes" | Less community material than Behavior Trees; need internal documentation |
| Scene destruction (set-piece) | **Chaos Destruction** | Stable | Used for specific set-piece segments like the colossus level | Expensive, **no full-scene destruction** |
| Environment lighting | **Lumen** + **Lumen Lite** | Lite is beta | Lite is about 2× faster, used for mid/low quality tiers; high tier uses full Lumen | Two quality presets need separate validation |
| Multiple dynamic lights | **MegaLights** | **Production-ready** | The core for many lights in industrial scenes (welding sparks, indicator lights, neon) | Need per-scene light limits |
| Static geometry | **Nanite** | Stable | Detail density of mega-structures in the environment | **Skeletal meshes do not rely on Nanite**, use the standard LOD pipeline |
| Open areas | **World Partition + HLOD** | Stable | Large-area streaming; 5.8 adds World Partition Insights streaming debug | Linear levels don't use it (see 3.7) |
| Environment population | **PCG** | Stable (some experimental nodes — use with care) | Scatter of ruins/debris, vegetation, pipes | Experimental nodes don't enter the production pipeline |
| UI | **Common UI + MVVM** | Stable | The customization UI is core UX and needs maintainable data binding | Need ViewModel conventions defined early |
| Audio | **MetaSounds + Quartz** | Stable | Robotic voice-synthesis feel, engine sound varying with load | None |
| Secondary animation motion | **Control Rig Physics** | Beta | Natural sway of antennas, cables, hydraulic hoses | **Beta, needs a fallback** (fall back to hand-keyed animation) |
| Animation retargeting | **IK Retargeter + RigMapper** | RigMapper is beta | 3 mech classes share animation assets | Main flow uses IK Retargeter; RigMapper is experimental only |
| Cutscenes | **Sequencer + Movie Render Queue** | Stable | Story presentation and marketing assets | Cutscene count must be tightly controlled (see 3.11) |
| Modular gameplay features | **Game Feature Plugins** | Stable | Optional area content, controls package size | Over-engineered for teams under 30; re-evaluate from P3 |

### 1.3 Three Explicit Technical Trade-offs

**Trade-off 1: Don't use Mover, but keep the interface.**
Mover is still officially described in 5.8 as "evolving from an experimental state toward a stable architecture," and isn't marked production-ready. A 42-month project shouldn't bet its locomotion system on an unsettled plugin. The approach: define the `IRobotLocomotion` interface, with CMC as the implementation; climbing, magnetic grip and dashing all go through the interface. When migrating to Mover later, only swap the implementation layer, leaving upper-level gameplay code untouched.

**Trade-off 2: Part dismantling uses "fake dismantling," not Chaos destruction.**
Chaos per-piece shattering has unpredictable performance with dozens of enemies on screen, and the dropped fragments can't reliably serve as recoverable pickups. The approach is in 3.2 — hide the bone + replace with a pre-made part model. Chaos is reserved for scripted set-pieces in the colossus level.

**Trade-off 3: Independent characters for mechs, sockets for modules.**
Don't pursue "free assembly of any parts" — that is an abyss of content cost. Make one complete SkeletalMesh + AnimBP for each of the 3 mech classes (light/medium/heavy); 40 modules attach via bone sockets. Only introduce Mutable when a module needs to change skeleton proportions or merge skins.

---

## 2. Project Architecture

### 2.1 Directory Structure

```
robot_game/
├─ Config/                     Engine & project config, quality presets
├─ Content/
│  └─ RobotGame/
│     ├─ Art/
│     │  ├─ Characters/        Mechs, modules, enemies
│     │  ├─ Environment/       Area modular assets
│     │  ├─ Props/             Interactive props, drops
│     │  ├─ VFX/               Niagara systems
│     │  └─ Materials/         Master materials & instances
│     ├─ Audio/                MetaSounds, Sound Cues
│     ├─ Blueprints/           Content-layer logic only (see 2.3)
│     ├─ Data/
│     │  ├─ Chassis/           Mech data assets
│     │  ├─ Modules/           Module data assets
│     │  ├─ Enemies/           Enemy config tables
│     │  └─ Economy/           Economy & drop config
│     ├─ Maps/
│     │  ├─ Persistent/        Persistent level (main base)
│     │  └─ Regions/           5 areas
│     ├─ UI/                   Common UI widgets & styles
│     └─ Cinematics/           Level Sequences
├─ Source/
│  ├─ RobotGame/               Main game module (Target, GameMode)
│  ├─ RobotCore/               Base types, GameplayTag, data asset definitions
│  ├─ RobotAssembly/           Mech & module assembly
│  ├─ RobotCombat/             GAS abilities, damage routing, part system
│  ├─ RobotAI/                 StateTree tasks, perception, EQS
│  ├─ RobotWorld/              Areas, streaming, mobile base
│  ├─ RobotUI/                 ViewModel & C++ base classes
│  ├─ RobotSave/               Saves & version migration
│  └─ RobotEditor/             Editor-only: data validation, content tools
├─ Plugins/
│  └─ RobotGameplay/           Standalone gameplay plugin (easy to trim per area)
├─ Tools/                      Build scripts, data validation, automated tests
└─ Docs/                       This directory
```

### 2.2 C++ Module Division Principles

| Module | Responsibility | Dependency direction |
|---|---|---|
| `RobotCore` | Pure data types, GameplayTag declarations, Primary Data Asset base classes | Depends on no other game module |
| `RobotAssembly` | Mech assembly, module mounting, Mutable bridge | → Core |
| `RobotCombat` | GAS, damage routing, part HP | → Core, Assembly |
| `RobotAI` | StateTree, perception, EQS | → Core, Combat |
| `RobotWorld` | Streaming, base, area management | → Core |
| `RobotUI` | ViewModel, widget base classes | → Core (**does not directly depend on Combat**, reads data via interfaces) |
| `RobotSave` | Save serialization, version migration | → Core |

**Hard rule**: dependencies only go one way. `RobotUI` is not allowed to `#include` `RobotCombat` headers — UI gets data through interfaces or events. This rule prevents UI and gameplay from becoming hopelessly tangled and unrefactorable later.

### 2.3 Blueprint / C++ Boundary Rules

This is the easiest place to lose control; rules must be set in stone in week 1:

| Content | Use C++ | Use Blueprint |
|---|---|---|
| Core system logic (assembly, damage, saves, AI decisions) | ✅ | ❌ |
| Data asset definition & validation | ✅ | ❌ |
| Number tuning, curves, drop tables | ❌ | ✅ |
| Level scripts, triggers, one-off set-pieces | ❌ | ✅ |
| UI layout & styling | ❌ | ✅ |
| Prototype validation (P0–P1 phase) | ❌ | ✅ Fast trial and error allowed; rewrite before entering P2 |

**Prohibition**: don't implement core gameplay logic in Blueprint and then "move it to C++ when there's time." Prototype Blueprints must be rewritten before P2, otherwise performance and maintainability will blow up in P3.

### 2.4 Data-Driven Conventions

All tunable content goes through **Primary Data Assets**, not scattered Blueprint default values:

```
URobotChassisData : UPrimaryDataAsset
  ├─ ChassisTag          (GameplayTag: Chassis.Light)
  ├─ Mass                (float, kg)
  ├─ PowerCapacity       (float)
  ├─ HeatCapacity        (float)
  ├─ BaseMovementParams  (FChassisMovementParams)
  ├─ SocketLayout        (TArray<FModuleSlotDef>)
  └─ UnlockCost          (FEconomyCost)
```

Benefits: designers change numbers without opening Blueprints; editor tools can batch-validate (e.g. "all mechs must have 4 slots"); numbers can be exported to CSV for balance analysis.

### 2.5 Version Control & Continuous Integration

| Item | Solution | Reason |
|---|---|---|
| Version control | **Perforce Helix Core** (preferred) or Epic's built-in **Unreal Revision Control** | UE assets are binary; Git struggles with large files. Teams > 15 use P4, small teams can use URC |
| Asset locking | Mandatory Checkout / Lock | Prevent conflicts from two people editing the same uasset |
| Large files | Binary assets go through P4 or Git-LFS; never directly into the Git main repo | Avoid repository bloat |
| Build acceleration | **Unreal Build Accelerator (UBA)** + distributed build | Build time of a large C++ project directly determines iteration speed |
| CI | **Unreal Horde + BuildGraph** | Automatic daily builds |
| Automated testing | **Gauntlet** + Automation Spec | Smoke tests: launch, load, save read/write, key levels passable |
| Data validation | In-house Editor Validator | Validate naming, slots, LOD, material slots before every commit |

**Daily build acceptance line**: can launch → can enter the main base → can enter an area → can fight → can customize → can save and load. Fix any broken link the same day.

---

## 3. Core System Implementation

### 3.1 Mech & Module Assembly

**Target experience**: the player drags a part in the customization UI, immediately sees the mech's form change in the preview, and reads live feedback on the three constraints of weight/power/cooling.

**Implementation layers**:

| Layer | Content | Implementation |
|---|---|---|
| Chassis | Light biped / medium general / heavy quadruped, 3 classes | Separate `ARobotCharacter` subclass + separate SkeletalMesh + separate AnimBP |
| Module | Head, core, arms, chassis, auxiliary, about 40 total | Bone socket mounting, `UStaticMeshComponent` / `USkeletalMeshComponent` subcomponents |
| Tool | Battlefield quick-swap tools, a few | Hand sockets, swapped at runtime |

**Key constraint design (where pillar P1 lands)**:

| Constraint | Effect | Design intent |
|---|---|---|
| Mass | Affects movement speed, jump height, hit displacement | Make "heavy build" genuinely cumbersome, not pure benefit |
| Power | All active modules share a cap | Force trade-offs: can't fill up on high-drain modules at once |
| Heat | Determines sustained output duration | Create a "burst–pause" combat rhythm |

The three constraints check each other — the core mechanism preventing "one best build wins all." **Without these three, 40 modules are just 40 number stickers.**

**When to introduce Mutable**:
- P1 phase: use the socket mounting approach first (simple, controllable, good enough).
- P2 evaluation: if a "module needs to change skeleton proportions" or "merge skins to reduce draw calls" need appears, then introduce Mutable.
- Judgment criterion: draw calls exceed budget under the socket approach, or artists need to make deformation-type modules.

### 3.2 Part Dismantling & Damage Routing

**Target experience**: the player aims at an enemy's legs rather than the torso, and after shooting them off the enemy genuinely limps instead of just losing more HP.

**Implementation plan**:

```
Hit detection
  └─ Hit bone name (FName BoneName)
       └─ UPartMapData (DataAsset): BoneName → FGameplayTag (Part.Leg.R)
            └─ UPartDamageComponent: TMap<FGameplayTag, FPartHealth>
                 └─ Part HP reaches zero
                      └─ Presentation layer: HideBoneByName() + spawn a drop Actor
```

**Why part HP is not put into the GAS AttributeSet**: part counts are dynamic (different enemies have different part counts), while AttributeSets suit fixed attributes. A standalone component manages them; GAS only delivers damage via GameplayEffects.

**How "Fake Dismantling" works**:
1. One body per part in the Physics Asset, naming convention `part_upperarm_R`.
2. When a part is destroyed, `HideBoneByName` hides that part's bone.
3. Simultaneously spawn a pre-made **part model** (physics-simulated), which becomes pickable after landing.
4. Don't use Chaos per-piece shattering — fragments are uncontrollable and can't reliably serve as pickups.

**Named enemies (repairable / recruitable)**: additionally attach `UCompanionCandidateComponent`. When part HP hits zero but the core survives, they enter a "repairable" state, and the player chooses repair (consume resources, gain a companion) or dismantle (gain a rare core). This is where pillar P2 lands.

**Edge cases that must be handled**:
- All parts destroyed but core alive → enemy enters a "disabled" state rather than dead, still interactable.
- Player's own part destroyed → temporarily lose the corresponding ability (if an arm is destroyed, that arm's weapon can't be used), auto-repaired at mission end.
- Multiple hits on the same part → damage doesn't spill to other parts, preventing "shooting the leg equals shooting the whole body."

### 3.3 Power & Heat (GAS Implementation)

**AttributeSet definition**:

| Attribute | Type | Effect | Initial value |
|---|---|---|---|
| `Power` | Current power | Consumed by abilities | `[PLACEHOLDER]` |
| `PowerRegen` | Power recovery rate | Determined by core module | `[PLACEHOLDER]` |
| `Heat` | Current heat | **Only rises, never falls on its own** | 0 |
| `HeatDissipation` | Cooling rate | Determined by chassis/auxiliary modules | `[PLACEHOLDER]` |
| `OverheatThreshold` | Overheat threshold | Triggers lock | `[PLACEHOLDER]` |

**Heat is a "reverse resource"** — the core lever of combat rhythm:
- Attacks, dashes and overloads all add Heat.
- Heat only drops through cooling actions (pause attacking, dedicated cooling ability, environment cooling zones).
- Heat reaching the threshold triggers `GameplayTag.State.Overheated`, locking weapons for 2 seconds `[PLACEHOLDER]`.

**Design intent**: create a "burst window — forced pause" rhythm, making players actively plan their output rhythm instead of mindlessly firing. This is where pillar P1 lands at the combat layer.

**Validation path**: paper simulation (Excel computes the "sustained output time" for 3 module combos) → first playable prototype records 10 real matches → observe whether players actively manage heat. **If players never look at the heat bar, the lever has failed and needs redrawing.**

### 3.4 Locomotion & Climbing

**Foundation**: CMC + Enhanced Input.

**Movement differences among the three mechs (players must feel them immediately)**:

| Mech | Movement trait | Custom MovementMode |
|---|---|---|
| Light biped | Double jump, air dash, wall kick | `MOVE_Custom_1` air dash |
| Medium general | Standard run/jump, grapple hook | `MOVE_Custom_2` grapple pull |
| Heavy quadruped | Slow, high resistance, magnetic-foot climbing | `MOVE_Custom_3` surface adhesion |

**Climbing implementation points**:
- Magnetic climbing uses a custom MovementMode: detect normal → align character orientation to the surface → replace gravity with adhesion force.
- Don't fake climbing with "special travel volumes" (NavLink + animation montages) — players will immediately feel "this isn't really climbing."
- Climbing is the heavy mech's core selling point and a landing spot for pillar P1: swap mech → swap reachable routes.

### 3.5 Enemy AI

**StateTree structure example (a named enemy)**:

```
Root
├─ State: Patrol        Patrol, sense the player
├─ State: Engage        Fight, switch attack mode by part damage
│   ├─ Task: Choose attack part (based on own part survival)
│   └─ Task: Move to effective range (EQS query for cover and firing lines)
├─ State: Staggered     Core exposed, enters repairable/recruitable window
└─ State: Disabled      Core destroyed, disabled and interactable
```

**Key points**:
- Enemies reuse `UPartDamageComponent`, the same system as the player. **One set of code, two experiences** — that's the key architectural benefit.
- Named enemies' attack modes change with part survival (break an arm → switch to melee) — this is "dismantling has strategy" on the enemy side.
- EQS queries cover and firing lines, avoiding enemies queuing up to die.
- Regular enemies use lightweight AI (simplified StateTree), named enemies use the full state machine. **Don't write a full state machine for all 20 enemy types.**

### 3.6 Salvage & Economy System

**Sources & Sinks model** (the foundation of whether customization gameplay holds up):

| Sources (where materials come from) | Sinks (where materials go) |
|---|---|
| Dismantling enemies (main source) | Craft modules |
| Area wreckage / chests | Craft mech frames |
| Mission rewards | Repair mechs & parts |
| Base recycling station (passive output) | Upgrade module tiers |
| — | Base construction (companion facilities) |

**Inflation risk & countermeasures**:

> **Risk**: dismantling is an unlimited source; players can farm the same area for infinite materials, and module prices quickly lose meaning.

**Countermeasures (all three at once)**:
1. **Modules are unlocked with "blueprint + rare core"; materials are only a consumable.** Rare cores come only from named enemies and key missions, limited in number and not farmable.
2. **Area material decay**: repeatedly clearing the same area yields diminishing materials (`[PLACEHOLDER]` decay curve).
3. **Base construction consumes large amounts of materials**, acting as a long-term sink that absorbs inflation.

**Validation path**: use Monte Carlo to simulate the material-stock curves of 3 player types (speedrunner / collector / grinder) over 30 hours. If the grinder's stock tends to infinity after 10 hours, the sinks are insufficient.

### 3.7 Mobile Base & Level Streaming

**Two streaming strategies, used separately by level type**:

| Level type | Solution | Reason |
|---|---|---|
| 5 large areas | **World Partition + HLOD** | Need wide-range streaming and HLOD simplification |
| Main base (inside the mobile city) | **Traditional sub-level streaming (Level Streaming)** | Compact space, complex logic; World Partition is harder to control |
| Colossus level | **Single level + segmented loading** | The colossus is a controlled-moving whole, not suitable for spatial splitting |

**Mobile base implementation**:
- The base is an `ALevelInstance` Actor in the Persistent Level.
- Base movement is **controlled and scripted**, no real physics simulation of the whole city.
- Interior base space uses sub-level streaming, unloading the outer area when entering indoors.
- Players see companion facilities change with progress inside the base — this is the visualization of "choices having consequences."

**Use the new 5.8 tool**: World Partition Insights can analyze streaming performance per cell and replay sessions — the direct tool for diagnosing "why does entering this area hitch."

### 3.8 Save System

**Save granularity decision (a real design tension)**:

> PC single-player players expect "save anytime" by default. But in this game, saving anytime means serializing: mech assembly state, ownership of 40 modules, drop positions in the world, enemy part HP, companion relationships, base construction progress — a huge state space, and bug-prone.

**Decision**: **checkpoint-style autosave + manual save slots**, no save-anytime quicksave.
- Each mission has 2–3 checkpoints, matching the 20–40 minute run pace.
- Players can manually save to multiple slots at the main base.
- Save points align with mission beats (after preparation, during tension, before salvage).

**Version migration**:
- `USaveGame` subclasses carry a `SaveVersion` field.
- Every time the save structure changes, write a migration function.
- **From P2 on, every iteration must test reading old-version saves.** Without this, corrupted player saves after launch would be the most fatal source of bad reviews.

### 3.9 UI

**Technology**: Common UI + MVVM.

**Three highest-priority screens (in implementation order)**:

1. **Customization screen** — carries pillar P1, must be done earliest. Requirements: live preview of mech form; live numeric feedback on the three constraints; highlight the difference from the current loadout.
2. **Mission briefing / map** — carries pillar P3's "preparation" beat.
3. **Combat HUD** — heat bar, power bar, part damage indicators.

**Key UX decision**: the customization screen must let players **see changes in weight/power/cooling without leaving the screen**. If players have to switch back and forth to judge whether a loadout is viable, customization turns from "fun" into "bookkeeping."

### 3.10 Audio

| Requirement | Solution |
|---|---|
| Robotic voice (non-human but emotional) | MetaSounds synthesis, pitch/filter varying with emotion parameters |
| Engine sound varying with load | MetaSounds parameter binding to movement speed and heat |
| Combat rhythm sync | Quartz beat synchronization |
| Debugging | Audio Insights (production-ready in 5.8) |

**Design point**: robot characters don't use human voice actors; they use **synthesized voice + subtitles**. The reason is character-setting consistency (they aren't human), plus significantly lower cost and avoiding the scale problem of multilingual dubbing.

### 3.11 Presentation & Cutscenes

**Strictly control the number of cutscenes.** Focus investment on 4 scenes:

| Scene | Content | Purpose |
|---|---|---|
| Opening | Shiyi gains cross-mech migration ability | Establish worldview and core mechanic |
| Departure | The Lighthouse mobile city starts up for the first time | Show the "big production" scale |
| Colossus | The "Walking Blizzard" level concludes | Highlight moment for the core selling point |
| Ending | The global forced-reclamation program terminates | Emotional landing point |

Other areas use **environmental storytelling + companion dialogue**, not full cutscenes. Every extra high-cost cutscene means a batch less of playable content — a trade-off that must be guarded.

---

## 4. System Interaction Matrix

Expose the risk of systems fighting each other early. Mark each pair's relationship: **Intended** / **Acceptable** / **Bug** (must fix).

| System A | System B | Relation | Notes |
|---|---|---|---|
| Part dismantling | Locomotion system | Intended | Leg part destroyed → movement limited, core experience |
| Part dismantling | Animation system | Intended | Animation must adapt after parts are hidden (firing without an arm) |
| Part dismantling | Drop physics | **Bug risk** | Many drops simulated at once → performance spikes. Need a drop count cap + switch to static immediately on landing |
| Customization | Saves | **Bug risk** | Save and reload after customizing; module ownership must be consistent. Needs dedicated testing |
| Customization | Economy | Intended | Rare cores limit customization pace |
| Heat system | Enemy AI | Intended | Enemies should attack during the player's overheat window |
| Heat system | UI | Intended | The heat bar must be one of the most prominent HUD elements |
| Climbing | Streaming | **Bug risk** | Crossing streaming cells while climbing → possible loading hitch causing a fall. Need climbing-path preloading |
| Mobile base | Saves | Acceptable | Base position doesn't need precise saving, just a progress marker |
| Companion system | Mission flow | **Bug risk** | Different companion recruit orders → dialogue branch combinations explode. Need to limit companion joining timing |
| MegaLights | Performance | Acceptable | Need per-scene light limits; industrial scenes easily exceed budget |
| Control Rig Physics | Stability | **Bug risk** | Beta feature, needs a fallback (fall back to hand-keyed animation) |

**Revisit this table at every milestone review**; every new system must add a row.

---

## 5. Art & Animation Pipeline

### 5.1 Robot Modeling Standards (Outsourcing Deliverables Must Comply)

| Item | Standard |
|---|---|
| Units & scale | Centimeter system, 1 unit = 1 cm |
| Orientation | Unified +X forward, +Z up |
| Pivot | Module pivots unified at socket centers, never at bounding-box centers |
| Socket naming | `socket_head`, `socket_arm_L`, `socket_arm_R`, `socket_back`, `socket_aux_01…` |
| Skeleton | Each of the 3 mech classes has its own skeleton, but shares the IK Rig definition to reuse animation |
| Triangle budget | Player mech 150k–250k; named enemies 60k–100k; regular enemies 30k–60k; modules 2k–8k |
| Textures | Parts 1024, mech body 2048, unified sRGB and normal formats |
| Material slots | Max 2 material slots per module (limit draw calls) |
| LOD | 4 levels auto-generated + manual fixes, ≥50% reduction from LOD1 |
| UV | Modules share a UV layout convention for material reuse |

### 5.2 Environment Art

- **Nanite is used for static environment geometry** (mega-structures, buildings, terrain).
- **Skeletal meshes use the standard LOD pipeline**, not Nanite.
- Area modularization: each area uses a unified modular piece set, reducing modeling cost and speeding up level construction.
- **PCG is used for scattering**: ruins/debris, pipes, vegetation. Prefer stable PCG nodes; experimental nodes don't enter the production pipeline.
- **Procedural foliage editor (experimental)**: only for concept exploration, not final assets.

### 5.3 Animation Pipeline

| Stage | Solution |
|---|---|
| Animation shared across 3 mech classes | IK Retargeter + shared IK Rig definition |
| State machines | One AnimBP per mech class, sharing the base layer |
| Attack alignment | Motion Warping (auto-align to target when attacking) |
| Secondary motion | Control Rig Physics (antennas, cables, hydraulic hoses) — **beta, must have a fallback** |
| Procedural footsteps | Foot IK + terrain adaptation (heavy quadrupeds must plant firmly on uneven ground) |

**Outsourcing delivery package must include**: UE project template, naming-standard document, pivot/orientation acceptance checklist, LOD and material-slot checking tools. **Don't accept assets without acceptance tools** — otherwise rework costs eat the money saved by outsourcing.

---

## 6. Performance Budget & Gates

### 6.1 Target Configurations

| Tier | Hardware reference | Resolution / frame rate | Quality preset |
|---|---|---|---|
| Minimum | GTX 1660 / Ryzen 5 3600 | 1080p / 30fps | Low (Lumen Lite off, baked lighting) |
| Baseline | RTX 3060 / Ryzen 5 5600 | 1080p / 60fps | Medium (Lumen Lite + MegaLights throttled) |
| Recommended | RTX 4070 / Ryzen 7 5800X | 1440p / 60fps | High (full Lumen) |
| High-end | RTX 4080+ | 4K / 60fps | Very high |

### 6.2 Frame Budget (Baseline 1080p/60fps, total 16.6 ms)

| Item | Budget | Notes |
|---|---|---|
| Game thread | 6.0 ms | Includes AI, animation, physics |
| Render thread | 8.0 ms | Includes Lumen, MegaLights |
| GPU | 14.0 ms | — |
| Reserve | 2.6 ms | Fluctuation margin |

**Hard limits**:
- Draw call: < 5000 (baseline 1080p)
- Enemies on screen: ≤ 12 regular or 4 named `[PLACEHOLDER]`
- Drops on screen: ≤ 20, oldest automatically goes static beyond that `[PLACEHOLDER]`
- MegaLights on screen: ≤ 32 `[PLACEHOLDER]`
- VRAM: < 8 GB @ 1080p medium quality

### 6.3 Performance Gates

**Set a performance gate at every milestone; don't advance to the next phase if it fails.** This is the only mechanism that prevents "discovering it can't run right before launch." Must reach baseline 60fps by the end of P2, otherwise optimize before expanding content.

---

## 7. Milestone Plan (42 Months)

### P0 Pipeline & Pre-research · Month 1–2 · 6–8 people

| Item | Content |
|---|---|
| **Goal** | Engine pipeline working, four major technical risks validated |
| **Deliverables** | Empty project + module skeleton; Perforce/URC repo; naming and code convention docs; 4 technical validation reports |
| **Validation items** | ① Can Mutable assemble modules at runtime while keeping performance ② Can part dismantling + drop salvage loop run end-to-end ③ Does World Partition large-area streaming meet spec ④ Feasibility of GAS carrying power/heat |
| **Acceptance criteria** | Each validation report gives a clear "feasible / infeasible / needs a changed approach" conclusion, with measured data attached |
| **Failure signal** | Validation items closed with "should be fine" — validation without measured data equals no validation |
| **Risk** | Mutable learning curve exceeds expectations → fall back to the socket approach, don't block progress |

### P1 Core Prototype · Month 3–6 · 12–15 people

| Item | Content |
|---|---|
| **Goal** | Prove in gray-box that "changing gear really changes the fighting" |
| **Deliverables** | One playable gray-box level: 1 mech frame + 3 swappable modules + 1 battle + full dismantle/salvage/customize loop + minimal customization UI |
| **Acceptance criteria** | 10 external players in blind tests: ≥7 independently discover and try customizing; ≥6 can describe the gameplay difference before/after customizing |
| **Failure signals** | ① Players never open the customization UI ② Players can't describe the difference after customizing ③ Players only care about "which number is higher" |
| **Staffing focus** | 1 combat designer, 1 systems designer, 2 gameplay programmers, 1 AI programmer, 1 technical artist, 1 level designer |
| **Key discipline** | Get the paper prototype working before writing code. Work out the three constraints in Excel before entering the engine |

### P2 Vertical Slice · Month 7–14 · 20–30 people

| Item | Content |
|---|---|
| **Goal** | Build a 20–40 minute full-quality sample |
| **Deliverables** | One complete mission (incl. colossus level segment); art style established; performance baseline met; save system; final customization UI |
| **Acceptance criteria** | ① External blind-test completion ≥80%, no soft-locks ② Baseline 1080p/60fps met ③ 20 minutes continuous play without crashes ④ Old saves read correctly |
| **Failure signals** | ① Players drop out midway ② Frame rate misses spec but "plan to optimize later" ③ Colossus level can't be built and must become a static scene |
| **Key decision point** | **The colossus level is the project's biggest cost risk.** This phase must first produce a playable colossus sample; if not achievable, downgrade to a static giant scene and adjust all marketing accordingly |

### P3 Mass Production · Month 15–30 · 60–100 people

| Item | Content |
|---|---|
| **Goal** | Deliver content by area in bulk |
| **Deliverables** | 5 areas; 3 mech classes; ~40 modules; 20 enemy types; 6 boss fights; companion system; base construction |
| **Acceptance criteria** | Each area accepted independently: passable, performance met, no blocking bugs, old saves compatible |
| **Cadence** | Bi-weekly iterations, one playable build per iteration; monthly internal playtest; quarterly external playtest |
| **Failure signals** | ① Areas feel repetitive (players can't describe differences) ② Content output below plan and made up with overtime ③ Technical debt accumulates and slows new-area development |
| **Key discipline** | Systems freeze at end of P2. No new systems during P3 — only content and polish. **Any "add a new system" proposal must first include a conflict-risk doc against existing systems** |

### P4 Content Lock & Full Clear · Month 31–36 · 80–100 people

| Item | Content |
|---|---|
| **Goal** | Full flow playable, systems frozen |
| **Deliverables** | Complete main story passable; all endings reachable; UE6 migration assessment report |
| **Acceptance criteria** | ① 3 full playthroughs with no blocking bugs ② All save migration paths verified ③ Performance met |
| **Failure signals** | ① Closed out with "this bug doesn't block completion" ② Content still being added |
| **Key decision** | Assess whether to migrate to UE6. **If migrating, reserve 2 months and do migration only, no content**; if not, lock to 5.8 until release |

### P5 Polish & Release · Month 37–42 · 60–80 people

| Item | Content |
|---|---|
| **Goal** | Performance, compatibility, certification, launch |
| **Deliverables** | Release candidate; localization; accessibility features; store page & marketing assets |
| **Acceptance criteria** | ① All target configs met ② Accessibility passes review ③ Platform certification passes ④ 4-hour continuous stress test without crashes |
| **Failure signals** | ① Hiding insufficient optimization by lowering target configs ② Still fixing feature bugs right before launch |

---

## 8. Team & Budget

### 8.1 Staffing by Phase (Planned)

| Function | P0–P1 | P2 | P3 | P4–P5 |
|---|---|---|---|---|
| Producer / Director | 1 | 2 | 3 | 3 |
| Gameplay / Systems Designer | 2 | 3 | 5 | 4 |
| Level / Narrative Designer | 1 | 3 | 6 | 5 |
| Gameplay Programmer | 2 | 4 | 8 | 7 |
| Engine / Tools Programmer | 1 | 2 | 5 | 5 |
| AI Programmer | 1 | 2 | 3 | 3 |
| Technical Artist | 1 | 3 | 6 | 6 |
| Character Artist | 1 | 4 | 10 | 8 |
| Environment Artist | — | 4 | 16 | 12 |
| Animator | 1 | 3 | 8 | 6 |
| VFX / Effects | — | 1 | 4 | 4 |
| Audio | — | 2 | 3 | 3 |
| UI / UX | 1 | 2 | 4 | 4 |
| QA | 1 | 4 | 12 | 15 |
| **Total (approx.)** | **13** | **39** | **93** | **85** |

### 8.2 Budget Model (Example, Not a Market Quote)

| Item | Calculation | Amount |
|---|---|---|
| Internal staff | Average 70 people × 42 months × ¥45k fully-loaded monthly cost per person | ¥132M |
| Outsourcing (art / animation / audio) | — | ¥50M |
| Engine & tool licensing | — | ¥3M |
| Hardware, software & office | — | ¥5M |
| Testing & certification | — | ¥3M |
| **Subtotal** | — | **¥193M** |
| Contingency 20% | — | ¥38.6M |
| **Total R&D budget** | — | **~¥232M** |

> Marketing, platform revenue share and publishing-related costs are listed separately. **Per-person cost and average headcount are the most sensitive variables** — dropping average headcount from 70 to 50 lowers the budget to ~¥170M; raising it to 100 pushes it to ~¥320M. The model's value is showing what every 10 extra people means, not giving a precise figure.

---

## 9. Risk Register

| # | Risk | Probability | Impact | Mitigation | Trigger condition |
|---|---|---|---|---|---|
| R1 | Module combination explosion causes balance loss | High | High | Fixed slots + hard caps on weight/power/cooling constraints; module count capped at 40 | Appearance of a "dominant all-purpose build" |
| R2 | Colossus level cost overrun | High | High | Build a sample in P2 first; use controlled motion + localized physics; downgrade if not achievable | P2 sample 2 months late |
| R3 | Mover not production-ready causes rework | Medium | Medium | Locomotion via interface abstraction, CMC primary, re-evaluate at P4 | Official announcement that Mover is production-ready |
| R4 | UE6 migration risk | Medium | Medium | Lock to 5.8 until P4; reserve a 2-month evaluation window | Epic announces stable UE6 |
| R5 | Blueprint / C++ boundary confusion | High | Medium | Set rules in week 1; rewrite prototype Blueprints before P2 | P3 performance issues traced to Blueprints |
| R6 | Performance miss | Medium | High | Performance gate at each milestone; don't advance if it fails | 60fps not reached by end of P2 |
| R7 | Save compatibility broken | Medium | Medium | Save version number + migration functions; test old saves every iteration from P2 | An unreadable save appears |
| R8 | Outsourced asset quality miss | High | Medium | Delivery includes template + acceptance tools; reject if below standard | Rework rate > 20% |
| R9 | Area gameplay repetition | Medium | High | Each area must have a distinct exploration mechanic; quarterly external playtests | Players can't describe area differences |
| R10 | Control Rig Physics (beta) unstable | Medium | Low | Fallback: hand-keyed secondary motion animation | Non-reproducible jitter/clipping appears |
| R11 | Core experience fails (customization is imperceptible) | Medium | **Fatal** | P1 blind test; if it fails, redraw the customization system, no entry to P2 | P1 acceptance failure signal appears |

**R11 is the only fatal risk.** It means the game's entire selling point may not hold. So P1 acceptance can't rely on internal self-testing — you must find external players and define in advance "what broken looks like."

---

## 10. First 14 Days Execution Checklist

This is a startup checklist you can follow directly. The goal isn't to make a game, but to **get the first signal within two weeks on "whether this core loop holds up."**

| Day | Task | Output |
|---|---|---|
| D1–D2 | Install UE 5.8; set up a Perforce or Unreal Revision Control repo; establish project directories and naming-convention docs | A committable empty project |
| D3–D4 | Set up the C++ module skeleton (RobotCore / RobotCombat / RobotAssembly); integrate Enhanced Input; build a capsule that can run and jump | A controllable gray-box character |
| D5–D6 | Integrate GAS; implement Power / Heat attributes; make a dash ability that consumes power and generates heat; overheat lock | Movement where the "burst–pause" rhythm can be felt |
| D7–D8 | Implement `UPartDamageComponent`; make a bone-name → part-tag mapping DataAsset; make a dummy enemy that limps when shot in the leg | Part damage is verifiable |
| D9–D10 | Part destruction → hide bone + spawn a part drop → pickup → material count | Salvage loop working end-to-end |
| D11–D12 | Build the ugliest but usable customization UI: 3 slots, changing gear genuinely changes move speed and attack style | Customization affects gameplay |
| D13–D14 | Self-test 10 runs, record three data points: do players customize proactively? Do they perceive a difference after customizing? Do players watch the heat bar? | A self-test report + next-step decision |

**D14 decision rules**:
- All three data points positive → enter P1, expand module count and levels.
- Customization imperceptible → stop and redraw the customization system, don't keep adding content.
- Players don't watch the heat bar → heat lever failed, simplify or replace the mechanic.

**The most important role of this checklist isn't output — it's turning the vague question "is this game fun?" into a concrete experiment with an answer obtainable within two weeks.**

---

## Appendix A: Asset Naming Conventions

| Prefix | Type | Example |
|---|---|---|
| `BP_` | Blueprint class | `BP_RobotCharacter` |
| `SK_` | Skeletal mesh | `SK_Chassis_Light` |
| `SM_` | Static mesh | `SM_Module_Arm_Mining` |
| `M_` / `MI_` | Master material / material instance | `M_Robot_Master` / `MI_Robot_Rust` |
| `T_` | Texture | `T_Robot_BaseColor` |
| `ABP_` | Animation Blueprint | `ABP_Chassis_Light` |
| `AM_` | Animation Montage | `AM_Attack_Heavy` |
| `DA_` | Data Asset | `DA_Chassis_Light` |
| `DT_` | Data Table | `DT_EnemyStats` |
| `WBP_` | UMG widget | `WBP_AssemblyScreen` |
| `LS_` | Level Sequence | `LS_Intro_Migration` |
| `NS_` | Niagara System | `NS_Spark_Impact` |
| `MS_` | MetaSound | `MS_Engine_Load` |

## Appendix B: Number Table Template (every value must have a rationale)

| Parameter | Value | Status | Rationale | Validation path |
|---|---|---|---|---|
| Light mech mass | `[PLACEHOLDER]` | To validate | Must be 30% lighter than medium so "light and nimble" is perceptible | Blind-test whether players can tell in the prototype |
| Dash ability power cost | `[PLACEHOLDER]` | To validate | Must limit consecutive dashes to within 3 | Paper simulation + 10 real matches |
| Overheat lock time | `[PLACEHOLDER]` | To validate | Long enough to be a penalty, but not so long players abandon the weapon | Measure whether players change their output rhythm |
| Heavy mech climbing speed | `[PLACEHOLDER]` | To validate | Slower than walking but faster than detouring | Level pass-time comparison |

> Rule: **no value without a rationale is allowed into the config tables.** If you can't write a rationale, that value shouldn't exist yet.
