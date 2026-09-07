"""Ground-truth regression suite.

Safety model (follow-up audit P1-1). Before ANY operator or decoy:
  * preflight(): Blender must be in Object Mode -- in Edit Mode, primitive
    operators act on the edited mesh and the "new" object is the user's.
  * ownership is by CREATED REFERENCE: every fixture is the exact object that
    appeared after an operator (pointer diff), never bpy.context.active_object.
  * pre-existing objects, selection, active object and mesh datablocks are
    snapshotted; all are restored/asserted on exit. Only zero-user meshes
    created by this run are purged -- never a user's orphan data.
  * decoys named like OLD conventions (object AND collection) are planted and
    must survive.
A suite that damaged or changed the scene reports passed=False even if every
geometric test passed. Prefer run_isolated() (separate factory-startup Blender
with a timeout) for anything but a throwaway scene.
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
_KNOWN = set()       # pointers of everything that existed before this run touched the scene


class UnsafeSceneMode(RuntimeError):
    pass


def preflight():
    """Reject unsafe modes BEFORE any operator or decoy creation."""
    obj = bpy.context.view_layer.objects.active if bpy.context.view_layer else None   # not bpy.context.object: absent in socket/timer contexts
    if obj is not None and obj.mode != "OBJECT":
        raise UnsafeSceneMode(f"calibration refuses to run: active object '{obj.name}' is in {obj.mode} mode. "
                              "Return to Object Mode, or use run_isolated().")
    mode = getattr(bpy.context, "mode", "OBJECT")
    if mode not in ("OBJECT",):
        raise UnsafeSceneMode(f"calibration refuses to run in context mode {mode}")


def _n(base):
    """Run-unique name -- never collides with a user's object (audit P1-1)."""
    return f"{base}_{_RUN}"


# -------------------------------------------------------------- isolation ----
def _snapshot():
    return {o.name: (o.as_pointer(), o.hide_get(), o.hide_render, o.hide_viewport) for o in bpy.data.objects}


def _context_snapshot():
    return {"selected": [o.name for o in bpy.context.selected_objects],
            "active": bpy.context.view_layer.objects.active.name if bpy.context.view_layer.objects.active else None,
            "meshes": {m.as_pointer() for m in bpy.data.meshes}, "n_meshes": len(bpy.data.meshes),
            "n_collections": len(bpy.data.collections)}


@contextmanager
def isolated_scene():
    preflight()
    before = _snapshot()
    ctx = _context_snapshot()
    _KNOWN.clear(); _KNOWN.update(v[0] for v in before.values())
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
        # purge only zero-user meshes this run created (never a user's orphans)
        for m in list(bpy.data.meshes):
            if m.as_pointer() not in ctx["meshes"] and m.users == 0:
                bpy.data.meshes.remove(m)
        # restore selection + active
        bpy.ops.object.select_all(action='DESELECT') if bpy.context.mode == "OBJECT" else None
        for n in ctx["selected"]:
            o = bpy.data.objects.get(n)
            if o is not None:
                try: o.select_set(True)
                except RuntimeError: pass
        bpy.context.view_layer.objects.active = bpy.data.objects.get(ctx["active"]) if ctx["active"] else None
        after = _snapshot()
        extra = set(after) - set(before)
        if extra:
            integrity["problems"].append(f"objects left behind: {sorted(extra)}")
        if len(bpy.data.meshes) != ctx["n_meshes"]:
            integrity["problems"].append(f"mesh datablocks changed: {ctx['n_meshes']} -> {len(bpy.data.meshes)}")
        if len(bpy.data.collections) != ctx["n_collections"]:
            integrity["problems"].append(f"collections changed: {ctx['n_collections']} -> {len(bpy.data.collections)}")
        now = _context_snapshot()
        if now["selected"] != ctx["selected"] or now["active"] != ctx["active"]:
            integrity["problems"].append(f"selection/active changed: {ctx['selected']}/{ctx['active']} -> {now['selected']}/{now['active']}")
        integrity["ok"] = not integrity["problems"]


def _coll():
    c = bpy.data.collections.get(_COLL)
    if c is None:
        c = bpy.data.collections.new(_COLL)
        bpy.context.scene.collection.children.link(c)
    return c


