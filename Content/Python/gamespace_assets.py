"""Script-authored assets for gamespace: Enhanced Input, data assets, curve and data tables.

Runs inside the Unreal Editor's Python (PythonScriptPlugin), either headless through
Tools/run_editor_python.ps1 or from the editor's Python console. Content/Python is on
sys.path in both cases, so a script only needs:

    import gamespace_assets as ga

    thrust = ga.input_action("/Game/Input/IA_Boost", "bool")
    look = ga.existing("/Game/Input/IA_Look")          # reference, never modified
    ga.mapping_context("/Game/Input/IMC_Debug", [
        ga.Map(thrust, "LeftShift", triggers=["Pressed"]),
        ga.Map(look, "Up", swizzle="YXZ"),
        ga.Map(look, "Down", swizzle="YXZ", negate=True),
    ])

Safety model
------------
Nothing that already exists is touched unless the caller says so for that one call:

    on_exists="error"   (default) raise AssetExistsError, asset untouched
    on_exists="skip"    return the existing asset unmodified
    on_exists="update"  rewrite the listed properties in place (IMC: mappings are REPLACED)

This matters beyond scripts: AssetTools.create_asset() on an existing path pops a
"Replace?" dialog in the interactive editor and overwrites on Yes. Headless it just
returns None. Neither is acceptable for hand-authored assets, so existence is checked
here before any factory runs.

Existing assets are never deleted and recreated either. Deleting and recreating the same
path inside one editor session is unreliable: the old package lingers in memory and the
create fails with "already exists".

Verified against UE 5.8
-----------------------
- UInputAction: ValueType and AccumulationBehavior are settable.
- UInputMappingContext: key mappings including per-mapping Modifiers and Triggers, with
  modifier settings (Negate per axis, Swizzle order) surviving save and reload in a fresh
  process. See the limitation on map_key() below for why it is done the way it is.
- UDataAsset subclasses via DataAssetFactory.
- UCurveTable rows and keys via DataTableFunctionLibrary.
- UDataTable rows from JSON.

Known limitations
-----------------
- UInputMappingContext.map_key() returns the new FEnhancedActionKeyMapping *by value* in
  Python. Adding modifiers to the returned struct silently changes nothing on the asset.
  The mapping array is therefore built in full and written back through
  default_key_mappings, with each modifier/trigger object created with the IMC as outer.
- UCurveFloat / UCurveVector / UCurveLinearColor keys are not reachable: the FRichCurve
  data is a bare UPROPERTY() that Python does not expose, and the CSV/JSON import
  functions on UCurveBase are not UFUNCTIONs. Use a CurveTable, or hand-edit.
- CurveTable keys added through AddCurveTableKey are simple curves (linear
  interpolation). No cubic tangents.
- Only properties marked EditAnywhere / BlueprintReadWrite / BlueprintReadOnly are
  reachable. A property declared as bare UPROPERTY() can't be set from Python at all.
- PlayerMappableKeySettings on mappings is untested.
"""

import json

import unreal

__all__ = [
    "AssetExistsError",
    "Map",
    "add_mappings",
    "curve_table",
    "data_asset",
    "data_table",
    "existing",
    "existing_or_none",
    "import_file",
    "input_action",
    "mapping_context",
]

_EAL = unreal.EditorAssetLibrary
_ON_EXISTS = ("error", "skip", "update")


class AssetExistsError(RuntimeError):
    """The target path already holds an asset and on_exists did not allow touching it."""


# ---------------------------------------------------------------------------------------
# Shared plumbing
# ---------------------------------------------------------------------------------------


def _split(path):
    """'/Game/Input/IA_X' or '/Game/Input/IA_X.IA_X' -> ('/Game/Input', 'IA_X')."""
    if not path.startswith("/Game/"):
        raise ValueError("asset path must live under /Game/: %r" % path)
    package = path.split(".", 1)[0]
    folder, name = package.rsplit("/", 1)
    if not name:
        raise ValueError("asset path has no asset name: %r" % path)
    return folder, name


