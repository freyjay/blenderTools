# SPDX-License-Identifier: MIT
"""
blender-connect :: senses.py -- v0.3 "curriculum" senses pack
Five-stage perception upgrade (proportion -> angle -> rotation -> hardness -> parts).

1. proportions()    -- 2D silhouette analysis: width profile, ratios, symmetry
2. contour_angles() -- sub-pixel silhouette tracing, tangent angles, corner count
3. turntable()      -- form metrics at fixed rotation intervals (default 18 deg = 5%)
4. render_hardness()-- sharp-vs-soft perception via normal gradients
5. Doctrine: inspect part by part (every function takes frame=[names]).
"""

import math
import bpy
from mathutils import Vector
from .eye import _basis, _targets, _bounds
from . import cast as _cast

_H_RAMP = " .:-=+*#%@"


def _caster(frame, policy=None):
    """One casting policy for every sense (Stage B). Returns (cast, objs) where
    cast(origin, direction, rebase=True) -> (loc, nrm, name) or None. Frames are
    validated (audit P1-4); origins are depth-rebased unless rebase=False
    (enclosure probes must start INSIDE geometry)."""
    objs = _cast.resolve_frame(frame)
    caster = _cast.Caster(objs, policy=policy)
    if objs is None:
        objs = _targets(None)

    def cast(origin, direction, rebase=True):
        h = caster.cast(origin, direction, rebase=rebase)
        return None if h is None else (h[0], h[1], h[2])
    return cast, objs

def _edge_bisect(cast, forward, right, up_s, v, u_in, u_out, start, iters=7):
    """Sub-pixel silhouette edge: bisect between a hitting u and a missing u."""
    for _ in range(iters):
        um = (u_in + u_out) / 2
        if cast(-forward * start + right * um + up_s * v, forward):
            u_in = um
        else:
            u_out = um
    return (u_in + u_out) / 2


def silhouette(view="RIGHT", frame=None, rows=64):
    """Outer silhouette as sub-pixel (u,v) edge points per row. Returns
    dict with left[], right[] edge arrays (None where empty row)."""
    forward, right, up_s = _basis(view)
    cast, objs = _caster(frame)
    cu, cv, eu, ev = _bounds(objs, right, up_s)
    start = max(eu, ev) * 6 + 20.0
    scan_n = 72
    left, right_e, vs = [], [], []
    for r in range(rows):
        v = cv + ev - (r + 0.5) * (2 * ev / rows)
        us = [cu - eu + (i + 0.5) * (2 * eu / scan_n) for i in range(scan_n)]
        hits = [bool(cast(-forward * start + right * u + up_s * v, forward)) for u in us]
        vs.append(v)
        if not any(hits):
            left.append(None); right_e.append(None)
            continue
        i_first = hits.index(True)
        i_last = len(hits) - 1 - hits[::-1].index(True)
        uL = us[i_first] if i_first == 0 else _edge_bisect(
            cast, forward, right, up_s, v, us[i_first], us[i_first - 1], start)
        uR = us[i_last] if i_last == scan_n - 1 else _edge_bisect(
            cast, forward, right, up_s, v, us[i_last], us[i_last + 1], start)
        left.append(uL); right_e.append(uR)
    return {"v": vs, "left": left, "right": right_e,
            "center_u": cu, "extent": (eu, ev)}


def proportions(view="FRONT", frame=None, rows=64):
    """Stage 1: read the form 2-dimensionally. Width profile + ratios + symmetry."""
    s = silhouette(view, frame, rows)
    widths, mids = [], []
    for L, R in zip(s["left"], s["right"]):
        if L is None:
            widths.append(0.0); mids.append(None)
        else:
            widths.append(R - L); mids.append((R + L) / 2)
    occupied = [i for i, w in enumerate(widths) if w > 0]
    if not occupied:
        return {"empty": True}
    top, bot = occupied[0], occupied[-1]
    H = s["v"][top] - s["v"][bot]
    W = max(widths)
    widest_at = widths.index(W)
    valid_mids = [m for m in mids if m is not None]
    sym_err = (sum(abs(m - s["center_u"]) for m in valid_mids)
               / len(valid_mids)) / (W or 1)
    prof = [round(widths[top + int(k * (bot - top) / 9)] / W, 2) for k in range(10)]
    return {
        "H": round(H, 3), "W": round(W, 3), "W_over_H": round(W / H, 3),
        "widest_at_height_frac": round(1 - (widest_at - top) / max(1, bot - top), 2),
        "symmetry_error": round(sym_err, 3),
        "width_profile_top_to_bottom": prof,
    }


