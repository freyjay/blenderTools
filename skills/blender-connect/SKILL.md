---
name: blender-connect
description: Calibrated 3D modeling, verification, and math-to-drawing through Blender MCP with a text-based vision system (eye.py/senses.py). Make sure to use this skill whenever the user mentions Blender, modeling or sculpting anything in 3D via MCP, verifying or measuring geometry, rendering scenes as ASCII/text, silhouette or proportion analysis, calibrating against reference images, iterative refine loops on a model, or exporting geometry as a drawing (gesture/construction/contour) to any canvas -- even if they never say the word "skill" or "eye". Also applies when Blender screenshots are unreliable and a text-based verification path is needed.
compatibility: Requires the Blender MCP connector with the official addon running (localhost:9876) and the toolkit repo at ~/Developer/blenderTools (eye.py, senses.py).
---

> **LOAD PATTERN (v0.5.0, supersedes any `sys.path` / `sys.modules.pop` / `import eye, senses` text below):**
> ```python
> import blendertools as bt
> bt.doctor(); bt.calibration.run_all()      # must pass first
> bt.eye.render_ascii(...); bt.senses.proportions(...); bt.mesh_mind.fuse_group(...)
> bt.reload()                                # after editing any module
> ```
> The package is symlinked into Blender's `scripts/modules`; no path hacks. See `START-HERE.md`.


# blender-connect: Calibrated Modeling

**First action on trigger:** read references/toolkit-api.md, then save the .blend before any operation.

Screenshots over MCP are lossy; math rendered as text always arrives. This
skill fuses the classical atelier curriculum, a math-native vision toolkit,
and a calibration doctrine proven across many verification loops into one
modeling method. Read references/toolkit-api.md before first tool use;
read references/session-lessons.md when a loop stalls or a metric floors.

## The Interconnection Map

| Atelier stage | Math instrument | Doctrine | Blender practice |
|---|---|---|---|
| 1. Proportion (see 2D) | senses.proportions() | Measure, don't remember | Reference images non-negotiable |
| 2. Line and angle | senses.contour_angles() | Flowing ~11 deg/step vs featured ~16 | Start from nearest primitive |
| 3. Rotation | senses.turntable() 18-deg sweeps | continuity_ok through all angles | Form must survive every view |
| 4. Value: sharp vs soft | render_hardness() + shade | Hardness is anatomical or accidental | Soften seams, keep features |
| 5. Parts before whole | frame=[names] everywhere | Part-by-part reveals what averages hide | Stash parts, re-fuse skin |
| 6. Drawing output | silhouette() -> 3 layers | Math becomes drawing | Export point sets to any canvas |

## Calibration Doctrine

1. Adjust -> verify in the SAME window (view, center, extent). No verification, no adjustment.
2. Measure, don't remember -- stale numbers cause overshoots.
3. When a metric floors, change METHOD, not effort (e.g. primitives -> voxel-fuse).
4. Never guess what you cannot see; say so, then build an instrument.
5. Enumerate APIs (dir(), probe ladders); never guess signatures.
6. A veto from the math is a win.
7. Verify FUNCTION, not just form. Surface senses do not see cavities or interiors;
   vessels need senses.cavity_probe(). Depth cliffs within one object are invisible
   to edges mode -- use depth mode for interiors.
8. Think as a MESH, by PARTS: declare a part graph (mesh_mind.declare_graph)
   stating which surfaces are CONTINUOUS (one manifold) and where BREAKS
   belong. Prove connectivity BEFORE fusing (connectivity_check), prove
   continuity AFTER (island_census: islands=1, non-manifold=0), prove breaks
   by ray ownership. Route every adjustment through the graph: edit the part,
   re-fuse ONLY its group, witness-check that sibling layers are untouched.
   This keeps what is seen, made, created, and adjusted in one shared model.

## Standard Workflow

1. Save the .blend. Fresh-import eye+senses (purge sys.modules first).
2. Blockout with primitives at reference-derived ratios; verify ratios immediately.
3. Look (render_ascii shade + edges); critique like a sculptor before touching anything.
4. Loop: score -> adjust parts -> re-score same window. Iterate until synced.
5. Fuse ladder: duplicate parts -> join -> voxel remesh 0.06 -> 0.05; keep part stash hidden.
6. Detail passes part-by-part; wanted hardness = definition.
7. Close: proportions vs targets, turntable continuity, human audit.

When anything here is insufficient: references/toolkit-api.md has full
signatures, examples, and pitfalls; references/session-lessons.md has the
case studies behind every doctrine line.

9. Lapping pass: for precision work, don't one-shot a fix. Cycle drawing,
   depth, and dimension senses across many small checkpoints (20+), each a
   real measure-vs-reference-and-decide, not a batch of assumed numbers.
   Passing metrics still get looked at; a passing dimension can hide a
   failing depth metric at the same spot, and vice versa.

10. Consult the reference FRESH every loop; derived targets expire.
    Comparing model measurements to cached constants is measuring the
    photocopy. Each loop must include one direct model-output-vs-reference
    juxtaposition with new eyes -- the cache never contains the distinction
    you haven't noticed yet (ear protrusion went unmeasured for 60+ checks).

11. Fusion erases sub-part attribution. After mesh_mind.fuse_group, ray-cast
    only returns the fused name, never which original sphere is responsible.
    Diagnose post-fuse zones via bounding-box containment on the STASHED
    (hidden) parts, not by guessing from z-height. A z-height guess produced
    a real regression here before the correct part was found.
12. Regression-check denominators expire too. A width measured at a fixed
    height can silently start including a part that grew into that height
    band later (ears widened -> contaminated the face-width ruler used by
    three other ratios). Re-derive measurement heights after any edit that
    changes a part's z-extent, don't just re-run the old formula.

13. bisect(x_in, x_out) invariant: x_in MUST be the hit/true side, x_out the
    miss/false side, in every call, or the algorithm silently converges inside
    the wrong region instead of the boundary -- no error is raised. Ground-truth
    primitives (exact known R/r/H) are how this class of bug gets caught for
    certain; verify any new ad-hoc bisection against a known-geometry testbed
    before trusting it on organic/approximate work.
14. When ambiguous whether model or reference is wrong, build a ground-truth
    primitive (known R, r, H, angle) and test the INSTRUMENT there first.
