// Veyra's ground (21. 9. 2026, the planet reference video: starcitizenreference/Planets_VideoNotes.md).
// P: planet-local position, cm. T: the same position wrapped every TerrainTextureWrapCm (exact, for
// the textures). Nrm: the surface normal in world space (planet and tiles are not rotated, so world
// axes are the planet's). Returns base colour and roughness; NormalOut (world space) and AOOut are
// additional outputs.
float r = length(P);
float3 up = P / max(r, 1.0);
float height = r - Radius;                       // cm above sea level, about +/-160000
// Guarded: a zero vertex normal (a crease in the ridged terrain) would normalise to NaN, and TSR smears
// a NaN pixel into a black blob.
float3 n = Nrm * rsqrt(max(dot(Nrm, Nrm), 1e-8));
n = any(isnan(n)) ? up : n;
float slope = 1.0 - saturate(dot(n, up));        // 0 flat, 0.29 at 45 degrees

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
float breakup = N.Noise(P / 2400.0) - 0.5;
float rockMask = smoothstep(SlopeRockStart, SlopeRockEnd, slope + breakup * 0.08);
float steep = smoothstep(SlopeRockEnd, SlopeRockEnd * 2.2, slope + breakup * 0.06);
float low = smoothstep(20000.0, -60000.0, height);
float3 rockTint = lerp(Rock.rgb, region * 0.55, 0.35);
float3 ground = lerp(region, Dust.rgb, low * 0.45);
float3 colour = lerp(ground, rockTint, rockMask);
colour = lerp(colour, colour * 1.25 + 0.03, smoothstep(90000.0, 150000.0, height) * 0.6);
// Large-scale breakup (~40 m) that the textures cannot give.
colour *= lerp(0.8, 1.15, N.Fbm(P / 4000.0, 3));

// 3) Close up: photo-scanned ground (Poly Haven, CC0), projected from three sides (triplanar) in
//    planet space: gravelly sand on the flats, cracked rock on slopes, layered rock on cliffs. The
//    textures give the detail - grain, stones, cracks, relief - and the colour above keeps its hue:
//    each texture is divided by its own average colour. Texture2DSample, not .Sample: the ray tracing
//    hit shaders have no screen derivatives and refuse .Sample, which failed the whole material over
//    to the default grey one (21. 9. 2026).
float3 w = pow(abs(n), 6.0) + 1e-5;
w /= (w.x + w.y + w.z);
float mSand = 1.0 - rockMask;
float mRock = rockMask * (1.0 - steep);
float mStrata = rockMask * steep;

float3 detail = 0;
float3 tnSum = 0;
float2 ra = 0;           // roughness, occlusion
float scales[3] = { SandScale, RockScale, StrataScale };
float weights[3] = { mSand, mRock, mStrata };
[unroll] for (int i = 0; i < 3; i++)
{
    float3 q = T / scales[i];
    float2 uvX = q.zy, uvY = q.xz, uvZ = q.xy;
    float3 cX, cY, cZ, nX, nY, nZ, aX, aY, aZ;
    if (i == 0)
    {
        cX = Texture2DSample(SandD, SandDSampler, uvX).rgb; cY = Texture2DSample(SandD, SandDSampler, uvY).rgb; cZ = Texture2DSample(SandD, SandDSampler, uvZ).rgb;
        nX = Texture2DSample(SandN, SandNSampler, uvX).rgb; nY = Texture2DSample(SandN, SandNSampler, uvY).rgb; nZ = Texture2DSample(SandN, SandNSampler, uvZ).rgb;
        aX = Texture2DSample(SandA, SandASampler, uvX).rgb; aY = Texture2DSample(SandA, SandASampler, uvY).rgb; aZ = Texture2DSample(SandA, SandASampler, uvZ).rgb;
    }
    else if (i == 1)
    {
        cX = Texture2DSample(RockD, RockDSampler, uvX).rgb; cY = Texture2DSample(RockD, RockDSampler, uvY).rgb; cZ = Texture2DSample(RockD, RockDSampler, uvZ).rgb;
        nX = Texture2DSample(RockN, RockNSampler, uvX).rgb; nY = Texture2DSample(RockN, RockNSampler, uvY).rgb; nZ = Texture2DSample(RockN, RockNSampler, uvZ).rgb;
        aX = Texture2DSample(RockA, RockASampler, uvX).rgb; aY = Texture2DSample(RockA, RockASampler, uvY).rgb; aZ = Texture2DSample(RockA, RockASampler, uvZ).rgb;
    }
    else
    {
        cX = Texture2DSample(StrataD, StrataDSampler, uvX).rgb; cY = Texture2DSample(StrataD, StrataDSampler, uvY).rgb; cZ = Texture2DSample(StrataD, StrataDSampler, uvZ).rgb;
        nX = Texture2DSample(StrataN, StrataNSampler, uvX).rgb; nY = Texture2DSample(StrataN, StrataNSampler, uvY).rgb; nZ = Texture2DSample(StrataN, StrataNSampler, uvZ).rgb;
        aX = Texture2DSample(StrataA, StrataASampler, uvX).rgb; aY = Texture2DSample(StrataA, StrataASampler, uvY).rgb; aZ = Texture2DSample(StrataA, StrataASampler, uvZ).rgb;
    }
    float3 mean = i == 0 ? SandMean.rgb : (i == 1 ? RockMean.rgb : StrataMean.rgb);
    float3 c = (cX * w.x + cY * w.y + cZ * w.z) / max(mean, 0.02);
    // Normal maps come in as BC5 (x, y in 0..1); rebuild z, then blend into world space per plane
    // (whiteout blend: the plane's normal plus the map's tilt).
    float3 tX = float3(nX.xy * 2.0 - 1.0, 0); tX.z = sqrt(saturate(1.0 - dot(tX.xy, tX.xy)));
    float3 tY = float3(nY.xy * 2.0 - 1.0, 0); tY.z = sqrt(saturate(1.0 - dot(tY.xy, tY.xy)));
    float3 tZ = float3(nZ.xy * 2.0 - 1.0, 0); tZ.z = sqrt(saturate(1.0 - dot(tZ.xy, tZ.xy)));
    float3 wX = float3(tX.xy + n.zy, abs(tX.z) * n.x).zyx;
    float3 wY = float3(tY.xy + n.xz, abs(tY.z) * n.y).xzy;
    float3 wZ = float3(tZ.xy + n.xy, abs(tZ.z) * n.z);
    float3 nn = normalize(wX * w.x + wY * w.y + wZ * w.z);
    float3 arm = aX * w.x + aY * w.y + aZ * w.z;
    detail += c * weights[i];
    tnSum += nn * weights[i];
    ra += float2(arm.g, arm.r) * weights[i];
}
// The textures' detail on the region colour; a little of their own hue survives.
colour *= lerp(float3(1, 1, 1), detail, DetailStrength);
float3 tn = tnSum * rsqrt(max(dot(tnSum, tnSum), 1e-8));
float3 nOut = lerp(n, tn, NormalStrength);
nOut = nOut * rsqrt(max(dot(nOut, nOut), 1e-8));
nOut = any(isnan(nOut)) ? n : nOut;
NormalOut = nOut;
AOOut = lerp(1.0, ra.y, 0.8);
// Dry ground is rough: the scans' own roughness (some near 0.5) made the crests shine as if wet.
return float4(max(colour, 0.0), lerp(MinRoughness, 1.0, saturate(ra.x)));
