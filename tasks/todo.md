# TODO -- blender_connect

## Now
- [ ] Place boy reference photos (front/right) in experiment refs/; gate
      with refsense.preview(); run first engine2.compare() loop
- [ ] Re-baseline eye_span/mouth/jaw ratios at clean ruler z=0.655
- [ ] Perspective projection mode
- [ ] Auto-calibration self-test scene (asserts, not eyeballs)
- [ ] Curve inspector (Bezier control points, curvature sampling)

## Next
- [ ] Ordered cross-section loops (connect edge pairs into polylines)

- [ ] Multi-view composite report (TOP+FRONT+RIGHT in one call)

## Done
- [x] ENGINE v2: refsense digitizer (sub-pixel, alpha/background auto)
- [x] ENGINE v2: canonical registration + 96-row signed error field
- [x] ENGINE v2: per-row floor field (median 0.0156 world, 5.5x v1)
- [x] ENGINE v2: auto-generated ranked distinctions + prescriptions
- [x] ENGINE v2: verify_pass same-field re-measure + registration drift
- [x] ENGINE v2 calibration gate: round-trip masterwork=True, 0.1% mismatch
- [x] Diff renders: senses.grid_diff() -- window-checked, +/- cell render
- [x] Window lock on occupancy_grid (auto-fit misregistration fixed)
- [x] senses.attribute(): post-fuse ownership via stashed-part bbox
- [x] senses.clean_heights()/width_at(): ruler-contamination guard
- [x] senses.perception_floor(): masterwork exit criterion measurable
- [x] Patch MCP addon sendall truncation (issue #21) -- see PATCHES.md
- [x] Diagnose screenshot pipeline (PNG, 786KB budget, iterative downscale)
- [x] v0.1 eye.py: ray-cast ASCII renderer + scanline probe
- [x] Calibration round 1: scanline matched human front-view observation
- [x] v0.2: basis handedness fix (v0.1 rendered 180-deg rotated -- caught by rig)
- [x] v0.2: aspect-true auto-framing, arbitrary view vectors, frame= targeting
- [x] v0.2: edges mode (uppercase silhouettes), shade mode (curvature perception)
- [x] v0.2: 2x2 supersampling option, cross-section slicer
- [x] Calibration round 2: v0.2 FRONT render verified (cone top/apex-up, sphere right, cube peek)

## Curriculum (v0.3) -- DONE
- [x] S1 proportions(): 2D width profiles, ratios, symmetry (part-by-part capable)
- [x] S2 contour_angles(): sub-pixel silhouette tracing, tangent angles, corner census
- [x] S3 turntable(): 18-deg (5%) rotation sweep, form-continuity verification
- [x] S4 render_hardness(): normal-gradient perception of sharp vs soft
- [x] S5 doctrine: every sense takes frame=[parts]; refine region by region

## Skill (v0.4) -- DONE
- [x] Authored blender-connect SKILL.md via skill-creator doctrine (3 refinement passes)
- [x] references/: toolkit-api.md + session-lessons.md (progressive disclosure)
- [x] Pushy trigger description, 6/6 trigger-simulation pass
