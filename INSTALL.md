# Install (fresh download or clone)

`blendertools` is a plain Python package that runs inside Blender's own
interpreter (Blender 5.1+ / 5.2 tested). It needs no pip and no MCP to import.
The official Blender MCP add-on is only the *transport this project uses to
drive Blender live* — see `docs/CONNECTION-HANDOFF.md` if you want that.

## 1. Get the source
Either `git clone https://github.com/freyjay/blenderTools` or download a tagged
source archive (see `RELEASES.md` for the commit and SHA-256). Put it anywhere;
the install step records where.

## 2. Install into THIS Blender (destination-aware)
```bash
/path/to/Blender --background --python /path/to/blenderTools/blendertools/install.py -- --source /path/to/blenderTools
```
It discovers this Blender's user `scripts/modules` directory (no hard-coded
version), creates a symlink `blendertools -> your checkout`, verifies the import,
and prints one line `INSTALL {...}`. It refuses to replace an existing real
directory, replaces an existing symlink only with `--force`, and never touches
anything else. Moved the checkout? Re-run with `--force`.

Uninstall: same command with `--uninstall` (removes only the symlink).

## 3. Verify in a disposable process (recommended)
```bash
/path/to/Blender --background --factory-startup --disable-autoexec --python-exit-code 1 \
  --python /path/to/blenderTools/blendertools/tests/run_calibration.py -- --source /path/to/blenderTools
```
Exit status is nonzero if any test or the scene-integrity assertion fails. The
report is written under the state directory (below). From inside a session:
`import blendertools as bt; bt.calibration.run_isolated()`.

## Writable state
Reports, plans and the gauge log go to `config.state_dir()`:
`$BLENDERTOOLS_HOME` if set → the repo checkout if the package lives in one →
`~/.blendertools`. Installed code is never written to.

## Everyday use
```python
import blendertools as bt
bt.doctor()                    # versions, install route, socket-patch marker, what is NOT verified
bt.reload()                    # after editing any module
```
Then `START-HERE.md` for the method.
