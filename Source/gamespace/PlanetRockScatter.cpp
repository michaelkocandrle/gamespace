// Copyright Epic Games, Inc. All Rights Reserved.

#include "PlanetRockScatter.h"

#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/CollisionProfile.h"
#include "Engine/StaticMesh.h"

namespace PlanetRocks
{
	/** A stable hash of a cell and a salt: the same cell always gets the same rocks. */
	uint32 Hash(int32 Face, int32 X, int32 Y, uint32 Salt)
	{
		uint32 H = uint32(Face) * 0x9E3779B1u ^ uint32(X) * 0x85EBCA77u ^ uint32(Y) * 0xC2B2AE3Du ^ Salt * 0x27D4EB2Fu;
		H ^= H >> 15;
		H *= 0x2C1B3C6Du;
		H ^= H >> 12;
		H *= 0x297A2D39u;
		H ^= H >> 15;
		return H;
	}
}

UPlanetRockScatter::UPlanetRockScatter()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UPlanetRockScatter::Initialize(const FPlanetTerrainSettings& InSettings)
{
	Settings = InSettings;
	for (UInstancedStaticMeshComponent* Existing : Instances)
	{
		if (Existing)
		{
			Existing->DestroyComponent();
		}
	}
	Instances.Reset();
	for (int32 Index = 0; Index < Kinds.Num(); ++Index)
	{
		UInstancedStaticMeshComponent* Component = NewObject<UInstancedStaticMeshComponent>(GetOwner(),
			*FString::Printf(TEXT("Rocks_%d"), Index));
		Component->SetStaticMesh(Kinds[Index].Mesh);
		Component->SetMobility(EComponentMobility::Movable);
		Component->SetCollisionProfileName(UCollisionProfile::NoCollision_ProfileName);
		Component->SetGenerateOverlapEvents(false);
		Component->SetCanEverAffectNavigation(false);
		Component->SetupAttachment(this);
		if (GetOwner() && GetOwner()->GetWorld())
		{
			Component->RegisterComponent();
		}
		Instances.Add(Component);
	}
	LastCell = { -1, INT_MIN, INT_MIN };
	bInitialized = true;
}

void UPlanetRockScatter::CellsAround(const FVector& CameraLocal, TArray<FCellKey>& OutCells) const
{
	OutCells.Reset();
	const int64 Cells = int64(1) << CellDepth;
	const double CellFace = 2.0 / double(Cells);
	// Cell size along the ground, roughly: a face spans a quarter of the circumference.
	const double CellCm = UE_HALF_PI * Settings.RadiusCm / double(Cells);
	const int32 Reach = FMath::CeilToInt32(ScatterRadiusM * 100.0 / CellCm) + 1;
	const FVector Dir = CameraLocal.GetSafeNormal();
	int32 Face;
	double U, V;
	PlanetTerrain::DirectionToFace(Dir, Face, U, V);
	const int32 CX = FMath::Clamp(int32((U + 1.0) / CellFace), 0, int32(Cells) - 1);
	const int32 CY = FMath::Clamp(int32((V + 1.0) / CellFace), 0, int32(Cells) - 1);
	const double RadiusSq = FMath::Square(ScatterRadiusM * 100.0 + CellCm);
	TSet<uint64> Seen;
	for (int32 DY = -Reach; DY <= Reach; ++DY)
	{
		for (int32 DX = -Reach; DX <= Reach; ++DX)
		{
			// Past a face edge FaceDirection simply extends the face's plane, which lands on the
			// neighbouring face; the cell is then looked up again there, so no rocks go missing at seams.
			const double CU = -1.0 + (CX + DX + 0.5) * CellFace;
			const double CV = -1.0 + (CY + DY + 0.5) * CellFace;
			if (FMath::Abs(CU) > 1.9 || FMath::Abs(CV) > 1.9)
			{
				continue;
			}
			const FVector CellDir = PlanetTerrain::FaceDirection(Face, CU, CV).GetSafeNormal();
			if (FVector::DistSquared(CellDir * Settings.RadiusCm, Dir * Settings.RadiusCm) > RadiusSq)
			{
				continue;
			}
			int32 CellFaceIndex;
			double FU, FV;
			PlanetTerrain::DirectionToFace(CellDir, CellFaceIndex, FU, FV);
			const FCellKey Key{ CellFaceIndex,
				FMath::Clamp(int32((FU + 1.0) / CellFace), 0, int32(Cells) - 1),
				FMath::Clamp(int32((FV + 1.0) / CellFace), 0, int32(Cells) - 1) };
			const uint64 Packed = (uint64(Key.Face) << 56) | (uint64(uint32(Key.X)) << 28) | uint64(uint32(Key.Y));
			if (!Seen.Contains(Packed))
			{
				Seen.Add(Packed);
				OutCells.Add(Key);
			}
		}
	}
}

