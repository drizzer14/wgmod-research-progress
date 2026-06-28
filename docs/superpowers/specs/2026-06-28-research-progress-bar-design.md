# Design: Garage Research-Progress Bar (WoT mod)

_Date: 2026-06-28 · Status: approved for planning_

## 1. Goal

Add a progress bar to the World of Tanks Garage that shows the **research progress
of the currently selected vehicle**. The bar lays research milestones ("ticks")
on a single XP axis, fills toward them with the player's XP, and explains each
tick with an icon and a tooltip. It uses the game's design-system fonts and colors.

Target client: WoT 2.x (Gameface UI era, 2026). Runtime: Python 2.7 / BigWorld.

## 2. Scope

In scope (all in v1):
- Tech-tree research (modules + next vehicles)
- Field modifications (post-progression, tiers VI–X)
- Tier XI upgrade nodes
- "Potential Tier XI" target for Tier X vehicles
- Elite-system milestones (badge color/shape changes), for **any** elite vehicle

Out of scope:
- Configuration/settings UI (possible later via ModsSettings API)
- Any non-research garage information
- Battle-screen UI

## 3. Bar model

- **Single XP axis.** Every tick — research target or elite milestone — is placed
  by its **cumulative XP** value on one horizontal axis.
- **Remaining only.** Left edge = the progress already behind the player (spent or
  earned baseline); right edge = the end of the active mode's scope. Only
  not-yet-reached points get ticks.
- **One continuous bar.** When more than one category is active (e.g. field mods +
  Tier XI), all their ticks sit on the same bar, ordered by cumulative XP and
  coded by category (icon/color).
- **Stacked fill.** In research modes the fill is the player's spendable XP shown
  as two stacked segments: earned **vehicle XP** first, then **global Free XP** on
  top. Ticks at or below the fill are "affordable" and are visually distinguished.

### Tick model

Each tick carries:
`{ xpPosition, category, icon, name, xpGained, xpRequired, affordable, completed }`

- `xpPosition` — cumulative XP location on the axis
- `category` — `techtree | fieldmod | tierXI | potentialXI | elite`
- `icon` — module / vehicle / field-mod / milestone icon
- `name`, `xpGained`, `xpRequired` — tooltip content
- `affordable` — fill ≥ position (research modes)
- `completed` — already unlocked/reached (normally filtered out by "remaining only")

## 4. Mode state machine

Evaluated for the selected vehicle, in priority order.

### Tiers I–X

| Vehicle state | Bar measures | Scale (left → right) | Fill |
|---|---|---|---|
| Not elite | Tech tree: remaining modules + next vehicle(s) | baseline → total XP for all remaining unlocks | spendable XP (vehicle + free, stacked) |
| Elite; field mods and/or a Tier XI target remain | Field modifications **+** Tier XI unlock (*or* potential Tier XI for a Tier X with none yet) — one continuous bar | baseline → total remaining XP across both | spendable XP |
| Elite; field mods done; no Tier XI target left | Elite-system milestones | baseline → last milestone (cap) | earned elite progress |

### Tier XI

| Vehicle state | Bar measures | Scale (left → right) | Fill |
|---|---|---|---|
| Upgrades incomplete | Tier XI upgrade nodes | cumulative XP earned → last upgrade | spendable XP (vehicle + **free** — nodes accept free XP) |
| Upgrades complete | Elite-system milestones **+** special Tier XI rewards | baseline → **level 150** (last reward; then it becomes the final elite level) | earned elite progress |

### Fill semantics

- **Research modes** (tech tree, field mods, Tier XI unlock, Tier XI nodes): fill =
  what the player can **spend now** = vehicle unspent XP + global Free XP, stacked.
- **Elite-milestone modes**: fill = XP **earned** toward the milestones. Free XP does
  **not** apply — elite levels are earned on the vehicle, not bought.
- The elite system applies to **all** elite vehicles, not only Tier XI. The milestone
  cap is tier-dependent (`level 150` for Tier XI; the last badge milestone otherwise).

## 5. Architecture

Two clean layers with a thin adapter between them, so the fragile engine access is
isolated and the XP logic is testable off-game.

1. **Domain layer (pure, testable, no engine imports).** A `ResearchProgressModel`
   builder. Input: a normalized vehicle snapshot. Output:
   `{ mode, scaleMin, scaleMax, fillSpendable, fillEarned, ticks[] }`.
   The mode state-machine and all XP math live here. Per-category sub-resolvers —
   `TechTree`, `FieldMods`, `TierXI` (nodes + potential), `EliteSystem` (milestones) —
   each emit ticks; the builder concatenates and orders them per §4.

2. **Engine adapter (thin, PC-only).** The only code that touches `g_currentVehicle`,
   `itemsCache`, `descriptor.type.unlocksDescrs`, post-progression, elite data, etc.
   It reads the live client and produces the snapshot the domain layer consumes.
   Centralizing this keeps version-sensitive symbol access in one small file.

