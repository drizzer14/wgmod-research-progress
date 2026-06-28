# Task 1 — Decompiled-Client Verification Spike (findings)

_Date: 2026-06-28 · Author: Claude Opus 4.8 (1M context) on the Windows PC._

**Source verified against:** `StranikS-Scan/WorldOfTanks-Decompiled` (shallow clone), reference
mods `wot-public-mods/battle-hits` and `ANIALLATOR114/extended-interface-scaling`.
All module paths below are relative to the decompiled source root
`source/res/scripts/`.

> **⚠️ GATE RESULT: FAIL (elite-system milestones).** The "elite-system milestones on a
> cumulative-XP axis" feature (spec §2/§4, design §6 item "Elite-system milestones") is
> **not backed by readable client data** for non-Tier-XI vehicles — and not even for Tier XI
> in the cumulative-XP form the design assumes. See **§E** and **"Gate & required decision"**
> at the end. Phase 1 (domain layer) is unaffected; Phase 2 needs a scope decision before
> the adapter/UI are built.

---

## A. Selected vehicle & change event — CONFIRMED

**Module:** `client/CurrentVehicle.py`

- `g_currentVehicle` is a module-level instance of `_CurrentVehicle(_CachedVehicle)`.
- `isPresent()` (on `_CachedVehicle`): `return self.item is not None`. **CONFIRMED.**
- `.item` returns a `gui.shared.gui_items.Vehicle.Vehicle` or `None`:
  ```python
  @property
  def item(self):
      return self.itemsCache.items.getVehicle(self.__vehInvID) if self.__vehInvID > 0 else None
  ```
- `onChanged` is a plain `Event` (from `Event.py`, **not** a SafeEvent), created in
  `_CachedVehicle.__init__`. Subscribe/unsubscribe with `+=` / `-=`; it is fired by calling it.
  A separate `onChangeStarted` also exists.
  ```python
  self.onChanged = Event(self._eManager)
  ...
  g_currentVehicle.onChanged += self.__onCurrentVehicleChanged   # real consumer in hangar.py
  ```

**Adapter impact:** the planned `g_currentVehicle.isPresent()/.item/.onChanged += _refresh`
pattern (Task 9/10) is correct as written.

---

## B. Vehicle gui_item & ItemsRequester/stats — CONFIRMED (with name corrections)

**Modules:** `client/gui/shared/gui_items/Vehicle.py`,
`client/gui/shared/utils/requesters/ItemsRequester.py`,
`client/gui/shared/utils/requesters/statsrequester.py`,
`client/gui/shared/items_cache.py`, `client/skeletons/gui/shared/__init__.py`.

| Symbol | Verdict | Notes |
|---|---|---|
| `vehicle.xp` | CONFIRMED | property; unspent accumulated vehicle XP (slot `_xp`, from `stats.vehiclesXPs`). |
| `vehicle.isElite` | CONFIRMED | `not vehDescr.type.unlocksDescrs or intCD in stats.eliteVehicles`. |
| `vehicle.isFullyElite` | CONFIRMED | elite **and** every unlock target already in `stats.unlocks`. |
| `vehicle.level` | CONFIRMED | returns `descriptor.type.level`, **range 1..11** (Tier XI = 11). |
| `vehicle.getUnlocksDescrs()` | CONFIRMED | generator yielding `(unlockIdx, xpCost, intCD, set(prereqs))` — see §C. Use this, not raw tuple access. |
| `vehicle.postProgression` | CONFIRMED | lazy property → `PostProgressionItem` (see §D). camelCase only. |
| `vehicle.userName` / `icon` / `iconSmall` | CONFIRMED | `icon` resolves a WG `R.images...` resource. |
| `item.itemTypeID` / `itemTypeName` | CONFIRMED | inherited from base gui_item; `'vehicle'` for vehicles. |
| `GUI_ITEM_TYPE.VEHICLE` | CONFIRMED | `client/gui/shared/gui_items/__init__.py`, `VEHICLE` = index 0; modules = CHASSIS/TURRET/GUN/ENGINE/FUEL_TANK/RADIO. |
| `itemsCache.items.stats.freeXP` | CONFIRMED | `statsrequester.py`; account-global free XP (non-negative, wallet-gated; raw = `actualFreeXP`). |
| `itemsCache.items.stats.unlocks` | CONFIRMED | a **set** of unlocked intCDs (default `set()`). |
| `itemsCache.items.getItemByCD(cd)` | CONFIRMED | param named `typeCompDescr`; returns `Vehicle` or a simple FittingItem. |
| `dependency.instance(IItemsCache)` / `dependency.descriptor(IItemsCache)` | CONFIRMED | both forms used in client code. |

