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
	double SelectionMs = 0.0;
	/** Whole planet Tick on the game thread, including uploads. */
	double TickMs = 0.0;
	/** Creating tile components this frame. */
	double UploadMs = 0.0;
};

/**
 * A planet made of a quad-sphere: the six faces of a cube projected onto a sphere, each face a
 * quadtree whose tiles split as the camera approaches.
 *
 * LOD
 * - A tile splits when the camera is within LodDistanceFactor x its size (measured to its bounds)
 *   and merges back with a little hysteresis, so a tile does not flicker at the threshold.
 * - Parents stay visible until all four children are built, and children until the parent is,
 *   so there are never holes while tiles stream in.
 * - No popping: each vertex carries the offset to where its parent would put it, and the material
 *   blends towards it with distance (geomorphing). When a tile swaps with its parent, both look
 *   identical. Skirts under tile edges hide cracks where neighbours differ in depth.
 * - Tiles are built on worker threads; only the component upload is on the game thread, capped
 *   per frame.
 *
 * Precision: every tile component sits at its tile centre, and its vertices are relative to that
 * centre, so single-precision mesh data only holds tile-sized values.
 *
 * Collision is separate from rendering: a few invisible collision tiles of fixed size around the
 * player ship, so the physics body count - and with it the cost of an origin rebase, which
 * teleports every body - stays small whatever the render LOD. A hidden sphere just under the
 * lowest possible terrain (the Body component) catches anything that outruns them.
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
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void Tick(float DeltaSeconds) override;

	virtual double GetSurfaceDistance(const FVector& Location) const override;

	/** Terrain height above the base radius, in cm, straight below a world location. */
	UFUNCTION(BlueprintPure, Category = "Planet")
	double GetTerrainHeightAt(const FVector& WorldLocation) const;

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

protected:
	/** Planet centre. Tiles and the Body safety sphere hang off this, unscaled. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Planet")
	TObjectPtr<USceneComponent> TerrainRoot;

	// --- Shape -------------------------------------------------------------------------------

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Shape", meta = (ClampMin = "0.05", Units = "km"))
	float RadiusKm = 0.5f;

	/** Height of the largest terrain features; smaller octaves add less. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Shape", meta = (ClampMin = "0.0", Units = "m"))
	float TerrainAmplitudeM = 12.f;

	/** Size of the largest terrain features along the surface. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Shape", meta = (ClampMin = "1.0", Units = "m"))
	float BaseWavelengthM = 200.f;

	/** Noise octaves; each halves the feature size and the height. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Shape", meta = (ClampMin = "1", ClampMax = "16"))
	int32 NoiseOctaves = 8;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Shape")
	int32 NoiseSeed = 1;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Shape")
	TObjectPtr<UMaterialInterface> TerrainMaterial;

	// --- LOD -----------------------------------------------------------------------------------

	/** Cells per tile edge. Must be even (geomorphing pairs up vertices). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|LOD", meta = (ClampMin = "4", ClampMax = "64"))
	int32 TileQuads = 32;

	/** The finest tiles are about this big; sets the quadtree depth. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|LOD", meta = (ClampMin = "0.5", Units = "m"))
	float LeafTileSizeM = 4.f;

	/** A tile splits when the camera is closer than this many tile sizes. Higher: sharper, more tiles. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|LOD", meta = (ClampMin = "1.0", ClampMax = "10.0"))
	float LodDistanceFactor = 3.f;

	/** Merge only this much farther out than the split distance, so tiles do not flicker. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|LOD", meta = (ClampMin = "1.0", ClampMax = "2.0"))
	float MergeHysteresis = 1.15f;

	/** Geomorphing starts at this fraction of a tile's merge distance and completes at it. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|LOD", meta = (ClampMin = "0.1", ClampMax = "0.95"))
	float MorphStartFraction = 0.6f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|LOD", meta = (ClampMin = "1"))
	int32 MaxConcurrentBuilds = 8;

	/** Hard cap on component creations per frame; each costs a render state upload. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|LOD", meta = (ClampMin = "1"))
	int32 MaxTileUploadsPerFrame = 12;

	/** Game-thread time per frame for creating tile components; stops early once spent. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|LOD", meta = (ClampMin = "0.1", Units = "ms"))
	float UploadBudgetMs = 2.f;

	/** Built tiles kept around (visible or not) before the least recently used are freed. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|LOD", meta = (ClampMin = "64"))
	int32 TileCacheLimit = 1500;

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

	/** Collision tiles are about this big; independent of the render LOD. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Collision", meta = (ClampMin = "4.0", Units = "m"))
	float CollisionTileSizeM = 64.f;

	/**
	 * Collision tiles within this distance of the player ship exist. With 64 m tiles, 60 m keeps
	 * it to about 15-25 bodies; at the 83 m/s boost speed that is still most of a second ahead,
	 * while a tile builds and cooks in a few frames.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Collision", meta = (ClampMin = "10.0", Units = "m"))
	float CollisionRadiusM = 60.f;

	/** Cells per collision tile edge: 32 over 64 m is a 2 m grid. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Planet|Collision", meta = (ClampMin = "2", ClampMax = "64"))
	int32 CollisionTileQuads = 32;

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

	FPlanetTerrainSettings MakeSettings() const;
	void RefreshDerivedSettings();

	void UpdateRenderLod(const FVector& CameraLocal, double NowSeconds);
	void UpdateCollisionTiles(const FVector& ShipLocal);
	void LaunchBuild(const FQuadTileId& Id, bool bCollision);
	void CollectFinishedBuilds();
	UProceduralMeshComponent* CreateTileComponent(const FTerrainTileMesh& Mesh, bool bCollision);
	void DestroyTile(uint64 Key);
	void ApplyDebugTint(UProceduralMeshComponent* Mesh, int32 Depth) const;

	bool IsReady(const FQuadTileId& Id) const { return Tiles.Contains(Id.Key()); }
	bool CanRender(const FQuadTileId& Id, TMap<uint64, bool>& Memo) const;
	bool AllChildrenCanRender(const FQuadTileId& Id, TMap<uint64, bool>& Memo) const;
	void ChooseVisible(const FQuadTileId& Id, const TSet<uint64>& SplitNodes, TMap<uint64, bool>& Memo, TSet<uint64>& OutVisible) const;

	FPlanetTerrainSettings Settings;
	int32 MaxDepth = 0;
	int32 CollisionDepth = 0;

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
