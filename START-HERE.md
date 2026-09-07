# START HERE — agent handoff for blenderTools

You are an AI agent picking up this project. Read in this order; each step
is short and the order matters.

## 0. What this is (60 seconds)
Three layers. You own two of them.
- **Transport**: the official Blender MCP add-on (Blender Foundation). Gives you
  `Blender:execute_blender_code`. Not ours. One local socket patch — see docs/PATCHES.md.
- **Instruments**: `blendertools/`, a Python package that runs INSIDE Blender's
  interpreter. Text-based vision, measurement senses, part-graph, gauges, and a
  ground-truth calibration suite. Already symlinked into Blender's
  `scripts/modules` by `blendertools/install.py` (run it once per Blender; see INSTALL.md); then `import blendertools as bt` works in any session.
- **Generator (attached, not ours)**: an external image-to-3D service (Meshy / Hyper3D Rodin)
  called through `recipes.generate` with full provenance. Its output is measured like any
  other mesh, never trusted. Not installed yet — see STATUS.md.
- **Method**: `skills/blender-connect/SKILL.md`. Doctrine and workflow. Runs in
  YOUR context — it decides how you act on what the instruments tell you.

Screenshots over MCP arrive too degraded to read. Do not use them for
verification. Everything here exists to route around that.

## 1. Connect  →  docs/CONNECTION-HANDOFF.md
Which add-on, how to verify it, the first-command-fails quirk, the screenshot
pitfall, the socket patch. Then prove the link:
```python
import bpy; result = {"v": bpy.app.version_string, "n": len(bpy.data.objects)}
```

## 2. Load and self-test  →  blendertools/INSTALL.md
```python
import blendertools as bt
bt.doctor()                    # all modules True, Blender version, overrides
bt.calibration.run_isolated()  # separate factory-startup Blender; MUST pass before you trust a measurement (run_all() for a throwaway scene, Object Mode only)
```
If calibration fails, the instrument is wrong, not the scene — stop and fix it.
After editing any module: `bt.reload()` (dependency-ordered; never pop sys.modules by hand).

## 3. Learn the method  →  skills/blender-connect/SKILL.md
Read the whole file, then `references/toolkit-api.md` (signatures) and
`references/session-lessons.md` (the failure behind each rule). The 14 doctrine
lines are not style — each one closed a specific, logged bug.

## 4. Know where the work stands  →  STATUS.md, then ledger/masterwork_ledger.md
`STATUS.md` is the checklist (parts, function-level marks, open items in order).
Read the LAST two sections and the "Carried queue". That is the current state
and the open items. Add to it as you work; log failures as carefully as wins.

## 5. Score, don't opine  →  blendertools/gauge.py
Before and after any modeling pass:
```python
from blendertools import gauge, refs
sc = gauge.scorecard("<model_id>", frame_face=[...], ref_grid_front=gauge.spans_to_grid(refs.BOY_FRONT_SPANS_30))
g = gauge.gate(sc); gauge.log(sc); gauge.approve(sc["id"])   # gate -> log (history) -> approve only after review
```
"Better" means gate() reports no regressions against a compatible baseline; the composite is one lens, not the verdict.

## The one loop
reference (fresh, registered) → GENERATE or build the base mesh → measure against the
reference (calibrate the instrument first if it cannot) → correct the MODEL as plan edits →
verify in the same window → gauge → gate against the approved baseline → log. Repeat.

## Repos
- `~/Developer/blenderTools` — live, GitHub `freyjay/blenderTools`. Work here.
- `~/Developer/blender_connect` — archive. Read-only history. Don't edit.
- `~/Developer/blender-connect-experiment` — scratch .blend files (cat, boy v1-v3,
  mug, target range, depth calibration). Not a git repo you can commit to.

## Files you may see and can ignore
`CLAUDE.md`, `WORKFLOW.md`, `config/`, `tasks/` — the project-template layer
(blueprint workflow). `tasks/todo.md` is the roadmap; `config/stack.md` the stack.
