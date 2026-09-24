---
name: verify
description: Evidence gate before claiming work is complete, fixed, or passing — and before any commit, PR, or handoff. Requires running the verification command freshly and reading its output before making a success claim.
allowed-tools: Bash, Read
---

# Verification Before Completion

Adapted from obra/superpowers `verification-before-completion` for this template.

**Iron law: no completion claims without fresh verification evidence.** "Should work", "probably passes", and satisfaction words ("Done!", "Fixed!") before running the command are the failure mode this skill exists to stop.

## The Gate (run before every success claim)

1. **IDENTIFY** — which command proves the claim?
2. **RUN** — execute it freshly, in full. A cached or remembered result doesn't count.
3. **READ** — the whole output: exit code, failure counts, warnings.
4. **VERIFY** — does the output actually support the claim? If not, report what you found instead.
5. **CLAIM** — only now, and include the evidence (numbers, not adjectives).

## Claim → Command Map (this template)

| Claim | Evidence required |
|---|---|
| "Tests pass" | `make test` (or `make test-{scope}`) showing `N passed, 0 failed` and coverage ≥ 80% |
| "Lint/format clean" | `make lint` exiting 0 |
| "Types are fine" | `make typecheck` exiting 0 |
| "Ready to push / PR" | `make check` exiting 0 — the full gate, no shortcuts |
| "Bug is fixed" | The regression test passes AND the original reproduction no longer triggers |
| "Regression test works" | Red-green cycle: test fails on the pre-fix code, passes on the fixed code. If you never saw it red, you don't know it tests anything |
| "The app runs" | Actually start it (`make dev-backend`, hit `/health`; `make dev-frontend`, load the page) — compiling is not running |
| "Subagent completed X" | Check `git diff` / the files yourself; never relay an agent's self-report as verified fact |

## Red-Flag Language (in your own output)

Stop and run the gate when you catch yourself writing: "should", "probably", "seems to", "I believe", "ought to" — or any success statement not immediately followed by evidence.

## Reporting

Report outcomes faithfully. If the gate fails, say so with the failing output — a true "3 tests failing, here's why" is a completed verification; a false "all green" is not. Partial completion is reported as partial.
