"""Ground-truth regression suite.

Two kinds of test live here: known-geometry calibration (torus, pyramid,
occlusion, plan) and REGRESSION tests -- one per defect reproduced by the
external audit of v0.6.0, so none of them can return unnoticed.

Safety model (audit P1-1): every test runs inside isolated_scene(), which
snapshots every pre-existing object's identity, hides them, gives this run a
unique id for all names it creates, deletes only objects it created (by
reference), then restores visibility and ASSERTS the pre-existing set is
unchanged. A suite that damaged the scene reports passed=False even if every
geometric test passed.

    import blendertools as bt
    bt.calibration.run_all()   # -> {"passed", "results", "scene_integrity", "report_path"}
"""

import math
import uuid
from contextlib import contextmanager

import bpy
from mathutils import Vector

from . import config, measure

_RUN = uuid.uuid4().hex[:8]
_COLL = f"bt_calib_{_RUN}"
_OWNED = []          # objects this run created, by reference


def _n(base):
    """Run-unique name -- never collides with a user's object (audit P1-1)."""
    return f"{base}_{_RUN}"


# -------------------------------------------------------------- isolation ----
def _snapshot():
    return {o.name: (o.as_pointer(), o.hide_get(), o.hide_render, o.hide_viewport) for o in bpy.data.objects}


@contextmanager
def isolated_scene():
    before = _snapshot()
    for o in bpy.data.objects:
        try:
            o.hide_set(True)
        except RuntimeError:      # object not in the active view layer (multi-scene files)
            pass
        o.hide_render = True
    integrity = {"ok": True, "problems": []}
    try:
        yield integrity
    finally:
        _cleanup()
        for name, (ptr, hv, hr, hvp) in before.items():
            o = bpy.data.objects.get(name)
            if o is None or o.as_pointer() != ptr:
                integrity["problems"].append(f"pre-existing object lost or replaced: {name}")
                continue
            try:
                o.hide_set(hv)
            except RuntimeError:
                pass
            o.hide_render = hr; o.hide_viewport = hvp
        after = _snapshot()
        extra = set(after) - set(before)
        if extra:
            integrity["problems"].append(f"objects left behind: {sorted(extra)}")
        integrity["ok"] = not integrity["problems"]


def _coll():
    c = bpy.data.collections.get(_COLL)
    if c is None:
        c = bpy.data.collections.new(_COLL)
        bpy.context.scene.collection.children.link(c)
    return c


def _adopt(name):
    o = bpy.context.active_object
    for c in list(o.users_collection):
        c.objects.unlink(o)
    _coll().objects.link(o)
    o.name = _n(name)
    o.hide_set(False); o.hide_render = False
    _OWNED.append(o)
    return o


def _cleanup():
    for o in list(_OWNED):
        try:
            bpy.data.objects.remove(o, do_unlink=True)
        except ReferenceError:
            pass
    _OWNED.clear()
    c = bpy.data.collections.get(_COLL)
    if c is not None and len(c.objects) == 0:
        bpy.data.collections.remove(c)


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


def _cube(name, loc, size=2.0):
    bpy.ops.mesh.primitive_cube_add(size=size, location=loc)
    return _adopt(name)


# ======================================================= calibration tests ====
def test_torus(R=1.0, r=0.30):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=(0, 2, 0),
                                     rotation=(math.pi / 2, 0, 0), major_segments=48, minor_segments=24)
    _adopt("torus")
    cast = _ray()
    t = _transitions(lambda x: cast(x)[0])
    ok = len(t) == 4
    R_rec = r_rec = None
    if ok:
        oL, iL, iR, oR = t
        outer, inner = (abs(oL) + abs(oR)) / 2, (abs(iL) + abs(iR)) / 2
        R_rec, r_rec = (outer + inner) / 2, (outer - inner) / 2
    tol = config.TOL["calibration_len"]
    return {"pass": ok and abs(R_rec - R) < tol and abs(r_rec - r) < tol,
            "R": (R_rec, R), "r": (r_rec, r), "transitions": [round(v, 4) for v in t]}


