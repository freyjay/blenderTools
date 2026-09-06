# Session Lessons -- the case studies behind the doctrine

## The three vetoes (why "a veto is a win")
1. Wrong height: thigh blend at z=1.70 changed nothing (max 82->86 deg). The
   close-up showed the crease at z 1.2-1.4. Re-measured, moved, improved.
2. Method floor: after correct placement, max stuck ~74-86 deg. Overlapping
   primitives have a hardness floor (normals jump at intersections). Fix was
   a METHOD change: duplicate -> join -> voxel remesh = one skin. Junction max
   82 -> 47.5 deg; crease 86.5 -> 35.7; hard cells -66% / -83%.
3. Stale data: pre-fusion bbox ratios (0.68) drove a slimming edit; fused
   silhouette was already 0.643 (on target). Overshoot to 0.602; corrected by
   computed factor x1.225 -> 0.626 vs target 0.63.

## Hardness discrimination (loop 4)
Fusion softened the face too. Raising hardness at the muzzle (+24% hard cells)
was CORRECT there: chin, cleft, brow are anatomy. Same instrument, opposite
prescription. Ask: is this hardness a seam or a feature?

## The 180-degree lesson (eye v0.1 -> v0.2)
A single sign error (right = f x up * -1) rotated every render 180 deg. The
calibration rig (unique shape per axis: +X sphere, +Y cube, +Z cone, origin
torus) exposed it instantly. Always verify a new instrument on a rig with
known asymmetric ground truth before trusting it on real work.

## Transport truth
Blender MCP screenshots: PNG, ~786KB budget (1MB msg * 3/4 b64), HiDPI halved,
then downscaled iteratively -- complex content arrives illegible. Socket bug
upstream (#21): sendall on non-blocking socket truncates large sends on macOS;
patched locally with a blocking-send helper (see repo PATCHES.md). Conclusion
that built this system: text always survives; make the math speak text.

## API archaeology pattern (SketchUp, 3 probes)
1. dir() the entities/classes for candidate methods.
2. Try-ladder constructor variants; read tracebacks as documentation
   ("missing 1 required positional argument: vertex1_index" IS the spec).
3. Verify via authoritative counters (get_num_edges) not assumptions.

## The solid mug (form vs function)
A mug passed every surface sense (hardness 85.8->51.1, clean silhouette,
good ratios) while being a solid cylinder -- no cavity. Human audit caught it.
cavity_probe was born: 0.0 depth before, 1.88 deep / 2.93 units3 after boolean
carve. Also: edges mode showed a disc, not a ring -- same-object depth cliffs
are invisible to object-boundary edges; depth mode is the interior sense.

## Interpretation-engine lessons (boy head, 6-loop audit)
1. Pod/scale systems need TWO orientation modes: LYING (long axis tangent,
   flowing mass) and STANDING (long axis along outward normal + lean, hero
   spikes). Tangent projection mathematically annihilates 'up' at the crown --
   two vetoes proved no tangent flow can make a spike.
2. shade mode is COLORBLIND: it encodes normal-facing geometry. Color-role
   features (iris, pupil) verify via id mode (per-cell ownership), never shade.
3. Audit facial features as an ENSEMBLE: five features 0.11-0.13 low was ONE
   error (underestimated cartoon cranium; eyes belong at vertical middle).
   Coordinated lift fixed all five in one edit: 0.50/0.63/0.38/0.25/0.49.
4. Passing metrics get NO adjustment (profile nose passed loop 1 untouched).

## The disconnect (seen/made/created/adjusted)
Boy head, 64 objects: whole-scene fusing erased surface intent. Fix: part
graph with continuity contracts. Proofs on first run: skin connectivity =
1 component pre-fuse; SkinFused = 1 island, 0 non-manifold; ray ownership:
pupil ray hit PupilL, spike hit HairHero_0, forehead hit SkinFused; scene
census 55 = exactly the declared graph. Jaw edit -> skin-only refuse left
5 witness layers byte-identical. Surfaces are decisions; the graph is where
the decisions live.

## Target practice (layers talking)
Random sealed spawn. Shot 1 aimed by READING the ASCII picture (character
centroid): Bull, err 0.0095. Bisection refine: Bull, err 0.0000. Depth via
ray ranging: 5.0983 vs 5.0983 (err 0). Full 3D fix err 0.0003; radius
0.5499 vs 0.55. Annulus ownership read target structure (Bull center,
Outer ring). Range card drawn in SketchUp FROM the perception numbers --
first time drawing served the work as diagnostic memory, not demo.

## Reference metrology (boy v2 vs photos)
Measured the reference IMAGES into numeric targets (pixel proportions,
+-3 pct), measured the model with the same ratio instruments, diffed:
eyes 15 pct too wide, iris small, neck thin, mouth narrow, occiput
shallow. Five graph-routed corrections -> all five within 0.004 of
reference. Caught an instrument artifact first: skull D/H used bbox H
that included the NECK (0.727 false alarm; head-only = 0.938). Measure
the measurement before trusting the diff.

## The occlusion bug + 22-checkpoint lapping pass (boy v2, round 2)
_caster silently reported a MISS whenever a ray's first hit was outside
`frame` (e.g. hair in front of skin) instead of looking past it. This
fabricated a false forehead-recession reading last round. Fixed with
pass-through bounces (max 8). Re-measured: forehead was NEVER wrong
(-0.84 vs -0.85 target) -- the defect was the ruler, not the geometry.
Lesson: an instrument bug can manufacture a geometry problem that looks
completely convincing. Chin WAS genuinely short (engine-confirmed, both
engine-confirmed points closed to within 0.04). Fixing the chin opened a
new hardness hotspot at the jaw-neck seam (77.7deg) caught only because
depth was checked at the same spot as dimension -- softened to 55.3deg via
neck taper + finer voxel. Full 6-ratio regression held (worst drift 0.013)
and rotation continuity held (max jump 0.143) after both edits -- the part
graph is what makes that cheap to prove instead of assume. Also surfaced,
filed for next round: jaw WIDTH tapers too fast versus the reference
front-width curve (band diff 0.51) -- a depth-correct, width-wrong jaw.
