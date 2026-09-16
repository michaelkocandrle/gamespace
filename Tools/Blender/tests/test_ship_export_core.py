"""Unit tests for the bpy-free core of gamespace_ship_export.py.

    python Tools/Blender/tests/test_ship_export_core.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import gamespace_ship_export as gx  # noqa: E402

METRIC = {"unit_system": "METRIC", "scale_length": 1.0}


def mesh(name, tris=40_000, bounds=((-7, -5, -1.5), (7, 5, 1.5)), **kw):
    r = {"name": name, "type": "MESH", "parent": None, "location": (0, 0, 0), "rotation": (0, 0, 0),
         "scale": (1, 1, 1), "world_location": [0, 0, 0], "tris": tris, "verts": tris // 2, "uv_layers": 1,
         "materials": ["M_Ship_Vanguard_Hull"], "bounds": [list(bounds[0]), list(bounds[1])],
         "non_manifold_edges": 0, "loose_verts": 0, "zero_area_faces": 0}
    r.update(kw)
    return r


def hull(name, bounds=((-6.5, -4.5, -1.4), (6.5, 4.5, 1.4)), verts=24, convex=True, **kw):
    return mesh(name, tris=44, bounds=bounds, verts=verts, convex=convex, inside_out=False, materials=[], uv_layers=0, **kw)


def socket(name, parent="SM_Ship_Vanguard", location=(5.0, 0.5, 0.8)):
    return {"name": name, "type": "EMPTY", "parent": parent, "location": location, "rotation": (0, 0, 0),
            "scale": (1, 1, 1), "world_location": list(location)}


def good_ship():
    return [
        mesh("SM_Ship_Vanguard"),
        mesh("SM_Ship_Vanguard_Canopy", tris=2000, bounds=((2, -1, 0.5), (5, 1, 1.5)), materials=["M_Ship_Vanguard_Glass"]),
        mesh("SM_Ship_Vanguard_LOD1", tris=18_000),
        mesh("SM_Ship_Vanguard_LOD2", tris=8_000),
        hull("UCX_SM_Ship_Vanguard_00"),
        hull("UCX_SM_Ship_Vanguard_01", bounds=((-2, -5, -0.5), (2, 5, 0.5))),
        socket("SOCKET_Cockpit"),
        socket("SOCKET_EngineMain", location=(-7.0, 0.0, 0.0)),
        {"name": "HIGH_Vanguard", "type": "MESH", "parent": None},
        {"name": "Light", "type": "LIGHT", "parent": None},
    ]


def levels(issues, level):
    return [i for i in issues if i["level"] == level]


class ShipExportCoreTest(unittest.TestCase):
    def test_good_ship_has_no_errors_or_warnings(self):
        issues, c = gx.validate(good_ship(), METRIC)
        self.assertEqual(levels(issues, gx.ERROR), [], gx.format_issues(issues))
        self.assertEqual(levels(issues, gx.WARN), [], gx.format_issues(issues))
        self.assertEqual(sorted(c["ignored"]), ["HIGH_Vanguard", "Light"])

    def test_classification(self):
        c = gx.classify(good_ship())
        self.assertEqual(c["render"]["SM_Ship_Vanguard_Canopy"]["part"], "Canopy")
        self.assertEqual(c["render"]["SM_Ship_Vanguard_LOD2"]["lod"], 2)
        self.assertEqual(c["render"]["SM_Ship_Vanguard_LOD2"]["base"], "SM_Ship_Vanguard")
        self.assertEqual(c["collision"]["UCX_SM_Ship_Vanguard_01"]["mesh"], "SM_Ship_Vanguard")
        self.assertEqual(c["sockets"]["SOCKET_EngineMain"]["socket"], "EngineMain")

    def test_export_plan(self):
        _, c = gx.validate(good_ship(), METRIC)
        plan = dict(gx.plan_exports(c))
        self.assertEqual(plan["SM_Ship_Vanguard.fbx"], ["SM_Ship_Vanguard", "UCX_SM_Ship_Vanguard_00",
                                                        "UCX_SM_Ship_Vanguard_01", "SOCKET_Cockpit", "SOCKET_EngineMain"])
        self.assertEqual(plan["SM_Ship_Vanguard_Canopy.fbx"], ["SM_Ship_Vanguard_Canopy"])
        self.assertEqual(plan["SM_Ship_Vanguard_LOD1.fbx"], ["SM_Ship_Vanguard_LOD1"])

    def test_manifest_converts_to_unreal(self):
        _, c = gx.validate(good_ship(), METRIC)
        m = gx.build_manifest(c, gx.plan_exports(c))
        self.assertEqual(m["expected_ue_size_cm"], [1400.0, 1000.0, 300.0])
        self.assertEqual(m["sockets"]["SOCKET_Cockpit"]["location_ue_cm"], [500.0, -50.0, 80.0])
        s = m["suggested_pawn_settings"]
        self.assertEqual(s["HullCollision_BoxExtent_cm"], [650.0, 500.0, 140.0])
        self.assertEqual(s["CockpitCamera_location_ue_cm"], [500.0, -50.0, 80.0])

    def test_bad_names(self):
        issues, _ = gx.validate(good_ship() + [mesh("SM_Ship_Vanguard.001"), mesh("SM_ship_lower")], METRIC)
        bad = {i["object"] for i in levels(issues, gx.ERROR)}
        self.assertIn("SM_Ship_Vanguard.001", bad)
        self.assertIn("SM_ship_lower", bad)

    def test_units_and_transforms(self):
        records = good_ship()
        records[0]["scale"] = (0.01, 0.01, 0.01)
        records[4]["rotation"] = (0.0, 0.0, 1.57)
        issues, _ = gx.validate(records, {"unit_system": "NONE", "scale_length": 0.01})
        text = gx.format_issues(issues)
        self.assertIn("Metric", text)
        self.assertIn("scale is", text)
        self.assertIn("rotated", text)

    def test_collision_rules(self):
        records = good_ship()
        records[4] = hull("UCX_SM_Ship_Vanguard_00", convex=False, verts=300)
        records.append(hull("UCX_SM_Ship_Ghost_00"))
        issues, _ = gx.validate(records, METRIC)
        msgs = gx.format_issues(levels(issues, gx.ERROR))
        self.assertIn("Not convex", msgs)
        self.assertIn("300 vertices", msgs)
        self.assertIn("SM_Ship_Ghost", msgs)

    def test_lod_rules(self):
        records = [r for r in good_ship() if r["name"] != "SM_Ship_Vanguard_LOD1"]
        records.append(mesh("SM_Ship_Vanguard_LOD3", tris=7_900))
        issues, _ = gx.validate(records, METRIC)
        text = gx.format_issues(issues)
        self.assertIn("LODs must be consecutive", text)

    def test_socket_parent_and_orientation_and_scale(self):
        records = good_ship()
        records[6]["parent"] = None
        # Ship modelled along Y and at AI-import size (about 1.4 units).
        records[0]["bounds"] = [[-0.5, -0.7, -0.15], [0.5, 0.7, 0.15]]
        records[1]["bounds"] = [[-0.1, -0.2, 0.0], [0.1, 0.2, 0.1]]
        issues, _ = gx.validate(records, METRIC)
        text = gx.format_issues(issues)
        self.assertIn("Socket must be parented", text)
        self.assertIn("nose along +X", text)
        self.assertIn("scale mistake", text)

    def test_pivot_warning(self):
        records = good_ship()
        for r in records:
            if r["name"].startswith("UCX_"):
                r["bounds"] = [[b + 3.0 for b in r["bounds"][0]], [b + 3.0 for b in r["bounds"][1]]]
        issues, _ = gx.validate(records, METRIC)
        self.assertIn("Center on collision", gx.format_issues(issues))

    def test_budgets(self):
        records = good_ship()
        records[0]["tris"] = 1_500_000
        records[2]["tris"] = 1_000_000
        issues, _ = gx.validate(records, METRIC)
        text = gx.format_issues(issues)
        self.assertIn("far too heavy", text)
        self.assertIn("more than 60 %", text)

    def test_no_render_mesh(self):
        issues, _ = gx.validate([hull("UCX_SM_Ship_Vanguard_00")], METRIC)
        self.assertTrue(any("No render mesh" in i["message"] for i in issues))


if __name__ == "__main__":
    unittest.main(verbosity=1)
