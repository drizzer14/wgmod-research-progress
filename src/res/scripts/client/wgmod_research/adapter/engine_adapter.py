# -*- coding: utf-8 -*-
"""PC-only engine adapter: read the live WoT EU 2.3 client into a VehicleSnapshot.

This is the only module that touches game symbols. Every category read is wrapped
in try/except so one unreadable system degrades gracefully (spec section 8): the
category yields a safe empty default and the rest of the bar still renders.

Symbols verified against the EU 2.3 decompiled source — see
docs/superpowers/research/decompiled-findings.md.
"""
from CurrentVehicle import g_currentVehicle
from helpers import dependency
from skeletons.gui.shared import IItemsCache
from items import getTypeOfCompactDescr
from gui.shared.gui_items import GUI_ITEM_TYPE
from debug_utils import LOG_CURRENT_EXCEPTION

from wgmod_research.domain import types as t
from wgmod_research.domain.resolvers.fieldmods import max_level


def _items_cache():
    # NOTE: dependency.instance() returns the live service. dependency.descriptor()
    # is only valid as a class attribute (descriptor protocol) and raises if called
    # at module level -- verified in-game.
    return dependency.instance(IItemsCache)


def build_snapshot():
    """Read the selected vehicle into a VehicleSnapshot, or None if unavailable."""
    if not g_currentVehicle.isPresent():
        return None
    try:
        veh = g_currentVehicle.item
    except Exception:
        LOG_CURRENT_EXCEPTION()
        return None

    stats = _safe_stats()
    free_xp = _safe_int(lambda: stats.freeXP, 0) if stats is not None else 0
    unlocks = _safe(lambda: stats.unlocks, set()) if stats is not None else set()

    fm_steps, fm_done, fm_total = _read_post_progression(veh)

    return t.VehicleSnapshot(
        tier=_safe_int(lambda: veh.level, 0),
        is_elite=_safe(lambda: bool(veh.isElite), False),
        vehicle_xp=_safe_int(lambda: veh.xp, 0),
        free_xp=int(free_xp),
        tech_unlocks=_read_tech_unlocks(veh, unlocks),
        field_mod_steps=fm_steps,
        fieldmods_done=fm_done, fieldmods_total=fm_total,
        vehicle_class=_safe(lambda: veh.type, "") or "")


# --- helpers ---------------------------------------------------------------

def _safe(fn, default):
    try:
        value = fn()
        return default if value is None else value
    except Exception:
        LOG_CURRENT_EXCEPTION()
        return default


def _safe_int(fn, default):
    return int(_safe(fn, default))


def _safe_stats():
    try:
        return _items_cache().items.stats
    except Exception:
        LOG_CURRENT_EXCEPTION()
        return None


def _read_tech_unlocks(veh, unlocks):
    """Tech-tree unlocks: modules + next vehicles (incl. Tier XI) via the
    vehicle's unlock graph. getUnlocksDescrs() yields (idx, xpCost, intCD, prereqs)."""
    try:
        cache = _items_cache()
        out = []
        for _idx, xp_cost, int_cd, prereqs in veh.getUnlocksDescrs():
            try:
                is_vehicle = getTypeOfCompactDescr(int_cd) == GUI_ITEM_TYPE.VEHICLE
                item = cache.items.getItemByCD(int_cd)
                name = getattr(item, "userName", "") or ""
                # item.icon is the right art for both kinds, as img:// URLs:
                #  - module: the generic module-TYPE glyph (chassis/engine/tower/
                #    gun/radio under img://gui/maps/icons/modules/, 48x48) -- the
                #    same icons the in-battle info panel uses.
                #  - vehicle: the framed tech-tree-node icon (~160x100). NOT
                #    iconSmall -- that's the carousel contour strip, cropped
                #    edge-to-edge so it reads as "cut off".
                icon = getattr(item, "icon", "") or ""
            except Exception:
                LOG_CURRENT_EXCEPTION()
                is_vehicle, name, icon = False, "", ""
            out.append(t.UnlockItem(
                int_cd=int_cd, name=name, icon=icon, xp_cost=int(xp_cost),
                kind=("vehicle" if is_vehicle else "module"),
                researched=(int_cd in unlocks),
                prereqs_met=all(p in unlocks for p in prereqs)))
        return out
    except Exception:
        LOG_CURRENT_EXCEPTION()
        return []


def _read_post_progression(veh):
    """Read the vehicle's post-progression into (field_mod_steps, fm_done,
    fm_total), all clamped to the tier's level cap (the engine lists greyed
    levels above the cap; skip them). Verified in-game:

      - LEVELED field modifications (FeatureModItem / SimpleModItem /
        RoleSlotModItem): cost XP (price.xp), one per level -> bar hexagons, with
        getLevel() driving the roman numeral.
      - Multi-mod choice slots (MultiModsItem): cost no XP -> NOT on the bar.

    The counter (fm_done / fm_total) spans the LEVELED field mods within the cap
    (one per level, so fm_total == the tier cap) -- received vs total. Multi-mod
    choice slots are not counted. Only meaningful for elite vehicles with
    post-progression."""
    steps = []
    fm_done = 0
    fm_total = 0
    try:
        if not veh.isElite or not veh.isPostProgressionExists:
            return steps, 0, 0
        cap = max_level(_safe_int(lambda: veh.level, 0))
        pp = veh.postProgression
        for step in pp.iterOrderedSteps():
            try:
                level = int(_safe(lambda: step.getLevel(), 0))
                if level and level > cap:
                    continue  # level not unlockable at this tier (greyed in-game)
                received = bool(step.isReceived())
                # multi-mod choice slots are not "field mod levels": neither bar
                # hexagons nor part of the researched/total counter.
                if type(step.action).__name__ == "MultiModsItem":
                    continue
                # counter spans the leveled field mods within the cap
                fm_total += 1
                if received:
                    fm_done += 1
                price = step.getPrice()
                xp_cost = int(getattr(price, "xp", 0) or 0)
                if xp_cost <= 0:
                    continue  # non-XP leveled step (rare) -> not on the bar
                name, icon = _step_label(step)
                steps.append(t.ProgressionStep(
                    step_id=step.stepID, name=name, icon=icon,
                    xp_cost=xp_cost, unlocked=received,
                    level=level))
            except Exception:
                LOG_CURRENT_EXCEPTION()
                continue
        return steps, fm_done, fm_total
    except Exception:
        LOG_CURRENT_EXCEPTION()
        return steps, fm_done, fm_total


def _step_label(step):
    """Best-effort name/icon for a field-mod step via its action model.
    Falls back to the step id; refined during in-game verification."""
    try:
        action = getattr(step, "action", None)
        if action is not None:
            name = getattr(action, "locName", None) or getattr(action, "name", "") or ""
            icon = getattr(action, "imgName", "") or ""
            return name, icon
    except Exception:
        LOG_CURRENT_EXCEPTION()
    return ("step %s" % getattr(step, "stepID", "?")), ""
