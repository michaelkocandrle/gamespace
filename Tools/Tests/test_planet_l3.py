"""Headless checks for the 25 km Veyra and the altitude-based flight model (L3).

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\test_planet_l3.py

Loads TestSpace, never saves it. Checks:
  1. terrain noise: deterministic, in range, smooth, no float terracing
  2. LOD tile counts at several altitudes (current settings vs the L2 tuning, horizon culling on/off)
  3. atmosphere / gravity curves: bounds, monotonic, continuous
  4. simulated descent from the start position with the real drag/gravity/heat code
Prints "L3TEST PASS" / "L3TEST FAIL" lines and a summary.
"""

import math
import time

import unreal

LEVEL = "/Game/Maps/TestSpace"
failures = []


def log(msg):
    unreal.log("L3TEST " + msg)


def check(name, ok, detail=""):
    log(("PASS " if ok else "FAIL ") + name + ("  (" + detail + ")" if detail else ""))
    if not ok:
        failures.append(name)


def vec(v):
    return unreal.Vector(v[0], v[1], v[2])


def normalize(v):
    n = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
    return (v[0] / n, v[1] / n, v[2] / n)


def sample_env(planet, location):
    result = planet.sample_environment(location)
    # Out parameters come back as a tuple (return value, out struct), or just the struct.
    if isinstance(result, tuple):
        ok, env = result
        return env if ok else None
    return result


les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not les.load_level(LEVEL):
    raise RuntimeError("could not load " + LEVEL)
planet = next(a for a in eas.get_all_level_actors() if a.get_actor_label() == "Planet_Veyra")
centre = planet.get_actor_location()
C = (centre.x, centre.y, centre.z)
R = planet.get_editor_property("radius_km") * 100000.0
max_h = planet.get_max_terrain_height_cm()
log("planet radius %.1f km at (%.1f, %.1f, %.1f) km, max terrain height %.0f m" % (
    R / 1e5, C[0] / 1e5, C[1] / 1e5, C[2] / 1e5, max_h / 100))


def point(direction, radius):
    d = normalize(direction)
    return vec((C[0] + d[0] * radius, C[1] + d[1] * radius, C[2] + d[2] * radius))


# Direction from the planet centre to PlayerStart (0, 0, 300) - the descent line.
start_dir = normalize((0.0 - C[0], 0.0 - C[1], 300.0 - C[2]))

# ---------------------------------------------------------------------------------------
# 1) Noise
# ---------------------------------------------------------------------------------------
heights = []
seed_dirs = []
for i in range(2000):
    # Fibonacci sphere: even coverage.
    y = 1 - 2 * (i + 0.5) / 2000
    r = math.sqrt(1 - y * y)
    phi = i * math.pi * (3 - math.sqrt(5))
    d = (math.cos(phi) * r, y, math.sin(phi) * r)
    seed_dirs.append(d)
    heights.append(planet.get_terrain_height_at(point(d, R)))
repeat = [planet.get_terrain_height_at(point(d, R)) for d in seed_dirs[:200]]
check("noise deterministic", repeat == heights[:200])
mean = sum(heights) / len(heights)
std = math.sqrt(sum((h - mean) ** 2 for h in heights) / len(heights))
check("noise within max height", max(abs(h) for h in heights) <= max_h,
      "min %.0f m, max %.0f m, mean %.0f m, std %.0f m, bound %.0f m" % (
          min(heights) / 100, max(heights) / 100, mean / 100, std / 100, max_h / 100))
check("noise has real relief", std > 0.1 * max_h / 2, "std %.0f m" % (std / 100))

# Smoothness and precision along a 20 m line at 2 cm steps, right under the start.
tangent = normalize((-start_dir[1], start_dir[0], 0.0))
line = []
for k in range(1000):
    s = k * 2.0
    d = (start_dir[0] * R + tangent[0] * s, start_dir[1] * R + tangent[1] * s, start_dir[2] * R + tangent[2] * s)
    line.append(planet.get_terrain_height_at(point(d, R)))
