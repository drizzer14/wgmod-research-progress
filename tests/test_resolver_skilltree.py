# -*- coding: utf-8 -*-
from wgmod_research.domain import types as t
from wgmod_research.domain.resolvers import skilltree


def _snap(is_skill_tree=True, remaining=120000, done=3, total=12,
          vehicle_xp=40000, free_xp=5000):
    return t.VehicleSnapshot(
        tier=10, is_elite=True, vehicle_xp=vehicle_xp, free_xp=free_xp,
        is_skill_tree=is_skill_tree, skilltree_remaining_xp=remaining,
        skilltree_done=done, skilltree_total=total)


def test_not_skill_tree_returns_none():
    assert skilltree.resolve(_snap(is_skill_tree=False)) is None


def test_fully_upgraded_returns_none():
    # No XP remaining -> let the builder fall through to ELITE / COMPLETE.
    assert skilltree.resolve(_snap(remaining=0)) is None


def test_remaining_drives_scale_and_counts():
    res = skilltree.resolve(_snap(remaining=120000, done=3, total=12))
    assert res["scale_min"] == 0
    assert res["scale_max"] == 120000          # axis = XP to fully upgrade
    assert res["done"] == 3
    assert res["total"] == 12


def test_fill_is_total_spendable_xp():
    # fill = banked vehicle XP + free XP (the builder draws it as two segments).
    res = skilltree.resolve(_snap(vehicle_xp=40000, free_xp=5000))
    assert res["fill"] == 45000
