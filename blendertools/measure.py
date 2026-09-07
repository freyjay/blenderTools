"""Measurement primitives with the session's failure modes designed out.

Every measurement bug this project hit had the same shape: a ruler that
silently included something it shouldn't (ears in the face width, hair in the
skull probe, a neck in the head height). These helpers make the contents of
the ruler explicit and refuse to guess.
"""

import bpy
from mathutils import Vector

from . import config


# ----------------------------------------------------------------- bisect ----
def edge_bisect(hit_fn, x_hit, x_miss, iters=16):
    """Bisection with the invariant ENFORCED: hit_fn(x_hit) must be True and
    hit_fn(x_miss) must be False. The ground-truth torus test caught a version
    of this with the arguments swapped -- it converged inside the wrong region
    and raised nothing. Now it raises."""
    if not hit_fn(x_hit):
        raise ValueError(f"edge_bisect: x_hit={x_hit} is not a hit")
    if hit_fn(x_miss):
        raise ValueError(f"edge_bisect: x_miss={x_miss} is not a miss")
    for _ in range(iters):
        xm = (x_hit + x_miss) / 2
        if hit_fn(xm):
            x_hit = xm
        else:
            x_miss = xm
    return (x_hit + x_miss) / 2


# ------------------------------------------------------------ attribution ----
def bbox_world(obj):
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    return (min(p.x for p in pts), max(p.x for p in pts),
            min(p.y for p in pts), max(p.y for p in pts),
            min(p.z for p in pts), max(p.z for p in pts))


def parts_at_height(z, names=None, include_hidden=False):
    """Every mesh object whose world z-span contains z. This is what is
    actually inside a horizontal ruler at that height. Run it BEFORE trusting
    any width_at() -- it would have flagged the ear inside the 'face width'."""
    out = []
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        if names and o.name not in names:
            continue
        if not include_hidden and o.hide_get():
            continue
        x0, x1, y0, y1, z0, z1 = bbox_world(o)
        if z0 <= z <= z1:
            out.append(o.name)
    return out


def attribute_point(x, z, candidate_names):
    """Post-fusion attribution. Ray-cast can only say 'SkinFused'; this says
    which STASHED (hidden) part's bbox contains the point. Guessing from
    z-height alone caused a real regression -- use this instead."""
    hits = []
    for nm in candidate_names:
        o = bpy.data.objects.get(nm)
        if not o:
            continue
        x0, x1, y0, y1, z0, z1 = bbox_world(o)
        if x0 <= x <= x1 and z0 <= z <= z1:
            hits.append(nm)
    return hits


# ---------------------------------------------------------------- width -----
def width_at(z, frame, view="FRONT", rows=56):
    """Silhouette width at height z. `frame` is REQUIRED -- an unnamed ruler is
    the bug. Returns (width, contributors) where contributors is the list of
    frame objects whose z-span actually contains z, so you can see what you
    measured."""
    if not frame:
        raise ValueError("width_at: frame must name the objects being measured")
    from . import senses
    s = senses.silhouette(view, frame=frame, rows=rows)
    vs = s["v"]
    spacing = abs(vs[1] - vs[0]) if len(vs) > 1 else float("inf")
    best, bw = None, 0.0
    for L, R, v in zip(s["left"], s["right"], vs):
        if L is None:
            continue
        if best is None or abs(v - z) < abs(best - z):
            best, bw = v, R - L
    if best is None:
        raise ValueError("width_at: no occupied rows in this frame")
    if abs(best - z) > spacing:   # nearest occupied row is not at the requested height (audit P2-7)
        raise ValueError(f"width_at: z={z} is outside the occupied range; nearest occupied row is z={best:.3f}")
    info = {"contributors": parts_at_height(z, names=frame, include_hidden=True),
            "requested_z": z, "sampled_z": round(best, 4), "row_spacing": round(spacing, 4), "frame": list(frame)}
    return bw, info


def ratio(num, den, name="", canon=None):
    """A ratio that remembers what it is. `canon` optional -> pass/fail."""
    val = num / den if den else float("nan")
    out = {"name": name, "value": round(val, 4)}
    if canon is not None:
        out["canon"] = canon
        out["diff"] = round(abs(val - canon), 4)
        out["pass"] = out["diff"] <= config.TOL["ratio_pass"]
    return out


def head_height(parts=("Cranium", "Face", "Jaw")):
    """Crown->chin from the named skull parts. NOT the fused bbox -- that once
    included the neck and manufactured a false skull-depth alarm."""
    zs = []
    for nm in parts:
        o = bpy.data.objects.get(nm)
        if not o:
            continue
        _, _, _, _, z0, z1 = bbox_world(o)
        zs += [z0, z1]
    return (max(zs) - min(zs)) if zs else 0.0


# ---------------------------------------------------------------- probes ----
def owner_at(x, y_start, z, direction=(0, 1, 0)):
    """Which object a ray hits first. For 'does this layer own its surface' checks."""
    deps = bpy.context.evaluated_depsgraph_get()
    hit, loc, n, i, obj, m = bpy.context.scene.ray_cast(deps, Vector((x, y_start, z)), Vector(direction))
    return (obj.name, loc) if hit else (None, None)
