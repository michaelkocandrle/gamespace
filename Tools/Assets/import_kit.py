"""Imports the interior kit into Unreal and builds its showroom (step 4 of the kit brief, 26. 9. 2026).

    .\\Tools\\run_editor_python.ps1 Tools\\Assets\\import_kit.py

1. Parts from ArtSource/Kit/Export/kit_manifest.json (Tools/Kit/kit_build.py) -> /Game/Kit/Meshes/SM_Kit_*:
   no Nanite, the UCX hulls as collision (simple as complex, blocks the Camera channel with the default
   BlockAll profile), sockets checked against the manifest - with the ship importer's own checks.
2. Materials MI_Kit_<Maker>_<Role> in /Game/Kit/Materials on the shared ship masters, colours from
   kit_rules.json palettes; the trim sheet and the screen atlas in /Game/Kit/Textures. Slots are assigned by
   their role name. The decal slots use the ships' shared decal atlas instances.
3. The showroom in /Game/Maps/TestSpace at KIT_ORIGIN (500 m to -Y, the Steadfast interior sits at +Y): a
   section-W corridor composed of the batch's wall modules, a light at every light socket, closed in a dark
   box against the sun. Floor, ceiling, end walls and the three down-lights are provisional (batches 2 and 3).
   Everything carries the tag KitShowroom and is rebuilt on every run.
Prints KITIMPORT {...}.
"""
import json
import math
import os
import sys

import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import import_ship  # noqa: E402
import ship_materials  # noqa: E402

REPO = os.path.dirname(os.path.dirname(HERE))
MANIFEST = os.path.join(REPO, "ArtSource", "Kit", "Export", "kit_manifest.json")
RULES = json.load(open(os.path.join(REPO, "ArtSource", "Kit", "kit_rules.json"), encoding="utf-8"))
DEST, MATS, TEX = "/Game/Kit/Meshes", "/Game/Kit/Materials", "/Game/Kit/Textures"
MAP = "/Game/Maps/TestSpace"
KIT_ORIGIN = unreal.Vector(0.0, -50000.0, 0.0)
TAG = "KitShowroom"
MAKER = "Halcyon"
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
DECAL_MIS = {"Kit_Decal": "/Game/Ships/Wayfarer/Materials/MI_Ship_Wayfarer_Decal",
             "Kit_DecalAO": "/Game/Ships/Wayfarer/Materials/MI_Ship_Wayfarer_DecalAO",
             "Kit_DecalPaint": "/Game/Ships/Wayfarer/Materials/MI_Ship_Wayfarer_DecalPaint"}
# the composed corridor: part names (section W) from x = 0 along +X; left = +Y wall, right = -Y wall
CORRIDOR = {
    "left": ["Plain12W_A", "Display06W_A", "Locker06W_A", "Pipes12W_A", "Hatch06W_A", "Grille06W_A", "Plain12W_C",
             "Locker12W_C", "Display06W_B", "Plain03W_A", "Display03W_C"],
    "right": ["Pipes12W_B", "Grille12W_B", "Plain06W_A", "Locker06W_B", "Hatch12W_C", "Plain12W_B", "Grille12W_C",
              "Hatch06W_B", "Plain06W_A"],
}


def log(msg):
    unreal.log("import_kit: " + msg)


def import_texture(path, kind):
    name = os.path.splitext(os.path.basename(path))[0]
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", path)
    task.set_editor_property("destination_path", TEX)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", False)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    t = EAL.load_asset("%s/%s" % (TEX, name))
    if kind == "normal":
        t.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        t.set_editor_property("srgb", False)
        t.set_editor_property("flip_green_channel", True)
    elif kind == "masks":
        t.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
        t.set_editor_property("srgb", False)
    else:
        t.set_editor_property("srgb", True)
    EAL.save_loaded_asset(t, only_if_is_dirty=False)
    return t


