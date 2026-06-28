from wgmod_research.domain import types as t


def test_mode_constants_are_distinct():
    modes = {t.Mode.TECH_TREE, t.Mode.RESEARCH_PLUS_TIERXI,
             t.Mode.TIERXI_NODES, t.Mode.ELITE, t.Mode.ELITE_PLUS_TIERXI_REWARDS}
    assert len(modes) == 5


def test_tick_holds_fields():
    tick = t.Tick(xp_position=1500, category="techtree", icon="gun.png",
                  name="Gun X", xp_gained=0, xp_required=1500,
                  affordable=False, completed=False)
    assert tick.xp_position == 1500
    assert tick.category == "techtree"
    assert tick.affordable is False


def test_model_defaults_empty_ticks():
    m = t.ResearchProgressModel(mode=t.Mode.TECH_TREE, scale_min=0, scale_max=0,
                                fill_spendable=0, fill_earned=0, ticks=[])
    assert m.ticks == []
    assert m.mode == t.Mode.TECH_TREE
