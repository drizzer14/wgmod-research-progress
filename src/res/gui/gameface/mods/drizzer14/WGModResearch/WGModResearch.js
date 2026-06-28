// WGMod research-progress widget — STAGE 1: static mount test.
// Injected into the hangar view DOM by OpenWG Gameface (gf_mod_inject, scripts=[...]).
// Goal of this stage: confirm our code runs in the hangar document and can render.
(function () {
    "use strict";

    function mount() {
        try {
            if (document.getElementById("wgmod-test")) {
                return;
            }
            var box = document.createElement("div");
            box.id = "wgmod-test";
            box.textContent = "WGMOD research bar ✓ (stage 1)";
            document.body.appendChild(box);
            if (window.engine && engine.log) {
                engine.log("[wgmod] static test mounted");
            }
        } catch (e) {
            if (window.engine && engine.log) {
                engine.log("[wgmod] mount error: " + e);
            }
        }
    }

    if (typeof engine !== "undefined" && engine.whenReady && engine.whenReady.then) {
        engine.whenReady.then(mount);
    } else {
        mount();
    }
})();
