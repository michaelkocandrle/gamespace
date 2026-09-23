"""Import an interior piece (GLB from Blender) into Unreal and place it in the level.

    .\\Tools\\run_editor_python.ps1 Tools\\Assets\\import_interior.py

Co to dělá:

1. Naimportuje místnosti z `ArtSource/Ships/Steadfast/Interior/` (`CargoBay`, `Corridor`,
   `EngineRoom`, `Cockpit`, sklo `CockpitGlass` a křídlo dveří `DoorLeaf`) do
   `/Game/Environments/Steadfast/`. GLB i rozvržení (`Interior_layout.json`: světla, dveře, start,
   umělá gravitace) staví `Tools/Blender/build_steadfast_interior.py`. Meshe dostanou kolizi podle
   polygonů, aby se interiérem dalo chodit.
2. Postaví materiál `M_KitTrim`, který v enginu dělá totéž co `Tools/Blender/recolour_kit.py`
   v Blenderu: texturu kitu odbarví, přetónuje do gunmetalu a emisivní mapu kitu použije jako
   oranžové svítící pásy. Bez toho vypadá kit v enginu šedě a cize.
3. Na každou sadu textur (trim sheet) udělá instanci materiálu a přiřadí ji na sloty meshů.
4. Postaví to do `TestSpace` na `PLACE_AT` a uloží level.

Proč materiál znovu v enginu: přebarvení v Blenderu žije v node grafu, který GLB nepřenese.
Buď se textury vypečou (drahé, ztratí se opakovatelnost), nebo se stejná matematika udělá v
materiálu UE - tahle cesta.
"""

import json
import math
import os
import unreal

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INTERIOR = os.path.join(ROOT, "ArtSource", "Ships", "Steadfast", "Interior")
# One GLB per room, built by Tools/Blender/build_steadfast_interior.py, which also writes the layout
# (lights, doors, where the player starts, the artificial gravity box). The rooms share one origin,
# so they all stand at PLACE_AT.
ROOMS = ("CargoBay", "Corridor", "EngineRoom", "Cockpit")
GLASS = "CockpitGlass"          # its own mesh: translucent, so not Nanite
SCREENS = "CockpitScreens"      # the holograms: additive, so not Nanite either
SCREEN_PAGES = os.path.join(INTERIOR, "Screens")   # Tools/Assets/draw_holo_screens.py draws them
# Hologram look: the picture added onto the scene (black is see-through), blue-tinted, with faint
# scan lines. Strength is what bloom picks up - SC's screens glow round their edges.
HOLO_TINT = (0.75, 0.9, 1.0)
HOLO_STRENGTH = 5.0             # 3 washed out against a bright planet through the canopy
HOLO_SCANLINES = 240.0          # lines per screen height
SCREENS_TAG = "SpaceInteriorScreens"
# Meshy hero props (HANDOFF point 68): own meshes with Meshy's own PBR textures, in their own folder
# so the kit's material mapping leaves them alone.
MESHY_DIR = os.path.join(ROOT, "ArtSource", "Ships", "Steadfast", "Kitbash", "Meshy")
PROP_TAG = "SpaceInteriorProp"
# Stencil decals (HANDOFF point 69): a 4 x 4 atlas generated in Scenario (GPT Image 2.5), black =
# no paint. One deferred decal material, an instance per cell.
DECAL_ATLAS = os.path.join(INTERIOR, "Decals", "DecalAtlas_raw.png")
DECAL_TAG = "SpaceInteriorDecal"
DECAL_DEPTH_CM = 12.0
# Meshy's models face their own -Y; in Unreal (Y mirrored) that is +Y, so a prop turned by the
# layout's yaw first needs this to face +X.
MESHY_FRONT_YAW = -90.0
DOOR_LEAF = "DoorLeaf"
LAYOUT = os.path.join(INTERIOR, "Interior_layout.json")
PACKAGE = "/Game/Environments/Steadfast"
PROPS_PACKAGE = PACKAGE + "/Props"
HOLO_MATERIAL = PACKAGE + "/M_KitHolo"
LEATHER_MATERIAL = PACKAGE + "/M_KitLeather"
# Surface layers from ambientCG (CC0, ArtSource/Textures/ambientCG, Docs/AssetSources_Free.md): the kit
# has one trim sheet and a uniform finish, SC has worn paint, grime and deck plate (HANDOFF point 67).
# Projected in world space from three sides, so the kit's atlas UVs do not matter.
SURFACES = os.path.join(ROOT, "ArtSource", "Textures", "ambientCG")
SURFACE_PACKAGE = PACKAGE + "/Surfaces"
# Wear measured on 23. 9. 2026 (Tools/Shots/wear_tune.json): 0.8 with a fifth of it away from the
# edges turned whole walls into camouflage (fine detail 0.040, above SC's 0.024-0.035); half the
# strength, almost all of it on the edges, reads as SC's worn bevels at 0.027-0.030.
# Checked up close against the SC references on 23. 9. 2026 (Tools/Shots/wear_check.json): their
# painted panels read nearly clean; at 0.5 our wear showed as white chips, and on the procedural
# pieces (door jambs, lids) it landed mid-face. Now: faint, edges only, bare metal only a step
# lighter than the paint and not glossy.
WEAR_AMOUNT = 0.2               # scratches through to bare metal, on the kit's bevelled edges
WEAR_EVERYWHERE = 0.0           # how much of the wear shows away from the edges
GRIME_AMOUNT = 0.5              # blotches and dirt in the kit's cavities (its AO)
FLOOR_PLATES = 0.65             # deck plate blended over upward-facing surfaces
BARE_METAL = (0.3, 0.3, 0.31)
BARE_ROUGHNESS = 0.45
WEAR_TILE_CM = 120.0
GRIME_TILE_CM = 300.0
PLATE_TILE_CM = 100.0
MATERIAL = PACKAGE + "/M_KitTrim"
MAP = "/Game/Maps/TestSpace"
PLACE_AT = unreal.Vector(0.0, 50000.0, 0.0)      # 500 m sideways from the ship's spawn
# Blue steel. Measured on 23. 9. 2026 (Tools/Shots/interior_tune.json, HANDOFF point 59) against the
# author's mood references (cool, B/R 1.1-1.6 in sRGB): (0.62, 0.65, 0.70) under warm lights came out
# warm silver, B/R 0.95. The tint alone barely moves the hue - the light colour does most of it.
# Star Citizen style (author, 23. 9. 2026, HANDOFF point 65): the architecture is charcoal and
# warm-neutral, the colour comes from warm light strips and blue screens. Blue steel measured B/R
# 1.1-1.33 with auto exposure against SC's 0.72-1.05. A warm tint on top of warm light was too much
# (B/R 0.57-0.63, saturation 0.42-0.49); neutral metal under 5200 K gives B/R 0.70-0.76 and saturation
# 0.27-0.35, SC's own range (Tools/Shots/sc_tune.json).
GUNMETAL = (0.33, 0.33, 0.34)
BLACK = "/Engine/EngineResources/Black"
WHITE = "/Engine/EngineResources/WhiteSquareTexture"
ORANGE = (0.85, 0.34, 0.06)
# The look knobs, as material parameters so that space.Kit can try other values in the running game
# (Source/gamespace/SpaceInteriorTuning.cpp) without a repackage.
LIFT = 0.8                  # brightness of the desaturated kit texture before the tint (1.25 was chalky)
METALLIC_SCALE = 0.4        # straight off the ORM map the kit is chrome; less metal keeps the tint
ROUGHNESS_SCALE = 0.68      # roughness = floor + scale * ORM green
ROUGHNESS_FLOOR = 0.32
# Tags the console commands find the interior by: actor labels do not survive cooking.
INTERIOR_TAG = "SpaceInterior"
WORK_LIGHT_TAG = "SpaceInteriorLight_Work"
ACCENT_LIGHT_TAG = "SpaceInteriorLight_Accent"
GLASS_TAG = "SpaceInteriorGlass"
DOOR_TAG = "SpaceInteriorDoor"
SPAWN_TAG = "SpaceInteriorSpawn"       # ASpacePlayerController::ToggleInterior starts the walk here
GRAVITY_CMS2 = 981.0
# Work lights: cold white. Warm light (255, 238, 214) cancelled the blue of the steel; 7000 K is
# what turns the bay blue at all. Since the bay has a ceiling (Tools/Blender/build_steadfast_interior.py) they
# are spots under its fixtures pointing down, so the ceiling and corners stay dark - the contrast
# the mood references have and the open bay did not.
# Measured with the ceiling on (Tools/Shots/ceiling_tune.json, HANDOFF point 60): 575 lm under a
# 65-degree cone left the walls nearly black (mean 0.21 against the references' 0.24-0.42); a wider
# cone reaches the walls and 1150 lm lifts them, while 1800 already burns the floor out (p90 0.83).
WORK_LIGHT_LUMENS = 1150.0
WORK_LIGHT_KELVIN = 5200.0          # warm white, as SC's corridors (7000 K belonged to the blue look)
WORK_LIGHT_CONE = (25.0, 80.0)      # inner, outer half angle in degrees
# The orange accents: at 550 lm they painted the whole ceiling brown (B/R 0.93 looking up). Once they
# stood inside the rooms rather than behind the bay's walls, 200 lm still warmed the bay and engine
# room to B/R 0.97-1.11; 100 lm keeps every view at 1.10-1.26 and the orange spots still read
# (Tools/Shots/accent_tune.json; 50 lm all but lost them).
ACCENT_LIGHT_LUMENS = 100.0
# Performance (Tools/Shots/perf_interior.json, HANDOFF point 63): shadows of the 22 local lights were
# most of the frame - 15.3 ms in the bay, 9.9 with none. The small orange and blue fills cast none
# (no visible loss), and the work lights reach 4.5 m instead of 9, so each no longer renders the
# shadows of the rooms next door: 11.5 ms, with the crates' and columns' shadows kept.
WORK_LIGHT_RADIUS = 450.0
# The fixtures' glowing face: cold white, not the kit's orange.
LAMP_COLOUR = (1.0, 0.9, 0.75)
LAMP_STRENGTH = 20.0
# Cockpit displays: blue, and a blue light off them (the holo-blue screens of the mood references).
SCREEN_COLOUR = (0.15, 0.55, 1.0)
SCREEN_STRENGTH = 1.5          # 6 burnt the displays out to white at exposure 2 (HANDOFF point 63)
SCREEN_LIGHT = unreal.Color(r=90, g=170, b=255, a=255)
GLASS_MATERIAL = PACKAGE + "/M_KitGlass"
# Light strips: warm white and hot enough to bloom - SC's highlights (p99 0.56-0.88) come from them.
STRIP_COLOUR = (1.0, 0.8, 0.58)
STRIP_STRENGTH = 14.0


