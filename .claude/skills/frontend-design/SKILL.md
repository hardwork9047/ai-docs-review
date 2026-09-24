---
name: frontend-design
description: Design guidance for building distinctive, intentional frontend UI — use when creating or restyling pages, components, overlays, or HUD elements in frontend/, to avoid generic "AI slop" aesthetics.
---

# Frontend Design

Adapted from anthropics/skills `frontend-design` for this template.

Approach every UI task as a designer with a point of view, not a template-filler. The goal is an interface someone could recognize as *this product's*, not "a nicely formatted page".

## Ground choices in the subject

Before writing any markup or CSS, answer:
1. What is this screen concretely about? (this app: often a 3D scene plus controls/HUD around it)
2. Who uses it, in what context?
3. What is the one primary action or piece of information?

Derive the visual direction from those answers — the domain's materials, instruments, and vocabulary — not from a generic dashboard memory.

## Principles

- **Typography carries personality.** Choose a deliberate display/body pairing and a clear type scale per project. Default system-font-at-default-weights everywhere reads as unfinished.
- **Structure must mean something.** Numbered markers (01/02/03), hairline dividers, and label chips are justified only when the content genuinely has sequence, separation, or categories.
- **Motion with intent.** One considered page-load sequence or micro-interaction beats scattered hover effects. In this template, animation logic that has testable state (timing curves, interpolation) belongs in `frontend/src/logic/` with vitest tests; the scene/DOM only consumes it.
- **Avoid the known AI-default palettes:** warm cream + terracotta; near-black + acid green; broadsheet-with-hairlines. If your first idea matches one of these, that's the signal to look at the subject again.
- **Copy is design material.** Active voice, plain words, consistent naming — a button labeled "Publish" produces a toast that says "Published", not "Your changes have been saved successfully".

## Process: two passes

1. **Brainstorm tokens first:** 4–6 colors, two typeface roles, a layout concept, and one signature element (the thing a user would remember). Write them as CSS custom properties before building.
2. **Critique before building:** would this design also fit any other brief? If yes, sharpen it.
3. **Build precisely**, keeping specificity low and tokens authoritative.
4. **Refine with evidence:** screenshot the running app (use `/e2e` to capture it), self-critique, and delete decoration that serves nothing.

## Template constraints that still apply

- Rendering/DOM code is exempt from unit tests, but any computation you add for the design (layout math, color interpolation, formatting) goes in `frontend/src/logic/` — TDD as usual.
- `make check` (tsc, vitest) must stay green; design work doesn't relax the gates.
