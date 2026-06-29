# Research Progress Bar — Installation Guide

A World of Tanks mod that adds a progress bar to the Garage showing the selected
vehicle's progression at a glance:

- **Tech-tree research** — modules and the next vehicle to unlock.
- **Field Modifications** — the post-progression upgrade ladder.
- **Elite Levels (prestige)** — current grade band and the tier-XI reward track.
- **Tier-XI vehicle skill-tree** — upgrade progress as a "% upgraded" readout.

It uses the game's own icons and hover tooltips, and refreshes live whenever you
switch vehicles.

---

## Requirements

| Requirement | Detail |
|-------------|--------|
| **Game** | World of Tanks **EU (Wargaming)** client, version **2.3.0.1**. Built and tested against this version. |
| **Dependency** | **OpenWG GameFace** — this is a *hard* dependency. The bar will not appear without it. |

> ⚠️ **Region note:** this build targets the **Wargaming EU/global** client. It is
> *not* built for the Lesta / Mir Tankov (RU) client, which is a diverged fork.

---

## Step 1 — Install OpenWG GameFace (do this first)

This mod renders through OpenWG's GameFace bridge and **will silently do nothing**
without it.

1. Get **OpenWG GameFace** from the official WG mod portal (**wgmods.net**, search
   "OpenWG GameFace") or the OpenWG project's GitHub releases.
2. Install it the same way as any `.wotmod`: drop its `.wotmod` file into your
   game's `mods\<version>\` folder (see Step 2 for where that is), or run its
   installer if it ships one.

If you already run other GameFace-based mods, you most likely already have it.

## Step 2 — Install the Research Progress Bar

1. Locate your World of Tanks install folder. The default is something like:

   ```
   C:\Games\World_of_Tanks_EU\
   ```

2. Open the version-matched mods folder inside it:

   ```
   <World of Tanks>\mods\2.3.0.1\
   ```

   > The folder name **must match your installed client version exactly**. If
   > `2.3.0.1` doesn't exist, create it, or use whichever version folder is already
   > there for your client. After a game update the version number changes and you
   > must move the mod into the new version folder.

3. Copy **`com.drizzer14.wgmod_0.1.0.wotmod`** into that `mods\2.3.0.1\` folder.

4. **Delete any older version** of this mod from the same folder first
   (e.g. `com.drizzer14.wgmod_0.0.x.wotmod`). Leaving old copies behind can make
   the client ignore the mod.

5. Fully **restart the game client** (not just return to Garage — exit and relaunch).

That's it. Your `mods\2.3.0.1\` folder should contain at least:

```
mods\2.3.0.1\
  <OpenWG GameFace>.wotmod
  com.drizzer14.wgmod_0.1.0.wotmod
```

---

## Verifying it works

1. Launch the game and go to the **Garage**.
2. Select any vehicle that still has research, field modifications, or elite levels
   remaining.
3. A progress bar appears in the vehicle-parameters area of the Garage, with the
   matching header icon and a Total-XP readout.
4. Hover the ticks/icons to see tooltips. Switch vehicles — the bar updates.

---

## Troubleshooting

**The bar doesn't show up at all.**
- Confirm **OpenWG GameFace** is installed in the same `mods\<version>\` folder.
  This mod does nothing without it.
- Confirm the `.wotmod` is in the folder that **matches your client version**
  (`mods\2.3.0.1\`, not `mods\` directly and not an old version folder).
- Make sure there is **no loose copy** of the mod under
  `res_mods\<version>\scripts\client\...` — a leftover there overrides the
  packaged mod and can blank it out. Only the `.wotmod` in `mods\<version>\`
  should be present.
- Fully restart the client after installing.

**The bar shows the wrong / a previous vehicle.**
- Make sure you're on the latest build (`0.1.0` or newer) — earlier builds had a
  refresh bug that this build fixes.

**It worked, then a game update broke it.**
- Game updates change the version folder. Move the `.wotmod` from the old
  `mods\<old-version>\` into the new `mods\<new-version>\`. A new client version
  may also need a rebuilt mod — check for an updated release.

**Special "7×7" / event hangars.**
- Some special battle-mode hangars don't expose the panel the bar attaches to, so
  the bar won't appear there. This is expected; it returns in the normal Garage.

---

## Uninstalling

Delete `com.drizzer14.wgmod_0.1.0.wotmod` from `mods\<version>\` and restart the
client. (Leave OpenWG GameFace in place if other mods use it.)

---

*Mod by drizzer14. Built for WoT EU 2.3.0.1.*
