"""The ship interior's post-process (author 6. 10. 2026): a light haze and slightly lifted blacks only inside ships - never
the global tone curve, so space and planets do not change. Values in ArtSource/Kit/kit_rules.json "interior_post".

Used by Tools/Assets/kit_rooms.py (a PostProcessComponent in a box round a ship's kit rooms, moving with the ship) and
Tools/Assets/import_kit.py (a bounded PostProcessVolume over the parts factory's test section). One function fills
the settings, so both look the same.
"""
import json
import os

import unreal

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RULES = os.path.join(REPO, "ArtSource", "Kit", "kit_rules.json")


def values():
    return json.load(open(RULES, encoding="utf-8"))["interior_post"]


def settings(v=None):
    """unreal.PostProcessSettings with the veil: contrast down, the shadows offset up, a touch less saturation."""
    v = v or values()
    s = unreal.PostProcessSettings()
    c = v["contrast"]
    s.set_editor_property("override_color_contrast", True)
    s.set_editor_property("color_contrast", unreal.Vector4(c, c, c, 1.0))
    o = v["offset_shadows"]
    s.set_editor_property("override_color_offset_shadows", True)
    s.set_editor_property("color_offset_shadows", unreal.Vector4(o[0], o[1], o[2], 0.0))
    sat = v["saturation"]
    s.set_editor_property("override_color_saturation", True)
    s.set_editor_property("color_saturation", unreal.Vector4(sat, sat, sat, 1.0))
    return s


def apply_component(pp, v=None):
    """A PostProcessComponent: bounded by its parent box, the interior's priority and blend radius."""
    v = v or values()
    pp.set_editor_property("settings", settings(v))
    pp.set_editor_property("unbound", False)
    pp.set_editor_property("priority", float(v["priority"]))
    pp.set_editor_property("blend_radius", float(v["blend_radius_cm"]))
    pp.set_editor_property("blend_weight", 1.0)


def apply_volume(vol, v=None):
    """A PostProcessVolume actor (its brush is the bounds)."""
    v = v or values()
    vol.set_editor_property("settings", settings(v))
    vol.set_editor_property("unbound", False)
    vol.set_editor_property("priority", float(v["priority"]))
    vol.set_editor_property("blend_radius", float(v["blend_radius_cm"]))
    vol.set_editor_property("blend_weight", 1.0)
