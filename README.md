# blenderTools

**Calibrated AI modeling in Blender, over MCP.** An AI agent (Claude) drives a live Blender session — but instead of trusting screenshots, it sees the scene through instruments made of math, verifies every adjustment against measurements, and keeps an honest ledger of what worked, what failed, and why.

> The premise: an agent that can *measure* what it built is more useful than one that can only *describe* what it meant to build.

---

**New agent or new session?** Read [`START-HERE.md`](START-HERE.md) first.

## Why this exists

Blender's official MCP add-on lets an LLM execute Python inside Blender. It also offers screenshots — but over the official add-on's screenshot tool, images are budgeted, downscaled, and arrive too degraded for the agent to read anything but the simplest scene. The human sees a crisp render; the agent sees mush.

So this project gives the agent a different kind of sight. Every "view" is a ray-cast render expressed as **text**: object IDs, silhouette edges, depth ramps, surface shading — characters instead of pixels. Text always survives the wire. On top of that sit measurement senses (proportion, contour angle, rotation continuity, surface hardness, cavity depth, a 30×30 occupancy grid), a part-graph that declares which surfaces must be continuous and where breaks belong, and a ground-truth calibration suite that tests the instruments against shapes with exactly known geometry.

The result is a loop: **compare to reference → calibrate the instrument → adjust the model → verify in the same window.** Repeated until the translation between what is seen and what is measured is in sync.

## What it has done

Everything below was built and measured through this toolkit, with the agent verifying its own work:

| Subject | Result |
|---|---|
| British Shorthair cat (4 reference photos) | Final W/H 0.626 vs 0.63 target; D/H 0.732 vs 0.75; 5 blockout loops + fusion; three math-vetoes documented |
| Cartoon boy head (5 references, ~60 objects) | v1 needed ~10 corrections; v3 (after engine calibration) needed **2** — every discrepancy real, none an instrument lie |
| Mug | Passed every surface sense while being a solid cylinder. A human caught it. Result: `cavity_probe()` and doctrine #7 — *verify function, not just form* |
| Target practice | Random sealed target: located to 0.0000 error by reading its own ASCII render, ranged to 0.0000 depth, full 3D fix error 0.0003 |
| Ground-truth calibration | Torus R/r recovered to 6 decimals; pyramid vertex-on invariant exact; occlusion pass-through verified — **and it caught a real bisection bug** that a photo never could have |

The ledger in `ledger/masterwork_ledger.md` records the failures as carefully as the wins, because the failures are where the instruments improved.

## Architecture

```
blendertools/
  cast.py         the ONE casting policy: per-selection world-space BVH, depth-rebased
                  origins, explicit 'selected' vs 'visible' semantics
  eye.py          text renders: id · edges · depth · shade  (arbitrary views, windows, AA)
  senses.py       proportions · contour_angles · turntable · render_hardness ·
                  silhouette (sub-pixel) · cavity_probe + enclosure_check · occupancy_grid
  measure.py      guarded rulers (frame REQUIRED), edge_bisect with an enforced invariant,
                  parts_at_height / attribute_point for post-fusion diagnosis
  mesh_mind.py    part graph: continuity contracts, connectivity_check, island_census,
                  fuse_group (fuse ONE layer, stash the parts), witness checks
  recipes.py      voxel_fuse ladder · quadriflow (introspects the operator's real params) ·
                  hair_pods (lying mode) · hero_spikes (standing mode)
  plan.py         data-before-code: declarative specs, safe expressions, detail gate,
                  content hash, build() with provenance report, capture() from scene
  gauge.py        output quality as tracked numbers: fit · silhouette IoU · surface ·
                  topology · symmetry → composite, JSONL log, regression detection
  calibration.py  ground-truth suite: torus, pyramid, occlusion, bisect guard — in an
                  isolated scene, valid in any open file
  config.py       every canon value with a provenance note; ~/.blendertools.json overrides
  refs.py         digitized reference data, with confidence and known weak spots
skills/blender-connect/   the working method (SKILL.md + references) — read this first
docs/                     CONNECTION-HANDOFF.md (how to connect), PATCHES.md
ledger/                   masterwork_ledger.md, gauge_log.jsonl
artifacts/                drawing studies exported from the measurements
```

