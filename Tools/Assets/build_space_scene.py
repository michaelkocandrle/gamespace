"""Builds the space look of TestSpace: star sky, test planet, sun and exposure.

Two steps, editor closed:

    python Tools/Assets/generate_starfield.py Intermediate/GeneratedAssets/starfield.hdr
    .\\Tools\\run_editor_python.ps1 Tools\\Assets\\build_space_scene.py

Re-runnable. Assets and level actors this script owns are updated in place: materials are
rebuilt from the graph below and actors are found by label. Imported source assets (star
cubemap, planet mesh) are imported once and then left alone. Nothing else in the level is
touched, except that the SkyAtmosphere actor is removed - it renders an Earth-like sky and
horizon, which is the opposite of space.
"""

import math
import os

import unreal

import gamespace_assets as ga

# ---------------------------------------------------------------------------------------
# Tuning
# ---------------------------------------------------------------------------------------

# Fixed exposure. Auto exposure would brighten a mostly black star field until the stars
# bloom out, then darken again whenever a lit asteroid fills the view.
EXPOSURE_EV100 = 3.0

# Multiplies the star cubemap. Raise for more visible stars, lower for a darker sky.
STAR_BRIGHTNESS = 4.0

# Sky dome radius. Only has to enclose everything you can fly to; the stars are looked up by
# view direction, so they appear infinitely far away whatever the size.
SKY_RADIUS_CM = 8_000_00  # 8 km

# Planet: radius 500 m, surface ~2.5 km from PlayerStart. At the ~33 m/s cruise speed that is
# roughly 75 s of flight, ~30 s with boost, and the planet starts at ~19 degrees across - clearly
# visible, with plenty of room to grow.
PLANET_NAME = "Veyra"
PLANET_RADIUS_CM = 500_00
# Ahead of PlayerStart (which faces +X), a little right and up so the ship does not hide it.
PLANET_LOCATION_CM = (3000_00, 400_00, 250_00)

# Sun from behind the player's left shoulder, so the planet is seen about three-quarters lit.
SUN_PITCH, SUN_YAW = -39.0, 45.0

# ---------------------------------------------------------------------------------------

LEVEL = "/Game/Maps/TestSpace"
STARFIELD_TEXTURE = "/Game/Environments/Space/T_Starfield_Cube"
STARFIELD_MATERIAL = "/Game/Environments/Space/M_Starfield_Sky"
PLANET_MESH = "/Game/Planets/SM_PlanetSphere"
PLANET_MATERIAL = "/Game/Planets/M_Planet_Test"

MEL = unreal.MaterialEditingLibrary
GENERATED = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_intermediate_dir()), "GeneratedAssets")


def log(msg):
    unreal.log("build_space_scene: " + msg)


# ---------------------------------------------------------------------------------------
# Source assets
# ---------------------------------------------------------------------------------------


def write_sphere_obj(path, radius=100.0, segments=256, rings=128):
    """UV sphere, 1 unit = 1 cm. The engine's basic sphere has 960 triangles, which shows as a
    faceted silhouette on a 500 m planet; this one has ~65k."""
    lines = []
    for r in range(rings + 1):
        theta = math.pi * r / rings
        for s in range(segments + 1):
            phi = 2.0 * math.pi * s / segments
            n = (math.sin(theta) * math.cos(phi), math.sin(theta) * math.sin(phi), math.cos(theta))
            lines.append("v %.5f %.5f %.5f" % (n[0] * radius, n[1] * radius, n[2] * radius))
            lines.append("vn %.5f %.5f %.5f" % n)
            lines.append("vt %.5f %.5f" % (s / segments, 1.0 - r / rings))
    row = segments + 1
    for r in range(rings):
        for s in range(segments):
            a, b = r * row + s + 1, r * row + s + 2
            c, d = a + row, b + row
            if r != 0:
                lines.append("f %d/%d/%d %d/%d/%d %d/%d/%d" % (a, a, a, c, c, c, b, b, b))
            if r != rings - 1:
                lines.append("f %d/%d/%d %d/%d/%d %d/%d/%d" % (b, b, b, c, c, c, d, d, d))
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def import_sources():
    hdr = os.path.join(GENERATED, "starfield.hdr")
    if not ga.existing_or_none(STARFIELD_TEXTURE) and not os.path.isfile(hdr):
        raise RuntimeError("%s missing - run Tools/Assets/generate_starfield.py first" % hdr)
    cube = ga.import_file(STARFIELD_TEXTURE, hdr, on_exists="skip",
                          properties={"lod_group": unreal.TextureGroup.TEXTUREGROUP_SKYBOX})
    if not isinstance(cube, unreal.TextureCube):
        raise RuntimeError("%s imported as %s, expected TextureCube" % (STARFIELD_TEXTURE, cube.get_class().get_name()))

    mesh = ga.existing_or_none(PLANET_MESH)
    if mesh is None:
        os.makedirs(GENERATED, exist_ok=True)
        obj = os.path.join(GENERATED, "planet_sphere.obj")
        write_sphere_obj(obj)
        mesh = ga.import_file(PLANET_MESH, obj)
    ensure_sphere_collision(mesh)
    return cube, mesh