**NOT-FOUND / corrections:**
- `getPerLevelXp()` — **does not exist.** Per-unlock XP cost is `xpCost` from `getUnlocksDescrs()`.
- `post_progression` (snake_case) on the vehicle — **does not exist**; the accessor is camelCase `postProgression`.

```python
# Vehicle.py — elite flags
self._isElite = not vehDescr.type.unlocksDescrs or self.intCD in self._proxy.stats.eliteVehicles
self._isFullyElite = self.isElite and not any(
    (data[1] not in self._proxy.stats.unlocks for data in vehDescr.type.unlocksDescrs))

# statsrequester.py
@property
def freeXP(self):     return max(self.actualFreeXP, 0)
@property
def unlocks(self):    return self.getCacheValue('unlocks', set())
```

---

## C. `unlocksDescrs` tuple field order — CONFIRMED (assumed order was WRONG)

**Module:** `common/items/vehicles.py` (build/convert), `client/gui/shared/gui_items/Vehicle.py` (consume).

The spec §11 assumption `(position, intCD, xpCost, *prereqs)` is **incorrect**. The real
stored tuple is:

```
unlocksDescrs entry = (xpCost, intCD, *prereqIntCDs)
  index 0 = xpCost (int)
  index 1 = intCD  (compact descriptor of the unlocked item)
  index 2+ = prerequisite intCDs (recursively expanded)
```

There is **no** position/level field inside the tuple. Confirmed by the converter
(`__convertAndValidateUnlocksDescrs`, `destList.append((descr[0], compactDescr))`) and by
the consumer:

```python
def getUnlocksDescrs(self):
    for unlockIdx, data in enumerate(self.descriptor.type.unlocksDescrs):
        yield (unlockIdx, data[0], data[1], set(data[2:]))   # (idx, xpCost, intCD, prereqs)
```

**Module vs. vehicle unlock:** parse the intCD —
`parseIntCompactDescr(intCD)[0] == ITEM_TYPES.vehicle (==1)` → a vehicle (next tank);
`2..7` → a module (chassis/turret/gun/engine/fuelTank/radio). Helpers
`parseIntCompactDescr` / `makeIntCompactDescrByID` live in `common/items/__init__.py`
(imported by `vehicles.py`), not in `vehicles.py`.

**Adapter impact (Task 9):** the `_read_tech_unlocks` skeleton in the plan reads
`props[2], props[1]` for `(xp_cost, int_cd)` — **wrong**. Use `vehicle.getUnlocksDescrs()` and
take `xpCost` (2nd yielded) + `intCD` (3rd yielded); decide `kind` via `parseIntCompactDescr`.
`researched = intCD in stats.unlocks`.

---

## D. Field modifications / Tier XI nodes = the **post-progression** system — CONFIRMED (one system; no separate Tier-XI node API)

**Modules:** `common/post_progression_common.py`,
`common/post_progression_prices_common.py`,
`common/items/components/post_progression_components.py`,
`client/gui/veh_post_progression/models/progression.py` (`PostProgressionItem`),
`client/gui/veh_post_progression/models/progression_step.py` (`PostProgressionStepItem`).

- Accessor: `vehicle.postProgression` → `PostProgressionItem`
  (`itemsCache.items.getVehPostProgression(intCD, descr.type)`). Gated on elite
  (`VEH_NOT_ELITE`). Methods: `getStep(id)`, `iterOrderedSteps()`, `iterUnorderedSteps()`,
  `getCompletion()` (`EMPTY`/`PARTIAL`/`FULL`), `getFirstPurchasableStep(balance)`.
- Step = `PostProgressionStepItem`: `stepID`, `getState()` →
  `PostProgressionStepState` (`RESTRICTED`/`LOCKED`/`UNLOCKED`/`RECEIVED`), `getLevel()`,
  `getNextStepIDs()`, `getParentStepID()`, `getPrice()` → `ExtendedMoney`,
  `mayPurchase(balance, ...)`.
