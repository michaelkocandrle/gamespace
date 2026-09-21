// Veyra's ground in three scales (21. 9. 2026, the planet reference video:
// starcitizenreference/Planets_VideoNotes.md). P is the planet-local position in cm.
float r = length(P);
float3 up = P / max(r, 1.0);
float height = r - Radius;                       // cm above sea level, about +/-160000
float slope = 1.0 - saturate(dot(normalize(Nrm), up));  // 0 flat, 0.29 at 45 degrees

// 1) Regions seen from orbit: a warped low-frequency field over the unit sphere splits the planet
//    into plains, red basins, dark basalt and ochre highlands, with ragged but clear edges.
float3 s = up * RegionScale;
float3 warp = float3(N.Fbm(s + 11.3, 4), N.Fbm(s + 27.9, 4), N.Fbm(s + 3.7, 4)) - 0.5;
float3 sw = s + warp * 1.6;
float a = N.Fbm(sw, 5);
float b = N.Fbm(sw * 1.7 + 41.0, 4);
float basalt = smoothstep(0.60, 0.63, a);
float basin = smoothstep(0.39, 0.35, a);
float ochre = smoothstep(0.55, 0.60, b) * (1.0 - basalt);
float3 region = Plain.rgb;
region = lerp(region, Ochre.rgb, ochre);
region = lerp(region, Basin.rgb, basin);
region = lerp(region, Basalt.rgb, basalt);

// 2) Middle scale: bare rock on slopes, dust settled in the lows and on the flats.
float rockMask = smoothstep(SlopeRockStart, SlopeRockEnd, slope + (N.Noise(P / 2400.0) - 0.5) * 0.08);
float low = smoothstep(20000.0, -60000.0, height);      // valleys below ~200 m collect dust
float3 rock = lerp(Rock.rgb, region * 0.55, 0.35);
float3 ground = lerp(region, Dust.rgb, low * 0.45);
float3 colour = lerp(ground, rock, rockMask);
// Highest peaks a little paler (wind-scoured, dusted).
colour = lerp(colour, colour * 1.25 + 0.03, smoothstep(90000.0, 150000.0, height) * 0.6);

// 3) Close up: breakup at ~40 m, ~3 m and ~0.6 m so the ground never reads as flat paint.
float d1 = N.Fbm(P / 4000.0, 3);
float d2 = N.Fbm(P / 300.0, 2);
float d3 = N.Noise(P / 60.0);
colour *= lerp(0.7, 1.2, d1) * lerp(0.8, 1.12, d2) * lerp(0.88, 1.08, d3);
// Scattered darker pebbles and stones on the flats (not on rock, which is already dark).
float stones = smoothstep(0.72, 0.78, N.Noise(P / 45.0)) * (1.0 - rockMask);
colour = lerp(colour, Rock.rgb * 0.7, stones * 0.6);
float rough = lerp(DustRough, RockRough, rockMask);
return float4(max(colour, 0.0), rough);
