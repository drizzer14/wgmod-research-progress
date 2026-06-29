# -*- coding: utf-8 -*-
"""Pure resolver for the tier-XI "vehicle skill tree" upgrade. Engine-free, tested.

A tier-XI vehicle is reached by upgrading a tier-X through a branching skill tree
(post-progression with a tree id >= 10000), NOT the linear field-modification
ladder. Per the owner's directive the bar shows this as an AGGREGATE XP readout --
no per-node detail: the axis is the total XP still needed to fully upgrade the
vehicle (sum of the unreceived nodes' prices) and the fill is the player's banked
spendable XP (vehicle + free), exactly like the remaining-cost framing the
TECH_TREE / FIELD_MODS modes use. A header counter shows researched / total nodes.

resolve() returns a plain dict the builder maps onto ResearchProgressModel (the
same contract as elite.py), or None when this isn't a skill-tree vehicle or the
tree is already fully upgraded (so the builder falls through to ELITE / COMPLETE).
There are no ticks -- this is a single-segment fill bar.
"""


def resolve(snapshot):
    """Aggregate skill-tree upgrade progress, or None to fall through.

    None when the vehicle isn't a skill-tree vehicle, or its tree is fully
    upgraded (no XP remaining) -- in both cases the builder should continue to the
    elite / complete branches.
    """
    if not snapshot.is_skill_tree:
        return None
    remaining = int(snapshot.skilltree_remaining_xp or 0)
    if remaining <= 0:
        return None  # fully upgraded -> let the bar fall through to ELITE/COMPLETE
    return {
        "scale_min": 0,
        "scale_max": remaining,
        # banked spendable XP toward finishing the upgrade (drawn as the two
        # stacked segments by the builder: vehicle XP first, then free XP).
        "fill": snapshot.vehicle_xp + snapshot.free_xp,
        "done": int(snapshot.skilltree_done or 0),
        "total": int(snapshot.skilltree_total or 0),
    }
