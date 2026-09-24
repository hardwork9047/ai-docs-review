---
name: e2e
description: End-to-end testing of the running app (backend API + frontend in a real browser) using Playwright. Use to verify a feature works through the full stack, to reproduce a UI bug, or to capture screenshots of the frontend (including Three.js rendering).
allowed-tools: Read, Write, Bash, Glob, Grep
---

# E2E Testing

Adapted from anthropics/skills `webapp-testing` for this template's stack (FastAPI + Vite/Three.js).

Unit tests (pytest/vitest) stay the TDD backbone — E2E is for the seams unit tests can't reach: HTTP wiring, CORS, the frontend actually talking to the backend, and pixels actually rendering. Keep E2E scripts few and high-value.

## Setup (once per environment)

```bash
uvx playwright install chromium --with-deps
```

## Running servers + a test script together

Use the bundled helper — it starts the servers, waits for their ports, runs your command, and cleans up even on failure. Check usage with `--help` first:

```bash
python3 .claude/skills/e2e/scripts/with_server.py --help
```

Typical invocations:

```bash
# Frontend only (static/UI checks)
python3 .claude/skills/e2e/scripts/with_server.py \
  --server "cd frontend && pnpm dev" --port 5173 \
  -- uv run --project backend --with playwright python my_e2e_check.py

# Full stack
python3 .claude/skills/e2e/scripts/with_server.py \
  --server "cd backend && uv run uvicorn app.main:app --port 8000" --port 8000 \
  --server "cd frontend && pnpm dev" --port 5173 \
  -- uv run --project backend --with playwright python my_e2e_check.py
```

Write throwaway scripts to the scratchpad directory; only commit an E2E script if it earns a permanent place (then put it in `e2e/` at the repo root and add a `make e2e` target).

## Playwright script pattern

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("http://localhost:5173")
    page.wait_for_load_state("networkidle")  # let JS/Three.js boot
    page.screenshot(path="screenshot.png")
    # ... assertions: page.locator(...), page.get_by_role(...), API via page.request
    browser.close()
```

Rules of thumb:
- `wait_for_load_state("networkidle")` before inspecting dynamic content; prefer condition-based waits over `sleep`.
- Prefer semantic selectors: `get_by_role`, `get_by_text`, IDs. Avoid brittle CSS chains.
- Always close the browser, even on failure (use try/finally or a `with` block).
- Backend-only checks don't need a browser: `page.request` or plain `httpx` against `:8000` is faster.

## Three.js / WebGL specifics

- Headless Chromium renders WebGL via SwiftShader — screenshots work, but performance is not representative. Never assert on frame rate headlessly.
- To verify "the scene renders at all": screenshot after `networkidle` plus a short `page.wait_for_timeout(500)` for the first frames, then check the canvas isn't blank (read pixels via `page.evaluate` on the canvas, or eyeball the screenshot with the Read tool).
- Testable *logic* (positions, angles, state) belongs in `frontend/src/logic/` with vitest — don't use E2E to test math.

## When a check fails

Read the browser console first: `page.on("console", lambda msg: print(msg.text))` registered before `goto`. Then apply `/debug` — an E2E failure is a reproduction, not a diagnosis.
