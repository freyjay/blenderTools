# blender-connect :: mesh_mind.py -- v0.1 "topology awareness"
"""Part-graph layer: declares which surfaces are CONTINUOUS (one manifold)
and where BREAKS belong. All seeing/making/adjusting routes through this
graph so the four operations share one model."""

import bpy
import bmesh
from mathutils import Vector


def declare_graph():
    """The boy's part ontology. continuity='fuse' groups become ONE mesh;
    'separate' parts must NEVER be swallowed by a fuse."""
    hair = [o.name for o in bpy.data.objects if o.name.startswith(("Hair_", "HairS_", "HairHero_"))]
    return {
        "skin":  {"continuity": "fuse", "members": ["Cranium", "Face", "Jaw", "CheekL", "CheekR",
                                                     "Nose", "LipUp", "EarL", "EarR", "Neck", "JawBlend"]},
        "eyes":  {"continuity": "separate", "members": ["EyeL", "EyeR"]},
        "eye_deco": {"continuity": "separate", "rides_on": "eyes",
                     "members": ["IrisL", "IrisR", "PupilL", "PupilR"]},
        "brows": {"continuity": "separate", "members": ["BrowL", "BrowR"]},
        "hair":  {"continuity": "separate", "layer_overlap_ok": True, "members": hair},
        "cloth": {"continuity": "separate", "members": ["Collar"]},
    }


def _bbox_world(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return (Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))),
            Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))))


def _bbox_overlap(a, b, pad=0.0):
    (amin, amax), (bmin, bmax) = _bbox_world(a), _bbox_world(b)
    for i in range(3):
        if amax[i] + pad < bmin[i] or bmax[i] + pad < amin[i]:
            return False
    return True


def connectivity_check(members):
    """BROAD-PHASE ONLY: pairwise world-AABB overlap graph. Overlapping boxes do NOT
    prove touching surfaces (two unit spheres at distance 2.12 overlap as boxes).
    Use this to find candidates; prove connectivity AFTER fusing with island_census
    (audit P2-9). Returns components (each a list of names)."""
    objs = [bpy.data.objects[m] for m in members if m in bpy.data.objects]
    n = len(objs)
    adj = {i: set() for i in range(n)}
    for i in range(n):
        for j in range(i + 1, n):
            if _bbox_overlap(objs[i], objs[j]):
                adj[i].add(j); adj[j].add(i)
    seen, comps = set(), []
    for i in range(n):
        if i in seen:
            continue
        stack, comp = [i], []
        while stack:
            k = stack.pop()
            if k in seen:
                continue
            seen.add(k); comp.append(objs[k].name)
            stack.extend(adj[k] - seen)
        comps.append(comp)
    return comps


def island_census(obj_name):
    """AFTER fusing: mesh-level truth. Islands must be 1 for a continuous
    surface; non-manifold edge count should be 0 for a clean skin."""
    obj = bpy.data.objects[obj_name]
    deps = bpy.context.evaluated_depsgraph_get()
    me = obj.evaluated_get(deps).to_mesh()
    bm = bmesh.new(); bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    unvisited = set(v.index for v in bm.verts)
    islands = 0
    while unvisited:
        islands += 1
        stack = [bm.verts[next(iter(unvisited))]]
        while stack:
            v = stack.pop()
            if v.index not in unvisited:
                continue
            unvisited.discard(v.index)
            for e in v.link_edges:
                o = e.other_vert(v)
                if o.index in unvisited:
                    stack.append(o)
    nonman = sum(1 for e in bm.edges if len(e.link_faces) not in (1, 2))
    nverts = len(bm.verts)
    bm.free()
    obj.evaluated_get(deps).to_mesh_clear()
    return {"islands": islands, "non_manifold_edges": nonman, "verts": nverts}


def fuse_group(graph, group, voxel=0.05, fused_name=None, owner=None, collection=None):
    """Fuse ONE continuity group via recipes.fuse_objects (STAGED: the prior result
    is only replaced after the new one succeeds -- follow-up audit P1-4).
    Members stay stashed (hidden) for part-level adjustment. Returns the result name."""
    fused_name = fused_name or (group.capitalize() + "Fused")
    spec = graph.get(group)
    if spec is None:
        raise ValueError(f"fuse_group: unknown layer '{group}'")
    if spec.get("continuity") != "fuse":
        raise ValueError(f"fuse_group: layer '{group}' is declared continuity={spec.get('continuity')!r}; refusing")
    wanted = list(spec.get("members", []))
    missing = [m for m in wanted if m not in bpy.data.objects]
    if not wanted or missing:
        raise ValueError(f"fuse_group: members not found: {missing or '(none declared)'}")
    from . import recipes
    f = recipes.fuse_objects([bpy.data.objects[m] for m in wanted], fused_name, voxel=voxel, owner=owner, collection=collection)
    f["bt_owner"] = "fuse"
    return f.name


# audit P2-9: honest alias -- prefer this name
overlap_candidates = connectivity_check