def _prepare(path, on_exists):
    """Returns the existing asset to update/skip, or None if a new one should be created."""
    if on_exists not in _ON_EXISTS:
        raise ValueError("on_exists must be one of %s, got %r" % (_ON_EXISTS, on_exists))
    folder, name = _split(path)
    package = "%s/%s" % (folder, name)
    if not _EAL.does_asset_exist(package):
        return None
    if on_exists == "error":
        raise AssetExistsError(
            "%s already exists; pass on_exists='skip' to use it or 'update' to modify it" % package
        )
    asset = _EAL.load_asset(package)
    if asset is None:
        raise RuntimeError("%s exists but failed to load" % package)
    return asset


def _create(path, asset_class, factory):
    folder, name = _split(path)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset = tools.create_asset(name, folder, asset_class, factory)
    if asset is None:
        raise RuntimeError("could not create %s/%s (see LogAssetTools)" % (folder, name))
    return asset


def _save(asset):
    if not _EAL.save_loaded_asset(asset, only_if_is_dirty=False):
        raise RuntimeError("failed to save %s" % asset.get_path_name())
    unreal.log("gamespace_assets: saved %s" % asset.get_path_name())
    return asset


def _enum(enum_type, value, aliases=None):
    """Accepts the enum member itself or a forgiving string ('axis1d', 'Cumulative', ...)."""
    if isinstance(value, enum_type):
        return value
    wanted = str(value).upper().replace(" ", "_").replace("-", "_")
    wanted = (aliases or {}).get(wanted, wanted)
    members = [n for n in dir(enum_type) if n.isupper()]
    for name in members:
        if name == wanted or name.replace("_", "") == wanted.replace("_", ""):
            return getattr(enum_type, name)
    raise ValueError("%r is not a %s; expected one of %s" % (value, enum_type.__name__, members))


def _set_properties(obj, properties):
    for name, value in (properties or {}).items():
        obj.set_editor_property(name, value)


def _resolve_class(cls):
    """An unreal class, or a path: '/Script/gamespace.MyData' or '/Game/X/BP_Y.BP_Y_C'."""
    if isinstance(cls, str):
        loaded = unreal.load_class(None, cls)
        if loaded is None:
            raise ValueError("class not found: %r" % cls)
        return loaded
    return cls


def existing_or_none(path):
    """Like existing(), but returns None instead of raising when there is no asset."""
    folder, name = _split(path)
    package = "%s/%s" % (folder, name)
    return _EAL.load_asset(package) if _EAL.does_asset_exist(package) else None


def existing(path):
    """Loads an asset for reference only (e.g. an IA inside a new IMC). Never modifies it."""
    folder, name = _split(path)
    package = "%s/%s" % (folder, name)
    if not _EAL.does_asset_exist(package):
        raise ValueError("%s does not exist" % package)
    return _EAL.load_asset(package)


# ---------------------------------------------------------------------------------------
# Enhanced Input
# ---------------------------------------------------------------------------------------

_VALUE_TYPE_ALIASES = {"BOOL": "BOOLEAN", "DIGITAL": "BOOLEAN", "FLOAT": "AXIS1D", "VECTOR2D": "AXIS2D"}


def input_action(path, value_type, accumulation=None, triggers=None, properties=None, on_exists="error"):
    """Creates a UInputAction.

    value_type:   "bool" | "axis1d" | "axis2d" | "axis3d" (or unreal.InputActionValueType)
    accumulation: None (engine default, TakeHighestAbsoluteValue) | "cumulative" |
                  "take_highest_absolute_value". Use cumulative on 1D axes with opposed keys.
    triggers:     action-level triggers, applying to every key mapped to it, same form as on
                  Map: ["Pressed"] or [("Hold", {"hold_time_threshold": 0.5})].
    properties:   any other editable UInputAction property, e.g. {"consume_input": False}
    """
    value_type = _enum(unreal.InputActionValueType, value_type, _VALUE_TYPE_ALIASES)
    if accumulation is not None:
        accumulation = _enum(unreal.InputActionAccumulationBehavior, accumulation)
    triggers = list(triggers or [])
    _validate_instanced("InputTrigger", triggers)

    asset = _prepare(path, on_exists)
    if asset is not None and on_exists == "skip":
        return asset
    if asset is None:
        asset = _create(path, unreal.InputAction, unreal.InputAction_Factory())

    asset.set_editor_property("value_type", value_type)
    if accumulation is not None:
        asset.set_editor_property("accumulation_behavior", accumulation)
    if triggers or on_exists == "update":
        asset.set_editor_property("triggers", [_instanced("InputTrigger", t, asset) for t in triggers])
    _set_properties(asset, properties)
    return _save(asset)


