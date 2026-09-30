"""Builds a batch of interior kit parts in Blender (step 4 of the kit brief, 26. 9. 2026).

    blender -b --factory-startup --python Tools/Kit/kit_build.py -- walls [--sections W,N] [--no-render]

For each part: parametric geometry (kit_walls.py), mesh decals from the decal library laid onto it
(hs_decals.Placer, slots Kit_Decal / Kit_DecalAO / Kit_DecalPaint), UCX collision and SOCKET_ empties. Output:
  ArtSource/Kit/Kit_Walls.blend                 every part at the origin, one collection each
  ArtSource/Kit/Export/SM_Kit_*.fbx              one per part (metres -> centimetres, +X stays +X, +Y -> -Y)
  ArtSource/Kit/Export/kit_manifest.json         parts: category, family, size, variant, tris vs budget,
                                                 materials, sockets (UE cm) with light parameters, collision
  Saved/KitCatalog/<part>_front.png / _34.png    neutral studio renders for the catalog sheet (kit_catalog.py)
Prints KITBUILD {...}.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "Blender"))
import kit_geo  # noqa: E402
import kit_walls  # noqa: E402

ROOT = kit_geo.ROOT
EXPORT = os.path.join(ROOT, "ArtSource", "Kit", "Export")
RENDERS = os.path.join(ROOT, "Saved", "KitCatalog")
FBX = dict(use_selection=True, object_types={"MESH", "EMPTY"}, use_mesh_modifiers=True, mesh_smooth_type="FACE",
           use_tspace=True, use_triangles=True, use_custom_props=False, apply_unit_scale=True,
           apply_scale_options="FBX_SCALE_NONE", global_scale=1.0, axis_forward="-Z", axis_up="Y",
           bake_space_transform=False, add_leaf_bones=False, bake_anim=False, path_mode="AUTO", embed_textures=False,
           colors_type="LINEAR", prioritize_active_color=True)   # Col carries masks, not a colour: no sRGB curve


def decals(ob, part):
    """Lays the part's decal shots onto it; returns the decal object (joined into ob by the caller)."""
    import hs_decals
    index = json.load(open(os.path.join(ROOT, "ArtSource", "Ships", "Shared", "Decals", "decal_library_index.json"), encoding="utf-8"))
    pl = hs_decals.Placer(ob, {"offset_m": 0.0012, "grid_m": 0.06}, index, (0.0, 0.0, 0.0), (99.0, 99.0))
    placed, failed = [], []
    for it in part.decal_items:
        if it["item"] not in index["decals"]:
            failed.append((it["item"], "not in index"))
            continue
        o = Vector(it["from"])
        d = (Vector(it["to"]) - o).normalized()
        hit, n = pl.cast(o, d)
        if hit is None:
            failed.append((it["item"], "miss"))
            continue
        pl.reach = 0.02 if it.get("label") else 0.06
        fr = it.get("frame")
        fr = (Vector(fr[0]), Vector(fr[1])) if fr else None
        if fr and fr[0].cross(fr[1]).dot(n) < 0:
            # x cross y must be the surface normal, or the item reads mirrored (and before the face-normal fix in
            # hs_decals.grid it was laid with its back to the viewer: portal B's left hazard band, 27. 9. 2026)
            failed.append((it["item"], "mirrored frame"))
            continue
        if pl.place_at(it["item"], hit, n, it.get("rot", 0.0), it.get("scale", 1.0), "kit", not it.get("label"), fr):
            placed.append(it["item"])
        else:
            failed.append((it["item"], "edge/overlap"))
    # grime cards (kit_geo Part.grime): a ray along -normal from 5 cm out finds the surface, the card follows it
    for g in part.grime_cards:
        n0 = Vector(g["normal"]).normalized()
        hit, n = pl.cast(Vector(g["at"]) + n0 * 0.05, -n0)
        if hit is None or n.dot(n0) < 0.7:
            failed.append(("grime_" + g["kind"], "miss"))
            continue
        if pl.card_at(hit, n, Vector(g["up"]), g["size"], g["kind"], 0.08, 0.06, g["alpha"],
                      "DecalWear" if g.get("wear") else "DecalGrime"):
            placed.append("grime_" + g["kind"])
        else:
            failed.append(("grime_" + g["kind"], "no faces"))
    if not pl.bm.faces:
        pl.bm.free()
        return None, placed, failed
    me = bpy.data.meshes.new(ob.name + "_decals")
    pl.bm.to_mesh(me)
    pl.bm.free()
    for slot in ("Kit_Decal", "Kit_DecalAO", "Kit_DecalPaint", "Kit_Decal", "Kit_DecalAO", "Kit_DecalGrime", "Kit_DecalWear"):
        me.materials.append(bpy.data.materials[slot])
    dob = bpy.data.objects.new(me.name, me)
    ob.users_collection[0].objects.link(dob)
    return dob, placed, failed


