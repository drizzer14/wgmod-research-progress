# Research-Progress Bar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Garage progress bar that shows the selected vehicle's research progress on a single XP axis, per the design spec (`docs/superpowers/specs/2026-06-28-research-progress-bar-design.md`).

**Architecture:** A pure, engine-free **domain layer** (`wgmod_research.domain`) turns a normalized `VehicleSnapshot` into a `ResearchProgressModel` (mode state machine + tick math) and is unit-tested on macOS. A thin **engine adapter** (PC-only) reads the live WoT client into a `VehicleSnapshot`. A **bridge** patches the Hangar Gameface view and pushes the model into its ViewModel; a **Gameface view** (`gui/unbound`) renders it.

**Tech Stack:** Python 2.7 (game runtime; domain code written 2/3-compatible), pytest under Python 3 for unit tests on macOS, Coherent Gameface (HTML/CSS/JS) via the OpenWG Gameface framework, `.wotmod` packaging.

---

## Conventions

- **Domain code is 2/3-compatible and imports nothing engine-specific** (no `BigWorld`, `gui.*`, `items.*`). This is what lets us TDD it on the Mac. The build compiles it to 2.7 `.pyc` like everything else.
- **All XP values are ints.** A "tick position" is a cumulative XP value on the axis.
- **Mode** is one of: `TECH_TREE`, `RESEARCH_PLUS_TIERXI`, `TIERXI_NODES`, `ELITE`, `ELITE_PLUS_TIERXI_REWARDS` (see spec §4).
- Commit messages follow the repo convention and end with the `Co-Authored-By` trailer already used on `main`.

## File structure

```
src/res/scripts/client/
  gui/mods/mod_research_progress.py        # entry point: init()/fini() install+remove hooks
  wgmod_research/
    __init__.py
    domain/
      __init__.py
      types.py          # Tick, ResearchProgressModel, Mode, UnlockItem, ProgressionStep, Milestone, VehicleSnapshot
      builder.py        # build_model(snapshot) -> ResearchProgressModel  (the state machine)
      resolvers/
        __init__.py
        techtree.py     # tech-tree ticks from snapshot
        fieldmods.py    # field-modification ticks
        tierxi.py       # Tier XI nodes + successor + potential
        elite.py        # elite-system milestone ticks
    adapter/
      __init__.py
      engine_adapter.py # PC-only: live client -> VehicleSnapshot
    bridge/
      __init__.py
      hangar_hook.py    # patch RandomHangar._initialize; subscribe g_currentVehicle.onChanged
      viewmodel_bridge.py # push ResearchProgressModel into the Gameface ViewModel
  res/gui/unbound/research_progress/
    research_progress.html
    research_progress.css
    research_progress.js
tests/
  conftest.py           # puts src/res/scripts/client on sys.path
  test_types.py
  test_resolver_techtree.py
  test_resolver_fieldmods.py
  test_resolver_tierxi.py
  test_resolver_elite.py
  test_builder.py
docs/superpowers/research/decompiled-findings.md   # output of Task 1
```

---

## Phase 0 — De-risk & harness

### Task 1: Verification spike against the decompiled client

**Files:**
- Create: `docs/superpowers/research/decompiled-findings.md`

- [ ] **Step 1: Clone the decompiled client to a scratch location (not in the repo)**

Run:
```bash
git clone --depth 1 https://github.com/StranikS-Scan/WorldOfTanks-Decompiled.git /tmp/wot-src
```
Expected: a shallow clone under `/tmp/wot-src`.

- [ ] **Step 2: Grep the symbols the adapter depends on and record exact findings**

Run each and capture real output:
```bash
cd /tmp/wot-src
grep -rn "class _CurrentVehicle\|g_currentVehicle\|onChanged\|isPresent" source/res/scripts/client/CurrentVehicle.py
grep -rn "def xp\|isElite\|isFullyElite\|getUnlocksDescrs\|unlocksDescrs\|postProgression" source/res/scripts/client/gui/shared/gui_items/Vehicle.py
grep -rn "freeXP\|vehicleXP\|self.unlocks\|getItemByCD" source/res/scripts/client/gui/shared/utils/requesters/ItemsRequester.py
grep -rn "parseIntCompactDescr\|makeIntCompactDescrByID\|unlocksDescrs\|MAX_VEHICLE_LEVEL\|= 11" source/res/scripts/common/items/vehicles.py
grep -rln "post_progression\|PostProgression\|POST_PROGRESSION_ALL_PRICES" source/res/scripts/
grep -rln "elite" source/res/scripts/client/gui/ | grep -i "level\|milestone\|reward"
grep -rn "class RandomHangar\|_initialize\|viewModel" source/res/scripts/client/gui/impl/lobby/hangar/random/random_hangar.py
```
Expected: exact module paths, attribute names, function signatures, and the `unlocksDescrs` tuple layout.

- [ ] **Step 3: Read the two reference mods for the ViewModel-injection + dependency patterns**

Clone and read (focus on the Python that hooks a lobby view and pushes data, and how dependencies are declared):
```bash
git clone --depth 1 https://github.com/wot-public-mods/battle-hits.git /tmp/battle-hits
git clone --depth 1 https://github.com/ANIALLATOR114/extended-interface-scaling.git /tmp/eis
```
Expected: a concrete example of `view._initialize` patching, `viewModel.transaction()`, and the `meta.xml`/dependency declarations.

- [ ] **Step 4: Write `decompiled-findings.md`**

For each spec §11 item, record: exact module path, symbol name, signature/shape, a short verbatim snippet, and CONFIRMED / NOT-FOUND. Resolve in particular: the `unlocksDescrs` tuple field order; the post-progression accessor on the vehicle gui_item and its step fields (state, price, currency); whether Tier XI nodes reuse post-progression; whether elite-level/milestone data is readable for non-Tier-XI vehicles and the cap values; the current `RandomHangar` class path and ViewModel field/command syntax.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/research/decompiled-findings.md
git commit -m "research: verify WoT client symbols for research-progress bar

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

