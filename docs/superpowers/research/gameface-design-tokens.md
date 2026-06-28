# WoT EU 2.3 Gameface design tokens (for native-looking widgets)

Pulled from the live client's CSS so our widget matches the game. Source of
truth: the `gui/gameface/_dist/production/**/*.css` files inside
`res/packages/gui-part{1..4}.pkg` (zip archives). To re-extract, unzip a pkg and
grep the CSS for `font-family`, `--color-`, `@font-face`.

## Fonts (engine-registered; use by bare family name, no @font-face needed)
- **`PFDINMax`** — primary UI face (DIN-style). Used by ~all body/label text.
- **`Warhelios`** — secondary/display face.
Our widget uses `font-family: "PFDINMax", sans-serif`. (The old `"$FieldFont"`
was an invalid Flash-era leftover.)

## Color tokens (CSS custom properties)
Defined on `:root` (origin file: `mono/dialogs/lib/lib.css`) and broadly
redefined across view bundles, so they resolve in the hangar document our widget
injects into. We still pass hex fallbacks in `var(--token, #hex)` for safety.

| Token | Value | Meaning |
|---|---|---|
| `--color-general-primary` | `#ede6d9` | primary text (parchment) |
| `--color-general-secondary` | `#b2afab` | muted text |
| `--color-general-tertiary` | `#8e867d` | dim / disabled |
| `--color-general-dark` | `#353638` | dark surface |
| `--color-currency-combat-experience` | `#dce0e0` | combat (vehicle) XP currency |
| `--color-currency-free-experience` | `#ecca9d` | free XP currency (tan) |
| `--color-currency-credits` | (see client) | credits |
| `--color-currency-gold` | (see client) | gold |
| `--color-status-done` | `#64ba21` | done / positive (green) |
| `--color-status-alert` | `#ee7000` | alert (orange) |
| `--color-status-error` | `#f31201` | error (red) |
| `--hangar-highlight-shadow` | `0rem 0rem 15rem rgba(23,23,23,.4), 0rem 0rem 5rem rgba(23,23,23,.4), 0rem 2rem rgba(0,0,0,.3)` | standard hangar text/element shadow |

## How our widget maps them (WGModResearch.css)
- Vehicle-XP fill → `--color-status-done` green (WoT's XP-progress color; owner pick).
- Free-XP fill → `--color-currency-free-experience` tan.
- COMPLETE bar → full `--color-status-done` green.
- Tick (idle/not-yet-affordable) → `--color-general-secondary`.
- Tick affordable → `--color-general-primary` (bright; stands out on the green fill).
- Tick locked (prereqs unmet) → `--color-general-tertiary`, opacity 0.45 (owner pick: gray, not orange).
- Label → secondary color + `--hangar-highlight-shadow`.

## Native styling references worth copying
- `lobby/hangar/subViews/VehicleParams/VehicleParams.css` — the EXACT sub-view we
  inject into. Its `HorizontalBar` uses `border: 1rem solid #7e7b68` and
  `box-shadow: inset 0 0 1rem rgba(255,255,190,.3)` — we mirror that on `.wg-track`.
- Tooltip views (e.g. `lobby/common/tooltips/*`) — reference when building real
  hover tooltips. NOTE: our root currently sets `pointer-events: none`, so DOM
  hover won't fire; tooltips need either pointer-events on ticks or wiring into
  WoT's ViewModel-driven tooltip manager.
