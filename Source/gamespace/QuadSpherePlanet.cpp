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
#include "SpaceshipPawn.h"

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

	/** The bounds cache is dropped past this many nodes; a long flight would otherwise grow it forever. */
	constexpr int32 MaxCachedBounds = 400000;

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

	double SmoothStep01(double X)
	{
		const double T = FMath::Clamp(X, 0.0, 1.0);
		return T * T * (3.0 - 2.0 * T);
	}
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

	RefreshDerivedSettings();
}

FPlanetTerrainSettings AQuadSpherePlanet::MakeSettings() const
{
	FPlanetTerrainSettings Result;
	Result.RadiusCm = RadiusKm * 100000.0;
	Result.AmplitudeCm = TerrainAmplitudeM * 100.0;
	Result.BaseWavelengthCm = BaseWavelengthM * 100.0;
	Result.Octaves = NoiseOctaves;
	Result.Lacunarity = NoiseLacunarity;
	Result.Gain = NoiseGain;
	Result.Seed = uint32(NoiseSeed);
	return Result;
}

void AQuadSpherePlanet::RefreshDerivedSettings()
{
	const FPlanetTerrainSettings NewSettings = MakeSettings();
	const bool bShapeChanged = NewSettings.RadiusCm != Settings.RadiusCm || NewSettings.AmplitudeCm != Settings.AmplitudeCm
		|| NewSettings.BaseWavelengthCm != Settings.BaseWavelengthCm || NewSettings.Octaves != Settings.Octaves
		|| NewSettings.Lacunarity != Settings.Lacunarity || NewSettings.Gain != Settings.Gain || NewSettings.Seed != Settings.Seed;
	Settings = NewSettings;
	if (bShapeChanged)
	{
		BoundsCache.Reset();
	}

	TileQuads = FMath::Max(4, TileQuads & ~1);
	CollisionTileQuads = FMath::Max(2, CollisionTileQuads);
	const double RootSize = PlanetTerrain::TileSizeCm(Settings, 0);
	MaxDepth = FMath::Clamp(FMath::CeilToInt32(FMath::Log2(RootSize / (LeafTileSizeM * 100.0))), 0, 24);
	Stats.MaxDepth = MaxDepth;
}

void AQuadSpherePlanet::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	RefreshDerivedSettings();

	const double SafetyRadiusCm = Settings.RadiusCm - Settings.MaxHeightCm() - 100.0;
	Body->SetRelativeScale3D(FVector(FMath::Max(SafetyRadiusCm, 100.0) / SafetySphereMeshRadiusCm));
}

void AQuadSpherePlanet::PostLoad()
{
	Super::PostLoad();
	// Settings are not saved; rebuild them from the loaded properties so queries work in the
	// editor and in commandlets, not only after BeginPlay.
	RefreshDerivedSettings();
}

#if WITH_EDITOR
void AQuadSpherePlanet::PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent)
{
	Super::PostEditChangeProperty(PropertyChangedEvent);
	RefreshDerivedSettings();
}
#endif

