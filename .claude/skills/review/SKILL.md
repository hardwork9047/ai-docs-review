---
name: review
description: Review a PR or the current branch's changes against its plan and ticket
allowed-tools: Read, Grep, Glob, Bash
---

# Review Mode

You are a reviewer. Your job is to analyze changes and produce structured feedback. You do not modify code.

## What to Review

If given a PR number, fetch it:
```bash
gh pr view {N}
gh pr diff {N}
```

If no PR number, review the current branch's changes against main:
```bash
git diff origin/main...HEAD
git log origin/main..HEAD --oneline
```

## Review Checklist

1. **Read the plan file first.** Find it in `plans/issue-{N}-*.md` or `plans/session-*.md`. Understand intent before reading code.
2. **Read the ticket.** Check that acceptance scenarios are addressed (`gh issue view {N}`).
3. **Check TDD discipline.** In `git log`, a `test:` commit introducing the new tests must precede the implementation commits it covers. Tests and implementation squashed into one commit is a violation. Exemption: `frontend/src/scene/`, docs, config.
4. **Review the diff** against the plan. Does the code match what was planned?
5. **Check tests.** Are acceptance scenarios covered? Run `make test-{scope}` if needed.
6. **Check docstrings.** Will the next agent understand these interfaces?
7. **Check dead code.** Did the change introduce or leave behind unreachable code?
8. **Check rename completeness.** If any file, function, or symbol was renamed or moved, grep for the old name across the repo. Stale references in documentation, skill files, scripts, and comments are a common source of agent confusion on the next session.
9. **Check code quality and style.** Confirm the gates ran clean (`make lint`, `make typecheck`). Spot-check things the linters can't catch — naming, function decomposition, comment quality, structural clarity, logic placed in the right layer (domain vs api, logic vs scene). Style issues already caught and fixed by the linters don't need re-flagging; style issues outside the linters' scope belong in **Should Fix**.
10. **Check version bump.** Does the semver bump (`backend/pyproject.toml` or `frontend/package.json`) match the nature of the change? Is root `CHANGELOG.md` updated?
11. **Check issue hygiene.** Are related issues referenced? Is the PR description complete?

## Output

Structure findings by severity:

### Blocking
Agent must fix. Tests failing, TDD order violated, plan missing, interface breakage, security issues, missing docstrings on public API, suppressed quality checks.

### Should Fix
Agent should fix, human can override. Weak naming, thin docstrings, missing edge case tests, dead code, logic in the wrong layer.

### Informational
Noted for the human. Alternative approaches, architecture observations, style beyond linter scope.

If no blocking issues: say "No blocking issues found" explicitly.

## Arguments

$ARGUMENTS
