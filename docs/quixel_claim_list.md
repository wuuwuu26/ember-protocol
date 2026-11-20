> Language: **English** | [简体中文](./Quixel_领取清单.md)
# Quixel Megascans Claim List (Round 105 / 2026-11-09)

Goal: use the free Quixel Megascans assets on Fab to keep deepening the sci-fi industrial arena of "Ember Protocol"
(the current new area is procedural gray-blue steel plate + Cosmos industrial props).

## I. Why You Must Claim These First

| | Cosmos (last round, already working) | Fab / Megascans (this round) |
|---|---|---|
| Acquisition | Public CDN preview glTF, I download directly | Epic account login → claim → Launcher download |
| Anonymous direct link | Yes | **No**, the anonymous endpoint only gives metadata (title/cover/price) |
| Can I land it automatically | Yes | **No**, you must download the files locally first |

Current state of this machine: Epic Games Launcher is installed and logged in (logs show `LoggedIn` /
`Verify access token succeeded`), but `VaultCache\FabLibrary\listings_v1.db`
and the download cache **are all 0 rows** — there are no claimed/downloaded Megascans assets at all.

## II. Important Note About "Free"

- **2026-11-05** Quixel official announcement: `Update: Megascans are going free again` —
  **the entire Megascans library is free again on Fab**, with refunds to purchasers since 2025.
- But today in the anonymous search endpoint these assets still have `isFree` = `false` and show `$4.99`.
  This is **stale anonymous cache / phased rollout** (only 4 days have passed).

👉 **Go by your logged-in Fab UI**: after logging in it should show "Free / Owned / Claim".
If a few still ask for payment, first claim the explicitly free `... Megascans Sample` bundles and
Fab's `Free` filter, and wait for the phased rollout for the rest. Don't pay the $4.99 from the anonymous page.

Also worth checking **My Library** first — Megascans claimed historically are kept there.

## III. Claim List (all names are really searchable on Fab)

A single Fab series has dozens of variants; clicking through each is exhausting — claiming by "search keyword" in bulk is fastest.
Priority: **claim P0 first** (few and choice, big impact), P1/P2 if there's spare capacity.

### P0 — Best Fit, Claim First

| Search this on Fab | Representative asset | Type | Where to use it in the scene |
|---|---|---|---|
| `Industrial Abandoned Factory` | Wall Set Concrete Modular | 3D | Replace/enrich the walls on both sides of the new area, make industrial walls |
| Same as above | Door Double Metal, Vent Air Metal Rusted, Panel Console Modular, Cable Wall Modular | 3D | Door openings, wall detail, wall-mounted devices |
| Same as above | Ground Patch Gravel / Scatter Debris Plaster / Rubble Pile Plaster | 3D | Ground scatter, around cover, break the "clean floor" feel |
| Same as above | Debris Pipe Metal / Ceiling Concrete Rebar | 3D | Pipes and ceiling layers |
| `Derelict Corridor Megascans Sample` | Derelict Corridor Megascans Sample | Bundle | Directly reinforces the "corridor → new area" stretch (a ready-made set) |
| `Industrial Concrete Floor` | Industrial Concrete Floor | Material | Replace the pure-color procedural floor with realistic concrete |
| `Weathered Concrete Wall` | Weathered / Damaged / Stained Concrete Wall | Material | Make the walls realistic |

### P1 — Cover and Industrial Props (Reinforcing the Existing Cosmos Layout)

| Search this on Fab | Representative asset | Type | Purpose |
|---|---|---|---|
| `Rusty Metal Barrel` | Rusty Metal Barrel / Shelf / Workbench | 3D | Grouped cover |
| `Tarped Crate` | Tarped Crate | 3D | Cover |
| `Corrugated Metal Sheet` | Corrugated Metal Sheet | 3D | Temporary barricade/cover |
| `Painted Pipe` / `Concrete Pipe` | Painted Pipe Straight / Connector / Base / Y / T / Cross | 3D | Pipe groups, echoing the existing `cs1-pipe` |
| `Concrete Rubble Pile` | Concrete Rubble Pile / Cement Rubble / Construction Rubble | 3D | Rubble cover |
| `Sandbag` | Military Trenches Barrier Sandbag Canvas | 3D | Echoing the existing sandbag stacks |
| `Rusty Metal Sheet` | Rusty / Rusty Painted / Rusty Green Metal Sheet | Material | Rusted iron surfaces |

### P2 — Materials and Atmosphere (If There's Spare Capacity)

| Search on Fab | Type | Purpose |
|---|---|---|
| `Ground Gravel` / `Gravel Ground` / `Asphalt Road` | Material | Gravel/asphalt ground |
| `Damaged Concrete` | Decal | Floor damage decals |
| `Urban Trash` / `Bricks Rubble` | 3D | Environmental scatter |
| `Dark Ruins` / `Military Trench` Megascans Sample | Bundle | Wasteland/trench atmosphere reference or reuse |

> Type advice: prefer **3D Model** and **Material** (our scene uses StaticMesh + PBR materials),
> Decal / Brush second.

## IV. Claim and Placement Steps

1. **Fab web**: log in with your Epic account at top right → go to the `Quixel Megascans` seller page
   → search by the keywords in the table above → click "Claim / Add to Library" one by one (should be free now).
   Or use the **Epic Games Launcher → Fab** tab to search, claim and download.
2. **Download / export**: in the Launcher's **Fab Library**, download the assets you need;
   if there's "Export to project / Export as file", export as **FBX + textures** or a native UE package, either is fine.
3. **Put them in this directory** (keep the subdirectory structure, don't rename or merge):
   ```
   C:\Users\25227\Documents\robot_game\art_src\megascans\
   ```
4. **Tell me**, and I'll take over: scan the actual formats → downscale textures → batch import into UE →
   place them into the new area following the existing layout logic (reusing last round's idempotent Cosmos pipeline).

## V. What's Already Ready on My Side

- UE 5.8 ships with `MegascansPlugin` (no separate install needed)
- The offline pipeline that worked last round: `tools/cosmos_build.py` (downscale + package),
  `ue/Scripts/import_cosmos_assets.py` (batch import),
  `ue/Scripts/place_cosmos_props.py` (idempotent placement) — can be adapted and reused directly with a different asset source
- The new area skeleton + 31 Cosmos props are already in the level; Megascans is "layering on top to deepen it",
  it won't overturn what's already done

Probe scripts kept for the record: `tools/probe_fab_api*.py`, `probe_fab_quixel.py`,
`probe_fab_free.py`, `probe_fab_cache.py`; the real asset metadata is in
`docs/fab_quixel_assets.json` (163 Quixel assets).