void AQuadSpherePlanet::BeginPlay()
{
	Super::BeginPlay();
	RefreshDerivedSettings();

	// The six root tiles are built synchronously, so there is always something to fall back on.
	for (uint8 Face = 0; Face < 6; ++Face)
	{
		const FQuadTileId Root{ Face, 0, 0, 0 };
		const TSharedPtr<FTerrainTileMesh> Mesh = PlanetTerrain::BuildTile(Settings, Root, TileQuads, true, SkirtDepthCm(0));
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

double AQuadSpherePlanet::SkirtDepthCm(int32 Depth) const
{
	// Deep enough to cover the worst crack between neighbours one or two levels apart; with
	// kilometre-high relief the parent's chord can sit far from the child's surface.
	return PlanetTerrain::TileSizeCm(Settings, Depth) * 0.08 + 100.0;
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
			const double Altitude = FMath::Max(0.0, CameraLocal.Size() - Settings.RadiusCm - PlanetTerrain::Height(Settings, CameraLocal.GetSafeNormal()));
			const double MoveThreshold = FMath::Max(50.0, LodUpdateMoveFraction * Altitude);
			if (bTilesChangedSinceLod || FVector::DistSquared(CameraLocal, LastLodCameraLocal) > FMath::Square(MoveThreshold))
			{
				bTilesChangedSinceLod = false;
				LastLodCameraLocal = CameraLocal;
				UpdateRenderLod(CameraLocal, GetWorld()->GetTimeSeconds());
			}
		}
	}

	if (const APawn* Pawn = UGameplayStatics::GetPlayerPawn(this, 0))
	{
		const ASpaceshipPawn* Ship = Cast<ASpaceshipPawn>(Pawn);
		const double Speed = Ship ? Ship->GetLinearVelocity().Size() : Pawn->GetVelocity().Size();
		UpdateCollisionTiles(ToWorld.InverseTransformPositionNoScale(Pawn->GetActorLocation()), Speed);
	}

	const int32 DebugTint = CVarTerrainDebugLOD.GetValueOnGameThread();
	if (DebugTint != AppliedDebugTint)
	{
		AppliedDebugTint = DebugTint;
		for (TPair<uint64, FTile>& Pair : Tiles)
		{
			ApplyDebugTint(Pair.Value.Mesh);
		}
	}

	if (BoundsCache.Num() > MaxCachedBounds)
	{
		BoundsCache.Reset();
	}

	Stats.CachedTiles = Tiles.Num();
	Stats.PendingBuilds = Builds.Num();
	Stats.CollisionTiles = CollisionTiles.Num();
	Stats.CollisionDepth = CollisionDepth;
	Stats.TickMs = (FPlatformTime::Seconds() - TickStart) * 1000.0;
}

const AQuadSpherePlanet::FTileBounds& AQuadSpherePlanet::GetTileBounds(const FQuadTileId& Id) const
{
	const uint64 Key = Id.Key();
	if (const FTileBounds* Cached = BoundsCache.Find(Key))
	{
		return *Cached;
	}
	FTileBounds Bounds;
	PlanetTerrain::EstimateTileBounds(Settings, Id, Bounds.Center, Bounds.Radius);
	return BoundsCache.Add(Key, Bounds);
}

bool AQuadSpherePlanet::IsBelowHorizon(const FVector& CameraLocal, const FTileBounds& Bounds) const
{
	// The occluder is the sphere under the lowest possible terrain: whatever lies behind it is
	// hidden for sure. A point P is out of sight when it is farther from the camera than the two
	// horizon distances together - the camera's and P's own - since the line of sight then has to
	// dip into the occluder. For the bounds, take their nearest point and their highest possible
	// radius, which keeps the test conservative.
	const double OccluderRadius = Settings.RadiusCm - Settings.MaxHeightCm();
	const double CameraDistance = CameraLocal.Size();
	if (OccluderRadius <= 0.0 || CameraDistance <= OccluderRadius)
	{
		return false;
	}
	const double CameraHorizon = FMath::Sqrt(CameraDistance * CameraDistance - OccluderRadius * OccluderRadius);
	const double TopRadius = FMath::Min(Bounds.Center.Size() + Bounds.Radius, Settings.RadiusCm + Settings.MaxHeightCm());
	const double TopHorizon = FMath::Sqrt(FMath::Max(0.0, TopRadius * TopRadius - OccluderRadius * OccluderRadius));
	return FVector::Dist(CameraLocal, Bounds.Center) - Bounds.Radius > CameraHorizon + TopHorizon;
}

