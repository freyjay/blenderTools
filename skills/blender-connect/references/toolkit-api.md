# Toolkit API

> **LOAD PATTERN (v0.5.0, supersedes any `sys.path` / `sys.modules.pop` / `import eye, senses` text below):**
> ```python
> import blendertools as bt
> bt.doctor(); bt.calibration.run_all()      # must pass first
> bt.eye.render_ascii(...); bt.senses.proportions(...); bt.mesh_mind.fuse_group(...)
> bt.reload()                                # after editing any module
> ```
> The package is symlinked into Blender's `scripts/modules`; no path hacks. See `START-HERE.md`.

# Toolkit API -- eye.py / senses.py

Load pattern (Blender Python, avoids stale-module bugs):

    import sys, os
    p = os.path.expanduser("~/Developer/blenderTools")
    for m in ("eye", "senses"): sys.modules.pop(m, None)
    sys.path.insert(0, p)
    import eye, senses

## eye.py
- render_ascii(view="FRONT", width=72, height=None, mode="id", frame=None,
  aspect=0.5, aa=False, center=None, extent=None) -> str
  - view: FRONT/BACK/RIGHT/LEFT/TOP/BOTTOM or (x,y,z) direction vector
  - mode: id (letter per object + legend) | edges (UPPER=silhouette, lower=fill)
          | depth (near=dense) | shade (normal-facing ramp -- reveals curvature)
  - camera moves: center=(u,v) pans, extent=(eu,ev) zooms, frame=[names] isolates
- scanline(view, axis_value, lo, hi, step) -> [(pos, obj_name|None, depth)]

## senses.py
- proportions(view, frame, rows) -> H, W, W_over_H, widest_at_height_frac,
  symmetry_error, width_profile_top_to_bottom (10 samples)
- contour_angles(view, frame, rows, corner_deg=25) -> per edge:
  mean_turn_deg, max_turn_deg, corners_over_25deg
- turntable(step_deg=18, frame, rows) -> per-angle W/H table,
  max_W_jump_between_steps, continuity_ok
- render_hardness(view, frame, width) -> str; ramp by neighbor-normal angle,
  60deg=full, boundary forced hard
- silhouette(view, frame, rows) -> sub-pixel left/right edge arrays per row
  (bisection-refined; basis of proportions, contour_angles, drawing export)

## Inline hardness_score (calibration probe -- copy into build code)
Cast an n x n grid in a window; mean/max neighbor-normal angle + count > 25 deg.
Compare BEFORE and AFTER in the same window. See session-lessons for usage.

## Pitfalls
- sys.modules caching serves stale code after edits -- always purge before import.
- Voxel remesh erodes thin tips (ears); silhouette-check after every fuse.
- Part bounding-box ratios and fused silhouette ratios disagree; trust silhouette.
- First MCP command after a fresh connection sometimes fails; retry once.
- ray_cast respects visibility: hide the part stash so senses see only the skin.
- Characters are ~2x tall: width ~= 2x height for square world aspect.

## Drawing export (math -> drawing)
1. s = senses.silhouette("RIGHT", rows=72); downsample edges to ~36 pts each.
2. Gesture = every 4th contour point + authored curves (e.g. tail).
3. Construction = part spheres projected to view plane as (center, radius).
4. Contour = full edge chains.
5. Map world units -> canvas units; flip vertical axis when canvas y grows down.
Platform notes: SketchUp MCP edges go through GeometryInput.add_vertex ->
add_edge(i, j) (vertex INDICES) -> group.get_entities().fill(); color after fill
via edge.set_color(SUColor). Sandbox is an allowlist: no imports, no any().

- cavity_probe(center, rim_radius, rim_z, n, frame) -> holds_liquid,
  max/mean_depth, volume_units3. Use for any vessel/container BEFORE declaring done.

## mesh_mind.py (topology awareness)
- declare_graph() -> layer dict {continuity: fuse|separate, members}
- connectivity_check(members) -> components (must be 1 before fusing)
- island_census(obj) -> {islands, non_manifold_edges, verts} (1 / 0 for clean skin)
- fuse_group(graph, layer, voxel) -> fuses ONE group, stashes members hidden
- Adjustment protocol: edit part -> fuse_group(its layer) -> island_census
  + witness transform-hashes on sibling layers.

## Target acquisition (integrated perception recipe)
SEE: render_ascii(id) over a FIXED window -> parse non-space cells ->
character centroid = coarse aim. ACT: single ray at aim; part ownership
(mesh_mind graph) = ring score. REFINE: edge bisection L/R/T/B -> sub-pixel
center + radius. RANGE: ray hit-distances on center + annulus -> depth,
+half-thickness for plane center; (u,v)+depth = full 3D fix. DRAW: range
card from the perception's own numbers (rings, crosshair, shot marks,
error vectors, depth scale bar) -- the drawing is the loop's diagnostic
memory. Perception uses ONLY renders and rays; object coordinates are
referee-sealed for error scoring.


## Engine v2 -- refsense.py / engine2.py (direct reference->product translation)

Load pattern (add to the standard purge list): pop "refsense", "engine2" too.

### refsense.py (the reference side)
- digitize(source, threshold=0.5, flip_x=False) -> sub-pixel silhouette dict
  (pixel units) from an image path or bpy image. Alpha wins; else border-
  sampled background. FRONT-photo convention matches model FRONT (+u = screen
  right = subject's left).
- preview(dig) -> ASCII of what the digitizer saw. GATE: verify this looks
  like the subject BEFORE trusting any comparison.
- rasterize(sil, px) -> synthetic grayscale from known geometry (calibration).

### engine2.py (the pipeline)
- compare(ref_dig, view, frame, rows=128, K=96) -> THE entry point:
  registration solved -> 96-row sub-pixel signed error field -> clusters
  above a per-row MEASURED floor = the distinctions (generated, not
  eyeballed) -> prescriptions (owning stashed parts + world-unit magnitudes
  + direction). masterwork == True when zero clusters clear the floor.
- verify_pass(ref_dig, pre_compare_result, ...) -> same-field re-measure:
  matched cluster deltas, new clusters, resolved, registration drift.
- overlay(model_canon, ref_canon) -> ASCII '#'/'M'/'R' direct comparison.
- canonicalize / resample / error_field / floor2 / prescribe -> the organs,
  callable separately.

### v2 doctrine
- The reference is re-measured every loop (digitize is cheap); constants are
  never cached (honesty-audit lesson).
- The floor is a FIELD: tight on smooth rows (~0.009 canonical / ~0.016
  world on boy_v2), honestly loose at hair crevices (p90 ~0.041). A
  distinction below its row's floor is noise.
- Calibration gate passed 2026-07-05: model-vs-own-rasterization returns
  masterwork=True, pipeline error 0.0064 canonical max, overlay mismatch 0.1%.
- v1 stays the substrate: eye/senses unchanged; occupancy/grid_diff still the
  tool for interior (non-silhouette) features v2 cannot see.
