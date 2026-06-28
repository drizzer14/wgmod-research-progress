# -*- coding: utf-8 -*-
"""Engine-free data types shared by the domain layer. 2/3 compatible.

EU 2.3 model (verified in docs/superpowers/research/decompiled-findings.md):
the selected vehicle's research is a single XP axis with two phases — tech-tree
research (modules + next vehicles, Tier XI included as an ordinary unlock), then
Field Modifications ("upgrades") once the vehicle is fully researched (elite).
There is no elite-milestone or Paragons system in EU, so those modes/fields are
intentionally absent.
"""


class Mode(object):
    TECH_TREE = "tech_tree"     # not fully researched: modules + next vehicles
    FIELD_MODS = "field_mods"   # elite: remaining field-modification ("upgrade") steps
    COMPLETE = "complete"       # elite and all field mods done (or none): full bar


class Tick(object):
    def __init__(self, xp_position, category, icon, name,
                 xp_gained, xp_required, affordable, completed, locked=False,
                 level=0):
        self.xp_position = xp_position
        # vehicle | module (tech-tree unlock kind) | fieldmod. Drives the
        # per-tick glyph in the view (a bar is all-tech-tree or all-field-mods,
        # so within tech-tree this distinguishes the next-tank tick from modules).
        self.category = category
        self.icon = icon
        self.name = name
        self.xp_gained = xp_gained
        self.xp_required = xp_required
        self.affordable = affordable
        self.completed = completed
        # True = prerequisites not yet met, so this item can't be researched yet
        # even if affordable (only meaningful for tech-tree unlocks).
        self.locked = locked
        # Field-modification level (1..N) -> the roman numeral shown in the
        # hexagon glyph. 0 for non-field-mod ticks.
        self.level = level


class UnlockItem(object):
    """A tech-tree unlock (module or next vehicle, including a Tier XI vehicle)."""
    def __init__(self, int_cd, name, icon, xp_cost, kind, researched, prereqs_met):
        self.int_cd = int_cd
        self.name = name
        self.icon = icon
        self.xp_cost = xp_cost
        self.kind = kind                  # 'module' | 'vehicle'
        self.researched = researched
        self.prereqs_met = prereqs_met


class ProgressionStep(object):
    """A field-modification step (post-progression tree node, paid with XP)."""
    def __init__(self, step_id, name, icon, xp_cost, unlocked, level=0):
        self.step_id = step_id
        self.name = name
        self.icon = icon
        self.xp_cost = xp_cost
        self.unlocked = unlocked          # already received/earned
        self.level = level                # field-mod level (1..N) -> roman numeral


class VehicleSnapshot(object):
    """Engine-free description of the selected vehicle's research state.

    The engine adapter produces this; the domain layer consumes only this.
    All XP fields are real ints (never None) and lists are in natural
    progression order.
    """
    def __init__(self, tier, is_elite, vehicle_xp, free_xp,
                 tech_unlocks=None, field_mod_steps=None,
                 fieldmods_done=0, fieldmods_total=0, vehicle_class=""):
        self.tier = tier                          # 1..11
        self.is_elite = is_elite                  # True = fully researched
        self.vehicle_xp = vehicle_xp              # unspent accumulated vehicle XP
        self.free_xp = free_xp                    # global free XP
        self.tech_unlocks = tech_unlocks or []    # [UnlockItem]
        self.field_mod_steps = field_mod_steps or []   # [ProgressionStep]
        # Researched / total field-mod LEVELS within the tier cap -> the header
        # counter (multi-mod choice slots are not counted).
        self.fieldmods_done = fieldmods_done
        self.fieldmods_total = fieldmods_total
        # vehicle class id ('mediumTank' etc.) for the elite badge in COMPLETE.
        self.vehicle_class = vehicle_class


class ResearchProgressModel(object):
    """Output of build_model(). Fill is two stacked segments (vehicle XP, then
    free XP); the view draws fill_vehicle first and fill_free on top."""
    def __init__(self, mode, scale_min, scale_max,
                 fill_vehicle, fill_free, ticks,
                 fieldmods_done=0, fieldmods_total=0, vehicle_class=""):
        self.mode = mode
        self.scale_min = scale_min
        self.scale_max = scale_max
        self.fill_vehicle = fill_vehicle       # first stacked segment (vehicle XP)
        self.fill_free = fill_free             # second stacked segment (free XP)
        self.ticks = ticks                     # [Tick], ordered by xp_position
        self.fieldmods_done = fieldmods_done   # researched/total field-mod levels
        self.fieldmods_total = fieldmods_total
        self.vehicle_class = vehicle_class     # for the elite badge in COMPLETE