> **Gate:** If Step 4 finds that elite-level/milestone data is NOT readable for non-Tier-XI vehicles (spec §6/§11 item 4), STOP and report — the elite-system requirement may need to narrow to Tier XI. Domain Phase 1 is unaffected and can proceed regardless.

### Task 2: Test harness

**Files:**
- Create: `tests/conftest.py`
- Create: `src/res/scripts/client/wgmod_research/__init__.py` (empty)
- Create: `src/res/scripts/client/wgmod_research/domain/__init__.py` (empty)
- Create: `src/res/scripts/client/wgmod_research/domain/resolvers/__init__.py` (empty)

- [ ] **Step 1: Create the package `__init__.py` files (all empty) and conftest**

`tests/conftest.py`:
```python
import os
import sys

# Make the in-game package importable in tests without the game engine.
_CLIENT = os.path.join(os.path.dirname(__file__), "..", "src", "res", "scripts", "client")
sys.path.insert(0, os.path.abspath(_CLIENT))
```

- [ ] **Step 2: Verify pytest collects with an empty run**

Run: `python3 -m pytest -q`
Expected: `no tests ran` (exit code 5) — confirms collection works and the path is valid.

- [ ] **Step 3: Commit**

```bash
git add tests/conftest.py src/res/scripts/client/wgmod_research
git commit -m "test: add pytest harness and domain package skeleton

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Phase 1 — Domain layer (pure, TDD on macOS)

### Task 3: Domain types

**Files:**
- Create: `src/res/scripts/client/wgmod_research/domain/types.py`
- Test: `tests/test_types.py`

- [ ] **Step 1: Write the failing test**

`tests/test_types.py`:
```python
from wgmod_research.domain import types as t


def test_mode_constants_are_distinct():
    modes = {t.Mode.TECH_TREE, t.Mode.RESEARCH_PLUS_TIERXI,
             t.Mode.TIERXI_NODES, t.Mode.ELITE, t.Mode.ELITE_PLUS_TIERXI_REWARDS}
    assert len(modes) == 5


def test_tick_holds_fields():
    tick = t.Tick(xp_position=1500, category="techtree", icon="gun.png",
                  name="Gun X", xp_gained=0, xp_required=1500,
                  affordable=False, completed=False)
    assert tick.xp_position == 1500
    assert tick.category == "techtree"
    assert tick.affordable is False


def test_model_defaults_empty_ticks():
    m = t.ResearchProgressModel(mode=t.Mode.TECH_TREE, scale_min=0, scale_max=0,
                                fill_spendable=0, fill_earned=0, ticks=[])
    assert m.ticks == []
    assert m.mode == t.Mode.TECH_TREE
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_types.py -v`
Expected: FAIL with `ModuleNotFoundError`/`AttributeError` (types not defined).

- [ ] **Step 3: Write minimal implementation**

`src/res/scripts/client/wgmod_research/domain/types.py`:
```python
# -*- coding: utf-8 -*-
"""Engine-free data types shared by the domain layer. 2/3 compatible."""


class Mode(object):
    TECH_TREE = "tech_tree"
    RESEARCH_PLUS_TIERXI = "research_plus_tierxi"
    TIERXI_NODES = "tierxi_nodes"
    ELITE = "elite"
    ELITE_PLUS_TIERXI_REWARDS = "elite_plus_tierxi_rewards"


class Tick(object):
    def __init__(self, xp_position, category, icon, name,
                 xp_gained, xp_required, affordable, completed):
        self.xp_position = xp_position
        self.category = category          # techtree|fieldmod|tierXI|potentialXI|elite
        self.icon = icon
        self.name = name
        self.xp_gained = xp_gained
        self.xp_required = xp_required
        self.affordable = affordable
        self.completed = completed


class UnlockItem(object):
    """A tech-tree unlock (module or next vehicle)."""
    def __init__(self, int_cd, name, icon, xp_cost, kind, researched, prereqs_met):
        self.int_cd = int_cd
        self.name = name
        self.icon = icon
        self.xp_cost = xp_cost
        self.kind = kind                  # 'module' | 'vehicle'
        self.researched = researched
        self.prereqs_met = prereqs_met


class ProgressionStep(object):
    """A field-mod step or a Tier XI upgrade node."""
    def __init__(self, step_id, name, icon, xp_cost, unlocked):
        self.step_id = step_id
        self.name = name
        self.icon = icon
        self.xp_cost = xp_cost
        self.unlocked = unlocked


class Milestone(object):
    """An elite-system badge milestone at a cumulative XP threshold."""
    def __init__(self, level, xp_threshold, name, icon):
        self.level = level
        self.xp_threshold = xp_threshold
        self.name = name
        self.icon = icon


class VehicleSnapshot(object):
    """Engine-free description of the selected vehicle's research state.

    The engine adapter produces this; the domain layer consumes only this.
    """
    def __init__(self, tier, is_elite, vehicle_xp, free_xp,
                 tech_unlocks=None, field_mod_steps=None,
                 tierxi_nodes=None, tierxi_successor=None, potential_tierxi=None,
                 tierxi_earned_xp=0,
                 elite_milestones=None, elite_earned_xp=0, elite_cap_level=0):
        self.tier = tier                          # 1..11
        self.is_elite = is_elite
        self.vehicle_xp = vehicle_xp              # unspent accumulated XP
        self.free_xp = free_xp                    # global free XP
        self.tech_unlocks = tech_unlocks or []    # [UnlockItem]
        self.field_mod_steps = field_mod_steps or []   # [ProgressionStep]
        self.tierxi_nodes = tierxi_nodes or []    # [ProgressionStep] (tier 11 only)
        self.tierxi_successor = tierxi_successor  # UnlockItem | None (real Tier XI from a Tier X)
        self.potential_tierxi = potential_tierxi  # UnlockItem | None (synthetic for Tier X w/o XI)
        self.tierxi_earned_xp = tierxi_earned_xp  # cumulative XP earned toward nodes (left baseline)
        self.elite_milestones = elite_milestones or []  # [Milestone]
        self.elite_earned_xp = elite_earned_xp    # cumulative earned XP toward milestones
        self.elite_cap_level = elite_cap_level    # 150 for Tier XI


