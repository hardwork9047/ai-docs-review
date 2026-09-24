---
name: implement
description: Start an implementation task for a specific scope (backend|frontend) and GitHub issue
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent
---

# Implementation Mode

You are an implementing agent. Your job is to pick up a GitHub issue and deliver a clean PR, test-first.

## Setup

Identify your target from the arguments:
- **Scope:** `backend` or `frontend`?
- **Issue:** what GitHub issue number?

If either is missing, ask the user before proceeding.

### Resume Check

Before asking the plan-review question, check whether a prior session left a workflow state:

```bash
cat plans/workflow_state.md 2>/dev/null
git branch --show-current
git log --oneline -10
```

If the file exists and `issue:` matches your target issue, **validate it before trusting it**:

1. **Branch check** — does the current branch name match `feature/issue-{N}-*` or `bugfix/issue-{N}-*`? If you're on a branch for a *different* issue, the state file is stale — ask the user before proceeding.
2. **Step plausibility** — does the recorded `step:` make sense given recent commit messages? If the state says `step: 5 (write failing tests)` but git log shows commits that look like cleanup or review work, the file is behind reality — tell the user what you see and ask how to proceed.
3. **Scope match** — does the `scope:` field match where you're working? A state file for a different scope is always stale.

If any check fails, surface what you found:
> "I found a workflow_state.md for issue #{N} at step X, but [what's inconsistent]. Should I resume from that step, or start fresh?"

If all checks pass, **resume from the recorded step** — do not restart from step 1. Honor the recorded `plan-review-preference` and do not ask the question again.

### Plan Review Preference (skip if resuming)

**Ask this BEFORE starting any work.** The user may step away during the long tail of this skill, so you must set expectations upfront. Ask:

> "Before I start: when I finish writing the plan (step 4), do you want to review it before I commit and start coding, or should I proceed autonomously?"

Remember the answer and honour it when you reach step 4:
- **review**: pause at step 4, show where the plan file is, wait for their feedback, apply any edits they request, then commit.
- **proceed**: commit the plan at step 4 and keep going without prompting.

Do not ask this question later — the point is to lock it in before the user walks away.

### Workflow State Format

At each step transition, write `plans/workflow_state.md` and include it in the step's commit. This file survives context compaction and lets a resumed agent pick up exactly where the previous one stopped.

```
skill: implement
scope: {backend|frontend}
issue: {N}
plan-review-preference: {proceed|review}
step: {N} ({step name})
next: {one sentence — what to do first on resume}
```

Delete this file in the same commit as the PR is filed (step 9).

## Workflow

Follow this sequence exactly:

### 0. Write Initial State

Before doing anything else, write the workflow state so a resumed agent knows where you are:

```bash
mkdir -p plans
cat > plans/workflow_state.md << 'EOF'
skill: implement
scope: {scope}
issue: {N}
plan-review-preference: (pending — not yet asked)
step: 1 (sync and branch)
next: sync, branch, set up environment, read the issue
EOF
```

Update this file at every subsequent step transition.

### 1. Sync and Branch
```bash
git fetch origin && git rebase origin/main
git checkout -b {prefix}/issue-{N}-short-slug
```
Create a new branch from the latest main. Name it after the issue.

**Branch prefix:** read the issue first (step 3), then choose:
- `feature/` — new functionality, enhancements
- `bugfix/` — fixing broken behaviour

### 2. Set Up Environment

```bash
make setup
```

Verify by running the existing tests for your scope:

```bash
make test-{scope}
```

Ensure existing tests pass **before** making any changes.

### 3. Understand the Issue
```bash
gh issue view {N}
gh issue list --limit 30 --json number,title   # scan for related issues
```
Read it thoroughly. Note any acceptance scenarios.

### 4. Plan
Create `plans/issue-{N}-short-slug.md` with:
- Verbatim goal from the issue
- Your chosen approach and decomposition
- Alternatives you considered and rejected
- What's explicitly out of scope
- Assumptions about the other scope (with docstring references)
- How you'll test each acceptance scenario

