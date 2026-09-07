# blenderTools

**Calibrated, verified 3D modeling in Blender, over MCP.** An AI agent (Claude) drives a live Blender session and treats every mesh the same way — whether built from primitives or produced by an external generator: measured against the reference with instruments made of math, corrected, gated against an approved baseline, and logged in an honest ledger of what worked, what failed, and why.

> The premise: an agent that can *measure* what it built is more useful than one that can only *describe* what it meant to build.

---

**New agent or new session?** Read [`START-HERE.md`](START-HERE.md) first.

**Where things stand:** [`STATUS.md`](STATUS.md) is the working checklist; [`docs/structure.html`](docs/structure.html) is the same map drawn for visitors (open it in a browser).

## Why this exists

Blender's official MCP add-on lets an LLM execute Python inside Blender. It also offers screenshots — but over the official add-on's screenshot tool, images are budgeted, downscaled, and arrive too degraded for the agent to read anything but the simplest scene. The human sees a crisp render; the agent sees mush.

So this project gives the agent a different kind of sight. Every "view" is a ray-cast render expressed as **text**: object IDs, silhouette edges, depth ramps, surface shading — characters instead of pixels. Text always survives the wire. On top of that sit measurement senses (proportion, contour angle, rotation continuity, surface hardness, cavity depth, a 30×30 occupancy grid), a part-graph that declares which surfaces must be continuous and where breaks belong, and a ground-truth calibration suite that tests the instruments against shapes with exactly known geometry.

The result is a loop: **compare to reference → calibrate the instrument → adjust the model → verify in the same window.** Repeated until the translation between what is seen and what is measured is in sync.

## Direction (recalibrated 2026-09-07)

The 2026 consensus is blunt and, on our evidence, correct: an MCP-driven Blender is an excellent *operator* and a poor *modeller*; organic likeness is a generation problem, not a scripting problem. Our sphere blockouts confirmed it — scored on one ruler, v1 0.615 → v2 0.843 → v3 0.740, a regression nothing caught. So this project stops competing on generation and does the thing the generation ecosystem lacks: **measurement, correction and proof.** Base meshes come from an attached multi-view generator (Meshy or Hyper3D Rodin, called through `recipes.generate` with full provenance); blendertools measures them against the same references at fixed registration, records corrections as plan edits, quad-remeshes, gates every version against an approved baseline, and keeps the ledger. A generated mesh enters the loop like any other build: measured, never trusted.

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

**Library prerequisite:** any Blender 5.1+ (5.1.2 and 5.2.1 verified); it imports and runs standalone/headless with no MCP. **This project's selected transport** for driving Blender live is the [official Blender MCP add-on](https://www.blender.org/lab/mcp-server/) (not the community `ahujasid/blender-mcp` — different protocol, not interchangeable); see `docs/CONNECTION-HANDOFF.md`.

**Install** (destination-aware; discovers this Blender's modules dir, never replaces a real directory):
```bash
/path/to/Blender --background --python blendertools/install.py -- --source /path/to/blenderTools
```
See `INSTALL.md` for verification in a disposable process and uninstall.

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
g = gauge.gate(sc)   # vs the last APPROVED compatible baseline; 'unverified' if none
gauge.log(sc)        # history only -- logging never promotes
gauge.approve(sc["id"])   # after human review; only approved scorecards become baselines
```

After editing any module: `bt.reload()`.

## Status

**v0.9.0 — working, experimental, honest about its ceiling.** An independent audit of v0.6.0 reproduced twelve defects; the original reproductions from both audits are fixed with regression tests (`AUDIT-RESPONSE.md`; follow-up findings are tracked in the ledger). The full safety contract — live MCP round-trip, fresh install, Metal render, parented/animated transforms, vessel containment — is **not** yet verified and is listed as such in every report. Models so far are sphere-blockout plus voxel fusion, built before the instruments existed; see *Direction* above for what replaces them as the base-mesh source. The calibration suite passes 29/29: 5 known-geometry cases, 23 regression tests from two external audits, and a scene-integrity assertion (objects, selection, active object, mesh and collection counts, planted decoys). The gauge has three logged scorecards (v1/v2/v3 on one ruler) and — deliberately — no approved baseline yet: the first baseline will be the loop's own first output from a written brief. The tooling grew inside one long collaborative session between a human teaching calibration the way an atelier teaches drawing and an agent building the instruments it was being taught to use — the ledger reads accordingly.

## Credits

Built on the official [Blender MCP](https://projects.blender.org/lab/blender_mcp) by the Blender Foundation. The blockout → remesh → UV-sphere-eyes pipeline was derived independently, then found to match Keelan Jon's character workflow almost step for step. Doctrine and curriculum: Francis Rey. Instruments and their bugs: Claude.

## License

MIT — see `LICENSE`.
