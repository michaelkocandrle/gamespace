// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "ProceduralMeshComponent.h"

/**
 * Pure, stateless geometry for a quad-sphere planet: cube-to-sphere mapping, the height field and
 * tile mesh building. Everything here is thread-safe, so tiles are built on worker threads.
 *
 * Coordinates:
 * - "Planet-local" is relative to the planet centre, in cm, as double.
 * - Tile vertices are relative to the tile's own centre. The tile component sits at that centre,
 *   so the mesh data (single precision on the GPU and in the render proxy) only ever holds values
 *   the size of one tile, while the placement stays in the double-precision component transform.
 */

struct FPlanetTerrainSettings
{
	double RadiusCm = 50000.0;
	/** Height of the first noise octave; later octaves add Gain^n of it. */
	double AmplitudeCm = 1200.0;
	/** Wavelength of the first octave, measured along the surface. */
	double BaseWavelengthCm = 20000.0;
	int32 Octaves = 8;
	double Lacunarity = 2.0;
	double Gain = 0.5;
	/** Different seeds give different planets (mixed into the noise lattice hash). */
	uint32 Seed = 1;
	/**
	 * The first this many octaves are ridged (1 - |noise|): sharp crests, rounded valleys,
	 * instead of plain fBm's even, rolling bumps that read as water up close (21. 9. 2026). 0 is plain fBm.
	 */
	int32 RidgedOctaves = 0;
	/**
	 * The finer octaves are scaled by how much of a crest the point is on: this on the flats and in the
	 * valleys, 1 on the ridges. Dust fills the lows; rock stays rough.
	 */
	double DetailInValleys = 1.0;
	/**
	 * Finite-difference step for normals. Fixed, not per-LOD, so a point gets exactly the same
	 * normal whichever LOD level renders it - otherwise lighting shows seams between levels.
	 */
	double NormalStepCm = 50.0;

	/** Upper bound of |height|: the sum of all octave amplitudes. */
	double MaxHeightCm() const;
};

/** One node of the per-face quadtree. */
struct FQuadTileId
{
	uint8 Face = 0;
	uint8 Depth = 0;
	int32 X = 0;
	int32 Y = 0;

	uint64 Key() const
	{
		return (uint64(Face) << 58) | (uint64(Depth) << 52) | (uint64(uint32(X)) << 26) | uint64(uint32(Y));
	}

	FQuadTileId Child(int32 Index) const
	{
		return { Face, uint8(Depth + 1), X * 2 + (Index & 1), Y * 2 + ((Index >> 1) & 1) };
	}

	FQuadTileId Parent() const
	{
		return { Face, uint8(Depth - 1), X / 2, Y / 2 };
	}

	/** Face coordinates of the tile's lower corner and its edge length, all in [-1, 1] units. */
	void FaceBounds(double& OutUMin, double& OutVMin, double& OutSize) const
	{
		OutSize = 2.0 / double(int64(1) << Depth);
		OutUMin = -1.0 + X * OutSize;
		OutVMin = -1.0 + Y * OutSize;
	}
};

/** Mesh data for one tile, ready for UProceduralMeshComponent::CreateMeshSection. */
struct FTerrainTileMesh
{
	FQuadTileId Id;
	bool bRenderData = false;

	/** Tile centre on the surface, planet-local. The component is placed here. */
	FVector CenterLocal = FVector::ZeroVector;
	/** Largest vertex distance from CenterLocal. */
	double BoundsRadius = 0.0;

	TArray<FVector> Vertices;      // relative to CenterLocal
	TArray<int32> Triangles;
	TArray<FVector> Normals;
	TArray<FVector2D> UV0;         // tile-local (0..1), for later texturing
	TArray<FVector2D> UV1;         // morph delta X, Y (cm, tile-local frame)
	TArray<FVector2D> UV2;         // morph delta Z, unused
	TArray<FProcMeshTangent> Tangents;
};

namespace PlanetTerrain
{
	/**
	 * Unit direction for a point on a cube face. Uses the equi-angular mapping (tan of the face
	 * coordinate), which keeps tiles within ~30% of the same size across the face; a plain
	 * normalised cube makes corner tiles half the size of centre ones.
	 */
	GAMESPACE_API FVector FaceDirection(int32 Face, double U, double V);

	/** Inverse of FaceDirection. */
	GAMESPACE_API void DirectionToFace(const FVector& Dir, int32& OutFace, double& OutU, double& OutV);

	/**
	 * 3D gradient noise (improved Perlin) entirely in double precision, roughly in [-1, 1].
	 *
	 * Replaces FMath::PerlinNoise3D, which works in float: at the high octaves a large planet needs,
	 * the sample coordinates get big enough for float rounding to show up as terracing. The lattice
	 * is hashed instead of using a 256-entry permutation table, so it never repeats.
	 */
	GAMESPACE_API double GradientNoise3D(const FVector& Point, uint32 Seed);

	/** Terrain height above the base radius, in cm, for a unit direction. */
	GAMESPACE_API double Height(const FPlanetTerrainSettings& Settings, const FVector& Dir);

	/**
	 * Realistic bound (octaves combined as root of sum of squares) on how far the terrain inside a tile at Depth can rise or fall relative to the
	 * height at its centre. Large octaves barely change across a small tile, so this shrinks with
	 * depth - unlike the planet-wide MaxHeight, which is kilometres on a mountainous planet and would
	 * make every small tile look near and split.
	 */
	GAMESPACE_API double HeightVariationWithinTileCm(const FPlanetTerrainSettings& Settings, int32 Depth);

	/** Planet-local surface point for a unit direction. */
	GAMESPACE_API FVector SurfacePoint(const FPlanetTerrainSettings& Settings, const FVector& Dir);

	/** Outward surface normal, from the height field rather than from any mesh. */
	GAMESPACE_API FVector SurfaceNormal(const FPlanetTerrainSettings& Settings, const FVector& Dir);

	/** Nominal edge length of a tile at Depth, along the surface, in cm. */
	GAMESPACE_API double TileSizeCm(const FPlanetTerrainSettings& Settings, int32 Depth);

	/**
	 * Bounds for LOD decisions: centre on the real surface (one height sample) and a radius from
	 * the tile's extent plus HeightVariationWithinTileCm. Callers cache the result per tile.
	 */
	GAMESPACE_API void EstimateTileBounds(const FPlanetTerrainSettings& Settings, const FQuadTileId& Id, FVector& OutCenter, double& OutRadius);

	/**
	 * Builds a tile of Quads x Quads cells.
	 *
	 * bRenderData adds normals, UVs, per-vertex geomorph targets and edge skirts. Without it the
	 * result is positions and triangles only, for collision.
	 *
	 * Geomorphing: a vertex that does not exist on the parent's grid gets, in UV1/UV2, the offset
	 * that moves it onto the parent's surface. The material applies that offset as the camera
	 * moves away, so a tile looks exactly like its parent by the time it is swapped for it.
	 */
	GAMESPACE_API TSharedPtr<FTerrainTileMesh> BuildTile(const FPlanetTerrainSettings& Settings, const FQuadTileId& Id, int32 Quads, bool bRenderData, double SkirtDepthCm);
}
