"""plan.py -- data before code.

A model should exist as a SPEC before it exists as geometry. This module makes
that true: a plan is a JSON-serializable dict of parts (shape, transform,
layer, detail gate), resolved against parameters, hashed, then built. Any
version of any model can be rebuilt from its plan file instead of from prose.

Adopted from the Astra Blender Studio study (plan/build split, ast-whitelisted
expressions) and fused with our part graph: every part belongs to a layer with
a continuity contract, so a plan is also a mesh_mind graph.

    p = plan.new("boy_v4", detail=3)
    plan.add_part(p, "Cranium", "skin", "sphere", location=(0,-0.02,0.15), scale=(0.93,1.14,0.97))
    plan.add_part(p, "EyeL", "eyes", "sphere", location=("eye_x", -0.72, -0.02), scale=(0.23,0.20,0.23))
    p["parameters"] = {"eye_x": {"default": 0.385, "min": 0.2, "max": 0.6}}
    r = plan.resolve(p)                     # expressions evaluated, detail gate applied, sha256 attached
    plan.save(r, "~/Developer/blenderTools/plans/boy_v4.json")
    report = plan.build(r, clear_first=True)  # geometry + build report (provenance)

Capturing an existing scene: plan.capture("boy_v3", layers=mesh_mind.declare_graph())
"""

import ast
import hashlib
import json
import math
import operator
import os
import platform
import re
import time

from . import config

SCHEMA = 1
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
_IDENT = re.compile(r"^[A-Za-z][A-Za-z0-9_\-]{0,63}$")
SHAPES = ("sphere", "cube", "cylinder", "cone", "torus")


# ------------------------------------------------------------ expressions ----
def _num(v, lo=-1e4, hi=1e4):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not lo <= v <= hi:
        raise ValueError(f"expected finite number in {lo}..{hi}: {v!r}")
    return float(v)


def expression(value, variables):
    """Numbers, parameter names, + - * / and parentheses. Nothing else. No eval."""
    if not isinstance(value, str):
        return _num(value)
    if len(value) > 160:
        raise ValueError("expression too long")
    tree = ast.parse(value, mode="eval")
    if len(list(ast.walk(tree))) > 64:
        raise ValueError("expression too complex")
    def visit(n):
        if isinstance(n, ast.Constant):
            return _num(n.value)
        if isinstance(n, ast.Name) and n.id in variables:
            return _num(variables[n.id])
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
            return _num(visit(n.operand) * (-1 if isinstance(n.op, ast.USub) else 1))
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            return _num(_OPS[type(n.op)](visit(n.left), visit(n.right)))
        raise ValueError("only numbers, parameter names, + - * / and parentheses are allowed")
    return visit(tree.body)


# ------------------------------------------------------------------ plans ----
def new(model_id, detail=None, notes=""):
    detail = detail or config.DEFAULT_DETAIL
    if detail not in config.DETAIL_PROFILES:
        raise ValueError(f"detail must be one of {sorted(config.DETAIL_PROFILES)}")
    return {"schema": SCHEMA, "model": model_id, "detail": detail, "notes": notes,
            "package": config.VERSION_STR, "parameters": {}, "layers": {}, "parts": []}


def add_layer(p, name, continuity="separate", **extra):
    if continuity not in ("fuse", "separate"):
        raise ValueError("continuity must be 'fuse' or 'separate'")
    p["layers"][name] = {"continuity": continuity, **extra}


def add_part(p, name, layer, shape, location=(0, 0, 0), scale=(1, 1, 1), rotation=(0, 0, 0),
             color=None, min_detail=1, max_detail=5, segments=None, **shape_args):
    if not _IDENT.match(name):
        raise ValueError(f"bad part name: {name}")
    if shape not in SHAPES:
        raise ValueError(f"shape must be one of {SHAPES}")
    if layer not in p["layers"]:
        add_layer(p, layer)
    if not (1 <= min_detail <= max_detail <= 5):
        raise ValueError("detail gate must satisfy 1 <= min <= max <= 5")
    if any(pt["name"] == name for pt in p["parts"]):
        raise ValueError(f"duplicate part identifier: {name} (follow-up audit P1-3)")
    p["parts"].append({"name": name, "layer": layer, "shape": shape,
                       "location": list(location), "scale": list(scale), "rotation": list(rotation),
                       "color": list(color) if color else None, "min_detail": min_detail,
                       "max_detail": max_detail, "segments": segments, "shape_args": shape_args})
    return p


