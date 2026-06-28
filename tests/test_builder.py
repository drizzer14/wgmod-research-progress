# -*- coding: utf-8 -*-
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


def test_elite_potential_tierxi_only_is_research_plus_tierxi():
    pot = t.UnlockItem(0, "Potential T11", "pot.png", 300000, "vehicle", False, True)
    snap = t.VehicleSnapshot(tier=10, is_elite=True, vehicle_xp=0, free_xp=0,
                             potential_tierxi=pot)  # no field mods, no real successor
    m = build_model(snap)
    assert m.mode == t.Mode.RESEARCH_PLUS_TIERXI
    assert [tk.category for tk in m.ticks] == ["potentialXI"]
    assert m.ticks[0].xp_position == 300000
    assert m.scale_max == 300000


def test_elite_fieldmods_only_no_successor_is_research_plus_tierxi():
    snap = t.VehicleSnapshot(
        tier=8, is_elite=True, vehicle_xp=0, free_xp=0,
        field_mod_steps=[t.ProgressionStep(1, "fm1", "fm1.png", 1000, False),
                         t.ProgressionStep(2, "fm2", "fm2.png", 2000, False)])
    m = build_model(snap)
    assert m.mode == t.Mode.RESEARCH_PLUS_TIERXI
    assert [tk.category for tk in m.ticks] == ["fieldmod", "fieldmod"]
    assert [tk.xp_position for tk in m.ticks] == [1000, 3000]
    assert m.scale_max == 3000


def test_elite_partial_fieldmods_then_successor_stacks_correctly():
    succ = _u(99, 100000, kind="vehicle")
    snap = t.VehicleSnapshot(
        tier=10, is_elite=True, vehicle_xp=0, free_xp=0,
        field_mod_steps=[t.ProgressionStep(1, "fm1", "fm1.png", 1000, True),   # unlocked, skip
                         t.ProgressionStep(2, "fm2", "fm2.png", 3000, False)],
        tierxi_successor=succ)
    m = build_model(snap)
    # remaining fm2 at 3000; successor stacked at 3000 + 100000
    assert [tk.category for tk in m.ticks] == ["fieldmod", "tierXI"]
    assert [tk.xp_position for tk in m.ticks] == [3000, 103000]
    assert m.scale_max == 103000


def test_build_model_rich_research_plus_tierxi_end_to_end():
    succ = _u(99, 200000, kind="vehicle")
    snap = t.VehicleSnapshot(
        tier=10, is_elite=True, vehicle_xp=4000, free_xp=1000,  # spendable 5000
        field_mod_steps=[t.ProgressionStep(1, "fm1", "fm1.png", 2000, False),
                         t.ProgressionStep(2, "fm2", "fm2.png", 1000, True),  # done, skip
                         t.ProgressionStep(3, "fm3", "fm3.png", 3000, False)],
        tierxi_successor=succ)
    m = build_model(snap)
    assert m.mode == t.Mode.RESEARCH_PLUS_TIERXI
    assert [tk.category for tk in m.ticks] == ["fieldmod", "fieldmod", "tierXI"]
    assert [tk.xp_position for tk in m.ticks] == [2000, 5000, 205000]
    positions = [tk.xp_position for tk in m.ticks]
    assert positions == sorted(positions)          # monotonic left-to-right
    assert m.scale_min == 0
    assert m.scale_max == 205000
    assert m.fill_spendable == 5000
    assert m.fill_earned == 0
    assert [tk.affordable for tk in m.ticks] == [True, True, False]


def test_elite_maxed_clamps_to_cap():
    snap = t.VehicleSnapshot(
        tier=9, is_elite=True, vehicle_xp=0, free_xp=0,
        field_mod_steps=[t.ProgressionStep(1, "fm1", "fm1.png", 2000, True)],  # done
        elite_earned_xp=300000, elite_cap_level=150,
        elite_milestones=[t.Milestone(10, 10000, "Bronze", "b.png"),
                          t.Milestone(150, 200000, "Gold", "g.png")])  # all reached
    m = build_model(snap)
    assert m.mode == t.Mode.ELITE
    assert m.ticks == []            # nothing remaining
    assert m.scale_max == 200000    # anchored to cap, not collapsed to baseline
    assert m.scale_min == 200000    # clamped (earned 300k exceeds cap 200k)
    assert m.fill_earned == 200000  # fill clamped to cap