- **Price model:** per-step, **not cumulative**. `getPostProgressionPrice(priceTag, vehType)`
  returns a single-currency dict, e.g. `{'xp': 12000}`. Tree-unlock steps are forced to
  `xp` (`ALLOWED_CURRENCIES_FOR_TREE_STEP = {'xp'}`); buying the 2nd pair-modification is
  `credits`. Price keyed by `priceTag → vehicleLevel → currency`.
- **Tier XI nodes:** there is **no separate or parallel Tier-XI node system** in the client
  code. Field Modifications *are* the post-progression tree (action types `MODIFICATION` /
  `PAIR_MODIFICATION` / `FEATURE`); a Tier-XI tree would be more steps in the same
  `ProgressionTree`/`TreeStep` data, not a different API. (Confidence: HIGH no distinct code
  branch exists; whether WG ships Tier-XI content through this tree is a `trees.xml` data
  question — data files are not in the decompiled `scripts/` tree.)

**Domain impact:** the domain `ProgressionStep` models a *cumulative* `xp_cost` layout. The
real data is a per-step price **graph** (parent/child), state-driven, not a flat cumulative
list. The adapter must (a) walk steps in order, (b) read `getPrice()` per step (xp only for
unlock steps), (c) map state→`unlocked`. Cumulative positioning then happens in the resolver
as today. No engine `xp_gained`/cumulative threshold is provided — it is derived.

---

## E. Elite-system milestones — **NOT-FOUND (GATE FAIL)**

**Modules checked:** `client/gui/shared/gui_items/Vehicle.py`,
`client/account_helpers/stats.py`, `client/gui/shared/utils/requesters/statsrequester.py`,
`common/post_progression_common.py`, `common/paragons_common.py`,
`client/account_helpers/paragons.py`, `common/constants.py`.

Findings:
1. **"Elite" is a plain boolean** for all tiers. `isElite` / `isFullyElite` are backed by the
   `eliteVehicles` **set** (membership only — no XP, no level, no thresholds) and by
   module-unlock counts (`getEliteStatusProgress()` returns *counts*, not XP).
2. **No per-vehicle cumulative-XP milestone/level ladder exists.** Searches for
   `mastery`/`prestige`/`milestone`/`badge`/graded levels return only unrelated systems
   (dossier mastery marks, crew role levels, battle-pass badges, customization prestige).
3. **There is no "level 150."** Every `150` in the tree is environment/achievement noise.
   The Tier-XI cap is simply `MAX_VEHICLE_LEVEL = 11` (`common/constants.py:1599`) — i.e. a
   **tier**, not an elite level.
4. **Tier XI progression = Paragons** (`common/paragons_common.py`), and its "levels" come
   from **quest/chapter token progress** (`questsProgression.getLevel(tokenID, tokenCount)`),
   paid in `paragonsCoin`/access-points — **not cumulative vehicle XP**. It is restricted to
   specific branches (`V_11` entitlements), not "all elite vehicles."
5. `battle_royale_progression` is **not even shipped** in the decompiled `scripts/` tree
   (only string/resource accessors reference it). It is a game-mode progression, unrelated.

**Verdict:** the elite-milestone-on-a-cumulative-XP-axis concept (design §6, spec §4 elite
modes) has **no readable client data source**. It cannot be implemented as designed.

---

## F. UI mounting & ViewModel — CONFIRMED, but the planned approach is WRONG and must change

**Finding:** `gui.impl.lobby.hangar.random.random_hangar.RandomHangar` and its
`_initialize` **do not exist** in this client. The actual Garage hangar is the **Scaleform**
view `Hangar` at `client/gui/Scaleform/daapi/view/lobby/hangar/hangar.py`, whose lifecycle
hooks are `_populate` / `_dispose` — and it has **no** `getViewModel()`/`transaction()`
(those belong to the newer wulf `ViewImpl` views, e.g. `VehicleParamsView`).

**Correct pattern (from `battle-hits`, the OpenWG Gameface way):**
- Build your own wulf view + `ViewModel` (subclass `frameworks.wulf.ViewModel`; declare fields
  in `_initialize` via `_addStringProperty` / `_addArrayProperty(name, Array())` / `_addCommand`).
- Push data inside `with self.viewModel.transaction() as model:` using `setX(...)`; fill the
  ticks array with `getTicks().clear()` → per-row child `ViewModel` → `getTicks().addViewModel(child)`
  → `getTicks().invalidate()`.
