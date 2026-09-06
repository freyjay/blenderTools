"""Gauges: turn a finished model into numbers that can be tracked across
versions, so "is v4 better than v3?" is a lookup, not an opinion.

    sc = gauge.scorecard("boy_v3", frame_face=["SkinFused","EarL","EarR"],
                         canon=config.CANON_BOY, heights=config.MEASURE_HEIGHTS_BOY,
                         ref_grid_front=my_digitized_grid)
    gauge.log(sc)                 # appends to gauge_log.jsonl
    gauge.compare_to_last(sc)     # deltas vs previous entry, flags regressions

Every gauge returns its raw inputs alongside its score, so a number can be
audited back to what was actually measured.
"""

import json
import math
import os
import time

import bpy
import bmesh
from mathutils import Vector

from . import config, measure

LOG_PATH = os.path.expanduser(config.GAUGE_LOG)


# ---------------------------------------------------------- reference fit ----
def reference_fit(frame_face, canon, heights, eye_name="EyeL", iris_name="IrisL",
                  lip_name="LipUp", ear_name="EarL", skin_name="SkinFused"):
    """Ratio scorecard vs canon. Reports the contributors inside each ruler so
    a contaminated denominator is visible, not silent."""
    O = bpy.data.objects
    W, W_parts = measure.width_at(heights["eye_level"], frame_face)
    cheek, _ = measure.width_at(heights["cheek"], frame_face)
    jaw, _ = measure.width_at(heights["jaw"], frame_face)
    neck, _ = measure.width_at(heights["neck"], frame_face)
    r = {}
    if eye_name in O:
        r["eye_span_over_W"] = measure.ratio(2 * abs(O[eye_name].location.x), W, "eye_span_over_W", canon.get("eye_span_over_W"))
    if iris_name in O:
        r["iris_over_W"] = measure.ratio(2 * O[iris_name].scale.x, W, "iris_over_W", canon.get("iris_over_W"))
    if lip_name in O:
        r["mouth_over_W"] = measure.ratio(2 * O[lip_name].scale.x, W, "mouth_over_W", canon.get("mouth_over_W"))
    r["jaw_over_cheek"] = measure.ratio(jaw, cheek, "jaw_over_cheek", canon.get("jaw_over_cheek"))
    r["neck_over_W"] = measure.ratio(neck, W, "neck_over_W", canon.get("neck_over_W"))
    if skin_name in O:
        x0, x1, y0, y1, z0, z1 = measure.bbox_world(O[skin_name])
        r["skull_D_over_H"] = measure.ratio(y1 - y0, measure.head_height(), "skull_D_over_H", canon.get("skull_D_over_H"))
    n = len(r); passed = sum(1 for v in r.values() if v.get("pass"))
    worst = max(r.values(), key=lambda v: v.get("diff", 0))
    return {"score": round(passed / n, 3) if n else None, "passed": passed, "n": n,
            "worst": (worst["name"], worst.get("diff")), "ratios": r,
            "W": round(W, 4), "W_contributors": W_parts}


# ------------------------------------------------------- silhouette (IoU) ----
def spans_to_grid(spans, n=None):
    """[(left,right) or None] per row -> n x n occupancy grid. This is how a
    hand-digitized reference photo becomes comparable to occupancy_grid()."""
    n = n or config.OCCUPANCY_N
    g = []
    for s in spans:
        row = [0] * n
        if s:
            for c in range(max(0, s[0]), min(n - 1, s[1]) + 1):
                row[c] = 1
        g.append(row)
    return g


def iou(grid_a, grid_b):
    """Jaccard overlap of two same-size occupancy grids + per-row error."""
    inter = union = 0
    rows = []
    for ra, rb in zip(grid_a, grid_b):
        i = sum(1 for a, b in zip(ra, rb) if a and b)
        u = sum(1 for a, b in zip(ra, rb) if a or b)
        inter += i; union += u
        rows.append(u - i)   # cells in disagreement on this row
    return {"iou": round(inter / union, 4) if union else None,
            "disagree_cells": union - inter, "row_disagreement": rows,
            "worst_rows": sorted(range(len(rows)), key=lambda k: -rows[k])[:5]}