def ensure_sphere_collision(mesh):
    """Replace the importer's convex hull with one exact sphere, so the ship's swept movement
    meets the actual surface rather than a simplified hull.

    Written straight into the BodySetup: the collision helpers on StaticMeshEditorSubsystem /
    EditorStaticMeshLibrary refuse to run in the headless commandlet and just return -1.
    """
    body = mesh.get_editor_property("body_setup")
    agg = body.get_editor_property("agg_geom")
    spheres = agg.get_editor_property("sphere_elems")
    if (len(spheres) == 1 and abs(spheres[0].get_editor_property("radius") - 100.0) < 0.01
            and not agg.get_editor_property("convex_elems") and not agg.get_editor_property("box_elems")):
        return
    sphere = unreal.KSphereElem()
    sphere.set_editor_property("radius", 100.0)  # matches write_sphere_obj
    agg.set_editor_property("sphere_elems", [sphere])
    agg.set_editor_property("convex_elems", [])
    agg.set_editor_property("box_elems", [])
    agg.set_editor_property("sphyl_elems", [])
    body.set_editor_property("agg_geom", agg)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
    log("planet mesh collision set to one sphere, radius 100")


# ---------------------------------------------------------------------------------------
# Materials (script-owned: the graph is rebuilt on every run)
# ---------------------------------------------------------------------------------------


def fresh_material(path):
    material = ga.existing_or_none(path)
    if material is None:
        folder, name = path.rsplit("/", 1)
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, folder, unreal.Material, unreal.MaterialFactoryNew())
    else:
        # delete_all_material_expressions() leaves nodes behind when run headless, so the graph
        # grew on every run. Delete one by one and check the graph really is empty.
        for expr in list(MEL.get_material_expressions(material)):
            MEL.delete_material_expression(material, expr)
        left = MEL.get_num_material_expressions(material)
        if left:
            raise RuntimeError("%s still has %d expression(s) after clearing" % (path, left))
    return material


def node(material, cls, x, y, **properties):
    expr = MEL.create_material_expression(material, cls, x, y)
    for key, value in properties.items():
        expr.set_editor_property(key, value)
    return expr


def link(src, dst, dst_input, src_output=""):
    if not MEL.connect_material_expressions(src, src_output, dst, dst_input):
        raise RuntimeError("could not connect %s.%r -> %s.%r" % (
            src.get_class().get_name(), src_output, dst.get_class().get_name(), dst_input))


def output(src, prop, src_output=""):
    if not MEL.connect_material_property(src, src_output, prop):
        raise RuntimeError("could not connect %s.%r -> %s" % (src.get_class().get_name(), src_output, prop))


def finish(material):
    MEL.layout_material_expressions(material)
    MEL.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    log("built %s (%d nodes)" % (material.get_path_name(), MEL.get_num_material_expressions(material)))


