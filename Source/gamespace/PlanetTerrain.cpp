// Copyright Epic Games, Inc. All Rights Reserved.

#include "PlanetTerrain.h"

double FPlanetTerrainSettings::MaxHeightCm() const
{
	double Sum = 0.0;
	double Amplitude = 1.0;
	for (int32 Octave = 0; Octave < Octaves; ++Octave)
	{
		Sum += Amplitude;
		Amplitude *= Gain;
	}
	return AmplitudeCm * Sum;
}

namespace PlanetTerrain
{
	FVector FaceDirection(int32 Face, double U, double V)
	{
		const double A = FMath::Tan(U * UE_DOUBLE_HALF_PI * 0.5);
		const double B = FMath::Tan(V * UE_DOUBLE_HALF_PI * 0.5);
		FVector Cube;
		switch (Face)
		{
		case 0: Cube = FVector(1.0, A, B); break;
		case 1: Cube = FVector(-1.0, A, B); break;
		case 2: Cube = FVector(A, 1.0, B); break;
		case 3: Cube = FVector(A, -1.0, B); break;
		case 4: Cube = FVector(A, B, 1.0); break;
		default: Cube = FVector(A, B, -1.0); break;
		}
		return Cube.GetSafeNormal();
	}

	void DirectionToFace(const FVector& Dir, int32& OutFace, double& OutU, double& OutV)
	{
		const FVector Abs = Dir.GetAbs();
		double A;
		double B;
		if (Abs.X >= Abs.Y && Abs.X >= Abs.Z)
		{
			OutFace = Dir.X > 0.0 ? 0 : 1;
			A = Dir.Y / Abs.X;
			B = Dir.Z / Abs.X;
		}
		else if (Abs.Y >= Abs.Z)
		{
			OutFace = Dir.Y > 0.0 ? 2 : 3;
			A = Dir.X / Abs.Y;
			B = Dir.Z / Abs.Y;
		}
		else
		{
			OutFace = Dir.Z > 0.0 ? 4 : 5;
			A = Dir.X / Abs.Z;
			B = Dir.Y / Abs.Z;
		}
		OutU = FMath::Atan(A) / (UE_DOUBLE_HALF_PI * 0.5);
		OutV = FMath::Atan(B) / (UE_DOUBLE_HALF_PI * 0.5);
	}

	namespace
	{
		uint64 HashLattice(int64 X, int64 Y, int64 Z, uint32 Seed)
		{
			uint64 H = uint64(X) * 0x9E3779B185EBCA87ull;
			H ^= uint64(Y) * 0xC2B2AE3D27D4EB4Full + (H << 6) + (H >> 2);
			H ^= uint64(Z) * 0x165667B19E3779F9ull + (H << 6) + (H >> 2);
			H ^= uint64(Seed) * 0x27D4EB2F165667C5ull;
			// splitmix64 finaliser: every input bit affects every output bit.
			H ^= H >> 30;
			H *= 0xBF58476D1CE4E5B9ull;
			H ^= H >> 27;
			H *= 0x94D049BB133111EBull;
			H ^= H >> 31;
			return H;
		}

		/** Dot product with one of Perlin's 12 cube-edge gradients. */
		double Gradient(uint64 Hash, double X, double Y, double Z)
		{
			switch (Hash % 12)
			{
			case 0: return X + Y;
			case 1: return -X + Y;
			case 2: return X - Y;
			case 3: return -X - Y;
			case 4: return X + Z;
			case 5: return -X + Z;
			case 6: return X - Z;
			case 7: return -X - Z;
			case 8: return Y + Z;
			case 9: return -Y + Z;
			case 10: return Y - Z;
			default: return -Y - Z;
			}
		}

		double Fade(double T)
		{
			return T * T * T * (T * (T * 6.0 - 15.0) + 10.0);
		}
	}