class ResearchProgressModel(object):
    def __init__(self, mode, scale_min, scale_max,
                 fill_spendable, fill_earned, ticks):
        self.mode = mode
        self.scale_min = scale_min
        self.scale_max = scale_max
        self.fill_spendable = fill_spendable   # vehicle_xp + free_xp (research modes)
        self.fill_earned = fill_earned         # earned progress (elite modes)
        self.ticks = ticks                     # [Tick], ordered by xp_position
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_types.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add src/res/scripts/client/wgmod_research/domain/types.py tests/test_types.py
git commit -m "feat(domain): add research-progress data types

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

### Task 4: Tech-tree resolver

**Files:**
- Create: `src/res/scripts/client/wgmod_research/domain/resolvers/techtree.py`
- Test: `tests/test_resolver_techtree.py`

Cumulative-XP positioning: ticks are laid out by **cumulative** cost — sort remaining (not-researched) unlocks by `xp_cost`, then each tick's `xp_position` is the running sum including itself. `affordable` = `xp_position <= spendable`.

- [ ] **Step 1: Write the failing test**

`tests/test_resolver_techtree.py`:
```python
from wgmod_research.domain import types as t
from wgmod_research.domain.resolvers import techtree


def _unlock(cd, cost, researched=False):
    return t.UnlockItem(int_cd=cd, name="i%d" % cd, icon="i%d.png" % cd,
                        xp_cost=cost, kind="module",
                        researched=researched, prereqs_met=True)


def test_skips_researched_and_orders_cumulatively():
    snap = t.VehicleSnapshot(
        tier=5, is_elite=False, vehicle_xp=1000, free_xp=500,
        tech_unlocks=[_unlock(1, 800, researched=True),
                      _unlock(2, 2000),
                      _unlock(3, 600)])
    ticks = techtree.resolve(snap)
    # researched item excluded; remaining ordered by cost: 600 then 2000
    assert [tk.xp_required for tk in ticks] == [600, 2000]
    # cumulative positions: 600, then 2600
    assert [tk.xp_position for tk in ticks] == [600, 2600]


def test_affordable_against_spendable():
    snap = t.VehicleSnapshot(
        tier=5, is_elite=False, vehicle_xp=1000, free_xp=500,  # spendable = 1500
        tech_unlocks=[_unlock(3, 600), _unlock(2, 2000)])
    ticks = techtree.resolve(snap)
    # 600 affordable (<=1500), 2600 not
    assert [tk.affordable for tk in ticks] == [True, False]
    assert all(tk.category == "techtree" for tk in ticks)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_resolver_techtree.py -v`
Expected: FAIL (`ModuleNotFoundError: ...resolvers.techtree`).

- [ ] **Step 3: Write minimal implementation**

`src/res/scripts/client/wgmod_research/domain/resolvers/techtree.py`:
```python
# -*- coding: utf-8 -*-
from wgmod_research.domain import types as t


def resolve(snapshot):
    """Return tech-tree ticks ordered by cumulative XP cost (remaining only)."""
    spendable = snapshot.vehicle_xp + snapshot.free_xp
    remaining = [u for u in snapshot.tech_unlocks if not u.researched]
    remaining.sort(key=lambda u: u.xp_cost)
    ticks = []
    running = 0
    for u in remaining:
        running += u.xp_cost
        ticks.append(t.Tick(
            xp_position=running, category="techtree", icon=u.icon, name=u.name,
            xp_gained=0, xp_required=u.xp_cost,
            affordable=(running <= spendable), completed=False))
    return ticks
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_resolver_techtree.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add src/res/scripts/client/wgmod_research/domain/resolvers/techtree.py tests/test_resolver_techtree.py
git commit -m "feat(domain): tech-tree resolver

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

### Task 5: Field-modifications resolver

**Files:**
- Create: `src/res/scripts/client/wgmod_research/domain/resolvers/fieldmods.py`
- Test: `tests/test_resolver_fieldmods.py`

- [ ] **Step 1: Write the failing test**

`tests/test_resolver_fieldmods.py`:
```python
from wgmod_research.domain import types as t
from wgmod_research.domain.resolvers import fieldmods


def _step(sid, cost, unlocked=False):
    return t.ProgressionStep(step_id=sid, name="fm%d" % sid, icon="fm%d.png" % sid,
                             xp_cost=cost, unlocked=unlocked)


def test_orders_by_step_sequence_cumulatively_skipping_unlocked():
    snap = t.VehicleSnapshot(
        tier=9, is_elite=True, vehicle_xp=3000, free_xp=0,  # spendable 3000
        field_mod_steps=[_step(1, 1000, unlocked=True),
                         _step(2, 2000),
                         _step(3, 4000)])
    ticks = fieldmods.resolve(snap)
    assert [tk.xp_required for tk in ticks] == [2000, 4000]
    assert [tk.xp_position for tk in ticks] == [2000, 6000]
    assert [tk.affordable for tk in ticks] == [True, False]
    assert all(tk.category == "fieldmod" for tk in ticks)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_resolver_fieldmods.py -v`
Expected: FAIL (module missing).

- [ ] **Step 3: Write minimal implementation**

`src/res/scripts/client/wgmod_research/domain/resolvers/fieldmods.py`:
```python
# -*- coding: utf-8 -*-
from wgmod_research.domain import types as t