def _adopt(name):
    """Adopt the ONE object that appeared since the last known state -- by
    pointer diff, never by active_object (follow-up audit P1-1)."""
    owned = {o.as_pointer() for o in _OWNED if _alive(o)}
    new = [o for o in bpy.data.objects if o.as_pointer() not in _KNOWN and o.as_pointer() not in owned]
    if len(new) != 1:
        raise RuntimeError(f"_adopt: expected exactly one new object, found {[o.name for o in new]}")
    o = new[0]
    for c in list(o.users_collection):
        c.objects.unlink(o)
    _coll().objects.link(o)
    o.name = _n(name)
    o.hide_set(False); o.hide_render = False
    _OWNED.append(o)
    return o


def _alive(o):
    try:
        o.name
        return True
    except ReferenceError:
        return False


def _own(o):
    """Register an object created by other means (plan.build, fusion) as run-owned."""
    if o is not None and _alive(o):
        _OWNED.append(o)
    return o


def _cleanup():
    for o in list(_OWNED):
        try:
            bpy.data.objects.remove(o, do_unlink=True)
        except ReferenceError:
            pass
    _OWNED.clear()
    for c in list(bpy.data.collections):          # every run-prefixed collection, once empty
        if c.name.startswith(_COLL) and len(c.objects) == 0 and len(c.children) == 0:
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
    o = _own(bpy.data.objects.get(rep["actual_names"][a]))
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
    f1 = _own(recipes.voxel_fuse([a.name, b.name], out, voxel=0.2))
    r1 = f1.hide_render
    f2 = _own(recipes.voxel_fuse([a.name, b.name], out, voxel=0.2))
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
        d = {"id": cid, "model": model, "ts": "t", "config_hash": "h", "coverage": ["fit"],
             "scope": {"frame_face": ["x"], "views": [], "policy": "selected", "algorithm": config.GAUGE_ALGO},
             "components": {"fit": comp}, "composite": comp}
        d["compat"] = gauge.compat_key(d)
        return d
    try:
        base = sc("m", 0.9, "a")
        gauge.log(base, path); gauge.approve("a", path)     # v0.9: only APPROVED scorecards are baselines
        cand = sc("m", 0.1, "b")
        gauge.log(cand, path)                       # the wrong order, on purpose
        g_after = gauge.gate(cand, path)           # must STILL catch the drop (excluded by id)
        other = gauge.gate(sc("other_model", 0.1, "c"), path)
        return {"pass": (g_after["ok"] is False) and other.get("status") == "unverified" and other.get("ok") is None,
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
    return {"pass": ("holds_liquid" not in r and r.get("containment") == "not_verified"
                     and r["max_depth"] > 0.3 and (r.get("wall_coverage") or 0.0) < 0.1),
            "max_depth": r["max_depth"], "containment": r.get("containment"), "wall_coverage": r.get("wall_coverage")}


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


# ================================================= follow-up audit tests ====
def test_editmode_rejected():
    """F-P1-1: calibration must refuse to start while an object is in Edit Mode."""
    c = _cube("em", (0, 2, 0))
    bpy.ops.object.select_all(action='DESELECT'); c.select_set(True)
    bpy.context.view_layer.objects.active = c
    bpy.ops.object.mode_set(mode='EDIT')
    try:
        try:
            preflight(); refused = False
        except UnsafeSceneMode:
            refused = True
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')
    return {"pass": refused}


def test_adopt_never_takes_active():
    """F-P1-1: ownership is by created reference. Make a foreign object active,
    create a fixture, and prove the fixture is the new object, not the active one."""
    foreign = _cube("foreign_active", (7, 7, 7))
    bpy.ops.object.select_all(action='DESELECT'); foreign.select_set(True)
    bpy.context.view_layer.objects.active = foreign
    ptr = foreign.as_pointer()
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(0, 2, 0))
    bpy.context.view_layer.objects.active = foreign        # sabotage: active is the foreign one
    got = _adopt("sphere")
    return {"pass": got.as_pointer() != ptr and got.type == "MESH" and _alive(foreign), "adopted": got.name}