def contour_angles(view="RIGHT", frame=None, rows=64, corner_deg=25.0):
    """Stage 2: tangent angle along each silhouette edge; smoothness + corners."""
    s = silhouette(view, frame, rows)
    out = {}
    for side in ("left", "right"):
        pts = [(u, v) for u, v in zip(s[side], s["v"]) if u is not None]
        if len(pts) < 3:
            out[side] = {"n": len(pts)}
            continue
        angs = [math.degrees(math.atan2(pts[i + 1][1] - pts[i][1],
                                        pts[i + 1][0] - pts[i][0]))
                for i in range(len(pts) - 1)]
        deltas = []
        for a, b in zip(angs, angs[1:]):
            d = (b - a + 180) % 360 - 180
            deltas.append(abs(d))
        out[side] = {
            "n_points": len(pts),
            "mean_turn_deg": round(sum(deltas) / len(deltas), 2),
            "max_turn_deg": round(max(deltas), 1),
            "corners_over_{:g}deg".format(corner_deg):
                sum(1 for d in deltas if d > corner_deg),
        }
    return out


def turntable(step_deg=18.0, frame=None, rows=40):
    """Stage 3: rotate the viewpoint around Z at fixed intervals; track the form."""
    if not (0 < float(step_deg) <= 180.0):
        raise ValueError(f"turntable: step_deg must be in (0, 180], got {step_deg}")
    if int(rows) < 4:
        raise ValueError("turntable: rows must be >= 4")
    table = []
    a = 0.0
    while a < 360.0 - 1e-6:
        r = math.radians(a)
        view = (math.sin(r), math.cos(r), 0.0)
        p = proportions(view, frame, rows)
        table.append({"deg": round(a, 1), "W": p.get("W"), "H": p.get("H"),
                      "widest_frac": p.get("widest_at_height_frac")})
        a += step_deg
    ws = [t["W"] for t in table]
    jumps = [round(abs(b - a), 3) for a, b in zip(ws, ws[1:] + ws[:1])]
    return {"steps": table, "max_W_jump_between_steps": max(jumps),
            "continuity_ok": max(jumps) < 0.35 * max(ws)}


def render_hardness(view="RIGHT", frame=None, width=56, height=None, aspect=0.5):
    """Stage 4: sharp vs soft. Char density = normal gradient (deg) to neighbors;
    silhouette boundary forced hard. Soft curvature reads light, creases dense."""
    forward, right, up_s = _basis(view)
    cast, objs = _caster(frame)
    cu, cv, eu, ev = _bounds(objs, right, up_s)
    if height is None:
        height = max(4, min(56, round(width * (ev / eu) * aspect)))
    start = max(eu, ev) * 6 + 20.0
    du, dv = 2 * eu / width, 2 * ev / height
    grid = []
    for r in range(height):
        v = cv + ev - (r + 0.5) * dv
        row = []
        for c in range(width):
            u = cu - eu + (c + 0.5) * du
            h = cast(-forward * start + right * u + up_s * v, forward)
            row.append(h[1].normalized() if h else None)
        grid.append(row)
    rows_out = []
    for r in range(height):
        line = []
        for c in range(width):
            n = grid[r][c]
            if n is None:
                line.append(" ")
                continue
            worst = 0.0
            boundary = False
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < height and 0 <= cc < width and grid[rr][cc] is not None:
                    ang = math.degrees(n.angle(grid[rr][cc]))
                    worst = max(worst, ang)
                else:
                    boundary = True
            k = len(_H_RAMP) - 1 if boundary else min(
                int(worst / 60.0 * (len(_H_RAMP) - 1)), len(_H_RAMP) - 1)
            line.append(_H_RAMP[k])
        rows_out.append("".join(line))
    header = "[hardness {} | {}x{} | 60deg=full | boundary=@]".format(
        view if isinstance(view, str) else "custom", width, height)
    return chr(10).join([header] + rows_out)


