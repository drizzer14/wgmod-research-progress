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