void AQuadSpherePlanet::SelectLodTree(const FVector& CameraLocal, const TSet<uint64>& PreviousSplit, TSet<uint64>& OutSplit,
	TArray<TPair<double, FQuadTileId>>& OutLeaves, int32& OutHorizonCulled) const
{
	OutHorizonCulled = 0;
	TArray<FQuadTileId> Stack;
	for (uint8 Face = 0; Face < 6; ++Face)
	{
		Stack.Add({ Face, 0, 0, 0 });
	}
	while (Stack.Num() > 0)
	{
		const FQuadTileId Id = Stack.Pop(EAllowShrinking::No);
		const FTileBounds& Bounds = GetTileBounds(Id);
		const double Distance = FMath::Max(0.0, FVector::Dist(CameraLocal, Bounds.Center) - Bounds.Radius);
		const double Hysteresis = PreviousSplit.Contains(Id.Key()) ? MergeHysteresis : 1.0;
		const double SplitDistance = LodDistanceFactor * PlanetTerrain::TileSizeCm(Settings, Id.Depth) * Hysteresis;

		bool bSplit = Id.Depth < MaxDepth && Distance < SplitDistance;
		if (bSplit && bHorizonCulling && IsBelowHorizon(CameraLocal, Bounds))
		{
			bSplit = false;
			++OutHorizonCulled;
		}

		if (bSplit)
		{
			OutSplit.Add(Id.Key());
			for (int32 Child = 0; Child < 4; ++Child)
			{
				Stack.Add(Id.Child(Child));
			}
		}
		else
		{
			OutLeaves.Add({ Distance, Id });
		}
	}
}

int32 AQuadSpherePlanet::CountLodTilesFrom(const FVector& CameraWorldLocation)
{
	RefreshDerivedSettings();
	const FVector CameraLocal = GetActorTransform().InverseTransformPositionNoScale(CameraWorldLocation);
	TSet<uint64> Split;
	TArray<TPair<double, FQuadTileId>> Leaves;
	int32 Culled = 0;
	SelectLodTree(CameraLocal, TSet<uint64>(), Split, Leaves, Culled);
	return Leaves.Num();
}

