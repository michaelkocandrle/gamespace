// Copyright Epic Games, Inc. All Rights Reserved.

#include "QuadSpherePlanet.h"

#include "Async/Async.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/CollisionProfile.h"
#include "GameFramework/Pawn.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"
#include "ProceduralMeshComponent.h"

namespace
{
	TAutoConsoleVariable<int32> CVarTerrainDebugLOD(
		TEXT("space.TerrainDebugLOD"), 0,
		TEXT("1 tints every terrain tile by its quadtree depth, to watch LOD transitions."));

	TAutoConsoleVariable<int32> CVarTerrainFreezeLOD(
		TEXT("space.TerrainFreezeLOD"), 0,
		TEXT("1 stops terrain LOD updates, so the current tiles can be inspected from elsewhere."));

	/** SM_PlanetSphere, used for the Body safety sphere, has a radius of 100 cm. */
	constexpr double SafetySphereMeshRadiusCm = 100.0;

	/** Custom primitive data slots read by M_Planet_Terrain. */
	enum ETerrainPrimitiveData : int32
	{
		CPD_TileCenter = 0,     // 0..2, planet-local
		CPD_MorphStart = 3,
		CPD_MorphEnd = 4,
		CPD_PlanetRadius = 5,
		CPD_Depth = 6,
		CPD_DebugTint = 7,
	};
}

AQuadSpherePlanet::AQuadSpherePlanet()
{
	PrimaryActorTick.bCanEverTick = true;
	// After the camera has moved this frame.
	PrimaryActorTick.TickGroup = TG_PostUpdateWork;

	TerrainRoot = CreateDefaultSubobject<USceneComponent>(TEXT("TerrainRoot"));
	SetRootComponent(TerrainRoot);

	// The inherited Body becomes an invisible safety sphere just under the lowest possible terrain.
	Body->SetupAttachment(TerrainRoot);
	Body->SetHiddenInGame(true);
	Body->SetCastShadow(false);
}

FPlanetTerrainSettings AQuadSpherePlanet::MakeSettings() const
{
	FPlanetTerrainSettings Result;
	Result.RadiusCm = RadiusKm * 100000.0;
	Result.AmplitudeCm = TerrainAmplitudeM * 100.0;
	Result.BaseWavelengthCm = BaseWavelengthM * 100.0;
	Result.Octaves = NoiseOctaves;
	Result.SeedOffset = FVector(NoiseSeed * 17.31, NoiseSeed * -31.77, NoiseSeed * 7.13);
	return Result;
}

void AQuadSpherePlanet::RefreshDerivedSettings()
{
	Settings = MakeSettings();
	TileQuads = FMath::Max(4, TileQuads & ~1);
	CollisionTileQuads = FMath::Max(2, CollisionTileQuads);
	const double RootSize = PlanetTerrain::TileSizeCm(Settings, 0);
	MaxDepth = FMath::Clamp(FMath::CeilToInt32(FMath::Log2(RootSize / (LeafTileSizeM * 100.0))), 0, 24);
	CollisionDepth = FMath::Clamp(FMath::RoundToInt32(FMath::Log2(RootSize / (CollisionTileSizeM * 100.0))), 0, MaxDepth);
	Stats.MaxDepth = MaxDepth;
}

void AQuadSpherePlanet::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	RefreshDerivedSettings();

	const double SafetyRadiusCm = Settings.RadiusCm - Settings.MaxHeightCm() - 100.0;
	Body->SetRelativeScale3D(FVector(FMath::Max(SafetyRadiusCm, 100.0) / SafetySphereMeshRadiusCm));
}

void AQuadSpherePlanet::BeginPlay()
{
	Super::BeginPlay();
	RefreshDerivedSettings();

	// The six root tiles are built synchronously, so there is always something to fall back on.
	for (uint8 Face = 0; Face < 6; ++Face)
	{
		const FQuadTileId Root{ Face, 0, 0, 0 };
		const TSharedPtr<FTerrainTileMesh> Mesh = PlanetTerrain::BuildTile(
			Settings, Root, TileQuads, true, PlanetTerrain::TileSizeCm(Settings, 0) * 0.05 + 100.0);
		FTile& Tile = Tiles.Add(Root.Key());
		Tile.Id = Root;
		Tile.Mesh = CreateTileComponent(*Mesh, false);
		++Stats.TilesBuilt;
	}
}

