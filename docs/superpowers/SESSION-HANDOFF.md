# Session Handoff — Research-Progress Bar (Phase 2, in-game working)

_Updated 2026-06-28 (icons + field-mod session). Read tools/dev/README.md for the
dev loop — note the NEW hot-reload loop for JS/CSS-only changes._

## TL;DR — where we are
The mod **works in-game** on WoT **EU 2.3.0.1**. The Garage bar renders from live
data in all modes (tech-tree / field-mods / "Fully researched"), refreshes on
tank-switch (listener self-heals across the battle-exit cycle — see gotchas), and
now uses **real in-game icons**:
- **tech-tree module ticks** → the generic module-type glyph (chassis/engine/
  tower/gun/radio), **vehicle ticks** → the framed tech-tree-node tank icon.
- **field-mod ticks** → a hexagon with the level **roman numeral** (clip-path).
- **header category icon** (outboard left of the bar) → Research / Field
  Modifications icons from the in-game Vehicle-management menu.
- **field-mod counter** in the header → "FIELD MODIFICATIONS N/M" = researched /
  total field-mod LEVELS, clamped to the tier cap.
- **COMPLETE state** → class+elite badge (e.g. `mediumTank_elite.png`).

This session's work is committed (HEAD `5008d23`, branch `main`, unpushed). Tests
green (23, py3), 2.7-compiles clean.

**IMMEDIATE NEXT STEPS:**
1. **Tier XI field-mod level cap is UNKNOWN and currently guessed.** `max_level()`
   in `domain/resolvers/fieldmods.py` maps tier≥10→8, so tier **XI also gets 8**,
   which is unverified. The owner has no non-fully-upgraded tier-XI tank to read it
   live, so get the real cap from elsewhere: the EU **decompiled** post-progression
   config (`post_progression*`/vehicle XML — re-clone branch `2.3`, see
   tools/dev/README.md) or the WoT wiki. Confirmed caps so far: **VI–VII=5,
   VIII=6, IX=7, X=8**.
2. **Visually verify the elite badge** on a fully-maxed (all field-mods done) tank —
   not yet seen in-game (no maxed tank was loaded at handoff). It's the COMPLETE
   state: `img://gui/maps/icons/vehicleTypes/md/<class>_elite.png` ('-'→'_').
3. **Confirm the field-mod counter** reads N/8 (tier 10) and N/5 (tier 6) in-game —
   deployed at handoff but the owner moved to handoff before reporting back.

## Architecture (as built, EU 2.3)
- **Domain (engine-free, tested):** `wgmod_research/domain` — `VehicleSnapshot` →
  `build_model` → `ResearchProgressModel` with modes `TECH_TREE` / `FIELD_MODS` /
  `COMPLETE`, two-segment fill (`fill_vehicle`, `fill_free`), `ticks[]`. 15 pytest
  tests (`python3 -m pytest -q`).
- **Adapter (`wgmod_research/adapter/engine_adapter.py`):** live client →
  `VehicleSnapshot`. Tech unlocks via `vehicle.getUnlocksDescrs()` →
  `(idx, xpCost, intCD, prereqs)`; module vs vehicle via
  `getTypeOfCompactDescr/GUI_ITEM_TYPE.VEHICLE`; field mods via
  `vehicle.postProgression.iterOrderedSteps()` (`getPrice().xp`, `isReceived()`).
  Uses `dependency.instance(IItemsCache)`. Each read guarded → safe default.
- **Mount (the tricky part):** WoT 2.3 loads only `.wotmod`. OpenWG's JS injector
  (`gui/gameface/js/index.js`) injects a mod's assets only for hangar **sub-views**
  carrying a `ModInjectModel`. So `mod_wgmod.py` patches
  `HangarVehicleParamsPresenter._onLoading` and calls
  `gameface_bridge.attach(host_vm)` →
  `openwg_gameface.gf_mod_inject(host_vm, "WGModResearch", styles=[…], modules=[…])`
  (loads our JS into the hangar document) and
  `host_vm._addViewModelProperty("wgResearch", ResearchVM())` (our data model).
