# blenderTools — status

The working checklist. `docs/structure.html` is the same information drawn for
outsiders; when this file changes, update the `NODES` / `OPEN` arrays there too.
Last updated: 2026-09-07 (evening) · v0.9.0 (`4cabe32`) · suite 29/29 isolated **and** 29/29 live over MCP.

Status marks: `[x]` built and tested · `[~]` built, never executed · `[!]` built, known limitation · `[ ]` missing or blocked

## Parts

### The calibration loop
| | Part | Status | Open |
|---|---|---|---|
| R | Reference (`config`, `refs`) | `[!]` | no uncertainty on reference grids; only one subject digitized |
| P | Plan (`plan.py`) | `[~]` | boy_v3 captured (`plans/boy_v3.json`); no model has yet been **built** from a plan |
| B | Build (`recipes.py`) | `[~]` | `quadriflow`, `hair_pods`, `hero_spikes` never executed; profiles 4–5 never built |
| E | Eye (`eye.py`) | `[x]` | — |
| S | Senses (`senses.py`) | `[!]` | `cavity_probe` containment is `not_verified` (no leak-path check) |
| M | Measure (`measure.py`) | `[x]` | `attribute_point`, `owner_at` not in the call test |
| G | Gauge (`gauge.py`) | `[~]` | scorecards taken on v1/v2/v3; no approved baseline yet (deliberate — see zero step) |
| L | Ledger (`ledger/`) | `[x]` | — |

### Supporting the loop
| | Part | Status | Open |
|---|---|---|---|
| C | Cast (`cast.py`) | `[x]` | — |
| K | Calibration (`calibration.py`) | `[!]` | `run_isolated()` executed (isolated 29/29); Studio's parented-transform and loose-linework checks to adopt |
| N | Mesh mind (`mesh_mind.py`) | `[x]` | — |
| F | Config (`config.py`) | `[x]` | — |
| D | Doctor (`__init__.py`) | `[x]` | — |

### The transport
| | Part | Status | Open |
|---|---|---|---|
| T | Official Blender MCP | `[!]` | live round-trip verified on v0.9 (suite 29/29 over MCP); large-payload and reconnect untested; setup guide `docs/CONNECT-MAC.md` |
| Z | Filesystem MCP | `[ ]` | not scoped to the repo — every delivery goes zip → download → path fix → script |
| I | Installer (`install.py`) | `[~]` | never executed; fresh ZIP / clone paths untested |

### The method
| | Part | Status | Open |
|---|---|---|---|
| Q | Skill (`skills/blender-connect/`) | `[!]` | body text is v0.5: no plans, approve lifecycle, caster policies, preflight, run_isolated |
| H | Start here / README / INSTALL / CHANGELOG / RELEASES | `[x]` | never tested by a fresh agent with no help; `INSTALL.md` duplicated |

### What comes out
| | Part | Status | Open |
|---|---|---|---|
| V | Models (cat, mug, boy_v3) | `[!]` | none built from a plan; zero modeling since v0.5 |
| X | Releases (tag v0.9.0, archive, sha256) | `[x]` | — |
| A | Audit responses (public round 1; internal round 2 + letter) | `[x]` | `internal/` not backed up |
| W | Studio v0.3 Mac test (bundle `d49fe0bd…`) | `[x]` | native client activation and setup-rerun intentionally untested |

## Function-level marks
- plan: `[x]` new/add_layer/add_part · `[x]` expression · `[x]` resolve · `[x]` verify · `[x]` build · `[x]` capture
- recipes: `[x]` fuse_objects · `[x]` voxel_fuse · `[~]` quadriflow · `[~]` hair_pods · `[~]` hero_spikes
- senses: `[x]` proportions · `[x]` contour_angles · `[x]` turntable · `[x]` render_hardness · `[x]` silhouette · `[x]` occupancy_grid · `[!]` cavity_probe / enclosure_check
- measure: `[x]` edge_bisect · `[x]` width_at · `[x]` parts_at_height · `[~]` attribute_point · `[~]` owner_at
- gauge: `[x]` reference_fit · `[x]` silhouette_fit · `[x]` surface/topology/symmetry · `[x]` scorecard · `[x]` gate · `[x]` approve/reject/log
- calibration: `[x]` 5 known-geometry · `[x]` 23 regression · `[x]` scene integrity + decoys · `[x]` preflight (also refused live in Edit Mode) · `[x]` run_isolated · `[ ]` parented transform · `[ ]` loose linework
- transport: `[x]` execute_blender_code · `[x]` socket patch · `[!]` screenshots over this add-on · `[x]` live round-trip on v0.9
- installer: `[~]` install.py · `[x]` INSTALL.md

