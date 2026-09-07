"""cast.py -- the ONE casting policy (Stage B, audit P2-6 / P2-7a).

Before this module, `eye` stopped at the first unselected hit and `senses`
peeled through occluders with an 8-bounce cap, so occupancy and silhouette
disagreed about the same scene. Both now cast through a Caster with an
explicitly named policy:

  policy="selected"  Rays hit ONLY the selected objects, via per-object BVH
                     trees built from the evaluated (modifier-applied) mesh in
                     world space. Occluders are invisible. This is "full
                     projection of the selected objects" -- what silhouette,
                     proportions, occupancy and hardness mean.
  policy="visible"   Scene ray_cast, first hit wins; with a frame, a hit that
                     belongs to something else counts as a miss. This is
                     "what a camera would see" -- for ownership checks and
                     visible-occupancy questions.

Ray ORIGINS are rebased to the target's depth bounds along the ray direction
(audit P2-7a): the lateral position is kept, the depth is moved behind the
nearest surface. A subject at y=-100 is measured exactly like one at y=2.
Rebasing is opt-out (`rebase=False`) for rays that must start INSIDE geometry,
e.g. enclosure probes.
"""

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

PAD = 1.0


class Caster:
    def __init__(self, objs=None, policy=None):
        """objs: list of Objects (the frame) or None for the whole visible scene."""
        self.deps = bpy.context.evaluated_depsgraph_get()
        self.scene = bpy.context.scene
        scene_pool = [o for o in self.scene.objects if o.type == "MESH" and not o.hide_get()]
        if objs is None:
            objs_pool = scene_pool
            self.names = None
            self.policy = policy or "visible"
        else:
            objs_pool = list(objs)
            self.names = {o.name for o in objs_pool}
            self.policy = policy or "selected"
        if self.policy not in ("selected", "visible"):
            raise ValueError("policy must be 'selected' or 'visible'")
        # Depth bounds from world bbox corners. For 'visible' the pool is the WHOLE
        # scene: a rebased origin must sit behind every possible occluder, or it
        # would start inside/behind one and silently miss it.
        corner_pool = scene_pool if self.policy == "visible" else objs_pool
        self.corners = [o.matrix_world @ Vector(c) for o in corner_pool for c in o.bound_box]
        self.trees = []
        if self.policy == "selected":
            for o in objs_pool:
                ev = o.evaluated_get(self.deps)
                me = ev.to_mesh()
                try:
                    if len(me.polygons) == 0:
                        continue
                    mw = o.matrix_world
                    verts = [mw @ v.co for v in me.vertices]
                    polys = [tuple(p.vertices) for p in me.polygons]
                    self.trees.append((o.name, BVHTree.FromPolygons(verts, polys)))
                finally:
                    ev.to_mesh_clear()

    # ------------------------------------------------------------------
    def depth_range(self, direction):
        d = Vector(direction).normalized()
        if not self.corners:
            return -50.0, 50.0
        vals = [c.dot(d) for c in self.corners]
        return min(vals), max(vals)

    def rebase(self, origin, direction):
        """Keep lateral position; move depth to just behind the nearest surface."""
        d = Vector(direction).normalized()
        o = Vector(origin)
        lateral = o - d * o.dot(d)
        dmin, _ = self.depth_range(d)
        return lateral + d * (dmin - PAD)

    def cast(self, origin, direction, rebase=True):
        """-> (location, normal, owner_name, distance_from_origin) or None."""
        d = Vector(direction).normalized()
        o = self.rebase(origin, d) if rebase else Vector(origin)
        dmin, dmax = self.depth_range(d)
        maxd = (dmax - dmin) + 2 * PAD + 1.0 if rebase else 1e4
        if self.policy == "selected":
            best = None
            for name, tree in self.trees:
                loc, nrm, _idx, dist = tree.ray_cast(o, d, maxd)
                if loc is not None and (best is None or dist < best[3]):
                    best = (loc, nrm, name, dist)
            return best
        hit, loc, nrm, _i, obj, _m = self.scene.ray_cast(self.deps, o, d, distance=maxd)
        if not hit or (self.names is not None and obj.name not in self.names):
            return None
        return (loc, nrm, obj.name, (loc - o).length)


def resolve_frame(frame):
    """Names -> visible mesh Objects, or raise. An unresolved frame must never
    silently become 'the whole scene' (audit P1-4). Returns None for frame=None."""
    if frame is None:
        return None
    requested = list(frame)
    if not requested:
        raise ValueError("frame is empty -- pass None to mean the whole scene")
    objs, missing = [], []
    for n in requested:
        o = bpy.data.objects.get(n)
        if o is None or o.type != "MESH" or o.hide_get():
            missing.append(n)
        else:
            objs.append(o)
    if missing:
        raise ValueError(f"frame names not found or not visible: {missing}")
    return objs