def silhouette_fit(ref_grid, view="FRONT", frame=None):
    from . import senses
    g = senses.occupancy_grid(view=view, n=len(ref_grid), frame=frame)
    out = iou(g["grid"], ref_grid)
    out.update({"view": view, "window": (g["center"], g["extent"])})
    return out


# --------------------------------------------------------------- surface ----
def surface(frame, views=("FRONT", "RIGHT", "TOP"), n=40):
    """Whole-surface hardness distribution: mean/p95/max neighbor-normal angle,
    fraction of hard cells. A smoothness gauge that a seam can't hide from."""
    from . import eye, senses
    angs = []
    for view in views:
        forward, right, up_s = eye._basis(view)
        objs = [bpy.data.objects[nm] for nm in frame if nm in bpy.data.objects]
        cu, cv, eu, ev = eye._bounds(objs, right, up_s)
        cast, _ = senses._caster(frame)
        grid = []
        for rr in range(n):
            v = cv + ev - (rr + 0.5) * (2 * ev / n)
            grid.append([(cast(-forward * 40.0 + right * (cu - eu + (c + 0.5) * (2 * eu / n)) + up_s * v, forward) or (None, None, None))[1] for c in range(n)])
        for rr in range(n):
            for c in range(n):
                a = grid[rr][c]
                if a is None:
                    continue
                for dr, dc in ((1, 0), (0, 1)):
                    r2, c2 = rr + dr, c + dc
                    if r2 < n and c2 < n and grid[r2][c2] is not None:
                        angs.append(math.degrees(a.normalized().angle(grid[r2][c2].normalized())))
    if not angs:
        return {"score": None}
    angs.sort()
    p95 = angs[int(0.95 * (len(angs) - 1))]
    hard = sum(1 for a in angs if a > config.HARD_DEG) / len(angs)
    return {"score": round(1.0 - hard, 4), "mean_deg": round(sum(angs) / len(angs), 2),
            "p95_deg": round(p95, 1), "max_deg": round(angs[-1], 1),
            "hard_fraction": round(hard, 4), "samples": len(angs)}


# -------------------------------------------------------------- topology ----
def topology(obj_name):
    """Tri/quad/ngon mix, manifoldness, islands, pole valence, sliver edges.
    Directly answers the 'bad topology, barely modified primitives' critique."""
    obj = bpy.data.objects[obj_name]
    deps = bpy.context.evaluated_depsgraph_get()
    me = obj.evaluated_get(deps).to_mesh()
    bm = bmesh.new(); bm.from_mesh(me)
    faces = len(bm.faces)
    tris = sum(1 for f in bm.faces if len(f.verts) == 3)
    quads = sum(1 for f in bm.faces if len(f.verts) == 4)
    ngons = faces - tris - quads
    nonman = sum(1 for e in bm.edges if len(e.link_faces) not in (1, 2))
    boundary = sum(1 for e in bm.edges if len(e.link_faces) == 1)
    valence = {}
    for v in bm.verts:
        k = min(len(v.link_edges), 7)
        valence[k] = valence.get(k, 0) + 1
    lengths = [e.calc_length() for e in bm.edges] or [0.0]
    mean_len = sum(lengths) / len(lengths)
    slivers = sum(1 for L in lengths if L < 0.05 * mean_len)
    # islands
    bm.verts.ensure_lookup_table()
    unvisited = set(v.index for v in bm.verts); islands = 0
    while unvisited:
        islands += 1
        stack = [bm.verts[next(iter(unvisited))]]
        while stack:
            v = stack.pop()
            if v.index not in unvisited:
                continue
            unvisited.discard(v.index)
            stack.extend(o for e in v.link_edges for o in [e.other_vert(v)] if o.index in unvisited)
    bm.free(); obj.evaluated_get(deps).to_mesh_clear()
    quad_frac = quads / faces if faces else 0.0
    clean = (nonman == 0 and islands == 1)
    score = round(quad_frac * (1.0 if clean else 0.5), 4)
    return {"score": score, "faces": faces, "tris": tris, "quads": quads, "ngons": ngons,
            "quad_fraction": round(quad_frac, 4), "non_manifold_edges": nonman,
            "boundary_edges": boundary, "islands": islands,
            "valence_hist": dict(sorted(valence.items())), "sliver_edges": slivers,
            "mean_edge_len": round(mean_len, 4)}