	double GradientNoise3D(const FVector& Point, uint32 Seed)
	{
		const double FloorX = FMath::Floor(Point.X);
		const double FloorY = FMath::Floor(Point.Y);
		const double FloorZ = FMath::Floor(Point.Z);
		const int64 IX = int64(FloorX);
		const int64 IY = int64(FloorY);
		const int64 IZ = int64(FloorZ);
		const double X = Point.X - FloorX;
		const double Y = Point.Y - FloorY;
		const double Z = Point.Z - FloorZ;
		const double U = Fade(X);
		const double V = Fade(Y);
		const double W = Fade(Z);

		auto Corner = [&](int32 DX, int32 DY, int32 DZ)
		{
			return Gradient(HashLattice(IX + DX, IY + DY, IZ + DZ, Seed), X - DX, Y - DY, Z - DZ);
		};

		const double X00 = FMath::Lerp(Corner(0, 0, 0), Corner(1, 0, 0), U);
		const double X10 = FMath::Lerp(Corner(0, 1, 0), Corner(1, 1, 0), U);
		const double X01 = FMath::Lerp(Corner(0, 0, 1), Corner(1, 0, 1), U);
		const double X11 = FMath::Lerp(Corner(0, 1, 1), Corner(1, 1, 1), U);
		return FMath::Lerp(FMath::Lerp(X00, X10, V), FMath::Lerp(X01, X11, V), W);
	}

	double Height(const FPlanetTerrainSettings& Settings, const FVector& Dir)
	{
		// Sample 3D noise on the sphere itself: no seams, no pole distortion. The input is scaled
		// so one unit of noise space is one base wavelength along the surface.
		const FVector Point = Dir * (Settings.RadiusCm / Settings.BaseWavelengthCm);

		double Sum = 0.0;
		double Amplitude = 1.0;
		double Frequency = 1.0;
		for (int32 Octave = 0; Octave < Settings.Octaves; ++Octave)
		{
			// A different offset and seed per octave, so octaves don't line up on the same lattice.
			const FVector Offset(Octave * 31.4159, Octave * -17.1234, Octave * 11.7310);
			Sum += Amplitude * GradientNoise3D(Point * Frequency + Offset, Settings.Seed + uint32(Octave) * 1013u);
			Frequency *= Settings.Lacunarity;
			Amplitude *= Settings.Gain;
		}
		return Settings.AmplitudeCm * Sum;
	}

	double HeightVariationWithinTileCm(const FPlanetTerrainSettings& Settings, int32 Depth)
	{
		// Centre-to-corner distance of the tile along the surface.
		const double Reach = TileSizeCm(Settings, Depth) * 0.75;
		double SumSquares = 0.0;
		double Amplitude = Settings.AmplitudeCm;
		double Wavelength = Settings.BaseWavelengthCm;
		for (int32 Octave = 0; Octave < Settings.Octaves; ++Octave)
		{
			// Gradient noise changes by at most ~3 amplitudes per wavelength, and never by more
			// than its full range of 2 amplitudes.
			SumSquares += FMath::Square(FMath::Min(2.0 * Amplitude, 3.0 * Amplitude * Reach / Wavelength));
			Amplitude *= Settings.Gain;
			Wavelength /= Settings.Lacunarity;
		}
		// Octaves are independent, so their worst cases practically never line up; adding them
		// linearly made small tiles look several times taller than they are and doubled the tile
		// count. The root of the sum of squares is a realistic bound. An underestimate here only
		// makes a tile split a little later - it never opens holes.
		return FMath::Sqrt(SumSquares);
	}

	FVector SurfacePoint(const FPlanetTerrainSettings& Settings, const FVector& Dir)
	{
		return Dir * (Settings.RadiusCm + Height(Settings, Dir));
	}

	FVector SurfaceNormal(const FPlanetTerrainSettings& Settings, const FVector& Dir)
	{
		const FVector Helper = FMath::Abs(Dir.Z) < 0.9 ? FVector::UpVector : FVector::ForwardVector;
		const FVector T1 = FVector::CrossProduct(Dir, Helper).GetSafeNormal();
		const FVector T2 = FVector::CrossProduct(Dir, T1);
		const double Step = Settings.NormalStepCm / Settings.RadiusCm;

		// Central differences: symmetric, so the result does not lean towards one tangent.
		const FVector Dx = SurfacePoint(Settings, (Dir + T1 * Step).GetSafeNormal()) - SurfacePoint(Settings, (Dir - T1 * Step).GetSafeNormal());
		const FVector Dy = SurfacePoint(Settings, (Dir + T2 * Step).GetSafeNormal()) - SurfacePoint(Settings, (Dir - T2 * Step).GetSafeNormal());
		FVector Normal = FVector::CrossProduct(Dx, Dy).GetSafeNormal();
		return (Normal | Dir) < 0.0 ? -Normal : Normal;
	}