def test_pyramid(R=1.0, H=2.0):
    assumptions = []
    for rot_deg in (0.0, 45.0):
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=R, radius2=0.0, depth=H,
                                        location=(0, 3.0, 0), rotation=(0, 0, math.radians(rot_deg)))
        obj = _adopt("pyramid")
        cast = _ray()
        def depth(x):
            h, loc, *_ = cast(x)
            return loc.y if h else None
        half = R / 2
        d_edge, d_mid, d_q = depth(-half + 0.01), depth(0.0), depth(-half / 2)
        if None in (d_edge, d_mid, d_q) or abs(d_edge - d_mid) < 0.05:
            assumptions.append(f"rot={rot_deg}: not vertex-on, retrying")
            _OWNED.remove(obj); bpy.data.objects.remove(obj, do_unlink=True)
            continue
        slope = (d_mid - d_q) / (half / 2); amp = d_edge - d_mid
        assumptions.append(f"vertex-on achieved at rot={rot_deg}")
        return {"pass": abs(abs(slope) - 1.0) < config.TOL["calibration_slope"] and abs(amp - half) < 0.02,
                "slope": (round(slope, 4), 1.0), "amplitude": (round(amp, 4), half), "assumptions": assumptions}
    return {"pass": False, "error": "no vertex-on orientation found", "assumptions": assumptions}


def test_occlusion(R=1.0, r=0.30):
    from . import senses
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=(0, 2, 0), rotation=(math.pi / 2, 0, 0))
    t = _adopt("torus_occ")
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(1.0, 0.5, 0))
    _adopt("blocker")
    s = senses.silhouette("FRONT", frame=[t.name], rows=40)
    row = min(range(len(s["v"])), key=lambda i: abs(s["v"][i]))
    right = s["right"][row]
    return {"pass": right is not None and abs(right - (R + r)) < 0.02,
            "right_edge": (None if right is None else round(right, 4), R + r)}


def test_bisect_guard():
    hit = lambda x: x > 0.5
    try:
        measure.edge_bisect(hit, 0.0, 1.0)
        return {"pass": False, "note": "swapped arguments were accepted"}
    except ValueError:
        pass
    v = measure.edge_bisect(hit, 1.0, 0.0)
    return {"pass": abs(v - 0.5) < 1e-3, "root": round(v, 5)}


def test_plan():
    from . import plan
    pl = plan.new(_n("plan"), detail=3)
    pl["parameters"] = {"r": {"default": 0.5, "min": 0.1, "max": 2.0}}
    a, b = _n("p_a"), _n("p_b")
    plan.add_part(pl, a, "probe", "sphere", location=(0, 2, 0), scale=("r", "r*2", "r+0.5"))
    plan.add_part(pl, b, "probe", "sphere", location=(1, 2, 0), scale=(0.2, 0.2, 0.2), min_detail=5)
    r3, r3b, r5 = plan.resolve(pl), plan.resolve(pl), plan.resolve(dict(pl, detail=5))
    checks = {"expression": abs(r3["parts"][0]["scale"][1] - 1.0) < 1e-9,
              "gate_3": len(r3["parts"]) == 1, "gate_5": len(r5["parts"]) == 2,
              "hash_stable": r3["sha256"] == r3b["sha256"], "hash_detail": r3["sha256"] != r5["sha256"]}
    # P2-10: profile voxel must affect the hash
    saved = config.DETAIL_PROFILES[3]["voxel"]
    try:
        config.DETAIL_PROFILES[3]["voxel"] = saved * 2
        checks["hash_profile"] = plan.resolve(pl)["sha256"] != r3["sha256"]
    finally:
        config.DETAIL_PROFILES[3]["voxel"] = saved
    tampered = dict(r3, parts=[dict(r3["parts"][0], scale=[9, 9, 9])])
    checks["verify_rejects_tamper"] = not plan.verify(tampered)
    rep = plan.build(r3, clear_first=False, fuse=False, collection=_COLL)
    o = bpy.data.objects.get(a)
    if o:
        _OWNED.append(o)
    checks["build_count"] = rep["parts_built"] == 1
    checks["provenance"] = rep["plan_sha256"] == r3["sha256"]
    checks["in_collection"] = o is not None and any(c.name == _COLL for c in o.users_collection)
    try:
        plan.expression("__import__('os').system('x')", {}); checks["rejects_code"] = False
    except ValueError:
        checks["rejects_code"] = True
    return {"pass": all(checks.values()), "checks": checks}


# ================================================== audit regression tests ====
def test_bad_frame_rejected():
    """P1-4: a typo in frame must raise, not measure the whole scene."""
    from . import senses, eye
    _cube("decoy", (0, 2, 0))
    out = {}
    for label, fn in (("proportions", lambda: senses.proportions("FRONT", frame=[_n("does_not_exist")])),
                      ("render_ascii", lambda: eye.render_ascii(view="FRONT", width=10, frame=[_n("does_not_exist")])),
                      ("empty_frame", lambda: senses.silhouette("FRONT", frame=[]))):
        try:
            fn(); out[label] = "accepted (BUG)"
        except ValueError:
            out[label] = "rejected"
    return {"pass": all(v == "rejected" for v in out.values()), "checks": out}