void AQuadSpherePlanet::UpdateRenderLod(const FVector& CameraLocal, double NowSeconds)
{
	const double StartSeconds = FPlatformTime::Seconds();

	// 1) Which nodes should be split, and which leaves we want, from the camera alone.
	TSet<uint64> Split;
	TArray<TPair<double, FQuadTileId>> WantedLeaves;
	SelectLodTree(CameraLocal, SplitLastFrame, Split, WantedLeaves, Stats.HorizonCulled);

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

void AQuadSpherePlanet::UpdateCollisionTiles(const FVector& ShipLocal, double ShipSpeedCmS)
{
	// Radius: what the ship covers in the look-ahead time. It grows at once when the ship speeds
	// up, and shrinks gradually, so easing off the throttle does not drop tiles right in front.
	const double TargetRadius = FMath::Clamp(CollisionMinRadiusM * 100.0 + ShipSpeedCmS * CollisionLookaheadSeconds,
		CollisionMinRadiusM * 100.0, FMath::Max(CollisionMinRadiusM, CollisionMaxRadiusM) * 100.0);
	const double DeltaSeconds = GetWorld()->GetDeltaSeconds();
	Stats.CollisionRadiusCm = TargetRadius >= Stats.CollisionRadiusCm
		? TargetRadius
		: FMath::Lerp(TargetRadius, Stats.CollisionRadiusCm, FMath::Exp(-0.5 * DeltaSeconds));
	const double RadiusCm = Stats.CollisionRadiusCm;

	// Tile size follows the radius, with hysteresis: the depth only changes once the ideal size
	// is ~1.7x off, so a ship cruising at one speed never flips between two tile sizes.
	const double RootSize = PlanetTerrain::TileSizeCm(Settings, 0);
	const double IdealSize = FMath::Max(CollisionMinTileSizeM * 100.0, RadiusCm / CollisionTilesPerRadius);
	const double IdealDepth = FMath::Clamp(FMath::Log2(RootSize / IdealSize), 0.0, double(MaxDepth));
	if (CollisionDepth < 0 || FMath::Abs(IdealDepth - CollisionDepth) > 0.75)
	{
		CollisionDepth = FMath::Clamp(FMath::RoundToInt32(IdealDepth), 0, MaxDepth);
	}

	const double TileSize = PlanetTerrain::TileSizeCm(Settings, CollisionDepth);

	TSet<uint64> Wanted;
	TMap<uint64, FQuadTileId> WantedIds;
	const FVector Dir = ShipLocal.GetSafeNormal();
	const double AltitudeAboveTerrain = ShipLocal.Size() - Settings.RadiusCm - PlanetTerrain::Height(Settings, Dir);
	if (AltitudeAboveTerrain < RadiusCm + TileSize)
	{
		// Sample the surface around the point under the ship; this crosses cube-face edges
		// naturally, which walking tile indices on one face would not.
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
				const FQuadTileId Id = CollisionTileAt((Dir * Settings.RadiusCm + Offset).GetSafeNormal());
				if (Wanted.Contains(Id.Key()))
				{
					continue;
				}
				const FTileBounds& Bounds = GetTileBounds(Id);
				if (FVector::Dist(ShipLocal, Bounds.Center) - Bounds.Radius <= RadiusCm)
				{
					Wanted.Add(Id.Key());
					WantedIds.Add(Id.Key(), Id);
				}
			}
		}
	}

	if (AltitudeAboveTerrain < CollisionWarmupAltitudeM * 100.0)
	{
		WarmUpCollisionBelow(ShipLocal, Wanted);
	}

	bool bAllWantedReady = true;
	for (const TPair<uint64, FQuadTileId>& Pair : WantedIds)
	{
		if (!CollisionTiles.Contains(Pair.Key))
		{
			bAllWantedReady = false;
			break;
		}
	}

	// Tiles of the current size are dropped well outside the radius (with margin, so they don't
	// churn at the boundary). Tiles of a previous size stay until the new set is complete, so a
	// size change never leaves the ship without collision for the frames the builds take.
	TArray<uint64> ToRemove;
	for (const TPair<uint64, FTile>& Pair : CollisionTiles)
	{
		if (Wanted.Contains(Pair.Key))
		{
			continue;
		}
		bool bRemove;
		if (Pair.Value.Id.Depth != CollisionDepth)
		{
			bRemove = bAllWantedReady;
		}
		else
		{
			const FTileBounds& Bounds = GetTileBounds(Pair.Value.Id);
			bRemove = FVector::Dist(ShipLocal, Bounds.Center) - Bounds.Radius > RadiusCm * 1.5;
		}
		if (bRemove)
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

FQuadTileId AQuadSpherePlanet::CollisionTileAt(const FVector& LocalDirection) const
{
	const int32 TilesPerSide = 1 << CollisionDepth;
	int32 Face;
	double U;
	double V;
	PlanetTerrain::DirectionToFace(LocalDirection, Face, U, V);
	return { uint8(Face), uint8(CollisionDepth),
		FMath::Clamp(FMath::FloorToInt32((U + 1.0) * 0.5 * TilesPerSide), 0, TilesPerSide - 1),
		FMath::Clamp(FMath::FloorToInt32((V + 1.0) * 0.5 * TilesPerSide), 0, TilesPerSide - 1) };
}

void AQuadSpherePlanet::WarmUpCollisionBelow(const FVector& ShipLocal, TSet<uint64>& Wanted)
{
	// The point under the ship and four points around it: enough to cover the hull when it sits
	// near a tile edge or corner.
	const FVector Dir = ShipLocal.GetSafeNormal();
	const FVector T1 = FVector::CrossProduct(Dir, FMath::Abs(Dir.Z) < 0.9 ? FVector::UpVector : FVector::ForwardVector).GetSafeNormal();
	const FVector T2 = FVector::CrossProduct(Dir, T1);
	const double Reach = CollisionWarmupReachM * 100.0;
	const FVector Offsets[] = { FVector::ZeroVector, T1 * Reach, T1 * -Reach, T2 * Reach, T2 * -Reach };

	int32 Built = 0;
	for (const FVector& Offset : Offsets)
	{
		const FQuadTileId Id = CollisionTileAt((Dir * Settings.RadiusCm + Offset).GetSafeNormal());
		const uint64 Key = Id.Key();
		Wanted.Add(Key);
		if (CollisionTiles.Contains(Key) || Built >= MaxCollisionWarmupsPerFrame)
		{
			continue;
		}
		// An asynchronous build of the same tile may still be running; its result is dropped
		// when it arrives, because the tile already exists by then.
		const TSharedPtr<FTerrainTileMesh> Mesh = PlanetTerrain::BuildTile(Settings, Id, CollisionTileQuads, false, 0.0);
		FTile& Tile = CollisionTiles.Add(Key);
		Tile.Id = Id;
		Tile.Mesh = CreateTileComponent(*Mesh, true, true);
		++Built;
		++Stats.CollisionWarmups;
	}
}

float AQuadSpherePlanet::MeasureCollisionTileBuildMs(const FVector& WorldLocation)
{
	RefreshDerivedSettings();
	const int32 SavedDepth = CollisionDepth;
	const double RootSize = PlanetTerrain::TileSizeCm(Settings, 0);
	CollisionDepth = FMath::Clamp(FMath::RoundToInt32(FMath::Log2(RootSize / (CollisionMinTileSizeM * 100.0))), 0, MaxDepth);
	const FVector Local = GetActorTransform().InverseTransformPositionNoScale(WorldLocation);
	const FQuadTileId Id = CollisionTileAt(Local.GetSafeNormal());
	CollisionDepth = SavedDepth;

	const double Start = FPlatformTime::Seconds();
	const TSharedPtr<FTerrainTileMesh> Mesh = PlanetTerrain::BuildTile(Settings, Id, CollisionTileQuads, false, 0.0);
	return float((FPlatformTime::Seconds() - Start) * 1000.0);
}

// -------------------------------------------------------------------------------------------
// Building and uploading tiles
// -------------------------------------------------------------------------------------------

void AQuadSpherePlanet::LaunchBuild(const FQuadTileId& Id, bool bCollision)
{
	const FPlanetTerrainSettings BuildSettings = Settings;
	const int32 Quads = bCollision ? CollisionTileQuads : TileQuads;
	const double SkirtDepth = SkirtDepthCm(Id.Depth);

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

UProceduralMeshComponent* AQuadSpherePlanet::CreateTileComponent(const FTerrainTileMesh& Mesh, bool bCollision, bool bSynchronousCooking)
{
	UProceduralMeshComponent* Component = NewObject<UProceduralMeshComponent>(this, NAME_None, RF_Transient);
	Component->SetupAttachment(TerrainRoot);
	// The tile's place on the planet lives here, in the double-precision transform...
	Component->SetRelativeLocation(Mesh.CenterLocal);
	Component->SetCanEverAffectNavigation(false);
	// Async cooking keeps streaming smooth, but the tile has no collision until it finishes.
	Component->bUseAsyncCooking = !bSynchronousCooking;
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
		ApplyDebugTint(Component);
	}
	return Component;
}

void AQuadSpherePlanet::ApplyDebugTint(UProceduralMeshComponent* Mesh) const
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

bool AQuadSpherePlanet::GetSurfaceFrame(const FVector& Location, double FootprintRadiusCm, FVector& OutSurfacePoint, FVector& OutNormal) const
{
	const FTransform& ToWorld = GetActorTransform();
	const FVector Dir = ToWorld.InverseTransformPositionNoScale(Location).GetSafeNormal();
	if (Dir.IsNearlyZero())
	{
		return false;
	}
	const FVector T1 = FVector::CrossProduct(Dir, FMath::Abs(Dir.Z) < 0.9 ? FVector::UpVector : FVector::ForwardVector).GetSafeNormal();
	const FVector T2 = FVector::CrossProduct(Dir, T1);
	const double Radius = FMath::Max(FootprintRadiusCm, 10.0);
	auto SurfaceAt = [this, &Dir](const FVector& Offset)
	{
		return PlanetTerrain::SurfacePoint(Settings, (Dir * Settings.RadiusCm + Offset).GetSafeNormal());
	};

	// A plane through the footprint's four edge points: the average slope under the hull.
	const FVector AcrossT1 = SurfaceAt(T1 * Radius) - SurfaceAt(T1 * -Radius);
	const FVector AcrossT2 = SurfaceAt(T2 * Radius) - SurfaceAt(T2 * -Radius);
	FVector Normal = FVector::CrossProduct(AcrossT1, AcrossT2).GetSafeNormal();
	if ((Normal | Dir) < 0.0)
	{
		Normal = -Normal;
	}
	OutSurfacePoint = ToWorld.TransformPositionNoScale(PlanetTerrain::SurfacePoint(Settings, Dir));
	OutNormal = ToWorld.TransformVectorNoScale(Normal);
	return !OutNormal.IsNearlyZero();
}

bool AQuadSpherePlanet::SampleEnvironment(const FVector& Location, FCelestialEnvironment& Out) const
{
	const FVector Local = GetActorTransform().InverseTransformPositionNoScale(Location);
	const double DistanceFromCentre = FMath::Max(Local.Size(), 1.0);
	const FVector LocalUp = Local / DistanceFromCentre;

	Out.Up = GetActorTransform().TransformVectorNoScale(LocalUp);
	Out.AltitudeAboveSeaLevelCm = DistanceFromCentre - Settings.RadiusCm;
	Out.AltitudeAboveTerrainCm = Out.AltitudeAboveSeaLevelCm - PlanetTerrain::Height(Settings, LocalUp);

	const double Top = AtmosphereHeightKm * 100000.0;
	const double Altitude = Out.AltitudeAboveSeaLevelCm;

	// Exponential atmosphere, shifted so it reaches exactly zero at the top instead of trailing
	// off forever, and clamped to 1 below sea level (deep valleys).
	const double ScaleHeight = AtmosphereScaleHeightKm * 100000.0;
	const double TopFalloff = FMath::Exp(-Top / ScaleHeight);
	const double RawDensity = (FMath::Exp(-FMath::Max(Altitude, 0.0) / ScaleHeight) - TopFalloff) / (1.0 - TopFalloff);
	Out.AtmosphereDensity = float(Altitude >= Top ? 0.0 : FMath::Clamp(RawDensity, 0.0, 1.0));

	// Gravity: inverse square, faded in over the upper part of the atmosphere.
	const double FullBelow = Top * GravityFullBelowFraction;
	const double GravityFade = SmoothStep01((Top - Altitude) / FMath::Max(Top - FullBelow, 1.0));
	const double Ratio = Settings.RadiusCm / FMath::Max(DistanceFromCentre, Settings.RadiusCm * 0.5);
	Out.GravityCmS2 = SurfaceGravity * 100.0 * Ratio * Ratio * GravityFade;

	// The sky turns blue much faster than density grows: thin air already scatters visibly.
	const double Thin = 1.0 - double(Out.AtmosphereDensity);
	Out.SkyAmount = float(1.0 - Thin * Thin * Thin * Thin);
	Out.SkyZenithColor = SkyZenithColor;
	Out.SkyHorizonColor = SkyHorizonColor;
	Out.SkyBrightness = SkyBrightness;

	if (Altitude >= Top)
	{
		Out.Regime = EFlightRegime::Orbit;
	}
	else if (Out.AltitudeAboveTerrainCm < SurfaceRegimeAltitudeM * 100.0)
	{
		Out.Regime = EFlightRegime::Surface;
	}
	else
	{
		Out.Regime = EFlightRegime::Atmosphere;
	}
	return true;
}