## The doctrine

Fourteen rules, each one paid for by a specific failure. The short version:

1. Adjust → verify in the **same window**. No verification, no adjustment.
2. **Measure, don't remember.** Stale numbers caused the worst overshoot.
3. When a metric floors, change **method**, not effort.
4. Never guess what you can't see; say so, then build an instrument.
5. Enumerate APIs — `dir()` and probe ladders. Tracebacks are the spec.
6. A veto from the math is a win.
7. Verify **function**, not just form (the mug).
8. Think as a mesh, by parts: declare continuity and breaks, prove both.
9. Lapping pass — 20+ checkpoints cycling drawing / depth / dimension, not one shot.
10. Consult the reference **fresh every loop**; derived targets expire.
11. Fusion erases sub-part attribution; diagnose by stashed-part bounding boxes.
12. Regression-check rulers expire too — re-derive measurement heights after edits.
13. `bisect(x_hit, x_miss)` invariant enforced, or it converges in the wrong region silently.
14. When model-vs-reference is ambiguous, test the **instrument** on a ground-truth primitive first.

Full text with the case behind each: `skills/blender-connect/SKILL.md` and `references/session-lessons.md`.

## Quick start

**Requirements:** Blender 5.1+ with the [official Blender MCP add-on](https://www.blender.org/lab/mcp-server/) (not the community `ahujasid/blender-mcp` — different protocol, not interchangeable). See `docs/CONNECTION-HANDOFF.md` for the full connection setup, the screenshot pitfall, and a socket patch for large payloads.

**Install** (one symlink into Blender's auto-import path):
```bash
ln -s ~/Developer/blenderTools/blendertools \
  "$HOME/Library/Application Support/Blender/5.1/scripts/modules/blendertools"
```

**First run**, inside Blender (or via the MCP `execute_blender_code` tool):
```python
import blendertools as bt
bt.doctor()                    # modules loaded, Blender version, overrides
bt.calibration.run_all()       # must pass before trusting any measurement
```

**See the scene:**
```python
print(bt.eye.render_ascii(view="FRONT", width=64, mode="shade"))
bt.senses.proportions("FRONT", frame=["MyObject"])
```

**Score a model against a reference:**
```python
from blendertools import gauge, refs
sc = gauge.scorecard("boy_v3", frame_face=["SkinFused", "EarL", "EarR"],
                     ref_grid_front=gauge.spans_to_grid(refs.BOY_FRONT_SPANS_30))
gauge.gate(sc); gauge.log(sc)   # gate BEFORE log -- a failed candidate must not become a baseline
```

After editing any module: `bt.reload()`.

## Status

**v0.8.0 — working, experimental, honest about its ceiling.** An independent audit of v0.6.0 reproduced twelve defects; all P1 and P2 findings are fixed with regression tests (see `AUDIT-RESPONSE.md`). Models are sphere-blockout plus voxel fusion; the topology gap (quad flow, subdivision-ready meshes) is the current frontier, and `recipes.quadriflow` is the first step. The calibration suite passes 20/20 (5 known-geometry cases, 14 regression tests from the external audit incl. occlusion policy, far-subject and transform/modifier checks, and a scene-integrity assertion with planted decoys). The gauge system exists but has one baseline logged. The tooling grew inside one long collaborative session between a human teaching calibration the way an atelier teaches drawing and an agent building the instruments it was being taught to use — the ledger reads accordingly.

## Credits

Built on the official [Blender MCP](https://projects.blender.org/lab/blender_mcp) by the Blender Foundation. The blockout → remesh → UV-sphere-eyes pipeline was derived independently, then found to match Keelan Jon's character workflow almost step for step. Doctrine and curriculum: Francis Rey. Instruments and their bugs: Claude.

## License

MIT — see `LICENSE`.