def build_materials():
    masters = ship_materials.build_masters()
    pal = RULES["palettes"][MAKER]

    def layered(colour, rough, metal=0.0, secondary=None, grunge=0.3, vary=0.35, dirt=0.05, wear=0.0):
        return {"master": "layered",
                "vectors": {"PrimaryColor": colour, "SecondaryColor": secondary or [c * 0.72 for c in colour],
                            "BareMetalColor": [0.5, 0.5, 0.52], "DirtColor": [0.05, 0.045, 0.04]},
                "scalars": {"PrimaryRoughness": rough, "SecondaryRoughness": rough + 0.06, "PaintMetallic": metal,
                            "EdgeWear": wear, "WearThreshold": 0.45, "GrungeAmount": grunge, "GrungeTileCm": 45.0, "RoughVariation": vary, "DirtAmount": dirt,
                            "CavityStrength": 0.0, "AOStrength": 0.0, "PanelTone": 0.08, "PanelRough": 0.12, "MetalShare": 0.03,
                            "CarbonShare": 0.0, "LiveryAmount": 0.0, "ClearCoat": 0.0}}

    def plain(colour, rough, metal=0.0, emit=None, strength=0.0):
        s = {"master": "hull", "base_color": colour, "roughness": rough, "metallic": metal}
        if emit:
            s["emissive_color"], s["emissive_strength"] = emit, strength
        return s

    specs = {
        # painted panels are paint - a dielectric: at PaintMetallic 0.45 they lost almost half their diffuse light
        # and the walls went black (round 2, 27. 9. 2026); grime and dirt by the floor, fine grain kept low (it
        # sparkled like sandpaper). No worn edges: SC paint has none (Docs/Reviews/2026-09-26_sc_breakdown_tasks.md)
        "Kit_Primary": layered(pal["Kit_Primary"], 0.5, 0.1, secondary=[c * 0.72 for c in pal["Kit_Primary"]],
                               grunge=0.3, vary=0.35, dirt=0.35, wear=0.3),
        # the structure layer as the palette's lighter painted metal: pure metal (1.0) mirrored the dark room and
        # the frames vanished into the gaps
        # edge wear on the chamfers only (kit_geo: Col.G = 0 on bevel faces), like the Wayfarer interior (0.3-0.8);
        # "no worn edges, one roughness" read as plastic (critic round 3)
        "Kit_Structure": layered([c * 0.8 for c in pal["Kit_Structure"]], 0.36, 0.4, grunge=0.25, vary=0.3, dirt=0.3, wear=0.5),
        # the provisional floor plane (batch 3 brings the floor): rough, not a mirror for the plinth lights
        "Kit_ProvFloor": layered([0.07, 0.068, 0.065], 0.7, 0.2, grunge=0.5, vary=0.3, dirt=0.3),
        # cream paint at 70 % of the palette value: at 0.7 linear the pipes read as "white glossy pipes" (critic)
        "Kit_Accent": layered([c * 0.7 for c in pal["Kit_Accent"]], 0.56, grunge=0.45, dirt=0.3, wear=0.3),
        "Kit_Signal": plain([c * 0.8 for c in pal["Kit_Signal"]], 0.5),        # paint, not a glow (critic round 2)
        "Kit_Rubber": plain([0.018, 0.018, 0.02], 0.86),
        "Kit_Fabric": plain([0.03, 0.03, 0.032], 0.9),
        "Kit_Plastic": plain([0.035, 0.035, 0.038], 0.5),
        "Kit_Seal": plain([0.012, 0.012, 0.013], 0.7),
        "Kit_GlowWarm": plain([0.08, 0.08, 0.08], 0.3, emit=pal["Kit_GlowWarm"], strength=14.0),
        "Kit_GlowCool": plain([0.04, 0.04, 0.05], 0.3, emit=pal["Kit_GlowCool"], strength=4.0),   # the plinth, quieter
        "Kit_GlowSignal": plain([0.08, 0.04, 0.02], 0.3, emit=pal["Kit_GlowSignal"], strength=4.0),
        "Kit_Glass": {"master": "glass", "base_color": [0.02, 0.03, 0.035], "opacity": 0.4, "roughness": 0.05},
    }
    mis = {}
    for role, spec in specs.items():
        mis[role] = ship_materials.build_instance("MI_Kit_%s_%s" % (MAKER, role.split("_", 1)[1]), MATS, spec, masters)
    tex = os.path.join(REPO, "ArtSource", "Kit", "Textures")
    trim = ship_materials.build_instance("MI_Kit_%s_Trim" % MAKER, MATS, {"master": "pbr"}, masters)
    for param, fn, kind in (("BaseColorMap", "T_Kit_Trim_BC.png", "color"), ("ORMMap", "T_Kit_Trim_ORM.png", "masks"),
                            ("NormalMap", "T_Kit_Trim_N.png", "normal")):
        MEL.set_material_instance_texture_parameter_value(trim, param, import_texture(os.path.join(tex, fn), kind))
    MEL.update_material_instance(trim)
    EAL.save_loaded_asset(trim, only_if_is_dirty=False)
    mis["Kit_Trim"] = trim
    screen = ship_materials.build_instance("MI_Kit_%s_Screen" % MAKER, MATS, {"master": "screen"}, masters)
    MEL.set_material_instance_texture_parameter_value(screen, "ScreenTexture", import_texture(os.path.join(tex, "T_Kit_Screens.png"), "color"))
    MEL.update_material_instance(screen)
    EAL.save_loaded_asset(screen, only_if_is_dirty=False)
    mis["Kit_Screen"] = screen
    for role, path in DECAL_MIS.items():
        mis[role] = EAL.load_asset(path)
    return mis


