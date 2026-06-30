# -*- coding: utf-8 -*-
from wgmod_research.domain import types as t
from wgmod_research.domain.resolvers import fieldmods


def _step(sid, cost, unlocked=False, level=0, description="",
          options=None, option_effects=None):
    return t.ProgressionStep(step_id=sid, name="fm%d" % sid, icon="fm%d.png" % sid,
                             xp_cost=cost, unlocked=unlocked, level=level,
                             description=description, options=options,
                             option_effects=option_effects)


def test_effect_passes_through_to_tick():
    snap = t.VehicleSnapshot(
        tier=9, is_elite=True, vehicle_xp=0, free_xp=0,
        field_mod_steps=[_step(1, 2000, description="+1% to concealment"),
                         _step(2, 4000)])
    ticks = fieldmods.resolve(snap)
    assert ticks[0].effect == "+1% to concealment"
    assert ticks[1].effect == ""


def test_choice_variant_names_and_effects_pass_through():
    # A choice level carries both variant names (options) and each variant's own
    # buffs (option_effects), aligned by index, onto the tick for the tooltip.
    snap = t.VehicleSnapshot(
        tier=9, is_elite=True, vehicle_xp=0, free_xp=0,
        field_mod_steps=[_step(1, 2000,
                               options=["Reinforced Suspension", "Lightweight Suspension"],
                               option_effects=["+30% to suspension durability",
                                               "+5% to hull traverse speed"])])
    ticks = fieldmods.resolve(snap)
    assert ticks[0].options == ["Reinforced Suspension", "Lightweight Suspension"]
    assert ticks[0].option_effects == ["+30% to suspension durability",
                                       "+5% to hull traverse speed"]


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


def test_start_position_offsets_cumulative_positions():
    snap = t.VehicleSnapshot(
        tier=9, is_elite=True, vehicle_xp=10000, free_xp=0,
        field_mod_steps=[_step(1, 2000), _step(2, 4000)])
    ticks = fieldmods.resolve(snap, start_position=500)
    # cumulative from 500: 2500, then 6500
    assert [tk.xp_position for tk in ticks] == [2500, 6500]


def test_level_passes_through_to_tick():
    snap = t.VehicleSnapshot(
        tier=10, is_elite=True, vehicle_xp=0, free_xp=0,
        field_mod_steps=[_step(1, 2000, level=3), _step(2, 4000, level=4)])
    ticks = fieldmods.resolve(snap)
    assert [tk.level for tk in ticks] == [3, 4]
    assert all(tk.category == "fieldmod" for tk in ticks)


def test_max_level_caps_by_tier():
    assert fieldmods.max_level(6) == 5
    assert fieldmods.max_level(7) == 5
    assert fieldmods.max_level(8) == 6
    assert fieldmods.max_level(9) == 7
    assert fieldmods.max_level(10) == 8
    assert fieldmods.max_level(11) == 8


def test_resolve_skips_levels_above_tier_cap():
    # the engine lists all 8 levels; a tier-6 tank can only reach level 5.
    steps = [_step(i, 3500, level=i) for i in range(1, 9)]  # levels 1..8
    snap = t.VehicleSnapshot(tier=6, is_elite=True, vehicle_xp=0, free_xp=0,
                             field_mod_steps=steps)
    ticks = fieldmods.resolve(snap)
    assert [tk.level for tk in ticks] == [1, 2, 3, 4, 5]
    # cumulative XP only spans the available levels
    assert ticks[-1].xp_position == 5 * 3500