**Honour the plan-review preference captured in Setup.**
- If the user asked to review: tell them the plan is ready and the file path, and wait. Apply any revisions they request to the file, then commit.
- If the user said proceed: commit the plan and continue.

**Commit the plan before writing any code.** Include a `workflow_state.md` update in the plan commit:

```
step: 5 (write failing tests)
next: translate acceptance scenarios into failing tests, run them, confirm they fail, then commit
```

### 5. Write Failing Tests First (Red)

Translate acceptance scenarios from the issue into tests. Then **run them and confirm they fail — for the right reason**:

```bash
# backend
cd backend && uv run pytest tests/unit/test_{new}.py tests/integration/test_{new}.py
# frontend
cd frontend && pnpm vitest run tests/{new}.test.ts
```

- Each test must fail because the behaviour is **not implemented yet** — not because of an import error, typo, or broken fixture. Fix those before committing.
- If a test passes before you've written any implementation, it isn't testing the new behaviour — rewrite it.

Commit with a `test:` prefix. **Do not mix implementation code into this commit** — the reviewer verifies test-first ordering from git log. Include a `workflow_state.md` update in the same commit:

```
step: 6 (implement)
next: write code until tests pass; run fast quality checks iteratively
```

Exception: changes limited to `frontend/src/scene/` (render layer) are exempt from test-first. If the issue requires scene work with embedded logic, extract the logic to `frontend/src/logic/` and TDD that.

### 6. Implement (Green)

Write the minimum code to make the tests pass. During the inner loop:

```bash
# backend: your new tests + fast lint
cd backend && uv run pytest tests/unit/test_{new}.py
cd backend && uv run ruff check src tests
# frontend
cd frontend && pnpm vitest run tests/{new}.test.ts
cd frontend && pnpm typecheck
```

**Never suppress quality check failures.** No new exclude entries, skip markers, `# type: ignore`, or coverage-threshold changes to make checks pass. If a check fails for a pre-existing reason genuinely outside your scope, escalate to the human rather than masking the failure.

When your tests pass, run the full gate before moving on:

```bash
make check
```

Refactor while green if needed (`refactor:` commits). Then update `workflow_state.md` and commit before moving to step 7:

```
step: 7 (clean up)
next: check dead code, bump version, update CHANGELOG.md
```

### 7. Clean Up
- Check for dead code in files you touched — clean it up
- Bump the version (semver): `backend/pyproject.toml` or `frontend/package.json` depending on scope
- Update root `CHANGELOG.md`: `v{version}: {summary}, see PR #{N}`

Include a `workflow_state.md` update in the cleanup commit:

```
step: 8 (self-review)
next: run code-reviewer agent, fix blocking items, run doc-parrot, write findings file
```

### 8. Self-Review (MANDATORY — DO NOT SKIP)

**You must run the code-reviewer agent before pushing. This step is not optional.** If you push without running the reviewer, the PR will be rejected.

Call the code-reviewer agent now:
```
Use the code-reviewer agent to review my changes
```

Wait for its findings. Fix all **Blocking** items before proceeding. **Should Fix** items should also be addressed unless there's a good reason not to.

**Do not proceed to step 8b until the reviewer has run and all blocking items are resolved.**

### 8b. Doc-Parrot (MANDATORY for backend changes)

After the code-reviewer, run the doc-parrot skill to validate docstring–implementation alignment for every changed Python callable in the diff:

```
/doc-parrot
```

The parrot identifies every changed callable, extracts docstring prose, and asks you to derive a description and usage example from prose alone — then compare that against the implementation. For each callable, record a judgment: **Fix docstring**, **Fix code**, or **OK**. Act on any **Fix** judgments before proceeding.

