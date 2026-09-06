"""blendertools -- calibrated AI modeling toolkit for Blender over MCP.

Install (once): symlink this folder into Blender's auto-imported modules dir:
    ln -s ~/Developer/blenderTools/blendertools \\
          ~/Library/Application\\ Support/Blender/5.1/scripts/modules/blendertools
After that, in any session:
    import blendertools as bt
    bt.reload()          # after editing any submodule; dependency-ordered
    bt.eye.render_ascii(...)
"""

__version__ = "0.5.0"

import importlib as _importlib

# Dependency order matters: eye has no deps; senses imports eye; the rest import both.
_SUBMODULES = ["config", "eye", "senses", "measure", "mesh_mind", "recipes", "calibration", "gauge", "refs"]

from . import config, eye, senses, measure, mesh_mind, recipes, calibration, gauge, refs  # noqa: E402


def reload():
    """Reload every submodule in dependency order. Call after editing files.
    Replaces the old pattern of popping sys.modules by hand -- which silently
    served stale code whenever the order was wrong."""
    import sys
    pkg = sys.modules[__name__]
    for name in _SUBMODULES:
        mod = _importlib.import_module(f"{__name__}.{name}")
        _importlib.reload(mod)
        setattr(pkg, name, mod)
    return __version__


def doctor():
    """One-call health check: bpy reachable, submodules loaded, config overrides found."""
    import bpy
    return {
        "version": __version__,
        "blender": bpy.app.version_string,
        "modules": {n: hasattr(__import__(__name__), n) for n in _SUBMODULES},
        "config_overrides": config.overrides_path_if_present(),
    }
