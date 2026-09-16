"""Headless checks for landing on Veyra (L5).

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\test_landing_l5.py

Loads TestSpace, never saves it. The commandlet cannot run collision queries or tick the world,
so the parts of landing that live in pure functions are tested here:
  1. terrain slope under a ship-sized footprint (GetSurfaceFrame): how much ground is landable
  2. the touchdown rule (EvaluateLanding)
  3. ground friction: stands still up to the landing slope limit, slides beyond
  4. landed alignment: smooth, no snap, converges in about half a second
  5. cost of a synchronous collision warm-up build
Prints "L5TEST PASS" / "L5TEST FAIL" lines and a summary.
"""

import math

import unreal

LEVEL = "/Game/Maps/TestSpace"
failures = []


def log(msg):
    unreal.log("L5TEST " + msg)


def check(name, ok, detail=""):
    log(("PASS " if ok else "FAIL ") + name + ("  (" + detail + ")" if detail else ""))
    if not ok:
        failures.append(name)


def v3(v):
    return (v.x, v.y, v.z)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def length(a):
    return math.sqrt(dot(a, a))


def angle_deg(a, b):
    return math.degrees(math.acos(max(-1.0, min(1.0, dot(a, b) / (length(a) * length(b))))))


les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not les.load_level(LEVEL):
    raise RuntimeError("could not load " + LEVEL)
planet = next(a for a in eas.get_all_level_actors() if a.get_actor_label() == "Planet_Veyra")
ship = unreal.SpaceshipPawn.get_default_object()
C = v3(planet.get_actor_location())
R = planet.get_editor_property("radius_km") * 100000.0
footprint = ship.get_editor_property("landing_footprint_radius_cm")
max_slope = ship.get_editor_property("max_landing_slope_deg")
friction = ship.get_editor_property("ground_friction")

# ---------------------------------------------------------------------------------------
# 1) Landable ground
# ---------------------------------------------------------------------------------------
slopes = []
bad_normals = 0
for i in range(3000):
    y = 1 - 2 * (i + 0.5) / 3000
    r = math.sqrt(1 - y * y)
    phi = i * math.pi * (3 - math.sqrt(5))
    d = (math.cos(phi) * r, y, math.sin(phi) * r)
    loc = unreal.Vector(C[0] + d[0] * (R + 200000), C[1] + d[1] * (R + 200000), C[2] + d[2] * (R + 200000))
    result = planet.get_surface_frame(loc, footprint)
    ok, point, normal = result if len(result) == 3 else (True,) + tuple(result)
    n = v3(normal)
    if not ok or abs(length(n) - 1.0) > 1e-3 or dot(n, d) <= 0.0:
        bad_normals += 1
        continue
    slopes.append(angle_deg(n, d))