void AQuadSpherePlanet::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	// Unfinished builds only capture settings by value; dropping the futures lets them finish and
	// discard their results without touching this actor.
	Builds.Reset();
	Super::EndPlay(EndPlayReason);
}

// -------------------------------------------------------------------------------------------
// Per frame
// -------------------------------------------------------------------------------------------

void AQuadSpherePlanet::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	const double TickStart = FPlatformTime::Seconds();

	CollectFinishedBuilds();
	Stats.UploadMs = (FPlatformTime::Seconds() - TickStart) * 1000.0;

	const FTransform& ToWorld = GetActorTransform();
	Stats.SelectionMs = 0.0;
	if (CVarTerrainFreezeLOD.GetValueOnGameThread() == 0)
	{
		if (const APlayerCameraManager* Camera = UGameplayStatics::GetPlayerCameraManager(this, 0))
		{
			// Re-select only when the camera moved noticeably for its altitude, or tiles came or
			// went; a hovering or slow ship then costs nothing here.
			const FVector CameraLocal = ToWorld.InverseTransformPositionNoScale(Camera->GetCameraLocation());
			const double Altitude = FMath::Max(0.0, CameraLocal.Size() - Settings.RadiusCm);
			const double MoveThreshold = FMath::Max(50.0, LodUpdateMoveFraction * Altitude);
			if (bTilesChangedSinceLod || FVector::DistSquared(CameraLocal, LastLodCameraLocal) > FMath::Square(MoveThreshold))
			{
				bTilesChangedSinceLod = false;
				LastLodCameraLocal = CameraLocal;
				UpdateRenderLod(CameraLocal, GetWorld()->GetTimeSeconds());
			}
		}
	}

	if (const APawn* Ship = UGameplayStatics::GetPlayerPawn(this, 0))
	{
		UpdateCollisionTiles(ToWorld.InverseTransformPositionNoScale(Ship->GetActorLocation()));
	}

	const int32 DebugTint = CVarTerrainDebugLOD.GetValueOnGameThread();
	if (DebugTint != AppliedDebugTint)
	{
		AppliedDebugTint = DebugTint;
		for (TPair<uint64, FTile>& Pair : Tiles)
		{
			ApplyDebugTint(Pair.Value.Mesh, Pair.Value.Id.Depth);
		}
	}

	Stats.CachedTiles = Tiles.Num();
	Stats.PendingBuilds = Builds.Num();
	Stats.CollisionTiles = CollisionTiles.Num();
	Stats.TickMs = (FPlatformTime::Seconds() - TickStart) * 1000.0;
}