def test_refuse_render_visible():
    """P1-3: the second fuse must be render-visible."""
    from . import recipes
    a = _cube("fa", (0, 2, 0)); b = _cube("fb", (0.8, 2, 0))
    out = _n("fused")
    f1 = recipes.voxel_fuse([a.name, b.name], out, voxel=0.2); _OWNED.append(f1)
    r1 = f1.hide_render
    f2 = recipes.voxel_fuse([a.name, b.name], out, voxel=0.2); _OWNED.append(f2)
    r2 = f2.hide_render
    return {"pass": (r1 is False and r2 is False), "hide_render_first": r1, "hide_render_second": r2}


def test_fuse_contract():
    """P2-8: fusing a 'separate' layer must be refused; foreign-name collisions refused."""
    from . import mesh_mind, recipes
    a = _cube("ca", (0, 2, 0)); foreign = _cube("foreign", (5, 2, 0))
    graph = {"sep": {"continuity": "separate", "members": [a.name]},
             "fus": {"continuity": "fuse", "members": [a.name]}}
    checks = {}
    try:
        mesh_mind.fuse_group(graph, "sep", voxel=0.2, fused_name=_n("x")); checks["separate_refused"] = False
    except ValueError:
        checks["separate_refused"] = True
    try:
        recipes.voxel_fuse([a.name], foreign.name, voxel=0.2); checks["collision_refused"] = False
    except ValueError:
        checks["collision_refused"] = True
    checks["foreign_survived"] = bpy.data.objects.get(foreign.name) is not None
    return {"pass": all(checks.values()), "checks": checks}


def test_gate_order():
    """P1-5: log order must not fool the gate; no cross-model fallback."""
    import json, os, tempfile
    from . import gauge
    path = os.path.join(tempfile.gettempdir(), f"bt_gate_{_RUN}.jsonl")
    def sc(model, comp, cid):
        return {"id": cid, "model": model, "ts": "t", "config_hash": "h", "coverage": ["fit"],
                "components": {"fit": comp}, "composite": comp}
    try:
        gauge.log(sc("m", 0.9, "a"), path)
        cand = sc("m", 0.1, "b")
        gauge.log(cand, path)                       # the wrong order, on purpose
        g_after = gauge.gate(cand, path)           # must STILL catch the drop
        other = gauge.gate(sc("other_model", 0.1, "c"), path)
        return {"pass": (g_after["ok"] is False) and other.get("no_baseline") is True,
                "gate_after_log": g_after["ok"], "cross_model": other}
    finally:
        try: os.remove(path)
        except OSError: pass


def test_iou_shape_mismatch():
    from . import gauge
    try:
        gauge.iou([[1]], [[1, 1]]); return {"pass": False}
    except ValueError:
        return {"pass": True}


def test_cross_section_truncation():
    """P2-11: truncated sections must not reference dropped points."""
    from . import eye
    c = _cube("xs", (0, 2, 0))
    r = eye.cross_section(c.name, plane_co=(0, 2, 0), plane_no=(0, 0, 1), max_points=2)
    ok = r["truncated"] and all(0 <= i < r["n_points"] for e in r["edges"] for i in e)
    return {"pass": ok, "n_points": r["n_points"], "edges": r["edges"]}


def test_cavity_plane_not_enclosed():
    """P2-12: a flat plane under a rim height has depth but is NOT enclosed."""
    from . import senses
    bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, 0.0))
    _adopt("plane")
    r = senses.cavity_probe(center=(0, 0), rim_radius=0.7, rim_z=2.0, n=8)
    return {"pass": (r["enclosed"] is False and r["holds_liquid"] is False and r["max_depth"] > 0.3),
            "max_depth": r["max_depth"], "enclosed": r["enclosed"]}


def test_turntable_guard():
    from . import senses
    try:
        senses.turntable(step_deg=0); return {"pass": False}
    except ValueError:
        return {"pass": True}


def test_width_out_of_range():
    """P2-7: asking for a height the object never reaches must raise."""
    c = _cube("w", (0, 2, 0))
    try:
        measure.width_at(100.0, [c.name]); return {"pass": False}
    except ValueError:
        w, info = measure.width_at(0.0, [c.name])
        return {"pass": abs(w - 2.0) < 0.05 and abs(info["sampled_z"]) < info["row_spacing"],
                "width": round(w, 3), "sampled_z": info["sampled_z"]}


