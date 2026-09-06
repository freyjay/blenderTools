"""Ground-truth regression suite. Builds primitives with EXACTLY known geometry,
measures them with the toolkit, asserts the toolkit recovers the truth.
If a test fails, the INSTRUMENT is wrong -- here the scene is certain.

    import blendertools as bt
    bt.calibration.run_all()   # -> {"passed": bool, "results": {...}, "assumptions": [...]}

Runs inside an isolation context: every pre-existing object is hidden for the
duration (ray_cast respects visibility) and restored afterwards, so the suite
is valid in ANY open file, not just an empty one.
"""

import math
from contextlib import contextmanager

import bpy
from mathutils import Vector

from . import config, measure

_COLL = "bc_calibration"


# -------------------------------------------------------------- isolation ----
@contextmanager
def isolated_scene():
    """Hide everything that exists now; restore exact visibility on exit."""
    saved = {o.name: (o.hide_get(), o.hide_render) for o in bpy.data.objects}
    for o in bpy.data.objects:
        o.hide_set(True); o.hide_render = True
    try:
        yield
    finally:
        _clear()
        for name, (hv, hr) in saved.items():
            o = bpy.data.objects.get(name)
            if o:
                o.hide_set(hv); o.hide_render = hr


def _scratch():
    coll = bpy.data.collections.get(_COLL)
    if coll is None:
        coll = bpy.data.collections.new(_COLL)
        bpy.context.scene.collection.children.link(coll)
    return coll


def _clear():
    coll = bpy.data.collections.get(_COLL)
    if not coll:
        return
    for o in list(coll.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(coll)


def _adopt(name):
    o = bpy.context.active_object
    for c in list(o.users_collection):
        c.objects.unlink(o)
    _scratch().objects.link(o)
    o.name = name
    o.hide_set(False); o.hide_render = False
    return o


def _ray():
    deps = bpy.context.evaluated_depsgraph_get()
    scene = bpy.context.scene
    def cast(x, z=0.0, y0=-10.0):
        return scene.ray_cast(deps, Vector((x, y0, z)), Vector((0, 1, 0)))
    return cast


def _transitions(hit, lo=-2.5, hi=2.5, step=0.05):
    x, prev, out = lo, hit(lo), []
    while x <= hi + 1e-9:
        cur = hit(x)
        if cur != prev:
            out.append(measure.edge_bisect(hit, x, x - step) if cur
                       else measure.edge_bisect(hit, x - step, x))
        prev, x = cur, x + step
    return out


# ------------------------------------------------------------------ tests ----
def test_torus(R=1.0, r=0.30):
    """Hole facing camera; horizontal scan must recover R and r exactly."""
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=(0, 2, 0),
                                     rotation=(math.pi / 2, 0, 0),
                                     major_segments=48, minor_segments=24)
    _adopt("bc_torus")
    cast = _ray()
    t = _transitions(lambda x: cast(x)[0])
    ok = len(t) == 4
    R_rec = r_rec = None
    if ok:
        oL, iL, iR, oR = t
        outer, inner = (abs(oL) + abs(oR)) / 2, (abs(iL) + abs(iR)) / 2
        R_rec, r_rec = (outer + inner) / 2, (outer - inner) / 2
    tol = config.TOL["calibration_len"]
    passed = ok and abs(R_rec - R) < tol and abs(r_rec - r) < tol
    return {"pass": passed, "R": (R_rec, R), "r": (r_rec, r),
            "n_transitions": len(t), "transitions": [round(v, 4) for v in t]}


def test_pyramid(R=1.0, H=2.0):
    """Vertex-on square pyramid: depth profile is a V with |slope| == 1 (pure
    geometric invariant) and amplitude R/2 at mid-height. Blender's cone phase
    is NOT assumed: if the first orientation reads flat (face-on), rotate 45
    degrees and retry, and report which orientation was needed."""
    assumptions = []
    for rot_deg in (0.0, 45.0):
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=R, radius2=0.0, depth=H,
                                        location=(0, 3.0, 0), rotation=(0, 0, math.radians(rot_deg)))
        obj = _adopt("bc_pyramid")
        cast = _ray()
        def depth(x):
            h, loc, *_ = cast(x)
            return loc.y if h else None
        half = R / 2
        d_edge, d_mid, d_q = depth(-half + 0.01), depth(0.0), depth(-half / 2)
        if None in (d_edge, d_mid, d_q):
            bpy.data.objects.remove(obj, do_unlink=True)
            continue
        if abs(d_edge - d_mid) < 0.05:          # flat => face-on, wrong phase
            assumptions.append(f"cone phase at rot={rot_deg}: face-on, retrying")
            bpy.data.objects.remove(obj, do_unlink=True)
            continue
        slope = (d_mid - d_q) / (half / 2)
        amp = d_edge - d_mid
        ok_slope = abs(abs(slope) - 1.0) < config.TOL["calibration_slope"]
        ok_amp = abs(amp - half) < 0.02
        assumptions.append(f"vertex-on achieved at rot={rot_deg}")
        return {"pass": ok_slope and ok_amp, "slope": (round(slope, 4), 1.0),
                "amplitude": (round(amp, 4), half), "assumptions": assumptions}
    return {"pass": False, "error": "no vertex-on orientation found", "assumptions": assumptions}


def test_occlusion(R=1.0, r=0.30):
    """A blocker in front of the torus must NOT shorten a frame-filtered
    silhouette -- the hair-shadow / eye-shadow bug, made permanent."""
    from . import senses
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=(0, 2, 0),
                                     rotation=(math.pi / 2, 0, 0))
    _adopt("bc_torus_occ")
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(1.0, 0.5, 0))
    _adopt("bc_blocker")
    s = senses.silhouette("FRONT", frame=["bc_torus_occ"], rows=40)
    row = min(range(len(s["v"])), key=lambda i: abs(s["v"][i]))
    right = s["right"][row]
    passed = right is not None and abs(right - (R + r)) < 0.02
    return {"pass": passed, "right_edge": (None if right is None else round(right, 4), R + r)}


def test_bisect_guard():
    """The enforced invariant must refuse swapped arguments."""
    hit = lambda x: x > 0.5
    try:
        measure.edge_bisect(hit, 0.0, 1.0)   # swapped on purpose
        return {"pass": False, "note": "swapped arguments were accepted"}
    except ValueError:
        pass
    v = measure.edge_bisect(hit, 1.0, 0.0)
    return {"pass": abs(v - 0.5) < 1e-3, "root": round(v, 5)}


def run_all():
    results = {"bisect_guard": test_bisect_guard()}
    with isolated_scene():
        for name, fn in (("torus", test_torus), ("pyramid", test_pyramid), ("occlusion", test_occlusion)):
            _clear()
            try:
                results[name] = fn()
            except Exception as e:  # a crash is a failure, not an abort
                results[name] = {"pass": False, "error": f"{type(e).__name__}: {e}"}
    return {"passed": all(v.get("pass") for v in results.values()), "results": results,
            "assumptions": results.get("pyramid", {}).get("assumptions", [])}