def import_parts(mis, report):
    parts = json.load(open(MANIFEST, encoding="utf-8"))["parts"]
    import_ship.use_legacy_fbx_importer()
    meshes = {}
    for name, part in sorted(parts.items()):
        mesh = {"name": name, "fbx": os.path.join(REPO, part["fbx"]), "destination": DEST, "asset_path": "%s/%s" % (DEST, name),
                "nanite": False, "collision_hulls": part["collision_hulls"], "materials": part["materials"],
                "sockets": {k: v["location_ue_cm"] for k, v in part["sockets"].items()}, "expected_size_cm": part["expected_size_cm"]}
        sm = import_ship.import_fbx(mesh)
        verdict = import_ship.compare_size(import_ship.mesh_size_cm(sm), mesh["expected_size_cm"])
        if verdict != "ok":
            raise import_ship.ImportFailed("%s imported at %s cm, manifest %s (%s)" % (name, import_ship.mesh_size_cm(sm), mesh["expected_size_cm"], verdict))
        sm = import_ship.ensure_fbx_slots(sm, mesh, report)
        import_ship.check_and_fix_mesh(sm, mesh, report)
        body = sm.get_editor_property("body_setup")
        body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
        for i, slot in enumerate(sm.get_editor_property("static_materials")):
            role = str(slot.get_editor_property("material_slot_name"))
            if role in mis and mis[role] is not None:
                sm.set_material(i, mis[role])
            else:
                report.setdefault(name, []).append("slot %s has no kit material" % role)
        EAL.save_loaded_asset(sm, only_if_is_dirty=False)
        meshes[name] = (sm, part)
    return meshes


def spawn_mesh(actors, sm, loc, yaw, label, material=None, scale=None):
    a = actors.spawn_actor_from_class(unreal.StaticMeshActor, loc, unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw))
    a.static_mesh_component.set_static_mesh(sm)
    if material is not None:
        a.static_mesh_component.set_material(0, material)
    if scale is not None:
        a.set_actor_scale3d(scale)
    a.set_actor_label(label)
    a.set_editor_property("tags", [unreal.Name(TAG)])
    return a


LIGHT_COLOURS = {"warm": (255, 228, 200), "cool": (115, 184, 255), "work": (255, 236, 214), "signal": (255, 90, 20)}


