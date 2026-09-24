"""Gamespace ship exporter: validates a ship in Blender and exports FBX files for Unreal.

Use it three ways:

* Add-on: Edit > Preferences > Add-ons > Install from Disk... > this file. Then View3D sidebar
  (N) > "Gamespace" tab: Validate / Center on collision / Export.
* Script: open it in Blender's Text Editor and Run Script; the same sidebar panel appears.
* Command line (no UI):
      blender -b Ship.blend --python Tools/Blender/gamespace_ship_export.py -- --out "//Export" [--validate-only] [--force]
* Manifest check without Blender (before importing into Unreal):
      python Tools/Blender/gamespace_ship_export.py --check-manifest ArtSource/Ships/<Ship>/Export/<Ship>_manifest.json

Conventions (details in Docs/Ships/ShipPipeline.md):

    SM_Ship_<Ship>                 main hull, LOD0            -> SM_Ship_<Ship>.fbx
    SM_Ship_<Ship>_<Part>          extra part, e.g. _Canopy   -> SM_Ship_<Ship>_<Part>.fbx
    SM_Ship_<Ship>[_<Part>]_LOD<n> reduced LOD, n = 1..9      -> own .fbx, imported as LOD n in Unreal
    UCX_<MeshName>_<NN>            convex collision hull for <MeshName> (also UBX_ box, USP_ sphere, UCP_ capsule)
    SOCKET_<Name>                  empty parented to a mesh  -> Unreal static mesh socket

Everything else in the file (HIGH_ reference meshes, lights, cameras) is ignored.

Blender is right-handed Z-up in metres; Unreal is left-handed Z-up in centimetres. With the
settings below a ship modelled with its nose along Blender +X and top along +Z arrives in Unreal
with the nose along +X (the pawn's forward), the same size in real units, and Blender +Y mapped
to Unreal -Y. The manifest written next to the FBX files records sizes and socket positions in
both systems so the first import can be checked against it.

The validation core below does not import bpy, so it can be unit-tested with plain Python
(Tools/Blender/tests/test_ship_export_core.py).
"""

bl_info = {
    "name": "Gamespace Ship Export",
    "author": "gamespace",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Gamespace",
    "description": "Validate ship meshes (naming, transforms, collision, sockets) and export FBX for Unreal",
    "category": "Import-Export",
}

import json
import math
import os
import re
import sys

try:
    import bpy
    import bmesh
except ImportError:  # plain Python: only the core below is usable
    bpy = None
    bmesh = None


# =========================================================================================
# Core: pure Python, no bpy
# =========================================================================================

# Budgets. The player ship is seen up close all the time, so it gets a generous budget.
LIMITS = {
    "lod0_tris_warn": 300_000,        # above this, only reasonable with Nanite
    "lod0_tris_error": 1_000_000,     # AI raw output territory: decimate first
    "lod0_tris_non_nanite": 80_000,   # budget if Nanite is off
    "lod_reduction_warn": 0.6,        # each LOD should have at most 60 % of the previous one's triangles
    "hull_verts_warn": 32,
    "hull_verts_error": 255,
    "hulls_warn": 16,
    "materials_warn": 6,
    "length_min_m": 4.0,
    "length_max_m": 80.0,
    "pivot_offset_warn": 0.10,        # of the ship length
    "collision_overhang_warn": 0.05,  # of the ship length
}

RECOMMENDED_SOCKETS = ("Cockpit",)
RECOMMENDED_SOCKET_PREFIXES = ("Engine",)

NAME_PART = r"[A-Z][A-Za-z0-9]*"
RENDER_RE = re.compile(r"^SM_Ship_(?P<ship>%s)(?:_(?P<part>(?!LOD\d)%s))?(?:_LOD(?P<lod>[1-9]))?$" % (NAME_PART, NAME_PART))
COLLISION_RE = re.compile(r"^(?P<kind>UCX|UBX|USP|UCP)_(?P<mesh>SM_Ship_[A-Za-z0-9_]+?)_(?P<index>\d{2})$")
SOCKET_RE = re.compile(r"^SOCKET_(?P<socket>[A-Za-z0-9_]+)$")
MATERIAL_RE = re.compile(r"^(M|MI)_[A-Za-z0-9_]+$")
BLENDER_DUPLICATE_RE = re.compile(r"\.\d{3}$")
MANAGED_PREFIXES = ("SM_", "UCX_", "UBX_", "USP_", "UCP_", "SOCKET_")

ERROR, WARN, INFO = "ERROR", "WARN", "INFO"


def issue(level, message, obj=None):
    return {"level": level, "object": obj, "message": message}


def bounds_union(boxes):
    boxes = [b for b in boxes if b]
    if not boxes:
        return None
    return ([min(b[0][i] for b in boxes) for i in range(3)], [max(b[1][i] for b in boxes) for i in range(3)])


def bounds_size(box):
    return [box[1][i] - box[0][i] for i in range(3)]


def bounds_center(box):
    return [(box[0][i] + box[1][i]) * 0.5 for i in range(3)]


def blender_to_unreal_cm(v):
    """Blender metres (right-handed) to Unreal centimetres (left-handed): Y flips."""
    return [round(v[0] * 100.0, 2), round(-v[1] * 100.0, 2), round(v[2] * 100.0, 2)]


def classify(records):
    """Sorts object records into render meshes, collision hulls, sockets and ignored names.

    A record is a dict: name, type ('MESH' / 'EMPTY' / ...), parent, and for meshes the stats
    gathered by gather_records (see there).
    """
    result = {"render": {}, "collision": {}, "sockets": {}, "ignored": [], "unknown": []}
    for r in records:
        name = r["name"]
        if not name.startswith(MANAGED_PREFIXES):
            result["ignored"].append(name)
            continue
        m = RENDER_RE.match(name)
        if m and r["type"] == "MESH":
            result["render"][name] = dict(r, ship=m.group("ship"), part=m.group("part"), lod=int(m.group("lod") or 0),
                                          base=name if not m.group("lod") else name[: name.rindex("_LOD")])
            continue
        m = COLLISION_RE.match(name)
        if m and r["type"] == "MESH":
            result["collision"][name] = dict(r, kind=m.group("kind"), mesh=m.group("mesh"), index=int(m.group("index")))
            continue
        m = SOCKET_RE.match(name)
        if m and r["type"] == "EMPTY":
            result["sockets"][name] = dict(r, socket=m.group("socket"))
            continue
        result["unknown"].append(name)
    return result