class Map(object):
    """One key mapping inside a mapping context.

    Map(action, "S", negate=True)
    Map(action, "Up", swizzle="YXZ")                      1D key onto the Y of a 2D action
    Map(action, "Down", swizzle="YXZ", negate=True)       applied swizzle first, then negate
    Map(action, "LeftShift", triggers=["Pressed"])
    Map(action, "Gamepad_LeftX", modifiers=[("DeadZone", {"lower_threshold": 0.2})])

    negate:    True for all axes, or a subset string like "x" / "xy".
    modifiers: extra (name, properties) pairs, applied after swizzle and negate. The name is
               the class suffix: "Scalar" -> unreal.InputModifierScalar.
    triggers:  names or (name, properties) pairs: "Pressed" -> unreal.InputTriggerPressed.
    Key names are FKey names ("SpaceBar", "LeftControl", "Mouse2D", "Gamepad_Right2D") and are
    validated, because the engine otherwise accepts any string and silently maps nothing.
    """

    def __init__(self, action, key, negate=False, swizzle=None, modifiers=None, triggers=None):
        if action is None:
            raise ValueError("Map(%r): action is None" % key)
        self.action = action
        self.key = key
        self.negate = negate
        self.swizzle = swizzle
        self.modifiers = list(modifiers or [])
        self.triggers = list(triggers or [])


def _validate_instanced(prefix, specs):
    for item in specs:
        name = item if isinstance(item, str) else item[0]
        if getattr(unreal, prefix + name, None) is None:
            raise ValueError("unknown %s type %r (no unreal.%s%s)" % (prefix, name, prefix, name))


def _instanced(prefix, spec, outer):
    name, properties = (spec, None) if isinstance(spec, str) else spec
    cls = getattr(unreal, prefix + name, None)
    if cls is None:
        raise ValueError("unknown %s type %r (no unreal.%s%s)" % (prefix, name, prefix, name))
    # The owning asset must be the outer: these are Instanced subobjects and serialise inside it.
    obj = unreal.new_object(cls, outer=outer)
    _set_properties(obj, properties)
    return obj


def _key(name):
    key = unreal.Key()
    key.set_editor_property("key_name", name)
    if not unreal.InputLibrary.key_is_valid(key):
        raise ValueError("%r is not a valid FKey name" % name)
    return key


def _validate_mapping(spec):
    """Fails before any asset is created, so a typo cannot leave a half-built IMC behind."""
    _key(spec.key)
    if spec.swizzle:
        _enum(unreal.InputAxisSwizzle, spec.swizzle)
    _validate_instanced("InputModifier", spec.modifiers)
    _validate_instanced("InputTrigger", spec.triggers)


def _build_mapping(spec, imc):
    mapping = unreal.EnhancedActionKeyMapping()
    mapping.set_editor_property("action", spec.action)
    mapping.set_editor_property("key", _key(spec.key))

    modifiers = []
    if spec.swizzle:
        modifiers.append(
            _instanced("InputModifier", ("SwizzleAxis", {"order": _enum(unreal.InputAxisSwizzle, spec.swizzle)}), imc)
        )
    if spec.negate:
        axes = "xyz" if spec.negate is True else str(spec.negate).lower()
        modifiers.append(
            _instanced("InputModifier", ("Negate", {"x": "x" in axes, "y": "y" in axes, "z": "z" in axes}), imc)
        )
    modifiers.extend(_instanced("InputModifier", m, imc) for m in spec.modifiers)
    mapping.set_editor_property("modifiers", modifiers)

    mapping.set_editor_property("triggers", [_instanced("InputTrigger", t, imc) for t in spec.triggers])
    return mapping