- **Data → JS:** `WGModResearch.js` (ES module) reads the model via
  `ModelObserver("WGModResearch")` → `model.wgResearch` (+ `ticks[]`, elements as
  `item.value.*`) and renders the bar. Updates: `gameface_bridge.push()` writes via
  `rvm.transaction()` and nudges the host sub-view; subscription lives in the bridge
  (`install_vehicle_listener`) with a **strong global ref** (WG `Event` is weak-ref).

### Key files
```
src/res/scripts/client/gui/mods/mod_wgmod.py                 # entry: patch presenter
src/res/scripts/client/wgmod_research/adapter/engine_adapter.py
src/res/scripts/client/wgmod_research/bridge/gameface_bridge.py   # ViewModels + attach/push/refresh/listener
src/res/scripts/client/wgmod_research/domain/{types,builder,resolvers/*}.py
src/res/gui/gameface/mods/drizzer14/WGModResearch/{WGModResearch.js,.css}
build/deploy_wotmod.py        # clean build+deploy (Python 2.7, client CLOSED)
tools/dev/                    # debug REPL server + client + README (NOT shipped)
docs/superpowers/research/decompiled-findings.md   # verified EU symbols
```

## Remaining v1 work
1. **Tier XI field-mod cap** (see TL;DR #1) + **elite-badge visual verify** (#2) +
   **counter confirm** (#3).
2. **Visual polish** — mostly DONE this session (all hot-reloadable for further
   tuning; see the dev loop):
   - DONE: locked (prereqs-unmet) tech-tree ticks (gray). Field mods carry no
     prereq info so stay unlocked.
   - DONE: colors. Uses **literal hex** from `research/gameface-design-tokens.md`
     (NOT `var(--color-*)` — Gameface drops the whole declaration on an
     unresolved var, which is what made the bar render black; see gotcha). Tick
     color is state-driven (affordable / locked / idle).
   - DONE: **real in-game icons** (img:// loads in our injected doc). Module &
     vehicle ticks, header category icon, field-mod roman-numeral hexagons, elite
     badge. Icon paths + sizing in the "Icons" section below.
   - DONE: **field-mod level tier cap** + **researched/total counter**.
   - Owner DROPPED the "stable full-scale / completed-base bar" idea; keep the
     remaining-only view. Don't revisit unless re-raised.
   - STILL TODO: real hover **tooltips** (name + XP) — blocked by `pointer-events:
     none` on the root; either enable pointer events on ticks (watch for stealing
     clicks from the 3-D hangar) or wire WoT's ViewModel tooltip manager. Also
     fixes the empty field-mod tick names (see gotcha). Final **position/size**
     tuning against the live hangar (current: `top: 190rem`).
3. **Finalize packaging & docs** (Task): remove the loose `res_mods` gameface
   overlay before a clean ship verification (it shadows the packaged assets — see
   gotcha); `meta.xml` name/id (consider
   `com.drizzer14.research_progress` / "Research Progress"); declare OpenWG Gameface
   as a required dependency in README; deprecate `build/deploy_dev.py` (loose
   res_mods does not load in 2.3) pointing to `deploy_wotmod.py`; document the debug
   mod; build the distributable.

## Icons & field-mods (this session — verified in-game)
Data flow: `engine_adapter` reads icon URLs + field-mod levels → domain `Tick`
(`icon`, `level`, `category`) and `ResearchProgressModel` (`fieldmods_done/total`,
`vehicle_class`) → `TickVM`/`ResearchVM` → JS renders.

- **Tech-tree tick `category` carries the unlock kind** (`"vehicle"` | `"module"`),
  not a generic `"techtree"`. JS adds `wg-cat-<category>`.
- **Icon URLs (img://), read off the live item objects:**
  - module unlock → `item.icon` = generic module-type glyph,
    `img://gui/maps/icons/modules/{chassis,engine,tower,gun,radio}.png` (48×48).
  - vehicle unlock → `item.icon` = framed tech-tree-node icon (~160×100). **NOT
    `iconSmall`** (124×31 carousel contour — cropped edge-to-edge, looks "cut off").
  - header category → `img://gui/maps/icons/hangar/vehicleMenu/large/{research,
    fieldModification}.png` (64×64), keyed by mode in JS (`CAT_ICON`).
  - elite badge (COMPLETE) → `img://gui/maps/icons/vehicleTypes/md/<class>_elite.png`
    — pre-composed class+elite art; map `veh.type` '-'→'_' (`AT-SPG`→`AT_SPG`).
- **Render icons as `background-image` + `background-size:contain`** on a div, NOT
  `<img>` — Gameface ignores `object-fit` and CLIPS an `<img>` to its box (and
  `width:auto` collapses to 0). background-size:contain scales aspect-correct.
- **Field mods (post-progression), read via `veh.postProgression.iterOrderedSteps()`:**
  each step has `getLevel()` (1..N → roman numeral), `isReceived()`, `getPrice().xp`,
  and a typed `action`. Two kinds: **leveled mods** (`FeatureModItem`/`SimpleModItem`/
  `RoleSlotModItem`, cost `price.xp`, one per level → hexagon ticks) and **multi-mod
  choice slots** (`MultiModsItem`, `price.xp==0` → excluded from bar AND counter).
  The tree always lists **8 levels + 5 multi-mods regardless of tier**; only the
  per-level XP scales (T6 3500 / T8 11500 / T10 28000). Clamp to the tier cap:
  `max_level(tier)` (VI–VII=5, VIII=6, IX=7, X+=8 — **XI unverified**).
- **Counter** = researched / total LEVELED field mods within the cap (`fieldmods_done
  / fieldmods_total`); multi-mods are not counted.

## Gotchas / lessons (don't relearn these)
- **Gameface drops a whole CSS declaration on an unresolved `var()`** — it does NOT
  honor the hex fallback in `var(--x, #hex)`. Every color was a `var()`, so the bar
  rendered black. Fix: literal hex only. Custom properties are effectively unusable
  in our injected document.
- **Gameface ignores `object-fit` and clips `<img>` to its box; `width:auto`→0.**
  Use a div with `background-size:contain`. `clip-path: polygon(...)` DOES work
  (the field-mod hexagons use it).
- **Hot-reload loop for JS/CSS-only changes (no relaunch):** `tools/dev/
  sync_gameface.py "<install>" 2.3.0.1` copies the gameface assets into the
  `res_mods` overlay, then in-game switch to another screen and back to the Garage —
  the hangar sub-view document re-fetches them. Python (mount/data) changes still
  need build+deploy+relaunch via `deploy_wotmod.py`. **After every `deploy_wotmod`,
  re-run `sync_gameface`** or the (now stale) overlay shadows the fresh package.
  **Remove the overlay before a clean ship-verification** (`res_mods/2.3.0.1/gui/
  gameface/mods/drizzer14/`).
- **Wrong client trap:** the StranikS-Scan default branch is **MirTankov/Lesta RU**,
  a different client (it has "Paragons", lacks `RandomHangar`). Use branch **`2.3`**
  (EU). "Paragons / elite milestones / level-150" do **not** exist in EU — the elite
  feature was dropped; v1 is the XP-driven bar.
- **WoT 2.3 loads only `.wotmod`** from `mods/<version>/`; `res_mods` outranks it, so
  a stale loose copy SHADOWS the package and the client silently ignores the mod.
  Always deploy via `deploy_wotmod.py` (auto-cleans), with the **client closed**.
- **`g_currentVehicle.onChanged` is a STRONG-ref delegate `list`** (not a weak-ref
  Event — the earlier `1e11b90` theory was wrong). The real trap: WoT tears down and
  rebuilds the hangar space on **battle exit**, repopulating that list with WG's own
  presenters while dropping any handler that doesn't re-subscribe. WG presenters
  re-add themselves on each hangar load; so must we. `install_vehicle_listener()` is
  self-healing (re-adds iff not in the list) and is called from the patched
  `_onLoading` on every mount. Don't go back to a once-only subscription.
- **Field-mod tick names are empty** — the `step.action` label lookup in
  `engine_adapter._step_label` doesn't resolve; fix when wiring tooltips.
- **Special "7×7" tanks** (T57 Heavy 7×7, etc.) use a hangar without
  `HangarVehicleParamsPresenter`, so the bar won't mount there. If that matters,
  pick a more universally-present sub-view as the inject host (or accept the gap).
- Mod module isn't importable as `mod_wgmod` (loader namespace); the bridge module
  IS importable (`wgmod_research.bridge.gameface_bridge`) — use it for REPL pokes.
- The session **scratchpad is ephemeral**; durable dev tools now live in `tools/dev/`.
  Re-clone the EU decompiled source when needed (see tools/dev/README.md).
