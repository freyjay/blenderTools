"""Defaults and canon values. Rule: no bare magic numbers anywhere else in the
package -- every constant lives here WITH a note on where it came from, so it
can be audited instead of remembered.

Overrides: drop a JSON file at ~/.blendertools.json with any top-level key
below to override it per-machine without editing source.
"""

import json
import os

# ---------------------------------------------------------------- fusion ----
VOXEL_COARSE = 0.06    # blockout fuse (cat build); erodes thin tips -- check silhouette after
VOXEL_FINE = 0.045     # detail passes (boy v2/v3); finer preserves creases INCLUDING bad ones
QUADRIFLOW_FACES = 6000   # sensible default for a head; raise for full bodies
QUADRIFLOW_MAX_INPUT_FACES = 400_000   # above this, coarsen first (bpy crash #124004 on dense input)

# ------------------------------------------------------------- perception ----
HARD_DEG = 25.0        # neighbor-normal angle counted as a "hard" cell (hardness probes)
HARDNESS_FULL_DEG = 60.0   # ramp ceiling in render_hardness
TURNTABLE_STEP_DEG = 18.0  # 5% of a rotation, per the calibration curriculum
CHAR_ASPECT = 0.5      # terminal chars ~2x tall; width ~= 2x height for square world aspect
OCCUPANCY_N = 30       # 30x30 grid -- dense enough to catch what 10 bands miss

# ------------------------------------------------- reference-derived canon ----
# Boy head, digitized from the reference photos (+-3% visual-estimate band).
# W = silhouette width at EYE LEVEL, ear-inclusive -- that is how the photo was
# read, so the model must be measured the same way. Measuring "ear-safe" at a
# lower height answers a different question (learned the hard way in v3).
CANON_BOY = {
    "eye_span_over_W": 0.43,
    "iris_over_W": 0.22,
    "mouth_over_W": 0.26,
    "jaw_over_cheek": 0.71,
    "neck_over_W": 0.28,
    "skull_D_over_H": 0.97,      # H = head only (crown->chin), NOT bbox incl. neck
    "ear_protrusion_ratio": 1.13,   # (2 * ear tip x) / (2 * skull half-width at ear height)
    "feature_fractions": {         # z as fraction of crown->chin height
        "eye_line": 0.50, "brow_line": 0.62, "nose_tip": 0.38,
        "mouth": 0.25, "ear_center": 0.48,
    },
}

# Cat (British Shorthair figurine), from 4 reference photos.
CANON_CAT = {"W_over_H": 0.63, "D_over_H": 0.75, "head_diam_over_H": 0.31,
             "ear_rise_over_head_h": 0.15}

# Heights used by the boy ratio checks. Named so a contamination check can be
# run against them (see measure.parts_at_height).
MEASURE_HEIGHTS_BOY = {"eye_level": -0.02, "cheek": -0.55, "jaw": -0.80, "neck": -1.30}

# ------------------------------------------------------------------ hair ----
HAIR = {
    "scalp_center": (0.0, 0.05, 0.15),
    "scalp_radius": 0.95,
    "pod_len": 0.30, "pod_wid": 0.14, "pod_thick": 0.10,
    "flow_back": 0.85,             # lying-mode global flow y component
    "upc_front": 1.1, "upc_slope": 1.6,   # upc = upc_front - upc_slope * max(0, d.y)
    "temple_band": {"y_abs_max": 0.20, "z_min": -0.45, "z_max": 0.55, "x_abs_min": 0.55},
    "hero_standing_bias": (-0.15, -0.60, 0.50),   # outward + forward-up lean; tangent mode CANNOT make a spike
}

