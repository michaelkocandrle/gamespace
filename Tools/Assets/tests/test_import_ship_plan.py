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
        self.plan = import_ship.build_plan(self.manifest, "C:/art/Testship/Export")

    def test_meshes_main_first_lods_skipped(self):
        names = [m["name"] for m in self.plan["meshes"]]
        self.assertEqual(names, ["SM_Ship_Testship", "SM_Ship_Testship_Canopy"])
        self.assertEqual(sorted(self.plan["skipped_lods"]), ["SM_Ship_Testship_LOD1.fbx", "SM_Ship_Testship_LOD2.fbx"])
        main = self.plan["meshes"][0]
        self.assertEqual(main["asset_path"], "/Game/Ships/Testship/Meshes/SM_Ship_Testship")
        self.assertEqual(main["collision_hulls"], 2)
        self.assertEqual(sorted(main["sockets"]), ["SOCKET_Cockpit", "SOCKET_EngineMain"])
        self.assertEqual(main["expected_size_cm"], [1400.0, 1000.0, 300.0])
        self.assertTrue(main["fbx"].endswith("SM_Ship_Testship.fbx"))

    def test_glass_parts_skip_nanite_and_become_components(self):
        canopy = self.plan["meshes"][1]
        self.assertFalse(canopy["nanite"])
        self.assertTrue(self.plan["meshes"][0]["nanite"])
        self.assertEqual(self.plan["extra_components"][0]["component"], "Canopy")
        self.assertTrue(import_ship.is_glass_part("SM_Ship_X_Top", {"materials": ["M_Ship_X_Glass"]}))
        self.assertFalse(import_ship.is_glass_part("SM_Ship_X_Wing", {"materials": ["M_Ship_X_Hull"]}))
        # A hull with small glass bits keeps Nanite.
        self.assertFalse(import_ship.is_glass_part("SM_Ship_X", {"materials": ["M_Ship_X_Hull", "M_Ship_X_Glass"]}))

    def test_setup_can_turn_nanite_off_for_a_part(self):
        manifest = json.loads(json.dumps(self.manifest))
        manifest["meshes"]["SM_Ship_Testship"]["part"] = "Interior"
        without = import_ship.build_plan(manifest, "C:/art/Testship/Export")
        with_setup = import_ship.build_plan(manifest, "C:/art/Testship/Export", {"no_nanite_parts": ["Interior"]})
        self.assertTrue(without["meshes"][0]["nanite"])
        self.assertFalse(with_setup["meshes"][0]["nanite"])

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

    def test_setup_file_overrides_manifest_in_order(self):
        setup = {"pawn": {"_comment": "x", "pitch_rate": 70.0, "hide_hull_in_cockpit": False},
                 "components": {"camera_boom": {"target_arm_length": 1450.0},
                                "cockpit_camera": {"relative_location": [300.0, 0.0, 78.0]}},
                 "materials": {"MI_A": {"master": "hull", "slots": ["M_Ship_Testship_Hull"]}}}
        plan = import_ship.build_plan(self.manifest, "C:/art/Testship/Export", setup)
        settings = {}
        for c, p, v in plan["pawn_settings"]:
            settings[(c, p)] = v  # later entries win, as in apply_pawn_settings
        self.assertEqual(settings[("camera_boom", "target_arm_length")], 1450.0)
        self.assertEqual(settings[("cockpit_camera", "relative_location")], [300.0, 0.0, 78.0])
        self.assertIs(settings[(None, "hide_hull_in_cockpit")], False)
        self.assertNotIn((None, "_comment"), settings)
        self.assertIn("MI_A", plan["materials"])
        self.assertIn("material MI_A (hull)", import_ship.format_plan(plan))
        self.assertEqual(import_ship.setup_path("C:/art/Testship/Export", "Testship").replace("\\", "/"),
                         "C:/art/Testship/Testship_setup.json")

    def test_setup_covers_every_material_slot(self):
        # A synthetic ship folder laid out like ArtSource/Ships/<Ship>/: <Ship>_setup.json next to Export/.
        with tempfile.TemporaryDirectory() as root:
            ship_dir = os.path.join(root, "Testship")
            export_dir = os.path.join(ship_dir, "Export")
            os.makedirs(os.path.join(ship_dir, "Textures"))
            os.makedirs(export_dir)
            with open(os.path.join(export_dir, "Testship_manifest.json"), "w", encoding="utf-8") as f:
                json.dump(self.manifest, f)
            texture = os.path.join(ship_dir, "Textures", "T_Ship_Testship_BC.png")
            open(texture, "wb").close()
            setup_file = import_ship.setup_path(export_dir, "Testship")
            self.assertEqual(os.path.normcase(setup_file), os.path.normcase(os.path.join(ship_dir, "Testship_setup.json")))
            self.assertEqual(import_ship.load_setup(setup_file), {})  # no setup file yet: no hand tuning
            with open(setup_file, "w", encoding="utf-8") as f:
                json.dump({
                    "_comment": "Synthetic setup for the tests.",
                    "no_nanite_parts": ["Interior"],
                    "materials": {
                        "_comment": "A note, dropped by the plan.",
                        "MI_Ship_Testship_Hull": {"master": "pbr", "slots": ["M_Ship_Testship_Hull"],
                                                  "textures": {"base_color": texture}},
                        "MI_Ship_Testship_Glass": {"master": "glass", "slots": ["M_Ship_Testship_Glass"],
                                                   "meshes": ["SM_Ship_Testship_Canopy"]},
                    },
                }, f)

            with open(os.path.join(export_dir, "Testship_manifest.json"), encoding="utf-8") as f:
                manifest = json.load(f)
            setup = import_ship.load_setup(setup_file)
            self.assertTrue(setup)
            # Keys starting with _ are notes, as everywhere in the setup file.
            materials = {n: spec for n, spec in setup["materials"].items() if not n.startswith("_")}
            for mesh_name, info in manifest["meshes"].items():
                if info["lod"] != 0:
                    continue
                for slot in info["materials"]:
                    matches = [n for n, spec in materials.items()
                               if slot in spec["slots"] and (not spec.get("meshes") or mesh_name in spec["meshes"])]
                    self.assertTrue(matches, "%s slot %s has no material" % (mesh_name, slot))
                    self.assertIn(materials[matches[0]]["master"], ("hull", "pbr", "glass", "screen"))
            # A see-through canopy part gets the glass master.
            canopy = [n for n, spec in materials.items() if "SM_Ship_Testship_Canopy" in spec.get("meshes", [])]
            self.assertEqual(canopy, ["MI_Ship_Testship_Glass"])
            self.assertTrue(all(materials[n]["master"] == "glass" for n in canopy))
            # PBR entries name textures that exist.
            for name, spec in materials.items():
                for key, source in (spec.get("textures") or {}).items():
                    self.assertTrue(os.path.isfile(os.path.join(import_ship.REPO, source)), "%s %s: %s" % (name, key, source))
            # The plan drops the notes too and keeps the real entries.
            plan = import_ship.build_plan(manifest, export_dir, setup)
            self.assertFalse([n for n in plan["materials"] if n.startswith("_")])
            self.assertEqual(sorted(plan["materials"]), ["MI_Ship_Testship_Glass", "MI_Ship_Testship_Hull"])

    def test_dry_run_from_the_command_line(self):
        script = os.path.join(HERE, "..", "import_ship.py")
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "Testship_manifest.json")
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
            self.assertIn("BP_Ship_Testship", ok.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
