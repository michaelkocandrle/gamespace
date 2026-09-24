"""Checks that the level's look matches its recipe, in a fresh editor process (so only what was
saved counts): the fill from the sky light, the sun's contact shadows and size, the grade in the
unbound post process volume, and the hull's paint.

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\test_scene_look.py

Prints "LOOKTEST PASS" / "LOOKTEST FAIL" lines and a summary. Never saves.

The values themselves are not repeated here: they are read out of Tools/Assets/build_space_scene.py
and ArtSource/Ships/<Ship>/<Ship>_setup.json, so this only catches a level that was not rebuilt
after the recipe changed. Tuning them is a job for the running game (space.Post, space.Sun,
space.Sky; Source/gamespace/SpacePostTuning.cpp).
"""

import ast
import json
import os

import unreal

import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import ship_under_test as sut  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LEVEL = "/Game/Maps/TestSpace"
RECIPE = os.path.join(REPO, "Tools", "Assets", "build_space_scene.py")
WANTED = ("EXPOSURE_EV100", "SKY_LIGHT_INTENSITY", "SUN_CONTACT_SHADOW_M", "SUN_SOURCE_ANGLE_DEG", "POST_SETTINGS",
          "PLANET_NAME", "PLANET_RADIUS_CM", "PLANET_LOCATION_CM", "ATMO_HEIGHT_KM", "ATMO_RAYLEIGH_SCALE",
          "ATMO_RAYLEIGH_HEIGHT_KM", "ATMO_MIE_SCALE", "ATMO_MIE_HEIGHT_KM", "ATMO_AERIAL_DISTANCE_SCALE",
          "ATMO_GROUND_BELOW_SEA_KM")

failures = []


def log(msg):
    unreal.log("LOOKTEST " + msg)


def check(name, ok, detail=""):
    log(("PASS " if ok else "FAIL ") + name + ("  (" + detail + ")" if detail else ""))
    if not ok:
        failures.append(name)


def recipe_constants():
    """The tuning constants out of build_space_scene.py, without running the rest of it."""
    tree = ast.parse(open(RECIPE, encoding="utf-8").read(), RECIPE)
    body = [node for node in tree.body
            if isinstance(node, ast.Assign) and any(getattr(t, "id", None) in WANTED for t in node.targets)]
    namespace = {"unreal": unreal}
    exec(compile(ast.Module(body=body, type_ignores=[]), RECIPE, "exec"), namespace)
    return namespace


def close(a, b, tolerance=0.001):
    return abs(float(a) - float(b)) <= tolerance


R = recipe_constants()
check("build_space_scene.py still names every tuning constant", all(name in R for name in WANTED),
      ", ".join(sorted(set(WANTED) - set(R))))

unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()

# --- the two lights ----------------------------------------------------------------------
suns = [a.get_component_by_class(unreal.DirectionalLightComponent) for a in actors if isinstance(a, unreal.DirectionalLight)]
skies = [a.get_component_by_class(unreal.SkyLightComponent) for a in actors if isinstance(a, unreal.SkyLight)]
check("the level has one sun and one sky light", len(suns) == 1 and len(skies) == 1,
      "%d sun(s), %d sky light(s)" % (len(suns), len(skies)))

if suns:
    sun = suns[0]
    check("the sun's contact shadows are as in the recipe",
          close(sun.get_editor_property("contact_shadow_length"), R["SUN_CONTACT_SHADOW_M"]),
          "%.3f m, recipe %.3f m" % (sun.get_editor_property("contact_shadow_length"), R["SUN_CONTACT_SHADOW_M"]))
    check("the sun is as wide as in the recipe",
          close(sun.get_editor_property("light_source_angle"), R["SUN_SOURCE_ANGLE_DEG"]),
          "%.2f deg, recipe %.2f deg" % (sun.get_editor_property("light_source_angle"), R["SUN_SOURCE_ANGLE_DEG"]))

if skies:
    sky = skies[0]
    intensity = sky.get_editor_property("intensity")
    check("the sky light fills as much as in the recipe", close(intensity, R["SKY_LIGHT_INTENSITY"]),
          "%.2f, recipe %.2f" % (intensity, R["SKY_LIGHT_INTENSITY"]))
    # Below 0.5 the hull was a silhouette in space, above ~1.1 the planet lost its terminator
    # (Tools/Shots/look_fill.json, 20. 9. 2026).
    check("the sky light stays in the range the shots showed works", 0.5 <= intensity <= 1.1, "%.2f" % intensity)

# --- Veyra's atmosphere (planet reference video, 21. 9. 2026) --------------------------------
atmospheres = [a for a in actors if isinstance(a, unreal.SkyAtmosphere)]
check("one atmosphere, Veyra's", len(atmospheres) == 1 and atmospheres[0].get_actor_label() == "Atmosphere_" + R["PLANET_NAME"],
      ", ".join(a.get_actor_label() for a in atmospheres))