def _transform_issues(r, what):
    out = []
    scale = r.get("scale", (1, 1, 1))
    if any(s < 0 for s in scale):
        out.append(issue(ERROR, "%s has a negative scale (mirrored): apply it (Ctrl+A > Scale) and recalculate normals" % what, r["name"]))
    elif any(abs(s - 1.0) > 1e-4 for s in scale):
        out.append(issue(ERROR, "%s scale is %s, not 1: apply it (Ctrl+A > Scale)" % (what, _fmt(scale)), r["name"]))
    if any(abs(a) > 1e-4 for a in r.get("rotation", (0, 0, 0))):
        out.append(issue(ERROR, "%s is rotated: apply rotation (Ctrl+A > Rotation)" % what, r["name"]))
    if any(abs(c) > 1e-4 for c in r.get("location", (0, 0, 0))) and r.get("parent") is None:
        out.append(issue(WARN, "%s origin is not at the world origin: apply location (Ctrl+A > Location); "
                               "Unreal uses the world origin as the pivot" % what, r["name"]))
    return out


def _fmt(v):
    return "(" + ", ".join("%.3g" % x for x in v) + ")"


def validate(records, scene, limits=LIMITS):
    """Returns (issues, classified). scene: dict with unit_system, scale_length."""
    issues = []
    c = classify(records)

    if scene.get("unit_system") != "METRIC" or abs(scene.get("scale_length", 1.0) - 1.0) > 1e-6:
        issues.append(issue(ERROR, "Scene units must be Metric with Unit Scale 1.0 (1 Blender unit = 1 m); now %s, scale %s"
                            % (scene.get("unit_system"), scene.get("scale_length"))))

    for name in c["unknown"]:
        hint = " (Blender added a .001 suffix: rename it)" if BLENDER_DUPLICATE_RE.search(name) else ""
        issues.append(issue(ERROR, "Name does not follow the convention%s: SM_Ship_<Ship>[_<Part>][_LOD<n>], "
                                   "UCX_<Mesh>_<NN>, SOCKET_<Name> (sockets must be empties, the rest meshes)" % hint, name))

    render = c["render"]
    ships = sorted({r["ship"] for r in render.values()})
    if not render:
        issues.append(issue(ERROR, "No render mesh found: name the hull SM_Ship_<Ship>, e.g. SM_Ship_Example"))
        return issues, c
    if len(ships) > 1:
        issues.append(issue(ERROR, "More than one ship in the file: %s. Keep one ship per .blend" % ", ".join(ships)))
    ship = ships[0]
    main_name = "SM_Ship_%s" % ship
    if main_name not in render:
        issues.append(issue(ERROR, "Main hull %s is missing (parts and LODs need it)" % main_name))

    # --- render meshes ---------------------------------------------------------------------
    for name, r in sorted(render.items()):
        issues += _transform_issues(r, "Mesh")
        tris = r.get("tris", 0)
        if r["lod"] == 0:
            if tris > limits["lod0_tris_error"]:
                issues.append(issue(ERROR, "%d triangles: far too heavy even for Nanite as a player ship; decimate "
                                           "(Decimate modifier) or bake onto a lower mesh" % tris, name))
            elif tris > limits["lod0_tris_warn"]:
                issues.append(issue(WARN, "%d triangles: only reasonable with Nanite on" % tris, name))
            elif tris > limits["lod0_tris_non_nanite"]:
                issues.append(issue(INFO, "%d triangles: fine with Nanite; without Nanite add LOD1-3" % tris, name))
        else:
            if r["base"] not in render:
                issues.append(issue(ERROR, "LOD%d without its LOD0 mesh %s" % (r["lod"], r["base"]), name))
            prev = r["base"] if r["lod"] == 1 else "%s_LOD%d" % (r["base"], r["lod"] - 1)
            if prev not in render:
                issues.append(issue(ERROR, "LOD%d exists but %s does not: LODs must be consecutive" % (r["lod"], prev), name))
            elif tris > render[prev].get("tris", 0) * limits["lod_reduction_warn"]:
                issues.append(issue(WARN, "LOD%d has %d triangles, more than %d %% of %s (%d)" % (
                    r["lod"], tris, limits["lod_reduction_warn"] * 100, prev, render[prev].get("tris", 0)), name))
        if r.get("uv_layers", 0) == 0:
            issues.append(issue(ERROR, "No UV map: textures cannot be applied (UV > Smart UV Project or unwrap)", name))
        elif r.get("uv_layers", 0) > 2:
            issues.append(issue(WARN, "%d UV maps: Unreal only needs UV0 (Lumen needs no lightmap UVs)" % r["uv_layers"], name))
        materials = r.get("materials", [])
        if not materials:
            issues.append(issue(ERROR, "No material slot: Unreal would use its checker default material", name))
        for slot in materials:
            if not slot:
                issues.append(issue(ERROR, "Empty material slot: assign a material or remove the slot", name))
            elif not MATERIAL_RE.match(slot):
                issues.append(issue(WARN, "Material %r: name it M_Ship_%s_<Slot> (becomes the Unreal slot name)" % (slot, ship), name))
        if len(materials) > limits["materials_warn"]:
            issues.append(issue(WARN, "%d material slots: every slot is a separate draw; aim for 2-4" % len(materials), name))
        if r.get("non_manifold_edges", 0):
            issues.append(issue(WARN, "%d non-manifold edges (holes, internal faces): check Select > All by Trait > Non Manifold"
                                % r["non_manifold_edges"], name))
        if r.get("loose_verts", 0):
            issues.append(issue(WARN, "%d loose vertices: Mesh > Clean Up > Delete Loose" % r["loose_verts"], name))
        if r.get("zero_area_faces", 0):
            issues.append(issue(WARN, "%d zero-area faces: Mesh > Clean Up > Degenerate Dissolve" % r["zero_area_faces"], name))

    # --- collision -------------------------------------------------------------------------
    hulls_per_mesh = {}
    for name, h in sorted(c["collision"].items()):
        issues += _transform_issues(h, "Collision hull")
        target = render.get(h["mesh"])
        if target is None or target["lod"] != 0:
            issues.append(issue(ERROR, "Collision refers to %s, which is not a LOD0 render mesh in this file" % h["mesh"], name))
            continue
        hulls_per_mesh.setdefault(h["mesh"], []).append(h)
        verts = h.get("verts", 0)
        if h["kind"] == "UCX":
            if not h.get("convex", False):
                issues.append(issue(ERROR, "Not convex: Unreal would silently wrap it in a hull that no longer fits. "
                                           "Split it or use Mesh > Convex Hull", name))
            if verts > limits["hull_verts_error"]:
                issues.append(issue(ERROR, "%d vertices: physics caps convex hulls; keep it under %d (ideally %d)" % (
                    verts, limits["hull_verts_error"], limits["hull_verts_warn"]), name))
            elif verts > limits["hull_verts_warn"]:
                issues.append(issue(WARN, "%d vertices: simplify towards %d for cheap sweeps" % (verts, limits["hull_verts_warn"]), name))
            if h.get("inside_out"):
                issues.append(issue(WARN, "Normals point inwards: Mesh > Normals > Recalculate Outside", name))
    for mesh, hulls in hulls_per_mesh.items():
        indices = sorted(h["index"] for h in hulls)
        if indices != list(range(len(indices))):
            issues.append(issue(WARN, "Hull indices %s are not 00, 01, ... in sequence" % indices, mesh))
        if len(hulls) > limits["hulls_warn"]:
            issues.append(issue(WARN, "%d collision hulls: every sweep tests all of them" % len(hulls), mesh))
    if main_name in render and main_name not in hulls_per_mesh:
        issues.append(issue(WARN, "No UCX_ collision for the hull. The pawn sweeps its root box, not the mesh, but UCX "
                                  "hulls size that box and serve hit detection later", main_name))

    # --- sockets ---------------------------------------------------------------------------
    for name, s in sorted(c["sockets"].items()):
        parent = render.get(s.get("parent") or "")
        if parent is None or parent["lod"] != 0:
            issues.append(issue(ERROR, "Socket must be parented to a LOD0 render mesh (Ctrl+P > Object, Keep Transform); "
                                       "parent is %r" % s.get("parent"), name))
    names = {s["socket"] for s in c["sockets"].values()}
    for wanted in RECOMMENDED_SOCKETS:
        if wanted not in names:
            issues.append(issue(WARN, "No SOCKET_%s: the cockpit camera needs it" % wanted, main_name))
    for prefix in RECOMMENDED_SOCKET_PREFIXES:
        if not any(n.startswith(prefix) for n in names):
            issues.append(issue(INFO, "No SOCKET_%s*: engine effects and sound will need one per nozzle" % prefix, main_name))

    # --- whole ship ------------------------------------------------------------------------
    lod0 = [r for r in render.values() if r["lod"] == 0]
    render_box = bounds_union([r.get("bounds") for r in lod0])
    collision_box = bounds_union([h.get("bounds") for h in c["collision"].values()])
    if render_box:
        size = bounds_size(render_box)
        length = size[0]
        if size[1] > size[0] * 1.15:
            issues.append(issue(WARN, "The ship is wider along Y (%.2f m) than long along X (%.2f m): is the nose along +X?"
                                % (size[1], size[0]), main_name))
        if size[2] > max(size[0], size[1]):
            issues.append(issue(WARN, "The ship is taller than it is long: is +Z up?", main_name))
        longest = max(size)
        if longest < limits["length_min_m"] or longest > limits["length_max_m"]:
            issues.append(issue(WARN, "Ship is %.2f m across: scale mistake? AI models usually import about 1-2 units big. "
                                      "Set real dimensions in the N panel and apply scale" % longest, main_name))
        pivot_box = collision_box or render_box
        center = bounds_center(pivot_box)
        offset = math.sqrt(sum(x * x for x in center))
        if offset > limits["pivot_offset_warn"] * max(longest, 1e-6):
            issues.append(issue(WARN, "Pivot is %.2f m from the centre of the %s bounds %s: use 'Center on collision' "
                                      "so the root collision box and rotations are centred" % (
                                          offset, "collision" if collision_box else "render", _fmt(center)), main_name))
        if abs(render_box[0][1] + render_box[1][1]) > 0.05 * max(size[1], 1e-6):
            issues.append(issue(INFO, "Not symmetric about Y = 0 (%.2f m off): fine if intended" % (
                (render_box[0][1] + render_box[1][1]) * 0.5), main_name))
        if collision_box:
            over = max(max(render_box[0][i] - collision_box[0][i], collision_box[1][i] - render_box[1][i]) for i in range(3))
            if over > limits["collision_overhang_warn"] * longest:
                issues.append(issue(WARN, "Collision sticks out %.2f m beyond the visible mesh: the ship would bump into "
                                          "things it visibly clears" % over, main_name))
    return issues, c


