# blendertools package -- install & integration

## Layout (target state in the repo)

```
~/Developer/blendertools/
  blendertools/            <- the package (this folder)
    __init__.py               NEW  reload()/doctor()
    config.py                 NEW  every canon value, with provenance
    measure.py                NEW  guarded rulers, enforced bisect, attribution
    calibration.py            NEW  ground-truth regression suite
    recipes.py                NEW  fuse ladders, quadriflow, hair pods
    eye.py                    MOVE from repo root (unchanged)
    senses.py                 MOVE from repo root, edit 1 import line
    mesh_mind.py              MOVE from repo root, edit 1 import line
    tests/run_calibration.py  NEW  thin runner
  skills/ ...                 (unchanged)
```

## Integration edits (the only changes to existing code)

1. `senses.py`: `from eye import _basis, _targets, _bounds`
   -> `from .eye import _basis, _targets, _bounds`
2. `mesh_mind.py`, inside `occupancy_grid()`: `import eye` -> `from . import eye`
3. Optionally, in `senses.py`, replace the local `_edge_bisect` with
   `measure.edge_bisect` (it already has the correct invariant; the enforced
   version just adds the assertion).

## Make it importable everywhere (one time)

```
ln -s ~/Developer/blenderTools/blendertools \
      "$HOME/Library/Application Support/Blender/5.1/scripts/modules/blendertools"
```
Blender adds `scripts/modules` to `sys.path` at startup, so afterwards:
```python
import blendertools as bt
bt.doctor()
bt.calibration.run_all()     # must pass before trusting any measurement
```
After editing a file: `bt.reload()` -- no more `sys.modules.pop`.

## First run checklist

- [ ] symlink in place, `import blendertools` works with no path hacks
- [ ] `bt.calibration.run_all()["passed"] == True`
- [ ] old root-level eye.py/senses.py/mesh_mind.py removed (or left as shims)
- [ ] SKILL.md load pattern updated to `import blendertools as bt`
- [ ] commit: "package v0.5.0: blendertools/ with config, measure, calibration, recipes"

## Optional per-machine overrides

`~/.blendertools.json`, e.g. `{"VOXEL_FINE": 0.04, "QUADRIFLOW_FACES": 8000}`

## Bug found during package review (fix during integration)

`senses.occupancy_grid()` slices header lines with `[2 if frame is None else 1:]`,
but `eye.render_ascii` emits the legend line in id mode REGARDLESS of frame.
With `frame=` set, the legend text becomes a phantom occupied row 0.
Fix: always slice `[2:]`. (The gauge's IoU would otherwise inherit a fake row.)

## Gauges -- how output quality gets a number

```python
import blendertools as bt
from blendertools import gauge, refs, config
sc = gauge.scorecard("boy_v3", frame_face=["SkinFused","EarL","EarR"],
                     ref_grid_front=gauge.spans_to_grid(refs.BOY_FRONT_SPANS_30))
gauge.log(sc)                      # -> ~/Developer/blenderTools/ledger/gauge_log.jsonl
gauge.compare_to_last(sc)          # deltas + regressions vs previous entry
```
Components: fit (ratio pass fraction, with W contributors listed), silhouette
(IoU vs digitized reference, worst rows named), surface (hard-cell fraction over
3 views), topology (quad fraction, manifold, islands, valence, slivers),
symmetry (mirror error). Composite uses config.GAUGE_WEIGHTS -- change the
weights and the number means something different, so they're logged with it.
