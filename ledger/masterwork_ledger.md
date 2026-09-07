# Masterwork Ledger -- boy_v2 vs reference photos
Loop protocol: [1. compare output vs reference -> 3 distinctions with magnitudes;
2. calibrate the ENGINE for those distinctions (perceptual/geometric/both verdict);
3. adjust the MODEL with the calibrated engine; verify same windows] x 20.
Masterwork = new distinctions fall below the engine's perception floor.

## Loop 1 (of 20)
| D | Verdict | Finding | Open magnitude | Close magnitude |
|---|---|---|---|---|
| D1 | perceptual | width-curve band misregistration (bbox vs anatomical span) | false 0.51 | 0 -- engine: senses.width_bands() |
| D2 | geometric | upper skull too wide (bands 1-2) | +0.16/+0.18 | +0.13/+0.14 (carried) |
| D3 | geometric | jaw-neck seam hardness | 71.7 max | VETO at 96.8 (blend misplaced) -> repositioned, see below |

Loop 1 totals: width-curve abs error 0.75 -> 0.60. Regressions held (span 0.429).
Engine gains: width_bands() anatomical registration; graph learned JawBlend.

## Carried queue
- D2 residual: bands 1-2 (+0.13/+0.14)
- D3: seam (value below, post-reposition)

## Honesty audit (post-Loop-1)
User challenge: 'did you actually compare to the reference?' Answer: NO --
loops compared model vs CACHED derived constants; the reference images
stopped being consulted after initial digitization. Fresh look found what
the cache never contained: ear protrusion (defining trait, zero coverage
in 60+ measurements), nose too present from front, lid-over-iris beyond
blockout ceiling (logged as fidelity floor, not fixable by sphere tweak).
Then two instrument failures in the fix itself: a taper-confounded width
ratio faked a failure, causing an overshoot chase (1.14 -> 1.21 -> 1.14).
Ears now: tip 0.998, ratio 1.134 vs 1.13 target.

## Precision upgrade: 30x30 occupancy grid (per-cell, not per-band)
Sparse landmark comparison (10 bands, a dozen profile points) was the real
measuring problem -- too coarse to see localized errors. New instrument:
senses.occupancy_grid(), auto-fit to true bounding extent, dense enough to
catch what bands can't.

First pass found 3 distinctions bands never surfaced:
- rows 2-8: hair falls short 2-4 cols on the right (upper asymmetric bulge)
- rows 14-17: hair holds an unnatural flat plateau 2-3 cols too far LEFT
  while reference has already begun tapering there
- row 28: Collar alone (clean ray-ownership attribution) 3/2 cols too wide

Fixed row 28 (Collar scale 1.0->0.62): right edge now EXACT, left edge
4-off -> 1-off. Checking neighbor rows (never fix in isolation) found the
uniform scale overcorrected the torus's true equator (row 29: undershoots
[12,16] vs [10,19] target) -- filed, not buried. Hair distinctions (rows
2-8, 14-17) require pod-level edits across ~76 objects -- queued for a
dedicated pass rather than rushed this turn.

## Applied in practice (not hypothetical) -- 4 real findings, honestly tracked

1. Zone A (hair, rows 2-8 right shortfall): REAL, attributed to HairHero_1/Hair_05/
   Hair_13 via ray ownership + confirmed empty gap beyond them. Extended all three.
   Gaps closed 4->3, 2->1, 2->1, 2->1 (partial win). Row 2 (the peak) unmoved --
   HairHero_1's extension didn't reach that exact column; carried.