def rect_light(actors, loc, role, cd, radius_m, label, forward, along, width_cm, height_cm):
    """A linear fixture: a rect light facing `forward`, its width along `along` (world vectors)."""
    rot = unreal.MathLibrary.make_rot_from_xy(forward, along)
    a = actors.spawn_actor_from_class(unreal.RectLight, loc, rot)
    c = a.rect_light_component
    c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    c.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
    c.set_editor_property("intensity", float(cd))
    c.set_editor_property("attenuation_radius", float(radius_m) * 100.0)
    c.set_editor_property("cast_shadows", False)
    c.set_editor_property("source_width", float(width_cm))
    c.set_editor_property("source_height", float(height_cm))
    c.set_editor_property("barn_door_angle", 70.0)
    c.set_editor_property("barn_door_length", 3.0)
    c.set_editor_property("specular_scale", 0.3)
    col = LIGHT_COLOURS[role]
    c.set_editor_property("light_color", unreal.Color(r=col[0], g=col[1], b=col[2], a=255))
    a.set_actor_label(label)
    a.set_editor_property("tags", [unreal.Name(TAG)])
    return a


def light(actors, loc, role, cd, radius_m, label, spot=False, cone=80.0, source_cm=None):
    cls = unreal.SpotLight if spot else unreal.PointLight
    a = actors.spawn_actor_from_class(cls, loc, unreal.Rotator(roll=0.0, pitch=-90.0 if spot else 0.0, yaw=0.0))
    c = a.spot_light_component if spot else a.point_light_component
    c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    c.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
    c.set_editor_property("intensity", float(cd))
    c.set_editor_property("attenuation_radius", float(radius_m) * 100.0)
    c.set_editor_property("cast_shadows", spot)
    c.set_editor_property("source_radius", float(source_cm) if source_cm else (1.0 if not spot else 4.0))
    c.set_editor_property("specular_scale", 0.2 if not spot else 0.6)
    col = LIGHT_COLOURS[role]
    c.set_editor_property("light_color", unreal.Color(r=col[0], g=col[1], b=col[2], a=255))
    if spot:
        c.set_editor_property("outer_cone_angle", cone / 2)
        c.set_editor_property("inner_cone_angle", cone / 4)
    a.set_actor_label(label)
    a.set_editor_property("tags", [unreal.Name(TAG)])
    return a