3. **Hook + bridge layer.** Monkey-patch `RandomHangar._initialize` to mount the bar
   element and capture its ViewModel; subscribe to `g_currentVehicle.onChanged` to
   recompute; push the model via `viewModel.transaction()`. All hooks installed in
   `init()` and cleanly removed in `fini()`.

4. **Gameface view** (`gui/unbound/`, HTML/CSS/JS). Renders the axis, the two stacked
   fill segments, the category-coded ticks with icons, and tooltips, using the game's
   design-system fonts and colors.

### Data flow

`vehicle selected → g_currentVehicle.onChanged → adapter builds snapshot →
domain builds model → viewModel.transaction() → Gameface re-renders`

## 6. Data sources (and confidence)

From feasibility research (symbol names knowledge-based; **must be verified against
the decompiled source** — see §9):

- **Selected vehicle + change event:** `CurrentVehicle.g_currentVehicle` (`.item`,
  `.isPresent()`, `.onChanged`). _High._
- **Vehicle XP / Free XP:** `vehicle.xp`; `itemsCache.items.stats.freeXP` (via
  `dependency.instance(IItemsCache)`). _High._
- **Modules / next vehicles / costs:** `vehicle.descriptor.type.unlocksDescrs`
  (`(position, intCD, xpCost, *prereqs)`); unlocked set `itemsCache.items.stats.unlocks`;
  resolve items via `itemsCache.items.getItemByCD(intCD)`. _High (shape), medium (exact tuple order)._
- **Elite flag:** `vehicle.isElite`. _High._
- **Field modifications / Tier XI nodes:** the client "post-progression" system
  (`post_progression_common`, `POST_PROGRESSION_ALL_PRICES`, `vehPostProgression`);
  per-vehicle state via a `postProgression` accessor on the gui_items vehicle.
  _Exists: high; exact API: medium-low._
- **Tier XI / potential Tier XI:** tier as `level == 11`; successors via the unlock
  graph; potential = no level-11 successor present. _Medium._
- **Elite-system milestones (all tiers):** least-certain data point; **feasibility
  to confirm in source.** Tier XI cap = level 150.

## 7. UI integration

- **Dependencies (bundled / required):** OpenWG Gameface (hard dependency — client
  aborts on startup if a required-but-missing Gameface mod is referenced). ModsList /
  ModsSettings API only if/when a menu button or settings panel is added (not v1).
- **Assets:** HTML/CSS/JS in `res_mods/<version>/gui/unbound/`.
- **Mount pattern:** patch `gui.impl.lobby.hangar.random.random_hangar.RandomHangar._initialize`
  (verify class path against the installed build), attach the bar, capture the
  ViewModel, update via `with self.viewModel.transaction() as tr: ...`.
- **Design system:** use the game's fonts and color tokens; ticks color-coded by category.

## 8. Error handling

- Guard `g_currentVehicle.isPresent()` before any read.
- Each category resolver is wrapped so a failure (most likely in post-progression /
  elite reads) **degrades gracefully**: that category is skipped, the rest of the bar
  still renders, and the hangar never crashes (`LOG_CURRENT_EXCEPTION`).
- Centralize patched class paths; fail safe (log + no-op) if a symbol is missing after
  a client patch.
- Always unsubscribe / restore originals in `fini()` to survive mod reloads.

## 9. Testing & verification

- **Verification spike (first task):** clone `StranikS-Scan/WorldOfTanks-Decompiled`
  and grep the real symbols (`CurrentVehicle`, `gui/shared/gui_items/Vehicle.py`,
  `post_progression_common`, unlocks, elite/level-11); read `wot-public-mods/battle-hits`
  and `ANIALLATOR114/extended-interface-scaling` for the real ViewModel-injection and
  dependency-declaration patterns. Confirm the medium/low-confidence items in §6 before
  building on them.
- **Unit tests (Mac):** domain layer against fake snapshots covering every state —
  non-elite, elite + field mods, Tier X + potential XI, Tier XI partial, Tier XI complete,
  elite-milestone fallback.
- **Manual (PC):** adapter + view verified in-game across the same representative
  vehicles; `wot-debugserver` REPL to confirm live data shapes.

## 10. Distribution

- Dev: `build/deploy_dev.py` copies `src/res` into `res_mods/<version>` for live testing.
- Release: `build/build_wotmod.py` (Python 2.7.18) compiles `.pyc` + packages a stored
  `.wotmod`. Players also need the OpenWG Gameface dependency installed.

## 11. Open / verification items

1. Exact `unlocksDescrs` tuple field order (inspect one entry at runtime).
2. Post-progression accessor name + step object fields (state, price, currency).
3. Whether Tier XI nodes truly reuse the post-progression API (very likely; confirm).
4. Elite-system data for non-Tier-XI vehicles: readable? milestone thresholds + caps.
5. Current hangar view class path in the installed build.
6. ViewModel field/command syntax (confirm from example mods).