def mapping_context(path, mappings, description=None, on_exists="error"):
    """Creates a UInputMappingContext from a list of Map.

    With on_exists="update" the context's default mappings are REPLACED by `mappings`, not
    merged - the script is the source of truth for that asset from then on.
    """
    for spec in mappings:
        if not isinstance(spec, Map):
            raise TypeError("mappings must be Map instances, got %r" % (spec,))
        _validate_mapping(spec)

    asset = _prepare(path, on_exists)
    if asset is not None and on_exists == "skip":
        return asset
    if asset is None:
        asset = _create(path, unreal.InputMappingContext, unreal.InputMappingContext_Factory())

    # Not map_key(): in Python it returns a copy, so modifiers added to it never reach the asset.
    data = asset.get_editor_property("default_key_mappings")
    data.set_editor_property("mappings", [_build_mapping(spec, asset) for spec in mappings])
    asset.set_editor_property("default_key_mappings", data)
    if description is not None:
        asset.set_editor_property("context_description", description)
    return _save(asset)


def _snapshot(mapping):
    """Identity of one mapping, down to the exact modifier/trigger objects it references."""
    action = mapping.get_editor_property("action")
    return (
        action.get_path_name() if action else None,
        str(mapping.get_editor_property("key").get_editor_property("key_name")),
        tuple(m.get_path_name() for m in mapping.get_editor_property("modifiers")),
        tuple(t.get_path_name() for t in mapping.get_editor_property("triggers")),
    )


def add_mappings(path, mappings):
    """Appends mappings to an EXISTING mapping context, leaving every current mapping as is.

    This is the safe way to extend a hand-authored context. A Map whose action and key are
    already mapped is skipped rather than duplicated, so re-running a script is harmless.
    Before saving, the original mappings are compared against a snapshot - including the
    identity of their modifier and trigger objects - and the save is refused on any drift.

    Returns the number of mappings actually added.
    """
    for spec in mappings:
        if not isinstance(spec, Map):
            raise TypeError("mappings must be Map instances, got %r" % (spec,))
        _validate_mapping(spec)

    asset = existing(path)
    if not isinstance(asset, unreal.InputMappingContext):
        raise TypeError("%s is a %s, not an InputMappingContext" % (path, asset.get_class().get_name()))

    data = asset.get_editor_property("default_key_mappings")
    current = list(data.get_editor_property("mappings"))
    before = [_snapshot(m) for m in current]
    mapped = set((a, k) for a, k, _, _ in before)

    added = []
    for spec in mappings:
        pair = (spec.action.get_path_name(), spec.key)
        if pair in mapped:
            unreal.log("gamespace_assets: %s already maps %s to %s, skipped" % (path, spec.key, spec.action.get_name()))
            continue
        mapped.add(pair)
        added.append(_build_mapping(spec, asset))

    if not added:
        return 0

    data.set_editor_property("mappings", current + added)
    asset.set_editor_property("default_key_mappings", data)

    after = [_snapshot(m) for m in asset.get_editor_property("default_key_mappings").get_editor_property("mappings")]
    if after[: len(before)] != before or len(after) != len(before) + len(added):
        # Nothing has been written to disk yet. Reload from disk so an open editor cannot save
        # the half-applied edit later; raise whether or not that succeeds.
        try:
            unreal.EditorLoadingAndSavingUtils.reload_packages([asset.get_package()])
        except Exception as exc:
            unreal.log_error("gamespace_assets: could not reload %s, do not save it: %s" % (path, exc))
        raise RuntimeError("existing mappings in %s changed while appending; nothing was saved" % path)

    _save(asset)
    return len(added)