def resolve(snapshot, start_position=0):
    """Field-mod ticks, cumulative from start_position (remaining only).

    Field-mod steps are ordered by their natural step sequence (list order),
    not re-sorted by cost.
    """
    spendable = snapshot.vehicle_xp + snapshot.free_xp
    ticks = []
    running = start_position
    for step in snapshot.field_mod_steps:
        if step.unlocked:
            continue
        running += step.xp_cost
        ticks.append(t.Tick(
            xp_position=running, category="fieldmod", icon=step.icon, name=step.name,
            xp_gained=0, xp_required=step.xp_cost,
            affordable=(running <= spendable), completed=False))
    return ticks
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_resolver_fieldmods.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/res/scripts/client/wgmod_research/domain/resolvers/fieldmods.py tests/test_resolver_fieldmods.py
git commit -m "feat(domain): field-modifications resolver

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

### Task 6: Tier XI resolver (nodes + successor + potential)

**Files:**
- Create: `src/res/scripts/client/wgmod_research/domain/resolvers/tierxi.py`
- Test: `tests/test_resolver_tierxi.py`

Two entry points: `resolve_successor(snapshot, start_position)` adds a single tick for a real or potential Tier XI vehicle unlock (category `tierXI` or `potentialXI`); `resolve_nodes(snapshot)` lays out Tier XI upgrade nodes cumulatively from `tierxi_earned_xp` (the left baseline).

- [ ] **Step 1: Write the failing test**

`tests/test_resolver_tierxi.py`:
```python
from wgmod_research.domain import types as t
from wgmod_research.domain.resolvers import tierxi


def test_real_successor_tick():
    succ = t.UnlockItem(int_cd=99, name="T11", icon="t11.png", xp_cost=325000,
                        kind="vehicle", researched=False, prereqs_met=True)
    snap = t.VehicleSnapshot(tier=10, is_elite=True, vehicle_xp=0, free_xp=0,
                             tierxi_successor=succ)
    ticks = tierxi.resolve_successor(snap, start_position=10000)
    assert len(ticks) == 1
    assert ticks[0].category == "tierXI"
    assert ticks[0].xp_position == 335000   # 10000 + 325000
    assert ticks[0].xp_required == 325000


def test_potential_successor_uses_potential_category():
    pot = t.UnlockItem(int_cd=0, name="Potential T11", icon="pot.png",
                       xp_cost=325000, kind="vehicle", researched=False, prereqs_met=True)
    snap = t.VehicleSnapshot(tier=10, is_elite=True, vehicle_xp=0, free_xp=0,
                             potential_tierxi=pot)
    ticks = tierxi.resolve_successor(snap, start_position=0)
    assert ticks[0].category == "potentialXI"


def test_nodes_cumulative_from_earned_baseline():
    snap = t.VehicleSnapshot(
        tier=11, is_elite=False, vehicle_xp=5000, free_xp=2000,  # spendable 7000
        tierxi_earned_xp=20000,
        tierxi_nodes=[t.ProgressionStep(1, "n1", "n1.png", 10000, False),
                      t.ProgressionStep(2, "n2", "n2.png", 20000, True),  # unlocked, skip
                      t.ProgressionStep(3, "n3", "n3.png", 25000, False)])
    ticks = tierxi.resolve_nodes(snap)
    # baseline 20000; remaining 10000 -> 30000, then 25000 -> 55000
    assert [tk.xp_position for tk in ticks] == [30000, 55000]
    assert all(tk.category == "tierXI" for tk in ticks)
    # spendable 7000 covers neither beyond baseline -> none affordable
    assert [tk.affordable for tk in ticks] == [False, False]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_resolver_tierxi.py -v`
Expected: FAIL (module missing).

- [ ] **Step 3: Write minimal implementation**

`src/res/scripts/client/wgmod_research/domain/resolvers/tierxi.py`:
```python
# -*- coding: utf-8 -*-
from wgmod_research.domain import types as t


def resolve_successor(snapshot, start_position=0):
    """A single tick for a real (tierXI) or potential (potentialXI) Tier XI unlock."""
    item = snapshot.tierxi_successor
    category = "tierXI"
    if item is None:
        item = snapshot.potential_tierxi
        category = "potentialXI"
    if item is None or item.researched:
        return []
    spendable = snapshot.vehicle_xp + snapshot.free_xp
    pos = start_position + item.xp_cost
    return [t.Tick(xp_position=pos, category=category, icon=item.icon, name=item.name,
                   xp_gained=0, xp_required=item.xp_cost,
                   affordable=(pos <= spendable), completed=False)]


def resolve_nodes(snapshot):
    """Tier XI upgrade-node ticks, cumulative from the earned-XP baseline."""
    spendable = snapshot.vehicle_xp + snapshot.free_xp
    ticks = []
    running = snapshot.tierxi_earned_xp
    for node in snapshot.tierxi_nodes:
        if node.unlocked:
            continue
        running += node.xp_cost
        ticks.append(t.Tick(
            xp_position=running, category="tierXI", icon=node.icon, name=node.name,
            xp_gained=0, xp_required=node.xp_cost,
            affordable=(running <= snapshot.tierxi_earned_xp + spendable),
            completed=False))
    return ticks
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_resolver_tierxi.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add src/res/scripts/client/wgmod_research/domain/resolvers/tierxi.py tests/test_resolver_tierxi.py
git commit -m "feat(domain): Tier XI resolver (nodes + successor + potential)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

### Task 7: Elite-system resolver

**Files:**
- Create: `src/res/scripts/client/wgmod_research/domain/resolvers/elite.py`
- Test: `tests/test_resolver_elite.py`

Milestones already carry **cumulative XP thresholds** (spec §3). Resolver emits a tick per not-yet-reached milestone, positioned at its threshold; `affordable` is judged against **earned** XP only (free XP excluded — spec §4).

- [ ] **Step 1: Write the failing test**

`tests/test_resolver_elite.py`:
```python
from wgmod_research.domain import types as t
from wgmod_research.domain.resolvers import elite


