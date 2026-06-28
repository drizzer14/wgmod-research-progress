# -*- coding: utf-8 -*-
from wgmod_research.domain import types as t


def resolve(snapshot):
    """Elite milestone ticks (remaining only), judged against EARNED XP only."""
    earned = snapshot.elite_earned_xp
    ticks = []
    for ms in snapshot.elite_milestones:
        if ms.xp_threshold <= earned:
            continue  # already reached
        ticks.append(t.Tick(
            xp_position=ms.xp_threshold, category="elite", icon=ms.icon, name=ms.name,
            xp_gained=earned, xp_required=ms.xp_threshold,
            # elite milestones are earned through play, never bought; only
            # not-yet-reached milestones are emitted, so this is always False.
            affordable=False, completed=False))
    return ticks
