# -*- coding: utf-8 -*-
from wgmod_research.domain import types as t
from wgmod_research.domain.resolvers import techtree


def _unlock(cd, cost, researched=False, prereqs_met=True, kind="module",
            kind_label="", prereq_names=None):
    return t.UnlockItem(int_cd=cd, name="i%d" % cd, icon="i%d.png" % cd,
                        xp_cost=cost, kind=kind,
                        researched=researched, prereqs_met=prereqs_met,
                        kind_label=kind_label, prereq_names=prereq_names)


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


def test_category_reflects_unlock_kind():
    snap = t.VehicleSnapshot(
        tier=10, is_elite=False, vehicle_xp=0, free_xp=0,
        tech_unlocks=[_unlock(1, 600, kind="module"),
                      _unlock(2, 2000, kind="vehicle")])  # next-tank unlock
    ticks = techtree.resolve(snap)
    # ordered by cost: module tick first, vehicle tick second
    assert [tk.category for tk in ticks] == ["module", "vehicle"]


def test_locked_reflects_prereqs_met():
    snap = t.VehicleSnapshot(
        tier=5, is_elite=False, vehicle_xp=1000, free_xp=500,
        tech_unlocks=[_unlock(3, 600, prereqs_met=True),
                      _unlock(2, 2000, prereqs_met=False)])
    ticks = techtree.resolve(snap)
    # ordered by cost: 600 (prereqs met -> not locked), 2000 (unmet -> locked)
    assert [tk.locked for tk in ticks] == [False, True]


def test_kind_label_and_prereq_names_pass_through_to_ticks():
    snap = t.VehicleSnapshot(
        tier=10, is_elite=False, vehicle_xp=0, free_xp=0,
        tech_unlocks=[
            _unlock(1, 600, kind="module", kind_label="Gun"),
            _unlock(2, 2000, kind="vehicle", kind_label="Tier IX",
                    prereqs_met=False, prereq_names=["Some Engine", "Some Turret"])])
    ticks = techtree.resolve(snap)  # ordered by cost: module (600), vehicle (2000)
    assert [tk.kind_label for tk in ticks] == ["Gun", "Tier IX"]
    assert ticks[0].prereq_names == []
    assert ticks[1].prereq_names == ["Some Engine", "Some Turret"]