	double TileSizeCm(const FPlanetTerrainSettings& Settings, int32 Depth)
	{
		// A face spans 90 degrees of arc.
		return UE_DOUBLE_HALF_PI * Settings.RadiusCm / double(int64(1) << Depth);
	}

	void EstimateTileBounds(const FPlanetTerrainSettings& Settings, const FQuadTileId& Id, FVector& OutCenter, double& OutRadius)
	{
		double UMin;
		double VMin;
		double Size;
		Id.FaceBounds(UMin, VMin, Size);
		const FVector CenterDir = FaceDirection(Id.Face, UMin + Size * 0.5, VMin + Size * 0.5);
		const double SurfaceRadius = Settings.RadiusCm + Height(Settings, CenterDir);
		OutCenter = CenterDir * SurfaceRadius;

		// Corners on the sphere through the centre bound the curved patch; the terrain can then
		// only deviate from the centre height by the tile's own height variation.
		double MaxCornerSq = 0.0;
		for (int32 Corner = 0; Corner < 4; ++Corner)
		{
			const FVector P = FaceDirection(Id.Face, UMin + Size * (Corner & 1), VMin + Size * ((Corner >> 1) & 1)) * SurfaceRadius;
			MaxCornerSq = FMath::Max(MaxCornerSq, FVector::DistSquared(P, OutCenter));
		}
		OutRadius = FMath::Sqrt(MaxCornerSq) + HeightVariationWithinTileCm(Settings, Id.Depth);
	}

	namespace
	{
		/** Appends triangle (A, B, C), flipped if needed so it faces along Outward. */
		void AddFacingTriangle(TArray<int32>& Triangles, const TArray<FVector>& Positions, int32 A, int32 B, int32 C, const FVector& Outward)
		{
			// Unreal's front face: Cross(C - A, B - A) points out of the surface (see the box built
			// by UKismetProceduralMeshLibrary::GenerateBoxMesh).
			const FVector Facing = FVector::CrossProduct(Positions[C] - Positions[A], Positions[B] - Positions[A]);
			if ((Facing | Outward) >= 0.0)
			{
				Triangles.Append({ A, B, C });
			}
			else
			{
				Triangles.Append({ A, C, B });
			}
		}
	}