2. Zone B (rows 14-17, "flat plateau"): mis-attributed TWICE.
   - 1st guess (last turn): hair. Wrong -- z-band is below hair territory.
   - 2nd guess (this turn): cheek/face, based on z-height alone, NOT verified by
     attribution (SkinFused post-fuse can't attribute to sub-parts via ray-cast --
     fusion destroys that). Applied a Cheek/Face narrowing on the guess.
   - Verification: ZERO effect on the flagged rows. Regression check found real
     damage instead (eye_span diff 0.0->0.042, mouth 0.003->0.028, jaw/cheek
     0.013->0.152). REVERTED immediately.
   - Correct attribution (via stashed-part bounding-box containment, since fused
     ray-cast can't do it): EarR. The "excess" is the ear -- which was precisely
     calibrated last turn (1.134 vs 1.13 target) via a dedicated probe. Likely
     conclusion: my hand-digitized reference grid underestimated ear extent at
     this exact height -- a reference-reading limit, not a model defect. Held.

3. Discovered mid-repair: fusion (mesh_mind.fuse_group) erases original-part
   attribution for ray-based diagnosis. Bounding-box containment on the STASHED
   (hidden) parts is the correct diagnostic for post-fuse work; z-height alone
   is a guess and produced a real, damaging misfire above.

4. Discovered post-revert: the regression-check instrument itself is
   contaminated. width_at(z=-0.02), used as the W denominator for eye_span/
   mouth/jaw ratios, falls inside EarR's z-span (-0.44 to 0.16) ever since ears
   were widened. Every regression check since that fix has measured cheek+ear
   as one width. The 0.43/0.257/0.697 baseline predates the contamination --
   not wrong, but the wrong ruler now. Geometry (skin: 1 island, 0 non-manifold)
   confirmed sound; RATIO regression status is currently UNKNOWN, not passing,
   until W is redefined at a contamination-free height.

## Carried queue (honest, as of this pass)
- Redefine regression W measurement at a height outside all ear z-spans;
  re-verify true ratio status before trusting any prior "all passing" claim.
- Row 2 hair peak gap (HairHero_1 didn't move it) -- needs a different pod.
- Zone B ear-vs-reference-precision question unresolved -- do not adjust the
  ear again without a more careful direct re-look at that exact photo height.
- Collar equator (row 29) still undershoots, from two loops ago.

## Engine calibration pass (scrutiny session -- no model edits)
Scrutiny found one latent defect and instrumented three known limits:

1. LATENT: occupancy_grid auto-fit re-framed its window every call --
   cross-edit grid comparisons were only valid by luck (D1 class).
   Fix: window lock (center=/extent= params, window returned for reuse);
   auto-fit now projects via eye._basis (view-correct, was FRONT-only x/z).
2. grid_diff(): cell-exact before/after in the SAME window; refuses
   mismatched windows. Closes the overshoot-chase failure mode (todo item).
3. attribute(): stashed-part projected-bbox ownership as an instrument
   (finding 3 doctrine). Verified live: re-derived the EarR/EarL ownership
   of outer cells at v=-0.20 with zero guessing.
4. clean_heights() + width_at(): ruler-contamination guard (finding 4).
   Verified: old W height z=-0.02 lies inside both ear spans (-0.46..0.18),
   W=1.982 there vs W=1.474 at recommended clean z=0.655. Old ratio
   baselines (0.43/0.257/0.697) are RETIRED -- wrong ruler, not comparable.
   Next model pass: re-baseline eye_span/mouth/jaw ratios against clean W.
5. perception_floor(): MEASURED. 30x30 full-figure window: edge wobble
   1 cell (0.0849 world units); width_bands floor 0.052 (normalized).
   Consequences, applied to the carried queue:
   - 1-cell hair gaps (rows 3-8 residuals) are AT the floor: not evidence.
     Do not chase without a tighter window (head-only or n>=44, then
     re-measure the floor for that window).
   - Row-2 peak gap and D2 residual (+0.13/+0.14 > 0.052) remain real.
   Masterwork exit criterion is now computable, not a vibe.

Engine gains: window lock, grid_diff, attribute, clean_heights, width_at,
perception_floor. Verified live on boy_v2; self-tests: lock roundtrip 0/0,
mismatch refused, attribution inside-hit, floor reproducible.

## Engine v2 shipped -- direct reference->product translation
Files: refsense.py (reference senses) + engine2.py (pipeline). v1 unchanged
as substrate. What changed structurally:
- Reference is now a first-class measured object: images digitized to the
  SAME sub-pixel silhouette structure the model uses. Hand-digitized
  constants era closed (root cause of the honesty-audit failure).
- Registration is solved per measurement (crown/bottom anchors + median
  midline), never assumed. D1 doctrine enforced by construction.
- Comparison is a 96-row signed error field, both edges; distinctions are
  GENERATED as ranked clusters above the floor, not eyeballed as 3 picks.
- Prescriptions: each cluster -> owning stashed parts + world-unit
  magnitude + direction. verify_pass() re-measures the identical field.
- Floor is a FIELD: first cut (scalar max) was convicted pre-promotion --
  one ambiguous hair row taxed the whole figure (0.053 world, only 1.6x v1).
  Per-row floor: median 0.0156 world (5.5x v1 precision), p90 0.068 honest.
Calibration gate (instrument proves itself before promotion): rasterize the
model's own silhouette to a synthetic 512px photo, digitize back, compare ->
masterwork=True, zero false clusters, pipeline error 0.0064 canonical max,
overlay mismatch 0.1%.
BLOCKING the first real v2 loop: no reference photos exist as files (v1
constants came from chat-viewed photos). Drop front/right photos in
blender-connect-experiment/refs/, gate them with refsense.preview(), then
engine2.compare() replaces the band/landmark loop. Clean-ruler ratio
re-baseline still pending from the scrutiny pass.

## Ground-truth depth calibration (torus + pyramid, exact known geometry)
Purpose: the boy-model calibration kept hitting an ambiguity -- is a mismatch the
MODEL's fault or my REFERENCE-READING's fault? Primitives with exact, self-known
geometry remove that ambiguity entirely. Built depth_calibration.blend.

### Torus (hole depth, thickness, tilt)
- Built R=1.0, r=0.30, hole facing camera. First scan/bisect gave R=0.95,
  r=0.30 exact -- suspicious (r perfect, R off by 0.05). Hypothesis: mesh
  faceting. Test: doubled segment resolution (24->48). Result: BIT-IDENTICAL
  transitions. Faceting ruled out definitively -- resolution cannot cause an
  error that doesn't shrink under 2x refinement.
- Queried actual mesh vertices directly: true outer edge = -1.300 exactly
  (matches R+r). My scan measured -1.25. Confirmed: the SCAN CODE was wrong,
  not the mesh.
- Root cause found: bisect(x_in, x_out) requires x_in=hit-side, x_out=miss-
  side; my calling convention had them SWAPPED in both branches of the
  transition ternary, causing convergence to a point inside the wrong region
  instead of the true boundary. (Checked senses.py's real _edge_bisect --
  its calling convention is correct; this bug was fresh to this test script,
  not a shipped defect.)
- Fixed. Re-verified: R=1.0000, r=0.3000 -- EXACT to 4 decimals, all 4 edges.
- Thickness sweep: r=0.20->0.55 (nearly doubled). Recovered exactly (1.0/0.55)
  again. Size/thickness tracking confirmed solid post-fix.
- Tilt test (30 deg): naive flat-disk model predicts outer/inner extent via
  cos(30). Measured extents (1.0656/0.6665) both push OUTWARD of the flat
  prediction (1.0392/0.6928) by ~2.5-3% -- a real, quantified limit: a torus
  has 3D tube roundness a flat-ellipse model can't capture. Small, consistent,
  now known rather than assumed.

### Pyramid (depth gradient, angle, size)
- Square pyramid (4-vertex cone), R=1.0, H=2.0. First attempt copied the
  torus's "tip 90 deg to face camera" trick -- wrong, knocked the apex
  sideways, produced a nonsensical depth jump. Corrected: axis stays vertical
  (apex up), only Z-rotation controls vertex/face phase.
- 45 deg Z-rotation gave a FLAT depth profile (face pointed dead at camera,
  zero gradient) -- wrong guess for vertex-on. Default rotation (0 deg) gave
  a clean symmetric V: depth 3.0 -> 2.5 -> 3.0 across x=[-0.5,0,0.5].
- Slope = exactly 1.0. Verified this is a pure geometric INVARIANT (a square
  viewed vertex-on is a 45-deg diamond; diamond edges are always unit-slope
  regardless of size) -- not an R/H-dependent quantity, a clean symmetry
  check the depth sense passed exactly.
- Amplitude (0.5 at R=1) DOES carry size: predicted = R/2 always at the exact
  mid-height (H-independent there). Changed R: 1.0->1.6. Measured amplitude
  0.7989 vs predicted 0.8 -- confirmed size adjustment tracks correctly.

## Takeaway
Ground-truth primitives did exactly what they're for: caught a real bug with
total certainty (impossible against a photo), confirmed size/thickness
tracking to 4 decimals, and quantified (rather than guessed at) where a
simplifying depth model breaks down. This is the calibration the boy-model
work has been missing a foundation under.

## Cold-build test v3 (post ground-truth engine calibration)
Same exercise as the v1->v2 test, repeated now that the ENGINE itself has been
calibrated against ground truth (bisection bug fixed, occlusion-blindness fixed,
mesh_mind attribution understood, regression-ruler contamination understood).

Built fresh from canon values + three structural fixes applied from birth
(not patched later): neck as a stretched sphere (no cylinder cap-rim), temple
hair coverage included in the generation rule, hero spikes born in standing
mode. Corrective iterations needed this pass:

1. First "ear-safe" W measurement (z=-0.55, below ears) gave nonsense ratios
   (0.53/0.32/0.80 vs 0.43/0.26/0.71) -- caught BEFORE acting: realized this
   changed which geometric quantity was being measured, not fixed a bug.
   Corrected to eye-level (ear-inclusive), matching how the original targets
   were derived from the photo in the first place. Result: 0.389/0.232/0.799
   -- close on 2 of 3, one real residual (jaw/cheek).
2. Jaw narrow attempt: ZERO effect (same post-fusion attribution trap as two
   rounds ago). Checked stashed bounding boxes instead of guessing again:
   4 parts overlap at that height (Cranium/Face/Jaw/LipUp), Face is the
   larger contributor. Narrowed Face instead: 0.799 -> 0.753 (target 0.71).
   Eye span/mouth unaffected (no regression).

Final: skin 1 island / 0 non-manifold throughout. Turntable continuity_ok,
max jump 0.204. Two real, correctly-diagnosed corrections needed (vs v1's
~10 and v2's multi-bug journey through false leads). The engine calibration
paid for itself: no wasted loops chasing instrument lies this time, only
genuine residual geometry, found and fixed efficiently.

## v0.6.0 -- rigor adopted from the Astra Blender Studio study
Studied the competitor package (44 files). It cannot model organic subjects at
all and has no perception layer; it is ahead on engineering discipline. Adopted:
plan-before-build with content hashing (plan.py), process-depth detail profiles,
doctor() patch-presence check + explicit not-verified fields, calibration
evidence reports written to ledger/calibration/, mesh-sanity gauge fields, and
gauge.gate() as a hard regression invariant. Declined: CAD/DXF, job queue,
community bridge, and aspirational detail-level names.

## v0.7.0 -- audit response, Stage A
An independent audit of v0.6.0 (Astra team) reproduced 12 defects while our own
suite passed 5/5. All P1s fixed with regression tests (suite 5 -> 16); scene
integrity is now asserted with planted decoys; frame typos raise; re-fuse is
render-visible; gate cannot be fooled by log order; hashes cover build options;
cavity depth is an estimate with an enclosure check, not a verdict. Doctrine 15
and 16 added. The lesson under the twelve: test the failure paths. Stage B
(unified casting, depth-bounds origins) tracked in not_verified.

## v0.8.0 -- audit response, Stage B
One casting policy (cast.Caster): eye and senses now agree about occlusion by
construction; ray origins follow the subject's depth, so a head at y=-100
measures like one at y=2. Suite 16 -> 20. Every P1 and P2 audit finding is now
closed with a test. Open and stated: parented/animated transforms, reference
manifests with uncertainty, Studio adapter.

## v0.9.0 -- follow-up audit response
Second external audit reproduced our 20/20 on Windows / Blender 5.2.1, then
found four live-scene ownership failures (Edit Mode deletion, cross-model
clear, name-collision fusion, delete-before-replace) and five correctness
gaps. All original reproductions fixed with tests (suite 20 -> 29); safety
contract described as partially verified where that is the truth. Ownership is
now by created reference and per-model token; fusion is staged; baselines are
approved, not merely logged. Installer is destination-aware; state dir is
configurable; evidence is machine-readable. First run of the new exit-code
contract caught two of my own stale tests before anything was committed.


## 2026-09-07 -- direction recalibrated
Research and our own numbers agree: MCP-driven Blender is an operator, not a
modeller; likeness is a generation problem. On one ruler v1 0.615 -> v2 0.843 ->
v3 0.740 -- a regression nothing caught. We stop competing on generation and own
measurement, correction and proof: base meshes from an attached multi-view
generator (Meshy/Rodin) with full provenance, measured against the references at
fixed registration, corrected as plan edits, quad-remeshed, gated, approved,
logged. Doctrine 17 added. No baseline approved until the loop's own first output.


## 2026-09-07 -- gauge calibrated on known geometry (calib_head)
A subject we authored as a plan, rendered to three orthographic references with an
exact pixel->world manifest, then read back through the manifest alone: IoU 0.988 /
0.996 / 0.991 against the instrument. Registration is right; the noise floor is ~0.01.
Sensitivity: ear-size error -0.015, mirrored crest -0.054 from the front and 0.000
from the top (silhouette is outline-only -- interior features need id/depth renders),
jaw +10% -0.031 with a live staged re-fuse that replaced the prior result. The IoU
target is now stated as a pair with ratio tolerances. Live-context defects fixed in
plan.build, preflight and eye._targets; suite 29/29 before commit. Mistake recorded:
the reference PNGs carry the silhouette in ALPHA (no World in an empty scene).


## 2026-09-07 -- boy references registered
Three client renders on disk with digests; registration manifest built from
measurement (background sat <= 0.039, lum 0.50-0.55; a luminance-low rule produced
a false stripe from the vignette and was dropped; final rule sat > 0.045 or lum >
0.60). Silhouette grids n=32/64, bbox-normalized, holes filled. Finding: the
reference's eye span is 0.387 of W; canon said 0.43; v3 measured 0.389 and was
penalized for being right. Reference-derived ratios from here on.


## 2026-09-07 -- the references as material: visual hull test
Question: can the registered references supply the base mesh without a generator?
On honest square-window rulers the hand blockouts read 0.65-0.70 (the old 0.84 was a
non-square-window artifact). A two-view visual hull matches front and profile at the
noise floor by construction but is a box in depth (top fill 0.975) and loses 0.13 at
three-quarter angles. Replacing each cross-section rectangle with its inscribed
ellipse keeps both silhouettes and rounds the volume (top fill 0.776 = pi/4); on the
unseen back-3/4 reference it plateaus at 0.85 vs 0.66-0.71 for the plain hull and
0.71-0.74 for the blockouts. Deterministic, free, provenance = the images, ~2 s.
Two instrument lessons on the way: the profile image is the model's LEFT view
(mirror test 0.97 vs 0.66), and 'bbox-normalized' must say square vs per-axis.
Open: thin-region meshing (9 islands), concavities, hair/skin colour layers.
