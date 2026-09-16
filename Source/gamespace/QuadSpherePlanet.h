// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "CelestialBody.h"
#include "PlanetTerrain.h"
#include "QuadSpherePlanet.generated.h"

class UMaterialInterface;
class UProceduralMeshComponent;

/** Counters for the debug HUD and tests. */
struct FQuadSpherePlanetStats
{
	int32 VisibleTiles = 0;
	int32 CachedTiles = 0;
	int32 PendingBuilds = 0;
	int32 CollisionTiles = 0;
	int32 MaxVisibleDepth = 0;
	int32 MaxDepth = 0;
	int32 TilesBuilt = 0;
	/** Nodes kept coarse this selection because they were below the horizon. */
	int32 HorizonCulled = 0;
	double SelectionMs = 0.0;
	/** Whole planet Tick on the game thread, including uploads. */
	double TickMs = 0.0;
	/** Creating tile components this frame. */
	double UploadMs = 0.0;
	/** Current speed-scaled collision radius and collision tile depth. */
	double CollisionRadiusCm = 0.0;
	int32 CollisionDepth = 0;
	/** Collision tiles built synchronously because the ship was about to touch down on them. */
	int32 CollisionWarmups = 0;
};

/**
 * A planet made of a quad-sphere: the six faces of a cube projected onto a sphere, each face a
 * quadtree whose tiles split as the camera approaches. It also provides the planet's atmosphere
 * and gravity through SampleEnvironment.
 *
 * LOD
 * - A tile splits when the camera is within LodDistanceFactor x its size (measured to its bounds)
 *   and merges back with a little hysteresis, so a tile does not flicker at the threshold.
 * - Tile bounds use the real height at the tile centre plus how much the terrain can vary within
 *   a tile of that size - not the planet-wide maximum height, which on a mountainous planet would
 *   make every small tile look near and multiply the tile count.
 * - Tiles hidden below the horizon are not split.
 * - Parents stay visible until all four children are built, and children until the parent is,
 *   so there are never holes while tiles stream in.
 * - No popping: each vertex carries the offset to where its parent would put it, and the material
 *   blends towards it with distance (geomorphing). Skirts under tile edges hide cracks.
 * - Tiles are built on worker threads; component uploads are capped per frame by count and time.
 *
 * Precision: every tile component sits at its tile centre, and its vertices are relative to that
 * centre, so single-precision mesh data only holds tile-sized values. The height field is double
 * precision throughout (PlanetTerrain::GradientNoise3D).
 *
 * Collision is separate from rendering: a few invisible collision tiles around the player ship.
 * Their radius grows with ship speed (so fast descents never outrun them) and their size grows
 * with the radius (so their count - and the cost of an origin rebase, which teleports every
 * physics body - stays roughly constant). A hidden sphere just under the lowest possible terrain
 * (the Body component) catches anything that still gets through.
 *
 * Console: space.TerrainDebugLOD 1 tints tiles by depth; space.TerrainFreezeLOD 1 stops LOD
 * updates so the tiles can be inspected from elsewhere.
 */
UCLASS()
class GAMESPACE_API AQuadSpherePlanet : public ACelestialBody
{
	GENERATED_BODY()

public:
	AQuadSpherePlanet();

	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void PostLoad() override;
#if WITH_EDITOR
	virtual void PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent) override;