def test_clear_first_scoped():
    """F-P1-2: clear_first removes only THIS model's objects."""
    from . import plan
    other = plan.new(_n("other"), detail=3)
    plan.add_part(other, _n("oth_a"), "probe", "sphere", location=(5, 2, 0), scale=(0.2, 0.2, 0.2))
    ro = plan.resolve(other)
    rep_o = plan.build(ro, fuse=False, collection=_COLL + "_other")
    oth = _own(bpy.data.objects.get(rep_o["actual_names"][_n("oth_a")])); ptr = oth.as_pointer()
    mine = plan.new(_n("mine"), detail=3)
    plan.add_part(mine, _n("mine_a"), "probe", "sphere", location=(0, 2, 0), scale=(0.2, 0.2, 0.2))
    rm_ = plan.resolve(mine)
    rep1 = plan.build(rm_, fuse=False, collection=_COLL); _own(bpy.data.objects.get(rep1["actual_names"][_n("mine_a")]))
    rep2 = plan.build(rm_, clear_first=True, fuse=False, collection=_COLL)   # rebuild mine
    _own(bpy.data.objects.get(rep2["actual_names"][_n("mine_a")]))
    survived = _alive(oth) and bpy.data.objects.get(oth.name) is not None and oth.as_pointer() == ptr
    coll = bpy.data.collections.get(_COLL + "_other")
    if coll:
        for o in list(coll.objects):
            pass
    return {"pass": survived and rep2["parts_built"] == 1, "other_survived": survived}


def test_name_collision_refs():
    """F-P1-3: a pre-existing object with a requested name must not be fused in
    place of the new part; default refuses, 'suffix' fuses the NEW object."""
    from . import plan
    name = _n("Cranium")
    old = _cube("preexisting", (20, 2, 0)); old.name = name; old_ptr = old.as_pointer()
    pl = plan.new(_n("coll"), detail=3); plan.add_layer(pl, "skin", "fuse")
    plan.add_part(pl, name, "skin", "sphere", location=(0, 2, 0), scale=(0.5, 0.5, 0.5))
    r = plan.resolve(pl)
    checks = {}
    try:
        plan.build(r, fuse=True, collection=_COLL); checks["default_refuses"] = False
    except ValueError:
        checks["default_refuses"] = True
    rep = plan.build(r, fuse=True, collection=_COLL, on_collision="suffix")
    part = _own(bpy.data.objects.get(rep["actual_names"][name]))
    fused = _own(bpy.data.objects.get(rep["fused_layers"]["skin"]["name"]))
    lo, hi = rep["bounds"]
    checks["new_part_suffixed"] = part is not None and part.name != name
    checks["fused_near_new_part"] = lo is not None and lo[0] < 1.0 and hi[0] > -1.0 and hi[0] < 5.0
    checks["old_untouched"] = _alive(old) and old.as_pointer() == old_ptr and not old.hide_get()
    checks["fused_in_collection"] = fused is not None and any(c.name == _COLL for c in fused.users_collection)
    return {"pass": all(checks.values()), "checks": checks, "bounds": rep["bounds"]}


def test_staged_fusion():
    """F-P1-4: a failing re-fuse must leave the previous result untouched."""
    from . import recipes
    a = _cube("sfa", (0, 2, 0)); b = _cube("sfb", (0.8, 2, 0))
    out = _n("Result")
    res = _own(recipes.voxel_fuse([a.name, b.name], out, voxel=0.2)); ptr = res.as_pointer()
    bpy.ops.object.empty_add(location=(0, 2, 0)); empty = _adopt("empty")
    checks = {}
    try:
        recipes.fuse_objects([a, empty], out, voxel=0.2); checks["nonmesh_refused"] = False
    except ValueError:
        checks["nonmesh_refused"] = True
    try:
        recipes.fuse_objects([a, b], out, voxel=float("nan")); checks["bad_voxel_refused"] = False
    except ValueError:
        checks["bad_voxel_refused"] = True
    checks["old_result_survived"] = _alive(res) and bpy.data.objects.get(out) is not None and res.as_pointer() == ptr
    checks["no_staging_left"] = (out + ".__staging") not in bpy.data.objects
    return {"pass": all(checks.values()), "checks": checks}


def test_hash_post_resolve():
    """F-P2-5: mutating the resolved profile after resolve() must fail verify()."""
    from . import plan
    pl = plan.new(_n("hp"), detail=3)
    plan.add_part(pl, _n("hp_a"), "probe", "sphere", location=(0, 2, 0), scale=(0.2, 0.2, 0.2))
    r = plan.resolve(pl)
    checks = {"verifies_clean": plan.verify(r)}
    r["profile"]["voxel"] *= 2
    checks["profile_mutation_detected"] = not plan.verify(r)
    try:
        plan.build(r, fuse=False, collection=_COLL); checks["build_refuses"] = False
    except ValueError:
        checks["build_refuses"] = True
    checks["config_not_aliased"] = config.DETAIL_PROFILES[3]["voxel"] != r["profile"]["voxel"]
    return {"pass": all(checks.values()), "checks": checks}


