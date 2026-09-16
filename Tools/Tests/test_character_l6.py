"""Headless checks for the player character (L6).

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\test_character_l6.py

Loads TestSpace, spawns a temporary character in the editor world, never saves.
  1. assets: Mannequin mesh and animations, input actions and contexts
  2. gravity frame: scale, parallel transport once around the planet, view rotation
  3. ship exit: side exit placement
  4. animation: native pose evaluation (idle, walk, jog, fall) and foot IK with forced ground
  5. terrain: how far the visible ground departs from the coarse collision the capsule stands on
Prints "L6TEST PASS" / "L6TEST FAIL" lines and a summary.
"""

import math

import unreal

LEVEL = "/Game/Maps/TestSpace"
failures = []


def log(msg):
    unreal.log("L6TEST " + msg)


def check(name, ok, detail=""):
    log(("PASS " if ok else "FAIL ") + name + ("  (" + detail + ")" if detail else ""))
    if not ok:
        failures.append(name)


def v3(v):
    return (v.x, v.y, v.z)


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def length(a):
    return math.sqrt(dot(a, a))


def normalize(a):
    n = length(a)
    return (a[0] / n, a[1] / n, a[2] / n)


def angle_deg(a, b):
    return math.degrees(math.acos(max(-1.0, min(1.0, dot(normalize(a), normalize(b))))))


# ---------------------------------------------------------------------------------------
# 1) Assets
# ---------------------------------------------------------------------------------------
mesh = unreal.EditorAssetLibrary.load_asset("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple")
check("Manny mesh loads", isinstance(mesh, unreal.SkeletalMesh))
lengths = {}
for path in ("Unarmed/MM_Idle", "Unarmed/Walk/MF_Unarmed_Walk_Fwd", "Unarmed/Jog/MF_Unarmed_Jog_Fwd",
             "Unarmed/Jump/MM_Jump", "Unarmed/Jump/MM_Fall_Loop", "Unarmed/Jump/MM_Land"):
    anim = unreal.EditorAssetLibrary.load_asset("/Game/Characters/Mannequins/Anims/" + path)
    lengths[path.split("/")[-1]] = anim.get_play_length() if isinstance(anim, unreal.AnimSequence) else -1
check("animations load", all(v > 0 for v in lengths.values()), ", ".join("%s %.2f s" % kv for kv in lengths.items()))

anim_cdo = unreal.get_default_object(unreal.PlayerCharacterAnimInstance)
speeds = anim_cdo.get_locomotion_reference_speeds()
log("INFO locomotion reference speeds: walk %.0f cm/s, jog %.0f cm/s (from BS_Idle_Walk_Run)" % (speeds.x, speeds.y))
check("reference speeds from the blend space", 50 < speeds.x < speeds.y < 1000, "walk %.0f, jog %.0f" % (speeds.x, speeds.y))

character_cdo = unreal.get_default_object(unreal.PlayerCharacter)
cdo_mesh = character_cdo.get_editor_property("mesh")
check("character uses Manny", cdo_mesh.get_skeletal_mesh_asset() == mesh)
check("character anim instance is native", cdo_mesh.get_editor_property("anim_class") == unreal.PlayerCharacterAnimInstance.static_class())


def mappings(path):
    imc = unreal.EditorAssetLibrary.load_asset(path)
    result = []
    for m in imc.get_editor_property("default_key_mappings").get_editor_property("mappings"):
        action = m.get_editor_property("action")
        result.append((str(m.get_editor_property("key").get_editor_property("key_name")), action.get_name() if action else None,
                       [mod.get_class().get_name() for mod in m.get_editor_property("modifiers")]))
    return result


character_map = mappings("/Game/Input/IMC_Character")
expected = {("W", "IA_CharMove"), ("S", "IA_CharMove"), ("A", "IA_CharMove"), ("D", "IA_CharMove"), ("Mouse2D", "IA_CharLook"),
            ("SpaceBar", "IA_CharJump"), ("LeftShift", "IA_CharSprint"), ("F", "IA_Interact")}