#endif
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void Tick(float DeltaSeconds) override;

	virtual double GetSurfaceDistance(const FVector& Location) const override;
	virtual bool SampleEnvironment(const FVector& Location, FCelestialEnvironment& OutEnvironment) const override;
	virtual bool GetSurfaceFrame(const FVector& Location, double FootprintRadiusCm, FVector& OutSurfacePoint, FVector& OutNormal) const override;

	/** Milliseconds to build the smallest collision tile under a location on this thread. For tests. */
	UFUNCTION(BlueprintCallable, Category = "Planet|Debug")
	float MeasureCollisionTileBuildMs(const FVector& WorldLocation);

	/** Terrain height above the base radius, in cm, straight below a world location. */
	UFUNCTION(BlueprintPure, Category = "Planet")
	double GetTerrainHeightAt(const FVector& WorldLocation) const;

	/** Upper bound of terrain height above or below the base radius, in cm. */
	UFUNCTION(BlueprintPure, Category = "Planet")
	double GetMaxTerrainHeightCm() const { return Settings.MaxHeightCm(); }

	/**
	 * How many leaf tiles the LOD would want for a camera at this world location, selecting from
	 * scratch. Runs the same selection as the game without building anything: for tests and
	 * tuning TileQuads / LodDistanceFactor.
	 */
	UFUNCTION(BlueprintCallable, Category = "Planet|Debug")
	int32 CountLodTilesFrom(const FVector& CameraWorldLocation);

	const FQuadSpherePlanetStats& GetTerrainStats() const { return Stats; }

	// Stats for Blueprint / Python (tests and debugging).
	UFUNCTION(BlueprintPure, Category = "Planet|Debug")
	int32 GetVisibleTileCount() const { return Stats.VisibleTiles; }
	UFUNCTION(BlueprintPure, Category = "Planet|Debug")
	int32 GetBuiltTileCount() const { return Stats.CachedTiles; }
	UFUNCTION(BlueprintPure, Category = "Planet|Debug")
	int32 GetPendingBuildCount() const { return Stats.PendingBuilds; }
	UFUNCTION(BlueprintPure, Category = "Planet|Debug")
	int32 GetCollisionTileCount() const { return Stats.CollisionTiles; }
	UFUNCTION(BlueprintPure, Category = "Planet|Debug")
	int32 GetMaxVisibleDepth() const { return Stats.MaxVisibleDepth; }
	UFUNCTION(BlueprintPure, Category = "Planet|Debug")
	int32 GetMaxLodDepth() const { return Stats.MaxDepth; }
	UFUNCTION(BlueprintPure, Category = "Planet|Debug")
	float GetLodSelectionMs() const { return float(Stats.SelectionMs); }
	UFUNCTION(BlueprintPure, Category = "Planet|Debug")
	float GetTickMs() const { return float(Stats.TickMs); }
	UFUNCTION(BlueprintPure, Category = "Planet|Debug")
	float GetUploadMs() const { return float(Stats.UploadMs); }
	UFUNCTION(BlueprintPure, Category = "Planet|Debug")
	float GetCollisionRadiusM() const { return float(Stats.CollisionRadiusCm / 100.0); }
	UFUNCTION(BlueprintPure, Category = "Planet|Debug")
	int32 GetCollisionWarmupCount() const { return Stats.CollisionWarmups; }

