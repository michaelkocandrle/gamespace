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

	double Height(const FPlanetTerrainSettings& Settings, const FVector& Dir)
	{
		// Sample 3D noise on the sphere itself: no seams, no pole distortion. The input is scaled
		// so one unit of noise space is one base wavelength along the surface.
		const FVector Point = Dir * (Settings.RadiusCm / Settings.BaseWavelengthCm) + Settings.SeedOffset;

		double Sum = 0.0;
		double Amplitude = 1.0;
		double Frequency = 1.0;
		for (int32 Octave = 0; Octave < Settings.Octaves; ++Octave)
		{
			Sum += Amplitude * FMath::PerlinNoise3D(Point * Frequency);
			Frequency *= Settings.Lacunarity;
			Amplitude *= Settings.Gain;
		}
		return Settings.AmplitudeCm * Sum;
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
		OutCenter = FaceDirection(Id.Face, UMin + Size * 0.5, VMin + Size * 0.5) * Settings.RadiusCm;

		// Corners on the base sphere bound the curved patch around a centre that is also on it;
		// the terrain can then add or remove at most MaxHeight in any direction.
		double MaxCornerSq = 0.0;
		for (int32 Corner = 0; Corner < 4; ++Corner)
		{
			const FVector P = FaceDirection(Id.Face, UMin + Size * (Corner & 1), VMin + Size * ((Corner >> 1) & 1)) * Settings.RadiusCm;
			MaxCornerSq = FMath::Max(MaxCornerSq, FVector::DistSquared(P, OutCenter));
		}
		OutRadius = FMath::Sqrt(MaxCornerSq) + Settings.MaxHeightCm();
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