def build_starfield_material(cube):
    m = fresh_material(STARFIELD_MATERIAL)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("two_sided", True)   # seen from inside the dome
    m.set_editor_property("is_sky", True)      # sky pass; also picked up by the real-time sky light

    # CameraVector points from the pixel to the camera; the sky lookup needs the opposite.
    view = node(m, unreal.MaterialExpressionCameraVectorWS, -900, 0)
    flip = node(m, unreal.MaterialExpressionConstant, -900, 120, r=-1.0)
    direction = node(m, unreal.MaterialExpressionMultiply, -700, 0)
    link(view, direction, "A")
    link(flip, direction, "B")

    stars = node(m, unreal.MaterialExpressionTextureSampleParameterCube, -500, 0,
                 parameter_name="Starfield", texture=cube)
    link(direction, stars, "UVs")

    brightness = node(m, unreal.MaterialExpressionScalarParameter, -500, 250,
                      parameter_name="StarBrightness", default_value=STAR_BRIGHTNESS)
    emissive = node(m, unreal.MaterialExpressionMultiply, -250, 0)
    link(stars, emissive, "A", "RGB")
    link(brightness, emissive, "B")
    output(emissive, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    finish(m)
    return m


def build_planet_material():
    m = fresh_material(PLANET_MATERIAL)
    # The imported planet mesh is Nanite. Without this flag a packaged or -game build falls back
    # to the default material, and PIE would set it silently and dirty the asset.
    m.set_editor_property("used_with_nanite", True)

    # Unit direction from the planet's centre. Built from world position so it does not depend
    # on how the mesh is scaled; ObjectRadius is exact for a sphere.
    world = node(m, unreal.MaterialExpressionWorldPosition, -1600, 0)
    centre = node(m, unreal.MaterialExpressionObjectPositionWS, -1600, 150)
    offset = node(m, unreal.MaterialExpressionSubtract, -1400, 0)
    link(world, offset, "A")
    link(centre, offset, "B")
    radius = node(m, unreal.MaterialExpressionObjectRadius, -1400, 150)
    unit = node(m, unreal.MaterialExpressionDivide, -1200, 0)
    link(offset, unit, "A")
    link(radius, unit, "B")

    # Continents: one multi-octave noise over the surface blends two terrain colours.
    noise = node(m, unreal.MaterialExpressionNoise, -1000, 0,
                 scale=1.6, levels=6, output_min=0.0, output_max=1.0)
    link(unit, noise, "World Position")
    lowland = node(m, unreal.MaterialExpressionVectorParameter, -1000, 250,
                   parameter_name="LowlandColor", default_value=unreal.LinearColor(0.30, 0.12, 0.06, 1.0))
    highland = node(m, unreal.MaterialExpressionVectorParameter, -1000, 450,
                    parameter_name="HighlandColor", default_value=unreal.LinearColor(0.62, 0.42, 0.24, 1.0))
    terrain = node(m, unreal.MaterialExpressionLinearInterpolate, -700, 250)
    link(lowland, terrain, "A")
    link(highland, terrain, "B")
    link(noise, terrain, "Alpha")

    # Polar caps: |z| near 1, with the edge broken up by the same noise.
    z = node(m, unreal.MaterialExpressionComponentMask, -1000, -250, r=False, g=False, b=True, a=False)
    link(unit, z, "")
    abs_z = node(m, unreal.MaterialExpressionAbs, -850, -250)
    link(z, abs_z, "")
    wobble_amount = node(m, unreal.MaterialExpressionConstant, -850, -120, r=0.12)
    wobble = node(m, unreal.MaterialExpressionMultiply, -700, -120)
    link(noise, wobble, "A")
    link(wobble_amount, wobble, "B")
    latitude = node(m, unreal.MaterialExpressionAdd, -550, -250)
    link(abs_z, latitude, "A")
    link(wobble, latitude, "B")
    cap = node(m, unreal.MaterialExpressionSmoothStep, -400, -250, const_min=0.86, const_max=0.93)
    link(latitude, cap, "Value")

    ice = node(m, unreal.MaterialExpressionVectorParameter, -700, 600,
               parameter_name="IceColor", default_value=unreal.LinearColor(0.85, 0.88, 0.90, 1.0))
    base = node(m, unreal.MaterialExpressionLinearInterpolate, -300, 250)
    link(terrain, base, "A")
    link(ice, base, "B")
    link(cap, base, "Alpha")
    output(base, unreal.MaterialProperty.MP_BASE_COLOR)

    rough = node(m, unreal.MaterialExpressionConstant, -300, 500, r=0.85)
    output(rough, unreal.MaterialProperty.MP_ROUGHNESS)
    finish(m)
    return m


# ---------------------------------------------------------------------------------------
# Level
# ---------------------------------------------------------------------------------------


def upsert_actor(eas, actors, label, cls, location=(0.0, 0.0, 0.0)):
    for actor in actors:
        if actor.get_actor_label() == label:
            # cls may be a Python wrapper type or a UClass from load_class(); compare as UClass.
            wanted = cls if isinstance(cls, unreal.Class) else cls.static_class()
            if not unreal.MathLibrary.class_is_child_of(actor.get_class(), wanted):
                raise RuntimeError("actor %r is a %s, expected %s" % (label, actor.get_class().get_name(), cls))
            actor.set_actor_location(unreal.Vector(*location), False, False)
            return actor
    actor = eas.spawn_actor_from_class(cls, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(label)
    log("spawned %s" % label)
    return actor


def build_level(sky_material, planet_mesh, planet_material):
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not les.load_level(LEVEL):
        raise RuntimeError("could not load " + LEVEL)
    actors = eas.get_all_level_actors()

    for actor in actors:
        if isinstance(actor, unreal.SkyAtmosphere):
            log("removing %s" % actor.get_actor_label())
            eas.destroy_actor(actor)
    actors = eas.get_all_level_actors()

    # Keyword arguments on purpose: unreal.Rotator's positional order is roll, pitch, yaw.
    for actor in actors:
        if isinstance(actor, unreal.DirectionalLight):
            actor.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=SUN_PITCH, yaw=SUN_YAW), False)
        if isinstance(actor, unreal.SkyLight):
            sky_light = actor.get_component_by_class(unreal.SkyLightComponent)
            # Stars exist below the horizon too; don't clamp the captured lower half to black.
            sky_light.set_editor_property("lower_hemisphere_is_black", False)

    # Star dome
    sphere = unreal.load_object(None, "/Engine/BasicShapes/Sphere.Sphere")  # radius 50 cm
    sky = upsert_actor(eas, actors, "StarfieldSky", unreal.StaticMeshActor)
    sky.set_actor_scale3d(unreal.Vector(1, 1, 1) * (SKY_RADIUS_CM / 50.0))
    smc = sky.get_component_by_class(unreal.StaticMeshComponent)
    smc.set_static_mesh(sphere)
    smc.set_material(0, sky_material)
    smc.set_collision_profile_name("NoCollision")
    # A shell around the whole level: casting shadows would put everything in the dark.
    smc.set_editor_property("cast_shadow", False)
    smc.set_editor_property("affect_distance_field_lighting", False)
    smc.set_editor_property("affect_dynamic_indirect_lighting", False)
    smc.set_editor_property("visible_in_ray_tracing", False)

    # Planet
    body_class = unreal.load_class(None, "/Script/gamespace.CelestialBody")
    planet = upsert_actor(eas, actors, "Planet_" + PLANET_NAME, body_class, PLANET_LOCATION_CM)
    planet.set_editor_property("display_name", unreal.Text(PLANET_NAME))
    planet.set_actor_scale3d(unreal.Vector(1, 1, 1) * (PLANET_RADIUS_CM / 100.0))  # mesh radius 100 cm
    body = planet.get_component_by_class(unreal.StaticMeshComponent)
    body.set_static_mesh(planet_mesh)
    body.set_material(0, planet_material)

    # Exposure: clamp auto exposure to one value, i.e. fixed.
    ppv = upsert_actor(eas, actors, "PP_SpaceExposure", unreal.PostProcessVolume)
    ppv.set_editor_property("unbound", True)
    settings = ppv.get_editor_property("settings")
    for key, value in (("auto_exposure_min_brightness", EXPOSURE_EV100),
                       ("auto_exposure_max_brightness", EXPOSURE_EV100)):
        settings.set_editor_property("override_" + key, True)
        settings.set_editor_property(key, value)
    ppv.set_editor_property("settings", settings)

    if not les.save_current_level():
        raise RuntimeError("could not save " + LEVEL)
    log("saved %s" % LEVEL)


def main():
    cube, planet_mesh = import_sources()
    sky_material = build_starfield_material(cube)
    planet_material = build_planet_material()
    build_level(sky_material, planet_mesh, planet_material)

    start = unreal.Vector(0.0, 0.0, 300.0)
    centre = unreal.Vector(*PLANET_LOCATION_CM)
    surface_m = ((centre - start).length() - PLANET_RADIUS_CM) / 100.0
    log("planet surface %.0f m from PlayerStart: %.0f s at 33 m/s, %.0f s at 83 m/s boost" % (
        surface_m, surface_m / 33.3, surface_m / 83.3))


main()