def test_milestones_remaining_only_against_earned():
    snap = t.VehicleSnapshot(
        tier=11, is_elite=True, vehicle_xp=0, free_xp=999999,  # free XP must NOT count
        elite_earned_xp=15000, elite_cap_level=150,
        elite_milestones=[t.Milestone(10, 10000, "Bronze", "b.png"),   # reached (<=15000)
                          t.Milestone(50, 50000, "Silver", "s.png"),
                          t.Milestone(150, 200000, "Gold", "g.png")])
    ticks = elite.resolve(snap)
    # 10000 already reached -> excluded; remaining 50000, 200000
    assert [tk.xp_position for tk in ticks] == [50000, 200000]
    assert all(tk.category == "elite" for tk in ticks)
    # earned 15000 affords neither -> not affordable (free XP ignored)
    assert [tk.affordable for tk in ticks] == [False, False]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_resolver_elite.py -v`
Expected: FAIL (module missing).

- [ ] **Step 3: Write minimal implementation**

`src/res/scripts/client/wgmod_research/domain/resolvers/elite.py`:
```python
# -*- coding: utf-8 -*-
from wgmod_research.domain import types as t


def resolve(snapshot):
    """Elite milestone ticks (remaining only), judged against EARNED XP only."""
    earned = snapshot.elite_earned_xp
    ticks = []
    for ms in snapshot.elite_milestones:
        if ms.xp_threshold <= earned:
            continue  # already reached
        ticks.append(t.Tick(
            xp_position=ms.xp_threshold, category="elite", icon=ms.icon, name=ms.name,
            xp_gained=earned, xp_required=ms.xp_threshold,
            affordable=(ms.xp_threshold <= earned), completed=False))
    return ticks
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_resolver_elite.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/res/scripts/client/wgmod_research/domain/resolvers/elite.py tests/test_resolver_elite.py
git commit -m "feat(domain): elite-system milestone resolver

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

### Task 8: Builder / mode state machine

**Files:**
- Create: `src/res/scripts/client/wgmod_research/domain/builder.py`
- Test: `tests/test_builder.py`

Implements spec §4 exactly. Decision order:

```
if tier == 11:
    if tierxi_nodes has remaining: mode=TIERXI_NODES (nodes; scale_min=tierxi_earned_xp)
    else: mode=ELITE_PLUS_TIERXI_REWARDS (elite ticks; scale_max from cap/level-150 milestone)
else:  # tiers I-X
    if not is_elite: mode=TECH_TREE (techtree ticks)
    else:
        research = fieldmods + tierxi_successor/potential (remaining)
        if research non-empty: mode = RESEARCH_PLUS_TIERXI if a successor tick exists else (still field mods only)  -> RESEARCH_PLUS_TIERXI label covers both; if only field mods, mode=TECH_TREE-style research. Use RESEARCH_PLUS_TIERXI when a successor/potential tick is present, else a plain field-mods research mode (reuse TECH_TREE scale rules but category fieldmod).
        else: mode=ELITE (elite ticks)
```

To keep modes unambiguous, the builder sets:
- `TECH_TREE` when not elite.
- `RESEARCH_PLUS_TIERXI` whenever elite and any research tick remains (field mods and/or successor/potential) — this is the single "elite research" mode for tiers ≤ X.
- `ELITE` when elite and no research remains.
- `TIERXI_NODES` / `ELITE_PLUS_TIERXI_REWARDS` for tier 11.

Scale: `scale_min` = baseline (0, except `tierxi_earned_xp` for `TIERXI_NODES`, and `elite_earned_xp` for elite modes); `scale_max` = max tick position (or the cap milestone threshold for elite modes). Fill: `fill_spendable = vehicle_xp + free_xp` for research modes (else 0); `fill_earned = elite_earned_xp` for elite modes (else 0).

- [ ] **Step 1: Write the failing test**

