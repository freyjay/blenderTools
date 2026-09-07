# Changelog

## 0.9.0 — 2026-09-06 (follow-up audit response)
Live-scene safety: preflight refuses non-Object Mode before any operator;
fixtures owned by created reference (pointer diff), never active_object;
selection/active restored; run-created zero-user meshes purged, user data
untouched; collections counted; run_isolated() for a separate factory-startup
process with timeout. Ownership: per-model/per-build tokens; clear_first scoped;
created objects tracked by reference so name collisions fuse the NEW part;
staged fusion (validate -> build under staging name -> swap). Provenance: sealed
resolved profile; hash covers what the builder consumes; build-time options in
the report. Gauge: scope forwarded and recorded; reference ids; compat key;
approve/reject events; only approved scorecards are baselines; no-baseline =
unverified. Validation unified across occupancy/grid_diff/width_at; n bounded.
cavity_probe: containment not_verified, no physical boolean. Runner exits
nonzero on failure. Destination-aware install.py; state_dir(); richer evidence;
tag + archive + checksum. Suite 20 -> 29. Follow-up findings are tracked in ledger/masterwork_ledger.md.

## 0.8.0 — 2026-09-06 (audit response, Stage B)
`cast.py`: one casting policy for eye and senses -- per-selection world-space
BVH trees from evaluated meshes, depth-rebased ray origins, explicit 'selected'
(full projection, occluders ignored) vs 'visible' (first hit) semantics. Fixes
audit P2-6 (occupancy/silhouette disagreement) and P2-7a (subjects far from the
origin). scanline routed through it with a step guard. Suite 16 -> 20: occupancy
occlusion, policy semantics, far-subject (+-100 on three views), scale/rotation/
modifier evaluation. Decoy COLLECTION planted per the audit's exact repro;
hide_set guarded for multi-scene files; version has one source (config).

## 0.7.0 — 2026-09-06 (audit response, Stage A)
All P1 findings from the external audit of v0.6.0 fixed, each with a regression
test; suite grows 5 -> 16 including a scene-integrity assertion with planted
decoys. Frame validation in eye/senses (typos raise), render-visibility reset
on re-fuse, fuse contracts enforced with ownership-checked overwrite, gate()
with explicit compatible baseline and no cross-model fallback, scorecard id/
weights/config-hash/coverage, iou shape validation, cross_section edge remap,
cavity_probe -> estimate + enclosure_check, turntable guard, override allow-list,
plan hash covers build options + verify() before build, width_at rejects
out-of-range and returns sampled_z. See AUDIT-RESPONSE.md. Stage B (unified BVH
casting, depth-bounds origins) is listed as not_verified in every report.

## 0.6.0 — 2026-09-06
Adopted from the Astra Blender Studio study (its rigor, not its scope):
- `plan.py`: data-before-code. Declarative model specs with an ast-whitelisted
  expression evaluator, detail gating, content hashing, `build()` returning a
  provenance report, and `capture()` from a live scene. Tested in the suite.
- `config.DETAIL_PROFILES` 1–5 as a process-depth dial (voxel, segments, pods,
  senses, quadriflow). Names describe what the pipeline does, not the look.
- `doctor()`: socket-patch presence check (reinstall reverts it) and explicit
  `not_verified_by_doctor` fields.
- `calibration.run_all()` writes a timestamped evidence report to
  `ledger/calibration/` (platform, versions, every number, what was not verified).
- `gauge.topology`: loose vertices, degenerate faces, negative scale, empty
  material slots; `clean` flag. `gauge.gate()`: regression invariant vs the
  last logged scorecard of the same model.

## 0.5.0 — 2026-09-06
Package created: eye, senses, mesh_mind promoted from blender_connect; new
config, measure, calibration, recipes, gauge, refs. Ground-truth suite passes
4/4 on first headless run.
