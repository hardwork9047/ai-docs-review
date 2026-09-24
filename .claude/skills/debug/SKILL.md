---
name: debug
description: Systematic root-cause debugging for test failures, bugs, unexpected behaviour, build/CI failures. Use BEFORE attempting any fix — especially under time pressure, when a fix "looks obvious", or after a previous fix attempt failed.
allowed-tools: Read, Bash, Glob, Grep, Edit, Write
---

# Systematic Debugging

Adapted from obra/superpowers `systematic-debugging` for this template.

**Core principle: no fixes without root-cause investigation first.** Fixing a symptom without understanding the cause is a debugging failure, even if the symptom disappears.

Apply this to: failing tests, runtime bugs, unexpected behaviour, performance problems, CI failures. Apply it *especially* when the fix seems obvious, when you're in a hurry, or when previous fix attempts didn't stick — those are exactly the conditions that tempt guessing.

## Phase 1: Root Cause Investigation (mandatory before proposing ANY fix)

1. **Read the error completely.** Full stack trace, exit codes, warnings. Error text frequently contains the answer. Note exact files and line numbers.
2. **Reproduce deterministically.** Find the smallest command that triggers it:
   ```bash
   cd backend && uv run pytest tests/unit/test_x.py::test_case -x   # or
   cd frontend && pnpm vitest run tests/x.test.ts
   ```
   If you can't reproduce it reliably, gather more data before theorizing.
3. **Check recent changes.** `git log --oneline -15`, `git diff origin/main...HEAD`. Did a dependency, config, or environment change?
4. **Trace across boundaries.** This app has layers: frontend → HTTP → api router → domain → infra. For a cross-layer bug, log the data at each boundary (request payload, router input, domain input/output) to find *which* layer diverges from expectation — then investigate that layer only.
5. **Trace the bad value to its source.** Fix where the bad value originates, not where it crashes.

## Phase 2: Pattern Analysis

- Find working code in this repo that does something similar; read it fully, not skimming.
- List every difference between the working case and the broken case, including "insignificant" ones.

## Phase 3: Hypothesis and Minimal Test

1. State one concrete hypothesis: "X fails because Y."
2. Test it with the smallest possible change — one variable at a time. Never stack multiple speculative changes.
3. Confirmed → Phase 4. Refuted → new hypothesis. Don't layer fix attempts on top of each other; revert failed attempts first (`git checkout -- <file>` or `git stash`).

## Phase 4: Fix (TDD applies here)

1. **Write a failing regression test first** — this is the template's normal TDD rule applied to bugs:
   - backend: `backend/tests/unit/` or `tests/integration/`
   - frontend: `frontend/tests/`
   - Run it, confirm it fails *because of the bug*, commit with `test:` prefix.
2. **Implement one fix targeting the root cause.** No drive-by refactoring, no scope creep. Commit with `fix:`.
3. **Verify:** the regression test passes, and `make check` still passes. Use `/verify` discipline — claim "fixed" only with fresh command output as evidence.

## Escalation Rule

Count your fix attempts. **After 3 failed fixes, stop.** Symptoms: each fix reveals a new problem elsewhere; fixes keep requiring wider changes. This signals an architectural problem, not a bug. Write up what you've learned (hypotheses tested, evidence gathered) and discuss with the human before attempting fix #4.

## Red Flags — stop and return to Phase 1

- "Quick fix now, investigate later" / "it's probably X"
- Changing multiple things and re-running tests to "see what happens"
- Proposing a fix before you can state the root cause in one sentence
- "One more try" after 2+ failed attempts

## Recording

If this debugging session happens inside `/implement` or `/workon`, note the root cause and the regression test in the plan file (or the findings file at review time). A one-line entry is enough: `Root cause: {sentence}. Regression test: {path}::{name}`.
