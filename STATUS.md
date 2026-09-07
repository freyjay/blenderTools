# blenderTools — status

The working checklist. `docs/structure.html` is the same information drawn for
outsiders; when this file changes, update the `NODES` / `OPEN` arrays there too.
Last updated: 2026-09-07 · v0.9.0 (`a9a742e`) · suite 29/29 in an isolated process.

Status marks: `[x]` built and tested · `[~]` built, never executed · `[!]` built, known limitation · `[ ]` missing or blocked

## Parts

### The calibration loop
| | Part | Status | Open |
|---|---|---|---|
| R | Reference (`config`, `refs`) | `[!]` | no uncertainty on reference grids; only one subject digitized |
| P | Plan (`plan.py`) | `[~]` | boy_v3 never captured as a plan; `capture()` never run on a real model |
| B | Build (`recipes.py`) | `[~]` | `quadriflow`, `hair_pods`, `hero_spikes` never executed; profiles 4–5 never built |
| E | Eye (`eye.py`) | `[x]` | — |
| S | Senses (`senses.py`) | `[!]` | `cavity_probe` containment is `not_verified` (no leak-path check) |
| M | Measure (`measure.py`) | `[x]` | `attribute_point`, `owner_at` not in the call test |
| G | Gauge (`gauge.py`) | `[~]` | no scorecard on a real model; no approved baseline |
| L | Ledger (`ledger/`) | `[x]` | — |

### Supporting the loop
| | Part | Status | Open |
|---|---|---|---|
| C | Cast (`cast.py`) | `[x]` | — |
| K | Calibration (`calibration.py`) | `[!]` | `run_isolated()` never executed; Studio's parented-transform and loose-linework checks to adopt |
| N | Mesh mind (`mesh_mind.py`) | `[x]` | — |
| F | Config (`config.py`) | `[x]` | — |
| D | Doctor (`__init__.py`) | `[x]` | — |

### The transport
| | Part | Status | Open |
|---|---|---|---|
| T | Official Blender MCP | `[!]` | no live round-trip since v0.6; large-payload and reconnect untested |
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
- plan: `[x]` new/add_layer/add_part · `[x]` expression · `[x]` resolve · `[x]` verify · `[x]` build · `[~]` capture
- recipes: `[x]` fuse_objects · `[x]` voxel_fuse · `[~]` quadriflow · `[~]` hair_pods · `[~]` hero_spikes
- senses: `[x]` proportions · `[x]` contour_angles · `[x]` turntable · `[x]` render_hardness · `[x]` silhouette · `[x]` occupancy_grid · `[!]` cavity_probe / enclosure_check
- measure: `[x]` edge_bisect · `[x]` width_at · `[x]` parts_at_height · `[~]` attribute_point · `[~]` owner_at
- gauge: `[x]` reference_fit · `[x]` silhouette_fit · `[x]` surface/topology/symmetry · `[~]` scorecard · `[x]` gate · `[x]` approve/reject/log
- calibration: `[x]` 5 known-geometry · `[x]` 23 regression · `[x]` scene integrity + decoys · `[x]` preflight · `[~]` run_isolated · `[ ]` parented transform · `[ ]` loose linework
- transport: `[x]` execute_blender_code · `[x]` socket patch · `[!]` screenshots over this add-on · `[~]` live round-trip on v0.9
- installer: `[~]` install.py · `[x]` INSTALL.md

## Open items — in the order of what unblocks what
- [ ] Add `~/Developer/blenderTools` to the filesystem connector — *you*
- [ ] Open Blender with the MCP server; run `bt.calibration.run_isolated()` once for real — *you + agent*
- [ ] One live MCP round-trip of the suite so "live transport" leaves `not_verified` — *agent*
- [ ] `bt.plan.capture("boy_v3", …)` → `plans/boy_v3.json` — *agent*
- [ ] First `gauge.scorecard()` on boy_v3; log; approve → first baseline the gate can enforce — *agent + you*
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

## What "done" means
The loop has run end to end on the new instruments: a real model rebuilt from its plan, measured by a scorecard, gated against an approved baseline, and logged — with the live transport, the installer and `run_isolated()` all executed at least once.
