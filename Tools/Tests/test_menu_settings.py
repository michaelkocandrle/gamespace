"""Headless checks for the playable build: title screen level, menus wiring, settings class, cooking
configuration, sounds, and the exit facing.

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\test_menu_settings.py

The menus themselves are Slate and need a game viewport, so they are checked in the packaged game;
here everything they depend on is. Nothing is saved.
Prints "MENUTEST PASS" / "MENUTEST FAIL" lines and a summary.
"""

import json
import math
import os

import unreal

failures = []
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def log(msg):
    unreal.log("MENUTEST " + msg)


def check(name, ok, detail=""):
    log(("PASS " if ok else "FAIL ") + name + ("  (" + detail + ")" if detail else ""))
    if not ok:
        failures.append(name)


# --- Settings class ---------------------------------------------------------------------------
settings = unreal.GameUserSettings.get_game_user_settings()
check("engine settings object is SpaceUserSettings", settings is not None and settings.get_class().get_name() == "SpaceUserSettings",
      settings.get_class().get_name() if settings else "none")
cdo = unreal.get_default_object(unreal.SpaceUserSettings)
check("settings defaults", abs(cdo.get_editor_property("mouse_sensitivity") - 1.0) < 1e-6 and cdo.get_editor_property("hud_mode") == 1
      and 0.0 < cdo.get_editor_property("master_volume") <= 1.0 and not cdo.get_editor_property("invert_ship_pitch"))

# --- Game modes and controller ------------------------------------------------------------------
controller = unreal.SpacePlayerController.static_class()
space_mode = unreal.get_default_object(unreal.SpaceGameMode)
menu_mode = unreal.get_default_object(unreal.SpaceMenuGameMode)
check("game uses SpacePlayerController", space_mode.get_editor_property("player_controller_class") == controller)
check("title screen uses SpacePlayerController and no pawn", menu_mode.get_editor_property("player_controller_class") == controller
      and menu_mode.get_editor_property("default_pawn_class") is None)
bp_mode = unreal.EditorAssetLibrary.load_blueprint_class("/Game/Blueprints/BP_SpaceGameMode")
check("BP_SpaceGameMode inherits the controller", bp_mode is not None
      and unreal.get_default_object(bp_mode).get_editor_property("player_controller_class") == controller)

# --- Config: default map and cooking -------------------------------------------------------------
engine_ini = open(os.path.join(REPO, "Config", "DefaultEngine.ini"), encoding="utf-8").read()
game_ini = open(os.path.join(REPO, "Config", "DefaultGame.ini"), encoding="utf-8").read()
check("game starts on the title screen", "GameDefaultMap=/Game/Maps/MainMenu.MainMenu" in engine_ini)
check("editor still starts on TestSpace", "EditorStartupMap=/Game/Maps/TestSpace.TestSpace" in engine_ini)
check("settings class registered", "GameUserSettingsClassName=/Script/gamespace.SpaceUserSettings" in engine_ini)
cooked_dirs = ("/Game/Input", "/Game/Ships", "/Game/UI", "/Game/Environments", "/Game/Planets", "/Game/Characters")
missing = [d for d in cooked_dirs if '+DirectoriesToAlwaysCook=(Path="%s")' % d not in game_ini]
check("path-loaded asset folders always cooked", not missing, ", ".join(missing))
check("both maps cooked", '+MapsToCook=(FilePath="/Game/Maps/MainMenu")' in game_ini and '+MapsToCook=(FilePath="/Game/Maps/TestSpace")' in game_ini)

# --- Sounds --------------------------------------------------------------------------------------
for path, looping in (("/Game/UI/Audio/SW_UiHover", False), ("/Game/UI/Audio/SW_UiConfirm", False), ("/Game/UI/Audio/SW_MenuAmbience", True),
                      ("/Game/Ships/Audio/SW_Touchdown", False), ("/Game/Ships/Audio/SW_EngineHum", True)):
    sound = unreal.EditorAssetLibrary.load_asset(path)
    check("sound %s" % path.rsplit("/", 1)[1], isinstance(sound, unreal.SoundWave) and sound.get_editor_property("looping") == looping)

