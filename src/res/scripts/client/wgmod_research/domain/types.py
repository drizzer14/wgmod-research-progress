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
