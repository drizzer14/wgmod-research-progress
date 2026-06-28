# -*- coding: utf-8 -*-
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
