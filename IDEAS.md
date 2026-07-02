# Ideas Backlog

Recorded ideas for the mod. Entries are deleted once implemented.

## Open

### Add icons to tooltips' title block
Show a small icon in the tooltip header/title block so each tooltip is
identifiable at a glance — e.g. the module/component icon next to the tech-tree
name, or a per-category glyph next to the caption. Currently the header is
text-only (`wg-tip-caption` + `wg-tip-name`, built in `tooltipHtml()` in
`WGModResearch.js` ~264–300; styled in `WGModResearch.css`). Which icon per
category is TBD (tech-tree module icon vs. a generic per-mode glyph); the widget
already resolves `img://` game-icon URLs that could be reused. Feasibility of
inline images in the Gameface tooltip header unconfirmed.

### Bug: tier-XI "Next available" chips stop being hoverable/clickable after visiting an elite / exclusive-rewards vehicle
The tier-XI upgrade chips go dead (no hover, no click) after switching TO and
back FROM an elite vehicle or a tier-XI-with-exclusive-rewards vehicle. Root
cause: the elite render path (`renderElite`, `WGModResearch.js` ~992) sets
`hotEl._wgChips = []` but never resets `nextEl._wgSig`. So when you return to the
same skill-tree vehicle, `render()`'s rebuild gate (~782–789) finds the cached
`upgradesSig()` unchanged and takes the "keep chips" branch — re-showing the row
without rebuilding — but `_wgChips` was emptied by the elite path, so `chipAt()`
has nothing to hit-test. Likely fix: clear `nextEl._wgSig` (null it) whenever the
elite/rewards path empties `_wgChips`, forcing a rebuild on return.

### Tier-XI upgrades show text descriptions but not exact buff numbers
Tier-XI skill-tree node tooltips (the "final" end-tick and the "Upgrades
Available:" chips) render a localized sentence but often omit the actual
magnitude — e.g. "Reduces gun reload time by % in Pillbox mode." with no number.
`_skilltree_effect()` in `adapter/engine_adapter.py` (~732) fills the template's
`{value}` slot only when it finds a KPI of type `mul`/`add`; nodes whose KPI is
the generic unlabeled `value` (many signature/mechanic perks) fall through with
an empty value. Investigate reading the magnitude for those cases so the exact
buff shows. Sibling of the field-mod missing-numbers issue. Feasibility of
extracting the number for generic-`value` KPIs unconfirmed.

### Hide the bar outside the garage
Hide the bar on the playlists view and all other non-garage views — it should only
show in the actual garage. Extends the existing visibility mechanism (the `visible`
VM prop + loadout-overlay auto-hide in `gameface_bridge.py`); needs detection of
which view is mounted.

### Candidate settings (for the settings system in progress)
Everything below is currently hardcoded and would make a useful user setting. Listed
by likely demand; the settings framework being built is the vehicle for these.

**High impact**
- **Bar width / scale** (`WGModResearch.css`: `width: 520rem`). Shrink on small screens, grow on large.
- **Fill colors** — vehicle-XP, free-XP, complete, elite, elite-rewards fills (hardcoded hex in `WGModResearch.css` ~219–247). Accessibility/color-blind + theming.
- **Element visibility** — show/hide the category icon, the XP readout, the field-mod counter, and the "next available" skill-tree chips, for a minimal bar.

**Medium impact**
- **Shadow toggle/intensity** — pairs with the open drop-shadow idea above; let users dial it for light vs. dark hangars or turn it off (`WGModResearch.css` icon drop-shadow ~62, track shadow ~151).
- **Fill opacity** — free-XP fill and tick opacities (`WGModResearch.css` ~224/278/288/299).
- **Visibility override** — force always-show or never-show, on top of the existing auto-hide-in-loadout behavior (`gameface_bridge.py:482`, `visible` VM prop).
- **Click-to-research toggle** — view-only mode to prevent accidental spends.
- **Tooltips on/off** (`WGModResearch.js` hover handlers ~720–777).

**Low impact / niche**
- Custom or shortened mode labels (`WGModResearch.js` ~487).
- Click hit tolerance + hover proximity tuning (`WGModResearch.js` `CLICK_HIT_PCT` ~216, hover gate ~762).
- z-index, for conflicts with other UI mods (`WGModResearch.css:23`).