check("IMC_Character mappings", {(k, a) for k, a, _ in character_map} == expected,
      "; ".join("%s->%s %s" % m for m in character_map))
mods = {k: m for k, _, m in character_map}
check("WASD modifiers", mods["W"] == ["InputModifierSwizzleAxis"] and mods["S"] == ["InputModifierSwizzleAxis", "InputModifierNegate"]
      and mods["D"] == [] and mods["A"] == ["InputModifierNegate"], str(mods))
ship_map = mappings("/Game/Input/IMC_Spaceship")
check("IMC_Spaceship kept its mappings and got F", ("F", "IA_Interact") in {(k, a) for k, a, _ in ship_map}
      and {("W", "IA_Thrust"), ("C", "IA_ToggleCamera"), ("LeftShift", "IA_Boost")} <= {(k, a) for k, a, _ in ship_map},
      "%d mappings" % len(ship_map))
interact = unreal.EditorAssetLibrary.load_asset("/Game/Input/IA_Interact")
check("IA_Interact fires once per press", [t.get_class().get_name() for t in interact.get_editor_property("triggers")] == ["InputTriggerPressed"])

# ---------------------------------------------------------------------------------------
# 2) Gravity frame
# ---------------------------------------------------------------------------------------
PC = unreal.PlayerCharacter
check("gravity scale for 6 m/s2", abs(PC.compute_gravity_scale(600.0, -980.0) - 600.0 / 980.0) < 1e-4)
check("gravity scale in space is 0", PC.compute_gravity_scale(0.0, -980.0) == 0.0)

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les.load_level(LEVEL)
planet = next(a for a in eas.get_all_level_actors() if a.get_actor_label() == "Planet_Veyra")
C = v3(planet.get_actor_location())
R = planet.get_editor_property("radius_km") * 100000.0
start_dir = normalize((0.0 - C[0], 0.0 - C[1], 300.0 - C[2]))

# Walk a great circle around the planet in 0.25 degree steps (~110 m on Veyra), carrying the frame.
axis = normalize((0.0, 0.3, 1.0))
axis = normalize(sub(axis, tuple(dot(axis, start_dir) * c for c in start_dir)))
tangent = normalize((start_dir[1] * axis[2] - start_dir[2] * axis[1], start_dir[2] * axis[0] - start_dir[0] * axis[2],
                     start_dir[0] * axis[1] - start_dir[1] * axis[0]))
frame = unreal.MathLibrary.make_rot_from_xz(unreal.Vector(*tangent), unreal.Vector(*start_dir))
initial_forward = v3(unreal.MathLibrary.get_forward_vector(frame))
worst_up = 0.0
worst_perp = 0.0
steps = 1440
for i in range(1, steps + 1):
    a = 2 * math.pi * i / steps
    up = tuple(math.cos(a) * start_dir[k] + math.sin(a) * tangent[k] for k in range(3))
    frame = PC.transport_gravity_frame(frame, unreal.Vector(*up))
    worst_up = max(worst_up, angle_deg(v3(unreal.MathLibrary.get_up_vector(frame)), up))
    worst_perp = max(worst_perp, abs(90.0 - angle_deg(v3(unreal.MathLibrary.get_forward_vector(frame)), up)))
twist = angle_deg(v3(unreal.MathLibrary.get_forward_vector(frame)), initial_forward)
check("frame up follows gravity", worst_up < 0.01, "worst %.4f deg" % worst_up)
check("frame forward stays level", worst_perp < 0.01, "worst %.4f deg" % worst_perp)
check("no twist after a full lap", twist < 0.5, "%.3f deg" % twist)

