# Session Handoff — Research-Progress Bar (Phase 2, in-game working)

_Date: 2026-06-28. Supersedes the original PHASE2-HANDOFF.md, which predates the
EU-vs-RU client correction. Read tools/dev/README.md for the dev loop._

## TL;DR — where we are
The mod **works in-game** on WoT **EU 2.3.0.1**. A research-progress bar renders in
the Garage from live data: tech-tree, field-modifications, and a "Fully researched"
complete state. Live refresh on tank-switch is verified, including the battle-exit
cycle (the listener self-heals — see gotchas). Locked/prereqs-unmet ticks are done
and verified. (Current HEAD: `a91b0d4`.)

**IMMEDIATE NEXT STEP (do first):** the native-Gameface restyle (`a91b0d4`) is
committed and **deployed** but **NOT yet visually verified in-game** — the deploy
happened at end of session after the client closed. Relaunch and confirm in the
hangar:
- Bar uses the game font and colors (see `research/gameface-design-tokens.md`):
  green vehicle-XP fill, tan free-XP segment, **bright near-white** affordable
  ticks, **dim gray** locked ticks, full **green** bar when "Fully researched".
- Sanity-check that the `var(--color-*)` tokens actually resolve in the hangar
  document (if a token were out of scope the hex fallback kicks in, so it should
  look right regardless — but confirm the green/tan/white/gray read as intended).
- If any color reads wrong against the live hangar, tweak `WGModResearch.css`
  (owner already chose: locked=gray, vehicle fill=green).

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
1. **Verify the native restyle in-game** (immediate, see TL;DR) and the full mode
   matrix (graceful degradation if a read fails).
2. **Visual polish** (Task: design system).
   - DONE (`7d3fe8c`, verified in-game on the Lago): locked (prereqs-unmet) ticks.
     `UnlockItem.prereqs_met` → `Tick.locked` → `TickVM "locked"` → JS `wg-locked`.
     Field mods carry no prereq info so stay unlocked.
   - DONE (`a91b0d4`, deployed, pending visual check): native Gameface fonts/colors
     via `:root` design tokens. See `research/gameface-design-tokens.md` for the full
     token table + mapping. Tick color is now state-driven (affordable / locked /
     idle), not category-driven — a bar is all-tech-tree OR all-field-mods, so the
     label already disambiguates and per-tick category color was redundant.
   - Owner DROPPED the "stable full-scale / completed-base bar" idea (ticks staying
     put as you progress); keep the current remaining-only view. Don't revisit unless
     re-raised.
   - STILL TODO: real hover **tooltips** (name + XP) — blocked by `pointer-events:
     none` on the root; either enable pointer events on ticks (watch for stealing
     clicks from the 3-D hangar) or wire WoT's ViewModel tooltip manager. Also fixes
     the empty field-mod tick names (see gotcha). Category **icons**; final
     **position/size** tuning against the live hangar.
3. **Finalize packaging & docs** (Task): `meta.xml` name/id (consider
   `com.drizzer14.research_progress` / "Research Progress"); declare OpenWG Gameface
   as a required dependency in README; deprecate `build/deploy_dev.py` (loose
   res_mods does not load in 2.3) pointing to `deploy_wotmod.py`; document the debug
   mod; build the distributable.

## Gotchas / lessons (don't relearn these)
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
