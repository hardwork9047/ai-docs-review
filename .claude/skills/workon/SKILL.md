---
name: workon
description: Bootstrap an interactive development session for a scope (backend|frontend)
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Interactive Work Mode

You are entering an interactive development session. The developer will work alongside you,
making decisions in real-time. Your job is to set up the environment and establish context,
then assist as directed.

## Setup

Identify your target from the arguments:
- **Scope:** `backend` or `frontend`?

If no scope is specified, ask the user.

## Workflow

### 0. Resume Check

Before doing anything else, check whether a prior session left a workflow state:

```bash
cat plans/workflow_state.md 2>/dev/null
git branch --show-current
git log --oneline -10
```

If the file exists, **validate it before surfacing it**:

1. **Branch match** — does the current branch look like the one the state file was written on? If the branch name clearly belongs to a different task (e.g., you're on `feature/issue-12-*` but the state says `skill: workon` with no issue), flag it.
2. **Recency** — do the recent commits look like they belong to the same work session the state file describes? If git log shows a merge to main, a completely different topic, or commits well past what the state describes, the file is stale.
3. **Already shipped** — if git log shows a "remove workflow state" or "PR filed" commit, the state file is a leftover that wasn't cleaned up. Delete it and proceed fresh.

If the file looks valid, tell the developer what was in progress and ask:
> "I found a workflow state from a prior session: [step / next]. Continue from there, or start fresh?"

If clearly stale, tell the developer what you found and why you're ignoring it, then proceed fresh.

### 1. Sync
```bash
git fetch origin && git rebase origin/main
```

### 2. Set Up Environment

```bash
make setup
```

Verify by running tests for the target scope:
```bash
make test-{scope}
```

Ensure existing tests pass before making changes.

### 3. Establish Context

Read the scope's structure and recent history:
- root `CHANGELOG.md` — what changed recently
- `backend/pyproject.toml` or `frontend/package.json` — current version, dependencies
- Scan the scope's `src/` and `tests/` for conventions (test patterns, module structure)
- Root `CLAUDE.md` — the rules in force (TDD, layers, quality gates)

Tell the developer:
- What scope you're working in
- Whether tests are passing
- Current version
- A brief summary of recent changes from the changelog

### 4. Branch

If not already on a feature branch, create one. Use the appropriate prefix:
- `feature/` — new functionality, enhancements
- `bugfix/` — fixing broken behaviour

```bash
git checkout -b feature/{descriptive-slug}   # or bugfix/{descriptive-slug}
```

The slug is descriptive, not issue-linked. If the developer mentions an issue number,
use `feature/issue-{N}-slug` or `bugfix/issue-{N}-slug` instead.

After branching, write a workflow state file so future sessions can resume:

```bash
mkdir -p plans
cat > plans/workflow_state.md << 'EOF'
skill: workon
scope: {scope}
step: interactive (in progress)
next: continue interactive session; run /ship when ready to file PR
EOF
```

Do not commit this file yet — it will be committed (or cleaned up) when `/ship` runs.

## Operating Rules During Interactive Work

- You are **scope-bound** per CLAUDE.md rules. Read the other scope freely, don't modify it without permission.
- **TDD still applies** even in interactive mode: failing test first (`test:` commit), then implementation. The render layer (`frontend/src/scene/`) is the only exemption.
- **No plan file is required yet.** A retroactive plan will be generated when the developer runs `/ship`.
- Follow all quality gates: run tests iteratively, maintain docstrings, keep code clean.
- When making architectural decisions or crossing scope boundaries, note them — they'll become PR annotations at ship time.
- When the developer is ready to finalize, they run `/ship` (optionally with an issue number).

## Arguments

$ARGUMENTS
