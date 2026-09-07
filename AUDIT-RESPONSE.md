# Audit response — v0.8.0 (Stage A + Stage B)

In reply to the external audit of commit `edc88e9` (v0.6.0). Every finding was
reproducible as described; none is disputed. Each accepted finding now has a
regression test in `blendertools/calibration.py` so it cannot return unnoticed.
Evidence for this release is the calibration report committed under
`ledger/calibration/` alongside the code.

| # | Finding | Status | Regression test | Notes |
|---|---|---|---|---|
| P1-1 | Calibration deleted pre-existing objects by conventional name and still passed | **Fixed** | `audit_P1_1_scene_integrity` | Run-unique names; cleanup by reference only; every test inside the isolation boundary; pre/post identity snapshot; decoys named like the old conventions are planted and must survive. A damaged scene fails the suite even if all geometry passes. |
| P1-2 | Stale `import bpy, eye` in `senses.py`; `occupancy_grid`/`attribute` crashed on clean import | **Fixed** | `audit_P1_2_public_imports` | Patch anchors are now *required* (abort on miss) instead of silent no-ops. Test calls every advertised public function from the package import. |
| P1-3 | Second `voxel_fuse` inherited `hide_render=True` | **Fixed** | `audit_P1_3_refuse_render_visible` | Both visibility flags reset on copies and result, in `recipes` and `mesh_mind`. |
| P1-4 | Unresolved `frame` silently measured the whole scene | **Fixed** | `audit_P1_4_bad_frame_rejected` | `senses._caster` and `eye.render_ascii` raise on missing/empty frames and report requested names. |
| P1-5 | Gate fooled by log-before-compare; cross-model fallback; missing metrics inflated composite | **Fixed** | `audit_P1_5_gate_order` | Scorecards carry an `id`, weights, config hash and coverage. Baseline = same model, same config hash, same coverage, not self. No cross-model fallback. Missing components count as 0. Docs now say gate **before** log. |
| P2-6 | `eye` and `senses` disagree on occlusion | **Fixed (Stage B)** | `audit_P2_6_occupancy_occlusion`, `audit_P2_6_policy_semantics` | New `cast.Caster`: per-selection world-space BVH trees from evaluated meshes; one policy for `eye` and `senses`, named explicitly (`selected` = full projection of selected objects, `visible` = first hit). No pass-through, no bounce cap. |
| P2-7 | Ray origin from projected size; out-of-range height returned nearest row | **Fixed (Stage B)** | `audit_P2_7_width_out_of_range`, `audit_P2_7a_far_subject`, `stageB_transforms_and_modifiers` | Origins are rebased to the target's depth bounds along the ray; subjects at ±100 measure identically to those at the origin. Scale, rotation and modifier evaluation tested. `scanline` routed through the same policy. |
| P2-8 | Contracts declared, not enforced; global clear; unused `collection` | **Fixed** | `audit_P2_8_fuse_contract` | `fuse_group` refuses non-fuse layers, validates members before mutating, refuses foreign-name collisions. `plan.build(clear_first)` removes only run-owned geometry; `collection` honored. |
| P2-9 | AABB overlap presented as proof of connectivity | **Fixed (relabel)** | — | Docstring corrected; `overlap_candidates` alias added; `island_census` after fusion is the proof. |
| P2-10 | Plan hash omitted voxel/profile | **Fixed** | in `plan` test (`hash_profile`, `verify_rejects_tamper`) | Hash covers build options; `build()` verifies before executing. |
| P2-11 | `iou` zip-truncation; `cross_section` dangling edge indices | **Fixed** | `audit_P2_11_iou_shape`, `audit_P2_11_cross_section` | Shape validation; edge remap against retained points; `truncated` flag. |
| P2-12 | `holds_liquid: true` on a flat plane | **Fixed** | `audit_P2_12_cavity_plane` | New `enclosure_check` (radial rays must hit walls). Depth/volume are labeled estimates with stated assumptions. |
| hard. | `turntable(step_deg=0)` infinite loop | **Fixed** | `audit_hardening_turntable_guard` | |
| hard. | JSON overrides turned int profile keys into strings; arbitrary globals overridable | **Fixed** | — | Allow-list of overridable settings; int-key coercion for profile dicts. |
| docs | Stale 4-test count; log-before-compare examples; image "ban" wording | **Fixed** | — | Screenshot limitation is now described as specific to the official MCP screenshot tool, not a universal rule. Socket check described as source-marker detection, not transport validation. |

## Accepted nuance
- Image verification: agreed — the limitation is our transport's, and renders written to disk for a human reviewer are compatible with this toolkit. Studio should not import a blanket ban.
- Factory-startup isolation: agreed for headless runs; inside a live session the suite now enforces run-owned ownership plus a pre/post identity assertion instead.
- Composite score: agreed it is not the sole definition of improvement; `coverage` and per-component deltas are recorded so reviewers can weigh purpose.

## Stage B (done in v0.8.0)
Unified per-selection BVH casting; depth-bounds origins; translation/scale/modifier tests; decoy *collection* planted per your exact reproduction; `hide_set` guarded for multi-scene files; single version source. Still open: parented/animated transforms, reference-registration manifests with uncertainty, a Studio adapter via printed JSON.

Thank you for the reproduction discipline. It found what the author's own suite could not, for the reason the author's suite could not: it tested the failure paths, not the demo path.