## Open items — in the order of what unblocks what
- [ ] Add `~/Developer/blenderTools` to the filesystem connector — *you*
- [x] Open Blender with the MCP server; run `bt.calibration.run_isolated()` once for real — 2026-09-07, `calibration-2026-09-07T124513.json`, 29/29, exit contract honored
- [x] One live MCP round-trip of the suite — 2026-09-07, `calibration-2026-09-07T124543.json`, `headless: false`, 29/29, scene integrity ok. Also: the audit's Edit-Mode scenario reproduced live and **refused** by preflight. (`not_verified` text in code updated in v0.9.1.)
- [x] `bt.plan.capture("boy_v3", …)` → `plans/boy_v3.json` — 64 parts, 6 layers, sha `cad4416a…`; shapes recorded as spheres (stated in notes); `JawBlend` declared in graph but absent, skipped
- [~] First scorecards taken on the same ruler: **v1 0.6151 · v2 0.8425 · v3 0.7401** (logged, ids 6e94b56a / 2eabf9ca / 5eb8b2ea). **Approval deliberately withheld**: all three predate the instruments; v3 regressed from v2 and nothing caught it. The baseline must be the loop's own first output — see the zero step below.
- [ ] **Zero step**: write the brief (a client-style request) and put the five reference images on disk with a registration manifest (`refs/boy/`) — *you + agent*
- [ ] Author `plans/boy_v4.json` from the brief's measurements (not canon defaults); build at detail 3; scorecard; **approve as the first baseline** — *agent + you*
- [ ] v0.9.1: call tests for quadriflow, hair_pods, hero_spikes, capture, scorecard, attribute_point, owner_at — *agent*
- [ ] v0.9.1: adopt Studio's parented-transform and loose-linework checks, credited — *agent*
- [ ] Rewrite `SKILL.md` + `toolkit-api.md` for v0.9; re-upload the skill — *agent + you*
- [ ] Send `Mac-Results-Studio-v03.zip` (`d49fe0bd…`) and the v0.9 reply letters to the Astra team — *you*
- [ ] Rebuild the boy from its plan at detail 3 → gauge → approve: first end-to-end loop on the new instruments — *agent*
- [ ] Improvement loops: edit plan → build → gauge → gate → approve, each one in the ledger — *agent*
- [ ] Topology frontier: quadriflow + subdivision-ready mesh at detail 4–5 — *agent*
- [ ] Second subject from a plan (the cat) to prove generality — *agent*
- [ ] Fresh-agent test: new session, `START-HERE.md` only, no help — *you*
- [ ] Housekeeping: dedupe `INSTALL.md`; archive `freyjay/blender_connect`; private repo for `internal/` — *you*

## Findings — 2026-09-07 live session
- On one ruler, **v1 0.615 → v2 0.843 → v3 0.740**: v3 regressed from v2 and nothing caught it. This is the case for the gate.
- The v3 session's remembered ratios (eye span 0.43) do not reproduce under `gauge.reference_fit` (0.389 with the same W as v2) — the session used a different ruler. Doctrine 12.
- `eye._targets` uses `bpy.context.visible_objects`, which does not exist right after `wm.open_mainfile` in the MCP context; `cast.Caster` already uses `scene.objects`. Fix in v0.9.1.
- `bpy.context.object` is `None` in the MCP socket context even with an active object; use `view_layer.objects.active`.
- The gauge measures fidelity and mesh health, not appeal. A baseline is a floor, not an endorsement; human review (`approve`) stays a separate act.

## What "done" means
The loop has run end to end on the new instruments: a real model rebuilt from its plan, measured by a scorecard, gated against an approved baseline, and logged — with the live transport, the installer and `run_isolated()` all executed at least once.
