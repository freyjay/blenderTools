"""blendertools -- calibrated AI modeling toolkit for Blender over MCP.

Installed via symlink into Blender's scripts/modules; in any session:
    import blendertools as bt
    bt.doctor()                 # health + what is NOT verified
    bt.calibration.run_all()    # ground truth; writes an evidence report
    bt.reload()                 # after editing any submodule; dependency-ordered
"""

from .config import VERSION_STR as __version__  # single source of truth

import importlib as _importlib

# Dependency order matters: cast has no deps; eye imports cast; senses imports both; the rest follow.
_SUBMODULES = ["config", "cast", "eye", "senses", "measure", "mesh_mind", "recipes", "plan", "calibration", "gauge", "refs"]

from . import config, cast, eye, senses, measure, mesh_mind, recipes, plan, calibration, gauge, refs  # noqa: E402


def reload():
    """Reload every submodule in dependency order. Replaces popping sys.modules
    by hand, which silently served stale code whenever the order was wrong."""
    import sys
    pkg = sys.modules[__name__]
    for name in _SUBMODULES:
        mod = _importlib.import_module(f"{__name__}.{name}")
        _importlib.reload(mod)
        setattr(pkg, name, mod)
    return __version__


def patch_status():
    """Is the socket patch (docs/PATCHES.md) still present in the live addon file?
    An addon reinstall silently reverts it; this makes the revert visible."""
    import bpy, hashlib, os
    ver = "%d.%d" % bpy.app.version[:2]
    path = os.path.expanduser(config.MCP_ADDON_FILE.format(ver=ver))
    if not os.path.exists(path):
        return {"status": "addon file not found", "path": path}
    with open(path, "rb") as f:
        data = f.read()
    present = config.MCP_PATCH_MARKER.encode() in data
    return {"status": "present" if present else "REVERTED -- reapply per docs/PATCHES.md",
            "sha256": hashlib.sha256(data).hexdigest()[:16], "path": path,
            "backup_exists": os.path.exists(path + ".bak")}


def doctor():
    """Health check that also lists what it did NOT verify. A passing doctor is
    not permission to trust an untested layer."""
    import bpy, os, platform
    pkg = __import__(__name__)
    return {
        "version": __version__,
        "blender": bpy.app.version_string,
        "platform": f"{platform.system()} {platform.machine()}",
        "headless": bpy.app.background,
        "modules": {n: hasattr(pkg, n) for n in _SUBMODULES},
        "config_overrides": config.overrides_path_if_present(),
        "socket_patch": patch_status(),   # source-marker detection, NOT a transport test
        "plans_dir": os.path.expanduser(config.PLANS_DIR),
        "not_verified_by_doctor": [
            "live MCP round-trip (doctor cannot tell if it was called over MCP or headless)",
            "calibration suite (run bt.calibration.run_all() -- it writes a report)",
            "any model's fidelity to its reference (run bt.gauge.scorecard)",
        ],
    }