def to_corner_colour(me, name="Col"):
    """A point-domain colour attribute as a face-corner one of the same name. The part's masks are per corner
    (kit_geo), the decal cards' per point (hs_decals): joined as they were, the point layer won the name and the
    part's masks were lost - all white, which Unreal drops on import (27. 9. 2026)."""
    src = me.color_attributes.get(name)
    if src is None or src.domain == "CORNER":
        return
    vals = [tuple(d.color) for d in src.data]
    me.color_attributes.remove(src)
    dst = me.color_attributes.new(name, "FLOAT_COLOR", "CORNER")
    for loop in me.loops:
        dst.data[loop.index].color = vals[loop.vertex_index]


def colour_masks(ob, name="Col"):
    """How many face corners carry the edge mask (G) and the secondary tone (B): zero means the masks are gone."""
    a = ob.data.color_attributes.get(name)
    if a is None:
        return {"domain": None, "edge": 0, "secondary": 0, "floor": 0, "seam": 0}
    edge = sum(1 for d in a.data if d.color[1] < 0.5)
    sec = sum(1 for d in a.data if d.color[2] < 0.5)
    floor = sum(1 for d in a.data if d.color[0] < 0.95)
    # occlusion on faces looking up: only the seam dirt puts it there (kit_geo SEAM_*)
    seam = 0
    if a.domain == "CORNER":
        seam = sum(1 for p in ob.data.polygons if p.normal.z > 0.9 for li in p.loop_indices if a.data[li].color[0] < 0.95)
    return {"domain": a.domain, "edge": edge, "secondary": sec, "floor": floor, "seam": seam}


def join(ob, other):
    """Appends other's mesh (same frame) to ob's, mapping its material slots onto ob's (no operators: the
    background context has no reliable selection)."""
    import bmesh
    me = ob.data
    to_corner_colour(other.data)
    names = [m.name for m in me.materials]
    remap = []
    for m in other.data.materials:
        if m.name not in names:
            me.materials.append(m)
            names.append(m.name)
        remap.append(names.index(m.name))
    bm = bmesh.new()
    bm.from_mesh(me)
    n0 = len(bm.faces)
    bm.from_mesh(other.data)
    bm.faces.ensure_lookup_table()
    for f in bm.faces[n0:]:
        f.material_index = remap[f.material_index] if f.material_index < len(remap) else 0
    bm.to_mesh(me)
    bm.free()
    bpy.data.objects.remove(other)


def drop_unused_slots(ob):
    """The FBX exporter leaves out material slots no face uses (a module without structural decals) - so does
    the manifest, or the importer's slot check fails."""
    me = ob.data
    used = sorted({p.material_index for p in me.polygons})
    mats = [me.materials[i] for i in used]
    remap = {old: new for new, old in enumerate(used)}
    idx = [remap[p.material_index] for p in me.polygons]
    me.materials.clear()
    for m in mats:
        me.materials.append(m)
    me.polygons.foreach_set("material_index", idx)
    me.update()


def tris(ob, slots=None):
    me = ob.data
    names = [m.name for m in me.materials]
    return sum(len(p.vertices) - 2 for p in me.polygons if slots is None or names[p.material_index] in slots)


def export(ob):
    bpy.context.view_layer.update()
    for o in bpy.context.scene.objects:
        if o is not None:
            o.select_set(False)
    ob.select_set(True)
    for c in ob.children:
        c.select_set(True)
    bpy.context.view_layer.objects.active = ob
    path = os.path.join(EXPORT, ob.name + ".fbx")
    bpy.ops.export_scene.fbx(filepath=path, **FBX)
    return path


