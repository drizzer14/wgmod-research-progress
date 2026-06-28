# Phase 2 Handoff — WoT Research-Progress Bar

**Audience:** a fresh Claude Code install on the Windows PC, continuing this mod. You
have NO prior conversation context — everything you need is in the repo. Read this
file top to bottom first.

## TL;DR

- **Phase 1 (the pure domain layer) is DONE, tested (24 passing), and on `main`.**
- **Phase 2 (engine integration + UI) remains and must run on this Windows PC** —
  World of Tanks only runs on Windows.
- Start with **Task 1 (verification spike)** in the plan; it confirms the exact game
  API symbols that Phase 2 depends on. Do NOT skip it.

## Read these, in order

1. `docs/superpowers/specs/2026-06-28-research-progress-bar-design.md` — the design (what the bar does).
2. `docs/superpowers/plans/2026-06-28-research-progress-bar.md` — the implementation plan (your task list). Phase 2 = Task 1 + Tasks 9–14.
3. `RESEARCH.md` — WoT modding background (engine, file structure, packaging, Gameface).

## Working rules (the owner's preferences — follow them)

- **Single branch.** Commit directly on `main`. Do NOT create branches or git worktrees unless explicitly asked.
- **Commit trailer.** End every commit message with:
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
- **Workflow:** code is authored on a Mac and tested here on the PC. The domain layer is engine-free and already complete; your job is the Windows/in-game half.
- If the **superpowers** skill suite is installed, the plan is built for `subagent-driven-development` (fresh subagent per task + spec & quality review). If it is NOT installed, just execute the plan tasks manually in TDD order, one commit per task.

## What Phase 1 delivered (don't rebuild it)

Pure, engine-free, Python 2/3-compatible domain layer under
`src/res/scripts/client/wgmod_research/domain/`:
- `types.py` — `VehicleSnapshot` (the input contract), `Tick`, `ResearchProgressModel`, `Mode`, `UnlockItem`, `ProgressionStep`, `Milestone`.
- `resolvers/{techtree,fieldmods,tierxi,elite}.py` — turn a snapshot into ticks.
- `builder.py` — `build_model(snapshot)` = the mode state machine.
- Tests in `tests/` (run `python3 -m pytest` → expect **24 passed**; `pip install pytest` if needed).

**The seam between Phase 1 and Phase 2 is `VehicleSnapshot`.** Your engine adapter (Task 9)
reads the live client and produces a `VehicleSnapshot`; `build_model()` does the rest.

### Snapshot contract (what the adapter MUST provide)
- All XP fields are **real ints, never `None`** (the domain does no coercion and will raise on `None`).
- Lists (`tech_unlocks`, `field_mod_steps`, `tierxi_nodes`, `elite_milestones`) in **natural progression order**.
- `elite_milestones` carry **cumulative XP thresholds**; the highest is the cap.
- See the per-field docstrings in `types.py:VehicleSnapshot` for exact meanings.

## The design in one screen (so you needn't re-derive it)

- **Single XP axis, "remaining only," one continuous bar.** Ticks = research targets / elite milestones positioned by cumulative XP.
- **Mode state machine** (`build_model`):
  - Tiers I–X, not elite → **TECH_TREE** (modules + next vehicles).
  - Tiers I–X, elite, field mods and/or a (real or potential) Tier XI successor remain → **RESEARCH_PLUS_TIERXI** (one bar, field-mod ticks then successor stacked).
  - Tiers I–X, elite, nothing left → **ELITE** (milestone ticks).
  - Tier XI, upgrades remain → **TIERXI_NODES** (scale starts at earned XP).
  - Tier XI, upgrades done → **ELITE_PLUS_TIERXI_REWARDS** (milestones to cap, e.g. level 150).
- **Fill:** research modes → `fill_spendable` = vehicle unspent XP + global free XP (both segments always drawn). Elite modes → `fill_earned` = earned XP only (free XP does NOT count).
- **Clamp (decided):** elite `scale_max` is anchored to the cap and `scale_min`/`fill_earned` are clamped to it, so a maxed vehicle renders **full**. The view should treat a `scale_min == scale_max` range as 100% (guard divide-by-zero).

