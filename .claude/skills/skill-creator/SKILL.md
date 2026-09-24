---
name: skill-creator
description: Create or revise a skill in this template's .claude/skills/. Use when adding a new workflow skill, adapting an external skill, or when an existing skill repeatedly misfires and needs restructuring.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Skill Creator

Adapted from anthropics/skills `skill-creator` for this template.

## When to create a skill (and when not to)

Create a skill for a **repeatable workflow with judgment** — a sequence an agent should follow the same way every time (implement, ship, debug). Do NOT create a skill for:
- A plain command sequence with no judgment → that's a `Makefile` target (or a `bin/` script called from one)
- A rule that always applies → that belongs in `CLAUDE.md`
- A one-off task → just do it

## Process

1. **Capture intent.** What should the skill do, when should it trigger, what does "done" look like? Ask the human about edge cases and success criteria before writing.
2. **Check for overlap.** Read the existing skills first — extend one rather than adding a near-duplicate.
3. **Draft SKILL.md** (structure below).
4. **Test it:** invoke the skill on 2–3 realistic cases (a real issue, a real bug). Watch where the agent hesitates or deviates — those are the unclear instructions.
5. **Iterate:** fix the instruction, not the symptom. Generalize from the failure; don't overfit to one example.

## Structure

```
.claude/skills/{kebab-case-name}/
├── SKILL.md            # required, keep under ~200 lines
└── scripts/            # optional: deterministic helpers (see e2e/scripts/with_server.py)
```

SKILL.md frontmatter:

```yaml
---
name: {kebab-case-name}
description: {What it does AND when to trigger — this line is the trigger mechanism, so name concrete situations. Err on the specific side; vague descriptions cause under-triggering.}
allowed-tools: {only the tools the skill needs}
---
```

## House conventions (every skill in this repo must follow)

- **Commands go through `make`** (or state why not). Never hardcode `uv run pytest --cov...` incantations that duplicate the Makefile.
- **Scopes are `backend` / `frontend`**; artifacts (plans, findings, workflow state) live in `plans/`.
- **GitHub via `gh` CLI** — no custom API wrappers.
- **TDD is assumed**, not re-litigated: a skill that produces code must say where the failing test comes first.
- **Long-running skills write `plans/workflow_state.md`** at step transitions so a resumed session can pick up (see implement/workon for the format and the validation rules).
- Write instructions as imperatives and explain *why* a rule exists — agents follow reasoning better than bare MUSTs. Reserve hard "MANDATORY" phrasing for real gates (like self-review before push).
- Bundle a script only when the operation is deterministic and would otherwise be reinvented each run; make it self-documenting (`--help`).

## After creating

- Adapting an external skill? Note the origin repo at the top ("Adapted from ...") so future updates can be diffed.
- Update `CLAUDE.md`'s workflow section and `README.md` if the skill is part of the standard flow.
- Commit the skill by itself with a `docs:` or `chore:` prefix.