def plan_exports(classified):
    """FBX files to write: [(file name, [object names])]. One file per LOD0 mesh (with its
    collision and sockets), one per reduced LOD."""
    render = classified["render"]
    plan = []
    for name, r in sorted(render.items()):
        if r["lod"] != 0:
            continue
        objects = [name]
        objects += sorted(h for h, d in classified["collision"].items() if d["mesh"] == name)
        objects += sorted(s for s, d in classified["sockets"].items() if d.get("parent") == name)
        plan.append((name + ".fbx", objects))
    for name, r in sorted(render.items()):
        if r["lod"] > 0:
            plan.append((name + ".fbx", [name]))
    return plan


MANIFEST_VERSION = 1


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def suggest_pawn_settings(render_box, collision_box, cockpit_location_m):
    """Starting values for ASpaceshipPawn (and the planet) from the ship's size.

    The single source of the formulas in Docs/Ships/ShipPipeline.md, section 5; import_ship.py
    applies these values as they are. All sizes in Unreal centimetres unless the key says M.
    """
    size = bounds_size(render_box)
    box = collision_box or render_box
    box_size = bounds_size(box)
    longest_cm = max(size) * 100.0
    box_height_cm = box_size[2] * 100.0
    center_offset = blender_to_unreal_cm(bounds_center(box))
    cockpit = None
    if cockpit_location_m is not None:
        # Relative to the root box, which sits on the actor origin: the mesh is shifted by
        # -center_offset so the box is centred on the collision hulls.
        cockpit = [round(a - b, 2) + 0.0 for a, b in zip(blender_to_unreal_cm(cockpit_location_m), center_offset)]
    return {
        "HullCollision_BoxExtent_cm": [round(x * 50.0, 1) for x in box_size],
        "HullCollision_center_offset_ue_cm": center_offset,
        "Hull_RelativeLocation_cm": [round(-x, 2) + 0.0 for x in center_offset],
        "CameraBoom_TargetArmLength_cm": round(max(900.0, longest_cm * 1.8), 0),
        "CameraBoom_SocketOffset_Z_cm": round(max(200.0, size[2] * 100.0), 0),
        "CameraBoom_ProbeSize_cm": round(_clamp(box_height_cm * 0.15, 25.0, 50.0), 1),
        "CameraBoom_CameraLagMaxDistance_cm": round(max(1500.0, longest_cm * 2.0), 0),
        "CockpitCamera_location_ue_cm": cockpit,
        "LandingFootprintRadiusCm": round(_clamp(min(box_size[0], box_size[1]) * 50.0, 50.0, 2000.0), 0),
        "LandingMaxGapCm": round(_clamp(box_height_cm * 0.33, 60.0, 200.0), 0),
        "GroundContactToleranceCm": round(_clamp(box_height_cm * 0.05, 10.0, 25.0), 1),
        "HeatShakeCm": round(_clamp(longest_cm * 0.02, 14.0, 60.0), 1),
        "Planet_CollisionWarmupReachM": round(max(15.0, max(size) * 0.75), 1),
        "Planet_CollisionMinRadiusM": round(max(60.0, max(size) * 5.0), 0),
    }