	TSharedPtr<FTerrainTileMesh> BuildTile(const FPlanetTerrainSettings& Settings, const FQuadTileId& Id, int32 Quads, bool bRenderData, double SkirtDepthCm)
	{
		TSharedPtr<FTerrainTileMesh> Tile = MakeShared<FTerrainTileMesh>();
		Tile->Id = Id;
		Tile->bRenderData = bRenderData;

		double UMin;
		double VMin;
		double Size;
		Id.FaceBounds(UMin, VMin, Size);

		const int32 Side = Quads + 1;
		const int32 GridCount = Side * Side;
		auto Index = [Side](int32 I, int32 J) { return J * Side + I; };

		// Planet-local surface samples. Face coordinates come from integers, so a vertex shared
		// with the parent or a neighbour of the same depth samples exactly the same direction.
		TArray<FVector> Dirs;
		TArray<FVector> Local;
		Dirs.SetNum(GridCount);
		Local.SetNum(GridCount);
		for (int32 J = 0; J < Side; ++J)
		{
			for (int32 I = 0; I < Side; ++I)
			{
				const FVector Dir = FaceDirection(Id.Face, UMin + Size * I / Quads, VMin + Size * J / Quads);
				Dirs[Index(I, J)] = Dir;
				Local[Index(I, J)] = SurfacePoint(Settings, Dir);
			}
		}

		const FVector CenterDir = FaceDirection(Id.Face, UMin + Size * 0.5, VMin + Size * 0.5);
		Tile->CenterLocal = SurfacePoint(Settings, CenterDir);

		Tile->Vertices.Reserve(GridCount + (bRenderData ? 4 * Quads : 0));
		for (const FVector& P : Local)
		{
			Tile->Vertices.Add(P - Tile->CenterLocal);
		}

		Tile->Triangles.Reserve(Quads * Quads * 6 + (bRenderData ? 4 * Quads * 6 : 0));
		for (int32 J = 0; J < Quads; ++J)
		{
			for (int32 I = 0; I < Quads; ++I)
			{
				const int32 A = Index(I, J);
				const int32 B = Index(I + 1, J);
				const int32 C = Index(I, J + 1);
				const int32 D = Index(I + 1, J + 1);
				// Diagonal always A-D: the geomorph targets below assume the parent is split the same way.
				AddFacingTriangle(Tile->Triangles, Tile->Vertices, A, D, B, Dirs[A]);
				AddFacingTriangle(Tile->Triangles, Tile->Vertices, A, C, D, Dirs[A]);
			}
		}

		if (bRenderData)
		{
			Tile->Normals.SetNum(GridCount);
			Tile->UV0.SetNum(GridCount);
			Tile->UV1.SetNum(GridCount);
			Tile->UV2.SetNum(GridCount);
			for (int32 J = 0; J < Side; ++J)
			{
				for (int32 I = 0; I < Side; ++I)
				{
					const int32 Vertex = Index(I, J);
					Tile->Normals[Vertex] = SurfaceNormal(Settings, Dirs[Vertex]);
					Tile->UV0[Vertex] = FVector2D(double(I) / Quads, double(J) / Quads);

					// Where the parent grid would put this point: vertices on even rows and columns
					// exist in the parent too; the rest lie on a parent edge or on the A-D diagonal.
					FVector Target = Local[Vertex];
					const bool bOddI = (I & 1) != 0;
					const bool bOddJ = (J & 1) != 0;
					if (bOddI && bOddJ)
					{
						Target = 0.5 * (Local[Index(I - 1, J - 1)] + Local[Index(I + 1, J + 1)]);
					}
					else if (bOddI)
					{
						Target = 0.5 * (Local[Index(I - 1, J)] + Local[Index(I + 1, J)]);
					}
					else if (bOddJ)
					{
						Target = 0.5 * (Local[Index(I, J - 1)] + Local[Index(I, J + 1)]);
					}
					const FVector Delta = Target - Local[Vertex];
					Tile->UV1[Vertex] = FVector2D(Delta.X, Delta.Y);
					Tile->UV2[Vertex] = FVector2D(Delta.Z, 0.0);
				}
			}

			// Skirts: a strip hanging below every edge. Neighbouring tiles of different depth do not
			// share vertices along their border, and the skirt covers the sliver that would open.
			TArray<int32> Perimeter;
			Perimeter.Reserve(4 * Quads);
			for (int32 I = 0; I < Quads; ++I) { Perimeter.Add(Index(I, 0)); }
			for (int32 J = 0; J < Quads; ++J) { Perimeter.Add(Index(Quads, J)); }
			for (int32 I = Quads; I > 0; --I) { Perimeter.Add(Index(I, Quads)); }
			for (int32 J = Quads; J > 0; --J) { Perimeter.Add(Index(0, J)); }

			const int32 FirstSkirt = Tile->Vertices.Num();
			for (int32 Edge : Perimeter)
			{
				// Copies first: Add() may reallocate, and a reference into the same array would dangle.
				const FVector Normal = Tile->Normals[Edge];
				const FVector2D UV0 = Tile->UV0[Edge];
				const FVector2D UV1 = Tile->UV1[Edge];
				const FVector2D UV2 = Tile->UV2[Edge];
				Tile->Vertices.Add(Local[Edge] - Dirs[Edge] * SkirtDepthCm - Tile->CenterLocal);
				Tile->Normals.Add(Normal);
				Tile->UV0.Add(UV0);
				Tile->UV1.Add(UV1);
				Tile->UV2.Add(UV2);
			}
			for (int32 K = 0; K < Perimeter.Num(); ++K)
			{
				const int32 E0 = Perimeter[K];
				const int32 E1 = Perimeter[(K + 1) % Perimeter.Num()];
				const int32 S0 = FirstSkirt + K;
				const int32 S1 = FirstSkirt + (K + 1) % Perimeter.Num();
				// Face away from the tile centre, like the tile's side walls.
				const FVector Outward = (0.5 * (Local[E0] + Local[E1])) - Tile->CenterLocal;
				AddFacingTriangle(Tile->Triangles, Tile->Vertices, E0, S0, E1, Outward);
				AddFacingTriangle(Tile->Triangles, Tile->Vertices, E1, S0, S1, Outward);
			}
		}

		for (const FVector& V : Tile->Vertices)
		{
			Tile->BoundsRadius = FMath::Max(Tile->BoundsRadius, V.Size());
		}
		return Tile;
	}
}
