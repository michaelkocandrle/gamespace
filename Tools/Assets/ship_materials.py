"""Ship materials: two master materials and per-ship instances from <Ship>_setup.json.

Used by Tools/Assets/import_ship.py. Editor-side only (needs `unreal`).

Masters (rebuilt on every run, like the scene materials):
    /Game/Ships/Shared/Materials/M_Ship_Hull   opaque, Nanite: BaseColor, Metallic, Roughness,
                                               EmissiveColor x EmissiveStrength
    /Game/Ships/Shared/Materials/M_Ship_Glass  translucent, two-sided, surface forward shading:
                                               BaseColor, Opacity, Roughness

Instances go to /Game/Ships/<Ship>/Materials/MI_... and are assigned to mesh slots by slot name
(the Blender material name), optionally only on the meshes an entry lists.
"""

import unreal

MEL = unreal.MaterialEditingLibrary
SHARED = "/Game/Ships/Shared/Materials"
MASTERS = {"hull": SHARED + "/M_Ship_Hull", "glass": SHARED + "/M_Ship_Glass"}


def _asset_tools():
    return unreal.AssetToolsHelpers.get_asset_tools()


def _fresh_material(path):
    material = unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if material is None:
        folder, name = path.rsplit("/", 1)
        material = _asset_tools().create_asset(name, folder, unreal.Material, unreal.MaterialFactoryNew())
    else:
        for expr in list(MEL.get_material_expressions(material)):
            MEL.delete_material_expression(material, expr)
    return material


def _node(material, cls, x, y, **properties):
    expr = MEL.create_material_expression(material, cls, x, y)
    for key, value in properties.items():
        expr.set_editor_property(key, value)
    return expr


def _link(src, dst, dst_input):
    if not MEL.connect_material_expressions(src, "", dst, dst_input):
        raise RuntimeError("could not connect %s -> %s.%s" % (src.get_class().get_name(), dst.get_class().get_name(), dst_input))


def _output(src, prop):
    if not MEL.connect_material_property(src, "", prop):
        raise RuntimeError("could not connect %s -> %s" % (src.get_class().get_name(), prop))


def _vector(material, name, default, x, y):
    return _node(material, unreal.MaterialExpressionVectorParameter, x, y, parameter_name=name,
                 default_value=unreal.LinearColor(default[0], default[1], default[2], 1.0))


def _scalar(material, name, default, x, y):
    return _node(material, unreal.MaterialExpressionScalarParameter, x, y, parameter_name=name, default_value=default)


def build_masters():
    hull = _fresh_material(MASTERS["hull"])
    hull.set_editor_property("used_with_nanite", True)
    _output(_vector(hull, "BaseColor", (0.35, 0.35, 0.35), -600, 0), unreal.MaterialProperty.MP_BASE_COLOR)
    _output(_scalar(hull, "Metallic", 0.3, -600, 150), unreal.MaterialProperty.MP_METALLIC)
    _output(_scalar(hull, "Roughness", 0.5, -600, 250), unreal.MaterialProperty.MP_ROUGHNESS)
    emissive = _node(hull, unreal.MaterialExpressionMultiply, -300, 400)
    _link(_vector(hull, "EmissiveColor", (0.0, 0.0, 0.0), -600, 400), emissive, "A")
    _link(_scalar(hull, "EmissiveStrength", 0.0, -600, 550), emissive, "B")
    _output(emissive, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(hull)
    unreal.EditorAssetLibrary.save_loaded_asset(hull, only_if_is_dirty=False)

    glass = _fresh_material(MASTERS["glass"])
    glass.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    glass.set_editor_property("two_sided", True)
    glass.set_editor_property("translucency_lighting_mode", unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
    _output(_vector(glass, "BaseColor", (0.25, 0.35, 0.4), -600, 0), unreal.MaterialProperty.MP_BASE_COLOR)
    _output(_scalar(glass, "Opacity", 0.2, -600, 150), unreal.MaterialProperty.MP_OPACITY)
    _output(_scalar(glass, "Roughness", 0.03, -600, 250), unreal.MaterialProperty.MP_ROUGHNESS)
    _output(_node(glass, unreal.MaterialExpressionConstant, -600, 350, r=1.0), unreal.MaterialProperty.MP_SPECULAR)
    MEL.recompile_material(glass)
    unreal.EditorAssetLibrary.save_loaded_asset(glass, only_if_is_dirty=False)
    return {"hull": hull, "glass": glass}


def build_instance(name, folder, spec, masters):
    path = "%s/%s" % (folder, name)
    mi = unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if mi is None:
        mi = _asset_tools().create_asset(name, folder, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, masters[spec["master"]])
    for key, param in (("base_color", "BaseColor"), ("emissive_color", "EmissiveColor")):
        if key in spec:
            c = spec[key]
            MEL.set_material_instance_vector_parameter_value(mi, param, unreal.LinearColor(c[0], c[1], c[2], 1.0))
    for key, param in (("metallic", "Metallic"), ("roughness", "Roughness"), ("emissive_strength", "EmissiveStrength"), ("opacity", "Opacity")):
        if key in spec:
            MEL.set_material_instance_scalar_parameter_value(mi, param, float(spec[key]))
    MEL.update_material_instance(mi)
    unreal.EditorAssetLibrary.save_loaded_asset(mi, only_if_is_dirty=False)
    return mi


def apply(ship, setup, mesh_assets):
    """setup: the parsed <Ship>_setup.json. mesh_assets: {mesh name: StaticMesh}. Returns notes."""
    specs = setup.get("materials") or {}
    if not specs:
        return []
    masters = build_masters()
    folder = "/Game/Ships/%s/Materials" % ship
    notes = []
    # Mesh-specific entries win over general ones for the same slot.
    ordered = sorted(specs.items(), key=lambda kv: 1 if kv[1].get("meshes") else 0)
    instances = {name: build_instance(name, folder, spec, masters) for name, spec in ordered}
    for mesh_name, mesh in mesh_assets.items():
        slots = mesh.get_editor_property("static_materials")
        for index, slot in enumerate(slots):
            slot_name = str(slot.get_editor_property("material_slot_name"))
            chosen = None
            for name, spec in ordered:
                if slot_name in spec.get("slots", []) and (not spec.get("meshes") or mesh_name in spec["meshes"]):
                    chosen = name
            if chosen is None:
                notes.append("%s slot %s has no material in the setup" % (mesh_name, slot_name))
                continue
            mesh.set_material(index, instances[chosen])
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
    notes.append("%d material instances, masters %s" % (len(instances), ", ".join(MASTERS.values())))
    return notes