def build_manifest(classified, plan, blend_file=""):
    render = classified["render"]
    ship = sorted({r["ship"] for r in render.values()})[0] if render else None
    lod0 = [r for r in render.values() if r["lod"] == 0]
    render_box = bounds_union([r.get("bounds") for r in lod0])
    collision_box = bounds_union([h.get("bounds") for h in classified["collision"].values()])
    manifest = {
        "manifest_version": MANIFEST_VERSION,
        "ship": ship,
        "blend_file": blend_file,
        "units": "Blender metres, right-handed Z-up; *_ue_cm = Unreal centimetres (Y flipped)",
        "files": [{"fbx": f, "objects": o} for f, o in plan],
        "meshes": {},
        "collision": {},
        "sockets": {},
    }
    for name, r in sorted(render.items()):
        manifest["meshes"][name] = {
            "lod": r["lod"], "part": r.get("part"), "tris": r.get("tris"), "verts": r.get("verts"),
            "materials": r.get("materials"), "uv_layers": r.get("uv_layers"), "bounds_m": r.get("bounds"),
        }
    for name, h in sorted(classified["collision"].items()):
        manifest["collision"][name] = {"kind": h["kind"], "mesh": h["mesh"], "verts": h.get("verts"), "bounds_m": h.get("bounds")}
    for name, sock in sorted(classified["sockets"].items()):
        manifest["sockets"][name] = {"parent": sock.get("parent"), "location_m": sock.get("world_location"),
                                     "location_ue_cm": blender_to_unreal_cm(sock.get("world_location") or [0, 0, 0])}
    if render_box:
        size = bounds_size(render_box)
        manifest["render_bounds_m"] = render_box
        manifest["render_size_m"] = [round(x, 4) for x in size]
        manifest["expected_ue_size_cm"] = [round(x * 100.0, 1) for x in size]
        manifest["collision_bounds_m"] = collision_box
        cockpit = classified["sockets"].get("SOCKET_Cockpit")
        manifest["suggested_pawn_settings"] = suggest_pawn_settings(
            render_box, collision_box, cockpit["world_location"] if cockpit else None)
    return manifest


# Every key import_ship.py relies on, with the range a sane ship produces. (min, max) in the
# key's units; None = any number.
PAWN_SETTING_RANGES = {
    "HullCollision_BoxExtent_cm": (1.0, 5000.0),
    "HullCollision_center_offset_ue_cm": None,
    "Hull_RelativeLocation_cm": None,
    "CameraBoom_TargetArmLength_cm": (300.0, 20000.0),
    "CameraBoom_SocketOffset_Z_cm": (0.0, 5000.0),
    "CameraBoom_ProbeSize_cm": (5.0, 200.0),
    "CameraBoom_CameraLagMaxDistance_cm": (500.0, 50000.0),
    "CockpitCamera_location_ue_cm": None,
    "LandingFootprintRadiusCm": (10.0, 5000.0),
    "LandingMaxGapCm": (10.0, 500.0),
    "GroundContactToleranceCm": (1.0, 100.0),
    "HeatShakeCm": (0.0, 200.0),
    "Planet_CollisionWarmupReachM": (5.0, 200.0),
    "Planet_CollisionMinRadiusM": (20.0, 2000.0),
}
VECTOR_SETTINGS = {"HullCollision_BoxExtent_cm", "HullCollision_center_offset_ue_cm", "Hull_RelativeLocation_cm",
                   "CockpitCamera_location_ue_cm"}


def _is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _is_vec3(v):
    return isinstance(v, (list, tuple)) and len(v) == 3 and all(_is_number(x) for x in v)


def _is_box(b):
    return (isinstance(b, (list, tuple)) and len(b) == 2 and _is_vec3(b[0]) and _is_vec3(b[1])
            and all(b[0][i] <= b[1][i] for i in range(3)))


def _inside(point, box, margin):
    return all(box[0][i] - margin <= point[i] <= box[1][i] + margin for i in range(3))


