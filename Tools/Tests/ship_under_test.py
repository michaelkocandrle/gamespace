"""The one place that names the modelled ship the headless tests check.

    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import ship_under_test as sut

SHIP is the ship's name as the pipeline spells it: ArtSource/Ships/<Ship>/ (<Ship>_setup.json,
Export/<Ship>_manifest.json, <Ship>_ai_build.json) and /Game/Ships/<Ship>/ (BP_Ship_<Ship>,
SM_Ship_<Ship>...). Set it once the ship is imported (Tools/Assets/import_ship.py).

With SHIP = None there is no modelled ship (the first fighter was removed on 24. 9. 2026; a new small
multirole ship is in 2D design):
- flight tests run on the native ASpaceshipPawn (placeholder cube hull, C++ defaults): flight_class();
- checks that need the model (its recipe, interior, sockets, gear part, materials) print a SKIP line
  (skip()) instead of failing;
- the per-ship expectations - the Blueprint carries its <Ship>_setup.json values - are skipped too.
"""

import json
import os

import unreal

# The ship under test, e.g. "Example". None: no modelled ship yet.
SHIP = None

NO_SHIP = "no ship model yet - new ship in design"
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def name():
    return SHIP


def asset(template):
    """A /Game/Ships/<Ship>/... path from a template with {ship}, e.g. 'Meshes/SM_Ship_{ship}'. None without a ship."""
    return "/Game/Ships/%s/%s" % (SHIP, template.format(ship=SHIP)) if SHIP else None


def bp_path():
    return asset("Blueprints/BP_Ship_{ship}")


def bp_class():
    """The ship's Blueprint class, or None when there is no ship. A named ship without its Blueprint is an error."""
    if not SHIP:
        return None
    cls = unreal.EditorAssetLibrary.load_blueprint_class(bp_path())
    if cls is None:
        raise RuntimeError("ship_under_test.SHIP = %r but %s does not exist - import the ship or set SHIP = None" % (SHIP, bp_path()))
    return cls


def flight_class():
    """The ship Blueprint if there is one, otherwise the native pawn with its placeholder hull."""
    return bp_class() or unreal.SpaceshipPawn


def flight_cdo():
    return unreal.get_default_object(flight_class())


def label():
    return SHIP or "native SpaceshipPawn (placeholder hull)"


def art_path(*parts):
    """A path under ArtSource/Ships/<Ship>/, with {ship} replaced. None without a ship."""
    return os.path.join(REPO, "ArtSource", "Ships", SHIP, *[p.format(ship=SHIP) for p in parts]) if SHIP else None


def _json(path):
    if path is None:
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def setup():
    """ArtSource/Ships/<Ship>/<Ship>_setup.json, or None."""
    return _json(art_path("{ship}_setup.json"))


def manifest():
    """ArtSource/Ships/<Ship>/Export/<Ship>_manifest.json, or None."""
    return _json(art_path("Export", "{ship}_manifest.json"))


def recipe():
    """ArtSource/Ships/<Ship>/<Ship>_ai_build.json, or None."""
    return _json(art_path("{ship}_ai_build.json"))


def skip(log, what):
    """Log a SKIP line for a check that needs the modelled ship. Always returns False (so `if not sut.SHIP and sut.skip(...)`)."""
    log("SKIP %s (%s)" % (what, NO_SHIP))
    return False


def check_setup_values(check, log, keys_or_prefixes, what):
    """Per-ship expectation: the ship Blueprint carries the values of its <Ship>_setup.json "pawn" section for the
    given keys (a key ending in '_' is a prefix: every setup key starting with it). Skipped without a ship."""
    if not SHIP:
        skip(log, what)
        return
    pawn = setup()["pawn"]
    keys = []
    for k in keys_or_prefixes:
        keys += [s for s in pawn if s.startswith(k) and not s.startswith("_")] if k.endswith("_") else ([k] if k in pawn else [])
    keys = [k for k in keys if isinstance(pawn[k], (int, float))]  # numbers only (lists and texts are checked elsewhere)
    cdo = unreal.get_default_object(bp_class())
    wrong = ["%s %s != %s" % (k, cdo.get_editor_property(k), pawn[k]) for k in keys
             if abs(float(cdo.get_editor_property(k)) - float(pawn[k])) > 1e-4]
    check("%s: %s from %s_setup.json (%d values)" % (SHIP, what, SHIP, len(keys)), keys and not wrong, "; ".join(wrong))
