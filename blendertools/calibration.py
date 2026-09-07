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


def test_plan():
    """plan.py invariants: expressions evaluate, the detail gate filters, the
    hash is content-based (stable across identical plans, different across
    detail levels), and build() produces exactly the resolved parts."""
    from . import plan
    pl = plan.new("bc_plan_test", detail=3)
    pl["parameters"] = {"r": {"default": 0.5, "min": 0.1, "max": 2.0}}
    plan.add_part(pl, "bc_p_a", "probe", "sphere", location=(0, 2, 0), scale=("r", "r*2", "r+0.5"))
    plan.add_part(pl, "bc_p_b", "probe", "sphere", location=(1, 2, 0), scale=(0.2, 0.2, 0.2), min_detail=5)
    r3 = plan.resolve(pl)
    r3b = plan.resolve(pl)
    pl5 = dict(pl, detail=5)
    r5 = plan.resolve(pl5)
    checks = {
        "expression": abs(r3["parts"][0]["scale"][1] - 1.0) < 1e-9 and abs(r3["parts"][0]["scale"][2] - 1.0) < 1e-9,
        "gate_filters_at_3": len(r3["parts"]) == 1,
        "gate_opens_at_5": len(r5["parts"]) == 2,
        "hash_stable": r3["sha256"] == r3b["sha256"],
        "hash_differs_by_detail": r3["sha256"] != r5["sha256"],
    }
    rep = plan.build(r3, clear_first=False, fuse=False)
    checks["build_count"] = rep["parts_built"] == 1
    checks["provenance"] = rep["plan_sha256"] == r3["sha256"]
    for nm in ("bc_p_a", "bc_p_b"):
        o = bpy.data.objects.get(nm)
        if o:
            bpy.data.objects.remove(o, do_unlink=True)
    bad = False
    try:
        plan.expression("__import__('os').system('x')", {})
    except ValueError:
        bad = True
    checks["rejects_code"] = bad
    return {"pass": all(checks.values()), "checks": checks}


def run_all(write_report=True):
    """Run every ground-truth test. Returns the results AND, by default, writes a
    timestamped evidence report (platform, versions, every number) to
    config.CALIBRATION_REPORT_DIR -- a pass is a claim; a report is evidence."""
    import json, os, platform, time
    results = {"bisect_guard": test_bisect_guard(), "plan": test_plan()}
    with isolated_scene():
        for name, fn in (("torus", test_torus), ("pyramid", test_pyramid), ("occlusion", test_occlusion)):
            _clear()
            try:
                results[name] = fn()
            except Exception as e:  # a crash is a failure, not an abort
                results[name] = {"pass": False, "error": f"{type(e).__name__}: {e}"}
    out = {"passed": all(v.get("pass") for v in results.values()), "results": results,
           "assumptions": results.get("pyramid", {}).get("assumptions", []),
           "evidence": {"package": config.VERSION_STR, "blender": bpy.app.version_string,
                        "platform": f"{platform.system()} {platform.machine()}",
                        "headless": bpy.app.background, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")},
           "not_verified": ["live-scene measurement on a real model (this suite uses known primitives)",
                            "reference fidelity (see gauge.scorecard)"]}
    if write_report:
        d = os.path.expanduser(config.CALIBRATION_REPORT_DIR)
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, f"calibration-{out['evidence']['ts'].replace(':', '')}.json")
        with open(path, "w") as f:
            json.dump(out, f, indent=2, default=str)
        out["report_path"] = path
    return out