def validate_manifest(manifest, base_dir=None, limits=LIMITS):
    """Checks a manifest (as loaded from JSON) before anything is imported into Unreal:
    structure, types, internal consistency and sane ranges. base_dir, when given, is the folder
    the FBX files must exist in. Returns a list of issues like validate()."""
    issues = []
    if not isinstance(manifest, dict):
        return [issue(ERROR, "Manifest is not a JSON object")]

    def need(key, check, what):
        if key not in manifest:
            issues.append(issue(ERROR, "Missing key %r" % key))
            return False
        if not check(manifest[key]):
            issues.append(issue(ERROR, "Key %r must be %s, is %r" % (key, what, manifest[key])))
            return False
        return True

    version = manifest.get("manifest_version")
    if version != MANIFEST_VERSION:
        issues.append(issue(ERROR, "manifest_version is %r, this tool reads %d: re-export from Blender" % (version, MANIFEST_VERSION)))

    ship_ok = need("ship", lambda v: isinstance(v, str) and re.match("^%s$" % NAME_PART, v), "a ship name like 'Example'")
    ship = manifest.get("ship") if ship_ok else None
    main = "SM_Ship_%s" % ship if ship else None

    # --- meshes ----------------------------------------------------------------------------
    meshes = manifest.get("meshes")
    if need("meshes", lambda v: isinstance(v, dict) and v, "a non-empty object"):
        for name, m in meshes.items():
            match = RENDER_RE.match(name)
            if not match or (ship and match.group("ship") != ship):
                issues.append(issue(ERROR, "Mesh name does not belong to ship %r" % ship, name))
                continue
            if not isinstance(m, dict):
                issues.append(issue(ERROR, "Mesh entry must be an object", name))
                continue
            if m.get("lod") != int(match.group("lod") or 0):
                issues.append(issue(ERROR, "lod is %r but the name says LOD%s" % (m.get("lod"), match.group("lod") or 0), name))
            for key in ("tris", "verts"):
                if not isinstance(m.get(key), int) or m.get(key) <= 0:
                    issues.append(issue(ERROR, "%s must be a positive integer, is %r" % (key, m.get(key)), name))
            if isinstance(m.get("tris"), int) and m.get("lod") == 0 and m["tris"] > limits["lod0_tris_error"]:
                issues.append(issue(ERROR, "%d triangles is over the %d limit" % (m["tris"], limits["lod0_tris_error"]), name))
            mats = m.get("materials")
            if not isinstance(mats, list) or not mats or not all(isinstance(x, str) and x for x in mats):
                issues.append(issue(ERROR, "materials must be a non-empty list of names, is %r" % (mats,), name))
            if not _is_box(m.get("bounds_m")):
                issues.append(issue(ERROR, "bounds_m must be [[min x,y,z],[max x,y,z]], is %r" % (m.get("bounds_m"),), name))
        if main and main not in meshes:
            issues.append(issue(ERROR, "Main hull %s is not in meshes" % main))

    # --- files -----------------------------------------------------------------------------
    files = manifest.get("files")
    if need("files", lambda v: isinstance(v, list) and v, "a non-empty list"):
        exported_meshes = set()
        for entry in files:
            if not isinstance(entry, dict) or not isinstance(entry.get("fbx"), str) or not isinstance(entry.get("objects"), list) \
                    or not entry.get("objects"):
                issues.append(issue(ERROR, "files entry must be {fbx: name, objects: [...]}, is %r" % (entry,)))
                continue
            fbx, objects = entry["fbx"], entry["objects"]
            if not fbx.lower().endswith(".fbx") or os.path.basename(fbx) != fbx:
                issues.append(issue(ERROR, "fbx must be a plain file name ending in .fbx", fbx))
            if isinstance(meshes, dict) and objects[0] not in meshes:
                issues.append(issue(ERROR, "First object %r is not a listed mesh" % objects[0], fbx))
            if fbx != "%s.fbx" % objects[0]:
                issues.append(issue(ERROR, "File name must be the mesh name + .fbx", fbx))
            exported_meshes.add(objects[0])
            if base_dir is not None and not os.path.isfile(os.path.join(base_dir, fbx)):
                issues.append(issue(ERROR, "File not found next to the manifest", fbx))
        if isinstance(meshes, dict):
            for name in meshes:
                if name not in exported_meshes:
                    issues.append(issue(ERROR, "Mesh has no FBX file in files", name))

    # --- collision -------------------------------------------------------------------------
    collision = manifest.get("collision", {})
    if not isinstance(collision, dict):
        issues.append(issue(ERROR, "collision must be an object"))
        collision = {}
    for name, h in collision.items():
        if not COLLISION_RE.match(name) or not isinstance(h, dict):
            issues.append(issue(ERROR, "Bad collision entry", name))
            continue
        if isinstance(meshes, dict) and (h.get("mesh") not in meshes or meshes[h.get("mesh")].get("lod") != 0):
            issues.append(issue(ERROR, "Collision mesh %r is not a LOD0 mesh" % h.get("mesh"), name))
        if h.get("kind") not in ("UCX", "UBX", "USP", "UCP") or not name.startswith(str(h.get("kind")) + "_"):
            issues.append(issue(ERROR, "kind %r does not match the name" % h.get("kind"), name))
        if not isinstance(h.get("verts"), int) or not 4 <= h["verts"] <= limits["hull_verts_error"]:
            issues.append(issue(ERROR, "verts must be 4..%d, is %r" % (limits["hull_verts_error"], h.get("verts")), name))
        if not _is_box(h.get("bounds_m")):
            issues.append(issue(ERROR, "bounds_m is not a valid box", name))
    if main and not any(isinstance(h, dict) and h.get("mesh") == main for h in collision.values()):
        issues.append(issue(WARN, "No collision hulls for %s: the root box is then sized from the visible mesh" % main))

    # --- size ------------------------------------------------------------------------------
    render_box = manifest.get("render_bounds_m")
    size = manifest.get("render_size_m")
    if need("render_bounds_m", _is_box, "a valid box") and need("render_size_m", lambda v: _is_vec3(v) and min(v) > 0, "three positive numbers"):
        if any(abs(size[i] - (render_box[1][i] - render_box[0][i])) > 0.01 for i in range(3)):
            issues.append(issue(ERROR, "render_size_m does not match render_bounds_m"))
        longest = max(size)
        if not limits["length_min_m"] <= longest <= limits["length_max_m"]:
            issues.append(issue(ERROR, "Ship is %.2f m across, outside %.0f-%.0f m: scale mistake in Blender" % (
                longest, limits["length_min_m"], limits["length_max_m"])))
        if size[1] > size[0] * 1.15:
            issues.append(issue(WARN, "Wider along Y than long along X: nose not along +X?"))
        if need("expected_ue_size_cm", _is_vec3, "three numbers"):
            if any(abs(manifest["expected_ue_size_cm"][i] - size[i] * 100.0) > 0.5 for i in range(3)):
                issues.append(issue(ERROR, "expected_ue_size_cm is not render_size_m x 100"))
    else:
        render_box = None

    collision_box = manifest.get("collision_bounds_m")
    if collision_box is not None and not _is_box(collision_box):
        issues.append(issue(ERROR, "collision_bounds_m must be null or a valid box"))
        collision_box = None
    if render_box and collision_box:
        margin = limits["collision_overhang_warn"] * max(size)
        if not (_inside(collision_box[0], render_box, margin) and _inside(collision_box[1], render_box, margin)):
            issues.append(issue(WARN, "Collision bounds stick out of the render bounds"))

    # --- sockets ---------------------------------------------------------------------------
    sockets = manifest.get("sockets", {})
    if not isinstance(sockets, dict):
        issues.append(issue(ERROR, "sockets must be an object"))
        sockets = {}
    for name, sock in sockets.items():
        if not SOCKET_RE.match(name) or not isinstance(sock, dict):
            issues.append(issue(ERROR, "Bad socket entry", name))
            continue
        loc, ue = sock.get("location_m"), sock.get("location_ue_cm")
        if not _is_vec3(loc) or not _is_vec3(ue):
            issues.append(issue(ERROR, "location_m and location_ue_cm must be three numbers each", name))
            continue
        if any(abs(a - b) > 0.05 for a, b in zip(blender_to_unreal_cm(loc), ue)):
            issues.append(issue(ERROR, "location_ue_cm %s is not location_m %s converted (x100, Y flipped)" % (ue, loc), name))
        if isinstance(meshes, dict) and (sock.get("parent") not in meshes or meshes[sock.get("parent")].get("lod") != 0):
            issues.append(issue(ERROR, "Parent %r is not a LOD0 mesh" % sock.get("parent"), name))
        if render_box and not _inside(loc, render_box, 0.1 * max(size)):
            issues.append(issue(WARN, "Socket lies well outside the ship", name))
    if "SOCKET_Cockpit" not in sockets:
        issues.append(issue(WARN, "No SOCKET_Cockpit: the cockpit camera keeps its current position"))

    # --- suggested pawn settings -----------------------------------------------------------
    settings = manifest.get("suggested_pawn_settings")
    if need("suggested_pawn_settings", lambda v: isinstance(v, dict), "an object"):
        for key, allowed in PAWN_SETTING_RANGES.items():
            if key not in settings:
                issues.append(issue(ERROR, "suggested_pawn_settings is missing %r" % key))
                continue
            value = settings[key]
            if key == "CockpitCamera_location_ue_cm" and value is None:
                continue
            if key in VECTOR_SETTINGS:
                if not _is_vec3(value):
                    issues.append(issue(ERROR, "%s must be three numbers, is %r" % (key, value)))
                    continue
                values = value
            else:
                if not _is_number(value):
                    issues.append(issue(ERROR, "%s must be a number, is %r" % (key, value)))
                    continue
                values = [value]
            if allowed and not all(allowed[0] <= x <= allowed[1] for x in values):
                issues.append(issue(ERROR, "%s = %r is outside %s..%s" % (key, value, allowed[0], allowed[1])))
        for key in settings:
            if key not in PAWN_SETTING_RANGES:
                issues.append(issue(WARN, "Unknown suggested_pawn_settings key %r (ignored by the import)" % key))
        if render_box and all(k in settings for k in PAWN_SETTING_RANGES):
            longest_cm = max(size) * 100.0
            extent = settings["HullCollision_BoxExtent_cm"]
            offset = settings["HullCollision_center_offset_ue_cm"]
            if _is_vec3(extent) and any(extent[i] > size[i] * 55.0 + 1.0 for i in range(3)):
                issues.append(issue(WARN, "Root box extent %s is larger than the ship itself" % (extent,)))
            if _is_vec3(offset) and math.sqrt(sum(x * x for x in offset)) > limits["pivot_offset_warn"] * longest_cm:
                issues.append(issue(WARN, "Collision centre is %.0f cm off the pivot: run 'Center on collision' in Blender"
                                    % math.sqrt(sum(x * x for x in offset))))
            hull_loc = settings["Hull_RelativeLocation_cm"]
            if _is_vec3(offset) and _is_vec3(hull_loc) and any(abs(a + b) > 0.05 for a, b in zip(offset, hull_loc)):
                issues.append(issue(ERROR, "Hull_RelativeLocation_cm must be -HullCollision_center_offset_ue_cm"))
            cockpit = settings["CockpitCamera_location_ue_cm"]
            if _is_vec3(extent) and _is_vec3(cockpit) and any(abs(cockpit[i]) > extent[i] * 1.2 + 50.0 for i in range(3)):
                issues.append(issue(WARN, "Cockpit camera %s lies outside the root box" % (cockpit,)))
            if _is_number(settings["Planet_CollisionMinRadiusM"]) and settings["Planet_CollisionMinRadiusM"] < max(size) * 2.0:
                issues.append(issue(ERROR, "Planet_CollisionMinRadiusM must be at least twice the ship length"))
            if _is_number(settings["Planet_CollisionWarmupReachM"]) and settings["Planet_CollisionWarmupReachM"] < max(size) * 0.5:
                issues.append(issue(ERROR, "Planet_CollisionWarmupReachM must cover at least half the ship length"))
    return issues