steps = [abs(line[k + 1] - line[k]) for k in range(len(line) - 1)]
equal_runs = sum(1 for k in range(len(line) - 1) if line[k + 1] == line[k])
second = [abs(line[k + 1] - 2 * line[k] + line[k - 1]) for k in range(1, len(line) - 1)]
check("noise smooth at 2 cm", max(steps) < 20.0, "max step %.3f cm per 2 cm" % max(steps))
check("noise has no float plateaus", equal_runs == 0, "%d equal neighbours" % equal_runs)
check("noise curvature continuous", max(second) < 1.0, "max 2nd difference %.4f cm" % max(second))

# Slopes over 10 m, for the landing risk assessment.
slopes = []
for d in seed_dirs[:400]:
    t = normalize((-d[1], d[0], 0.3))
    h0 = planet.get_terrain_height_at(point(d, R))
    d2 = (d[0] * R + t[0] * 1000, d[1] * R + t[1] * 1000, d[2] * R + t[2] * 1000)
    h1 = planet.get_terrain_height_at(point(d2, R))
    slopes.append(math.degrees(math.atan(abs(h1 - h0) / 1000.0)))
slopes.sort()
log("INFO slope over 10 m: median %.1f deg, 90%% %.1f deg, max %.1f deg" % (
    slopes[len(slopes) // 2], slopes[int(len(slopes) * 0.9)], slopes[-1]))

# ---------------------------------------------------------------------------------------
# 2) LOD tile counts
# ---------------------------------------------------------------------------------------
terrain_under_start = planet.get_terrain_height_at(point(start_dir, R))
altitudes_m = [20000, 12000, 5000, 1000, 200, 30, 5]


def counts(label):
    row = []
    for alt in altitudes_m:
        loc = point(start_dir, R + terrain_under_start + alt * 100.0)
        t0 = time.perf_counter()
        n = planet.count_lod_tiles_from(loc)
        row.append((n, (time.perf_counter() - t0) * 1000))
    log("INFO tiles %-34s " % label + "  ".join("%5dm:%5d (%4.1fms)" % (a, n, ms) for a, (n, ms) in zip(altitudes_m, row)))
    return [n for n, _ in row]


quads = planet.get_editor_property("tile_quads")
factor = planet.get_editor_property("lod_distance_factor")
current = counts("current (%d quads, factor %.1f)" % (quads, factor))
planet.set_editor_property("horizon_culling", False)
no_cull = counts("no horizon culling")
planet.set_editor_property("horizon_culling", True)
leaf = planet.get_editor_property("leaf_tile_size_m")
old = None
for q, f, lf in ((32, 3.0, 4.0), (48, 2.0, 4.0), (64, 1.5, 16.0)):
    planet.set_editor_property("tile_quads", q)
    planet.set_editor_property("lod_distance_factor", f)
    planet.set_editor_property("leaf_tile_size_m", lf)
    row = counts("sweep %d quads, factor %.2f, leaf %g m" % (q, f, lf))
    log("INFO   -> vertex spacing ~ distance/%.0f, triangles at 5 m %.1f M" % (q * f, row[-1] * q * q * 2 / 1e6))
    if (q, f, lf) == (32, 3.0, 4.0):
        old = row
planet.set_editor_property("tile_quads", quads)
planet.set_editor_property("lod_distance_factor", factor)
planet.set_editor_property("leaf_tile_size_m", leaf)
check("tile count at 5 m <= 1000", current[-1] <= 1000, "%d tiles" % current[-1])
check("tile count bounded at every altitude", max(current) <= 1000, "max %d" % max(current))
check("horizon culling never adds tiles", all(c <= n for c, n in zip(current, no_cull)))
log("INFO triangles near ground: current %d, L2 tuning %d" % (
    current[-1] * quads * quads * 2, old[-1] * 32 * 32 * 2))

# ---------------------------------------------------------------------------------------
# 3) Environment curves
# ---------------------------------------------------------------------------------------
top_cm = planet.get_editor_property("atmosphere_height_km") * 1e5
profile = []
for alt in range(25000, -1, -10):  # sea-level altitude, m, 10 m steps
    env = sample_env(planet, point(start_dir, R + alt * 100.0))
    profile.append((alt, env))
check("environment available", all(e is not None for _, e in profile))
above = [e for a, e in profile if a * 100.0 >= top_cm]
check("no air, gravity or sky above the atmosphere",
      all(e.atmosphere_density == 0 and e.gravity_cm_s2 == 0 and e.sky_amount == 0 for e in above))
check("regime ORBIT above the atmosphere", all(e.regime == unreal.FlightRegime.ORBIT for e in above))
sea = profile[-1][1]
check("sea level density 1", abs(sea.atmosphere_density - 1.0) < 1e-4, "%.4f" % sea.atmosphere_density)
check("sea level gravity", abs(sea.gravity_cm_s2 - planet.get_editor_property("surface_gravity") * 100) < 1.0,
      "%.1f cm/s2" % sea.gravity_cm_s2)
dens = [e.atmosphere_density for _, e in profile]
grav = [e.gravity_cm_s2 for _, e in profile]
sky = [e.sky_amount for _, e in profile]
check("density monotonic", all(b >= a - 1e-6 for a, b in zip(dens, dens[1:])))
check("gravity monotonic", all(b >= a - 1e-3 for a, b in zip(grav, grav[1:])))
check("sky monotonic", all(b >= a - 1e-6 for a, b in zip(sky, sky[1:])))
check("density continuous (10 m steps)", max(abs(b - a) for a, b in zip(dens, dens[1:])) < 0.01,
      "max step %.5f" % max(abs(b - a) for a, b in zip(dens, dens[1:])))
check("gravity continuous (10 m steps)", max(abs(b - a) for a, b in zip(grav, grav[1:])) < 2.0,
      "max step %.3f cm/s2" % max(abs(b - a) for a, b in zip(grav, grav[1:])))
for alt in (12000, 10000, 8000, 5000, 3000, 1000, 0):
    e = dict(profile)[alt]
    log("INFO env %5d m ASL: air %.3f  g %.2f m/s2  sky %.2f  regime %s  AGL %.0f m" % (
        alt, e.atmosphere_density, e.gravity_cm_s2 / 100, e.sky_amount, e.regime, e.altitude_above_terrain_cm / 100))

# ---------------------------------------------------------------------------------------
# 4) Simulated descent, integrated like ASpaceshipPawn::UpdateLinearMotion
# ---------------------------------------------------------------------------------------
ship = unreal.SpaceshipPawn.get_default_object()
thrust = ship.get_editor_property("thrust_acceleration")
boost = ship.get_editor_property("boost_multiplier")
max_speed = ship.get_editor_property("scm_max_speed")
damping = ship.get_editor_property("linear_damping")
space_damping = ship.get_editor_property("space_linear_damping")
quad = ship.get_editor_property("quadratic_drag")
heat_response = ship.get_editor_property("heat_response")


def simulate(label, start_alt_m, throttle, boosting, stop_throttle_at_m=None, dt=1.0 / 60.0):
    p = point(start_dir, R + start_alt_m * 100.0)
    pos = [p.x, p.y, p.z]
    vel = [0.0, 0.0, 0.0]
    t = 0.0
    heat = 0.0
    max_heat = 0.0
    max_jerk = 0.0
    prev_acc = None
    marks = {}
    speed_cap = max_speed * (boost if boosting else 1.0)
    while t < 1800.0:
        env = sample_env(planet, vec(pos))
        down = (-env.up.x, -env.up.y, -env.up.z)
        agl = env.altitude_above_terrain_cm / 100.0
        if agl <= 2.0:
            marks["ground"] = (t, math.sqrt(sum(v * v for v in vel)) / 100.0)
            break
        active = throttle if (stop_throttle_at_m is None or agl > stop_throttle_at_m) else 0.0
        a_thrust = thrust * (boost if boosting else 1.0) * active
        env_speed = math.sqrt(sum(v * v for v in vel))
        # Same order as the pawn: thrust, then clamped drag, then gravity.
        v1 = [vel[i] + down[i] * a_thrust * dt for i in range(3)]
        spd1 = math.sqrt(sum(v * v for v in v1))
        rate = space_damping + (damping + quad * spd1) * env.atmosphere_density
        v2 = [v1[i] - v1[i] * min(rate * dt, 1.0) for i in range(3)]
        v3 = [v2[i] + down[i] * env.gravity_cm_s2 * dt for i in range(3)]
        spd = math.sqrt(sum(v * v for v in v3))
        if spd > speed_cap:
            v3 = [x * speed_cap / spd for x in v3]
        # Jerk of the environment alone (drag + gravity): the pilot letting go of the throttle
        # is a deliberate step, not something the flight model should smooth.
        acc = [(v2[i] - v1[i]) / dt + down[i] * env.gravity_cm_s2 for i in range(3)]
        if prev_acc is not None:
            max_jerk = max(max_jerk, math.sqrt(sum((acc[i] - prev_acc[i]) ** 2 for i in range(3))) / 100.0)
        prev_acc = acc
        # Cross-check the C++ helper against this integration once in a while.
        if int(t / dt) % 600 == 0:
            cpp = ship.compute_environment_acceleration(env, vec(vel))
            mine_rate = space_damping + (damping + quad * env_speed) * env.atmosphere_density
            ex = [-vel[0] * mine_rate - env.up.x * env.gravity_cm_s2,
                  -vel[1] * mine_rate - env.up.y * env.gravity_cm_s2,
                  -vel[2] * mine_rate - env.up.z * env.gravity_cm_s2]
            diff = math.sqrt((cpp.x - ex[0]) ** 2 + (cpp.y - ex[1]) ** 2 + (cpp.z - ex[2]) ** 2)
            if diff > 0.5:
                check("C++ environment acceleration matches (%s, t=%.0f)" % (label, t), False, "diff %.3f cm/s2" % diff)
        vel = v3
        pos = [pos[i] + vel[i] * dt for i in range(3)]
        target = ship.compute_heat_target(env.atmosphere_density, spd)
        heat += (target - heat) * min(heat_response * dt, 1.0)
        max_heat = max(max_heat, heat)
        asl = env.altitude_above_sea_level_cm / 100.0
        for m in (12000, 8000, 5000, 3000, 1000, 200):
            if asl <= m and m not in marks:
                marks[m] = (t, spd / 100.0, heat, env.atmosphere_density)
        t += dt
    parts = []
    for m in (12000, 8000, 5000, 3000, 1000, 200):
        if m in marks:
            tt, sp, ht, rho = marks[m]
            parts.append("%dm@%.0fs %.0fm/s heat %.2f" % (m, tt, sp, ht))
    ground = marks.get("ground")
    log("INFO descent %-28s %s | ground %s | max heat %.2f | max jerk %.2f m/s2/frame" % (
        label, "; ".join(parts), ("%.0f s at %.1f m/s" % ground) if ground else "not reached", max_heat, max_jerk))
    return ground, max_heat, max_jerk


g1, h1, j1 = simulate("boost dive, throttle to 3 km", 20000, 1.0, True, stop_throttle_at_m=3000)
g2, h2, j2 = simulate("cruise dive (no boost)", 20000, 1.0, False, stop_throttle_at_m=1000)
g3, h3, j3 = simulate("free fall from 11 km", 11000, 0.0, False)
check("boost dive reaches the ground", g1 is not None)
check("boost dive builds entry heat", h1 > 0.3, "max heat %.2f" % h1)
check("free fall reaches the ground below 20 m/s", g3 is not None and g3[1] < 20.0, "impact %.1f m/s" % (g3[1] if g3 else -1))
# Since SC-1a the boost dive hits the air at ~500 m/s (was ~260): drag then changes by ~4 m/s2 per
# frame, smoothly. A real discontinuity (e.g. at the top of the atmosphere) would be far larger.
check("no acceleration spikes (jerk < 5 m/s2 per frame)", max(j1, j2, j3) < 5.0,
      "max %.2f" % max(j1, j2, j3))
check("cruise dive stays cool", h2 < 0.2, "max heat %.2f" % h2)

log("SUMMARY %s (%d failed: %s)" % ("OK" if not failures else "FAILED", len(failures), ", ".join(failures)))
