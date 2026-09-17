"""Builds /Game/Maps/MainMenu, the title screen level: the Vanguard in the foreground, the ringed gas
giant Orun and a moon behind it, the star sky, and a camera for ASpacePlayerController to drift.

Editor closed, after build_space_scene.py and import_ship.py (it uses their assets):

    .\\Tools\\run_editor_python.ps1 Tools\\Assets\\build_main_menu.py

Re-runnable: the level is created once, actors are found by label and updated. The level's game
mode override is ASpaceMenuGameMode (no pawn; the controller shows the menu).
"""

import math

import unreal

LEVEL = "/Game/Maps/MainMenu"
SKY_MATERIAL = "/Game/Environments/Space/M_Starfield_Sky"
PLANET_MESH = "/Game/Planets/SM_PlanetSphere"
GIANT_MATERIAL = "/Game/Environments/Space/M_GasGiant"
MOON_MATERIAL = "/Game/Environments/Space/M_Moon"
RINGS_MATERIAL = "/Game/Environments/Space/M_PlanetRings"
SHIP_MESH = "/Game/Ships/Vanguard/Meshes/SM_Ship_Vanguard"
CANOPY_MESH = "/Game/Ships/Vanguard/Meshes/SM_Ship_Vanguard_Canopy"

EXPOSURE_EV100 = 3.0
SUN_PITCH, SUN_YAW = -22.0, 25.0          # light travels towards +X: lights what the camera sees
CAMERA_LOCATION = (-2200.0, -900.0, 350.0)  # cm, around the ship at the origin
CAMERA_FOV = 60.0
SHIP_YAW = 200.0


def log(msg):
    unreal.log("build_main_menu: " + msg)


def direction(yaw_deg, elevation_deg, distance_km):
    yaw, elevation = math.radians(yaw_deg), math.radians(elevation_deg)
    d = distance_km * 100000.0
    return (d * math.cos(elevation) * math.cos(yaw), d * math.cos(elevation) * math.sin(yaw), d * math.sin(elevation))


def load(path):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if asset is None:
        raise RuntimeError("%s missing - run build_space_scene.py / import_ship.py first" % path)
    return asset


def upsert(eas, label, cls, location=(0.0, 0.0, 0.0), rotation=None):
    for actor in eas.get_all_level_actors():
        if actor.get_actor_label() == label:
            wanted = cls if isinstance(cls, unreal.Class) else cls.static_class()
            if not unreal.MathLibrary.class_is_child_of(actor.get_class(), wanted):
                eas.destroy_actor(actor)
                break
            actor.set_actor_location(unreal.Vector(*location), False, False)
            if rotation is not None:
                actor.set_actor_rotation(rotation, False)
            return actor
    actor = eas.spawn_actor_from_class(cls, unreal.Vector(*location), rotation or unreal.Rotator())
    actor.set_actor_label(label)
    log("spawned %s" % label)
    return actor


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(LEVEL):
        if not les.load_level(LEVEL):
            raise RuntimeError("could not load " + LEVEL)
    elif not les.new_level(LEVEL):
        raise RuntimeError("could not create " + LEVEL)

    # Keyword arguments on purpose: unreal.Rotator's positional order is roll, pitch, yaw.
    sun = upsert(eas, "Sun", unreal.DirectionalLight, rotation=unreal.Rotator(roll=0.0, pitch=SUN_PITCH, yaw=SUN_YAW))
    sun_light = sun.get_component_by_class(unreal.DirectionalLightComponent)
    sun_light.set_mobility(unreal.ComponentMobility.MOVABLE)
    sun_light.set_editor_property("intensity", 8.0)

    sky_light = upsert(eas, "SkyLight", unreal.SkyLight)
    capture = sky_light.get_component_by_class(unreal.SkyLightComponent)
    capture.set_mobility(unreal.ComponentMobility.MOVABLE)
    capture.set_editor_property("real_time_capture", True)
    capture.set_editor_property("intensity", 0.35)
    capture.set_editor_property("lower_hemisphere_is_black", False)

    ppv = upsert(eas, "PP_SpaceExposure", unreal.PostProcessVolume)
    ppv.set_editor_property("unbound", True)
    settings = ppv.get_editor_property("settings")
    for key in ("auto_exposure_min_brightness", "auto_exposure_max_brightness"):
        settings.set_editor_property("override_" + key, True)
        settings.set_editor_property(key, EXPOSURE_EV100)
    ppv.set_editor_property("settings", settings)

    sky = upsert(eas, "StarfieldSky", unreal.load_class(None, "/Script/gamespace.SkyDome"))
    sky.set_editor_property("dome_radius_km", 2000.0)
    sky.get_component_by_class(unreal.StaticMeshComponent).set_material(0, load(SKY_MATERIAL))

    body_class = unreal.load_class(None, "/Script/gamespace.DistantBody")
    planet_mesh = load(PLANET_MESH)
    giant = upsert(eas, "GasGiant_Orun", body_class, direction(18.0, 12.0, 420.0))
    moon = upsert(eas, "Moon_Keth", body_class, direction(-12.0, 21.0, 90.0))
    for actor, name, radius, material in ((giant, "Orun", 150.0, GIANT_MATERIAL), (moon, "Keth", 6.0, MOON_MATERIAL)):
        body = actor.get_editor_property("body")
        body.set_static_mesh(planet_mesh)
        body.set_material(0, load(material))
        actor.set_editor_property("display_name", unreal.Text(name))
        actor.set_editor_property("radius_km", radius)
    giant.set_editor_property("ring_outer_radius_km", 330.0)
    giant.set_editor_property("axial_tilt_deg", 18.0)
    giant.set_editor_property("spin_period_seconds", 1800.0)
    giant.get_editor_property("rings").set_material(0, load(RINGS_MATERIAL))

    ship_rotation = unreal.Rotator(roll=0.0, pitch=0.0, yaw=SHIP_YAW)
    ship = upsert(eas, "MenuShip", unreal.StaticMeshActor, rotation=ship_rotation)
    canopy = upsert(eas, "MenuShipCanopy", unreal.StaticMeshActor, rotation=ship_rotation)
    for actor, mesh in ((ship, SHIP_MESH), (canopy, CANOPY_MESH)):
        component = actor.get_component_by_class(unreal.StaticMeshComponent)
        component.set_mobility(unreal.ComponentMobility.MOVABLE)
        component.set_static_mesh(load(mesh))
    ship.set_editor_property("tags", [unreal.Name("MenuOrbitCenter")])

    camera = upsert(eas, "MenuCamera", unreal.CameraActor, CAMERA_LOCATION,
                    unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*CAMERA_LOCATION), unreal.Vector(0.0, 0.0, 150.0)))
    camera.set_editor_property("tags", [unreal.Name("MenuCamera")])
    lens = camera.get_component_by_class(unreal.CameraComponent)
    lens.set_editor_property("field_of_view", CAMERA_FOV)
    lens.set_editor_property("constrain_aspect_ratio", False)

    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    world.get_world_settings().set_editor_property("default_game_mode", unreal.load_class(None, "/Script/gamespace.SpaceMenuGameMode"))

    if not les.save_current_level():
        raise RuntimeError("could not save " + LEVEL)
    log("saved %s" % LEVEL)


main()