check("surface frame valid everywhere", bad_normals == 0, "%d bad of 3000" % bad_normals)
slopes.sort()
n = len(slopes)
pct = lambda limit: 100.0 * sum(1 for s in slopes if s <= limit) / n
log("INFO slope under a %.0f cm footprint: median %.1f deg, 90%% %.1f deg, max %.1f deg" % (
    footprint, slopes[n // 2], slopes[int(n * 0.9)], slopes[-1]))
log("INFO landable (<= %.0f deg): %.1f %% of the surface; <= 21 deg: %.1f %%; > 30 deg: %.1f %%" % (
    max_slope, pct(max_slope), pct(21.0), 100.0 - pct(30.0)))
check("most of the surface is landable", pct(max_slope) > 75.0, "%.1f %%" % pct(max_slope))
check("friction can hold the landing slope limit", math.degrees(math.atan(friction)) >= max_slope,
      "friction holds up to %.1f deg, limit %.1f deg" % (math.degrees(math.atan(friction)), max_slope))

# ---------------------------------------------------------------------------------------
# 2) Touchdown rule
# ---------------------------------------------------------------------------------------
B = unreal.LandingBlocker
cases = [
    ((20.0, 100.0, 5.0, 10.0, False), B.NONE),
    ((61.0, 100.0, 5.0, 10.0, False), B.TOO_HIGH),
    ((-1.0, 100.0, 5.0, 10.0, False), B.TOO_HIGH),
    ((20.0, 100.0, 5.0, 26.0, False), B.TOO_STEEP),
    ((20.0, 400.0, 5.0, 10.0, False), B.TOO_FAST),
    ((20.0, 100.0, 35.0, 10.0, False), B.TILTED),
    ((20.0, 100.0, 5.0, 10.0, True), B.ENGINE_INPUT),
    ((0.0, 0.0, 0.0, 25.0, False), B.NONE),
]
wrong = [(args, want, ship.evaluate_landing(*args)) for args, want in cases if ship.evaluate_landing(*args) != want]
check("touchdown rule", not wrong, "; ".join("%s -> %s, expected %s" % (a, got, w) for a, w, got in wrong))

# ---------------------------------------------------------------------------------------
# 3) Friction on slopes, integrated like the ship touching the ground (5 s at 60 fps)
# ---------------------------------------------------------------------------------------
g = planet.get_editor_property("surface_gravity") * 100.0
damping = ship.get_editor_property("linear_damping")
quad = ship.get_editor_property("quadratic_drag")
dt = 1.0 / 60.0
up = unreal.Vector(0.0, 0.0, 1.0)
slide = {}
for slope in (0, 10, 21, 25, 28, 35):
    s = math.radians(slope)
    normal = unreal.Vector(0.0, math.sin(s), math.cos(s))
    vel = [0.0, 0.0, 0.0]
    travelled = 0.0
    for _ in range(300):
        speed = length(vel)
        rate = min((damping + quad * speed) * 1.0, 1.0 / dt)
        vel = [x - x * rate * dt for x in vel]
        vel[2] -= g * dt
        vel = v3(ship.apply_ground_friction(unreal.Vector(*vel), normal, up, g, dt))
        # The swept move blocks the part into the ground.
        into = dot(vel, v3(normal))
        if into < 0.0:
            vel = [vel[i] - v3(normal)[i] * into for i in range(3)]
        travelled += length(vel) * dt
    slide[slope] = (length(vel), travelled)
log("INFO slide after 5 s: " + "   ".join("%d deg: %.1f cm/s, %.0f cm" % (k, v[0], v[1]) for k, v in slide.items()))
check("stands still up to 25 deg", all(slide[k][1] < 1.0 for k in (0, 10, 21, 25)),
      "max drift %.2f cm" % max(slide[k][1] for k in (0, 10, 21, 25)))
check("slides on 28 deg and steeper", slide[28][1] > 50.0 and slide[35][1] > slide[28][1],
      "28 deg %.0f cm, 35 deg %.0f cm" % (slide[28][1], slide[35][1]))

# ---------------------------------------------------------------------------------------
# 4) Landed alignment
# ---------------------------------------------------------------------------------------
worst_step = 0.0
times = []
for tilt_roll, tilt_pitch, slope in ((30.0, 0.0, 20.0), (-20.0, 15.0, 0.0), (0.0, -25.0, 25.0)):
    s = math.radians(slope)
    normal = (0.0, math.sin(s), math.cos(s))
    rot = unreal.Rotator(roll=tilt_roll, pitch=tilt_pitch, yaw=37.0)
    start_angle = angle_deg(v3(unreal.MathLibrary.get_up_vector(rot)), normal)
    t = 0.0
    t95 = None
    prev_up = v3(unreal.MathLibrary.get_up_vector(rot))
    prev_forward = v3(unreal.MathLibrary.get_forward_vector(rot))
    for _ in range(120):
        rot = ship.compute_landed_rotation_step(rot, unreal.Vector(*normal), dt)
        t += dt
        up_v = v3(unreal.MathLibrary.get_up_vector(rot))
        fwd = v3(unreal.MathLibrary.get_forward_vector(rot))
        worst_step = max(worst_step, angle_deg(up_v, prev_up), angle_deg(fwd, prev_forward))
        prev_up, prev_forward = up_v, fwd
        if t95 is None and angle_deg(up_v, normal) <= 0.05 * start_angle:
            t95 = t
    final = angle_deg(prev_up, normal)
    times.append(t95)
    log("INFO align from %.0f deg: 95 %% after %.2f s, after 2 s %.3f deg off" % (start_angle, t95 or -1, final))
    check("alignment converges (from %.0f deg)" % start_angle, final < 0.1 and t95 is not None and t95 < 0.8)
check("alignment is not a snap (max step per 60 fps frame < 4 deg)", worst_step < 4.0, "max %.2f deg" % worst_step)
check("alignment is not instant (95 percent takes > 0.25 s)", all(t and t > 0.25 for t in times))

# ---------------------------------------------------------------------------------------
# 5) Warm-up build cost
# ---------------------------------------------------------------------------------------
costs = []
for i in range(20):
    a = i * 0.7
    d = (math.cos(a) * 0.6, math.sin(a) * 0.6, 0.53)
    k = length(d)
    loc = unreal.Vector(C[0] + d[0] / k * R, C[1] + d[1] / k * R, C[2] + d[2] / k * R)
    costs.append(planet.measure_collision_tile_build_ms(loc))
costs.sort()
log("INFO synchronous collision tile build (%d cells): median %.2f ms, max %.2f ms (physics cooking comes on top)" % (
    planet.get_editor_property("collision_tile_quads"), costs[len(costs) // 2], costs[-1]))
check("warm-up build fits in a frame", costs[len(costs) // 2] < 8.0, "median %.2f ms" % costs[len(costs) // 2])

log("SUMMARY %s (%d failed: %s)" % ("OK" if not failures else "FAILED", len(failures), ", ".join(failures)))
