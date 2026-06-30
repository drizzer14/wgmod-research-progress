# WoT / BigWorld game API used by the mod

Concrete game symbols the mod depends on, and where they live in the EU 2.3 decompiled
client. Game symbols are confined to `engine_adapter.py` (reads) and `actions.py`
(writes); the domain layer never imports these. All reads are wrapped in try/except so an
API drift degrades a single category to a safe default instead of blanking the bar.

To inspect any of these live, use the **wgmod-debug-repl** skill. To re-locate a symbol
after a client patch, clone the decompiled source for the matching region/branch (see
that skill).

## Entry / mount (`gui/mods/mod_wgmod.py`, `bridge/gameface_bridge.py`)
- `gui.impl.lobby.hangar.presenters.hangar_vehicle_params_presenter.HangarVehicleParamsPresenter`
  — patched sub-view; `_onLoading` is the mount hook, `getViewModel()` the host model.
- `openwg_gameface.gf_mod_inject(host_vm, name, styles=[…], modules=[…])` — load our
  CSS/JS into the hangar document (hard dependency; import raises if OpenWG absent).
- `frameworks.wulf.ViewModel`, `frameworks.wulf.Array` — base classes for
  `ResearchVM`/`TickVM`/`UpgradeVM`; `_addNumber/String/Bool/Array/ViewModelProperty`,
  `_addCommand`, `transaction()`, `addViewModel`, `invalidate`.
- `BigWorld.callback(0.0, fn)` — defer the coalesced refresh to the next tick (main thread).

## Listeners (`bridge/gameface_bridge.py`)
- `CurrentVehicle.g_currentVehicle.onChanged` — vehicle-selection event (list-based;
  re-arm every mount).
- `skeletons.gui.game_control.ILoadoutController` (via `helpers.dependency.instance`) —
  `.interactor` (None ⇔ plain garage), `.onInteractorUpdated` event.
- `skeletons.gui.shared.IItemsCache` — `.onSyncCompleted(updateReason, invalidItems)`
  event (long-lived singleton); reason strings `shop`/`clan` are ignored, all else
  refreshes (fail-open).

## Reads (`adapter/engine_adapter.py`)
- `CurrentVehicle.g_currentVehicle` — `.isPresent()`, `.item` (the selected vehicle).
- Vehicle item: `.level`, `.isElite`, `.xp`, `.type` (class id), `.intCD`,
  `.getUnlocksDescrs()` → rows `(unlockIdx, xpCost, intCD, prereqs)`,
  `.postProgression` → `.isVehSkillTree()`, `.iterOrderedSteps()` (a DAG — DEDUPE by
  stepID; visited once per parent edge).
- `helpers.dependency.instance(IItemsCache)` → `stats.freeXP`, `stats.unlocks` (set).
- `items.getTypeOfCompactDescr(intCD)` + `gui.shared.gui_items.GUI_ITEM_TYPE.VEHICLE` —
  distinguish a next-vehicle unlock from a module unlock.
- Localization: `action.getLocNameRes()` returns a Wulf `DynAccessor` — CALL it for the
  res id, then `gui.impl.backport.text(res_id)`. Skill-tree names:
  `R.strings.veh_skill_tree.tooltips.title.dyn(<imageName>)` → `backport.text`.
- Prestige (`gui.prestige.prestige_helpers as ph`):
  `ph.hasVehiclePrestige(cd, checkElite=True)` (gate),
  `ph.getVehiclePrestige(cd)` → `.currentLevel`, `.remainingPoints`,
  `ph.prestigePointsToXP(points)`, `ph.mapGradeIDToUI(prestigeMarkID)` → (family enum, sub).
  Per-level XP table comes from
  `dependency.instance(ILobbyContext).getServerSettings().prestigeConfig`.

## Writes (`adapter/actions.py`) — verified via the dev REPL
- **Tech-tree research:** `gui.shared.gui_items.items_actions.factory.doAction(
  factory.UNLOCK_ITEM, intCD, props)` where `props = UnlockProps(parentID, unlockIdx,
  xpCost, set(required), 0, xpFullCost)` from
  `gui.Scaleform.daapi.view.lobby.techtree.settings.UnlockProps`. Build the row from
  `veh.getUnlocksDescrs()`.
- **Field-mod step:** `gui.shared.event_dispatcher.showPostProgressionResearchDialog(
  veh, [stepID])` — WG's dialog that BOTH confirms and researches.
- **Tier-XI skill tree:** `gui.shared.event_dispatcher.showVehicleHubVehSkillTree(
  veh.intCD)` — the current Upgrades screen (the older `showVehPostProgressionView` 404s
  for skill-tree vehicles).
- **Fallback screens:** `showResearchView(intCD)`, `showVehPostProgressionView(intCD)`.
  Every write path falls back to one of these rather than raising into JS.