if atmospheres:
    atmo = atmospheres[0].get_component_by_class(unreal.SkyAtmosphereComponent)
    where = atmospheres[0].get_actor_location()
    check("centred on the planet", all(close(getattr(where, axis), R["PLANET_LOCATION_CM"][k], 1.0) for k, axis in enumerate("xyz")))
    check("its ground below the lowest terrain, so the horizon has no black band",
          close(atmo.get_editor_property("bottom_radius"), R["PLANET_RADIUS_CM"] / 100000.0 - R["ATMO_GROUND_BELOW_SEA_KM"])
          and R["ATMO_GROUND_BELOW_SEA_KM"] >= 1.6, "%.2f km" % atmo.get_editor_property("bottom_radius"))
    for key, name in (("atmosphere_height", "ATMO_HEIGHT_KM"), ("rayleigh_scattering_scale", "ATMO_RAYLEIGH_SCALE"),
                      ("rayleigh_exponential_distribution", "ATMO_RAYLEIGH_HEIGHT_KM"), ("mie_scattering_scale", "ATMO_MIE_SCALE"),
                      ("mie_exponential_distribution", "ATMO_MIE_HEIGHT_KM"),
                      ("aerial_pespective_view_distance_scale", "ATMO_AERIAL_DISTANCE_SCALE")):
        check("atmosphere %s as in the recipe" % key, close(atmo.get_editor_property(key), R[name]),
              "%.4f, recipe %.4f" % (atmo.get_editor_property(key), R[name]))
    # A halo a tenth of the planet thick, not the reference's thin limb (atmo_tune, 21. 9. 2026).
    check("a thin limb: scale height under 10 % of the radius",
          R["ATMO_RAYLEIGH_HEIGHT_KM"] < 0.1 * R["PLANET_RADIUS_CM"] / 100000.0)
if suns:
    check("the sun lights the atmosphere", suns[0].get_editor_property("atmosphere_sun_light"))

# --- the grade ---------------------------------------------------------------------------
volumes = [a for a in actors if isinstance(a, unreal.PostProcessVolume)]
unbound = [v for v in volumes if v.get_editor_property("unbound")]
check("one unbound post process volume covers the level", len(unbound) == 1, "%d of %d volumes" % (len(unbound), len(volumes)))

if unbound:
    settings = unbound[0].get_editor_property("settings")
    expected = (("auto_exposure_min_brightness", R["EXPOSURE_EV100"]),
                ("auto_exposure_max_brightness", R["EXPOSURE_EV100"])) + tuple(R["POST_SETTINGS"])
    for key, value in expected:
        on = settings.get_editor_property("override_" + key)
        have = settings.get_editor_property(key)
        if isinstance(value, unreal.Vector4):
            same = all(close(getattr(have, axis), getattr(value, axis)) for axis in ("x", "y", "z", "w"))
        else:
            same = close(have, value)
        check("the level overrides %s as in the recipe" % key, bool(on) and same, "%s, recipe %s" % (have, value))
    # Both were tried on 20. 9. 2026 and dropped: colour fringes along the cockpit's edges and a
    # blue interior (Tools/Shots/look_final.json).
    for key in ("scene_fringe_intensity", "white_temp"):
        check("the level leaves %s alone" % key, not settings.get_editor_property("override_" + key))

# --- the hull's paint (per ship: its <Ship>_setup.json, Tools/Tests/ship_under_test.py) -------------------
if not sut.SHIP:
    sut.skip(log, "the hull wears the paint from its setup JSON")
elif "base_color_tint" not in sut.setup()["materials"].get("MI_Ship_%s_Hull" % sut.SHIP, {}):
    # A hard-surface ship (hs_build_ship.py): flat paint zones on the hull master, one colour each.
    for name, spec in sut.setup()["materials"].items():
        if not isinstance(spec, dict) or spec.get("master") != "hull" or "base_color" not in spec:
            continue
        mi = unreal.EditorAssetLibrary.load_asset(sut.asset("Materials/" + name))
        have = unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(mi, "BaseColor") if mi else None
        check("%s wears the paint from %s_setup.json" % (name, sut.SHIP),
              have is not None and all(close(getattr(have, axis), spec["base_color"][i]) for i, axis in enumerate(("r", "g", "b"))),
              "%s, setup %s" % (have, spec["base_color"]))
else:
    setup = sut.setup()
    hull_name = "MI_Ship_%s_Hull" % sut.SHIP
    tint = setup["materials"][hull_name]["base_color_tint"]
    hull = unreal.EditorAssetLibrary.load_asset(sut.asset("Materials/MI_Ship_{ship}_Hull"))
    if hull:
        have = unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(hull, "BaseColorTint")
        check("the hull wears the paint from %s_setup.json" % sut.SHIP,
              all(close(getattr(have, axis), tint[i]) for i, axis in enumerate(("r", "g", "b"))),
              "%s, setup %s" % (have, tint))
        # 2.2 left it a silhouette against space, 4.5 went chalky (Tools/Shots/look_fill.json).
        check("the paint stays in the range the shots showed works", all(2.6 <= c <= 4.0 for c in tint), "%s" % tint)
    else:
        check("%s exists" % hull_name, False)

log("SUMMARY %s (%d failed: %s)" % ("OK" if not failures else "FAILED", len(failures), ", ".join(failures)))
if failures:
    unreal.log_error("LOOKTEST FAILURES: " + ", ".join(failures))