def test_public_imports():
    """P1-2: every advertised public function must be callable from a clean package import."""
    from . import senses, eye, gauge, mesh_mind, plan, recipes, measure as m
    bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.3, location=(0, 2, 0), rotation=(math.pi / 2, 0, 0))
    t = _adopt("imp")
    checks = {}
    for label, fn in (("occupancy_grid", lambda: senses.occupancy_grid(n=8, frame=[t.name])),
                      ("silhouette", lambda: senses.silhouette("FRONT", frame=[t.name], rows=8)),
                      ("proportions", lambda: senses.proportions("FRONT", frame=[t.name], rows=8)),
                      ("render_ascii", lambda: eye.render_ascii(view="FRONT", width=8, frame=[t.name])),
                      ("island_census", lambda: mesh_mind.island_census(t.name)),
                      ("topology", lambda: gauge.topology(t.name)),
                      ("parts_at_height", lambda: m.parts_at_height(0.0, names=[t.name])),
                      ("overlap_candidates", lambda: mesh_mind.overlap_candidates([t.name])),
                      ("enclosure_check", lambda: senses.enclosure_check(center=(0, 2), rim_radius=0.7, rim_z=1.0, floor_z=-0.5, frame=[t.name], n_dirs=4, levels=1))):
        try:
            fn(); checks[label] = "ok"
        except Exception as e:
            checks[label] = f"{type(e).__name__}: {e}"[:90]
    return {"pass": all(v == "ok" for v in checks.values()), "checks": checks}


# ======================================================== Stage B tests ====
def test_occupancy_occlusion():
    """P2-6: an unselected blocker in front must not change selected-frame occupancy,
    and occupancy must agree with silhouette about the same scene."""
    from . import senses
    bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.3, location=(0, 2, 0), rotation=(math.pi / 2, 0, 0))
    t = _adopt("occ_t")
    n0 = sum(sum(r) for r in senses.occupancy_grid(n=16, frame=[t.name])["grid"])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.6, location=(1.0, 0.4, 0))
    _adopt("occ_blocker")
    n1 = sum(sum(r) for r in senses.occupancy_grid(n=16, frame=[t.name])["grid"])
    return {"pass": n0 > 0 and n0 == n1, "cells_before": n0, "cells_after_blocker": n1}


def test_policy_semantics():
    """'selected' ignores occluders; 'visible' counts them. Both must be explicit."""
    from . import eye
    bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.3, location=(0, 2, 0), rotation=(math.pi / 2, 0, 0))
    t = _adopt("pol_t")
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.6, location=(1.0, 0.4, 0))
    _adopt("pol_blocker")
    def cells(policy):
        g = eye.render_ascii(view="FRONT", width=16, height=16, mode="id", frame=[t.name], policy=policy)
        return sum(1 for ch in "".join(g.split(chr(10))[2:]) if ch != " ")
    sel, vis = cells("selected"), cells("visible")
    return {"pass": sel > vis > 0, "selected_cells": sel, "visible_cells": vis}


def test_far_subject():
    """P2-7a: subjects far from the origin measure exactly like near ones."""
    from . import senses
    out = {}
    for label, loc, view in (("front_far_neg", (0, -100, 0), "FRONT"), ("front_far_pos", (0, 100, 0), "FRONT"),
                              ("right_far", (100, 3, 0), "RIGHT"), ("top_far", (0, 0, -100), "TOP")):
        c = _cube("far", loc)
        p = senses.proportions(view, frame=[c.name], rows=24)
        out[label] = round(p["W"], 3)
        _OWNED.remove(c); bpy.data.objects.remove(c, do_unlink=True)
    return {"pass": all(abs(w - 2.0) < 0.05 for w in out.values()), "widths": out}


def test_transforms_and_modifiers():
    """Scale, rotation and modifiers must be reflected (evaluated world-space BVH)."""
    from . import senses
    out = {}
    c = _cube("sc", (0, 2, 0)); c.scale = (3, 1, 1)
    out["scaled_w"] = round(senses.proportions("FRONT", frame=[c.name], rows=24)["W"], 3)
    c.scale = (1, 1, 1); c.rotation_euler = (0, 0, math.radians(45))
    out["rotated_w"] = round(senses.proportions("FRONT", frame=[c.name], rows=24)["W"], 3)
    c.rotation_euler = (0, 0, 0)
    mod = c.modifiers.new("arr", "ARRAY"); mod.count = 2; mod.relative_offset_displace = (1.0, 0, 0)
    out["array_w"] = round(senses.proportions("FRONT", frame=[c.name], rows=24)["W"], 3)
    ok = abs(out["scaled_w"] - 6.0) < 0.1 and abs(out["rotated_w"] - 2 * math.sqrt(2)) < 0.1 and abs(out["array_w"] - 4.0) < 0.1
    return {"pass": ok, "measured": out, "expected": {"scaled_w": 6.0, "rotated_w": round(2 * math.sqrt(2), 3), "array_w": 4.0}}