def read_layout():
    """Interior_layout.json as the builder wrote it: rooms (work, accent, screen lights), doors,
    spawn, gravity box - Blender metres."""
    with open(LAYOUT, encoding="utf-8") as source:
        return json.load(source)


def yaw_of(direction):
    """Unreal yaw (degrees) of a direction given in Blender axes (Y mirrored)."""
    return math.degrees(math.atan2(-direction[1], direction[0]))


def to_unreal(point):
    """Blender metres to Unreal centimetres at PLACE_AT: X and Z shared, Y mirrored."""
    return unreal.Vector(PLACE_AT.x + point[0] * 100.0, PLACE_AT.y - point[1] * 100.0, PLACE_AT.z + point[2] * 100.0)


MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary


def log(message):
    unreal.log("import_interior: %s" % message)


def node(material, cls, x, y, **properties):
    expression = MEL.create_material_expression(material, cls, x, y)
    for key, value in properties.items():
        expression.set_editor_property(key, value)
    return expression


def link(src, dst, dst_input, src_output=""):
    if not MEL.connect_material_expressions(src, src_output, dst, dst_input):
        raise RuntimeError("nelze spojit %s -> %s.%s" % (src.get_class().get_name(), dst.get_class().get_name(), dst_input))


def import_surfaces():
    """The ambientCG maps, with the compression each sampler type needs (WORKFLOW 9.3 f)."""
    tasks = []
    for folder in sorted(os.listdir(SURFACES)):
        for name in sorted(os.listdir(os.path.join(SURFACES, folder))):
            task = unreal.AssetImportTask()
            task.filename = os.path.join(SURFACES, folder, name)
            task.destination_path = SURFACE_PACKAGE
            task.destination_name = name.replace("_2K-JPG", "").replace(".jpg", "")
            task.automated = True
            task.replace_existing = True
            task.save = True
            tasks.append(task)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    textures = {}
    for task in tasks:
        for path in task.get_editor_property("imported_object_paths") or []:
            texture = EAL.load_asset(path)
            if not isinstance(texture, unreal.Texture2D):
                continue
            name = texture.get_name()
            if name.endswith("_NormalDX"):
                texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
                texture.set_editor_property("srgb", False)
            elif not name.endswith("_Color"):
                texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
                texture.set_editor_property("srgb", False)
            EAL.save_loaded_asset(texture, only_if_is_dirty=False)
            textures[name] = texture
    log("povrchy ambientCG: %d textur" % len(textures))
    return textures


def sample(material, texture, uv, x, y, kind="color"):
    """A plain texture sample of `texture` at `uv`, sampler type matching its compression."""
    s = node(material, unreal.MaterialExpressionTextureSample, x, y, texture=texture)
    s.set_editor_property("sampler_type", {"color": unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
                                           "normal": unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
                                           "mask": unreal.MaterialSamplerType.SAMPLERTYPE_MASKS}[kind])
    link(uv, s, "UVs")
    return s


def triplanar(material, texture, tile_cm, weights, x, y, kind="mask", channel="R"):
    """`texture` projected along world X, Y and Z and blended by how much the surface faces each."""
    world = node(material, unreal.MaterialExpressionWorldPosition, x - 700, y)
    scaled = node(material, unreal.MaterialExpressionDivide, x - 560, y)
    link(world, scaled, "A")
    link(node(material, unreal.MaterialExpressionConstant, x - 700, y + 80, r=tile_cm), scaled, "B")
    parts = []
    for i, (mask, weight) in enumerate(((dict(r=False, g=True, b=True, a=False), "R"),      # along X: YZ
                                        (dict(r=True, g=False, b=True, a=False), "G"),      # along Y: XZ
                                        (dict(r=True, g=True, b=False, a=False), "B"))):    # along Z: XY
        uv = node(material, unreal.MaterialExpressionComponentMask, x - 420, y + i * 120, **mask)
        link(scaled, uv, "")
        s = sample(material, texture, uv, x - 260, y + i * 120, kind)
        w = node(material, unreal.MaterialExpressionComponentMask, x - 260, y + 60 + i * 120,
                 r=weight == "R", g=weight == "G", b=weight == "B", a=False)
        link(weights, w, "")
        part = node(material, unreal.MaterialExpressionMultiply, x - 100, y + i * 120)
        link(s, part, "A", channel if kind == "mask" else "RGB")
        link(w, part, "B")
        parts.append(part)
    sum1 = node(material, unreal.MaterialExpressionAdd, x, y)
    link(parts[0], sum1, "A")
    link(parts[1], sum1, "B")
    total = node(material, unreal.MaterialExpressionAdd, x + 120, y)
    link(sum1, total, "A")
    link(parts[2], total, "B")
    return total