The parrot is not a gate. It produces an artifact you act on with judgment. (Frontend-only changes: skip this step and note "doc-parrot: n/a (no Python changes)" in the findings file.)

### 8c. Write (or update) findings file

After both the code-reviewer and the doc-parrot have run, append a round section to
`plans/issue-{N}-slug-findings.md`. If the file doesn't exist yet, create it
with the file header first. Each review iteration adds a new round — do not overwrite
previous rounds.

```markdown
# Findings: issue-{N}-{slug}

## Round 1

### Code Reviewer
- Blocking: N
- Should Fix: N
- Informational: N
- Key Issues: {bullet list or "none"}
- Judgment: {one-line assessment — did the reviewer catch something real?}

### Doc Parrot
- Divergences Found: N
- Details: {bullet list of callable + what diverged, or "none"}
- Judgment: {one-line assessment — did the parrot catch something real?}
```

If you fix blocking items and re-run steps 8 and 8b, append `## Round 2` (and so on)
with the same structure. Commit after each round. Do not push until the latest round
shows `Blocking: 0`.

Include a `workflow_state.md` update in the findings commit:

```
step: 9 (push and PR)
next: run make check, push, create PR, delete workflow_state.md
```

### 9. Push and PR

```bash
make check
git rm plans/workflow_state.md
git commit -m "chore: remove workflow state (PR filed)"
git push -u origin HEAD
```

Create the PR and capture the PR number and commit SHA:
```bash
PR_URL=$(gh pr create --title "{concise title}" --body "Closes #{N}

{summary}

Plan: plans/issue-{N}-slug.md" --base main)
PR_NUMBER=$(echo "$PR_URL" | grep -oP '\d+$')
COMMIT_SHA=$(git rev-parse HEAD)
```
Reference all related issues in the PR body.

### 10. Post PR Annotations

Using the `annotation-data` JSON block from the code-reviewer's output (step 8 Self-Review), post targeted annotations to help the human reviewer.

**Guided tour comment** — post a summary comment on the PR:
```bash
gh pr comment $PR_NUMBER --body "## Guided Review Tour
### Scope Violations
{list from annotation-data, or 'None'}

### Architectural Decisions (worth a second opinion)
{list with file:line and descriptions}

### Areas of Uncertainty
{list with file:line and descriptions}

### Mechanical Changes (safe to skim)
{list of mechanical files}

---
_Generated by the implementing agent's self-review._"
```

**Line-specific annotations** — for each item in the annotation data:
```bash
# Scope violations:
gh api "repos/{owner}/{repo}/pulls/$PR_NUMBER/comments" \
  -f body="⚠️ **SCOPE VIOLATION**: {reason}" \
  -f commit_id="$COMMIT_SHA" -f path="{path}" -F line={line} -f side=RIGHT

# Architectural decisions:
gh api "repos/{owner}/{repo}/pulls/$PR_NUMBER/comments" \
  -f body="🏗️ **ARCHITECTURAL DECISION**: {description}" \
  -f commit_id="$COMMIT_SHA" -f path="{path}" -F line={line} -f side=RIGHT

# Uncertainties:
gh api "repos/{owner}/{repo}/pulls/$PR_NUMBER/comments" \
  -f body="❓ **UNCERTAINTY**: {description}" \
  -f commit_id="$COMMIT_SHA" -f path="{path}" -F line={line} -f side=RIGHT
```

**Rules:**
- The literal `{owner}/{repo}` placeholders are expanded by `gh api` automatically — leave them as-is.
- If the annotation-data has no items to flag, post a simplified tour: "All changes are routine. No items flagged for special attention."
- If a line comment fails (line not in diff hunk), skip it — don't let annotation failures block the PR.
- Limit to 15 line-specific comments maximum.

### 11. Issue Hygiene
```bash
gh issue comment {N} --body "Addressed in PR #${PR_NUMBER}. {brief summary}"
```
Comment on related issues the same way.

## Arguments

$ARGUMENTS