## Phase 2 task order (from the plan — full text/code is in the plan file)

1. **Task 1 — Verification spike (DO FIRST).** Clone `https://github.com/StranikS-Scan/WorldOfTanks-Decompiled`, grep the real symbols, read reference mods, and write `docs/superpowers/research/decompiled-findings.md`. The plan's Phase 2 tasks contain `⟨confirm⟩` markers — those are the symbols this spike pins down. **Gate:** if elite-level/milestone data is NOT readable for non-Tier-XI vehicles, stop and tell the owner (the elite requirement may need to narrow to Tier XI).
2. **Task 9 — Engine adapter** (`wgmod_research/adapter/engine_adapter.py`): live client → `VehicleSnapshot`, each read wrapped in try/except → safe default (graceful per-category degradation, spec §8).
3. **Task 10 — Hangar hook + entry point**: rename `mod_wgmod.py` → `mod_research_progress.py`; patch `RandomHangar._initialize`; subscribe `g_currentVehicle.onChanged`.
4. **Task 11 — ViewModel bridge**: adapter → `build_model` → `viewModel.transaction()`.
5. **Task 12 — Gameface view** (`res/gui/unbound/research_progress/`): render axis, stacked fill, category-coded ticks, icons, tooltips, design-system fonts/colors. **Ask the owner** whether `prereqs_met` / `completed` should drive tick styling (deferred decision). Render the clamp as 100% when range is zero-width.
6. **Task 13 — Dependencies + packaging**: OpenWG Gameface (hard dependency); build `.wotmod` via `build/build_wotmod.py` (needs **Python 2.7.18**).
7. **Task 14 — In-game verification matrix**: test every mode on a representative vehicle; confirm graceful degradation.

## Key technical facts (from research — VERIFY in the Task 1 spike)

- **UI path:** WoT 2.x Garage is Coherent Gameface. Pattern: monkey-patch `gui.impl.lobby.hangar.random.random_hangar.RandomHangar._initialize` (store original, restore in `fini()`), put HTML/CSS/JS in `res_mods/<version>/gui/unbound/`, push data via `with view.viewModel.transaction() as tr: ...`.
- **Selected vehicle + change event:** `from CurrentVehicle import g_currentVehicle` → `g_currentVehicle.isPresent()`, `g_currentVehicle.item`, `g_currentVehicle.onChanged`.
- **Data:** `itemsCache = dependency.instance(IItemsCache)`; `itemsCache.items.stats.freeXP`, `.unlocks`; `vehicle.xp`, `vehicle.isElite`, `vehicle.descriptor.type.unlocksDescrs`. Field mods / Tier XI nodes via the client "post-progression" system (`post_progression_common`). Tier = `vehicle.level` (11 for Tier XI).
- **Dependencies:** OpenWG Gameface (required; a missing required Gameface mod can abort client startup). ModsList / ModsSettings API only if you add a menu button / settings panel (not in v1).
- **Reference mods to study:** `wot-public-mods/battle-hits` (lobby Gameface panel), `ANIALLATOR114/extended-interface-scaling` (dependency declaration + build), `wotstat/wotstat-analytics` (reading live vehicle data).
- **Debugging:** `juho-p/wot-debugserver` gives a live Python REPL into the running client — ideal for confirming data shapes before wiring the adapter.

## Things to get from the owner on the PC

- **WoT install path** and **current client version** (needed for `build/deploy_dev.py "<path>" <version>` and the `mods/<version>` folder).
- Git auth on this machine (this is a fresh PC; set up your own credentials/keys for `git@github.com:drizzer14/wgmod-research-progress.git`).
- The `prereqs_met` / `completed` styling decision (Task 12).

## First concrete steps on the PC

1. `git pull` (or clone) the repo.
2. Read the three docs listed above.
3. `python3 -m pytest -q` → confirm **24 passed** (domain layer healthy).
4. Begin **Task 1 (verification spike)**.
