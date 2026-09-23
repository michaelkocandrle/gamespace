"""Import an interior piece (GLB from Blender) into Unreal and place it in the level.

    .\\Tools\\run_editor_python.ps1 Tools\\Assets\\import_interior.py

Co to dělá:

1. Naimportuje `ArtSource/Ships/Steadfast/Interior/CargoBay.glb` do `/Game/Environments/Steadfast/`.
2. Postaví materiál `M_KitTrim`, který v enginu dělá totéž co `Tools/Blender/recolour_kit.py`
   v Blenderu: texturu kitu odbarví, přetónuje do gunmetalu a emisivní mapu kitu použije jako
   oranžové svítící pásy. Bez toho vypadá kit v enginu šedě a cize.
3. Na každou sadu textur (trim sheet) udělá instanci materiálu a přiřadí ji na sloty meshů.
4. Postaví to do `TestSpace` na `PLACE_AT` a uloží level.

Proč materiál znovu v enginu: přebarvení v Blenderu žije v node grafu, který GLB nepřenese.
Buď se textury vypečou (drahé, ztratí se opakovatelnost), nebo se stejná matematika udělá v
materiálu UE - tahle cesta.
"""

import os
import unreal

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOURCE = os.path.join(ROOT, "ArtSource", "Ships", "Steadfast", "Interior", "CargoBay.glb")
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
# Work lights: cold white, and half of what they were. Warm light (255, 238, 214) cancelled the blue
# of the steel; 7000 K is what turns the bay blue at all.
WORK_LIGHT_LUMENS = 575.0
WORK_LIGHT_KELVIN = 7000.0

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
    task = unreal.AssetImportTask()
    task.filename = SOURCE
    task.destination_path = PACKAGE
    task.automated = True
    task.replace_existing = True
    task.save = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported = list(task.get_editor_property("imported_object_paths") or [])
    log("naimportováno %d objektů" % len(imported))
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


def place_lights(actors, mesh):
    """Work lights under the ceiling, plus two orange strips low down.

    The kit's panels are metal in the ORM map, and metal with nothing to reflect renders black -
    in space there is no sky to fill it in. Without these the bay is a silhouette (23. 9. 2026).
    """
    for actor in actors.get_all_level_actors():
        if actor.get_actor_label().startswith("Steadfast_Light"):
            actors.destroy_actor(actor)
    if not mesh:
        return
    bounds = mesh.get_bounds()
    origin, extent = bounds.origin, bounds.box_extent
    floor = origin.z - extent.z
    # Two rows: under the upper deck, where the crates stand, and above it. A single row at
    # ceiling height only lit the deck plate and left the bay below it black (23. 9. 2026).
    heights = (floor + 190.0, origin.z + extent.z - 40.0)
    lights = 0
    for height in heights:
        for x in (-0.55, 0.0, 0.55):
            spot = unreal.Vector(PLACE_AT.x + origin.x + x * extent.x,
                                 PLACE_AT.y + origin.y + (0.45 * extent.y if height == heights[1] else 0.0),
                                 PLACE_AT.z + height)
            light = actors.spawn_actor_from_class(unreal.PointLight, spot, unreal.Rotator(0, 0, 0))
            lights += 1
            light.set_actor_label("Steadfast_Light_Work_%d" % lights)
            light.set_editor_property("tags", [unreal.Name(WORK_LIGHT_TAG)])
            component = light.point_light_component
            component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
            component.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
            component.set_editor_property("intensity", WORK_LIGHT_LUMENS)
            component.set_editor_property("attenuation_radius", 900.0)
            component.set_editor_property("light_color", unreal.Color(r=255, g=255, b=255, a=255))
            component.set_editor_property("use_temperature", True)
            component.set_editor_property("temperature", WORK_LIGHT_KELVIN)
    for y in (-0.85, 0.85):
        spot = unreal.Vector(PLACE_AT.x + origin.x, PLACE_AT.y + origin.y + y * extent.y,
                             PLACE_AT.z + origin.z - extent.z + 60.0)
        light = actors.spawn_actor_from_class(unreal.PointLight, spot, unreal.Rotator(0, 0, 0))
        lights += 1
        light.set_actor_label("Steadfast_Light_Accent_%d" % lights)
        light.set_editor_property("tags", [unreal.Name(ACCENT_LIGHT_TAG)])
        component = light.point_light_component
        component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
        component.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
        component.set_editor_property("intensity", 550.0)
        component.set_editor_property("attenuation_radius", 600.0)
        component.set_editor_property("light_color", unreal.Color(r=255, g=140, b=40, a=255))
    log("rozsvíceno %d světel" % lights)


def main():
    if not os.path.exists(SOURCE):
        raise SystemExit("import_interior: chybí %s" % SOURCE)
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
            elif "light" in name or "screen" in name:
                pick = glow
            if pick:
                mesh.set_material(index, pick)
        EAL.save_loaded_asset(mesh, only_if_is_dirty=False)
    log("materiály přiřazeny na %d meshů" % len(meshes))

    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in actors.get_all_level_actors():
        if actor.get_actor_label().startswith("Steadfast_Interior"):
            actors.destroy_actor(actor)
    for mesh in meshes:
        # spawn_actor_from_object crashed the headless editor; spawning the class and setting the
        # mesh afterwards is the stable way (23. 9. 2026).
        actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, PLACE_AT, unreal.Rotator(0, 0, 0))
        actor.set_actor_label("Steadfast_Interior_%s" % mesh.get_name())
        actor.set_editor_property("tags", [unreal.Name(INTERIOR_TAG)])
        component = actor.static_mesh_component
        component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
        component.set_static_mesh(mesh)
    place_lights(actors, meshes[0] if meshes else None)
    kept = [master, dark, glow] + list(instances.values()) + meshes
    for instance in [dark, glow] + list(instances.values()):
        for parameter in ("BaseColor", "NormalMap", "ORMMap", "EmissiveMap"):
            kept.append(MEL.get_material_instance_texture_parameter_value(instance, parameter))
    for parameter in ("BaseColor", "NormalMap", "ORMMap"):
        kept.append(reference.get(parameter))
    prune(kept)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    log("postaveno v %s na %s" % (MAP, PLACE_AT))
    return 0


main()
