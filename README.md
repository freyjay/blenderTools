# blenderTools

Calibrated AI modeling in Blender over MCP. Claude connects to a live Blender
through the official Blender MCP add-on; screenshots are unreliable over that
transport, so this project gives the agent working senses made of math and
rendered as text -- plus the doctrine, gauges, and ground-truth tests that
keep those senses honest.

## Layout
- `blendertools/` -- the package. `import blendertools as bt`
  - `eye` text renders (id/edges/depth/shade) · `senses` proportion/contour/
    rotation/hardness/silhouette/cavity/occupancy · `measure` guarded rulers,
    enforced bisect, post-fusion attribution · `mesh_mind` part graph and
    continuity contracts · `recipes` fuse ladders, quadriflow, hair pods ·
    `gauge` output quality as tracked numbers · `calibration` ground-truth
    regression suite · `config` every canon value with provenance · `refs`
    digitized reference data
- `skills/blender-connect/` -- the working method (read SKILL.md first)
- `docs/` -- CONNECTION-HANDOFF.md (how to connect), PATCHES.md
- `ledger/` -- masterwork_ledger.md (every loop, honestly), gauge_log.jsonl
- `artifacts/` -- drawing studies

## First run
```python
import blendertools as bt
bt.doctor()
bt.calibration.run_all()     # must pass before trusting any measurement
```
Install: see `blendertools/INSTALL.md` (one symlink into Blender's scripts/modules).

History: this supersedes `freyjay/blender_connect`, kept as the archive.