view = PC.compute_view_rotation(frame, 90.0, -20.0)
view_forward = v3(unreal.MathLibrary.get_forward_vector(view))
frame_up = v3(unreal.MathLibrary.get_up_vector(frame))
frame_right = v3(unreal.MathLibrary.get_right_vector(frame))
check("view yaw 90 looks along the frame's right", angle_deg(sub(view_forward, tuple(dot(view_forward, frame_up) * c for c in frame_up)), frame_right) < 0.1)
check("view pitch -20 looks 20 deg down", abs((90.0 - angle_deg(view_forward, frame_up)) + 20.0) < 0.1)

# ---------------------------------------------------------------------------------------
# 3) Ship exit
# ---------------------------------------------------------------------------------------
exit_loc = unreal.SpaceshipPawn.compute_side_exit_location(unreal.Vector(0, 0, 0), unreal.Rotator(roll=0.0, pitch=0.0, yaw=90.0),
                                                           unreal.Vector(100, 50, 17.5), 42.0, 80.0)
check("side exit is right of the ship, clear of the hull", abs(exit_loc.x + 172.0) < 0.01 and abs(exit_loc.y) < 0.01,
      "%s (ship yaw 90: right is -X)" % exit_loc)

# ---------------------------------------------------------------------------------------
# 4) Animation and foot IK (native evaluation on a temporary character)
# ---------------------------------------------------------------------------------------
character = eas.spawn_actor_from_class(unreal.PlayerCharacter, unreal.Vector(0.0, 0.0, 50000.0))
BONES = ("pelvis", "foot_l", "foot_r", "thigh_l", "thigh_r", "calf_l", "calf_r")
try:
    def sample(speed=0.0, falling=False, ground=None, seconds=1.0):
        out = character.debug_sample_animation(speed, falling, ground is not None, (ground or (0, 0))[0], (ground or (0, 0))[1], seconds)
        return dict(zip(BONES, [v3(v) for v in out])) if len(out) >= len(BONES) else None

    idle = sample()
    check("pose evaluates", idle is not None and all(abs(c) < 1e5 for p in idle.values() for c in p),
          "no anim instance" if idle is None else "")
    if idle:
        ref_pose = sample(0.0, False, None, 0.0)
        walk_a = sample(250.0, seconds=1.0)
        walk_b = sample(250.0, seconds=0.3)
        jog = sample(500.0, seconds=1.0)
        fall = sample(0.0, True, seconds=1.0)
        moved = lambda a, b: max(length(sub(a[k], b[k])) for k in BONES)
        log("INFO idle feet z: left %.1f, right %.1f; pelvis z %.1f" % (idle["foot_l"][2], idle["foot_r"][2], idle["pelvis"][2]))
        check("walking moves the legs", moved(idle, walk_a) > 5.0, "%.1f cm" % moved(idle, walk_a))
        check("the walk cycle advances", moved(walk_a, walk_b) > 2.0, "%.1f cm" % moved(walk_a, walk_b))
        check("jog differs from walk", moved(walk_a, jog) > 2.0, "%.1f cm" % moved(walk_a, jog))
        check("falling uses the air pose", moved(idle, fall) > 5.0, "%.1f cm" % moved(idle, fall))

        flat = sample(0.0, False, (0.0, 0.0), 1.5)
        slope = sample(0.0, False, (20.0, -20.0), 1.5)
        deep = sample(0.0, False, (90.0, -90.0), 1.5)
        dl = slope["foot_l"][2] - flat["foot_l"][2]
        dr = slope["foot_r"][2] - flat["foot_r"][2]
        dp = slope["pelvis"][2] - flat["pelvis"][2]
        check("IK raises the left foot 20 cm", abs(dl - 20.0) < 2.0, "%+.1f cm" % dl)
        check("IK lowers the right foot 20 cm", abs(dr + 20.0) < 2.0, "%+.1f cm" % dr)
        check("IK drops the pelvis to the lower foot", abs(dp + 20.0) < 2.0, "%+.1f cm" % dp)
        for side in ("l", "r"):
            thigh0 = length(sub(flat["calf_" + side], flat["thigh_" + side]))
            thigh1 = length(sub(slope["calf_" + side], slope["thigh_" + side]))
            shin0 = length(sub(flat["foot_" + side], flat["calf_" + side]))
            shin1 = length(sub(slope["foot_" + side], slope["calf_" + side]))
            check("leg %s keeps its bone lengths" % side, abs(thigh0 - thigh1) < 0.5 and abs(shin0 - shin1) < 0.5,
                  "thigh %.1f/%.1f, shin %.1f/%.1f" % (thigh0, thigh1, shin0, shin1))
        dl_deep = deep["foot_l"][2] - flat["foot_l"][2]
        dp_deep = deep["pelvis"][2] - flat["pelvis"][2]
        check("large differences are clamped", dl_deep <= 46.0 and dp_deep >= -41.0,
              "foot %+.1f, pelvis %+.1f cm" % (dl_deep, dp_deep))
        ik = character.get_foot_ik_state()
        log("INFO foot IK readout after clamp test: active %s, clamped %s, pelvis %.1f" % (
            ik.get_editor_property("active"), ik.get_editor_property("clamped"), ik.get_editor_property("pelvis_offset_cm")))