# ======================================================================= run ====
CALIBRATION = (("bisect_guard", test_bisect_guard), ("torus", test_torus), ("pyramid", test_pyramid),
               ("occlusion", test_occlusion), ("plan", test_plan))
REGRESSION = (("audit_P1_2_public_imports", test_public_imports),
              ("audit_P1_3_refuse_render_visible", test_refuse_render_visible),
              ("audit_P1_4_bad_frame_rejected", test_bad_frame_rejected),
              ("audit_P1_5_gate_order", test_gate_order),
              ("audit_P2_7_width_out_of_range", test_width_out_of_range),
              ("audit_P2_8_fuse_contract", test_fuse_contract),
              ("audit_P2_11_iou_shape", test_iou_shape_mismatch),
              ("audit_P2_11_cross_section", test_cross_section_truncation),
              ("audit_P2_12_cavity_plane", test_cavity_plane_not_enclosed),
              ("audit_hardening_turntable_guard", test_turntable_guard),
              ("audit_P2_6_occupancy_occlusion", test_occupancy_occlusion),
              ("audit_P2_6_policy_semantics", test_policy_semantics),
              ("audit_P2_7a_far_subject", test_far_subject),
              ("stageB_transforms_and_modifiers", test_transforms_and_modifiers))


def run_all(write_report=True):
    """Run calibration + regression tests inside one isolation boundary. Also
    plants decoys named like the OLD conventions (audit P1-1) to prove the suite
    no longer deletes a user's objects by name."""
    import json, os, platform, time
    results = {}
    decoys, decoy_coll = [], None
    for name in ("bc_p_a", "bc_calibration_decoy"):
        if name not in bpy.data.objects:
            bpy.ops.mesh.primitive_cube_add(size=0.5, location=(9, 9, 9))
            d = bpy.context.active_object; d.name = name; decoys.append(d)
    # the audit's exact reproduction: a pre-existing COLLECTION named like the old convention
    if "bc_calibration" not in bpy.data.collections and decoys:
        decoy_coll = bpy.data.collections.new("bc_calibration")
        bpy.context.scene.collection.children.link(decoy_coll)
        decoy_coll.objects.link(decoys[0])
    dec_ptrs = {d.name: d.as_pointer() for d in decoys}
    with isolated_scene() as integrity:
        for name, fn in CALIBRATION + REGRESSION:
            try:
                results[name] = fn()
            except Exception as e:
                results[name] = {"pass": False, "error": f"{type(e).__name__}: {e}"}
            _cleanup()
    decoy_ok = all(bpy.data.objects.get(n) is not None and bpy.data.objects[n].as_pointer() == p for n, p in dec_ptrs.items())
    if decoy_coll is not None:
        decoy_ok = decoy_ok and bpy.data.collections.get("bc_calibration") is not None and decoys[0].name in decoy_coll.objects
    results["audit_P1_1_scene_integrity"] = {"pass": integrity["ok"] and decoy_ok,
                                             "problems": integrity["problems"], "decoys_survived": decoy_ok}
    for d in decoys:
        bpy.data.objects.remove(d, do_unlink=True)
    if decoy_coll is not None:
        bpy.data.collections.remove(decoy_coll)
    passed = all(v.get("pass") for v in results.values())
    out = {"passed": passed, "run_id": _RUN,
           "n_tests": len(results), "n_passed": sum(1 for v in results.values() if v.get("pass")),
           "results": results, "scene_integrity": integrity,
           "evidence": {"package": config.VERSION_STR, "blender": bpy.app.version_string,
                        "platform": f"{platform.system()} {platform.machine()}",
                        "headless": bpy.app.background, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")},
           "not_verified": ["live-scene measurement on a real model (this suite uses known primitives)",
                            "reference fidelity (see gauge.scorecard)",
                            "parented / animated transforms (only scale, rotation and one modifier are tested)",
                            "measure.owner_at uses the 'visible' policy by design; not exercised here"]}
    if write_report:
        d = os.path.expanduser(config.CALIBRATION_REPORT_DIR)
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, f"calibration-{out['evidence']['ts'].replace(':', '')}.json")
        with open(path, "w") as f:
            json.dump(out, f, indent=2, default=str)
        out["report_path"] = path
    return out