# --------------------------------------------------------- detail profiles ----
# A detail level is a PROCESS-DEPTH dial: how fine we fuse, how many pods, which
# senses run, whether quad-remesh happens. Names describe what the pipeline DOES,
# never what the result will look like -- a config string must not promise what a
# gauge cannot confirm (the Astra Studio study's one habit worth NOT copying).
DEFAULT_DETAIL = 3
DETAIL_PROFILES = {
    1: {"name": "blockout",  "voxel": 0.08,  "segments": 16, "hair_pods": 0,  "senses": ["proportions"],
        "gauge": False, "quadriflow": False},
    2: {"name": "massed",    "voxel": 0.06,  "segments": 20, "hair_pods": 30, "senses": ["proportions", "silhouette"],
        "gauge": False, "quadriflow": False},
    3: {"name": "defined",   "voxel": 0.05,  "segments": 24, "hair_pods": 45,
        "senses": ["proportions", "silhouette", "hardness", "turntable"], "gauge": True, "quadriflow": False},
    4: {"name": "refined",   "voxel": 0.045, "segments": 32, "hair_pods": 60,
        "senses": ["proportions", "silhouette", "hardness", "turntable", "occupancy"], "gauge": True, "quadriflow": True},
    5: {"name": "finished",  "voxel": 0.04,  "segments": 48, "hair_pods": 80,
        "senses": ["proportions", "silhouette", "hardness", "turntable", "occupancy", "cavity"], "gauge": True,
        "quadriflow": True, "subdivision": 1},
}

# ------------------------------------------------------------ patch check ----
# The local socket fix to the official MCP addon (docs/PATCHES.md) is reverted by
# any addon reinstall. doctor() checks for this marker in the live file.
MCP_ADDON_FILE = "~/Library/Application Support/Blender/{ver}/extensions/user_default/mcp/mcp_to_blender_server.py"
MCP_PATCH_MARKER = "_sendall_blocking"

# ------------------------------------------------------------- evidence ----
CALIBRATION_REPORT_DIR = "~/Developer/blenderTools/ledger/calibration"
PLANS_DIR = "~/Developer/blenderTools/plans"

# ------------------------------------------------------------------ gauge ----
VERSION_STR = "0.8.0"
GAUGE_LOG = "~/Developer/blenderTools/ledger/gauge_log.jsonl"
# Composite weights. Transparent on purpose: change these, and the composite
# score means something different -- so log the weights with the score.
GAUGE_WEIGHTS = {"fit": 0.30, "silhouette": 0.30, "surface": 0.15, "topology": 0.15, "symmetry": 0.10}

# --------------------------------------------------------------- tolerance ----
TOL = {
    "ratio_pass": 0.03,            # |measured - canon| within this = passing, no touch
    "calibration_len": 1e-3,       # torus R/r recovery on the ground-truth testbed
    "calibration_slope": 0.01,     # pyramid vertex-on slope must be 1.0 +- this
}


def overrides_path_if_present():
    p = os.path.expanduser("~/.blendertools.json")
    return p if os.path.exists(p) else None


def load_overrides():
    """Apply ~/.blendertools.json on top of the defaults above (top-level keys only)."""
    p = overrides_path_if_present()
    if not p:
        return {}
    with open(p) as f:
        data = json.load(f)
    g = globals()
    applied = {}
    ALLOWED = {"VOXEL_COARSE", "VOXEL_FINE", "QUADRIFLOW_FACES", "HARD_DEG", "DEFAULT_DETAIL",
               "DETAIL_PROFILES", "GAUGE_WEIGHTS", "TOL", "GAUGE_LOG", "CALIBRATION_REPORT_DIR", "PLANS_DIR", "MCP_ADDON_FILE"}
    for k, v in data.items():
        if k not in ALLOWED:
            raise ValueError(f"overrides: '{k}' is not an overridable setting (allowed: {sorted(ALLOWED)})")
        if isinstance(g[k], dict) and isinstance(v, dict):
            # JSON keys are strings; profile keys are ints -- coerce (audit hardening)
            v = {(int(kk) if kk.isdigit() else kk): vv for kk, vv in v.items()}
            g[k] = {**g[k], **v}
        else:
            g[k] = v
        applied[k] = v
    return applied


load_overrides()