def render_setup():
    sc = bpy.context.scene
    engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = 900, 900
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.exposure = 0.6
    w = bpy.data.worlds.new("kit_studio")
    sc.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (0.32, 0.33, 0.35, 1.0)
    bg.inputs[1].default_value = 0.6
    # key, fill, rim: the same neutral light for every part
    for name, rot, energy in (("key", (math.radians(50), 0, math.radians(35)), 3.5), ("fill", (math.radians(70), 0, math.radians(-60)), 1.2),
                              ("rim", (math.radians(110), 0, math.radians(160)), 1.5)):
        ld = bpy.data.lights.new(name, "SUN")
        ld.energy = energy
        lo = bpy.data.objects.new(name, ld)
        lo.rotation_euler = rot
        sc.collection.objects.link(lo)
    cd = bpy.data.cameras.new("cat_cam")
    cd.lens = 60
    cam = bpy.data.objects.new("cat_cam", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    return cam


def render(ob, cam, views=((1, 0, 0.12), (1, -0.9, 0.35))):
    os.makedirs(RENDERS, exist_ok=True)
    for o in bpy.context.scene.objects:
        if o.type == "MESH":
            o.hide_render = o is not ob
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    lo = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
    hi = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
    c = (lo + hi) / 2
    r = (hi - lo).length / 2
    dist = r / math.tan(math.radians(17)) * 1.05
    out = {}
    for tag, d in (("front", Vector(views[0])), ("34", Vector(views[1]))):
        d.normalize()
        cam.location = c + d * dist
        cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        path = os.path.join(RENDERS, "%s_%s.png" % (ob.name, tag))
        bpy.context.scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        out[tag] = path
    return out


def jobs(batch, sections, budget):
    """What a batch builds: dicts with the part builder and its manifest facts."""
    seed = 11
    if batch == "walls":
        for sec in sections:
            for kind, L, var in kit_walls.BATCH1:
                if kind == "Locker" and sec == "N" and L > 0.9:
                    continue
                seed += 7
                yield dict(name=kit_walls.part_name(kind, L, sec, var), part=(lambda k=kind, l=L, s=sec, v=var, sd=seed: kit_walls.build_part(k, l, s, v, sd)),
                           category="Wall", family="Wall_" + kind, kind=kind, length=L, section=sec, variant=var, batch=1,
                           budget=int(budget.get("Wall_base", 0) + budget["Wall_per_m"] * L), render=(sec == sections[0]),
                           views=((1, 0, 0.12), (1, -0.9, 0.35)))
    elif batch == "batch2":
        import kit_batch2
        for cat, part, size, sec, var in kit_batch2.BATCH2:
            seed += 7
            yield dict(name=kit_batch2.part_name(cat, part, size, sec, var),
                       part=(lambda c=cat, pa=part, sz=size, s=sec, v=var, sd=seed: kit_batch2.build_part(c, pa, sz, s, v, sd)),
                       category=cat, family="%s_%s" % (cat, part), kind=part, length=size, section=sec, variant=var, batch=2,
                       budget=kit_batch2.budget(cat, part, size), render=True, views=kit_batch2.VIEWS[(cat, part)])
        # the sample's narrow stub walls (batch 1 families in section N, not rendered)
        for kind, L, var in (("Plain", 1.2, "A"), ("Plain", 1.2, "C")):
            seed += 7
            yield dict(name=kit_walls.part_name(kind, L, "N", var), part=(lambda k=kind, l=L, v=var, sd=seed: kit_walls.build_part(k, l, "N", v, sd)),
                       category="Wall", family="Wall_" + kind, kind=kind, length=L, section="N", variant=var, batch=1,
                       budget=int(budget.get("Wall_base", 0) + budget["Wall_per_m"] * L), render=False, views=None)
    elif batch == "batch3":
        import kit_batch3
        for cat, part, size, sec, var in kit_batch3.BATCH3:
            seed += 7
            yield dict(name=kit_batch3.part_name(cat, part, size, sec, var),
                       part=(lambda c=cat, pa=part, sz=size, s=sec, v=var, sd=seed: kit_batch3.build_part(c, pa, sz, s, v, sd)),
                       category=cat, family="%s_%s" % (cat, part), kind=part, length=size, section=sec, variant=var, batch=3,
                       budget=kit_batch3.budget(cat, part, size), render=True, views=kit_batch3.VIEWS[(cat, part)])
    elif batch == "batch4":
        import kit_batch4
        for cat, part, size, sec, var in kit_batch4.BATCH4:
            seed += 7
            yield dict(name=kit_batch4.part_name(cat, part, size, sec, var),
                       part=(lambda c=cat, pa=part, sz=size, s=sec, v=var, sd=seed: kit_batch4.build_part(c, pa, sz, s, v, sd)),
                       category=cat, family="%s_%s" % (cat, part), kind=part, length=size, section=sec, variant=var, batch=4,
                       budget=kit_batch4.budget(cat, part, size), render=True, views=kit_batch4.VIEWS[(cat, part)])
    elif batch == "liner":
        import kit_liner
        seed0 = seed
        for i, (kind, L, var) in enumerate(kit_liner.LINER):
            seed = seed0 + 7 * (i + 1)
            yield dict(name=kit_liner.part_name(kind, L, var), part=(lambda k=kind, l=L, v=var, sd=seed: kit_liner.build_part(k, l, v, sd)),
                       category="Wall", family="Wall_" + kind, kind=kind, length=L, section="L", variant=var, batch=4,
                       budget=kit_liner.budget(L), render=True, views=kit_liner.VIEWS)
        # the ceilings of the liner rooms (their width per room: sections L41 hold, L38 cabin)
        seed = seed0 + 7 * 5          # the ceilings' seeds as before the sixth liner part (D, 30. 9. 2026)
        import kit_batch2
        for sec, size, var in (("L41", 1.2, "A"), ("L41", 1.2, "C"), ("L41", 0.6, "A"), ("L41", 0.6, "B"),
                               ("L38", 1.2, "A"), ("L38", 1.2, "C")):
            seed += 7
            yield dict(name=kit_batch2.part_name("Ceiling", "Panel", size, sec, var),
                       part=(lambda s=sec, z=size, v=var, sd=seed: kit_batch2.build_part("Ceiling", "Panel", z, s, v, sd)),
                       category="Ceiling", family="Ceiling_Panel", kind="Panel", length=size, section=sec, variant=var, batch=4,
                       budget=max(1500, int(kit_geo.RULES["tri_budget"]["Ceiling_per_m"] * size)), render=True,
                       views=kit_batch2.VIEWS[("Ceiling", "Panel")])
        # the floors of the liner rooms (30. 9. 2026: the Wayfarer's cabin, its own tiles "a bathroom"), after the
        # ceilings so their seeds stay
        import kit_batch3
        for sec, size, var in (("L38", 1.2, "A"),):
            seed += 7
            yield dict(name=kit_batch3.part_name("Floor", "Plate", size, sec, var),
                       part=(lambda s=sec, z=size, v=var, sd=seed: kit_batch3.build_part("Floor", "Plate", z, s, v, sd)),
                       category="Floor", family="Floor_Plate", kind="Plate", length=size, section=sec, variant=var, batch=4,
                       budget=kit_batch3.budget("Floor", "Plate", size), render=True, views=kit_batch3.VIEWS[("Floor", "Plate")])
    elif batch == "batch4b":
        import kit_batch4b
        for cat, part, size, sec, var in kit_batch4b.BATCH4B:
            seed += 7
            yield dict(name=kit_batch4b.part_name(cat, part, size, sec, var),
                       part=(lambda c=cat, pa=part, sz=size, s=sec, v=var, sd=seed: kit_batch4b.build_part(c, pa, sz, s, v, sd)),
                       category=cat, family="%s_%s" % (cat, part), kind=part, length=size, section=sec, variant=var, batch=4,
                       budget=kit_batch4b.budget(cat, part, size), render=True, views=kit_batch4b.VIEWS[(cat, part)])
    elif batch == "furniture":
        import kit_furniture
        for cat, part, size, sec, var in kit_furniture.FURNITURE:
            seed += 7
            yield dict(name=kit_furniture.part_name(cat, part, size, sec, var),
                       part=(lambda c=cat, pa=part, sz=size, s=sec, v=var, sd=seed: kit_furniture.build_part(c, pa, sz, s, v, sd)),
                       category=cat, family="%s_%s" % (cat, part), kind=part, length=size, section=sec, variant=var, batch=6,
                       budget=kit_furniture.budget(cat, part, size), render=True, views=kit_furniture.VIEWS[(cat, part)])
    else:
        raise SystemExit("unknown batch %s" % batch)


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    batch = args[0]
    sections = ["W"]
    if "--sections" in args:
        sections = args[args.index("--sections") + 1].split(",")
    do_render = "--no-render" not in args
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    mats = kit_geo.materials()
    os.makedirs(EXPORT, exist_ok=True)
    budget = kit_geo.RULES["tri_budget"]
    manifest_path = os.path.join(EXPORT, "kit_manifest.json")
    manifest = json.load(open(manifest_path, encoding="utf-8")) if os.path.exists(manifest_path) else {"parts": {}}
    cam = render_setup() if do_render else None
    report = {"parts": 0, "over_budget": [], "decals_failed": {}}
    only = set(args[args.index("--only") + 1].split(",")) if "--only" in args else None
    for job in jobs(batch, sections, budget):
        if only and job["name"] not in only:
            continue
        if True:
            part, L, sec, kind, var = job["part"](), job["length"], job["section"], job["kind"], job["variant"]
            coll = bpy.data.collections.new(part.name)
            bpy.context.scene.collection.children.link(coll)
            ob = part.build(coll, mats)
            dob, placed, failed = decals(ob, part)
            if dob is not None:
                join(ob, dob)
            drop_unused_slots(ob)
            masks = colour_masks(ob)
            if masks["domain"] != "CORNER" or masks["edge"] + masks["floor"] + masks["secondary"] == 0:
                raise SystemExit("%s: the colour masks did not survive (%s) - Unreal drops an all-white Col" % (ob.name, masks))
            if failed:
                report["decals_failed"][ob.name] = failed
            geo = tris(ob, [r for r in kit_geo.ROLES])
            limit = job["budget"]
            if geo > limit:
                report["over_budget"].append((ob.name, geo, limit))
            bad = [c.name for c in ob.children if c.name.startswith("SOCKET_") and "." in c.name]
            if bad:
                raise SystemExit("%s: socket names clash with an earlier part: %s" % (ob.name, bad))
            path = export(ob)
            sockets = {}
            for c in ob.children:
                if c.name.startswith("SOCKET_"):
                    t = c.matrix_world.translation
                    sockets[c.name] = {"location_ue_cm": [round(t.x * 100, 2), round(-t.y * 100, 2), round(t.z * 100, 2)],
                                       "params": json.loads(c.get("params", "{}"))}
            # object names are global in a .blend: rename this part's sockets now it is exported, or the next
            # part's SOCKET_Light_Cove_0 becomes SOCKET_Light_Cove_0.001 (and Unreal keeps the suffix)
            for c in ob.children:
                if c.name.startswith("SOCKET_"):
                    c.name = "%s__%s" % (c.name, ob.name)
            dims = [round(d, 3) for d in ob.dimensions]
            manifest["parts"][ob.name] = {
                "category": job["category"], "family": job["family"], "section": sec, "length_m": L, "variant": var, "batch": job["batch"],
                "fbx": os.path.relpath(path, ROOT).replace("\\", "/"), "dims_m": dims,
                "expected_size_cm": [round(ob.dimensions.x * 100, 1), round(ob.dimensions.y * 100, 1), round(ob.dimensions.z * 100, 1)],
                "tris": geo, "tris_decals": tris(ob) - geo, "tri_budget": limit,
                "materials": [m.name for m in ob.data.materials], "sockets": sockets,
                "collision_hulls": sum(1 for c in ob.children if c.name.startswith("UCX_")),
                "decals": len(placed), "decal_items": placed,
                # the labels that name a system or a service point: layout rule, never the same on neighbours
                "service_labels": sorted({d for d in placed if d.startswith(("st_", "label_"))}),
                "colour_masks": masks, "status": "built"}
            if do_render and job["render"]:
                manifest["parts"][ob.name]["renders"] = {k: os.path.relpath(v, ROOT).replace("\\", "/") for k, v in render(ob, cam, job["views"]).items()}
            # every part stays at the origin in its collection; hide it so the next one renders alone
            coll.hide_render = True
            report["parts"] += 1
    json.dump(manifest, open(manifest_path, "w", encoding="utf-8"), indent=1)
    out = os.path.join(ROOT, "ArtSource", "Kit", {"walls": "Kit_Walls.blend"}.get(batch, "Kit_%s.blend" % batch.capitalize()))
    for c in bpy.data.collections:
        c.hide_render = False
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print("KITBUILD " + json.dumps(report))


if __name__ == "__main__":
    main()
