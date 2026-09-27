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
SPAWN_TAG = "KitShowroomSpawn"          # space.Showroom / U walks the player here (SpacePlayerController)
ANNEX_SPAWN_TAG = "KitShowroomAnnexSpawn"   # U again from the showroom (or space.Showroom annex): the annex
STAIRS_SPAWN_TAG = "KitShowroomStairsSpawn" # U from the annex (or space.Showroom stairs): the stair bay (batch 3)
GRAVITY_CMS2 = 981.0
# every kit light x1.8 (author 27. 9. 2026): under MegaLights' ray-traced shadows the lights stopped leaking through the
# geometry and the corridor's mean fell from 0.20 to 0.13; x1.8 puts it in the middle of the SC range (kit_brightness)
KIT_LIGHT_SCALE = 1.8
MAKER = "Halcyon"
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
DECAL_MIS = {"Kit_Decal": "/Game/Ships/Wayfarer/Materials/MI_Ship_Wayfarer_Decal",
             "Kit_DecalAO": "/Game/Ships/Wayfarer/Materials/MI_Ship_Wayfarer_DecalAO",
             "Kit_DecalPaint": "/Game/Ships/Wayfarer/Materials/MI_Ship_Wayfarer_DecalPaint"}
# The composed sample (batches 1 and 2, 27. 9. 2026), in metres from KIT_ORIGIN, Unreal axes (+X along the main
# corridor, +Y to its left). A W corridor from an end wall with a window (x = 0) with portals at a 2.4 m pitch and
# its ceiling; an L-turn at x = 9.6..12 (the outer corner on the left, the inner corner at the far right); the leg
# along +Y to a transition into an N stub and its end wall.
#   wall_runs: (start, end, face normal, modules from start to end) - wall modules, W unless named N
#   run_parts: (start, direction, parts one after another) - portals, ceiling, the transition
#   placed:    (part, position, yaw deg) - end walls and corners, placed by their own pivot
SHOWROOM = {
    "wall_runs": [
        ((0.0, 1.2), (2.1, 1.2), (0, -1), ["Wall_Plain12W_A", "Wall_Display06W_A", "Wall_Plain03W_A"]),
        ((2.4, 1.2), (4.5, 1.2), (0, -1), ["Wall_Locker06W_A", "Wall_Pipes12W_A", "Wall_Display03W_C"]),
        ((4.8, 1.2), (6.9, 1.2), (0, -1), ["Wall_Hatch06W_A", "Wall_Grille06W_A", "Wall_Plain06W_A", "Wall_Plain03W_A"]),
        ((7.2, 1.2), (9.6, 1.2), (0, -1), ["Wall_Plain12W_C", "Wall_Locker06W_B", "Wall_Plain06W_A"]),
        ((0.0, -1.2), (2.1, -1.2), (0, 1), ["Wall_Pipes12W_B", "Wall_Hatch06W_B", "Wall_Plain03W_A"]),
        ((2.4, -1.2), (4.5, -1.2), (0, 1), ["Wall_Grille12W_B", "Wall_Plain06W_A", "Wall_Plain03W_A"]),
        ((4.8, -1.2), (6.9, -1.2), (0, 1), ["Wall_Hatch12W_C", "Wall_Display06W_B", "Wall_Plain03W_A"]),
        ((7.2, -1.2), (12.0, -1.2), (0, 1), ["Wall_Locker12W_C", "Wall_Plain12W_B", "Wall_Grille12W_C", "Wall_Plain12W_A"]),
        ((12.0, -1.2), (12.0, 4.8), (-1, 0), ["Wall_Plain12W_C", "Wall_Pipes12W_C", "Wall_Plain12W_B", "Wall_Hatch06W_A",
                                              "Wall_Plain06W_A", "Wall_Plain12W_A"]),
        ((9.6, 1.2), (9.6, 4.8), (1, 0), ["Wall_Plain12W_A", "Wall_Locker06W_A", "Wall_Display06W_A", "Wall_Plain12W_C"]),
        ((10.2, 5.7), (10.2, 8.1), (1, 0), ["Wall_Plain12N_A", "Wall_Plain12N_C"]),
        ((11.4, 5.7), (11.4, 8.1), (-1, 0), ["Wall_Plain12N_C", "Wall_Plain12N_A"]),
        # the annex (author 27. 9.: the catalogue-only parts in the game): a closed L south of the corridor - End24W_A,
        # 2.4 m of W, a turn with the chamfered inner corner B, 2.4 m of leg and the narrowing into a crawlway.
        # Its own start (U from the showroom); not visible from the showroom's measured views
        ((2.4, -3.6), (7.2, -3.6), (0, -1), ["Wall_Plain12W_A", "Wall_Grille06W_A", "Wall_Plain06W_A", "Wall_Locker12W_C",
                                             "Wall_Plain12W_B"]),
        ((7.2, -3.6), (7.2, -8.4), (-1, 0), ["Wall_Plain12W_C", "Wall_Pipes12W_A", "Wall_Plain12W_A", "Wall_Hatch06W_B",
                                             "Wall_Plain06W_A"]),
        ((2.4, -6.0), (4.8, -6.0), (0, 1), ["Wall_Hatch12W_C", "Wall_Plain12W_B"]),
        ((4.8, -6.0), (4.8, -8.4), (1, 0), ["Wall_Display06W_B", "Wall_Plain06W_A", "Wall_Plain12W_C"]),
    ],
    "run_parts": [
        ((2.1, 0.0), (1, 0), ["Portal_Ring03W_A"]),
        ((4.5, 0.0), (1, 0), ["Portal_Ring03W_B"]),
        ((6.9, 0.0), (1, 0), ["Portal_Ring03W_C"]),
        # light sources at most ~1.8 m apart: down-lights (Panel A), linear lights (C), the lit portal (A)
        ((0.0, 0.0), (1, 0), ["Ceiling_Panel03W_A", "Ceiling_Panel12W_A", "Ceiling_Tray06W_A"]),
        ((2.4, 0.0), (1, 0), ["Ceiling_Panel06W_A", "Ceiling_Tray12W_A", "Ceiling_Panel03W_A"]),
        # portal C carries tray B's duct and pipe through its head: tray B on both sides of it
        ((4.8, 0.0), (1, 0), ["Ceiling_Panel03W_A", "Ceiling_Panel06W_A", "Ceiling_Tray12W_B"]),
        ((7.2, 0.0), (1, 0), ["Ceiling_Tray12W_B", "Ceiling_Panel12W_A"]),
        ((10.8, 1.2), (0, 1), ["Ceiling_Panel12W_C", "Ceiling_Panel12W_B", "Ceiling_Panel12W_A"]),
        ((10.8, 5.4), (0, -1), ["Wall_Transition06W_A"]),
        ((10.8, 5.4), (0, 1), ["Portal_Ring03N_B"]),         # the heavy bulkhead frame at the narrow end
        ((10.8, 5.7), (0, 1), ["Ceiling_Panel12N_A", "Ceiling_Panel12N_A"]),
        # floors (batch 3) instead of the provisional planes: plates, gratings over the service channel, hatches
        ((0.0, 0.0), (1, 0), ["Floor_Plate12W_A", "Floor_Plate12W_B", "Floor_Grille12W_A", "Floor_Plate06W_A", "Floor_Hatch06W_A",
                              "Floor_Plate12W_A", "Floor_Plate12W_B", "Floor_Grille06W_A", "Floor_Plate06W_B", "Floor_Plate12W_A",
                              "Floor_Plate12W_A"]),
        ((9.6, 0.0), (1, 0), ["Floor_Plate12W_A", "Floor_Plate12W_A"]),
        ((10.8, 1.2), (0, 1), ["Floor_Plate12W_B", "Floor_Grille12W_A", "Floor_Plate12W_A", "Floor_Plate06W_A"]),
        ((10.8, 5.4), (0, 1), ["Floor_Plate03N_A", "Floor_Grille12N_A", "Floor_Plate12N_B"]),
        ((2.4, -4.8), (1, 0), ["Floor_Plate12W_A", "Floor_Hatch06W_A", "Floor_Plate06W_B", "Floor_Plate12W_A", "Floor_Plate12W_A"]),
        ((6.0, -6.0), (0, -1), ["Floor_Grille12W_A", "Floor_Plate12W_B"]),
        # the stair bay (batch 3): a provisional hall with a 0.8 m deck, the ship's stair and the boarding ramp up to it
        ((16.5, -1.8), (1, 0), ["Stair_Flight08N_A"]),
        ((14.6, 1.2), (1, 0), ["Stair_Ramp29W_A"]),
        ((17.5, -1.8, 0.8), (1, 0), ["Floor_Plate12W_A", "Floor_Plate12W_B"]),
        ((17.5, 1.2, 0.8), (1, 0), ["Floor_Plate12W_B", "Floor_Plate12W_A"]),
        ((2.4, -4.8), (1, 0), ["Ceiling_Panel12W_C", "Ceiling_Panel12W_A"]),
        ((6.0, -6.0), (0, -1), ["Ceiling_Panel12W_B", "Ceiling_Panel12W_A"]),   # the down-light by the crawlway
    ],
    "placed": [
        ("Wall_End24W_B", (0.0, 1.2), 0.0),
        ("Wall_End12N_A", (11.4, 8.1), -90.0),
        ("Corner_Inner00W_A", (12.0, -1.2), 180.0),
        ("Corner_Outer00W_A", (9.6, 1.2), 0.0),
        ("Wall_End24W_A", (2.4, -3.6), 0.0),
        ("Wall_Narrow24W_A", (4.8, -8.4), 90.0),
        ("Corner_Inner00W_B", (7.2, -3.6), -90.0),
        ("Corner_Outer00W_A", (4.8, -6.0), 90.0),
    ],
    # provisional until the kit has them: the junction's and the transition's ceiling, the floor (batch 3)
    "prov_ceiling": [(9.6, 12.0, -1.2, 1.2), (9.6, 12.0, 4.8, 5.4), (4.8, 7.2, -6.0, -3.6)],
    # the corridors have kit floors now (batch 3); the stair bay keeps a provisional floor
    "prov_floor": [(14.0, 20.0, -3.0, 3.0)],
    # the stair bay's provisional hall: walls, ceiling and the deck (x0, x1, y0, y1, z0, z1)
    "prov_boxes": [(13.9, 14.0, -3.1, 3.1, 0.0, 3.4), (20.0, 20.1, -3.1, 3.1, 0.0, 3.4), (13.9, 20.1, -3.1, -3.0, 0.0, 3.4),
                   (13.9, 20.1, 3.0, 3.1, 0.0, 3.4), (13.9, 20.1, -3.1, 3.1, 3.4, 3.5), (17.5, 20.0, -3.0, 3.0, 0.0, 0.79)],
    # ((x, y), cd[, cone]); the second junction spot lights the inner corner (its walls sat at a mean of 0.09 under
    # the one in the middle) from the open ceiling - over the slopes' tops (0.6 m in from the walls) it was shadowed
    "prov_spots": [((10.8, 0.0), 30.0), ((11.1, -0.3), 24.0, 120.0), ((10.8, 5.1), 12.0),
                   ((6.0, -4.8), 30.0), ((6.3, -4.5), 24.0, 120.0),
                   # the stair bay's hall (provisional, 3.4 m high): 100 cd - at 40 its mean was 0.07
                   ((15.3, -1.8), 100.0, 110.0, 3.35), ((15.3, 1.5), 100.0, 110.0, 3.35), ((18.8, -1.8), 100.0, 110.0, 3.35),
                   ((18.8, 1.5), 100.0, 110.0, 3.35)],
    "gravity": (-0.3, 20.3, -9.3, 8.3),
    "spawn": ((0.7, 0.0), 0.0),
    "spawn_annex": ((3.1, -4.8), 0.0),
    "spawn_stairs": ((15.0, -1.8), 0.0),             # in front of the stair: space.Walk 1 0 3 climbs it
    # the half-open window of End24W_B looks out at a star field: a card behind the wall whose material looks the
    # stars up by the view direction (a window onto infinity, no parallax); in a ship the real outside
    "window_stars": ((-1.3, 0.0, 1.0), (3.0, 2.2)),
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


TRIM_MASTER = "/Game/Kit/Materials/M_Kit_Trim"


def build_trim_master():
    """The kit's trim sheet master: base colour x tint, ORM (roughness, metallic), the normal map, nothing else. The
    ship hull master (M_Ship_PBR) it used before adds hull-only layers - a triplanar micro normal, panel seams, soot -
    and on faces lying exactly flat it rendered black whatever its parameters (anti-slip lanes, hazard strips, the
    ceiling vent; the same faces in the layered master lit fine - 27. 9. 2026)."""
    sm = ship_materials
    m = sm._fresh_material(TRIM_MASTER)
    col = sm._texture_param(m, "BaseColorMap", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
                            "/Engine/EngineResources/WhiteSquareTexture", -700, 0)
    tint = sm._node(m, unreal.MaterialExpressionMultiply, -350, 0)
    if not MEL.connect_material_expressions(col, "RGB", tint, "A"):
        raise RuntimeError("trim: colour -> tint")
    sm._link(sm._vector(m, "BaseColorTint", (1.0, 1.0, 1.0), -700, 200), tint, "B")
    sm._output(tint, unreal.MaterialProperty.MP_BASE_COLOR)
    orm = sm._texture_param(m, "ORMMap", unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
                            "/Engine/EngineResources/WhiteSquareTexture", -700, 350)
    for i, (ch, prop, par) in enumerate((("G", unreal.MaterialProperty.MP_ROUGHNESS, "RoughnessScale"),
                                         ("B", unreal.MaterialProperty.MP_METALLIC, "MetallicScale"))):
        mul = sm._node(m, unreal.MaterialExpressionMultiply, -350, 350 + i * 120)
        if not MEL.connect_material_expressions(orm, ch, mul, "A"):
            raise RuntimeError("trim: ORM %s" % ch)
        sm._link(sm._scalar(m, par, 1.0, -700, 550 + i * 100), mul, "B")
        sm._output(mul, prop)
    ao = sm._node(m, unreal.MaterialExpressionLinearInterpolate, -350, 600, const_a=1.0)
    if not MEL.connect_material_expressions(orm, "R", ao, "B"):
        raise RuntimeError("trim: ORM R")
    sm._link(sm._scalar(m, "AOStrength", 0.6, -700, 750), ao, "Alpha")
    sm._output(ao, unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    nrm = sm._texture_param(m, "NormalMap", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
                            "/Engine/EngineMaterials/DefaultNormal", -700, 850)
    if not MEL.connect_material_property(nrm, "RGB", unreal.MaterialProperty.MP_NORMAL):
        raise RuntimeError("trim: normal")
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m, only_if_is_dirty=False)
    return m


def build_materials():
    masters = ship_materials.build_masters()
    pal = RULES["palettes"][MAKER]

    def layered(colour, rough, metal=0.0, secondary=None, grunge=0.3, vary=0.35, dirt=0.05, wear=0.0):
        return {"master": "layered",
                "vectors": {"PrimaryColor": colour, "SecondaryColor": secondary or [c * 0.72 for c in colour],
                            "BareMetalColor": [0.5, 0.5, 0.52], "DirtColor": [0.05, 0.045, 0.04]},
                "scalars": {"PrimaryRoughness": rough, "SecondaryRoughness": rough + 0.06, "PaintMetallic": metal,
                            "EdgeWear": wear, "WearThreshold": 0.45, "BareMetalRoughness": 0.52, "GrungeAmount": grunge, "GrungeTileCm": 45.0, "RoughVariation": vary, "DirtAmount": dirt,
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
        # roughness 0.46 and worn bare metal 0.52 (layered()): interiors run without Lumen reflections, and metal under ~0.45
        # has nothing to reflect there - the tread plates rendered black (27. 9. 2026)
        "Kit_Structure": layered([c * 0.8 for c in pal["Kit_Structure"]], 0.46, 0.4, grunge=0.25, vary=0.3, dirt=0.3, wear=0.5),
        # the provisional floor plane (batch 3 brings the floor): rough, not a mirror for the plinth lights
        "Kit_ProvFloor": layered([0.07, 0.068, 0.065], 0.7, 0.2, grunge=0.5, vary=0.3, dirt=0.3),
        # cream paint at 70 % of the palette value: at 0.7 linear the pipes read as "white glossy pipes" (critic)
        "Kit_Accent": layered([c * 0.7 for c in pal["Kit_Accent"]], 0.56, grunge=0.45, dirt=0.3, wear=0.3),
        "Kit_Signal": plain([c * 0.8 for c in pal["Kit_Signal"]], 0.5),        # paint, not a glow (critic round 2)
        "Kit_Rubber": plain([0.018, 0.018, 0.02], 0.86),
        "Kit_Fabric": plain([0.03, 0.03, 0.032], 0.9),
        "Kit_Plastic": plain([0.035, 0.035, 0.038], 0.5),
        "Kit_Seal": plain([0.012, 0.012, 0.013], 0.7),
        # 7, not 14: the fixture diffusers and the ring clipped to white plates (critic r2); 4 still read 0.88
        "Kit_GlowWarm": plain([0.08, 0.08, 0.08], 0.3, emit=pal["Kit_GlowWarm"], strength=7.0),
        "Kit_GlowCool": plain([0.04, 0.04, 0.05], 0.3, emit=pal["Kit_GlowCool"], strength=4.0),   # the plinth, quieter
        "Kit_GlowSignal": plain([0.08, 0.04, 0.02], 0.3, emit=pal["Kit_GlowSignal"], strength=4.0),
        # opacity 0.2: at 0.4 the dark glass swallowed a lit shutter behind it (the end wall's window read black)
        "Kit_Glass": {"master": "glass", "base_color": [0.02, 0.03, 0.035], "opacity": 0.2, "roughness": 0.05},
    }
    mis = {}
    for role, spec in specs.items():
        mis[role] = ship_materials.build_instance("MI_Kit_%s_%s" % (MAKER, role.split("_", 1)[1]), MATS, spec, masters)
    tex = os.path.join(REPO, "ArtSource", "Kit", "Textures")
    # the trim sheet carries its own grooves and bolts: the PBR master's hull detail normal (30 cm tile) under the
    # grazing wash light drew grass-like streaks on the rails, its hull panel lines dark bars across them - both
    # off (critic finding "noise band over the window", batch 2; checked with space.Kit on the packaged game)
    trim = ship_materials.build_instance("MI_Kit_%s_Trim" % MAKER, MATS, {"master": "trim"}, dict(masters, trim=build_trim_master()))
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
        # the FBX's normals and tangents as they are: with the build's own recompute (on in these assets) the engine
        # smoothed every thin box across its edges (the export writes face smoothing, no sharp edges) and the flat
        # faces of the normal-mapped trim came out black - anti-slip lanes, hazard strips, the vent (27. 9. 2026)
        bs = unreal.EditorStaticMeshLibrary.get_lod_build_settings(sm, 0)
        if bs.get_editor_property("recompute_normals") or bs.get_editor_property("recompute_tangents"):
            bs.set_editor_property("recompute_normals", False)
            bs.set_editor_property("recompute_tangents", False)
            unreal.EditorStaticMeshLibrary.set_lod_build_settings(sm, 0, bs)
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
    c.set_editor_property("intensity", float(cd) * KIT_LIGHT_SCALE)
    c.set_editor_property("attenuation_radius", float(radius_m) * 100.0)
    # MegaLights variant C (author, 27. 9. 2026): every kit light casts its ray-traced shadow; MegaLights is on while
    # walking an interior (SpacePlayerController), shots of the showroom set r.MegaLights.EnableForProject 1
    c.set_editor_property("cast_shadows", True)
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
    c.set_editor_property("intensity", float(cd) * KIT_LIGHT_SCALE)
    c.set_editor_property("attenuation_radius", float(radius_m) * 100.0)
    c.set_editor_property("cast_shadows", True)             # MegaLights variant C, as rect_light
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


def check_layout_labels(parts):
    """The layout rule for decals (author, 27. 9. 2026): a service label (st_*, label_*) only at its hardware -
    kit_walls - and never the same one on neighbouring modules of a run. parts: {"left": [part dicts in order], ...}."""
    clashes = []
    for side, seq in parts.items():
        for (na, a), (nb, b) in zip(seq, seq[1:]):
            same = set(a.get("service_labels", [])) & set(b.get("service_labels", []))
            if same:
                clashes.append("%s: %s next to %s share %s" % (side, na, nb, sorted(same)))
    if clashes:
        raise import_ship.ImportFailed("neighbouring modules repeat a service label: " + "; ".join(clashes))
    return sum(len(seq) - 1 for seq in parts.values())


def _v(xy, z=0.0):
    return KIT_ORIGIN + unreal.Vector(xy[0] * 100.0, xy[1] * 100.0, z * 100.0)


def _rot(yaw, x, y):
    ca, sa = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    return x * ca - y * sa, x * sa + y * ca


def place_part(actors, meshes, short, pos_cm, yaw, label, counts):
    """One kit part at a world position (cm, relative to KIT_ORIGIN) and yaw, with the lights of its sockets."""
    sm, part = meshes["SM_Kit_" + short]
    spawn_mesh(actors, sm, KIT_ORIGIN + pos_cm, yaw, label)
    counts["parts"] += 1
    for sname, sock in part["sockets"].items():
        prm = sock.get("params") or {}
        if not sname.startswith("SOCKET_Light"):
            continue
        lx, ly, lz = sock["location_ue_cm"]
        wx, wy = _rot(yaw, lx, ly)
        at = KIT_ORIGIN + pos_cm + unreal.Vector(wx, wy, lz)
        lab = "KitLight_%s_%d" % (short, counts["lights"])
        if prm.get("type") == "rect":
            dx, dy, dz = prm["dir_ue"]
            fx, fy = _rot(yaw, dx, dy)
            ax, ay, az = prm.get("along_ue", (0.0, -1.0, 0.0))    # default: the part's +Y (Unreal -Y)
            gx, gy = _rot(yaw, ax, ay)
            rect_light(actors, at, prm.get("role", "warm"), prm["cd"], prm.get("radius_m", 2.0), lab, unreal.Vector(fx, fy, dz),
                       unreal.Vector(gx, gy, az), prm["width_cm"], prm["height_cm"])
        elif prm.get("type") == "spot":
            light(actors, at, prm.get("role", "work"), prm["cd"], prm.get("radius_m", 3.8), lab, spot=True,
                  cone=prm.get("cone_deg", 90.0), source_cm=prm.get("source_radius_cm"))
        else:
            light(actors, at, prm.get("role", "warm"), prm.get("cd", 1.0), prm.get("radius_m", 1.6), lab,
                  source_cm=prm.get("source_radius_cm"))
        counts["lights"] += 1


STARS_MATERIAL = "/Game/Kit/Materials/M_Kit_WindowStars"


def build_window_stars():
    """An unlit opaque star field looked up by the view direction, from the space sky's own HLSL (stars, nebulae,
    the Milky Way glow): on a card behind a window it reads as the sky at infinity. Not the sky material itself:
    that one is a sky-pass material (is_sky). build_space_scene runs its main() on import: its constants by ast."""
    import ast
    src = open(os.path.join(REPO, "Tools", "Assets", "build_space_scene.py"), encoding="utf-8").read()
    const = {}
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                const[node.targets[0].id] = ast.literal_eval(node.value)
            except ValueError:
                pass
    sm = ship_materials
    m = sm._fresh_material(STARS_MATERIAL)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("two_sided", True)
    view = sm._node(m, unreal.MaterialExpressionCameraVectorWS, -1100, 0)
    d = sm._node(m, unreal.MaterialExpressionMultiply, -900, 0, const_b=-1.0)   # from the eye, not to it
    sm._link(view, d, "A")
    stars = sm._custom(m, "Stars", const["STAR_HLSL"], unreal.CustomMaterialOutputType.CMOT_FLOAT3,
                       ["Dir", "Density", "Brightness", "Time", "Twinkle"], -600, 0)
    sm._link(d, stars, "Dir")
    sm._link(sm._scalar(m, "StarDensity", const["STAR_DENSITY"], -900, 200), stars, "Density")
    sm._link(sm._scalar(m, "StarBrightness", const["STAR_BRIGHTNESS"], -900, 320), stars, "Brightness")
    sm._link(sm._node(m, unreal.MaterialExpressionTime, -900, 440), stars, "Time")
    sm._link(sm._scalar(m, "Twinkle", 0.0, -900, 540), stars, "Twinkle")
    nebula = sm._custom(m, "Nebulae", const["NOISE_STRUCT"] + const["NEBULA_HLSL"], unreal.CustomMaterialOutputType.CMOT_FLOAT3,
                        ["Dir", "Brightness"], -600, 700)
    sm._link(d, nebula, "Dir")
    sm._link(sm._scalar(m, "NebulaBrightness", const["NEBULA_BRIGHTNESS"], -900, 750), nebula, "Brightness")
    glow = sm._node(m, unreal.MaterialExpressionTextureSampleParameterCube, -600, 400, parameter_name="MilkyWayGlow",
                    texture=EAL.load_asset(const["GLOW_TEXTURE"]))
    sm._link(d, glow, "UVs")
    glow_scaled = sm._node(m, unreal.MaterialExpressionMultiply, -350, 400)
    if not MEL.connect_material_expressions(glow, "RGB", glow_scaled, "A"):
        raise RuntimeError("window stars: glow cube -> multiply")
    sm._link(sm._scalar(m, "GlowBrightness", const["GLOW_BRIGHTNESS"], -600, 600), glow_scaled, "B")
    a = sm._node(m, unreal.MaterialExpressionAdd, -250, 0)
    sm._link(stars, a, "A")
    sm._link(glow_scaled, a, "B")
    b = sm._node(m, unreal.MaterialExpressionAdd, -150, 0)
    sm._link(a, b, "A")
    sm._link(nebula, b, "B")
    out = sm._node(m, unreal.MaterialExpressionMultiply, -50, 0)
    sm._link(b, out, "A")
    sm._link(sm._scalar(m, "WindowExposure", 1.0, -250, 200), out, "B")
    sm._output(out, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m, only_if_is_dirty=False)
    return m


def build_showroom(meshes, mis, report):
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAP)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in actors.get_all_level_actors():
        if unreal.Name(TAG) in a.get_editor_property("tags"):
            actors.destroy_actor(a)
    L = SHOWROOM
    report["label_pairs_checked"] = check_layout_labels(
        {"run%d" % i: [(m, meshes["SM_Kit_" + m][1]) for m in run[3]] for i, run in enumerate(L["wall_runs"])})
    counts = {"parts": 0, "lights": 0}
    # wall runs: a wall module's pivot is its start on the face plane, it faces +X and runs along its local -Y (the
    # Blender +Y); a run facing n turns the module by yaw = atan2(n) and the module then runs along (sin, -cos)
    for i, (a, b, n, mods) in enumerate(L["wall_runs"]):
        yaw = math.degrees(math.atan2(n[1], n[0]))
        nat = (math.sin(math.radians(yaw)), -math.cos(math.radians(yaw)))
        ln = math.hypot(b[0] - a[0], b[1] - a[1])
        d = ((b[0] - a[0]) / ln, (b[1] - a[1]) / ln)
        same = nat[0] * d[0] + nat[1] * d[1] > 0
        total = sum(meshes["SM_Kit_" + m][1]["length_m"] for m in mods)
        if abs(total - ln) > 0.01:
            raise import_ship.ImportFailed("wall run %d: modules %.2f m for a run of %.2f m" % (i, total, ln))
        cum = 0.0
        for m in mods:
            lm = meshes["SM_Kit_" + m][1]["length_m"]
            t = cum if same else cum + lm
            place_part(actors, meshes, m, unreal.Vector((a[0] + d[0] * t) * 100.0, (a[1] + d[1] * t) * 100.0, 0.0), yaw,
                       "Kit_run%d_%s" % (i, m), counts)
            cum += lm
    # run parts: +X along the run from the pivot
    for i, (a, d, parts) in enumerate(L["run_parts"]):
        yaw = math.degrees(math.atan2(d[1], d[0]))
        cum = 0.0
        z = a[2] if len(a) > 2 else 0.0              # the stair bay's deck
        for m in parts:
            place_part(actors, meshes, m, unreal.Vector((a[0] + d[0] * cum) * 100.0, (a[1] + d[1] * cum) * 100.0, z * 100.0), yaw,
                       "Kit_line%d_%s" % (i, m), counts)
            cum += meshes["SM_Kit_" + m][1]["length_m"]
    for m, pos, yaw in L["placed"]:
        place_part(actors, meshes, m, unreal.Vector(pos[0] * 100.0, pos[1] * 100.0, 0.0), yaw, "Kit_" + m, counts)
    # provisional: ceiling and floor planes, a dark box against the sun, spots where the kit has no ceiling yet
    plane = EAL.load_asset("/Engine/BasicShapes/Plane")
    cube = EAL.load_asset("/Engine/BasicShapes/Cube")
    C = RULES["sections"]["W"]["ceiling"]
    for k, (x0, x1, y0, y1) in enumerate(L["prov_ceiling"]):
        c = spawn_mesh(actors, plane, _v(((x0 + x1) / 2, (y0 + y1) / 2), C + 0.002), 0.0, "KitProvisional_Ceiling_%d" % k,
                       mis["Kit_ProvFloor"], unreal.Vector(x1 - x0, y1 - y0, 1.0))
        c.set_actor_rotation(unreal.Rotator(roll=180.0, pitch=0.0, yaw=0.0), False)
    for k, (x0, x1, y0, y1) in enumerate(L["prov_floor"]):
        spawn_mesh(actors, plane, _v(((x0 + x1) / 2, (y0 + y1) / 2), 0.0), 0.0, "KitProvisional_Floor_%d" % k,
                   mis["Kit_ProvFloor"], unreal.Vector(x1 - x0, y1 - y0, 1.0))
    gx0, gx1, gy0, gy1 = L["gravity"]
    box = spawn_mesh(actors, cube, _v(((gx0 + gx1) / 2, (gy0 + gy1) / 2), 1.0), 0.0, "KitProvisional_SunBox", mis["Kit_Seal"],
                     unreal.Vector((gx1 - gx0) + 4.0, (gy1 - gy0) + 4.0, 5.0))
    # the box encloses the showroom: without this the walking player would spawn inside its collision
    box.static_mesh_component.set_collision_profile_name("NoCollision")
    for k, (x0, x1, y0, y1, z0, z1) in enumerate(L["prov_boxes"]):
        spawn_mesh(actors, cube, _v(((x0 + x1) / 2, (y0 + y1) / 2), (z0 + z1) / 2), 0.0, "KitProvisional_Box_%d" % k,
                   mis["Kit_ProvFloor"], unreal.Vector(x1 - x0, y1 - y0, z1 - z0))
    for k, spot in enumerate(L["prov_spots"]):
        light(actors, _v(spot[0], spot[3] if len(spot) > 3 else C - 0.05), "work", spot[1], 3.8 if len(spot) < 4 else 4.5,
              "KitProvisional_Down_%d" % k, spot=True, cone=spot[2] if len(spot) > 2 else 90.0)
    # walkable (author, 27. 9. 2026): gravity over the whole sample and the start the player is put at
    gravity = actors.spawn_actor_from_class(unreal.SpaceGravityVolume, _v(((gx0 + gx1) / 2, (gy0 + gy1) / 2), C * 0.5),
                                            unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
    gravity.set_actor_label("KitShowroom_Gravity")
    gravity.set_editor_property("gravity_cm_s2", GRAVITY_CMS2)
    # 4 m tall: the stair bay's deck is 0.8 m up
    gravity.get_editor_property("volume").set_box_extent(unreal.Vector((gx1 - gx0) * 50.0, (gy1 - gy0) * 50.0, 200.0))
    gravity.set_editor_property("tags", [unreal.Name(TAG)])
    for key, label, tag in (("spawn", "KitShowroom_Spawn", SPAWN_TAG), ("spawn_annex", "KitShowroom_AnnexSpawn", ANNEX_SPAWN_TAG),
                            ("spawn_stairs", "KitShowroom_StairsSpawn", STAIRS_SPAWN_TAG)):
        (sx, sy), syaw = L[key]
        spawn = actors.spawn_actor_from_class(unreal.TargetPoint, _v((sx, sy), 0.05), unreal.Rotator(roll=0.0, pitch=0.0, yaw=syaw))
        spawn.set_actor_label(label)
        spawn.set_editor_property("tags", [unreal.Name(TAG), unreal.Name(tag)])
    (wx, wy, wz), (ww, wh) = L["window_stars"]
    stars = spawn_mesh(actors, plane, _v((wx, wy), wz), 0.0, "KitShowroom_WindowStars", build_window_stars(),
                       unreal.Vector(wh, ww, 1.0))
    stars.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=-90.0, yaw=0.0), False)   # the plane's +Z to +X
    stars.static_mesh_component.set_collision_profile_name("NoCollision")
    stars.static_mesh_component.set_editor_property("cast_shadow", False)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    report["showroom"] = {"parts": counts["parts"], "lights": counts["lights"]}


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
