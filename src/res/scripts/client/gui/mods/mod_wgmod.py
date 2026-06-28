# -*- coding: utf-8 -*-
"""WGMod research-progress bar — entry point.

Loaded by the WoT mod loader from a packaged .wotmod at client startup.
STAGE 1: inject a static test widget into the hangar via OpenWG Gameface, to
confirm the mount path. Data wiring (adapter -> domain -> ViewModel) follows.

Target runtime: Python 2.7 (BigWorld). OpenWG Gameface is a hard dependency.
"""
from debug_utils import LOG_NOTE, LOG_CURRENT_EXCEPTION

MOD_NAME = "Research Progress"
MOD_VERSION = "0.1.0"
WIDGET_NAME = "WGModResearch"
COUI = "coui://gui/gameface/mods/drizzer14/WGModResearch"


def _install():
    import openwg_gameface
    from gui.impl.lobby.hangar.random import random_hangar

    RH = random_hangar.RandomHangar
    if getattr(RH, "_wgmod_patched", False):
        return

    _orig_onLoading = RH._onLoading

    def _onLoading(self, *args, **kwargs):
        _orig_onLoading(self, *args, **kwargs)
        try:
            openwg_gameface.gf_mod_inject(
                self.getViewModel(), WIDGET_NAME,
                styles=[COUI + "/WGModResearch.css"],
                scripts=[COUI + "/WGModResearch.js"])
            LOG_NOTE("[%s] injected widget assets into hangar" % MOD_NAME)
        except Exception:
            LOG_CURRENT_EXCEPTION()

    RH._onLoading = _onLoading
    RH._wgmod_patched = True
    LOG_NOTE("[%s] v%s hangar patch installed" % (MOD_NAME, MOD_VERSION))


try:
    _install()
except Exception:
    LOG_CURRENT_EXCEPTION()
