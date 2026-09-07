"""Reusable build recipes -- the things I kept retyping every session, as
parameterized functions. Each encodes a lesson from the ledger.
"""

import math
import random

import bpy
from mathutils import Matrix, Vector

from . import config


# ------------------------------------------------------------- primitives ----
def sphere(name, loc, scale, color=(0.92, 0.89, 0.85, 1), segs=24):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=loc, segments=segs, ring_count=segs // 2)
    o = bpy.context.active_object
    o.name, o.scale, o.color = name, scale, color
    bpy.ops.object.shade_smooth()
    return o


# ------------------------------------------------------------------ fusion ----
def _valid_voxel(v):
    return isinstance(v, (int, float)) and math.isfinite(v) and 0.005 <= v <= 2.0


def _link_to(obj, collection):
    if collection is None:
        return
    coll = bpy.data.collections.get(collection) or bpy.data.collections.new(collection)
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)


def fuse_objects(sources, out_name, voxel=None, owner=None, collection=None, color=None):
    """STAGED fusion (follow-up audit P1-4). Order of operations:
      1. validate everything (types, voxel, identities, prior-result ownership)
      2. build the replacement under a staging name -- the old result is untouched
      3. only after remesh succeeds: remove the OLD result, rename staging, hide sources
    Any failure after step 1 deletes the staging object and leaves the scene as it was.
    `owner` is a per-model token: a prior result with a different owner is never replaced."""
    voxel = voxel or config.VOXEL_FINE
    if not _valid_voxel(voxel):
        raise ValueError(f"fuse_objects: voxel must be finite in [0.005, 2.0], got {voxel!r}")
    if not sources:
        raise ValueError("fuse_objects: no sources")
    bad = [o.name for o in sources if getattr(o, "type", None) != "MESH"]
    if bad:
        raise ValueError(f"fuse_objects: non-mesh sources {bad}")
    if any(o.name == out_name for o in sources):
        raise ValueError("fuse_objects: result name collides with a source")
    prior = bpy.data.objects.get(out_name)
    if prior is not None:
        if prior.get("bt_owner") not in ("fuse", "mesh_mind"):
            raise ValueError(f"fuse_objects: '{out_name}' exists and is not a fuse result -- refusing to overwrite")
        if owner is not None and prior.get("bt_model") not in (None, owner):
            raise ValueError(f"fuse_objects: '{out_name}' belongs to model {prior.get('bt_model')!r}, not {owner!r}")
    staging_name = out_name + ".__staging"
    if staging_name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[staging_name], do_unlink=True)
    # remember state to restore on failure
    sel = [o.name for o in bpy.context.selected_objects]
    active = bpy.context.view_layer.objects.active
    dups, staged = [], None
    try:
        bpy.ops.object.select_all(action='DESELECT')
        for o in sources:
            d = o.copy(); d.data = o.data.copy()
            bpy.context.collection.objects.link(d)
            d.hide_set(False); d.hide_render = False; d.hide_viewport = False
            d.select_set(True); dups.append(d)
        bpy.context.view_layer.objects.active = dups[0]
        bpy.ops.object.join()
        staged = bpy.context.active_object
        staged.name = staging_name
        dups = []   # consumed by join
        rm = staged.modifiers.new("Remesh", 'REMESH')
        rm.mode, rm.voxel_size = 'VOXEL', voxel
        bpy.ops.object.modifier_apply(modifier="Remesh")
        if len(staged.data.polygons) == 0:
            raise RuntimeError("remesh produced an empty mesh")
        bpy.ops.object.shade_smooth()
    except Exception:
        for d in dups:
            bpy.data.objects.remove(d, do_unlink=True)
        if staged is not None:
            bpy.data.objects.remove(staged, do_unlink=True)
        bpy.ops.object.select_all(action='DESELECT')
        for n in sel:
            o = bpy.data.objects.get(n)
            if o: o.select_set(True)
        bpy.context.view_layer.objects.active = active
        raise
    # ---- commit: only now is the prior result touched
    if prior is not None:
        bpy.data.objects.remove(prior, do_unlink=True)
    staged.name = out_name
    staged.hide_set(False); staged.hide_render = False; staged.hide_viewport = False
    staged["bt_owner"] = "fuse"
    staged["bt_fused_from"] = ",".join(o.name for o in sources)
    if owner is not None:
        staged["bt_model"] = owner
    if color:
        staged.color = color
    else:
        staged.color = sources[0].color[:]
    _link_to(staged, collection)
    for o in sources:
        o.hide_set(True); o.hide_render = True
    return staged


def voxel_fuse(part_names, out_name, voxel=None, color=None, owner=None, collection=None):
    """Name-based convenience wrapper over fuse_objects. Resolves names to
    objects FIRST (missing or non-mesh names raise before anything mutates)."""
    missing = [n for n in part_names if n not in bpy.data.objects]
    if missing or not part_names:
        raise ValueError(f"voxel_fuse: unknown parts {missing or '(none given)'}")
    return fuse_objects([bpy.data.objects[n] for n in part_names], out_name, voxel=voxel,
                        owner=owner, collection=collection, color=color)