def test_gauge_scope_and_lifecycle():
    """F-P2-6: silhouette scope is forwarded; only APPROVED scorecards are baselines."""
    import os, tempfile
    from . import gauge, senses
    checks = {}
    bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.3, location=(0, 2, 0), rotation=(math.pi / 2, 0, 0))
    t = _adopt("gt"); _cube("gt_far", (30, 2, 0))
    ref = senses.occupancy_grid(n=12, frame=[t.name])["grid"]
    fit = gauge.silhouette_fit(ref, "FRONT", frame=[t.name])
    checks["scope_forwarded_iou_1"] = fit["iou"] == 1.0 and fit["frame"] == [t.name]
    try:
        gauge.silhouette_fit(ref, "FRONT"); checks["unscoped_refused"] = False
    except ValueError:
        checks["unscoped_refused"] = True
    path = os.path.join(tempfile.gettempdir(), f"bt_life_{_RUN}.jsonl")
    def sc(comp, cid):
        d = {"id": cid, "model": "m", "ts": "t", "config_hash": "h", "coverage": ["fit"],
             "scope": {"frame_face": ["x"], "views": [], "policy": "selected", "algorithm": config.GAUGE_ALGO},
             "components": {"fit": comp}, "composite": comp}
        d["compat"] = gauge.compat_key(d); return d
    try:
        g0 = gauge.gate(sc(0.9, "a"), path)
        checks["no_baseline_is_unverified"] = g0["ok"] is None and g0["status"] == "unverified"
        gauge.log(sc(0.9, "a"), path); gauge.approve("a", path)
        bad = sc(0.1, "b"); g1 = gauge.gate(bad, path); gauge.log(bad, path)   # rejected candidate, logged as history
        g2 = gauge.gate(sc(0.2, "c"), path)
        checks["rejected_not_promoted"] = g1["ok"] is False and g2["ok"] is False and g2["vs_id"] == "a"
    finally:
        try: os.remove(path)
        except OSError: pass
    return {"pass": all(checks.values()), "checks": checks}


def test_measurement_validation():
    """F-P2-7: every public measurement entry point validates the same way."""
    from . import senses
    c = _cube("mv", (0, 2, 0))
    checks = {}
    for label, fn in (("occupancy_missing", lambda: senses.occupancy_grid(n=8, frame=[_n("nope")])),
                      ("occupancy_n_too_big", lambda: senses.occupancy_grid(n=141, frame=[c.name])),
                      ("occupancy_n_too_small", lambda: senses.occupancy_grid(n=2, frame=[c.name])),
                      ("senses_width_out_of_range", lambda: senses.width_at(100.0, frame=[c.name]))):
        try:
            fn(); checks[label] = "accepted (BUG)"
        except ValueError:
            checks[label] = "rejected"
    if hasattr(senses, "grid_diff"):
        try:
            senses.grid_diff({"grid": [[1, 1], [1, 1]], "n": 2}, {"grid": [[1]], "n": 2}); checks["grid_diff_shape"] = "accepted (BUG)"
        except ValueError:
            checks["grid_diff_shape"] = "rejected"
    g = senses.occupancy_grid(n=8, frame=[c.name])["grid"]
    checks["grid_is_square"] = "rejected" if (len(g) == 8 and all(len(r) == 8 for r in g)) else "wrong shape (BUG)"
    return {"pass": all(v == "rejected" for v in checks.values()), "checks": checks}


def test_leaky_vessel_not_verified():
    """F-P2-8: an open-bottom wall over a disconnected floor must not claim containment."""
    from . import senses
    bpy.ops.mesh.primitive_cylinder_add(radius=0.8, depth=2.0, location=(0, 0, 1.0), end_fill_type='NOTHING')
    _adopt("leak_wall")
    bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, -0.1)); _adopt("leak_floor")
    r = senses.cavity_probe(center=(0, 0), rim_radius=0.7, rim_z=2.0, n=8)
    return {"pass": ("holds_liquid" not in r) and r.get("containment") == "not_verified" and r["max_depth"] > 0.3,
            "containment": r.get("containment"), "wall_coverage": r.get("wall_coverage")}


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
              ("stageB_transforms_and_modifiers", test_transforms_and_modifiers),
              ("followup_P1_1_editmode_rejected", test_editmode_rejected),
              ("followup_P1_1_adopt_by_reference", test_adopt_never_takes_active),
              ("followup_P1_2_clear_first_scoped", test_clear_first_scoped),
              ("followup_P1_3_name_collision_refs", test_name_collision_refs),
              ("followup_P1_4_staged_fusion", test_staged_fusion),
              ("followup_P2_5_hash_post_resolve", test_hash_post_resolve),
              ("followup_P2_6_gauge_scope_lifecycle", test_gauge_scope_and_lifecycle),
              ("followup_P2_7_measurement_validation", test_measurement_validation),
              ("followup_P2_8_leaky_vessel", test_leaky_vessel_not_verified))


