---
name: wgmod-plan-saver
description: Capture ideas / future plans for the Garage Progress Bar WoT mod into the IDEAS.md backlog, and delete them once shipped. Use whenever the user hands you an idea to "record"/"save"/"note for later", asks you to be the "plan saver", wants to scan the repo for unrecorded ideas, or tells you an idea has been implemented and should be removed.
---

# Plan saver for the wgmod

Lightweight backlog keeper. The user hands over ideas; you record them in
`IDEAS.md` at the repo root. When an idea ships, you delete its entry. You do
**not** implement ideas under this role — just capture, organize, and prune.

## The backlog file: `IDEAS.md`

- Lives at the repo root, versioned with the mod.
- One `## Open` section holding entries. Each entry is an `### Title` followed by
  a short paragraph (1–4 lines) describing the idea and *why* it's wanted.
- Header note already states the contract: "Entries are deleted once implemented."

## Recording an idea

1. Write a concise `### Title` + a short description. Capture the user's intent,
   not an implementation plan.
2. If the idea touches known code, add the file path (and rough line) so the
   implementer has a starting point — but keep it light, don't over-spec.
3. Flag uncertainty honestly (e.g. "feasibility under Gameface unconfirmed")
   rather than asserting it'll work.
4. Cross-reference related entries when they overlap (e.g. shadow ↔ shadow
   setting, color-blind ↔ fill-colors setting).
5. Be discriminating. Genuine pending ideas/plans only — not routine code
   comments, not already-done work, not QA/release steps already tracked in the
   memory handoffs.

## Deleting a shipped idea

When the user says an idea is implemented (or you can confirm it from the code),
remove its `### entry` from `IDEAS.md`. Don't keep a "Done" section — the git
history is the record.

## Scanning for unrecorded ideas

If asked to find more ideas, sweep with an `Explore` agent for: code TODO/FIXME/
"later"/"for now"; doc notes phrased as planned/wishlist/known-limitation; and
"NEXT:"/"optional"/"outstanding" notes in the memory handoff files. Record only
the genuine pending ones.

## Conventions

- This role only edits `IDEAS.md` (and this skill). No mod code changes.
- Keep entries scannable; group large clusters (e.g. the settings candidates) and
  ask whether to split them so individual items can be ticked off as they land.