# ---------------------------------------------------------------- symmetry ----
def symmetry(frame, view="FRONT", rows=48):
    """Mirror error of the silhouette about u=0 (heads should be ~0; hair
    intentionally isn't -- gauge them separately)."""
    from . import senses
    s = senses.silhouette(view, frame=frame, rows=rows)
    errs, widths = [], []
    for L, R in zip(s["left"], s["right"]):
        if L is None:
            continue
        errs.append(abs(-L - R)); widths.append(R - L)
    if not errs:
        return {"score": None}
    W = max(widths)
    e = (sum(errs) / len(errs)) / W
    return {"score": round(1.0 - min(1.0, e), 4), "mean_mirror_error_over_W": round(e, 4)}


# --------------------------------------------------------------- ownership ----
def ownership(expectations):
    """[(x, z, expected_owner), ...] -> fraction of probes owned as declared."""
    hits = []
    for x, z, exp in expectations:
        owner, _ = measure.owner_at(x, -10.0, z)
        hits.append({"x": x, "z": z, "expected": exp, "got": owner, "ok": owner == exp})
    ok = sum(1 for h in hits if h["ok"])
    return {"score": round(ok / len(hits), 3) if hits else None, "probes": hits}


# --------------------------------------------------------------- scorecard ----
def scorecard(model_id, frame_face, canon=None, heights=None, ref_grid_front=None,
              ref_grid_side=None, skin_name="SkinFused", ownership_probes=None, notes=""):
    canon = canon or config.CANON_BOY
    heights = heights or config.MEASURE_HEIGHTS_BOY
    sc = {"model": model_id, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
          "blender": bpy.app.version_string, "pkg": config.VERSION_STR, "notes": notes}
    sc["fit"] = reference_fit(frame_face, canon, heights, skin_name=skin_name)
    if ref_grid_front:
        sc["silhouette_front"] = silhouette_fit(ref_grid_front, "FRONT")
    if ref_grid_side:
        sc["silhouette_side"] = silhouette_fit(ref_grid_side, "RIGHT")
    sc["surface"] = surface(frame_face)
    if skin_name in bpy.data.objects:
        sc["topology"] = topology(skin_name)
    sc["symmetry"] = symmetry(frame_face)
    if ownership_probes:
        sc["ownership"] = ownership(ownership_probes)
    # composite: transparent weights from config
    w = config.GAUGE_WEIGHTS
    parts = {"fit": sc["fit"]["score"], "surface": sc["surface"].get("score"),
             "topology": sc.get("topology", {}).get("score"), "symmetry": sc["symmetry"].get("score"),
             "silhouette": (sc.get("silhouette_front") or {}).get("iou")}
    num = sum(w[k] * v for k, v in parts.items() if v is not None)
    den = sum(w[k] for k, v in parts.items() if v is not None)
    sc["composite"] = round(num / den, 4) if den else None
    sc["components"] = parts
    return sc


def log(sc, path=None):
    path = path or LOG_PATH
    with open(path, "a") as f:
        f.write(json.dumps(sc, default=str) + "\n")
    return path


def history(path=None):
    path = path or LOG_PATH
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def compare_to_last(sc, path=None):
    """Deltas vs the previous logged scorecard; anything that dropped is a regression."""
    hist = history(path)
    if not hist:
        return {"first_entry": True}
    prev = hist[-1]
    deltas, regressions = {}, []
    for k, v in sc["components"].items():
        pv = prev.get("components", {}).get(k)
        if v is not None and pv is not None:
            d = round(v - pv, 4); deltas[k] = d
            if d < -0.005:
                regressions.append(k)
    return {"vs": prev["model"], "composite_delta": round((sc["composite"] or 0) - (prev["composite"] or 0), 4),
            "deltas": deltas, "regressions": regressions}