def cavity_probe(center=(0.0, 0.0), rim_radius=0.7, rim_z=2.1, n=14, frame=None):
    """Function-not-form probe: vertical rays down into a vessel.
    Returns holds_liquid, max/mean interior depth below rim, volume held.
    Born from a human audit: a mug modeled solid scored perfectly on every
    surface sense. Surface senses do not see cavities; this one does."""
    deps = bpy.context.evaluated_depsgraph_get()
    scene = bpy.context.scene
    down = Vector((0, 0, -1))
    cast, _ = _caster(frame)
    cell = (2.0 * rim_radius / n) ** 2
    depths = []
    for i in range(n):
        for j in range(n):
            x = center[0] - rim_radius + (i + 0.5) * 2 * rim_radius / n
            y = center[1] - rim_radius + (j + 0.5) * 2 * rim_radius / n
            if (x - center[0]) ** 2 + (y - center[1]) ** 2 > rim_radius ** 2:
                continue
            h = cast(Vector((x, y, rim_z + 5.0)), down)
            if h:
                depths.append(max(0.0, rim_z - h[0].z))
    if not depths:
        return {"holds_liquid": False, "enclosed": False, "max_depth": 0.0, "volume_units3_estimate": 0.0,
                "assumptions": ["no interior surface hit below the rim"]}
    vol = sum(d * cell for d in depths)
    mx = max(depths)
    enc = enclosure_check(center, rim_radius, rim_z, rim_z - mx, frame=frame)
    return {"max_depth": round(mx, 2), "mean_depth": round(sum(depths) / len(depths), 2),
            "volume_units3_estimate": round(vol, 2), "enclosed": enc["enclosed"], "enclosure": enc,
            "holds_liquid": bool(enc["enclosed"] and mx > 0.3),
            "assumptions": ["vertical depth sampling inside the rim circle",
                            "enclosure = radial rays from interior points hit a wall within 1.5x rim radius",
                            "no watertightness, leak-path or units check -- an estimate, not an engineering verdict"]}


def width_bands(view="FRONT", frame=None, z_top=1.10, z_bot=-1.15, bands=10, rows=64):
    """Anatomical-span width curve (crown->chin), normalized to max width.
    Registration matters: never compare curves normalized over different spans."""
    s = silhouette(view, frame, rows)
    out = []
    for k in range(bands):
        z = z_top - (k + 0.5) * (z_top - z_bot) / bands
        best, bw = None, 0.0
        for L, R, v in zip(s["left"], s["right"], s["v"]):
            if L is None:
                continue
            if best is None or abs(v - z) < abs(best - z):
                best, bw = v, R - L
        out.append(bw)
    m = max(out) or 1.0
    return [round(w / m, 3) for w in out]


def occupancy_grid(view="FRONT", n=30, frame=None, center=None, extent=None):
    """n x n occupancy grid. WINDOW LOCK: pass center=/extent= (from a prior
    call's return) to measure in the SAME window across edits. Auto-fit
    re-frames every call, so auto-fit grids from different moments are NOT
    cell-comparable (D1 class: never compare over different spans).
    Returns grid + its window (center, extent, n, view) for reuse."""
    import bpy
    from . import eye
    from mathutils import Vector
    if center is None or extent is None:
        _f, right, up_s = eye._basis(view)
        objs = _targets(frame)
        us, vs = [], []
        for o in objs:
            for c in o.bound_box:
                w = o.matrix_world @ Vector(c)
                us.append(w.dot(right)); vs.append(w.dot(up_s))
        if not us:
            return {"grid": [], "center": (0, 0), "extent": (0, 0),
                    "n": n, "view": view, "locked": False}
        cu, cv = (min(us) + max(us)) / 2, (min(vs) + max(vs)) / 2
        eu, ev = (max(us) - min(us)) / 2 * 1.03, (max(vs) - min(vs)) / 2 * 1.03
        locked = False
    else:
        cu, cv = center
        eu, ev = extent
        locked = True
    from . import eye
    g = eye.render_ascii(view=view, width=n, height=n, mode="id",
                         center=(cu, cv), extent=(eu, ev), frame=frame)
    rows = g.split(chr(10))[2:]
    grid = [[1 if ch != " " else 0 for ch in row] for row in rows if row]
    return {"grid": grid, "center": (round(cu, 4), round(cv, 4)),
            "extent": (round(eu, 4), round(ev, 4)), "n": n, "view": view,
            "locked": locked}


