// WGMod research-progress widget. Injected into the hangar document by OpenWG.
// Reads our data model (exposed as `wgResearch` on the host sub-view's model)
// via ModelObserver, and renders a single-axis XP bar with stacked fill + ticks.
import { ModelObserver } from "../../libs/model.js";

const observer = ModelObserver("WGModResearch");

// Category icon for the bar header -- the same art the in-game "Vehicle
// management" menu uses for each section. Keyed by bar mode.
const CAT_ICON = {
    tech_tree: "img://gui/maps/icons/hangar/vehicleMenu/large/research.png",
    field_mods: "img://gui/maps/icons/hangar/vehicleMenu/large/fieldModification.png",
};

// Elite badge for the COMPLETE state: the in-game class+elite icon. veh class
// ids use '-' (AT-SPG); the icon files use '_' (AT_SPG_elite.png).
function eliteIcon(vehClass) {
    if (!vehClass) return "";
    return "img://gui/maps/icons/vehicleTypes/md/" +
        vehClass.replace(/-/g, "_") + "_elite.png";
}

const ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"];
function romanize(n) {
    n = n | 0;
    if (n > 0 && n < ROMAN.length) return ROMAN[n];
    return n > 0 ? String(n) : "";
}

function setCatIcon(el, url) {
    if (url) {
        el.style.backgroundImage = "url('" + url + "')";
        el.style.display = "block";
    } else {
        el.style.backgroundImage = "";
        el.style.display = "none";
    }
}

function setUpgrades(el, done, total) {
    if (total > 0) {
        el.textContent = done + "/" + total;
        el.style.display = "block";
    } else {
        el.textContent = "";
        el.style.display = "none";
    }
}

// wulf exposes nested viewmodels / array elements wrapped as { value: ... }.
function unwrap(x) {
    return x && x.value !== undefined ? x.value : x;
}

function ensureRoot() {
    let root = document.getElementById("wgmod-root");
    if (!root) {
        root = document.createElement("div");
        root.id = "wgmod-root";
        root.innerHTML =
            '<div class="wg-head">' +
            '<div class="wg-cat-icon"></div>' +
            '<div class="wg-label"></div>' +
            '<div class="wg-upgrades"></div>' +
            "</div>" +
            '<div class="wg-track">' +
            '<div class="wg-fill wg-fill-veh"></div>' +
            '<div class="wg-fill wg-fill-free"></div>' +
            '<div class="wg-ticks"></div>' +
            "</div>";
        document.body.appendChild(root);
    }
    return root;
}

function arrLen(a) {
    if (!a) return 0;
    if (typeof a.length === "number") return a.length;
    if (typeof a.count === "number") return a.count;
    return 0;
}

function render(model) {
    const root = ensureRoot();
    const label = root.querySelector(".wg-label");
    const catIcon = root.querySelector(".wg-cat-icon");
    const upgradesEl = root.querySelector(".wg-upgrades");
    const data = unwrap(model && model.wgResearch);

    if (!data) {
        const keys = model ? Object.keys(model).join(",") : "no-model";
        label.textContent = "WGMOD: waiting for data | keys=" + keys;
        setCatIcon(catIcon, "");
        setUpgrades(upgradesEl, 0, 0);
        return;
    }

    // Field-mod progress counter (researched / total levels within the tier
    // cap) -- shown whenever the vehicle has field mods, regardless of mode.
    setUpgrades(upgradesEl, data.fieldModsDone || 0, data.fieldModsTotal || 0);

    const mode = data.mode;
    const sMin = data.scaleMin || 0;
    const sMax = data.scaleMax || 0;
    const fv = data.fillVehicle || 0;
    const ff = data.fillFree || 0;
    const span = Math.max(sMax - sMin, 1);
    const pct = (xp) => Math.max(0, Math.min(100, ((xp - sMin) / span) * 100));

    const vehEl = root.querySelector(".wg-fill-veh");
    const freeEl = root.querySelector(".wg-fill-free");
    const ticksEl = root.querySelector(".wg-ticks");

    if (mode === "complete" || sMax <= sMin) {
        root.className = "wg-complete";
        label.textContent = "Fully researched";
        setCatIcon(catIcon, eliteIcon(data.vehicleClass));  // class + elite badge
        vehEl.style.left = "0%";
        vehEl.style.width = "100%";
        freeEl.style.width = "0%";
        ticksEl.innerHTML = "";
        return;
    }
    root.className = "";

    label.textContent = mode === "field_mods" ? "Field Modifications" : "Research";
    setCatIcon(catIcon, CAT_ICON[mode] || "");

    const vehW = pct(sMin + fv);
    const freeW = Math.max(0, pct(sMin + fv + ff) - vehW);
    vehEl.style.left = "0%";
    vehEl.style.width = vehW + "%";
    freeEl.style.left = vehW + "%";
    freeEl.style.width = freeW + "%";

    ticksEl.innerHTML = "";
    const ticks = data.ticks;
    const n = arrLen(ticks);
    for (let i = 0; i < n; i++) {
        const t = unwrap(ticks[i] !== undefined ? ticks[i] : ticks.get && ticks.get(i));
        if (!t) continue;
        const mark = document.createElement("div");
        mark.className =
            "wg-tick wg-cat-" + (t.category || "x") +
            (t.locked ? " wg-locked" : t.affordable ? " wg-aff" : "");
        mark.style.left = pct(t.position) + "%";
        mark.title = (t.name || "") + " — " + (t.xpRequired || 0) + " XP";

        if (t.category === "fieldmod") {
            // Field-mod ticks: a hexagon glyph with the level roman numeral
            // (mirrors the in-game field-modification level badges).
            const hex = document.createElement("div");
            hex.className = "wg-tick-hex";
            const num = document.createElement("span");
            num.textContent = romanize(t.level);
            hex.appendChild(num);
            mark.appendChild(hex);
        } else if (t.icon) {
            // Tech-tree ticks: the real in-game art (module-type glyph / framed
            // vehicle icon) as an img:// URL. Rendered as a background-image (not
            // <img>): Gameface honors background-size:contain for aspect-correct
            // scaling, whereas it clips an <img>. A URL that fails just renders
            // nothing (graceful).
            const img = document.createElement("div");
            img.className = "wg-tick-img";
            img.style.backgroundImage = "url('" + t.icon + "')";
            mark.appendChild(img);
        }
        ticksEl.appendChild(mark);
    }
}

engine.whenReady.then(() => {
    observer.onUpdate(render);
    observer.subscribe();
    render(observer.model);
});
