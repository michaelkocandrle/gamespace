// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "SpaceShotRunner.generated.h"

class ASpaceshipPawn;

/** One screenshot: where the ship is, what it is doing and which camera takes the picture. */
struct FSpaceShot
{
	FString Name;
	/** "cockpit" or "chase". */
	FString Camera = TEXT("chase");
	/** space.Hud: 0 hidden, 1 flight HUD only, 2 plus compact text, 3 plus full text; -1 leaves it alone. */
	int32 HudMode = 1;
	/** Place the ship this far above the nearest body's terrain (negative: leave it where it is). */
	float AltitudeM = -1.f;
	/** "planet", "away", "horizon": where the nose points after placing. */
	FString Facing = TEXT("horizon");
	/** Speed along the nose after placing, m/s. */
	float SpeedMS = 0.f;
	FString MasterMode;
	float Limiter = -1.f;
	int32 Coupled = -1;
	int32 GSafe = -1;
	int32 ComStab = -1;
	bool bBoost = false;
	bool bAfterburner = false;
	/** Mouse virtual joystick cursor, -1..1. */
	FVector2D Stick = FVector2D::ZeroVector;
	/** Seconds to let everything settle (thruster glow, HUD, camera lag) before the picture. */
	float Settle = 0.6f;
	/** Try another pilot eye position (relative to the hull, cm); zero keeps the ship's own. */
	FVector CockpitEye = FVector::ZeroVector;
	/** Hide the hull / the canopy from the pilot for this shot; -1 leaves the ship's setting. */
	int32 HideHull = -1;
	int32 HideCanopy = -1;
	/** Landing gear put straight down (1) or up (0), no animation; -1 leaves it. */
	int32 Gear = -1;
	/** Start lowering the gear (animated), so a short settle catches it on the way down. */
	bool bLowerGear = false;
	/** Precision mode on (1) / off (0) after the gear; -1 leaves what the gear set. */
	int32 Precision = -1;
	/** Chase camera swung round the ship (free look angles, degrees) and its distance as a multiple
	 * of the normal one (0: unchanged). All zero: the normal view from behind. */
	float ChaseYaw = 0.f;
	float ChasePitch = 0.f;
	float ChaseZoom = 0.f;
	/** Cockpit lighting for this shot (candela; -1 leaves the ship's): key and fill light, the glow of
	 * the displays onto the cockpit, and a multiplier on the interior's base colour. */
	float CockpitKeyCd = -1.f;
	float CockpitFillCd = -1.f;
	float DisplayLightCd = -1.f;
	float InteriorTint = -1.f;
	/** Console commands run before the shot (e.g. "r.AntiAliasingMethod 2"), for comparing settings. */
	TArray<FString> Console;
};

/**
 * Takes the screenshots that Docs/HANDOFF.md's "visual check" chapter is about, so a change to the
 * camera, the HUD or a ship can be looked at without anyone playing the game.
 *
 * Driven from the command line by Tools/Shots.ps1 in the packaged game (cooked materials, no editor):
 *
 *     gamespace.exe -ShotList="...\Tools\Shots\cockpit.json" -ShotOut="...\Saved\Shots\<stamp>_cockpit"
 *
 * It waits for the ship, then for every shot in the list places it, sets up the ship and the camera,
 * lets things settle, saves <index>_<name>.png and finally quits the game. In a normal session the
 * console commands do the same by hand:
 *
 *     space.Shot [name]        one picture of what is on screen now
 *     space.Shots <list.json>  run a whole list from here
 */
UCLASS()
class GAMESPACE_API USpaceShotRunner : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

	/** Runs a shot list (a JSON file, see Tools/Shots/*.json). Returns false if it cannot be read. */
	bool RunShotList(const FString& ListPath, const FString& OutputDirectory, bool bQuitWhenDone);

	/** One picture of the current view into the session's folder. */
	void TakeSingleShot(const FString& Name);

	/** Parses a shot list; exposed so tests can check the files without running the game. */
	static bool ParseShotList(const FString& Json, TArray<FSpaceShot>& OutShots, FString& OutError);

	/** Where shots go by default: <project>/Saved/Shots/manual. */
	static FString DefaultOutputDirectory();

private:
	void ApplyShot(const FSpaceShot& Shot, ASpaceshipPawn& Ship);
	ASpaceshipPawn* FindShip() const;

	TArray<FSpaceShot> Shots;
	FString OutputDirectory;
	int32 ShotIndex = INDEX_NONE;
	float Timer = 0.f;
	bool bQuitWhenFinished = false;
	/** Waiting for the picture to land on disk. */
	bool bWaitingForFile = false;
	FString PendingFile;
	int32 ManualShotCount = 0;
};
