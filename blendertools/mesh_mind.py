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
    """BEFORE fusing: prove the group is one connected component via
    pairwise overlap graph. Returns components (each a list of names)."""
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


def fuse_group(graph, group, voxel=0.05, fused_name=None):
    """Fuse ONE continuity group only; everything else untouched.
    Members stay stashed (hidden) for future part-level adjustment."""
    fused_name = fused_name or (group.capitalize() + "Fused")
    if fused_name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[fused_name], do_unlink=True)
    members = [bpy.data.objects[m] for m in graph[group]["members"] if m in bpy.data.objects]
    bpy.ops.object.select_all(action='DESELECT')
    dups = []
    for o in members:
        d = o.copy(); d.data = o.data.copy()
        bpy.context.collection.objects.link(d)
        d.hide_set(False); d.select_set(True); dups.append(d)
    bpy.context.view_layer.objects.active = dups[0]
    bpy.ops.object.join()
    f = bpy.context.active_object; f.name = fused_name
    rm = f.modifiers.new("Remesh", 'REMESH')
    rm.mode = 'VOXEL'; rm.voxel_size = voxel
    bpy.ops.object.modifier_apply(modifier="Remesh")
    bpy.ops.object.shade_smooth()
    try:
        f.color = members[0].color[:]
    except Exception:
        pass
    for o in members:
        o.hide_set(True); o.hide_render = True
    return fused_name