def resolve(p, parameters=None):
    """Evaluate expressions, apply the detail gate, attach a content hash.
    The hash covers the RESOLVED geometry spec -- two plans that build the
    same thing hash the same."""
    specs = p.get("parameters", {})
    supplied = dict(parameters or {})
    if set(supplied) - set(specs):
        raise ValueError(f"unknown parameters: {sorted(set(supplied) - set(specs))}")
    values = {}
    for k, spec in specs.items():
        values[k] = _num(supplied.get(k, spec["default"]), spec.get("min", -1e4), spec.get("max", 1e4))
    values["detail"] = p["detail"]
    prof = config.DETAIL_PROFILES[p["detail"]]
    parts = []
    for part in p["parts"]:
        if not part["min_detail"] <= p["detail"] <= part["max_detail"]:
            continue
        vec = lambda seq: [expression(x, values) for x in seq]
        parts.append({**part, "location": vec(part["location"]), "scale": vec(part["scale"]),
                      "rotation": vec(part["rotation"]),
                      "segments": part["segments"] or prof["segments"]})
    if not parts:
        raise ValueError("plan resolves to no parts at this detail level")
    import copy
    sealed = copy.deepcopy(prof)          # no aliasing of mutable config (follow-up audit P2-5)
    resolved = {**copy.deepcopy(p), "parts": parts, "resolved_parameters": values, "profile": sealed,
                "build_options": {"voxel": sealed["voxel"], "segments": sealed["segments"]}}
    resolved["sha256"] = _hash(resolved)
    return resolved


def _hash(resolved):
    """Content hash over everything that affects geometry: parts, layers, detail,
    AND the profile/build options (audit P2-10 -- voxel size changed the result
    but not the hash)."""
    body = json.dumps({"parts": resolved["parts"], "layers": resolved["layers"], "detail": resolved["detail"],
                       "build_options": resolved["build_options"], "profile": resolved.get("profile"),
                       "schema": SCHEMA}, sort_keys=True)
    return hashlib.sha256(body.encode()).hexdigest()


def verify(resolved):
    """Recompute and compare the hash. build() refuses a plan that fails this."""
    return resolved.get("sha256") == _hash(resolved)


