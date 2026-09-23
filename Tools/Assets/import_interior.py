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
DOOR_LEAF = "DoorLeaf"
LAYOUT = os.path.join(INTERIOR, "Interior_layout.json")
PACKAGE = "/Game/Environments/Steadfast"
MATERIAL = PACKAGE + "/M_KitTrim"
MAP = "/Game/Maps/TestSpace"
PLACE_AT = unreal.Vector(0.0, 50000.0, 0.0)      # 500 m sideways from the ship's spawn
# Blue steel. Measured on 23. 9. 2026 (Tools/Shots/interior_tune.json, HANDOFF point 59) against the
# author's mood references (cool, B/R 1.1-1.6 in sRGB): (0.62, 0.65, 0.70) under warm lights came out
# warm silver, B/R 0.95. The tint alone barely moves the hue - the light colour does most of it.
GUNMETAL = (0.35, 0.42, 0.55)
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
WORK_LIGHT_KELVIN = 7000.0
WORK_LIGHT_CONE = (25.0, 80.0)      # inner, outer half angle in degrees
# The orange accents: at 550 lm they painted the whole ceiling brown (B/R 0.93 looking up). Once they
# stood inside the rooms rather than behind the bay's walls, 200 lm still warmed the bay and engine
# room to B/R 0.97-1.11; 100 lm keeps every view at 1.10-1.26 and the orange spots still read
# (Tools/Shots/accent_tune.json; 50 lm all but lost them).
ACCENT_LIGHT_LUMENS = 100.0
# The fixtures' glowing face: cold white, not the kit's orange.
LAMP_COLOUR = (0.78, 0.88, 1.0)
LAMP_STRENGTH = 20.0
# Cockpit displays: blue, and a blue light off them (the holo-blue screens of the mood references).
SCREEN_COLOUR = (0.15, 0.55, 1.0)
SCREEN_STRENGTH = 6.0
SCREEN_LIGHT = unreal.Color(r=90, g=170, b=255, a=255)
GLASS_MATERIAL = PACKAGE + "/M_KitGlass"


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


def build_master(defaults):
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

    MEL.connect_material_property(tint, "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(normal, "", unreal.MaterialProperty.MP_NORMAL)
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

    MEL.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
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
    for room in ROOMS + (GLASS, DOOR_LEAF):
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
            component.set_editor_property("attenuation_radius", 900.0)
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
    master = build_master(reference)

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
    meshes = [m for m in meshes if isinstance(m, unreal.StaticMesh)]
    # Slots come in named after the kit's own materials (MI_Trim_01_007, M_Black_002, M_LightFade_Red)
    # while the texture sets are called T_Trim_01 and friends - so the "T_" has to come off before
    # matching, or every slot falls back to the first instance (which is what happened first time).
    default = instances.get("T_Trim_01") or next(iter(instances.values()), None)
    maps = {p: t for p, t in reference.items() if p != "EmissiveMap"}
    dark = make_plain(master, "MI_KitDark", (0.02, 0.02, 0.022), maps)
    glow = make_plain(master, "MI_KitGlow", (0.02, 0.02, 0.02), maps, emissive=ORANGE, strength=14.0, glow=True)
    lamp = make_plain(master, "MI_KitLamp", (0.02, 0.02, 0.02), maps, emissive=LAMP_COLOUR, strength=LAMP_STRENGTH, glow=True)
    screen = make_plain(master, "MI_KitScreen", (0.01, 0.015, 0.03), maps, emissive=SCREEN_COLOUR, strength=SCREEN_STRENGTH, glow=True)
    glass = build_glass()
    for mesh in meshes:
        for index, slot in enumerate(mesh.static_materials):
            name = str(slot.material_slot_name).lower()
            pick = default
            for stem, instance in instances.items():
                key = stem.lower()[2:] if stem.lower().startswith("t_") else stem.lower()
                if key in name:
                    pick = instance
                    break
            if "black" in name:
                pick = dark
            elif "lamp" in name:
                pick = lamp
            elif "glass" in name:
                pick = glass
            elif name.startswith("m_screen"):
                pick = screen
            elif "light" in name or "screen" in name:
                pick = glow
            if pick:
                mesh.set_material(index, pick)
        if mesh.get_name() == GLASS:
            # Nanite draws no translucency; the glass is an ordinary mesh.
            settings = mesh.get_editor_property("nanite_settings")
            settings.set_editor_property("enabled", False)
            # set_editor_property rebuilds the mesh (PostEditChange); the StaticMeshEditorSubsystem that
            # would do it explicitly is not there in a headless editor (23. 9. 2026).
            mesh.set_editor_property("nanite_settings", settings)
        if not collide_per_polygon(mesh):
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
        actor.set_editor_property("tags", [unreal.Name(GLASS_TAG if mesh.get_name() == GLASS else INTERIOR_TAG)])
        component = actor.static_mesh_component
        component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
        component.set_static_mesh(mesh)
    place_lights(actors)
    place_interior_actors(actors, leaf_mesh)
    kept = [master, dark, glow, lamp, screen, glass] + list(instances.values()) + meshes
    for instance in [dark, glow, lamp, screen] + list(instances.values()):
        for parameter in ("BaseColor", "NormalMap", "ORMMap", "EmissiveMap"):
            kept.append(MEL.get_material_instance_texture_parameter_value(instance, parameter))
    for parameter in ("BaseColor", "NormalMap", "ORMMap"):
        kept.append(reference.get(parameter))
    prune(kept)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    log("postaveno v %s na %s" % (MAP, PLACE_AT))
    return 0


main()