void AQuadSpherePlanet::UpdateRenderLod(const FVector& CameraLocal, double NowSeconds)
{
	const double StartSeconds = FPlatformTime::Seconds();

	// 1) Which nodes should be split, and which leaves we want, from the camera distance alone.
	TSet<uint64> Split;
	TArray<TPair<double, FQuadTileId>> WantedLeaves;
	TArray<FQuadTileId> Stack;
	for (uint8 Face = 0; Face < 6; ++Face)
	{
		Stack.Add({ Face, 0, 0, 0 });
	}
	while (Stack.Num() > 0)
	{
		const FQuadTileId Id = Stack.Pop(EAllowShrinking::No);
		FVector Center;
		double Radius;
		PlanetTerrain::EstimateTileBounds(Settings, Id, Center, Radius);
		const double Distance = FMath::Max(0.0, FVector::Dist(CameraLocal, Center) - Radius);
		const double Hysteresis = SplitLastFrame.Contains(Id.Key()) ? MergeHysteresis : 1.0;
		const double SplitDistance = LodDistanceFactor * PlanetTerrain::TileSizeCm(Settings, Id.Depth) * Hysteresis;

		if (Id.Depth < MaxDepth && Distance < SplitDistance)
		{
			Split.Add(Id.Key());
			for (int32 Child = 0; Child < 4; ++Child)
			{
				Stack.Add(Id.Child(Child));
			}
		}
		else
		{
			WantedLeaves.Add({ Distance, Id });
		}
	}

	// 2) What can actually be shown right now without holes.
	TMap<uint64, bool> Memo;
	TSet<uint64> Visible;
	for (uint8 Face = 0; Face < 6; ++Face)
	{
		const FQuadTileId Root{ Face, 0, 0, 0 };
		if (CanRender(Root, Memo))
		{
			ChooseVisible(Root, Split, Memo, Visible);
		}
	}

	int32 MaxVisibleDepth = 0;
	for (TPair<uint64, FTile>& Pair : Tiles)
	{
		FTile& Tile = Pair.Value;
		const bool bShow = Visible.Contains(Pair.Key);
		if (bShow != Tile.bVisible)
		{
			Tile.Mesh->SetVisibility(bShow);
			Tile.bVisible = bShow;
		}
		if (bShow)
		{
			Tile.LastUsedSeconds = NowSeconds;
			MaxVisibleDepth = FMath::Max<int32>(MaxVisibleDepth, Tile.Id.Depth);
		}
	}

	// 3) Build what is missing, nearest first.
	TSet<uint64> WantedKeys;
	WantedLeaves.Sort([](const TPair<double, FQuadTileId>& A, const TPair<double, FQuadTileId>& B) { return A.Key < B.Key; });
	for (const TPair<double, FQuadTileId>& Leaf : WantedLeaves)
	{
		const uint64 Key = Leaf.Value.Key();
		WantedKeys.Add(Key);
		if (FTile* Existing = Tiles.Find(Key))
		{
			Existing->LastUsedSeconds = NowSeconds;
		}
		else if (!BuildingRender.Contains(Key) && BuildingRender.Num() < MaxConcurrentBuilds)
		{
			LaunchBuild(Leaf.Value, false);
		}
	}

	// 4) Free the least recently used tiles beyond the cache limit, a few per frame: destroying
	// hundreds of components in one frame is a visible hitch.
	if (Tiles.Num() > TileCacheLimit)
	{
		TArray<TPair<double, uint64>> Candidates;
		for (const TPair<uint64, FTile>& Pair : Tiles)
		{
			if (!Pair.Value.bVisible && Pair.Value.Id.Depth > 0 && !WantedKeys.Contains(Pair.Key))
			{
				Candidates.Add({ Pair.Value.LastUsedSeconds, Pair.Key });
			}
		}
		Candidates.Sort([](const TPair<double, uint64>& A, const TPair<double, uint64>& B) { return A.Key < B.Key; });
		const int32 Evictions = FMath::Min3(Candidates.Num(), Tiles.Num() - TileCacheLimit, MaxEvictionsPerFrame);
		for (int32 I = 0; I < Evictions; ++I)
		{
			DestroyTile(Candidates[I].Value);
		}
		// Built descendants changed, so what can render changed: select again next frame.
		bTilesChangedSinceLod |= Evictions > 0;
	}

	SplitLastFrame = MoveTemp(Split);
	Stats.VisibleTiles = Visible.Num();
	Stats.MaxVisibleDepth = MaxVisibleDepth;
	Stats.SelectionMs = (FPlatformTime::Seconds() - StartSeconds) * 1000.0;
}

bool AQuadSpherePlanet::CanRender(const FQuadTileId& Id, TMap<uint64, bool>& Memo) const
{
	const uint64 Key = Id.Key();
	if (const bool* Known = Memo.Find(Key))
	{
		return *Known;
	}
	// Only descend where built descendants exist; otherwise this would walk the whole tree.
	const bool bResult = IsReady(Id) || (ReadyDescendants.Contains(Key) && AllChildrenCanRender(Id, Memo));
	Memo.Add(Key, bResult);
	return bResult;
}