def _row_edges(row):
    idx = [i for i, v in enumerate(row) if v]
    return (idx[0], idx[-1]) if idx else (None, None)


def grid_diff(a, b, tol=1e-6):
    """Cell-exact diff of two occupancy grids IN THE SAME WINDOW. Refuses
    mismatched windows (misregistration is a D1-class error, not a diff).
    Render: '+' added, '-' removed, '#' stable, ' ' empty."""
    if a["n"] != b["n"] or a.get("view") != b.get("view") or \
       any(abs(x - y) > tol for x, y in zip(a["center"], b["center"])) or \
       any(abs(x - y) > tol for x, y in zip(a["extent"], b["extent"])):
        return {"error": "window mismatch -- re-measure with the stored window",
                "a_window": (a["center"], a["extent"], a["n"]),
                "b_window": (b["center"], b["extent"], b["n"])}
    ga, gb = a["grid"], b["grid"]
    added, removed, art, edge_deltas = [], [], [], []
    for r in range(min(len(ga), len(gb))):
        ra, rb = ga[r], gb[r]
        line = []
        for c in range(min(len(ra), len(rb))):
            va, vb = ra[c], rb[c]
            if vb and not va:
                added.append((r, c)); line.append("+")
            elif va and not vb:
                removed.append((r, c)); line.append("-")
            else:
                line.append("#" if va else " ")
        art.append("".join(line))
        ea, eb = _row_edges(ra), _row_edges(rb)
        dl = None if None in (ea[0], eb[0]) else eb[0] - ea[0]
        dr = None if None in (ea[1], eb[1]) else eb[1] - ea[1]
        if dl or dr:
            edge_deltas.append({"row": r, "d_left": dl, "d_right": dr})
    return {"n_added": len(added), "n_removed": len(removed),
            "added": added[:60], "removed": removed[:60],
            "edge_deltas": edge_deltas, "render": art}


def attribute(grid, cells, stash=None, margin=0.02):
    """Post-fuse ownership: which STASHED (hidden) part claims each grid cell.
    Fusion erases ray attribution (ledger finding 3); projected-bbox
    containment on the hidden part stash is the proven diagnostic. Ranked:
    inside-first, then gap distance. z-height alone is a guess -- never again."""
    import bpy
    from . import eye
    from mathutils import Vector
    _f, right, up_s = eye._basis(grid.get("view", "FRONT"))
    if stash is None:
        stash = [o.name for o in bpy.data.objects
                 if o.type == "MESH" and o.hide_get()]
    boxes = {}
    for name in stash:
        o = bpy.data.objects.get(name)
        if not o:
            continue
        us, vs = [], []
        for cbb in o.bound_box:
            w = o.matrix_world @ Vector(cbb)
            us.append(w.dot(right)); vs.append(w.dot(up_s))
        boxes[name] = (min(us), max(us), min(vs), max(vs))
    (cu, cv), (eu, ev), n = grid["center"], grid["extent"], grid["n"]
    out = []
    for (r, c) in cells:
        u = cu - eu + (c + 0.5) * (2 * eu / n)
        v = cv + ev - (r + 0.5) * (2 * ev / n)
        cands = []
        for name, (u0, u1, v0, v1) in boxes.items():
            inside = (u0 - margin <= u <= u1 + margin) and \
                     (v0 - margin <= v <= v1 + margin)
            du = max(u0 - u, u - u1, 0.0)
            dv = max(v0 - v, v - v1, 0.0)
            d = (du * du + dv * dv) ** 0.5
            if inside or d < 0.15:
                cands.append((0 if inside else 1, round(d, 4), name))
        cands.sort()
        out.append({"cell": (r, c), "u": round(u, 3), "v": round(v, 3),
                    "owners": [{"part": nm, "inside": fl == 0, "gap": d}
                               for fl, d, nm in cands[:4]]})
    return out