def load_and_validate_manifest(path, check_files=True):
    """(manifest or None, issues) for a manifest file on disk."""
    try:
        with open(path, encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, ValueError) as error:
        return None, [issue(ERROR, "Cannot read manifest %s: %s" % (path, error))]
    return manifest, validate_manifest(manifest, os.path.dirname(os.path.abspath(path)) if check_files else None)


def format_issues(issues):
    order = {ERROR: 0, WARN: 1, INFO: 2}
    lines = []
    for i in sorted(issues, key=lambda x: (order[x["level"]], x["object"] or "")):
        lines.append("%-5s %s%s" % (i["level"], ("[%s] " % i["object"]) if i["object"] else "", i["message"]))
    counts = {lvl: sum(1 for i in issues if i["level"] == lvl) for lvl in (ERROR, WARN, INFO)}
    lines.append("-> %d error(s), %d warning(s), %d note(s)" % (counts[ERROR], counts[WARN], counts[INFO]))
    return "\n".join(lines)


# =========================================================================================
# Blender side
# =========================================================================================

FBX_EXPORT_SETTINGS = dict(
    use_selection=True,
    object_types={"MESH", "EMPTY"},
    use_mesh_modifiers=True,
    mesh_smooth_type="FACE",          # writes smoothing groups; Unreal warns without them
    use_tspace=True,                  # tangents for normal maps baked in Blender
    use_triangles=True,               # tangents need tris or quads; n-gons (bevels, text) get none otherwise
    use_custom_props=False,
    apply_unit_scale=True,
    # "All Local": the metre-to-centimetre factor goes into the exported transforms, so the file
    # is already in centimetres and Unreal's default import (Convert Scene Unit off) gets the size
    # right. "FBX Units Scale" instead needs Convert Scene Unit on, or the ship arrives 100x small.
    apply_scale_options="FBX_SCALE_NONE",
    global_scale=1.0,
    axis_forward="-Z",                # Blender defaults: +X stays +X in Unreal, +Y becomes -Y
    axis_up="Y",
    bake_space_transform=False,
    add_leaf_bones=False,
    bake_anim=False,
    path_mode="AUTO",
    embed_textures=False,
)


