# SPDX-License-Identifier: MIT
"""
blender-connect :: eye.py -- v0.2 "elite"
Text-based vision for AI agents driving Blender over MCP.

v0.2: fixed basis handedness (v0.1 rendered 180-deg rotated -- caught by
calibration rig), arbitrary view directions, aspect-true auto-framing,
edge mode, normal-shading mode (curvature perception), optional 2x2
supersampling, cross-section slicer.
"""

import bpy
from mathutils import Vector

_VIEWS = {
    "FRONT":  Vector((0, 1, 0)),
    "BACK":   Vector((0, -1, 0)),
    "RIGHT":  Vector((-1, 0, 0)),
    "LEFT":   Vector((1, 0, 0)),
    "TOP":    Vector((0, 0, -1)),
    "BOTTOM": Vector((0, 0, 1)),
}

_SHADE_RAMP = " .:-=+*#%@"   # dark -> bright (facing viewer)
_DEPTH_RAMP = "@%#*+=-:. "   # near -> far
_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def _basis(view):
    """Return (forward, right, up_screen) -- right-handed, verified v0.2."""
    if isinstance(view, str):
        forward = _VIEWS[view.upper()].copy()
    else:
        forward = Vector(view).normalized()
    up_hint = Vector((0, 1, 0)) if abs(forward.z) > 0.99 else Vector((0, 0, 1))
    right = forward.cross(up_hint).normalized()
    up_s = right.cross(forward).normalized()
    return forward, right, up_s


def _targets(frame):
    objs = [o for o in bpy.context.visible_objects if o.type == "MESH"]
    if frame:
        wanted = set(frame)
        objs = [o for o in objs if o.name in wanted]
    return objs


def _bounds(objs, right, up_s):
    us, vs = [], []
    for obj in objs:
        for corner in obj.bound_box:
            w = obj.matrix_world @ Vector(corner)
            us.append(w.dot(right))
            vs.append(w.dot(up_s))
    if not us:
        return 0.0, 0.0, 5.0, 5.0
    cu, cv = (min(us) + max(us)) / 2, (min(vs) + max(vs)) / 2
    eu = max((max(us) - min(us)) / 2, 0.05) * 1.12
    ev = max((max(vs) - min(vs)) / 2, 0.05) * 1.12
    return cu, cv, eu, ev