def quadriflow(obj, target_faces=None, symmetry=True, preserve_sharp=False, seed=0):
    """Voxel soup -> quads. Requires manifold input (voxel_fuse guarantees it).
    AutoLow's trick: if the vertex count doesn't change, QuadriFlow silently
    failed -- voxel-remesh and retry once."""
    target_faces = target_faces or config.QUADRIFLOW_FACES
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    before = len(obj.data.vertices)
    # Enumerate, don't guess: the symmetry flag was renamed across versions
    # (use_paint_symmetry -> use_mesh_symmetry). Pass only what THIS Blender has.
    props = {p.identifier for p in bpy.ops.object.quadriflow_remesh.get_rna_type().properties}
    kw = {"mode": 'FACES', "target_faces": target_faces, "seed": seed}
    for cand in ("use_mesh_symmetry", "use_paint_symmetry"):
        if cand in props:
            kw[cand] = symmetry
            break
    if "use_preserve_sharp" in props:
        kw["use_preserve_sharp"] = preserve_sharp
    # Known bpy crash (#124004) on very dense input: coarsen first rather than crash.
    if len(obj.data.polygons) > config.QUADRIFLOW_MAX_INPUT_FACES:
        rm = obj.modifiers.new("Remesh", 'REMESH')
        rm.mode, rm.voxel_size = 'VOXEL', config.VOXEL_COARSE
        bpy.ops.object.modifier_apply(modifier="Remesh")
    bpy.ops.object.quadriflow_remesh(**kw)
    if len(obj.data.vertices) == before:
        rm = obj.modifiers.new("Remesh", 'REMESH')
        rm.mode, rm.voxel_size = 'VOXEL', config.VOXEL_FINE
        bpy.ops.object.modifier_apply(modifier="Remesh")
        bpy.ops.object.quadriflow_remesh(**kw)
    quads = sum(1 for p in obj.data.polygons if len(p.vertices) == 4)
    return {"verts_before": before, "verts_after": len(obj.data.vertices),
            "quads": quads, "faces": len(obj.data.polygons),
            "quad_fraction": round(quads / max(1, len(obj.data.polygons)), 3)}


# ------------------------------------------------------------------- hair ----
def _lying_matrix(d, gflow):
    flow = gflow - d * gflow.dot(d)
    if flow.length < 0.05:
        flow = Vector((0, 1, 0)) - d * d.y
    xa = flow.normalized(); za = d
    ya = za.cross(xa).normalized(); xa = ya.cross(za).normalized()
    return Matrix(((xa.x, ya.x, za.x, 0), (xa.y, ya.y, za.y, 0), (xa.z, ya.z, za.z, 0), (0, 0, 0, 1)))


def default_include(d, H=None):
    """Crown + back + temple band. The temple band is what v1/v2 forgot."""
    H = H or config.HAIR
    tb = H["temple_band"]
    if d.z > 0.55:
        return True
    if d.y > 0.10 and d.z > -0.55:
        return True
    return abs(d.y) <= tb["y_abs_max"] and tb["z_min"] < d.z < tb["z_max"] and abs(d.x) > tb["x_abs_min"]


def hair_pods(n=80, seed=7, include=default_include, prefix="Hair_", color=(0.38, 0.30, 0.34, 1)):
    """Lying-mode pods on a golden-spiral scalp sampling, flow field back-swept,
    continuous height taper (no flat plateau). Returns count."""
    H = config.HAIR
    rnd = random.Random(seed)
    center = Vector(H["scalp_center"])
    golden = math.pi * (3 - math.sqrt(5))
    made = 0
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        rr = math.sqrt(max(0.0, 1 - z * z))
        d = Vector((rr * math.cos(golden * i), rr * math.sin(golden * i), z)).normalized()
        if not include(d):
            continue
        upc = H["upc_front"] - H["upc_slope"] * max(0.0, d.y)
        taper = 0.6 + 0.5 * max(0.0, (d.z + 0.3) / 1.3)
        boost = taper * (1.35 if (d.y < -0.1 and d.z > 0.5) else 1.0)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=16, ring_count=8)
        p = bpy.context.active_object
        p.name = f"{prefix}{made:02d}"
        p.matrix_world = Matrix.Translation(center + d * H["scalp_radius"]) @ _lying_matrix(d, Vector((0, H["flow_back"], upc)))
        p.scale = ((H["pod_len"] + rnd.uniform(-0.04, 0.10)) * boost,
                   (H["pod_wid"] + rnd.uniform(-0.02, 0.03)) * boost,
                   (H["pod_thick"] + rnd.uniform(-0.02, 0.02)) * boost)
        p.color = (color[0] + rnd.uniform(-0.03, 0.03), color[1], color[2] + rnd.uniform(-0.03, 0.03), 1)
        bpy.ops.object.shade_smooth()
        made += 1
    return made


def hero_spikes(specs=None, prefix="HairHero_", color=(0.36, 0.29, 0.33, 1)):
    """STANDING-mode pods: long axis along outward normal + lean. Tangent
    projection annihilates 'up' at the crown -- two vetoes proved no lying-mode
    flow can make a spike. specs: [(direction, length, bias_vec), ...]"""
    H = config.HAIR
    center = Vector(H["scalp_center"])
    specs = specs or [
        (Vector((-0.16, -0.42, 0.90)), 0.72, Vector(H["hero_standing_bias"])),
        (Vector((0.20, -0.35, 0.93)), 0.62, Vector((-0.10, -0.55, 0.42))),
        (Vector((-0.36, -0.30, 0.88)), 0.55, Vector((-0.15, -0.48, 0.38))),
    ]
    for i, (d0, L, bias) in enumerate(specs):
        d = d0.normalized()
        q = Vector((1, 0, 0)).rotation_difference((d + bias).normalized())
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=16, ring_count=8)
        p = bpy.context.active_object
        p.name = f"{prefix}{i}"
        p.matrix_world = Matrix.Translation(center + d * 0.90) @ q.to_matrix().to_4x4()
        p.scale, p.color = (L, 0.19, 0.13), color
        bpy.ops.object.shade_smooth()
    return len(specs)