`tests/test_builder.py`:
```python
from wgmod_research.domain import types as t
from wgmod_research.domain.builder import build_model


def _u(cd, cost, researched=False, kind="module"):
    return t.UnlockItem(cd, "u%d" % cd, "u%d.png" % cd, cost, kind, researched, True)


def test_not_elite_is_tech_tree():
    snap = t.VehicleSnapshot(tier=6, is_elite=False, vehicle_xp=500, free_xp=0,
                             tech_unlocks=[_u(1, 1000), _u(2, 500)])
    m = build_model(snap)
    assert m.mode == t.Mode.TECH_TREE
    assert m.scale_min == 0
    assert m.scale_max == 1500          # cumulative max
    assert m.fill_spendable == 500
    assert m.fill_earned == 0
    assert [tk.xp_position for tk in m.ticks] == [500, 1500]


def test_elite_with_fieldmods_and_successor_is_research_plus_tierxi():
    succ = _u(99, 325000, kind="vehicle")
    snap = t.VehicleSnapshot(
        tier=10, is_elite=True, vehicle_xp=1000, free_xp=0,
        field_mod_steps=[t.ProgressionStep(1, "fm1", "fm1.png", 2000, False)],
        tierxi_successor=succ)
    m = build_model(snap)
    assert m.mode == t.Mode.RESEARCH_PLUS_TIERXI
    # field mod tick at 2000, then successor stacked after: 2000 + 325000
    assert [tk.category for tk in m.ticks] == ["fieldmod", "tierXI"]
    assert [tk.xp_position for tk in m.ticks] == [2000, 327000]
    assert m.scale_max == 327000
    assert m.fill_spendable == 1000


def test_elite_no_research_is_elite_mode():
    snap = t.VehicleSnapshot(
        tier=9, is_elite=True, vehicle_xp=0, free_xp=0,
        field_mod_steps=[t.ProgressionStep(1, "fm1", "fm1.png", 2000, True)],  # done
        elite_earned_xp=5000,
        elite_milestones=[t.Milestone(10, 10000, "Bronze", "b.png")])
    m = build_model(snap)
    assert m.mode == t.Mode.ELITE
    assert m.scale_min == 5000
    assert m.scale_max == 10000
    assert m.fill_earned == 5000
    assert m.fill_spendable == 0


def test_tier11_with_remaining_nodes_is_node_mode():
    snap = t.VehicleSnapshot(
        tier=11, is_elite=False, vehicle_xp=0, free_xp=0,
        tierxi_earned_xp=20000,
        tierxi_nodes=[t.ProgressionStep(1, "n1", "n1.png", 10000, False)])
    m = build_model(snap)
    assert m.mode == t.Mode.TIERXI_NODES
    assert m.scale_min == 20000
    assert m.scale_max == 30000


def test_tier11_all_nodes_done_is_elite_rewards():
    snap = t.VehicleSnapshot(
        tier=11, is_elite=True, vehicle_xp=0, free_xp=0,
        tierxi_nodes=[t.ProgressionStep(1, "n1", "n1.png", 10000, True)],  # all done
        elite_earned_xp=1000, elite_cap_level=150,
        elite_milestones=[t.Milestone(150, 200000, "Gold", "g.png")])
    m = build_model(snap)
    assert m.mode == t.Mode.ELITE_PLUS_TIERXI_REWARDS
    assert m.scale_max == 200000
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_builder.py -v`
Expected: FAIL (`builder` missing).

- [ ] **Step 3: Write minimal implementation**

`src/res/scripts/client/wgmod_research/domain/builder.py`:
```python
# -*- coding: utf-8 -*-
from wgmod_research.domain import types as t
from wgmod_research.domain.resolvers import techtree, fieldmods, tierxi, elite


def _max_pos(ticks, default):
    return max([tk.xp_position for tk in ticks]) if ticks else default


def build_model(snapshot):
    spendable = snapshot.vehicle_xp + snapshot.free_xp

    if snapshot.tier == 11:
        node_ticks = tierxi.resolve_nodes(snapshot)
        if node_ticks:
            return t.ResearchProgressModel(
                mode=t.Mode.TIERXI_NODES,
                scale_min=snapshot.tierxi_earned_xp,
                scale_max=_max_pos(node_ticks, snapshot.tierxi_earned_xp),
                fill_spendable=spendable, fill_earned=0, ticks=node_ticks)
        elite_ticks = elite.resolve(snapshot)
        return t.ResearchProgressModel(
            mode=t.Mode.ELITE_PLUS_TIERXI_REWARDS,
            scale_min=snapshot.elite_earned_xp,
            scale_max=_max_pos(elite_ticks, snapshot.elite_earned_xp),
            fill_spendable=0, fill_earned=snapshot.elite_earned_xp, ticks=elite_ticks)

    # tiers I-X
    if not snapshot.is_elite:
        ticks = techtree.resolve(snapshot)
        return t.ResearchProgressModel(
            mode=t.Mode.TECH_TREE, scale_min=0, scale_max=_max_pos(ticks, 0),
            fill_spendable=spendable, fill_earned=0, ticks=ticks)

    # elite tiers I-X: field mods + (real/potential) Tier XI successor
    fm_ticks = fieldmods.resolve(snapshot)
    fm_end = _max_pos(fm_ticks, 0)
    succ_ticks = tierxi.resolve_successor(snapshot, start_position=fm_end)
    research_ticks = fm_ticks + succ_ticks
    if research_ticks:
        return t.ResearchProgressModel(
            mode=t.Mode.RESEARCH_PLUS_TIERXI, scale_min=0,
            scale_max=_max_pos(research_ticks, 0),
            fill_spendable=spendable, fill_earned=0, ticks=research_ticks)

    elite_ticks = elite.resolve(snapshot)
    return t.ResearchProgressModel(
        mode=t.Mode.ELITE, scale_min=snapshot.elite_earned_xp,
        scale_max=_max_pos(elite_ticks, snapshot.elite_earned_xp),
        fill_spendable=0, fill_earned=snapshot.elite_earned_xp, ticks=elite_ticks)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_builder.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Run the whole domain suite and commit**

Run: `python3 -m pytest -q`
Expected: all tests pass.
```bash
git add src/res/scripts/client/wgmod_research/domain/builder.py tests/test_builder.py
git commit -m "feat(domain): mode state-machine builder

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Phase 2 — Integration (PC, gated on Task 1 findings)

> These tasks use the exact symbol names confirmed in `docs/superpowers/research/decompiled-findings.md`. Where a name below is marked ⟨confirm⟩, substitute the verified symbol from Task 1. Verification is manual/in-game (no Mac unit tests possible for engine/UI code).

### Task 9: Engine adapter — live client → `VehicleSnapshot`

**Files:**
- Create: `src/res/scripts/client/wgmod_research/adapter/__init__.py` (empty)
- Create: `src/res/scripts/client/wgmod_research/adapter/engine_adapter.py`

- [ ] **Step 1: Implement the adapter using confirmed symbols**

