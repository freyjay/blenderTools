"""Suite runner with a real exit contract (follow-up audit P2-9).

Recommended invocation (separate factory-startup process, no auto-exec):
    /path/to/Blender --background --factory-startup --disable-autoexec --python-exit-code 1 \\
        --python blendertools/tests/run_calibration.py -- --source /path/containing/blendertools
Exit status is nonzero if ANY test or the scene-integrity assertion fails.
Prints one machine-readable line: RESULT {...}
"""
import json
import os
import sys

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if "--source" in argv:
    src = argv[argv.index("--source") + 1]
    if src not in sys.path:
        sys.path.insert(0, src)

import blendertools as bt  # noqa: E402

r = bt.calibration.run_all(write_report=True)
summary = {k: v for k, v in r.items() if k != "results"}
summary["failed"] = {n: t for n, t in r["results"].items() if not t.get("pass")}
print("RESULT " + json.dumps(summary, default=str))
print(("PASSED" if r["passed"] else "FAILED"), f"{r['n_passed']}/{r['n_tests']}", "->", r.get("report_path"))
if not r["passed"]:
    raise SystemExit(1)