void UPlanetRockScatter::RocksInCell(const FCellKey& Cell, TArray<TArray<FTransform>>& InOut) const
{
	const int64 Cells = int64(1) << CellDepth;
	const double CellFace = 2.0 / double(Cells);
	FRandomStream Random(int32(PlanetRocks::Hash(Cell.Face, Cell.X, Cell.Y, uint32(Settings.Seed))));
	// Clustering: some cells nearly empty, the rest full.
	const float CellFill = Random.FRand() < EmptyCellShare ? 0.15f : Random.FRandRange(0.7f, 1.4f);
	// The cell's own slope decides rock or dust, sampled at its centre.
	const FVector CentreDir = PlanetTerrain::FaceDirection(Cell.Face, -1.0 + (Cell.X + 0.5) * CellFace, -1.0 + (Cell.Y + 0.5) * CellFace);
	const float CentreSlope = float(1.0 - FVector::DotProduct(PlanetTerrain::SurfaceNormal(Settings, CentreDir), CentreDir));
	const float Rocky = FMath::SmoothStep(SlopeRockStart, SlopeRockEnd, CentreSlope);

	for (int32 KindIndex = 0; KindIndex < Kinds.Num(); ++KindIndex)
	{
		const FPlanetRockKind& Kind = Kinds[KindIndex];
		if (!Kind.Mesh)
		{
			continue;
		}
		const float Expected = FMath::Lerp(Kind.PerCellFlat, Kind.PerCellSlope, Rocky) * CellFill;
		// Whole rocks plus a chance of one more for the fraction.
		int32 Count = FMath::FloorToInt32(Expected);
		if (Random.FRand() < Expected - float(Count))
		{
			++Count;
		}
		const FBoxSphereBounds MeshBounds = Kind.Mesh->GetBounds();
		for (int32 Rock = 0; Rock < Count; ++Rock)
		{
			const double U = -1.0 + (Cell.X + Random.FRand()) * CellFace;
			const double V = -1.0 + (Cell.Y + Random.FRand()) * CellFace;
			const FVector Dir = PlanetTerrain::FaceDirection(Cell.Face, U, V);
			const FVector Ground = PlanetTerrain::SurfacePoint(Settings, Dir);
			const FVector Normal = PlanetTerrain::SurfaceNormal(Settings, Dir);
			// Mostly small, few big: squared.
			const float Scale = FMath::Lerp(Kind.MinScale, Kind.MaxScale, FMath::Square(Random.FRand()));
			// Up along the ground's normal (a little random tilt), a random turn about it.
			const FVector Up = (Normal + Random.GetUnitVector() * 0.15).GetSafeNormal();
			const FQuat Align = FQuat::FindBetweenNormals(FVector::UpVector, Up);
			const FQuat Spin(FVector::UpVector, Random.FRandRange(0.f, UE_TWO_PI));
			// The rock's lowest point goes SinkFraction of its height below the ground.
			const double Bottom = MeshBounds.Origin.Z - MeshBounds.BoxExtent.Z;
			const double Offset = (Bottom + MeshBounds.BoxExtent.Z * 2.0 * SinkFraction) * Scale;
			InOut[KindIndex].Add(FTransform(Align * Spin, Ground - Up * Offset, FVector(Scale)));
		}
	}
}

void UPlanetRockScatter::UpdateScatter(const FVector& CameraLocal, double AltitudeCm)
{
	if (!bInitialized || Instances.Num() != Kinds.Num())
	{
		return;
	}
	if (AltitudeCm > MaxAltitudeM * 100.0)
	{
		if (bShown)
		{
			for (UInstancedStaticMeshComponent* Component : Instances)
			{
				Component->ClearInstances();
			}
			bShown = false;
			LastCell = { -1, INT_MIN, INT_MIN };
		}
		return;
	}

	const int64 Cells = int64(1) << CellDepth;
	const double CellFace = 2.0 / double(Cells);
	int32 Face;
	double U, V;
	PlanetTerrain::DirectionToFace(CameraLocal.GetSafeNormal(), Face, U, V);
	const FCellKey Current{ Face, FMath::Clamp(int32((U + 1.0) / CellFace), 0, int32(Cells) - 1),
		FMath::Clamp(int32((V + 1.0) / CellFace), 0, int32(Cells) - 1) };
	if (bShown && Current == LastCell)
	{
		return;
	}
	LastCell = Current;
	bShown = true;

	TArray<FCellKey> Around;
	CellsAround(CameraLocal, Around);
	TArray<TArray<FTransform>> PerKind;
	PerKind.SetNum(Kinds.Num());
	for (const FCellKey& Cell : Around)
	{
		RocksInCell(Cell, PerKind);
	}
	for (int32 Index = 0; Index < Instances.Num(); ++Index)
	{
		Instances[Index]->ClearInstances();
		Instances[Index]->AddInstances(PerKind[Index], false, false, false);
	}
}

TArray<int32> UPlanetRockScatter::DebugCountRocksAround(const FVector& CameraLocal)
{
	TArray<FCellKey> Around;
	CellsAround(CameraLocal, Around);
	TArray<TArray<FTransform>> PerKind;
	PerKind.SetNum(Kinds.Num());
	for (const FCellKey& Cell : Around)
	{
		RocksInCell(Cell, PerKind);
	}
	TArray<int32> Counts;
	for (const TArray<FTransform>& Kind : PerKind)
	{
		Counts.Add(Kind.Num());
	}
	return Counts;
}

TArray<FTransform> UPlanetRockScatter::DebugRocksInCell(const FVector& PointLocal, int32 Kind)
{
	const int64 Cells = int64(1) << CellDepth;
	const double CellFace = 2.0 / double(Cells);
	int32 Face;
	double U, V;
	PlanetTerrain::DirectionToFace(PointLocal.GetSafeNormal(), Face, U, V);
	const FCellKey Cell{ Face, FMath::Clamp(int32((U + 1.0) / CellFace), 0, int32(Cells) - 1),
		FMath::Clamp(int32((V + 1.0) / CellFace), 0, int32(Cells) - 1) };
	TArray<TArray<FTransform>> PerKind;
	PerKind.SetNum(Kinds.Num());
	RocksInCell(Cell, PerKind);
	return PerKind.IsValidIndex(Kind) ? PerKind[Kind] : TArray<FTransform>();
}