bool AQuadSpherePlanet::AllChildrenCanRender(const FQuadTileId& Id, TMap<uint64, bool>& Memo) const
{
	if (Id.Depth >= MaxDepth)
	{
		return false;
	}
	for (int32 Child = 0; Child < 4; ++Child)
	{
		if (!CanRender(Id.Child(Child), Memo))
		{
			return false;
		}
	}
	return true;
}

void AQuadSpherePlanet::ChooseVisible(const FQuadTileId& Id, const TSet<uint64>& SplitNodes, TMap<uint64, bool>& Memo, TSet<uint64>& OutVisible) const
{
	const bool bWantsSplit = SplitNodes.Contains(Id.Key());
	const bool bReady = IsReady(Id);

	// Go finer when wanted and the children are complete - or when this tile itself is gone but
	// its children are still there (a merge waiting for the parent to be built).
	if ((bWantsSplit || !bReady) && AllChildrenCanRender(Id, Memo))
	{
		for (int32 Child = 0; Child < 4; ++Child)
		{
			ChooseVisible(Id.Child(Child), SplitNodes, Memo, OutVisible);
		}
	}
	else if (bReady)
	{
		OutVisible.Add(Id.Key());
	}
}

void AQuadSpherePlanet::UpdateCollisionTiles(const FVector& ShipLocal)
{
	const double RadiusCm = CollisionRadiusM * 100.0;
	const double TileSize = PlanetTerrain::TileSizeCm(Settings, CollisionDepth);
	const int32 TilesPerSide = 1 << CollisionDepth;

	TSet<uint64> Wanted;
	TMap<uint64, FQuadTileId> WantedIds;
	const double Altitude = ShipLocal.Size() - Settings.RadiusCm - Settings.MaxHeightCm();
	if (Altitude < RadiusCm)
	{
		// Sample the surface around the point under the ship; this crosses cube-face edges
		// naturally, which walking tile indices on one face would not.
		const FVector Dir = ShipLocal.GetSafeNormal();
		const FVector T1 = FVector::CrossProduct(Dir, FMath::Abs(Dir.Z) < 0.9 ? FVector::UpVector : FVector::ForwardVector).GetSafeNormal();
		const FVector T2 = FVector::CrossProduct(Dir, T1);
		const double Step = TileSize * 0.5;
		const double Reach = RadiusCm + TileSize;
		const int32 Steps = FMath::CeilToInt32(Reach / Step);
		for (int32 A = -Steps; A <= Steps; ++A)
		{
			for (int32 B = -Steps; B <= Steps; ++B)
			{
				const FVector Offset = T1 * (A * Step) + T2 * (B * Step);
				if (Offset.SizeSquared() > Reach * Reach)
				{
					continue;
				}
				const FVector SampleDir = (Dir * Settings.RadiusCm + Offset).GetSafeNormal();
				int32 Face;
				double U;
				double V;
				PlanetTerrain::DirectionToFace(SampleDir, Face, U, V);
				const FQuadTileId Id{ uint8(Face), uint8(CollisionDepth),
					FMath::Clamp(FMath::FloorToInt32((U + 1.0) * 0.5 * TilesPerSide), 0, TilesPerSide - 1),
					FMath::Clamp(FMath::FloorToInt32((V + 1.0) * 0.5 * TilesPerSide), 0, TilesPerSide - 1) };
				if (Wanted.Contains(Id.Key()))
				{
					continue;
				}
				FVector Center;
				double BoundsRadius;
				PlanetTerrain::EstimateTileBounds(Settings, Id, Center, BoundsRadius);
				if (FVector::Dist(ShipLocal, Center) - BoundsRadius <= RadiusCm)
				{
					Wanted.Add(Id.Key());
					WantedIds.Add(Id.Key(), Id);
				}
			}
		}
	}

	// Drop tiles well outside the radius (with margin, so they don't churn at the boundary).
	TArray<uint64> ToRemove;
	for (const TPair<uint64, FTile>& Pair : CollisionTiles)
	{
		if (Wanted.Contains(Pair.Key))
		{
			continue;
		}
		FVector Center;
		double BoundsRadius;
		PlanetTerrain::EstimateTileBounds(Settings, Pair.Value.Id, Center, BoundsRadius);
		if (FVector::Dist(ShipLocal, Center) - BoundsRadius > RadiusCm * 1.5)
		{
			ToRemove.Add(Pair.Key);
		}
		else
		{
			Wanted.Add(Pair.Key);
		}
	}
	for (uint64 Key : ToRemove)
	{
		CollisionTiles[Key].Mesh->DestroyComponent();
		CollisionTiles.Remove(Key);
	}

	for (const TPair<uint64, FQuadTileId>& Pair : WantedIds)
	{
		if (!CollisionTiles.Contains(Pair.Key) && !BuildingCollision.Contains(Pair.Key))
		{
			LaunchBuild(Pair.Value, true);
		}
	}
	CollisionWanted = MoveTemp(Wanted);
}