def save(p, path):
    path = os.path.expanduser(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(p, f, indent=2, allow_nan=False)
    return path


def load(path):
    with open(os.path.expanduser(path)) as f:
        p = json.load(f)
    if p.get("schema") != SCHEMA:
        raise ValueError(f"unsupported plan schema: {p.get('schema')}")
    return p


# ------------------------------------------------------------------ build ----
def build(resolved, clear_first=False, fuse=True, collection=None, on_collision="error", fused_name_fmt="{model}__{layer}Fused"):
    """Turn a RESOLVED plan into geometry. Returns a build report (provenance).

    Ownership (follow-up audit P1-2/P1-3): every created object is tagged with
    the model id and a unique build id; created objects are tracked by
    REFERENCE, so a name Blender suffixes ("Cranium.001") is still fused
    correctly. clear_first removes only objects tagged with THIS model id.
    on_collision: "error" (default) refuses requested names that already exist;
    "suffix" accepts Blender's renaming and records the actual names."""
    import uuid
    import bpy
    from mathutils import Vector
    if "sha256" not in resolved:
        raise ValueError("build() needs a resolved plan -- call resolve() first")
    if not verify(resolved):
        raise ValueError("build(): plan hash does not match its content -- plan was edited after resolve()")
    _act = bpy.context.view_layer.objects.active if bpy.context.view_layer else None
    if _act is not None and _act.mode != "OBJECT":
        raise RuntimeError("build(): Blender must be in Object Mode")
    model = resolved["model"]
    build_id = uuid.uuid4().hex[:10]
    opts = resolved["build_options"]                 # the ONLY config the builder consumes
    voxel, seg_default = float(opts["voxel"]), int(opts["segments"])
    if clear_first:
        for o in [o for o in bpy.data.objects if o.type == "MESH" and o.get("bt_model") == model]:
            bpy.data.objects.remove(o, do_unlink=True)
    names_requested = [pt["name"] for pt in resolved["parts"]]
    if len(set(names_requested)) != len(names_requested):
        raise ValueError("build(): duplicate part identifiers in resolved plan")
    if on_collision == "error":
        clash = [n for n in names_requested if n in bpy.data.objects]
        if clash:
            raise ValueError(f"build(): names already exist in the scene: {clash} -- use clear_first=True "
                             "(scoped to this model) or on_collision='suffix'")
    target_coll = None
    if collection:
        target_coll = bpy.data.collections.get(collection) or bpy.data.collections.new(collection)
        if target_coll.name not in bpy.context.scene.collection.children:
            bpy.context.scene.collection.children.link(target_coll)
    created = {}                                      # requested name -> Object reference
    for part in resolved["parts"]:
        seg = int(part["segments"] or seg_default); loc = part["location"]; sa = part["shape_args"]; shp = part["shape"]
        before = {o.as_pointer() for o in bpy.data.objects}
        if shp == "sphere":
            bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=loc, segments=seg, ring_count=max(6, seg // 2))
        elif shp == "cube":
            bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
        elif shp == "cylinder":
            bpy.ops.mesh.primitive_cylinder_add(radius=sa.get("radius", 1), depth=sa.get("depth", 1), location=loc, vertices=seg)
        elif shp == "cone":
            bpy.ops.mesh.primitive_cone_add(vertices=sa.get("vertices", seg), radius1=sa.get("radius1", 1),
                                            radius2=sa.get("radius2", 0), depth=sa.get("depth", 1), location=loc)
        elif shp == "torus":
            bpy.ops.mesh.primitive_torus_add(major_radius=sa.get("major_radius", 1), minor_radius=sa.get("minor_radius", 0.25),
                                             location=loc, major_segments=seg, minor_segments=max(8, seg // 2))
        new_objs = [o for o in bpy.data.objects if o.as_pointer() not in before]
        if len(new_objs) != 1:
            raise RuntimeError(f"build(): expected exactly one new object for {part['name']}, got {len(new_objs)}")
        o = new_objs[0]                               # ownership by created reference, never by active_object
        o.name = part["name"]
        o.scale = part["scale"]
        o.rotation_euler = [math.radians(a) for a in part["rotation"]]
        if part["color"]:
            o.color = part["color"]
        o["bt_plan_sha256"] = resolved["sha256"]; o["bt_model"] = model; o["bt_build"] = build_id
        o["bt_layer"] = part["layer"]; o["bt_detail"] = resolved["detail"]; o["bt_shape"] = shp
        if target_coll is not None:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            target_coll.objects.link(o)
        bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
        bpy.ops.object.shade_smooth()
        created[part["name"]] = o
    fused = {}
    if fuse:
        from . import mesh_mind, recipes
        for lname, spec in resolved["layers"].items():
            if spec.get("continuity") == "fuse":
                members = [created[pt["name"]] for pt in resolved["parts"] if pt["layer"] == lname]
                if members:
                    f = recipes.fuse_objects(members, fused_name_fmt.format(model=model, layer=lname), voxel=voxel,
                                             owner=model, collection=collection)
                    f["bt_model"] = model; f["bt_build"] = build_id; f["bt_plan_sha256"] = resolved["sha256"]
                    fused[lname] = {"name": f.name, **mesh_mind.island_census(f.name)}
    # provenance report: THIS build's objects only (follow-up audit P1-3)
    deps = bpy.context.evaluated_depsgraph_get()
    mine = [o for o in bpy.data.objects if o.type == "MESH" and o.get("bt_build") == build_id and not o.hide_get()]
    verts = faces = 0; pts = []
    for o in mine:
        me = o.evaluated_get(deps).to_mesh()
        verts += len(me.vertices); faces += len(me.polygons)
        pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
        o.evaluated_get(deps).to_mesh_clear()
    lo = [round(min(pt[i] for pt in pts), 4) for i in range(3)] if pts else None
    hi = [round(max(pt[i] for pt in pts), 4) for i in range(3)] if pts else None
    return {"model": model, "build_id": build_id, "plan_sha256": resolved["sha256"], "detail": resolved["detail"],
            "build_options_used": {**opts, "fuse": bool(fuse), "collection": collection, "on_collision": on_collision},
            "package": config.VERSION_STR, "blender": bpy.app.version_string,
            "platform": platform.system(), "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "parts_built": len(created), "actual_names": {k: v.name for k, v in created.items()},
            "fused_layers": fused, "visible_verts": verts, "visible_faces": faces, "bounds": [lo, hi]}


# ---------------------------------------------------------------- capture ----
def capture(model_id, layers, detail=None, notes="captured from live scene (APPROXIMATE: transforms exact, shape/materials/modifiers not)"):
    """Reverse direction: turn what is IN the scene into a plan, using a
    mesh_mind graph ({layer: {"continuity":..., "members":[...]}}) to assign
    parts to layers. Shape is recorded as 'sphere' unless the object carries a
    bt_shape custom property -- capture records transforms faithfully, geometry
    type approximately. Fused objects are skipped (their parts are the truth)."""
    import bpy
    p = new(model_id, detail, notes)
    for lname, spec in layers.items():
        add_layer(p, lname, spec.get("continuity", "separate"))
        for name in spec.get("members", []):
            o = bpy.data.objects.get(name)
            if not o or o.type != "MESH" or name.endswith("Fused"):
                continue
            add_part(p, name, lname, o.get("bt_shape", "sphere"),
                     location=[round(v, 4) for v in o.location], scale=[round(v, 4) for v in o.scale],
                     rotation=[round(math.degrees(a), 3) for a in o.rotation_euler],
                     color=[round(c, 3) for c in o.color])
    return p