- Register the view as a component into WG's factory:
  `ComponentSettings(VIEW_ID, InjectComponentAdaptor subclass, scope)` →
  `g_entitiesFactories.addSettings(...)`; resolve the layout with
  `openwg_gameface.ModDynAccessor("<itemID>")` passed as `layoutID=`.
- Assets: `res/.../gui/gameface/mods/<author>/<ViewName>/{*.html,*.css,*.js}`, bound via a
  `mods/configs/res_map/<ViewName>.json` (`type: Layout`, `impl: gameface`, `entrance`, `itemID`).
- Style with CSS custom properties in `:root`, reuse WG UI-kit class names, reference WG art
  via `url(R.images.gui.maps.icons.ui_kit...)`, size in `rem`.

**Dependency declaration & packaging (from `extended-interface-scaling`):**
- `.wotmod` = a ZIP with `meta.xml` at root + the `res/` tree; `.py` compiled to `.pyc`
  (Python 2.7) and only `.pyc` packaged. `meta.xml`: `<id>Author.Mod_Name</id>` + `<version>`
  + `<name>` + `<description>`; keep `id` stable across releases.
- OpenWG Gameface is a hard dependency: `battle-hits` imports `openwg_gameface` at module top
  and `sys.exit()`s the client if missing. Optional deps (ModsList/ModsSettings) are
  documented load-order + soft `hasattr`/`try-except` probes.

**Impact:** Tasks 10–13 must be rewritten around the OpenWG-Gameface component/res_map pattern
(not `RandomHangar._initialize` + a stock hangar ViewModel). The plan's `viewmodel_bridge`
still works conceptually — it just targets *our own* injected view's ViewModel.

---

## Spec §11 item-by-item resolution

| # | Open item | Result |
|---|---|---|
| 1 | `unlocksDescrs` tuple field order | **RESOLVED — §C.** `(xpCost, intCD, *prereqs)`; use `getUnlocksDescrs()`. |
| 2 | Post-progression accessor + step fields | **RESOLVED — §D.** `vehicle.postProgression`; per-step state + `getPrice()` (xp), graph-ordered, per-step (not cumulative). |
| 3 | Do Tier XI nodes reuse post-progression? | **RESOLVED — §D.** Yes, same system; no separate API. |
| 4 | Elite data for non-Tier-XI vehicles? caps? | **RESOLVED — §E. NOT AVAILABLE.** Elite is boolean; no cumulative-XP milestones; no level 150; Tier XI = Paragons (token-driven). **GATE FAIL.** |
| 5 | Current hangar view class path | **RESOLVED — §F.** Scaleform `Hangar` (`_populate`/`_dispose`); no `RandomHangar`. |
| 6 | ViewModel field/command syntax | **RESOLVED — §F.** wulf `ViewModel` + `transaction()` + `Array`/`addViewModel`/`invalidate`; mount via `g_entitiesFactories` + `openwg_gameface`. |

---

## Gate & required decision (STOP per plan Task 1 gate)

The plan's Task 1 gate says: *if elite-level/milestone data is NOT readable for non-Tier-XI
vehicles, STOP and report — the elite-system requirement may need to narrow to Tier XI.*
It does not just narrow to Tier XI: even Tier XI uses **Paragons** (quest tokens), not
cumulative vehicle XP, so the elite-milestone-on-XP-axis feature has no backing data anywhere.

**Options for the owner:**
- **(A) Drop elite milestones** from v1. Ship tech-tree + field-modifications + the real/
  potential Tier-XI successor on the XP axis (all XP-backed and confirmed). The domain `ELITE`
  / `ELITE_PLUS_TIERXI_REWARDS` modes stay in code but are never produced by the adapter.
- **(B) Reinterpret "elite" as Paragons** for Tier-X→XI branches: a *separate*, token-driven
  bar (not the cumulative-XP axis). New design + new resolver; larger scope.
- **(C) Show a flat "ELITE — fully researched" state** (boolean) with no milestone ticks when
  a Tier I–X vehicle is elite and has no field mods / successor left.

Other confirmed corrections that change Phase 2 regardless of the above:
- Tech-unlock reading must use `getUnlocksDescrs()` with `(xpCost, intCD)` order (§C).
- UI integration must use the OpenWG-Gameface component/res_map pattern, not
  `RandomHangar._initialize` (§F).
- Field-mod/Tier-XI data is a per-step state graph with per-step XP prices (§D).
