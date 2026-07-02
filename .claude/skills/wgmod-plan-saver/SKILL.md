---
name: wgmod-plan-saver
description: Capture ideas / future plans / bug reports for the Garage Progress Bar WoT mod into the IDEAS.md backlog — and research each submission against the codebase, saving an implementer-ready research note under IDEAS/. Delete backlog entries once shipped. Use whenever the user hands you an idea or bug to "record"/"save"/"note for later", asks you to be the "plan saver", wants to scan the repo for unrecorded ideas, or tells you an idea has been implemented and should be removed.
---

# Plan saver for the wgmod

Backlog keeper **and** researcher. The user hands over ideas and bug reports; for
each one you (1) record a short entry in `IDEAS.md`, and (2) research it against
the codebase and save a standalone research note the eventual implementer can
pick up cold. When an idea ships you delete its backlog entry. You do **not**
implement ideas under this role — you capture, research, organize, and prune.

The research step exists because whoever implements an idea is usually not the
person (or session) that captured it. A one-line backlog blurb loses the context
you had at capture time — which file, which function, why it's tricky. A saved
research note preserves that, so the implementer starts from findings instead of
from scratch. This is the difference between "add icons to tooltips" and "the
tooltip header is built in `tooltipHtml()` (WGModResearch.js ~264), it's
text-only today, and the widget already resolves `img://` icon URLs you can
reuse."

## Two artifacts per submission

1. **`IDEAS.md`** (repo root) — the scannable backlog. Short entries only.
2. **`IDEAS/<slug>.md`** — one research note per idea, deep enough to implement from.

### `IDEAS.md` — the backlog
- One `## Open` section. Each entry is an `### Title` + a short paragraph (1–4
  lines): the idea/bug and *why* it's wanted.
- End each entry with a pointer to its note: `→ Research: IDEAS/<slug>.md`.
- Keep it lean — the depth lives in the research note, not here.

### `IDEAS/<slug>.md` — the research note
`<slug>` is a kebab-case version of the title. Use this structure, dropping
sections that don't apply (e.g. "Root cause" is for bugs):

```
# Research: <Title>
_Submitted: <the user's words> · Status: open_

## Summary
The idea/bug in a sentence or two, and why it's wanted.

## Findings
What the code does today: the relevant path, files, and functions with
`file.py:line` refs. This is the meat — write what you actually learned.

## Root cause            (bugs only)
The mechanism, pinned to specific lines.

## Suggested approach
A starting direction, not a rigid spec. Flag uncertainty and feasibility
honestly rather than asserting it'll work.

## Touch points
The key files / functions the implementer will edit.

## Verification
How to confirm it works — tests to run, in-game steps, REPL probes.

## Open questions
Anything needing live confirmation or a user decision.
```

## Recording a submission

1. **Research first.** Launch an `Explore` agent (or explore inline for something
   small) to trace the real code path — don't guess from the description. Lean on
   the sibling skills for the map: `wgmod-architecture` for the Python data flow,
   `wgmod-widget` for the JS/CSS widget, `wgmod-debug-repl` for locating live game
   symbols in the decompiled client. For a bug, root-cause it down to the line;
   for a feature, find where it hooks in and what already exists to reuse.
2. **Write the research note** at `IDEAS/<slug>.md` using the structure above.
   Capture what you found — `file:line` refs, the mechanism, a suggested
   direction, how to verify. Be honest about what's still unconfirmed.
3. **Write the backlog entry** in `IDEAS.md`: a concise `### Title`, a 1–4 line
   blurb of intent (not an implementation plan), and the `→ Research:` pointer.
4. Cross-reference related entries/notes when they overlap (e.g. shadow ↔ shadow
   setting, color-blind ↔ fill-colors setting).
5. Be discriminating about what earns an entry: genuine pending ideas and bugs
   only — not routine code comments, not already-done work, not QA/release steps
   already tracked in the memory handoffs.

## Deleting a shipped idea

When the user says an idea is implemented (or you confirm it from the code),
remove its `### entry` from `IDEAS.md`. **Keep the research note** — it's durable
documentation of how the thing was figured out. Move it to `IDEAS/shipped/` to
keep the active research folder uncluttered, and (if quick) flip its top line to
`Status: shipped`. Don't keep a "Done" section in `IDEAS.md` — git history plus
the archived note are the record.

## Scanning for unrecorded ideas

If asked to find more ideas, sweep with an `Explore` agent for: code TODO/FIXME/
"later"/"for now"; doc notes phrased as planned/wishlist/known-limitation; and
"NEXT:"/"optional"/"outstanding" notes in the memory handoff files. Record only
the genuine pending ones — and research each the same way before it earns a note.

## Conventions

- This role edits `IDEAS.md` and files under `IDEAS/` (and this skill). No mod
  code changes — research reads the code, it doesn't touch it.
- Keep `IDEAS.md` entries scannable; the depth belongs in the research note.
  Group large clusters (e.g. the settings candidates) and ask whether to split
  them so individual items can be ticked off as they land.