# --- Title screen level ----------------------------------------------------------------------------
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
check("MainMenu level loads", les.load_level("/Game/Maps/MainMenu"))
actors = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
# The ship on the title screen is its hull plus every part its manifest lists, except the gear (stowed in
# space) and the cockpit interior (inside the hull).
_manifest = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                        "ArtSource", "Ships", "Vanguard", "Export", "Vanguard_manifest.json"), encoding="utf-8"))
_parts = ["MenuShip_" + info["part"] for name, info in _manifest["meshes"].items() if info.get("part") and info["part"] not in ("Gear", "Interior", "Lining")]
_ship_actors = sorted(label for label in actors if label.startswith("MenuShip"))
check("title ship = hull + the manifest's parts (no gear, nothing from an older model)", _ship_actors == sorted(["MenuShip"] + _parts), str(_ship_actors))
for label in ("Sun", "SkyLight", "PP_SpaceExposure", "StarfieldSky", "GasGiant_Orun", "Moon_Keth", "MenuShip", "MenuCamera"):
    check("title actor %s" % label, label in actors)
if "MenuCamera" in actors and "MenuShip" in actors:
    check("camera and orbit centre tagged", actors["MenuCamera"].actor_has_tag("MenuCamera") and actors["MenuShip"].actor_has_tag("MenuOrbitCenter"))
    camera = actors["MenuCamera"].get_actor_location()
    forward = unreal.MathLibrary.get_forward_vector(actors["MenuCamera"].get_actor_rotation())
    to_ship = actors["MenuShip"].get_actor_location() - camera
    cos = forward.dot(to_ship) / max(to_ship.length(), 1.0)
    check("camera looks at the ship", cos > 0.9, "cos %.3f" % cos)
    mesh = actors["MenuShip"].get_component_by_class(unreal.StaticMeshComponent).get_editor_property("static_mesh")
    check("ship mesh is the Vanguard", mesh is not None and mesh.get_name() == "SM_Ship_Vanguard")
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
mode = world.get_world_settings().get_editor_property("default_game_mode")
check("MainMenu game mode override", mode == unreal.SpaceMenuGameMode.static_class(), str(mode.get_name() if mode else None))

# --- Exit faces the ship ----------------------------------------------------------------------------
les.load_level("/Game/Maps/TestSpace")
planet = next(a for a in eas.get_all_level_actors() if a.get_actor_label() == "Planet_Veyra")
C = planet.get_actor_location()
R = planet.get_editor_property("radius_km") * 100000.0
up = unreal.Vector(-1.0, 0.0, 0.0)
probe = C + up * (R + 1000000.0)
spot = C + up * (R + planet.get_terrain_height_at(probe) + 250.0)
vanguard = unreal.EditorAssetLibrary.load_blueprint_class("/Game/Ships/Vanguard/Blueprints/BP_Ship_Vanguard")
ship = eas.spawn_actor_from_class(vanguard, spot, unreal.MathLibrary.make_rot_from_z(up))
try:
    ship.debug_step_flight(1.0 / 60.0, 0.0, 0.0, 0.0, False)  # samples the environment
    exit_transform = ship.compute_exit_transform()
    location = exit_transform.translation
    facing = unreal.MathLibrary.get_forward_vector(exit_transform.rotation.rotator())
    to_ship = ship.get_actor_location() - location
    to_ship = to_ship - up * to_ship.dot(up)
    cos = facing.dot(to_ship) / max(to_ship.length(), 1.0)
    check("pilot gets out facing the ship (camera away from the hull)", cos > 0.99, "cos %.4f" % cos)
    check("pilot stands upright", abs(unreal.MathLibrary.get_up_vector(exit_transform.rotation.rotator()).dot(up) - 1.0) < 1e-3)
finally:
    eas.destroy_actor(ship)

# --- Graphics quality in the menu ---------------------------------------------------------------------
# The engine calls a preset with a non-default resolution scale "custom" (-1); the menu used to show
# High then, and the next apply saved High over the player's choice. Nothing is saved here.
settings = unreal.GameUserSettings.get_game_user_settings()
saved_levels = [settings.get_view_distance_quality(), settings.get_shadow_quality()]
for level in (0, 1, 3, 4):
    settings.set_overall_scalability_level(level)
    settings.set_resolution_scale_value_ex(70.0)
    check("quality %d with 70 %% resolution scale shows as %d" % (level, level),
          settings.get_graphics_quality_level() == level and settings.get_overall_scalability_level() == -1,
          "menu %d, engine overall %d" % (settings.get_graphics_quality_level(), settings.get_overall_scalability_level()))
settings.set_shadow_quality(0)
check("mixed groups show the lowest", settings.get_graphics_quality_level() == 0)
settings.set_view_distance_quality(saved_levels[0])
settings.set_shadow_quality(saved_levels[1])

log("SUMMARY %s (%d failed: %s)" % ("OK" if not failures else "FAILED", len(failures), ", ".join(failures)))