`engine_adapter.py` (skeleton with the confirmed read points; fill ⟨confirm⟩ from Task 1):
```python
# -*- coding: utf-8 -*-
from CurrentVehicle import g_currentVehicle
from helpers import dependency
from skeletons.gui.shared import IItemsCache
from debug_utils import LOG_CURRENT_EXCEPTION
from wgmod_research.domain import types as t

_items = dependency.descriptor(IItemsCache)


def build_snapshot():
    """Read the selected vehicle into a VehicleSnapshot, or None if unavailable."""
    if not g_currentVehicle.isPresent():
        return None
    veh = g_currentVehicle.item
    stats = _items().items.stats
    free_xp = stats.freeXP
    unlocked = stats.unlocks                       # set of intCDs ⟨confirm⟩

    tech = _read_tech_unlocks(veh, unlocked)       # see helpers below
    field = _read_field_mods(veh)                  # ⟨confirm post-progression accessor⟩
    tier = veh.level                               # ⟨confirm 11 for Tier XI⟩
    return t.VehicleSnapshot(
        tier=tier, is_elite=veh.isElite,
        vehicle_xp=veh.xp, free_xp=free_xp,
        tech_unlocks=tech, field_mod_steps=field,
        tierxi_nodes=_read_tierxi_nodes(veh) if tier == 11 else [],
        tierxi_successor=_read_real_successor(veh, unlocked),
        potential_tierxi=_read_potential_successor(veh),
        tierxi_earned_xp=_read_tierxi_earned(veh),
        elite_milestones=_read_elite_milestones(veh),
        elite_earned_xp=_read_elite_earned(veh),
        elite_cap_level=_read_elite_cap(veh))


# Each _read_* wraps its access in try/except and returns a safe empty default,
# so one unreadable system degrades gracefully (spec §8). Implement each using
# the exact symbols from decompiled-findings.md. Example for tech unlocks:
def _read_tech_unlocks(veh, unlocked):
    try:
        out = []
        for props in veh.descriptor.type.unlocksDescrs:   # ⟨confirm tuple order⟩
            xp_cost, int_cd = props[2], props[1]
            item = _items().items.getItemByCD(int_cd)
            kind = "vehicle" if item.itemTypeID == 1 else "module"  # ⟨confirm GUI_ITEM_TYPE.VEHICLE⟩
            out.append(t.UnlockItem(
                int_cd=int_cd, name=item.userName, icon=getattr(item, "icon", ""),
                xp_cost=xp_cost, kind=kind,
                researched=(int_cd in unlocked), prereqs_met=True))
        return out
    except Exception:
        LOG_CURRENT_EXCEPTION()
        return []
# _read_field_mods, _read_tierxi_nodes, _read_real_successor,
# _read_potential_successor, _read_tierxi_earned, _read_elite_milestones,
# _read_elite_earned, _read_elite_cap follow the same try/except pattern using
# the symbols confirmed in Task 1.
```

- [ ] **Step 2: Smoke-test the read in isolation via the debug REPL (PC)**

Install `wot-debugserver`, open the garage, connect, and run `from wgmod_research.adapter import engine_adapter; s = engine_adapter.build_snapshot(); print(s.tier, s.is_elite, s.vehicle_xp, len(s.tech_unlocks))` on several vehicles. Expected: sane values matching the in-game garage.

- [ ] **Step 3: Commit**

```bash
git add src/res/scripts/client/wgmod_research/adapter
git commit -m "feat(adapter): live client -> VehicleSnapshot reader

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

### Task 10: Hangar hook + entry point

**Files:**
- Create: `src/res/scripts/client/wgmod_research/bridge/__init__.py` (empty)
- Create: `src/res/scripts/client/wgmod_research/bridge/hangar_hook.py`
- Modify: `src/res/scripts/client/gui/mods/mod_research_progress.py` (rename from `mod_wgmod.py`)

- [ ] **Step 1: Rename the entry-point file and wire init/fini**

```bash
git mv src/res/scripts/client/gui/mods/mod_wgmod.py src/res/scripts/client/gui/mods/mod_research_progress.py
```

`mod_research_progress.py`:
```python
# -*- coding: utf-8 -*-
from debug_utils import LOG_NOTE, LOG_CURRENT_EXCEPTION
from wgmod_research.bridge import hangar_hook

MOD_NAME = "Research Progress"
MOD_VERSION = "0.1.0"


def init():
    try:
        hangar_hook.install()
        LOG_NOTE("[{0}] v{1} installed".format(MOD_NAME, MOD_VERSION))
    except Exception:
        LOG_CURRENT_EXCEPTION()


def fini():
    try:
        hangar_hook.remove()
    except Exception:
        LOG_CURRENT_EXCEPTION()
```

- [ ] **Step 2: Implement the hangar hook**

`hangar_hook.py` (uses the confirmed Hangar class path from Task 1):
```python
# -*- coding: utf-8 -*-
from CurrentVehicle import g_currentVehicle
from debug_utils import LOG_CURRENT_EXCEPTION
# ⟨confirm path from Task 1⟩
from gui.impl.lobby.hangar.random.random_hangar import RandomHangar
from wgmod_research.bridge import viewmodel_bridge

_orig_initialize = None
_active_view = None


def _patched_initialize(self, *args, **kwargs):
    _orig_initialize(self, *args, **kwargs)
    global _active_view
    _active_view = self
    _refresh()


def _refresh():
    try:
        if _active_view is not None:
            viewmodel_bridge.push(_active_view)
    except Exception:
        LOG_CURRENT_EXCEPTION()


def install():
    global _orig_initialize
    if _orig_initialize is None:
        _orig_initialize = RandomHangar._initialize
        RandomHangar._initialize = _patched_initialize
    g_currentVehicle.onChanged += _refresh


def remove():
    global _orig_initialize, _active_view
    g_currentVehicle.onChanged -= _refresh
    if _orig_initialize is not None:
        RandomHangar._initialize = _orig_initialize
        _orig_initialize = None
    _active_view = None