// -------------------------------------------------------------------------------------------
// Building and uploading tiles
// -------------------------------------------------------------------------------------------

void AQuadSpherePlanet::LaunchBuild(const FQuadTileId& Id, bool bCollision)
{
	const FPlanetTerrainSettings BuildSettings = Settings;
	const int32 Quads = bCollision ? CollisionTileQuads : TileQuads;
	// Deep enough to cover the worst crack between neighbours one or two levels apart.
	const double SkirtDepth = PlanetTerrain::TileSizeCm(Settings, Id.Depth) * 0.05 + 100.0;

	FBuild& Build = Builds.AddDefaulted_GetRef();
	Build.Id = Id;
	Build.bCollision = bCollision;
	Build.Result = Async(EAsyncExecution::ThreadPool, [BuildSettings, Id, Quads, bCollision, SkirtDepth]()
	{
		return PlanetTerrain::BuildTile(BuildSettings, Id, Quads, !bCollision, SkirtDepth);
	});
	(bCollision ? BuildingCollision : BuildingRender).Add(Id.Key());
}

void AQuadSpherePlanet::CollectFinishedBuilds()
{
	const double Deadline = FPlatformTime::Seconds() + UploadBudgetMs / 1000.0;
	int32 Uploads = 0;
	for (int32 Index = Builds.Num() - 1;
		Index >= 0 && Uploads < MaxTileUploadsPerFrame && (Uploads == 0 || FPlatformTime::Seconds() < Deadline);
		--Index)
	{
		FBuild& Build = Builds[Index];
		if (!Build.Result.IsReady())
		{
			continue;
		}

		const TSharedPtr<FTerrainTileMesh> Mesh = Build.Result.Get();
		const uint64 Key = Build.Id.Key();
		if (Build.bCollision)
		{
			BuildingCollision.Remove(Key);
			if (CollisionWanted.Contains(Key) && !CollisionTiles.Contains(Key))
			{
				FTile& Tile = CollisionTiles.Add(Key);
				Tile.Id = Build.Id;
				Tile.Mesh = CreateTileComponent(*Mesh, true);
				++Uploads;
			}
		}
		else
		{
			BuildingRender.Remove(Key);
			if (!Tiles.Contains(Key))
			{
				FTile& Tile = Tiles.Add(Key);
				Tile.Id = Build.Id;
				Tile.Mesh = CreateTileComponent(*Mesh, false);
				Tile.LastUsedSeconds = GetWorld()->GetTimeSeconds();
				for (FQuadTileId Ancestor = Build.Id; Ancestor.Depth > 0;)
				{
					Ancestor = Ancestor.Parent();
					++ReadyDescendants.FindOrAdd(Ancestor.Key());
				}
				++Stats.TilesBuilt;
				++Uploads;
				bTilesChangedSinceLod = true;
			}
		}
		Builds.RemoveAtSwap(Index, EAllowShrinking::No);
	}
}

