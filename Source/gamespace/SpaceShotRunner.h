// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "SpaceShotRunner.generated.h"

class ASpaceshipPawn;
class ACameraActor;

/** One screenshot: where the ship is, what it is doing and which camera takes the picture. */
struct FSpaceShot
{
	FString Name;
	/** "cockpit", "chase", or "free" (a camera placed by camera_location / camera_look_at). */
	FString Camera = TEXT("chase");
	/**
	 * Free camera, metres in world space: where it stands and what it looks at. For pictures of
	 * something that is not the ship - an interior, a prop, a piece of the level.
	 */
	FVector CameraLocation = FVector::ZeroVector;
	FVector CameraLookAt = FVector::ZeroVector;
	bool bFreeCamera = false;
	/** Field of view of the free camera, degrees; 0 keeps the default. */
	float CameraFov = 0.f;

	/** Free camera only: pinned exposure, so two shots of the same room can be compared. 0 = auto. */
	float Exposure = 0.f;
	/** space.Hud: 0 hidden, 1 flight HUD only, 2 plus compact text, 3 plus full text; -1 leaves it alone. */
	int32 HudMode = 1;
	/** Place the ship this far above the nearest body's terrain (negative: leave it where it is). */
	float AltitudeM = -1.f;
	/** "planet", "away", "horizon", or "body:<name>": where the nose points after placing. */
	FString Facing = TEXT("horizon");
	/** Speed along the nose after placing, m/s. */
	float SpeedMS = 0.f;

	/**
	 * Velocity in the ship's own axes, m/s: forward, right, up. Set, it replaces speed_ms, which can
	 * only fly straight ahead. For the flight path marker, which only says anything when the ship is
	 * going somewhere other than where its nose points (SC-3).
	 */
	FVector Drift = FVector::ZeroVector;
	bool bHasDrift = false;
	FString MasterMode;
	/**
	 * Quantum jump at once to the body whose name starts with this ("quantum"; ASpaceshipPawn::
	 * DebugEngageQuantum), QuantumProgress of the way there ("quantum_progress"). Empty: no jump.
	 */
	FString QuantumTarget;
	float QuantumProgress = 0.f;
	/** Spool and calibration full ("quantum_ready"), for shots of the READY HUD. */
	bool bQuantumReady = false;
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
	void ApplyFreeCamera(const FSpaceShot& Shot, ASpaceshipPawn& Ship);
	void ApplyShot(const FSpaceShot& Shot, ASpaceshipPawn& Ship);
	ASpaceshipPawn* FindShip() const;

	TArray<FSpaceShot> Shots;
	/** Spawned only when a shot asks for a free camera. */
	TWeakObjectPtr<ACameraActor> FreeCamera;
	FString OutputDirectory;
	int32 ShotIndex = INDEX_NONE;
	float Timer = 0.f;
	bool bQuitWhenFinished = false;
	/** Waiting for the picture to land on disk. */
	bool bWaitingForFile = false;
	FString PendingFile;
	int32 ManualShotCount = 0;
};
