"""Destination-aware installer (follow-up audit, packaging). Run with Blender:

    /path/to/Blender --background --python blendertools/install.py -- --source /path/to/blenderTools
    /path/to/Blender --background --python blendertools/install.py -- --uninstall

Discovers THIS Blender's user scripts/modules directory (no hard-coded version),
never replaces an existing real directory, only replaces a symlink with --force,
and prints a machine-readable JSON line: INSTALL {...}
"""
import json
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


def main():
    modules_dir = bpy.utils.user_resource('SCRIPTS', path="modules", create=True)
    target = os.path.join(modules_dir, "blendertools")
    out = {"blender": bpy.app.version_string, "modules_dir": modules_dir, "target": target}
    if "--uninstall" in argv:
        if os.path.islink(target):
            os.unlink(target); out["action"] = "removed symlink"
        elif os.path.isdir(target):
            out["action"] = "refused: target is a real directory, remove it manually"
        else:
            out["action"] = "nothing installed"
        print("INSTALL " + json.dumps(out)); return
    source = arg("--source") or os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    pkg = os.path.join(os.path.abspath(source), "blendertools")
    if not os.path.isfile(os.path.join(pkg, "__init__.py")):
        out["action"] = f"refused: {pkg} is not the blendertools package"; print("INSTALL " + json.dumps(out)); sys.exit(1)
    if os.path.islink(target):
        current = os.path.realpath(target)
        if current == os.path.realpath(pkg):
            out["action"] = "already installed (symlink points here)"
        elif "--force" in argv:
            os.unlink(target); os.symlink(pkg, target); out["action"] = f"replaced symlink (was {current})"
        else:
            out["action"] = f"refused: symlink exists -> {current}; pass --force to replace"; print("INSTALL " + json.dumps(out)); sys.exit(1)
    elif os.path.exists(target):
        out["action"] = "refused: a real directory exists at target; will not replace"; print("INSTALL " + json.dumps(out)); sys.exit(1)
    else:
        os.symlink(pkg, target); out["action"] = "installed symlink"
    # verify import from THIS Blender
    try:
        if modules_dir not in sys.path:
            sys.path.insert(0, modules_dir)
        import importlib; bt = importlib.import_module("blendertools")
        out["import"] = {"ok": True, "version": bt.__version__, "path": os.path.dirname(bt.__file__)}
    except Exception as e:
        out["import"] = {"ok": False, "error": f"{type(e).__name__}: {e}"}
    print("INSTALL " + json.dumps(out))
    if not out["import"]["ok"]:
        sys.exit(1)


main()
