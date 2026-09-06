"""Run inside Blender (execute_blender_code) or headless:
    blender --background --python blendertools/tests/run_calibration.py
"""
import json
import blendertools as bt

r = bt.calibration.run_all()
print(json.dumps(r, indent=2, default=str))
result = r
