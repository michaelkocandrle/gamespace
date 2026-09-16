"""Tests for the Unreal-free part of Tools/Assets/import_ship.py (plan, size checks, dry run).

    python Tools/Assets/tests/test_import_ship_plan.py
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "Blender", "tests"))
import import_ship  # noqa: E402
import test_ship_export_core as blender_tests  # noqa: E402


class ImportPlanTest(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(json.dumps(blender_tests.good_manifest()))
        self.plan = import_ship.build_plan(self.manifest, "C:/art/Vanguard/Export")

    def test_meshes_main_first_lods_skipped(self):
        names = [m["name"] for m in self.plan["meshes"]]
        self.assertEqual(names, ["SM_Ship_Vanguard", "SM_Ship_Vanguard_Canopy"])
        self.assertEqual(sorted(self.plan["skipped_lods"]), ["SM_Ship_Vanguard_LOD1.fbx", "SM_Ship_Vanguard_LOD2.fbx"])
        main = self.plan["meshes"][0]
        self.assertEqual(main["asset_path"], "/Game/Ships/Vanguard/Meshes/SM_Ship_Vanguard")
        self.assertEqual(main["collision_hulls"], 2)
        self.assertEqual(sorted(main["sockets"]), ["SOCKET_Cockpit", "SOCKET_EngineMain"])
        self.assertEqual(main["expected_size_cm"], [1400.0, 1000.0, 300.0])
        self.assertTrue(main["fbx"].endswith("SM_Ship_Vanguard.fbx"))

    def test_glass_parts_skip_nanite_and_become_components(self):
        canopy = self.plan["meshes"][1]
        self.assertFalse(canopy["nanite"])
        self.assertTrue(self.plan["meshes"][0]["nanite"])
        self.assertEqual(self.plan["extra_components"][0]["component"], "Canopy")
        self.assertTrue(import_ship.is_glass_part("SM_Ship_X_Top", {"materials": ["M_Ship_X_Glass"]}))
        self.assertFalse(import_ship.is_glass_part("SM_Ship_X_Wing", {"materials": ["M_Ship_X_Hull"]}))

    def test_pawn_settings_come_from_the_manifest(self):
        settings = {(c, p): v for c, p, v in self.plan["pawn_settings"]}
        s = self.manifest["suggested_pawn_settings"]
        self.assertEqual(settings[("hull_collision", "box_extent")], s["HullCollision_BoxExtent_cm"])
        self.assertEqual(settings[("camera_boom", "target_arm_length")], s["CameraBoom_TargetArmLength_cm"])
        self.assertEqual(settings[(None, "landing_footprint_radius_cm")], s["LandingFootprintRadiusCm"])
        self.assertEqual(settings[("hull", "relative_scale3d")], [1.0, 1.0, 1.0])
        self.assertEqual(settings[("cockpit_camera", "relative_location")], s["CockpitCamera_location_ue_cm"])
        self.assertEqual(dict(self.plan["planet_settings"])["collision_min_radius_m"], s["Planet_CollisionMinRadiusM"])

    def test_every_suggested_setting_is_used(self):
        used = set()
        text = import_ship.format_plan(self.plan)
        for key, value in self.manifest["suggested_pawn_settings"].items():
            if key == "HullCollision_center_offset_ue_cm":
                continue  # applied through Hull_RelativeLocation_cm
            used.add(key)
            self.assertIn(str(value), text, key)
        self.assertTrue(used)

    def test_no_cockpit_socket(self):
        self.manifest["suggested_pawn_settings"]["CockpitCamera_location_ue_cm"] = None
        plan = import_ship.build_plan(self.manifest, ".")
        self.assertNotIn("cockpit_camera", [c for c, _, _ in plan["pawn_settings"]])

    def test_size_verdicts(self):
        expected = [1400.0, 1000.0, 300.0]
        self.assertEqual(import_ship.compare_size([1402.0, 998.0, 301.0], expected), "ok")
        self.assertEqual(import_ship.compare_size([14.0, 10.0, 3.0], expected), "unit")
        self.assertEqual(import_ship.compare_size([1000.0, 1400.0, 300.0], expected), "rotated")
        self.assertEqual(import_ship.compare_size([700.0, 500.0, 150.0], expected), "wrong")

    def test_socket_names(self):
        self.assertEqual(import_ship.socket_key("SOCKET_Cockpit"), "Cockpit")
        self.assertEqual(import_ship.socket_key("Cockpit"), "Cockpit")

    def test_dry_run_from_the_command_line(self):
        script = os.path.join(HERE, "..", "import_ship.py")
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "Vanguard_manifest.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.manifest, f)
            missing = subprocess.run([sys.executable, script, path], capture_output=True, text=True)
            self.assertEqual(missing.returncode, 1)
            self.assertIn("File not found", missing.stdout)
            for entry in self.manifest["files"]:
                open(os.path.join(folder, entry["fbx"]), "wb").close()
            ok = subprocess.run([sys.executable, script, path], capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
            self.assertIn("dry run", ok.stdout)
            self.assertIn("BP_Ship_Vanguard", ok.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