UProceduralMeshComponent* AQuadSpherePlanet::CreateTileComponent(const FTerrainTileMesh& Mesh, bool bCollision)
{
	UProceduralMeshComponent* Component = NewObject<UProceduralMeshComponent>(this, NAME_None, RF_Transient);
	Component->SetupAttachment(TerrainRoot);
	// The tile's place on the planet lives here, in the double-precision transform...
	Component->SetRelativeLocation(Mesh.CenterLocal);
	Component->SetCanEverAffectNavigation(false);
	Component->bUseAsyncCooking = true;
	Component->SetVisibility(false);

	if (bCollision)
	{
		Component->bUseComplexAsSimpleCollision = true;
		Component->SetCollisionProfileName(UCollisionProfile::BlockAll_ProfileName);
		Component->SetHiddenInGame(true);
		Component->SetCastShadow(false);
	}
	else
	{
		Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	}

	Component->RegisterComponent();
	// ...while the vertices only hold offsets within the tile.
	Component->CreateMeshSection(0, Mesh.Vertices, Mesh.Triangles, Mesh.Normals, Mesh.UV0, Mesh.UV1, Mesh.UV2,
		TArray<FVector2D>(), TArray<FColor>(), Mesh.Tangents, bCollision);

	if (!bCollision)
	{
		Component->SetMaterial(0, TerrainMaterial);
		const int32 Depth = Mesh.Id.Depth;
		// Geomorph range: fully the parent's shape at the distance where this tile merges into
		// it, fully its own shape by MorphStartFraction of that. Root tiles have no parent.
		const double MorphEnd = Depth > 0 ? LodDistanceFactor * PlanetTerrain::TileSizeCm(Settings, Depth - 1) : 1.0e20;
		const double MorphStart = Depth > 0 ? MorphEnd * MorphStartFraction : 1.0e20 - 1.0;
		Component->SetCustomPrimitiveDataVector3(CPD_TileCenter, Mesh.CenterLocal);
		Component->SetCustomPrimitiveDataFloat(CPD_MorphStart, float(MorphStart));
		Component->SetCustomPrimitiveDataFloat(CPD_MorphEnd, float(MorphEnd));
		Component->SetCustomPrimitiveDataFloat(CPD_PlanetRadius, float(Settings.RadiusCm));
		Component->SetCustomPrimitiveDataFloat(CPD_Depth, float(Depth));
		ApplyDebugTint(Component, Depth);
	}
	return Component;
}

void AQuadSpherePlanet::ApplyDebugTint(UProceduralMeshComponent* Mesh, int32 /*Depth*/) const
{
	Mesh->SetCustomPrimitiveDataFloat(CPD_DebugTint, CVarTerrainDebugLOD.GetValueOnGameThread() != 0 ? 1.f : 0.f);
}

void AQuadSpherePlanet::DestroyTile(uint64 Key)
{
	FTile Tile;
	if (!Tiles.RemoveAndCopyValue(Key, Tile))
	{
		return;
	}
	Tile.Mesh->DestroyComponent();
	for (FQuadTileId Ancestor = Tile.Id; Ancestor.Depth > 0;)
	{
		Ancestor = Ancestor.Parent();
		int32& Count = ReadyDescendants.FindChecked(Ancestor.Key());
		if (--Count == 0)
		{
			ReadyDescendants.Remove(Ancestor.Key());
		}
	}
}

// -------------------------------------------------------------------------------------------
// Queries
// -------------------------------------------------------------------------------------------

double AQuadSpherePlanet::GetTerrainHeightAt(const FVector& WorldLocation) const
{
	const FVector Local = GetActorTransform().InverseTransformPositionNoScale(WorldLocation);
	return PlanetTerrain::Height(Settings, Local.GetSafeNormal());
}

double AQuadSpherePlanet::GetSurfaceDistance(const FVector& Location) const
{
	const FVector Local = GetActorTransform().InverseTransformPositionNoScale(Location);
	return Local.Size() - (Settings.RadiusCm + PlanetTerrain::Height(Settings, Local.GetSafeNormal()));
}