def _world_bounds(obj, mesh):
    mw = obj.matrix_world
    if not mesh.vertices:
        return None
    pts = [mw @ v.co for v in mesh.vertices]
    return ([min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)])


def _convexity(obj, mesh):
    """(convex, inside_out) in world space; tolerant to coplanar splits."""
    mw = obj.matrix_world
    verts = [mw @ v.co for v in mesh.vertices]
    if len(verts) > 2000 or not mesh.polygons:
        return False, False
    size = max(max(v[i] for v in verts) - min(v[i] for v in verts) for i in range(3)) or 1.0
    eps = size * 1e-4
    normal_matrix = mw.to_3x3().inverted_safe().transposed()
    outward = inward = True
    for poly in mesh.polygons:
        n = (normal_matrix @ poly.normal).normalized()
        c = mw @ poly.center
        for v in verts:
            d = n.dot(v - c)
            if d > eps:
                outward = False
            if d < -eps:
                inward = False
        if not outward and not inward:
            return False, False
    return True, (inward and not outward)


def gather_records(context):
    depsgraph = context.evaluated_depsgraph_get()
    records = []
    for obj in context.scene.objects:
        rec = {
            "name": obj.name,
            "type": obj.type,
            "parent": obj.parent.name if obj.parent else None,
            "location": tuple(obj.location),
            "rotation": tuple(obj.rotation_euler) if obj.rotation_mode != "QUATERNION"
            else tuple(obj.rotation_quaternion.to_euler()),
            "scale": tuple(obj.scale),
            "world_location": [round(x, 5) for x in obj.matrix_world.translation],
            "visible": obj.visible_get(),
        }
        if obj.type == "MESH" and obj.name.startswith(MANAGED_PREFIXES):
            eval_obj = obj.evaluated_get(depsgraph)
            mesh = eval_obj.to_mesh()
            try:
                rec["verts"] = len(mesh.vertices)
                rec["tris"] = sum(len(p.vertices) - 2 for p in mesh.polygons)
                rec["uv_layers"] = len(mesh.uv_layers)
                rec["materials"] = [slot.material.name if slot.material else "" for slot in obj.material_slots]
                rec["bounds"] = _world_bounds(obj, mesh)
                bm = bmesh.new()
                bm.from_mesh(mesh)
                rec["non_manifold_edges"] = sum(1 for e in bm.edges if not e.is_manifold)
                rec["loose_verts"] = sum(1 for v in bm.verts if not v.link_edges)
                rec["zero_area_faces"] = sum(1 for f in bm.faces if f.calc_area() < 1e-10)
                bm.free()
                if obj.name.startswith(("UCX_", "UBX_", "USP_", "UCP_")):
                    rec["convex"], rec["inside_out"] = _convexity(obj, mesh)
            finally:
                eval_obj.to_mesh_clear()
        records.append(rec)
    return records


def scene_info(context):
    units = context.scene.unit_settings
    return {"unit_system": units.system, "scale_length": units.scale_length}


def run_validation(context):
    records = gather_records(context)
    issues, classified = validate(records, scene_info(context))
    return issues, classified, records


def _write_report(text):
    block = bpy.data.texts.get("gamespace_ship_report") or bpy.data.texts.new("gamespace_ship_report")
    block.clear()
    block.write(text + "\n")


def export_ship(context, out_dir, force=False):
    """Validates and writes the FBX files and manifest. Returns (ok, report text)."""
    if context.object and context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    issues, classified, _ = run_validation(context)
    report = format_issues(issues)
    if any(i["level"] == ERROR for i in issues) and not force:
        return False, report + "\nExport cancelled: fix the errors (or use --force)."

    out_dir = bpy.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    plan = plan_exports(classified)
    view_layer = context.view_layer
    selected = [o for o in context.scene.objects if o.select_get()]
    active = view_layer.objects.active
    written = []
    try:
        for file_name, names in plan:
            for o in context.scene.objects:
                o.select_set(False)
            restore_hidden = []
            for n in names:
                o = bpy.data.objects[n]
                if o.name not in view_layer.objects:
                    raise RuntimeError("%s is in an excluded collection; include it in the view layer" % n)
                if o.hide_get():
                    o.hide_set(False)
                    restore_hidden.append(o)
                o.select_set(True)
            view_layer.objects.active = bpy.data.objects[names[0]]
            path = os.path.join(out_dir, file_name)
            bpy.ops.export_scene.fbx(filepath=path, **FBX_EXPORT_SETTINGS)
            for o in restore_hidden:
                o.hide_set(True)
            written.append(path)
    finally:
        for o in context.scene.objects:
            o.select_set(o in selected)
        view_layer.objects.active = active

    manifest = build_manifest(classified, plan, bpy.data.filepath)
    manifest_path = os.path.join(out_dir, "%s_manifest.json" % (manifest["ship"] or "ship"))
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    written.append(manifest_path)
    # Read it back the way the Unreal import will: a manifest that does not pass here would
    # fail there, after the editor had to be closed for it.
    _, manifest_issues = load_and_validate_manifest(manifest_path)
    report += "\nWrote:\n  " + "\n  ".join(written) + "\n\nManifest check:\n" + format_issues(manifest_issues)
    return not any(i["level"] == ERROR for i in manifest_issues), report