def build_showroom(meshes, mis, report):
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAP)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in actors.get_all_level_actors():
        if unreal.Name(TAG) in a.get_editor_property("tags"):
            actors.destroy_actor(a)
    sec = RULES["sections"]["W"]
    half = sec["width"] / 2 * 100.0
    placed, lights = 0, 0
    length = {}
    for side, seq in CORRIDOR.items():
        x = 0.0
        for short in seq:
            name = "SM_Kit_Wall_" + short
            sm, part = meshes[name]
            L = part["length_m"] * 100.0
            if side == "left":
                # face +X -> -Y, length (-Y in UE) -> -X: the pivot sits at the module's +X end
                loc, yaw = unreal.Vector(x + L, half, 0.0), -90.0
            else:
                # face +X -> +Y, length -> +X: the pivot at the module's -X end
                loc, yaw = unreal.Vector(x, -half, 0.0), 90.0
            spawn_mesh(actors, sm, KIT_ORIGIN + loc, yaw, "Kit_%s_%02d_%s" % (side, placed, short))
            placed += 1
            ca, sa = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
            for sname, sock in part["sockets"].items():
                prm = sock.get("params") or {}
                if not sname.startswith("SOCKET_Light"):
                    continue
                lx, ly, lz = sock["location_ue_cm"]
                w = unreal.Vector(lx * ca - ly * sa, lx * sa + ly * ca, lz)
                if prm.get("type") == "rect":
                    dx, dy, dz = prm["dir_ue"]
                    fwd = unreal.Vector(dx * ca - dy * sa, dx * sa + dy * ca, dz)
                    along = unreal.Vector(sa, -ca, 0.0)        # the part's +Y (UE -Y) after the actor's yaw
                    rect_light(actors, KIT_ORIGIN + loc + w, prm.get("role", "warm"), prm["cd"], prm.get("radius_m", 2.0),
                               "KitLight_%s_%d" % (short, lights), fwd, along, prm["width_cm"], prm["height_cm"])
                else:
                    light(actors, KIT_ORIGIN + loc + w, prm.get("role", "warm"), prm.get("cd", 1.0), prm.get("radius_m", 1.6),
                          "KitLight_%s_%d" % (short, lights), source_cm=prm.get("source_radius_cm"))
                lights += 1
            x += L
        length[side] = x
    L = max(length.values())
    # provisional shell (floor / ceiling / ends: batches 2-3) and a dark box against the sun
    plane = EAL.load_asset("/Engine/BasicShapes/Plane")
    cube = EAL.load_asset("/Engine/BasicShapes/Cube")
    x_top = 0.75 * sec["slope_rise"] * 100.0
    ceil_w = sec["width"] * 100.0 - 2 * (x_top - 14.0)
    spawn_mesh(actors, plane, KIT_ORIGIN + unreal.Vector(L / 2, 0, 0.0), 0.0, "KitProvisional_Floor", mis["Kit_ProvFloor"],
               unreal.Vector(L / 100.0, (sec["width"] * 100.0 + 30.0) / 100.0, 1.0))
    # (a metallic provisional ceiling mirrored the provisional lights as a burnt cross: all provisional planes rough)
    c = spawn_mesh(actors, plane, KIT_ORIGIN + unreal.Vector(L / 2, 0, sec["ceiling"] * 100.0), 0.0, "KitProvisional_Ceiling",
                   mis["Kit_ProvFloor"], unreal.Vector(L / 100.0, ceil_w / 100.0, 1.0))
    c.set_actor_rotation(unreal.Rotator(roll=180.0, pitch=0.0, yaw=0.0), False)
    for xe, yaw in ((0.0, 0.0), (L, 180.0)):
        e = spawn_mesh(actors, plane, KIT_ORIGIN + unreal.Vector(xe, 0, sec["ceiling"] * 50.0), 0.0, "KitProvisional_End",
                       mis["Kit_ProvFloor"], unreal.Vector(sec["ceiling"] * 1.0, sec["width"] * 1.0 + 0.3, 1.0))
        e.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=-90.0, yaw=yaw), False)
    spawn_mesh(actors, cube, KIT_ORIGIN + unreal.Vector(L / 2, 0, 100.0), 0.0, "KitProvisional_SunBox", mis["Kit_Seal"],
               unreal.Vector(L / 100.0 + 4.0, 6.0, 5.0))
    # provisional ceiling lights (the kit's ceiling panels with light housings, batch 2, replace them): at the
    # approved Wayfarer corridor's 60 cd spots / 20 cd room lights they burnt a band into the ceiling and a patch
    # onto the end wall and flattened the walls (critic, 27. 9. 2026) - half that, narrower spots, dark between
    # (round 2: at 30 cd / 60 deg the walls under 1.3 m got no light - "a black wall"): 45 cd / 90 deg, away from
    # the ends so the end walls get no patch
    for k, xx in enumerate((L * 0.22, L * 0.5, L * 0.78)):
        light(actors, KIT_ORIGIN + unreal.Vector(xx, 0, sec["ceiling"] * 100.0 - 5.0), "work", 45.0, 3.8, "KitProvisional_Down_%d" % k,
              spot=True, cone=90.0)
        # the fill 80 cm under the ceiling: 30 cm under it, it burnt a hot spot into the plane right above
        light(actors, KIT_ORIGIN + unreal.Vector(xx, 0, sec["ceiling"] * 100.0 - 80.0), "work", 8.0, 4.0, "KitProvisional_Room_%d" % k)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    report["showroom"] = {"modules": placed, "lights": lights, "length_m": L / 100.0}


def clear_old():
    """Showroom actors out of the level first, then the old kit meshes: a reimport over them kept stale sockets."""
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAP)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in actors.get_all_level_actors():
        if unreal.Name(TAG) in a.get_editor_property("tags"):
            actors.destroy_actor(a)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    if EAL.does_directory_exist(DEST):
        for path in EAL.list_assets(DEST, recursive=False, include_folder=False):
            EAL.delete_asset(path.split(".")[0])


def main():
    report = {}
    clear_old()
    mis = build_materials()
    meshes = import_parts(mis, report)
    build_showroom(meshes, mis, report)
    print("KITIMPORT " + json.dumps({"parts": len(meshes), "notes": {k: v for k, v in report.items() if k != "showroom"},
                                     "showroom": report.get("showroom")}))


main()