def lerp(material, a, b, alpha, x, y):
    l = node(material, unreal.MaterialExpressionLinearInterpolate, x, y)
    link(a, l, "A")
    link(b, l, "B")
    link(alpha, l, "Alpha")
    return l


def const(material, value, x, y):
    if isinstance(value, tuple):
        return node(material, unreal.MaterialExpressionConstant3Vector, x, y,
                    constant=unreal.LinearColor(value[0], value[1], value[2], 1.0))
    return node(material, unreal.MaterialExpressionConstant, x, y, r=value)


def binary(material, cls, a, b, x, y):
    n = node(material, cls, x, y)
    first, second = ("Base", "Exp") if cls is unreal.MaterialExpressionPower else ("A", "B")
    link(a, n, first)
    link(b, n, second)
    return n


def build_master(defaults, surfaces=None):
    """The palette, as a material: desaturate, tint to gunmetal, orange emissive from the kit's map.

    `defaults` are the textures the sampler nodes fall back to when an instance binds nothing. They
    matter more than they look: an unbound sampler falls back to the engine's sRGB DefaultTexture,
    whose type does not match a Normal or Linear Color sampler, and the material then fails to
    compile for the cooked platform - the whole bay came out wrapped in WorldGridMaterial's
    checkerboard (23. 9. 2026).
    """
    if EAL.does_asset_exist(MATERIAL):
        EAL.delete_asset(MATERIAL)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    material = tools.create_asset("M_KitTrim", PACKAGE, unreal.Material, unreal.MaterialFactoryNew())

    base = node(material, unreal.MaterialExpressionTextureSampleParameter2D, -900, -200, parameter_name="BaseColor")
    normal = node(material, unreal.MaterialExpressionTextureSampleParameter2D, -900, 200, parameter_name="NormalMap")
    normal.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    orm = node(material, unreal.MaterialExpressionTextureSampleParameter2D, -900, 500, parameter_name="ORMMap")
    orm.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
    # The emissive mask stays a plain Color sampler, so that a black or white engine texture can
    # stand in for it without a sampler type mismatch.
    emissive = node(material, unreal.MaterialExpressionTextureSampleParameter2D, -900, 800, parameter_name="EmissiveMap")
    for sampler, parameter in ((base, "BaseColor"), (normal, "NormalMap"), (orm, "ORMMap")):
        if defaults.get(parameter):
            sampler.set_editor_property("texture", defaults[parameter])
    emissive.set_editor_property("texture", EAL.load_asset(BLACK))

    # gunmetal: the kit's own drawing, drained of colour and tinted
    grey = node(material, unreal.MaterialExpressionDesaturation, -600, -200)
    link(base, grey, "")
    lift = node(material, unreal.MaterialExpressionMultiply, -430, -200)
    link(grey, lift, "A")
    link(node(material, unreal.MaterialExpressionScalarParameter, -600, -60, parameter_name="Lift",
              default_value=LIFT), lift, "B")
    tint = node(material, unreal.MaterialExpressionMultiply, -260, -200)
    link(lift, tint, "A")
    link(node(material, unreal.MaterialExpressionVectorParameter, -430, -40, parameter_name="Gunmetal",
              default_value=unreal.LinearColor(GUNMETAL[0], GUNMETAL[1], GUNMETAL[2], 1.0)), tint, "B")

    # orange accent from the kit's emissive strips
    accent = node(material, unreal.MaterialExpressionVectorParameter, -600, 800, parameter_name="Accent",
                  default_value=unreal.LinearColor(ORANGE[0], ORANGE[1], ORANGE[2], 1.0))
    glow = node(material, unreal.MaterialExpressionMultiply, -350, 820)
    link(accent, glow, "A")
    link(emissive, glow, "B")
    hot = node(material, unreal.MaterialExpressionMultiply, -200, 820)
    link(glow, hot, "A")
    link(node(material, unreal.MaterialExpressionScalarParameter, -350, 960, parameter_name="AccentStrength",
              default_value=9.0), hot, "B")

    albedo_out, normal_out = tint, normal
    wear = grime = floor = plate_rough = None
    if surfaces:
        # Which way the surface faces, as blend weights for the world projections: |N|^4, normalised.
        n = node(material, unreal.MaterialExpressionVertexNormalWS, -2600, 1300)
        absn = node(material, unreal.MaterialExpressionAbs, -2450, 1300)
        link(n, absn, "")
        sharp = binary(material, unreal.MaterialExpressionPower, absn, const(material, 4.0, -2450, 1380), -2300, 1300)
        total = node(material, unreal.MaterialExpressionDotProduct, -2150, 1380)
        link(sharp, total, "A")
        link(const(material, (1.0, 1.0, 1.0), -2300, 1460), total, "B")
        weights = binary(material, unreal.MaterialExpressionDivide, sharp, total, -2000, 1300)
        # Scratches (PaintedMetal004's metalness is exactly where the paint is worn through), strongest
        # on the kit's bevels - where its normal map leans away from flat.
        scratch = triplanar(material, surfaces["PaintedMetal004_Metalness"], WEAR_TILE_CM, weights, -1400, 1300)
        nb = node(material, unreal.MaterialExpressionComponentMask, -1400, 1700, r=False, g=False, b=True, a=False)
        link(normal, nb, "")
        edge = node(material, unreal.MaterialExpressionOneMinus, -1250, 1700)
        link(nb, edge, "")
        edge8 = binary(material, unreal.MaterialExpressionMultiply, edge, const(material, 8.0, -1250, 1780), -1100, 1700)
        edge_sat = node(material, unreal.MaterialExpressionSaturate, -950, 1700)
        link(edge8, edge_sat, "")
        everywhere = node(material, unreal.MaterialExpressionScalarParameter, -950, 1780, parameter_name="WearEverywhere",
                          default_value=WEAR_EVERYWHERE)
        edge_bias = lerp(material, everywhere, const(material, 1.0, -950, 1860), edge_sat, -800, 1700)
        wear_raw = binary(material, unreal.MaterialExpressionMultiply, scratch, edge_bias, -650, 1300)
        wear_amt = node(material, unreal.MaterialExpressionScalarParameter, -650, 1400, parameter_name="WearAmount",
                        default_value=WEAR_AMOUNT)
        wear = binary(material, unreal.MaterialExpressionMultiply, wear_raw, wear_amt, -500, 1300)
        # Grime: large blotches (PaintedMetal013's occlusion) plus the kit's own cavities.
        blotch = triplanar(material, surfaces["PaintedMetal013_AmbientOcclusion"], GRIME_TILE_CM, weights, -1400, 2000)
        blotch_inv = node(material, unreal.MaterialExpressionOneMinus, -1100, 2000)
        link(blotch, blotch_inv, "")
        cavity = node(material, unreal.MaterialExpressionOneMinus, -1100, 2100)
        link(orm, cavity, "", "R")
        grime_sum = binary(material, unreal.MaterialExpressionAdd, blotch_inv, cavity, -950, 2000)
        grime_amt = node(material, unreal.MaterialExpressionScalarParameter, -950, 2100, parameter_name="GrimeAmount",
                         default_value=GRIME_AMOUNT)
        grime_raw = binary(material, unreal.MaterialExpressionMultiply, grime_sum, grime_amt, -800, 2000)
        grime = node(material, unreal.MaterialExpressionSaturate, -650, 2000)
        link(grime_raw, grime, "")
        # Deck plate on everything that faces up.
        nz = node(material, unreal.MaterialExpressionComponentMask, -1400, 2400, r=False, g=False, b=True, a=False)
        link(n, nz, "")
        up = binary(material, unreal.MaterialExpressionSubtract, nz, const(material, 0.8, -1400, 2480), -1250, 2400)
        up5 = binary(material, unreal.MaterialExpressionMultiply, up, const(material, 5.0, -1250, 2480), -1100, 2400)
        up_sat = node(material, unreal.MaterialExpressionSaturate, -950, 2400)
        link(up5, up_sat, "")
        plates_amt = node(material, unreal.MaterialExpressionScalarParameter, -950, 2480, parameter_name="FloorPlates",
                          default_value=FLOOR_PLATES)
        floor = binary(material, unreal.MaterialExpressionMultiply, up_sat, plates_amt, -800, 2400)
        world = node(material, unreal.MaterialExpressionWorldPosition, -1700, 2700)
        top = node(material, unreal.MaterialExpressionComponentMask, -1550, 2700, r=True, g=True, b=False, a=False)
        link(world, top, "")
        top_uv = binary(material, unreal.MaterialExpressionDivide, top, const(material, PLATE_TILE_CM, -1550, 2780), -1400, 2700)
        plate_col = sample(material, surfaces["MetalPlates006_Color"], top_uv, -1250, 2700, "color")
        plate_nrm = sample(material, surfaces["MetalPlates006_NormalDX"], top_uv, -1250, 2850, "normal")
        plate_rgh = sample(material, surfaces["MetalPlates006_Roughness"], top_uv, -1250, 3000, "mask")
        plate_grey = node(material, unreal.MaterialExpressionDesaturation, -1100, 2700)
        link(plate_col, plate_grey, "")
        plate_tone = binary(material, unreal.MaterialExpressionMultiply, plate_grey,
                            node(material, unreal.MaterialExpressionVectorParameter, -1100, 2780, parameter_name="PlateTint",
                                 default_value=unreal.LinearColor(0.9, 0.9, 0.92, 1.0)), -950, 2700)
        plated = lerp(material, tint, plate_tone, floor, -800, 2700)
        worn_paint = lerp(material, plated, const(material, BARE_METAL, -650, 2800), wear, -500, 2700)
        dirt = binary(material, unreal.MaterialExpressionMultiply, grime, const(material, 0.35, -500, 2880), -350, 2800)
        clean = node(material, unreal.MaterialExpressionOneMinus, -200, 2800)
        link(dirt, clean, "")
        albedo_out = binary(material, unreal.MaterialExpressionMultiply, worn_paint, clean, -50, 2700)
        blended_n = lerp(material, normal, plate_nrm, floor, -800, 2900)
        normal_out = node(material, unreal.MaterialExpressionNormalize, -650, 2900)
        link(blended_n, normal_out, "")
        plate_rough = plate_rgh
    MEL.connect_material_property(albedo_out, "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(normal_out, "", unreal.MaterialProperty.MP_NORMAL)
    # Straight off the ORM map the kit is chrome: metal everywhere, and polished. Pull the metal
    # back a little and put a floor under the roughness, or the bay mirrors the work lights.
    metal = node(material, unreal.MaterialExpressionMultiply, -600, 560)
    link(orm, metal, "A", "B")
    link(node(material, unreal.MaterialExpressionScalarParameter, -760, 640, parameter_name="MetallicScale",
              default_value=METALLIC_SCALE), metal, "B")
    worn = node(material, unreal.MaterialExpressionMultiply, -600, 420)
    link(orm, worn, "A", "G")
    link(node(material, unreal.MaterialExpressionScalarParameter, -760, 470, parameter_name="RoughnessScale",
              default_value=ROUGHNESS_SCALE), worn, "B")
    rough = node(material, unreal.MaterialExpressionAdd, -440, 420)
    link(worn, rough, "A")
    link(node(material, unreal.MaterialExpressionScalarParameter, -600, 340, parameter_name="RoughnessFloor",
              default_value=ROUGHNESS_FLOOR), rough, "B")

    rough_out, metal_out = rough, metal
    if surfaces:
        on_plate = lerp(material, rough, plate_rough, floor, -300, 3100)
        on_wear = lerp(material, on_plate, const(material, BARE_ROUGHNESS, -300, 3200), wear, -150, 3100)
        rough_out = binary(material, unreal.MaterialExpressionAdd, on_wear,
                           binary(material, unreal.MaterialExpressionMultiply, grime, const(material, 0.15, -300, 3300), -150, 3300),
                           0, 3100)
        metal_out = lerp(material, metal, const(material, 1.0, -300, 3400), wear, -150, 3400)
    MEL.connect_material_property(rough_out, "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(metal_out, "", unreal.MaterialProperty.MP_METALLIC)
    MEL.connect_material_property(orm, "R", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.connect_material_property(hot, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    # Nanite is on for imported meshes, and a material without the matching usage flag cannot
    # compile in a cooked build - the engine silently swaps in WorldGridMaterial, which is the
    # grey checkerboard the bay was covered in (23. 9. 2026). The editor sets the flag on demand
    # when you drop the material on a mesh; a script has to set it itself.
    for usage in ("used_with_nanite", "used_with_static_mesh", "used_with_instanced_static_meshes"):
        material.set_editor_property(usage, True)
    MEL.recompile_material(material)
    EAL.save_loaded_asset(material, only_if_is_dirty=False)
    log("materiál %s hotov" % MATERIAL)
    return material


def import_mesh():
    # A clean slate: an earlier run of this script left 67 separate meshes behind.
    if EAL.does_directory_exist(PACKAGE):
        for path in EAL.list_assets(PACKAGE, recursive=True, include_folder=False):
            EAL.delete_asset(path)
    tasks = []
    for room in ROOMS + (GLASS, SCREENS, DOOR_LEAF):
        task = unreal.AssetImportTask()
        task.filename = os.path.join(INTERIOR, room + ".glb")
        task.destination_path = PACKAGE
        task.automated = True
        task.replace_existing = True
        task.save = True
        tasks.append(task)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    imported = [path for task in tasks for path in (task.get_editor_property("imported_object_paths") or [])]
    log("naimportováno %d objektů z %d souborů" % (len(imported), len(tasks)))
    return imported


def make_plain(master, name, base, textures, emissive=None, strength=0.0, glow=False):
    """The kit's plain slots: black plastic, and the glowing strips.

    They still borrow a trim sheet's maps - a material instance with no texture bound renders the
    engine checkerboard, including through roughness and metallic.
    """
    path = "%s/%s" % (PACKAGE, name)
    if EAL.does_asset_exist(path):
        EAL.delete_asset(path)
    instance = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, PACKAGE, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(instance, master)
    for parameter, texture in textures.items():
        MEL.set_material_instance_texture_parameter_value(instance, parameter, texture)
    MEL.set_material_instance_texture_parameter_value(
        instance, "EmissiveMap", EAL.load_asset(WHITE if glow else BLACK))
    MEL.set_material_instance_vector_parameter_value(instance, "Gunmetal", unreal.LinearColor(base[0], base[1], base[2], 1.0))
    if emissive:
        MEL.set_material_instance_vector_parameter_value(instance, "Accent", unreal.LinearColor(emissive[0], emissive[1], emissive[2], 1.0))
    MEL.set_material_instance_scalar_parameter_value(instance, "AccentStrength", strength)
    EAL.save_loaded_asset(instance, only_if_is_dirty=False)
    return instance


def texture_sets():
    """Kit textures land next to the mesh; group them by trim sheet."""
    sets = {}
    for path in EAL.list_assets(PACKAGE, recursive=True, include_folder=False):
        asset = EAL.load_asset(path)
        if not isinstance(asset, unreal.Texture2D):
            continue
        name = asset.get_name()
        stem = name.split("_BaseColor")[0].split("_Normal")[0].split("_ORM")[0].split("_Emissive")[0]
        entry = sets.setdefault(stem, {})
        if "BaseColor" in name:
            entry["BaseColor"] = asset
        elif "Normal" in name:
            asset.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
            entry["NormalMap"] = asset
        elif "ORM" in name:
            entry["ORMMap"] = asset
        elif "Emissive" in name:
            entry["EmissiveMap"] = asset
    return sets


def prune(keep):
    """Throw away what the import brought along and nothing uses.

    glTF import makes its own material instance per slot and re-imports the same trim sheet once
    per material - seven copies of the same 2048 texture. Unreferenced, but they would still go
    into git LFS (84 MB on the first pass, 23. 9. 2026).
    """
    names = {asset.get_path_name().split(".")[0] for asset in keep if asset}
    removed = 0
    for path in EAL.list_assets(PACKAGE, recursive=True, include_folder=False):
        if path.split(".")[0] in names:
            continue
        if EAL.delete_asset(path):
            removed += 1
    log("uklizeno %d nepoužitých assetů" % removed)


def place_lights(actors):
    """Work lights under every ceiling fixture, and the orange accents, room by room.

    The kit's panels are metal in the ORM map, and metal with nothing to reflect renders black -
    in space there is no sky to fill it in. Without these the bay is a silhouette (23. 9. 2026).
    """
    for actor in actors.get_all_level_actors():
        if actor.get_actor_label().startswith("Steadfast_Light"):
            actors.destroy_actor(actor)
    lights = 0
    rooms = read_layout()["rooms"]
    for room, layout in ((name, rooms[name]) for name in ROOMS):
        for point in layout["work"]:
            # 20 cm under the ceiling, pointing straight down.
            spot = to_unreal(point) - unreal.Vector(0.0, 0.0, 20.0)
            light = actors.spawn_actor_from_class(unreal.SpotLight, spot, unreal.Rotator(roll=0.0, pitch=-90.0, yaw=0.0))
            lights += 1
            light.set_actor_label("Steadfast_Light_Work_%s_%d" % (room, lights))
            light.set_editor_property("tags", [unreal.Name(WORK_LIGHT_TAG)])
            component = light.spot_light_component
            component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
            component.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
            component.set_editor_property("intensity", WORK_LIGHT_LUMENS)
            component.set_editor_property("attenuation_radius", WORK_LIGHT_RADIUS)
            component.set_editor_property("inner_cone_angle", WORK_LIGHT_CONE[0])
            component.set_editor_property("outer_cone_angle", WORK_LIGHT_CONE[1])
            component.set_editor_property("light_color", unreal.Color(r=255, g=255, b=255, a=255))
            component.set_editor_property("use_temperature", True)
            component.set_editor_property("temperature", WORK_LIGHT_KELVIN)
        for point in layout["accent"]:
            light = actors.spawn_actor_from_class(unreal.PointLight, to_unreal(point), unreal.Rotator(0, 0, 0))
            lights += 1
            light.set_actor_label("Steadfast_Light_Accent_%s_%d" % (room, lights))
            light.set_editor_property("tags", [unreal.Name(ACCENT_LIGHT_TAG)])
            component = light.point_light_component
            component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
            component.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
            component.set_editor_property("intensity", ACCENT_LIGHT_LUMENS)
            component.set_editor_property("attenuation_radius", 600.0)
            component.set_editor_property("cast_shadows", False)
            component.set_editor_property("light_color", unreal.Color(r=255, g=140, b=40, a=255))
        for point in layout.get("screen", []):
            light = actors.spawn_actor_from_class(unreal.PointLight, to_unreal(point), unreal.Rotator(0, 0, 0))
            lights += 1
            light.set_actor_label("Steadfast_Light_Screen_%s_%d" % (room, lights))
            light.set_editor_property("tags", [unreal.Name(ACCENT_LIGHT_TAG)])
            component = light.point_light_component
            component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
            component.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
            component.set_editor_property("intensity", ACCENT_LIGHT_LUMENS)
            component.set_editor_property("attenuation_radius", 350.0)
            component.set_editor_property("cast_shadows", False)
            component.set_editor_property("light_color", SCREEN_LIGHT)
    log("rozsvíceno %d světel" % lights)


def build_glass():
    """Cockpit glass: translucent, two-sided, a faint blue tint and a sharp reflection."""
    if EAL.does_asset_exist(GLASS_MATERIAL):
        EAL.delete_asset(GLASS_MATERIAL)
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        GLASS_MATERIAL.split("/")[-1], PACKAGE, unreal.Material, unreal.MaterialFactoryNew())
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    material.set_editor_property("two_sided", True)
    material.set_editor_property("translucency_lighting_mode", unreal.TranslucencyLightingMode.TLM_SURFACE)
    material.set_editor_property("used_with_static_mesh", True)
    tint = node(material, unreal.MaterialExpressionConstant3Vector, -400, -100, constant=unreal.LinearColor(0.55, 0.68, 0.8, 1.0))
    MEL.connect_material_property(tint, "", unreal.MaterialProperty.MP_BASE_COLOR)
    for value, prop, y in ((0.1, unreal.MaterialProperty.MP_OPACITY, 50), (0.05, unreal.MaterialProperty.MP_ROUGHNESS, 150),
                           (0.8, unreal.MaterialProperty.MP_SPECULAR, 250), (0.0, unreal.MaterialProperty.MP_METALLIC, 350)):
        MEL.connect_material_property(node(material, unreal.MaterialExpressionConstant, -400, y, r=value), "", prop)
    MEL.recompile_material(material)
    EAL.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def import_pages():
    """The hologram pictures as textures, {page: texture}."""
    tasks = []
    for name in sorted(os.listdir(SCREEN_PAGES)):
        if not name.endswith(".png"):
            continue
        task = unreal.AssetImportTask()
        task.filename = os.path.join(SCREEN_PAGES, name)
        task.destination_path = PACKAGE + "/Screens"
        task.automated = True
        task.replace_existing = True
        task.save = True
        tasks.append(task)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    pages = {}
    for task in tasks:
        for path in task.get_editor_property("imported_object_paths") or []:
            texture = EAL.load_asset(path)
            if isinstance(texture, unreal.Texture2D):
                pages[texture.get_name().replace("Holo_", "")] = texture
    return pages


def build_holo(default_page):
    """The hologram master: additive, unlit, two-sided; picture x tint x strength x scan lines."""
    if EAL.does_asset_exist(HOLO_MATERIAL):
        EAL.delete_asset(HOLO_MATERIAL)
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        HOLO_MATERIAL.split("/")[-1], PACKAGE, unreal.Material, unreal.MaterialFactoryNew())
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    material.set_editor_property("two_sided", True)
    material.set_editor_property("used_with_static_mesh", True)
    page = node(material, unreal.MaterialExpressionTextureSampleParameter2D, -900, -100, parameter_name="Page")
    page.set_editor_property("texture", default_page)       # a sampler never without a texture (WORKFLOW 9.3 f)
    tint = node(material, unreal.MaterialExpressionVectorParameter, -900, 150, parameter_name="Tint",
                default_value=unreal.LinearColor(HOLO_TINT[0], HOLO_TINT[1], HOLO_TINT[2], 1.0))
    strength = node(material, unreal.MaterialExpressionScalarParameter, -900, 300, parameter_name="Strength",
                    default_value=HOLO_STRENGTH)
    uv = node(material, unreal.MaterialExpressionTextureCoordinate, -1100, 450)
    v = node(material, unreal.MaterialExpressionComponentMask, -950, 450, r=False, g=True, b=False, a=False)
    link(uv, v, "")
    lines = node(material, unreal.MaterialExpressionMultiply, -800, 450)
    link(v, lines, "A")
    link(node(material, unreal.MaterialExpressionConstant, -950, 550, r=HOLO_SCANLINES * 6.2832), lines, "B")
    wave = node(material, unreal.MaterialExpressionSine, -650, 450)
    link(lines, wave, "")
    ripple = node(material, unreal.MaterialExpressionMultiply, -500, 450)
    link(wave, ripple, "A")
    link(node(material, unreal.MaterialExpressionConstant, -650, 550, r=0.12), ripple, "B")
    scan = node(material, unreal.MaterialExpressionAdd, -350, 450)
    link(ripple, scan, "A")
    link(node(material, unreal.MaterialExpressionConstant, -500, 550, r=0.88), scan, "B")
    lit = node(material, unreal.MaterialExpressionMultiply, -600, 0)
    link(page, lit, "A", "RGB")
    link(tint, lit, "B")
    hot = node(material, unreal.MaterialExpressionMultiply, -400, 0)
    link(lit, hot, "A")
    link(strength, hot, "B")
    out = node(material, unreal.MaterialExpressionMultiply, -200, 100)
    link(hot, out, "A")
    link(scan, out, "B")
    MEL.connect_material_property(out, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(material)
    EAL.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def make_holo(master, page_name, texture):
    path = "%s/MI_Holo_%s" % (PACKAGE, page_name)
    if EAL.does_asset_exist(path):
        EAL.delete_asset(path)
    instance = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "MI_Holo_%s" % page_name, PACKAGE, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(instance, master)
    MEL.set_material_instance_texture_parameter_value(instance, "Page", texture)
    EAL.save_loaded_asset(instance, only_if_is_dirty=False)
    return instance


def build_leather(surfaces):
    """Black leather for the pilot seats: ambientCG Leather033A drained of its brown."""
    if EAL.does_asset_exist(LEATHER_MATERIAL):
        EAL.delete_asset(LEATHER_MATERIAL)
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        LEATHER_MATERIAL.split("/")[-1], PACKAGE, unreal.Material, unreal.MaterialFactoryNew())
    uv0 = node(material, unreal.MaterialExpressionTextureCoordinate, -900, 0, u_tiling=4.0, v_tiling=4.0)
    col = sample(material, surfaces["Leather033A_Color"], uv0, -700, 0, "color")
    nrm = sample(material, surfaces["Leather033A_NormalDX"], uv0, -700, 200, "normal")
    rgh = sample(material, surfaces["Leather033A_Roughness"], uv0, -700, 400, "mask")
    grey = node(material, unreal.MaterialExpressionDesaturation, -500, 0)
    link(col, grey, "")
    dark = binary(material, unreal.MaterialExpressionMultiply, grey, const(material, 0.12, -500, 80), -350, 0)
    MEL.connect_material_property(dark, "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(nrm, "", unreal.MaterialProperty.MP_NORMAL)
    soft = binary(material, unreal.MaterialExpressionMultiply, rgh, const(material, 0.85, -500, 480), -350, 400)
    MEL.connect_material_property(soft, "R", unreal.MaterialProperty.MP_ROUGHNESS)
    for usage in ("used_with_nanite", "used_with_static_mesh"):
        material.set_editor_property(usage, True)
    MEL.recompile_material(material)
    EAL.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def place_props(actors):
    """Import the Meshy props the layout asks for and stand them on the floor, scaled uniformly to
    their width, turned to face where the layout says."""
    for actor in actors.get_all_level_actors():
        if actor.get_actor_label().startswith("Steadfast_Prop"):
            actors.destroy_actor(actor)
    wanted = sorted({p["mesh"] for p in read_layout().get("props", [])})
    tasks = []
    for name in wanted:
        task = unreal.AssetImportTask()
        task.filename = os.path.join(MESHY_DIR, name + ".glb")
        task.destination_path = PROPS_PACKAGE + "/" + name
        task.automated = True
        task.replace_existing = True
        task.save = True
        tasks.append(task)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    meshes = {}
    for name, task in zip(wanted, tasks):
        for path in task.get_editor_property("imported_object_paths") or []:
            asset = EAL.load_asset(path)
            if isinstance(asset, unreal.StaticMesh):
                meshes[name] = asset
                collide_per_polygon(asset)
                EAL.save_loaded_asset(asset, only_if_is_dirty=False)
    count = 0
    for index, prop in enumerate(read_layout().get("props", [])):
        mesh = meshes.get(prop["mesh"])
        if not mesh:
            log("VAROVÁNÍ: Meshy díl %s chybí" % prop["mesh"])
            continue
        box = mesh.get_bounding_box()
        scale = prop["width"] * 100.0 / max(box.max.x - box.min.x, 1.0)
        yaw = MESHY_FRONT_YAW - prop["yaw"]                       # Blender yaw -> Unreal (Y mirrored)
        centre = unreal.Vector((box.min.x + box.max.x) / 2.0 * scale, (box.min.y + box.max.y) / 2.0 * scale, 0.0)
        c, si = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        turned = unreal.Vector(centre.x * c - centre.y * si, centre.x * si + centre.y * c, 0.0)
        spot = to_unreal(prop["at"]) - turned + unreal.Vector(0.0, 0.0, -box.min.z * scale)
        actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, spot, unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw))
        actor.set_actor_label("Steadfast_Prop_%s_%d" % (prop["mesh"], index))
        actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
        actor.set_editor_property("tags", [unreal.Name(PROP_TAG)])
        component = actor.static_mesh_component
        component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
        component.set_static_mesh(mesh)
        count += 1
    log("Meshy díly: %d (%s)" % (count, ", ".join(wanted)))
    return count


def build_decal_material():
    """Deferred decal: the atlas cell's colour, opacity from how bright it is (black = no paint)."""
    task = unreal.AssetImportTask()
    task.filename = DECAL_ATLAS
    task.destination_path = PACKAGE + "/Decals"
    task.destination_name = "T_DecalAtlas"
    task.automated = True
    task.replace_existing = True
    task.save = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    atlas = EAL.load_asset(PACKAGE + "/Decals/T_DecalAtlas")
    path = PACKAGE + "/Decals/M_Decal"
    if EAL.does_asset_exist(path):
        EAL.delete_asset(path)
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset("M_Decal", PACKAGE + "/Decals", unreal.Material,
                                                                      unreal.MaterialFactoryNew())
    material.set_editor_property("material_domain", unreal.MaterialDomain.MD_DEFERRED_DECAL)
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    uv = node(material, unreal.MaterialExpressionTextureCoordinate, -1200, 0)
    quarter = binary(material, unreal.MaterialExpressionMultiply, uv, const(material, 0.25, -1200, 100), -1050, 0)
    cu = node(material, unreal.MaterialExpressionScalarParameter, -1200, 200, parameter_name="CellU", default_value=0.0)
    cv = node(material, unreal.MaterialExpressionScalarParameter, -1200, 300, parameter_name="CellV", default_value=0.0)
    cell = node(material, unreal.MaterialExpressionAppendVector, -1050, 250)
    link(cu, cell, "A")
    link(cv, cell, "B")
    offset = binary(material, unreal.MaterialExpressionMultiply, cell, const(material, 0.25, -1050, 350), -900, 250)
    cell_uv = binary(material, unreal.MaterialExpressionAdd, quarter, offset, -750, 100)
    tex = node(material, unreal.MaterialExpressionTextureSampleParameter2D, -600, 100, parameter_name="Atlas", texture=atlas)
    link(cell_uv, tex, "UVs")
    level = node(material, unreal.MaterialExpressionDesaturation, -300, 300)
    link(tex, level, "", "RGB")
    lifted = binary(material, unreal.MaterialExpressionSubtract, level, const(material, 0.12, -300, 400), -150, 300)
    steep = binary(material, unreal.MaterialExpressionMultiply, lifted, const(material, 4.0, -150, 400), 0, 300)
    alpha = node(material, unreal.MaterialExpressionSaturate, 150, 300)
    link(steep, alpha, "")
    strength = node(material, unreal.MaterialExpressionScalarParameter, 150, 400, parameter_name="Opacity", default_value=0.85)
    opacity = binary(material, unreal.MaterialExpressionMultiply, alpha, strength, 300, 300)
    # The paint a little darker than the atlas: stencils on a dim ship, not stickers under a lamp.
    paint = binary(material, unreal.MaterialExpressionMultiply, tex, const(material, 0.7, -400, 0), -200, 0)
    MEL.connect_material_property(paint, "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(opacity, "", unreal.MaterialProperty.MP_OPACITY)
    MEL.connect_material_property(const(material, 0.55, 0, 500), "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(material)
    EAL.save_loaded_asset(material, only_if_is_dirty=False)
    return material, atlas


def place_decals(actors, material):
    """A decal actor per layout entry, projecting into the surface it names."""
    for actor in actors.get_all_level_actors():
        if actor.get_actor_label().startswith("Steadfast_Decal"):
            actors.destroy_actor(actor)
    instances = {}
    kept = []
    for index, decal in enumerate(read_layout().get("decals", [])):
        cell = decal["cell"]
        if cell not in instances:
            path = "%s/Decals/MI_Decal_%02d" % (PACKAGE, cell)
            if EAL.does_asset_exist(path):
                EAL.delete_asset(path)
            instance = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
                "MI_Decal_%02d" % cell, PACKAGE + "/Decals", unreal.MaterialInstanceConstant,
                unreal.MaterialInstanceConstantFactoryNew())
            MEL.set_material_instance_parent(instance, material)
            MEL.set_material_instance_scalar_parameter_value(instance, "CellU", float(cell % 4))
            MEL.set_material_instance_scalar_parameter_value(instance, "CellV", float(cell // 4))
            EAL.save_loaded_asset(instance, only_if_is_dirty=False)
            instances[cell] = instance
            kept.append(instance)
        n = decal["normal"]
        # The decal projects along its +X: into the surface, against its normal (Blender -> Unreal: Y mirrored).
        if n[2] > 0.5:
            rotation = unreal.Rotator(roll=0.0, pitch=-90.0, yaw=0.0)
        else:
            # Roll 90: without it the atlas lies on its side on walls (text read bottom to top; -90 put it upside down).
            rotation = unreal.Rotator(roll=90.0, pitch=0.0, yaw=math.degrees(math.atan2(n[1], -n[0])))
        actor = actors.spawn_actor_from_class(unreal.DecalActor, to_unreal(decal["at"]), rotation)
        actor.set_actor_label("Steadfast_Decal_%02d_%d" % (cell, index))
        actor.set_editor_property("tags", [unreal.Name(DECAL_TAG)])
        component = actor.get_editor_property("decal")
        component.set_editor_property("decal_material", instances[cell])
        half = decal["size"] * 50.0
        component.set_editor_property("decal_size", unreal.Vector(DECAL_DEPTH_CM, half, half))
    log("decaly: %d (%d druhů)" % (len(read_layout().get("decals", [])), len(instances)))
    return kept


def collide_per_polygon(mesh):
    """Walkable: the character collides with the mesh itself, not a box round it."""
    body = mesh.get_editor_property("body_setup")
    if body:
        body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        return True
    return False


def place_interior_actors(actors, leaf_mesh):
    """Sliding doors, the artificial gravity box and the start of the walk, from the layout."""
    layout = read_layout()
    for actor in actors.get_all_level_actors():
        label = actor.get_actor_label()
        if label.startswith("Steadfast_Door") or label in ("Steadfast_Gravity", "Steadfast_Spawn"):
            actors.destroy_actor(actor)
    for index, door in enumerate(layout["doors"]):
        actor = actors.spawn_actor_from_class(unreal.SpaceSlidingDoor, to_unreal(door["at"]),
                                              unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw_of(door["dir"])))
        actor.set_actor_label("Steadfast_Door_%d" % (index + 1))
        actor.set_editor_property("tags", [unreal.Name(DOOR_TAG)])
        actor.get_editor_property("leaf_a").set_static_mesh(leaf_mesh)
        actor.get_editor_property("leaf_b").set_static_mesh(leaf_mesh)
        actor.layout_leaves()
    lo, hi = layout["gravity_box"]
    centre = to_unreal([(a + b) / 2.0 for a, b in zip(lo, hi)])
    gravity = actors.spawn_actor_from_class(unreal.SpaceGravityVolume, centre, unreal.Rotator(0, 0, 0))
    gravity.set_actor_label("Steadfast_Gravity")
    gravity.set_editor_property("gravity_cm_s2", GRAVITY_CMS2)
    gravity.get_editor_property("volume").set_box_extent(
        unreal.Vector(*[(b - a) * 50.0 for a, b in zip(lo, hi)]))
    spawn = actors.spawn_actor_from_class(unreal.TargetPoint, to_unreal(layout["spawn"]), unreal.Rotator(0, 0, 0))
    spawn.set_actor_label("Steadfast_Spawn")
    spawn.set_editor_property("tags", [unreal.Name(SPAWN_TAG)])
    log("dveře %d, gravitační box %s, start %s" % (len(layout["doors"]), centre, spawn.get_actor_location()))


def main():
    for path in [os.path.join(INTERIOR, room + ".glb") for room in ROOMS + (GLASS, DOOR_LEAF)] + [LAYOUT]:
        if not os.path.exists(path):
            raise SystemExit("import_interior: chybí %s (Tools/Blender/build_steadfast_interior.py)" % path)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAP)
    import_mesh()
    reference = texture_sets().get("T_Trim_01") or {}
    surfaces = import_surfaces()
    master = build_master(reference, surfaces)
    leather = build_leather(surfaces)

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    instances = {}
    for stem, textures in texture_sets().items():
        if "BaseColor" not in textures:
            continue
        path = "%s/MI_%s" % (PACKAGE, stem)
        if EAL.does_asset_exist(path):
            EAL.delete_asset(path)
        instance = tools.create_asset("MI_%s" % stem, PACKAGE, unreal.MaterialInstanceConstant,
                                      unreal.MaterialInstanceConstantFactoryNew())
        MEL.set_material_instance_parent(instance, master)
        textures.setdefault("EmissiveMap", EAL.load_asset(BLACK))
        for parameter, texture in textures.items():
            MEL.set_material_instance_texture_parameter_value(instance, parameter, texture)
        EAL.save_loaded_asset(instance, only_if_is_dirty=False)
        instances[stem] = instance
    log("instance materiálu: %s" % ", ".join(sorted(instances)))

    meshes = [EAL.load_asset(p) for p in EAL.list_assets(PACKAGE, recursive=True, include_folder=False)]
    meshes = [m for m in meshes if isinstance(m, unreal.StaticMesh) and "/Props/" not in m.get_path_name()]
    # Slots come in named after the kit's own materials (MI_Trim_01_007, M_Black_002, M_LightFade_Red)
    # while the texture sets are called T_Trim_01 and friends - so the "T_" has to come off before
    # matching, or every slot falls back to the first instance (which is what happened first time).
    default = instances.get("T_Trim_01") or next(iter(instances.values()), None)
    maps = {p: t for p, t in reference.items() if p != "EmissiveMap"}
    dark = make_plain(master, "MI_KitDark", (0.02, 0.02, 0.022), maps)
    glow = make_plain(master, "MI_KitGlow", (0.02, 0.02, 0.02), maps, emissive=ORANGE, strength=14.0, glow=True)
    lamp = make_plain(master, "MI_KitLamp", (0.02, 0.02, 0.02), maps, emissive=LAMP_COLOUR, strength=LAMP_STRENGTH, glow=True)
    screen = make_plain(master, "MI_KitScreen", (0.01, 0.015, 0.03), maps, emissive=SCREEN_COLOUR, strength=SCREEN_STRENGTH, glow=True)
    white = make_plain(master, "MI_KitWhite", (0.75, 0.77, 0.8), maps)      # seat stripes, stick tops, buttons
    strip = make_plain(master, "MI_KitStrip", (0.05, 0.05, 0.05), maps, emissive=STRIP_COLOUR, strength=STRIP_STRENGTH, glow=True)
    glass = build_glass()
    pages = import_pages()
    holo_master = build_holo(pages.get("Power") or next(iter(pages.values())))
    holos = {name: make_holo(holo_master, name, texture) for name, texture in pages.items()}
    log("hologramy: %s" % ", ".join(sorted(holos)))
    for mesh in meshes:
        for index, slot in enumerate(mesh.static_materials):
            name = str(slot.material_slot_name).lower()
            pick = default
            for stem, instance in instances.items():
                key = stem.lower()[2:] if stem.lower().startswith("t_") else stem.lower()
                if key in name:
                    pick = instance
                    break
            if name.startswith("m_black_seat"):
                pick = leather
            elif "black" in name:
                pick = dark
            elif "lamp" in name:
                pick = lamp
            elif "glass" in name:
                pick = glass
            elif name.startswith("m_holo_"):
                page = str(slot.material_slot_name).split("_")[2]
                pick = holos.get(page, pick)
            elif "white" in name:
                pick = white
            elif "strip" in name:
                pick = strip
            elif name.startswith("m_screen"):
                pick = screen
            elif "light" in name or "screen" in name:
                pick = glow
            if pick:
                mesh.set_material(index, pick)
        if mesh.get_name() in (GLASS, SCREENS):
            # Nanite draws no translucency; the glass and the holograms are ordinary meshes.
            settings = mesh.get_editor_property("nanite_settings")
            settings.set_editor_property("enabled", False)
            # set_editor_property rebuilds the mesh (PostEditChange); the StaticMeshEditorSubsystem that
            # would do it explicitly is not there in a headless editor (23. 9. 2026).
            mesh.set_editor_property("nanite_settings", settings)
        if mesh.get_name() == SCREENS:
            pass                          # light, not a surface: nothing to bump into
        elif not collide_per_polygon(mesh):
            log("VAROVÁNÍ: %s nemá body setup, kolize nebude" % mesh.get_name())
        EAL.save_loaded_asset(mesh, only_if_is_dirty=False)
    log("materiály a kolize na %d meshích" % len(meshes))

    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in actors.get_all_level_actors():
        if actor.get_actor_label().startswith("Steadfast_Interior"):
            actors.destroy_actor(actor)
    leaf_mesh = next((m for m in meshes if m.get_name() == DOOR_LEAF), None)
    for mesh in meshes:
        if mesh.get_name() == DOOR_LEAF:
            continue                      # lives in the door actors
        # spawn_actor_from_object crashed the headless editor; spawning the class and setting the
        # mesh afterwards is the stable way (23. 9. 2026).
        actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, PLACE_AT, unreal.Rotator(0, 0, 0))
        actor.set_actor_label("Steadfast_Interior_%s" % mesh.get_name())
        tag = {GLASS: GLASS_TAG, SCREENS: SCREENS_TAG}.get(mesh.get_name(), INTERIOR_TAG)
        actor.set_editor_property("tags", [unreal.Name(tag)])
        component = actor.static_mesh_component
        component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
        component.set_static_mesh(mesh)
        if mesh.get_name() == SCREENS:
            # A profile, not set_collision_enabled(): only the profile is saved with the level.
            component.set_collision_profile_name("NoCollision")
            component.set_editor_property("cast_shadow", False)
    place_lights(actors)
    place_interior_actors(actors, leaf_mesh)
    kept = [master, dark, glow, lamp, screen, white, strip, glass, holo_master, leather] + list(holos.values()) \
        + list(surfaces.values()) \
        + list(pages.values()) + list(instances.values()) + meshes
    for instance in [dark, glow, lamp, screen, white, strip] + list(instances.values()):
        for parameter in ("BaseColor", "NormalMap", "ORMMap", "EmissiveMap"):
            kept.append(MEL.get_material_instance_texture_parameter_value(instance, parameter))
    for parameter in ("BaseColor", "NormalMap", "ORMMap"):
        kept.append(reference.get(parameter))
    props = place_props(actors)
    decal_material, decal_atlas = build_decal_material()
    kept += [decal_material, decal_atlas] + place_decals(actors, decal_material)
    kept += [EAL.load_asset(p) for p in EAL.list_assets(PROPS_PACKAGE, recursive=True, include_folder=False)] if props else []
    prune(kept)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    log("postaveno v %s na %s" % (MAP, PLACE_AT))
    return 0


main()