def run_all(write_report=True):
    """Run calibration + regression tests inside one isolation boundary. Also
    plants decoys named like the OLD conventions (audit P1-1) to prove the suite
    no longer deletes a user's objects by name."""
    import json, os, platform, subprocess, sys, time
    preflight()                                   # BEFORE any operator or decoy (follow-up audit P1-1)
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
        me = d.data
        bpy.data.objects.remove(d, do_unlink=True)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)
    if decoy_coll is not None:
        bpy.data.collections.remove(decoy_coll)
    passed = all(v.get("pass") for v in results.values())
    out = {"passed": passed, "run_id": _RUN,
           "n_tests": len(results), "n_passed": sum(1 for v in results.values() if v.get("pass")),
           "results": results, "scene_integrity": integrity,
           "evidence": _evidence(),
           "not_verified": ["live-scene measurement on a real model (this suite uses known primitives)",
                            "reference fidelity (see gauge.scorecard)",
                            "parented / animated transforms; multi-scene files; Sculpt/Pose modes (only Edit Mode refusal is tested)",
                            "run_isolated() exit/timeout contract (exercised manually, not inside this suite)",
                            "live MCP transport, Metal rendering, fresh-install path (outside this suite's scope)",
                            "vessel containment: cavity_probe reports depth + sampled wall coverage only"]}
    if write_report:
        d = os.path.expanduser(config.CALIBRATION_REPORT_DIR)
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, f"calibration-{out['evidence']['ts'].replace(':', '')}.json")
        with open(path, "w") as f:
            json.dump(out, f, indent=2, default=str)
        out["report_path"] = path
    return out


def _evidence():
    """Machine-readable provenance (follow-up audit packaging section)."""
    import os, platform, subprocess, sys, time
    here = os.path.realpath(os.path.dirname(__file__))
    repo = os.path.dirname(here)
    def git(*a):
        try:
            return subprocess.run(["git", "-C", repo] + list(a), capture_output=True, text=True, timeout=10).stdout.strip()
        except Exception:
            return None
    commit = git("rev-parse", "HEAD")
    dirty = git("status", "--porcelain")
    mod_path = os.path.dirname(__file__)
    return {"package": config.VERSION_STR, "algorithm": config.GAUGE_ALGO,
            "commit": commit, "dirty_tree": (bool(dirty) if dirty is not None else None),
            "blender": bpy.app.version_string, "python": sys.version.split()[0],
            "os": f"{platform.system()} {platform.mac_ver()[0] or platform.release()}", "chip": platform.machine(),
            "headless": bpy.app.background,
            "install_route": {"module_path": mod_path, "realpath": here,
                              "via_symlink": os.path.islink(mod_path) or mod_path != here},
            "state_dir": config.state_dir(), "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}


def run_isolated(timeout=600, blender=None, source=None):
    """Run the suite in a SEPARATE factory-startup Blender (follow-up audit P1-1/P2-9):
    --factory-startup --disable-autoexec --python-exit-code 1, external timeout.
    Returns the parsed result; raises on nonzero exit or timeout."""
    import json, os, subprocess, sys
    blender = blender or bpy.app.binary_path
    source = source or os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    runner = os.path.join(os.path.dirname(os.path.realpath(__file__)), "tests", "run_calibration.py")
    cmd = [blender, "--background", "--factory-startup", "--disable-autoexec", "--python-exit-code", "1",
           "--python", runner, "--", "--source", source]
    env = dict(os.environ); env.setdefault("BLENDERTOOLS_HOME", config.state_dir())
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
    line = next((l for l in proc.stdout.splitlines() if l.startswith("RESULT ")), None)
    if proc.returncode != 0 or line is None:
        raise RuntimeError(f"run_isolated: exit={proc.returncode}\n{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}")
    return json.loads(line[len("RESULT "):])