def center_on_collision(context):
    """Moves every ship mesh so the collision bounds (or render bounds without collision) are
    centred on the world origin, keeping each object's origin at the world origin."""
    issues, classified, _ = run_validation(context)
    blocking = [i for i in issues if i["level"] == ERROR and ("scale" in i["message"] or "rotated" in i["message"])]
    if blocking:
        return False, "Apply rotation and scale first:\n" + format_issues(blocking)
    lod0 = [r for r in classified["render"].values() if r["lod"] == 0]
    box = bounds_union([h.get("bounds") for h in classified["collision"].values()]) or bounds_union([r.get("bounds") for r in lod0])
    if not box:
        return False, "Nothing to center"
    from mathutils import Matrix, Vector
    offset = Vector(bounds_center(box))
    moved = []
    for name in list(classified["render"]) + list(classified["collision"]):
        obj = bpy.data.objects[name]
        # Move the geometry, not the object: origins stay at the world origin, which is the pivot.
        obj.data.transform(Matrix.Translation(obj.matrix_world.inverted().to_3x3() @ -offset))
        moved.append(name)
    for name in classified["sockets"]:
        obj = bpy.data.objects[name]
        obj.matrix_world = Matrix.Translation(-offset) @ obj.matrix_world
        moved.append(name)
    return True, "Shifted %d objects by %s m. HIGH_ reference meshes were not moved." % (len(moved), _fmt(-offset))


if bpy is not None:

    class GAMESPACE_OT_validate_ship(bpy.types.Operator):
        bl_idname = "gamespace.validate_ship"
        bl_label = "Validate ship"
        bl_description = "Check naming, transforms, collision hulls, sockets and budgets"

        def execute(self, context):
            issues, _, _ = run_validation(context)
            text = format_issues(issues)
            print(text)
            _write_report(text)
            errors = sum(1 for i in issues if i["level"] == ERROR)
            self.report({"ERROR" if errors else "INFO"}, text.splitlines()[-1] + " (Text Editor: gamespace_ship_report)")
            return {"FINISHED"}

    class GAMESPACE_OT_center_ship(bpy.types.Operator):
        bl_idname = "gamespace.center_ship"
        bl_label = "Center on collision"
        bl_description = "Shift ship geometry so the collision hull bounds are centred on the world origin (the pivot)"
        bl_options = {"REGISTER", "UNDO"}

        def execute(self, context):
            ok, text = center_on_collision(context)
            print(text)
            self.report({"INFO" if ok else "ERROR"}, text.splitlines()[0])
            return {"FINISHED"} if ok else {"CANCELLED"}

    class GAMESPACE_OT_export_ship(bpy.types.Operator):
        bl_idname = "gamespace.export_ship"
        bl_label = "Export FBX for Unreal"
        bl_description = "Validate, then write one FBX per mesh (with UCX_ collision and SOCKET_ empties) and a manifest"

        def execute(self, context):
            ok, text = export_ship(context, context.scene.gamespace_export_dir)
            print(text)
            _write_report(text)
            self.report({"INFO" if ok else "ERROR"}, "Exported" if ok else "Export cancelled: see gamespace_ship_report")
            return {"FINISHED"} if ok else {"CANCELLED"}

    class GAMESPACE_PT_ship_export(bpy.types.Panel):
        bl_label = "Ship Export"
        bl_idname = "GAMESPACE_PT_ship_export"
        bl_space_type = "VIEW_3D"
        bl_region_type = "UI"
        bl_category = "Gamespace"

        def draw(self, context):
            layout = self.layout
            layout.prop(context.scene, "gamespace_export_dir")
            layout.operator("gamespace.validate_ship", icon="CHECKMARK")
            layout.operator("gamespace.center_ship", icon="PIVOT_BOUNDBOX")
            layout.operator("gamespace.export_ship", icon="EXPORT")

    CLASSES = (GAMESPACE_OT_validate_ship, GAMESPACE_OT_center_ship, GAMESPACE_OT_export_ship, GAMESPACE_PT_ship_export)


def register():
    bpy.types.Scene.gamespace_export_dir = bpy.props.StringProperty(
        name="Export folder", subtype="DIR_PATH", default="//Export",
        description="Where the FBX files and manifest go; // is the .blend file's folder")
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.gamespace_export_dir


def _main_cli(argv):
    import argparse
    parser = argparse.ArgumentParser(prog="gamespace_ship_export")
    parser.add_argument("--out", default="//Export")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--force", action="store_true", help="export despite validation errors")
    args = parser.parse_args(argv)
    if args.validate_only:
        issues, _, _ = run_validation(bpy.context)
        print(format_issues(issues))
        return 1 if any(i["level"] == ERROR for i in issues) else 0
    ok, text = export_ship(bpy.context, args.out, force=args.force)
    print(text)
    return 0 if ok else 1


def _main_plain(argv):
    import argparse
    parser = argparse.ArgumentParser(prog="gamespace_ship_export", description="Manifest check without Blender")
    parser.add_argument("--check-manifest", required=True, metavar="MANIFEST_JSON")
    parser.add_argument("--no-files", action="store_true", help="do not require the FBX files next to the manifest")
    args = parser.parse_args(argv)
    _, issues = load_and_validate_manifest(args.check_manifest, check_files=not args.no_files)
    print(format_issues(issues))
    return 1 if any(i["level"] == ERROR for i in issues) else 0


if __name__ == "__main__" and bpy is None:
    sys.exit(_main_plain(sys.argv[1:]))

if __name__ == "__main__" and bpy is not None:
    if bpy.app.background and "--" in sys.argv:
        sys.exit(_main_cli(sys.argv[sys.argv.index("--") + 1:]))
    else:
        try:
            unregister()
        except Exception:
            pass
        register()
