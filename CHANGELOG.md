# Changelog

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
