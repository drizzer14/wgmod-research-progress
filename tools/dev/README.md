# Dev tools (WoT 2.3 EU)

In-game introspection + the real dev loop for this mod. **Not shipped** with the mod.

## Environment (this PC)
- WoT install: `D:\Games\World_of_Tanks_EU`, version **2.3.0.1**. OpenWG Gameface installed (`mods\2.3.0.1\net.openwg`).
- **Python 2.7.18** at `C:\Python27\python.exe` — packaging only (compiles `.pyc`; bytecode is 2.7-locked).
- **Python 3.13** at `%LOCALAPPDATA%\Programs\Python\Python313\python.exe` — runs pytest + the REPL client.
- Git at `C:\Program Files\Git\cmd\git.exe`, `core.longpaths=true` (needed for decompiled clones).

## The dev loop (WoT 2.3 loads ONLY `.wotmod`)
Loose `res_mods\<version>\scripts` does **not** load in 2.3, and `res_mods` outranks `.wotmod`
(a stale loose copy SHADOWS the package → client ignores the mod). So always:

```
# 1) close the WoT client (file locks); then build+deploy the real mod:
& "C:\Python27\python.exe" build\deploy_wotmod.py "D:\Games\World_of_Tanks_EU" 2.3.0.1
# 2) relaunch the client. (OpenWG may auto-restart once when res_map changes.)
```
`deploy_wotmod.py` auto-cleans old `com.drizzer14.wgmod_[0-9]*.wotmod` and loose leftovers.

Unit tests (engine-free domain layer, Python 3):
```
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" -m pytest -q   # expect green
```

## Debug REPL (live introspection)
`com.drizzer14.wgmod_debug.wotmod` runs a TCP REPL on **127.0.0.1:2223** in the client.
- Build/deploy it (client closed):
  `& "C:\Python27\python.exe" tools\dev\build_debug_wotmod.py "D:\Games\World_of_Tanks_EU" 2.3.0.1`
- Drive it from the host (client running, in Garage):
  `& "<py3>" tools\dev\repl_client.py "<expr>"` or `--file cmds.txt`
- One command per line; state shared only within one run → put interdependent
  commands in one `--file`. For multi-line code: write a `.py` and send
  `execfile(r'<abs path>')` as one command.
- Keep the debug package SLIM (only `mod_wgmod_debug.pyc`). If it also ships
  `wgmod_research`, it conflicts with the real mod and WoT ignores it.

### Handy REPL snippets
```python
# current vehicle -> snapshot -> model
from CurrentVehicle import g_currentVehicle
from wgmod_research.adapter import engine_adapter
from wgmod_research.domain.builder import build_model
m = build_model(engine_adapter.build_snapshot())
(m.mode, m.scale_min, m.scale_max, m.fill_vehicle, m.fill_free, len(m.ticks))

# force a refresh of the mounted widget
from wgmod_research.bridge import gameface_bridge as B
B.refresh()
```

## Decompiled source (re-clone as needed; not in repo)
Match the client's branch/region — use the **EU** branch, not the RU default:
```
& $git clone --depth 1 --branch 2.3 --single-branch https://github.com/StranikS-Scan/WorldOfTanks-Decompiled.git wot-eu
```
(The default branch is MirTankov/Lesta RU — different client. Cross-check against
the live `res/packages/scripts.pkg` by listing module filenames.)