finally:
    eas.destroy_actor(character)

# ---------------------------------------------------------------------------------------
# 5) Visible terrain vs the collision the capsule stands on
# ---------------------------------------------------------------------------------------
root_size_cm = math.pi * 0.5 * R
min_tile_cm = planet.get_editor_property("collision_min_tile_size_m") * 100.0
depth = round(math.log2(root_size_cm / min_tile_cm))
cell = root_size_cm / (2 ** depth) / planet.get_editor_property("collision_tile_quads")


def height(u, v, t1, t2, base):
    d = normalize(tuple(base[k] * R + t1[k] * u + t2[k] * v for k in range(3)))
    return planet.get_terrain_height_at(unreal.Vector(C[0] + d[0] * R, C[1] + d[1] * R, C[2] + d[2] * R))


deviations = []
t1 = normalize((-start_dir[1], start_dir[0], 0.0))
t2 = normalize((start_dir[1] * t1[2] - start_dir[2] * t1[1], start_dir[2] * t1[0] - start_dir[0] * t1[2], start_dir[0] * t1[1] - start_dir[1] * t1[0]))
for i in range(600):
    u = (i * 7.31) % 2000.0 * 100.0
    v = (i * 3.17) % 2000.0 * 100.0
    cu, cv = math.floor(u / cell) * cell, math.floor(v / cell) * cell
    fu, fv = (u - cu) / cell, (v - cv) / cell
    h00, h10 = height(cu, cv, t1, t2, start_dir), height(cu + cell, cv, t1, t2, start_dir)
    h01, h11 = height(cu, cv + cell, t1, t2, start_dir), height(cu + cell, cv + cell, t1, t2, start_dir)
    # Two triangles split along the 00-11 diagonal, like the tile mesh.
    collision = h00 + fu * (h10 - h00) + fv * (h11 - h10) if fu >= fv else h00 + fv * (h01 - h00) + fu * (h11 - h01)
    deviations.append(height(u, v, t1, t2, start_dir) - collision)
absd = sorted(abs(d) for d in deviations)
n = len(absd)
drop = anim_cdo.get_editor_property("max_pelvis_drop_cm")
within = 100.0 * sum(1 for d in absd if d <= drop) / n
log("INFO collision cell %.0f cm: visible ground vs collision |dev| median %.1f cm, 90%% %.1f, 99%% %.1f, max %.1f" % (
    cell, absd[n // 2], absd[int(n * 0.9)], absd[int(n * 0.99)], absd[-1]))
check("foot IK range covers the collision error", within >= 95.0, "%.1f %% within %.0f cm" % (within, drop))

log("SUMMARY %s (%d failed: %s)" % ("OK" if not failures else "FAILED", len(failures), ", ".join(failures)))