# ---------------------------------------------------------------------------------------
# Other asset types
# ---------------------------------------------------------------------------------------


def import_file(path, source_file, properties=None, on_exists="error"):
    """Imports a file (texture, mesh, ...) through the editor's normal importer.

    The asset type follows from the file: .png -> Texture2D, a 2:1 long-lat .hdr ->
    TextureCube, .obj / .fbx -> StaticMesh. properties are set on the imported asset.
    With on_exists="update" the existing asset is reimported from source_file in place.
    """
    import os

    if not os.path.isfile(source_file):
        raise ValueError("source file not found: %r" % source_file)
    folder, name = _split(path)
    asset = _prepare(path, on_exists)
    if asset is not None and on_exists == "skip":
        return asset

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", source_file)
    task.set_editor_property("destination_path", folder)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", False)
    # Only reached for "update"; _prepare() has already refused an existing asset otherwise.
    task.set_editor_property("replace_existing", asset is not None)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    package = "%s/%s" % (folder, name)
    if not _EAL.does_asset_exist(package):
        raise RuntimeError("import of %s produced no asset at %s (see LogInterchange / LogAssetTools)" % (source_file, package))
    asset = _EAL.load_asset(package)
    _set_properties(asset, properties)
    return _save(asset)


def data_asset(path, asset_class, properties=None, on_exists="error"):
    """Creates an instance of any UDataAsset subclass (C++ or Blueprint) and sets properties.

    asset_class: unreal class, "/Script/gamespace.MyDataAsset", or "/Game/.../BP_X.BP_X_C"
    """
    cls = _resolve_class(asset_class)
    asset = _prepare(path, on_exists)
    if asset is not None and on_exists == "skip":
        return asset
    if asset is None:
        factory = unreal.DataAssetFactory()
        factory.set_editor_property("data_asset_class", cls)
        asset = _create(path, cls, factory)
    _set_properties(asset, properties)
    return _save(asset)


def curve_table(path, rows, on_exists="error"):
    """Creates a UCurveTable of simple (linearly interpolated) curves.

    rows: {"RowName": [(time, value), ...], ...}
    With on_exists="update" the listed rows are rebuilt; rows not listed are left alone.
    """
    lib = unreal.DataTableFunctionLibrary
    asset = _prepare(path, on_exists)
    if asset is not None and on_exists == "skip":
        return asset
    if asset is None:
        asset = _create(path, unreal.CurveTable, unreal.CurveTableFactory())
        # The factory seeds a new table with an empty placeholder row named "Curve".
        for placeholder in list(lib.get_curve_table_row_names(asset)):
            if str(placeholder) not in rows:
                lib.remove_curve_table_row(asset, placeholder)

    present = set(str(n) for n in lib.get_curve_table_row_names(asset))
    for row, keys in rows.items():
        if row in present:
            lib.remove_curve_table_row(asset, row)
        if not lib.add_simple_curve_to_table(asset, row):
            raise RuntimeError("could not add row %r to %s" % (row, path))
        for time, value in keys:
            if not lib.add_curve_table_key(asset, row, time, value):
                raise RuntimeError("could not add key (%s, %s) to row %r" % (time, value, row))
    return _save(asset)


def data_table(path, row_struct, rows, on_exists="error"):
    """Creates a UDataTable from a list of row dicts (each needs a "Name" field).

    row_struct: unreal struct type (e.g. unreal.GameplayTagTableRow) or a C++ USTRUCT
                deriving from FTableRowBase.
    With on_exists="update" the table's rows are REPLACED by `rows`.
    """
    asset = _prepare(path, on_exists)
    if asset is not None and on_exists == "skip":
        return asset
    if asset is None:
        factory = unreal.DataTableFactory()
        factory.set_editor_property("struct", row_struct.static_struct())
        asset = _create(path, unreal.DataTable, factory)
    if not unreal.DataTableFunctionLibrary.fill_data_table_from_json_string(asset, json.dumps(rows)):
        raise RuntimeError("could not fill %s from JSON (see LogDataTable)" % path)
    return _save(asset)