def clean_heights(exclude, z_lo=-1.15, z_hi=1.10, steps=48, margin=0.02):
    """Ruler-contamination guard (ledger finding 4): measurement heights whose
    z lies OUTSIDE every excluded part's world z-span. Recommends the midpoint
    of the widest clean run."""
    import bpy
    from mathutils import Vector
    spans = []
    for name in exclude:
        o = bpy.data.objects.get(name)
        if not o:
            continue
        zs = [(o.matrix_world @ Vector(c)).z for c in o.bound_box]
        spans.append((min(zs) - margin, max(zs) + margin))
    zs_clean, runs, cur = [], [], []
    for k in range(steps):
        z = z_lo + (k + 0.5) * (z_hi - z_lo) / steps
        if any(a <= z <= b for a, b in spans):
            if cur:
                runs.append(cur)
            cur = []
        else:
            zs_clean.append(round(z, 3)); cur.append(z)
    if cur:
        runs.append(cur)
    best = max(runs, key=len) if runs else []
    rec = round(best[len(best) // 2], 3) if best else None
    return {"clean": zs_clean, "recommended": rec,
            "excluded_spans": [(round(a, 3), round(b, 3)) for a, b in spans]}


def width_at(z, view="FRONT", frame=None, rows=96):
    """Silhouette width at the row nearest z (sub-pixel edges). Pair with
    clean_heights() before using as a ratio denominator."""
    s = silhouette(view, frame, rows)
    best, bw, bv = None, None, None
    for L, R, v in zip(s["left"], s["right"], s["v"]):
        if L is None:
            continue
        if best is None or abs(v - z) < best:
            best, bw, bv = abs(v - z), R - L, v
    return {"z_requested": z,
            "z_measured": round(bv, 4) if bv is not None else None,
            "width": round(bw, 4) if bw is not None else None}


def perception_floor(view="FRONT", frame=None, n=30, trials=4):
    """Empirical noise floor: re-sample the SAME window with sub-cell grid
    offsets and report edge wobble with ZERO model change. A distinction at
    or below the floor is instrument noise, not evidence. This makes the
    masterwork exit criterion computable."""
    base = occupancy_grid(view=view, n=n, frame=frame)
    (cu, cv), (eu, ev) = base["center"], base["extent"]
    cell = 2 * eu / n
    e0 = [_row_edges(r) for r in base["grid"]]
    max_wobble = 0
    for t in range(1, trials + 1):
        f = t / (trials + 1.0) - 0.5
        g = occupancy_grid(view=view, n=n, frame=frame,
                           center=(cu + f * cell, cv + f * cell),
                           extent=(eu, ev))
        for (a0, b0), (a1, b1) in zip(e0, [_row_edges(r) for r in g["grid"]]):
            for x0, x1 in ((a0, a1), (b0, b1)):
                if x0 is not None and x1 is not None:
                    max_wobble = max(max_wobble, abs(x1 - x0))
    wb0 = width_bands(view=view, frame=frame)
    wb1 = width_bands(view=view, frame=frame, rows=71)
    wb_floor = max(abs(x - y) for x, y in zip(wb0, wb1))
    return {"occupancy_edge_floor_cells": max_wobble,
            "cell_world_units": round(cell, 4),
            "width_band_floor": round(wb_floor, 3),
            "note": "distinction <= floor is inside instrument noise"}


def enclosure_check(center=(0.0, 0.0), rim_radius=0.7, rim_z=2.1, floor_z=0.2, frame=None, n_dirs=16, levels=3):
    """Are there WALLS? From interior points at several heights between floor and
    rim, cast rays radially outward; each must hit a surface within 1.5 x rim_radius.
    A flat plane under a rim height has depth but no enclosure (audit P2-12)."""
    cast, _ = _caster(frame)
    escapes, hits = [], 0
    for k in range(levels):
        z = floor_z + (rim_z - floor_z) * (k + 0.5) / levels
        for i in range(n_dirs):
            a = 2 * math.pi * i / n_dirs
            d = Vector((math.cos(a), math.sin(a), 0.0))
            h = cast(Vector((center[0], center[1], z)), d, rebase=False)   # must start inside
            if h and (h[0] - Vector((center[0], center[1], z))).length <= 1.5 * rim_radius:
                hits += 1
            else:
                escapes.append({"z": round(z, 3), "deg": round(math.degrees(a), 1)})
    total = n_dirs * levels
    return {"enclosed": not escapes, "wall_hits": hits, "rays": total, "escapes": escapes[:8],
            "escape_fraction": round(len(escapes) / total, 3)}