protected:
	/** Planet centre. Tiles and the Body safety sphere hang off this, unscaled. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Planet")
	TObjectPtr<USceneComponent> TerrainRoot;

	// --- Shape -------------------------------------------------------------------------------

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Shape", meta = (ClampMin = "0.05", Units = "km"))
	float RadiusKm = 25.f;

	/**
	 * Height of the largest terrain features; each further octave adds NoiseGain times less.
	 * 800 m with gain 0.5 gives peaks and valleys up to about +/-1.6 km on a 25 km planet.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Shape", meta = (ClampMin = "0.0", Units = "m"))
	float TerrainAmplitudeM = 800.f;

	/** Size of the largest terrain features along the surface. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Shape", meta = (ClampMin = "1.0", Units = "m"))
	float BaseWavelengthM = 8000.f;

	/** Noise octaves; each divides the feature size by NoiseLacunarity. 12 reaches ~4 m features. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Shape", meta = (ClampMin = "1", ClampMax = "20"))
	int32 NoiseOctaves = 12;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Shape", meta = (ClampMin = "1.1", ClampMax = "4.0"))
	float NoiseLacunarity = 2.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Shape", meta = (ClampMin = "0.1", ClampMax = "0.9"))
	float NoiseGain = 0.5f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Shape")
	int32 NoiseSeed = 1;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Shape")
	TObjectPtr<UMaterialInterface> TerrainMaterial;

	// --- LOD -----------------------------------------------------------------------------------

	/**
	 * Cells per tile edge. Must be even (geomorphing pairs up vertices). Detail on screen depends
	 * on TileQuads x LodDistanceFactor; for the same detail, more cells and a lower factor means
	 * fewer, bigger tiles - fewer components, which is what ProceduralMeshComponent pays for.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|LOD", meta = (ClampMin = "4", ClampMax = "64"))
	int32 TileQuads = 48;

	/** The finest tiles are about this big; sets the quadtree depth. 16 m / 48 cells = 33 cm, 12 vertices across the smallest noise feature. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|LOD", meta = (ClampMin = "0.5", Units = "m"))
	float LeafTileSizeM = 16.f;

	/** A tile splits when the camera is closer than this many tile sizes. Higher: sharper, more tiles. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|LOD", meta = (ClampMin = "1.0", ClampMax = "10.0"))
	float LodDistanceFactor = 1.5f;

	/** Merge only this much farther out than the split distance, so tiles do not flicker. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|LOD", meta = (ClampMin = "1.0", ClampMax = "2.0"))
	float MergeHysteresis = 1.15f;

	/** Geomorphing starts at this fraction of a tile's merge distance and completes at it. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|LOD", meta = (ClampMin = "0.1", ClampMax = "0.95"))
	float MorphStartFraction = 0.6f;

	/** Do not split tiles that are hidden behind the planet's curvature. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|LOD")
	bool bHorizonCulling = true;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|LOD", meta = (ClampMin = "1"))
	int32 MaxConcurrentBuilds = 8;

	/** Hard cap on component creations per frame; each costs a render state upload. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|LOD", meta = (ClampMin = "1"))
	int32 MaxTileUploadsPerFrame = 12;

	/** Game-thread time per frame for creating tile components; stops early once spent. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|LOD", meta = (ClampMin = "0.1", Units = "ms"))
	float UploadBudgetMs = 2.f;

	/**
	 * Built tiles kept around (visible or not) before the least recently used are freed. Each
	 * 48-cell tile holds ~2,600 vertices in the component, so this is also a memory budget.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|LOD", meta = (ClampMin = "64"))
	int32 TileCacheLimit = 1200;

	/** Tiles freed per frame at most, so crossing the cache limit never frees hundreds at once. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|LOD", meta = (ClampMin = "1"))
	int32 MaxEvictionsPerFrame = 24;

	/**
	 * LOD selection is skipped while the camera has moved less than this fraction of its height
	 * above the surface (and no tile finished building). Nothing changes that fast up close.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|LOD", meta = (ClampMin = "0.0", ClampMax = "0.5"))
	float LodUpdateMoveFraction = 0.02f;

	// --- Collision -----------------------------------------------------------------------------

	/** Collision radius around a slow or stationary ship. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Collision", meta = (ClampMin = "10.0", Units = "m"))
	float CollisionMinRadiusM = 60.f;

	/** The radius also reaches this far ahead in time at the ship's current speed. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Collision", meta = (ClampMin = "0.1", Units = "s"))
	float CollisionLookaheadSeconds = 2.5f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Collision", meta = (ClampMin = "10.0", Units = "m"))
	float CollisionMaxRadiusM = 2000.f;

	/** Collision tiles are never smaller than this. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Collision", meta = (ClampMin = "4.0", Units = "m"))
	float CollisionMinTileSizeM = 64.f;

	/**
	 * Collision tile size is the radius divided by this, so a bigger radius uses bigger tiles and
	 * the tile count stays around 25-50 whatever the speed. Higher: finer collision, more bodies.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Collision", meta = (ClampMin = "1.0", ClampMax = "8.0"))
	float CollisionTilesPerRadius = 2.f;

	/** Cells per collision tile edge. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Collision", meta = (ClampMin = "2", ClampMax = "64"))
	int32 CollisionTileQuads = 32;

	/**
	 * Below this height above the terrain, the collision tiles right under the ship (within
	 * CollisionWarmupReachM) are built on the game thread with synchronous physics cooking if they
	 * are still missing. Asynchronous builds and cooking can leave a tile without collision for a
	 * few frames, which is exactly when a slowly landing ship would sink into it.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Collision", meta = (ClampMin = "0.0", Units = "m"))
	float CollisionWarmupAltitudeM = 150.f;

	/** How far around the point under the ship the warm-up looks, so tile edges are covered. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Collision", meta = (ClampMin = "0.0", Units = "m"))
	float CollisionWarmupReachM = 15.f;

	/** Synchronous warm-up builds per frame at most; each costs a few milliseconds. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Collision", meta = (ClampMin = "1"))
	int32 MaxCollisionWarmupsPerFrame = 2;

	// --- Atmosphere and gravity ----------------------------------------------------------------

	/** Top of the atmosphere above sea level. Above it: no drag, no gravity, black sky. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Atmosphere", meta = (ClampMin = "0.1", Units = "km"))
	float AtmosphereHeightKm = 12.f;

	/** Density falls by e over this height (exponential atmosphere), reaching 0 at the top. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Atmosphere", meta = (ClampMin = "0.1", Units = "km"))
	float AtmosphereScaleHeightKm = 3.f;

	/** Gravity at sea level, m/s^2; falls off with distance squared. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Atmosphere", meta = (ClampMin = "0.0"))
	float SurfaceGravity = 6.f;

	/**
	 * Gravity fades in from zero at the top of the atmosphere to full strength at this fraction of
	 * its height, so leaving orbit does not feel like a switch.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Atmosphere", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float GravityFullBelowFraction = 0.4f;

	/** Below this height above the terrain the regime reads SURFACE. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Atmosphere", meta = (ClampMin = "0.0", Units = "m"))
	float SurfaceRegimeAltitudeM = 500.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Atmosphere")
	FLinearColor SkyZenithColor = FLinearColor(0.16f, 0.32f, 0.62f);

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Atmosphere")
	FLinearColor SkyHorizonColor = FLinearColor(0.62f, 0.70f, 0.80f);

	/** Emissive multiplier for the sky colours; ~6 reads as daylight at the fixed EV100 3 exposure. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Atmosphere", meta = (ClampMin = "0.0"))
	float SkyBrightness = 6.f;

private:
	struct FTile
	{
		FQuadTileId Id;
		UProceduralMeshComponent* Mesh = nullptr;
		bool bVisible = false;
		double LastUsedSeconds = 0.0;
	};

	struct FBuild
	{
		FQuadTileId Id;
		bool bCollision = false;
		TFuture<TSharedPtr<FTerrainTileMesh>> Result;
	};

	struct FTileBounds
	{
		FVector Center;
		double Radius = 0.0;
	};

	FPlanetTerrainSettings MakeSettings() const;
	void RefreshDerivedSettings();

	const FTileBounds& GetTileBounds(const FQuadTileId& Id) const;
	bool IsBelowHorizon(const FVector& CameraLocal, const FTileBounds& Bounds) const;
	/** The desired quadtree for a camera: nodes to split, and leaves with their distances. */
	void SelectLodTree(const FVector& CameraLocal, const TSet<uint64>& PreviousSplit, TSet<uint64>& OutSplit, TArray<TPair<double, FQuadTileId>>& OutLeaves, int32& OutHorizonCulled) const;

	void UpdateRenderLod(const FVector& CameraLocal, double NowSeconds);
	void UpdateCollisionTiles(const FVector& ShipLocal, double ShipSpeedCmS);
	void LaunchBuild(const FQuadTileId& Id, bool bCollision);
	void CollectFinishedBuilds();
	UProceduralMeshComponent* CreateTileComponent(const FTerrainTileMesh& Mesh, bool bCollision, bool bSynchronousCooking = false);
	FQuadTileId CollisionTileAt(const FVector& LocalDirection) const;
	void WarmUpCollisionBelow(const FVector& ShipLocal, TSet<uint64>& Wanted);
	void DestroyTile(uint64 Key);
	void ApplyDebugTint(UProceduralMeshComponent* Mesh) const;
	double SkirtDepthCm(int32 Depth) const;

	bool IsReady(const FQuadTileId& Id) const { return Tiles.Contains(Id.Key()); }
	bool CanRender(const FQuadTileId& Id, TMap<uint64, bool>& Memo) const;
	bool AllChildrenCanRender(const FQuadTileId& Id, TMap<uint64, bool>& Memo) const;
	void ChooseVisible(const FQuadTileId& Id, const TSet<uint64>& SplitNodes, TMap<uint64, bool>& Memo, TSet<uint64>& OutVisible) const;

	FPlanetTerrainSettings Settings;
	int32 MaxDepth = 0;
	int32 CollisionDepth = -1;

	/** Per-node LOD bounds; each needs a height sample, so they are computed once. */
	mutable TMap<uint64, FTileBounds> BoundsCache;

	TMap<uint64, FTile> Tiles;
	/** For every ancestor of a built tile, how many built descendants it has. */
	TMap<uint64, int32> ReadyDescendants;
	TSet<uint64> SplitLastFrame;

	TMap<uint64, FTile> CollisionTiles;
	TSet<uint64> CollisionWanted;

	TArray<FBuild> Builds;
	TSet<uint64> BuildingRender;
	TSet<uint64> BuildingCollision;

	int32 AppliedDebugTint = -1;

	/** Camera position at the last LOD selection, and whether tiles changed since. */
	FVector LastLodCameraLocal = FVector(TNumericLimits<double>::Max());
	bool bTilesChangedSinceLod = true;

	FQuadSpherePlanetStats Stats;
};