```

- [ ] **Step 3: Deploy and verify the hook fires (PC)**

Run: `python build/deploy_dev.py "<wot_path>" <version>` then launch WoT. Expected: `python.log` shows the install note; switching tanks triggers `_refresh` without errors.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat(bridge): hangar hook + renamed entry point

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

### Task 11: ViewModel bridge

**Files:**
- Create: `src/res/scripts/client/wgmod_research/bridge/viewmodel_bridge.py`

- [ ] **Step 1: Implement the bridge — adapter → builder → ViewModel transaction**

`viewmodel_bridge.py` (ViewModel field/command syntax per Task 1):
```python
# -*- coding: utf-8 -*-
from debug_utils import LOG_CURRENT_EXCEPTION
from wgmod_research.adapter import engine_adapter
from wgmod_research.domain.builder import build_model


def push(view):
    """Compute the model and write it into the view's ViewModel in one transaction."""
    try:
        snap = engine_adapter.build_snapshot()
        if snap is None:
            return
        model = build_model(snap)
        vm = view.getViewModel()                 # ⟨confirm accessor from Task 1⟩
        with vm.transaction() as tr:             # ⟨confirm transaction API⟩
            tr.setMode(model.mode)
            tr.setScaleMin(model.scale_min)
            tr.setScaleMax(model.scale_max)
            tr.setFillSpendable(model.fill_spendable)
            tr.setFillEarned(model.fill_earned)
            _write_ticks(tr, model.ticks)        # serialize ticks into the VM array
    except Exception:
        LOG_CURRENT_EXCEPTION()
```

- [ ] **Step 2: Verify data reaches the view (PC)**

With a temporary debug element in the view (or `console.log` in the JS), confirm the ViewModel receives correct mode/scale/ticks per vehicle. Expected: values match the domain model for the selected tank.

- [ ] **Step 3: Commit**

```bash
git add src/res/scripts/client/wgmod_research/bridge/viewmodel_bridge.py
git commit -m "feat(bridge): push research model into Gameface ViewModel

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

### Task 12: Gameface view (HTML/CSS/JS)

**Files:**
- Create: `src/res/gui/unbound/research_progress/research_progress.html`
- Create: `src/res/gui/unbound/research_progress/research_progress.css`
- Create: `src/res/gui/unbound/research_progress/research_progress.js`

- [ ] **Step 1: Build the bar markup + binding**

Render: the axis from `scaleMin`→`scaleMax`; two stacked fill segments (`fillSpendable` split into vehicle vs free in research modes, `fillEarned` in elite modes); one positioned tick per `ticks[]` entry with its category icon and an affordable/locked state class; a tooltip per tick showing `name` + `xpGained`/`xpRequired`. Bind to the ViewModel fields written in Task 11.

- [ ] **Step 2: Style with the game design system**

Use the client's Gameface design-system fonts/color tokens (identified in Task 1 from existing `gui/unbound` views). Category colors: techtree / fieldmod / tierXI / potentialXI / elite each distinct.

- [ ] **Step 3: Verify rendering in-game (PC) across modes**

Expected: bar appears in the hangar; correct ticks/fill for each of the five modes.

- [ ] **Step 4: Commit**

```bash
git add src/res/gui/unbound/research_progress
git commit -m "feat(ui): Gameface research-progress bar view

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

### Task 13: Dependencies + packaging

**Files:**
- Modify: `src/meta.xml` (name/id/version)
- Modify: `README.md` (dependency list: OpenWG Gameface)

- [ ] **Step 1: Update `meta.xml` and document the OpenWG Gameface dependency**

Set `<id>com.drizzer14.research_progress</id>`, name "Research Progress". In README, list OpenWG Gameface as a required install for players.

- [ ] **Step 2: Build the package**

Run: `python build/build_wotmod.py` (Python 2.7.18 on the PC).
Expected: `dist/com.drizzer14.research_progress_0.1.0.wotmod` (stored ZIP, meta.xml at root, `.pyc` under `res/`).

- [ ] **Step 3: Install the built package + OpenWG Gameface and smoke-test**

Copy both into `mods/<version>/`. Expected: client starts, bar renders from the packaged build (not just `res_mods`).

- [ ] **Step 4: Commit**

```bash
git add src/meta.xml README.md
git commit -m "build: package research-progress mod + declare Gameface dependency

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

### Task 14: Full in-game verification matrix

**Files:** none (verification only; record results in the PR/commit message)

- [ ] **Step 1: Verify each mode on a representative vehicle (PC)**

Check: non-elite (tech tree), elite + field mods (research), Tier X elite + real Tier XI successor (research+tierXI), Tier X elite + potential Tier XI, Tier X elite fully done (elite milestones), Tier XI partial (nodes), Tier XI complete (elite + rewards to 150). For each: ticks count/positions, fill segments, icons, tooltips, and design-system styling all correct.

- [ ] **Step 2: Confirm graceful degradation**

Temporarily force a resolver read to fail; expected: that category drops out, the rest of the bar still renders, hangar does not crash, error logged.

- [ ] **Step 3: Final commit / wrap up**

```bash
git add -A && git commit -m "test: in-game verification matrix complete

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Self-review notes

- **Spec coverage:** §3 bar model → Tasks 4–8 (cumulative positioning, remaining-only, stacked fill in builder/resolvers) + Task 12 (rendering). §4 state machine → Task 8. §5 architecture → file structure + Tasks 3/9/10/11/12. §6 data sources → Tasks 1 & 9. §7 UI → Tasks 10–13. §8 error handling → try/except in Tasks 9/11 + Task 14 Step 2. §9 testing → Phase 1 unit tests + Tasks 1/14. §11 open items → Task 1.
- **Elite-system feasibility risk** is gated explicitly in Task 1's STOP note.
- **Type consistency:** `VehicleSnapshot`/`Tick`/`ResearchProgressModel` field names are defined once in Task 3 and used unchanged in Tasks 4–11.