def render_ascii(view="FRONT", width=72, height=None, mode="id",
                 frame=None, aspect=0.5, aa=False, center=None, extent=None):
    """
    Orthographic character render of the scene.

    view   -- FRONT/BACK/RIGHT/LEFT/TOP/BOTTOM or an (x,y,z) direction
    mode   -- "id" | "edges" | "depth" | "shade"
              id:    letter per object (+legend)
              edges: silhouette boundaries UPPERCASE, interior lowercase
              depth: distance gradient (near=dense)
              shade: normal-facing gradient -- reveals curvature/form
    frame  -- optional list of object names to frame (default: all meshes)
    aspect -- character cell width/height ratio (~0.5 for terminals)
    aa     -- 2x2 supersampling (4x rays, smoother silhouettes)
    height -- auto-computed aspect-true from extents when None
    """
    forward, right, up_s = _basis(view)
    objs = _targets(frame)
    cu, cv, eu, ev = _bounds(objs, right, up_s)
    if center is not None:
        cu, cv = center
    if extent is not None:
        eu, ev = extent
    if height is None:
        height = max(4, min(60, round(width * (ev / eu) * aspect)))
    width = min(width, 140)

    deps = bpy.context.evaluated_depsgraph_get()
    scene = bpy.context.scene
    start = max(eu, ev) * 6 + 20.0

    letters = {o.name: _ALPHABET[i % len(_ALPHABET)] for i, o in enumerate(objs)}
    limit_names = set(letters) if frame else None

    offs = [(-0.25, -0.25), (0.25, -0.25), (-0.25, 0.25), (0.25, 0.25)] if aa else [(0.0, 0.0)]

    def cast(u, v):
        origin = -forward * start + right * u + up_s * v
        hit, loc, nrm, _i, obj, _m = scene.ray_cast(deps, origin, forward)
        if not hit or (limit_names and obj.name not in limit_names):
            return None
        return (letters.get(obj.name, "?"), (loc - origin).length, nrm)

    du, dv = 2 * eu / width, 2 * ev / height
    grid = []
    for r in range(height):
        v0 = cv + ev - (r + 0.5) * dv
        row = []
        for c in range(width):
            u0 = cu - eu + (c + 0.5) * du
            samples = [cast(u0 + ou * du, v0 + ov * dv) for ou, ov in offs]
            hits = [s for s in samples if s]
            if not hits:
                row.append(None)
            else:
                # majority letter; averaged depth & normal
                counts = {}
                for h in hits:
                    counts[h[0]] = counts.get(h[0], 0) + 1
                letter = max(counts, key=counts.get)
                d = sum(h[1] for h in hits) / len(hits)
                n = sum((h[2] for h in hits), Vector()) / len(hits)
                row.append((letter, d, n))
        grid.append(row)

    def at(r, c):
        if 0 <= r < height and 0 <= c < width and grid[r][c]:
            return grid[r][c][0]
        return None

    if mode == "depth":
        ds = [cell[1] for row in grid for cell in row if cell]
        dmin, dspan = (min(ds), (max(ds) - min(ds)) or 1.0) if ds else (0, 1)
        rows = ["".join(" " if not cell else _DEPTH_RAMP[
            min(int((cell[1] - dmin) / dspan * (len(_DEPTH_RAMP) - 2)),
                len(_DEPTH_RAMP) - 2)] for cell in row) for row in grid]
    elif mode == "shade":
        rows = []
        for row in grid:
            line = []
            for cell in row:
                if not cell:
                    line.append(" ")
                else:
                    b = max(0.0, cell[2].normalized().dot(-forward))
                    line.append(_SHADE_RAMP[min(int(b * (len(_SHADE_RAMP) - 1)),
                                                len(_SHADE_RAMP) - 1)])
            rows.append("".join(line))
    elif mode == "edges":
        rows = []
        for r in range(height):
            line = []
            for c in range(width):
                cell = grid[r][c]
                if not cell:
                    line.append(" ")
                    continue
                me = cell[0]
                edge = any(at(r + dr, c + dc) != me
                           for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                line.append(me.upper() if edge else me.lower())
            rows.append("".join(line))
    else:  # id
        rows = ["".join(cell[0] if cell else " " for cell in row) for row in grid]

    header = "[{} | {}x{} | u:[{:.2f},{:.2f}] v:[{:.2f},{:.2f}] | {:.3f} u/char{}]".format(
        view if isinstance(view, str) else tuple(round(x, 2) for x in view),
        width, height, cu - eu, cu + eu, cv - ev, cv + ev, du, " | AA" if aa else "")
    legend = "  ".join("{}={}".format(l, n) for n, l in
                       sorted(letters.items(), key=lambda x: x[1]))
    parts = [header]
    if mode in ("id", "edges"):
        parts.append(legend)
    return chr(10).join(parts + rows)


def scanline(view="FRONT", axis_value=0.0, lo=-2.0, hi=2.0, step=0.1):
    """1-D probe along the screen-up axis at horizontal position axis_value."""
    forward, right, up_s = _basis(view)
    deps = bpy.context.evaluated_depsgraph_get()
    scene = bpy.context.scene
    out, v = [], lo
    while v <= hi + 1e-9:
        origin = -forward * 50.0 + right * axis_value + up_s * v
        hit, loc, _n, _i, obj, _m = scene.ray_cast(deps, origin, forward)
        out.append((round(v, 3), obj.name if hit else None,
                    round((loc - origin).length, 3) if hit else None))
        v += step
    return out


def cross_section(object_name, plane_co=(0, 0, 0), plane_no=(0, 0, 1),
                  max_points=200):
    """
    Slice a mesh with a plane; return the intersection as 2D points
    (in-plane coordinates) plus edge pairs. Math-native orthographic slice.
    """
    import bmesh
    obj = bpy.data.objects[object_name]
    deps = bpy.context.evaluated_depsgraph_get()
    mesh = obj.evaluated_get(deps).to_mesh()

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.transform(obj.matrix_world)
    co, no = Vector(plane_co), Vector(plane_no).normalized()
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
                                 plane_co=co, plane_no=no,
                                 clear_inner=True, clear_outer=True)
    cut_verts = [g for g in res["geom_cut"] if isinstance(g, bmesh.types.BMVert)]
    cut_edges = [g for g in res["geom_cut"] if isinstance(g, bmesh.types.BMEdge)]

    # In-plane 2D basis
    helper = Vector((0, 1, 0)) if abs(no.z) > 0.99 else Vector((0, 0, 1))
    ax_u = no.cross(helper).normalized()
    ax_v = no.cross(ax_u).normalized()

    idx = {v: i for i, v in enumerate(cut_verts)}
    pts = [(round((v.co - co).dot(ax_u), 4), round((v.co - co).dot(ax_v), 4))
           for v in cut_verts][:max_points]
    edges = [(idx[e.verts[0]], idx[e.verts[1]]) for e in cut_edges
             if e.verts[0] in idx and e.verts[1] in idx][:max_points]
    bm.free()
    obj.evaluated_get(deps).to_mesh_clear()
    return {"points_2d": pts, "edges": edges,
            "n_points": len(pts), "plane_co": tuple(co), "plane_no": tuple(no)}
