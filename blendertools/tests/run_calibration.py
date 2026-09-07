"""Run inside Blender (execute_blender_code) or headless:
    blender --background --python blendertools/tests/run_calibration.py
Writes an evidence report; prints its path."""
import json
import blendertools as bt

r = bt.calibration.run_all(write_report=True)
print(json.dumps({k: v for k, v in r.items() if k != "results"}, indent=2, default=str))
print("PASSED" if r["passed"] else "FAILED", "->", r.get("report_path"))
result = r
