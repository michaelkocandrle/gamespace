"""Re-applies a ship's material instances from <Ship>_setup.json without importing its meshes again: for tuning
material parameters (the slots keep the instances import_ship.py gave them, textures stay as imported). Uses the
masters as they are on disk (rebuilt by import_ship.py, import_kit.py or probe_pbr_flat.py).

    .\\Tools\\run_editor_python.ps1 Tools\\Assets\\apply_ship_materials.py

Ship: GAMESPACE_SHIP, else Tools/Tests/ship_under_test.py. GAMESPACE_MATS: comma-separated parts of instance names
to touch (default all) - every instance it touches is saved again, so narrow it to the ones that changed.
"""
import json
import os
import re
import sys

import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import ship_materials  # noqa: E402


def main():
    ship = os.environ.get("GAMESPACE_SHIP")
    if not ship:
        src = open(os.path.join(REPO, "Tools", "Tests", "ship_under_test.py"), encoding="utf-8").read()
        ship = re.search(r'^SHIP = "([^"]+)"', src, re.M).group(1)
    only = [s for s in os.environ.get("GAMESPACE_MATS", "").split(",") if s]
    setup = json.load(open(os.path.join(REPO, "ArtSource", "Ships", ship, "%s_setup.json" % ship), encoding="utf-8"))
    masters = {k: unreal.EditorAssetLibrary.load_asset(p) for k, p in ship_materials.MASTERS.items()
               if unreal.EditorAssetLibrary.does_asset_exist(p)}
    folder = "/Game/Ships/%s/Materials" % ship
    done = []
    for name, spec in setup.get("materials", {}).items():
        if not isinstance(spec, dict) or spec.get("master") not in masters or (only and not any(o in name for o in only)):
            continue
        # the textures are left as imported: importing them again would only re-save the same assets
        ship_materials.build_instance(name, folder, {k: v for k, v in spec.items() if k != "textures"}, masters, ship)
        done.append(name)
    unreal.log("APPLYMATS %s: %d instances %s" % (ship, len(done), ", ".join(done)))


main()
