// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "CelestialBody.h"
#include "GameFramework/Character.h"
#include "PlayerCharacterAnimInstance.h"
#include "PlayerCharacter.generated.h"

class ASpaceshipPawn;
class UCameraComponent;
class UInputAction;
class UInputMappingContext;
class USpringArmComponent;
struct FInputActionValue;

/**
 * The player on foot: UE5 Mannequin placeholder, third-person camera, walk / sprint / jump, and
 * boarding a landed ship.
 *
 * Gravity follows the nearest celestial body: every tick the movement component gets the
 * body's local down (SetGravityDirection) and its strength (GravityScale against the world's
 * gravity). Character Movement then walks, jumps and stays upright in that frame by itself.
 *
 * What the engine does not do for custom gravity is the view. Control rotation is a world-space
 * rotator that the camera manager clamps in world pitch and roll, which breaks as soon as "up"
 * is not world Z. So the look direction is kept here instead: yaw and pitch relative to a gravity
 * frame that is carried along (parallel-transported) as up changes, and the camera boom is
 * rotated to it directly. Walking once around the planet leaves no twist in the controls.
 */
UCLASS(Blueprintable)
class GAMESPACE_API APlayerCharacter : public ACharacter
{
	GENERATED_BODY()

public:
	APlayerCharacter();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
	virtual void UnPossessed() override;

	/** Points the view (and the character) along Forward, projected onto the local ground plane. */
	UFUNCTION(BlueprintCallable, Category = "Player")
	void FaceDirection(const FVector& Forward);

	/** Nearest landed ship within BoardingRangeCm, or null. */
	UFUNCTION(BlueprintPure, Category = "Player|Ship")
	ASpaceshipPawn* FindBoardableShip(double& OutDistanceCm) const;

	/** Hands control to the nearest boardable ship and removes this character. */
	UFUNCTION(BlueprintCallable, Category = "Player|Ship")
	bool TryBoardShip();

	UFUNCTION(BlueprintPure, Category = "Player")
	bool IsSprinting() const { return bSprintHeld; }

	UFUNCTION(BlueprintPure, Category = "Player")
	bool HasEnvironment() const { return bHasEnvironment; }

	const FCelestialEnvironment& GetEnvironment() const { return Environment; }

	UFUNCTION(BlueprintPure, Category = "Player")
	FVector GetGravityUp() const { return GravityFrame.GetUpVector(); }

	/** Standing in a ship's artificial gravity (ASpaceGravityVolume) rather than a planet's. */
	UFUNCTION(BlueprintPure, Category = "Player")
	bool IsInArtificialGravity() const { return bInGravityVolume; }

	/** Turns the view (and so the walking direction) to yaw degrees in the gravity frame. */
	UFUNCTION(BlueprintCallable, Category = "Player")
	void SetLookYaw(float Yaw) { LookYaw = FRotator::NormalizeAxis(Yaw); }

	/**
	 * Walks as if the movement keys were held (X right, Y forward, -1..1) for Seconds, then logs
	 * where the character stopped. space.Walk; checks collision in the packaged game.
	 */
	UFUNCTION(BlueprintCallable, Category = "Player|Tests")
	void DebugWalk(FVector2D Input, float Seconds);

	UFUNCTION(BlueprintPure, Category = "Player")
	FFootIKState GetFootIKState() const;

	/** How often the character was put back on top of the terrain (fallen through, or stuck). */
	UFUNCTION(BlueprintPure, Category = "Player")
	int32 GetTerrainRecoveryCount() const { return TerrainRecoveries; }

	/**
	 * The safety net on its own: if the capsule is more than FallThroughToleranceCm under the
	 * terrain (the analytic height, not the collision mesh), or has been stuck falling without
	 * moving, lifts it back on top. Tick calls this; returns true when it moved the character.
	 */
	UFUNCTION(BlueprintCallable, Category = "Player")
	bool RecoverFromTerrain(float DeltaSeconds);

	// --- Pure helpers, exposed for tests -------------------------------------------------------

	/** Character Movement's GravityScale for a gravity in cm/s^2 in a world with WorldGravityZ. */
	UFUNCTION(BlueprintCallable, Category = "Player|Tests")
	static float ComputeGravityScale(float GravityCmS2, float WorldGravityZ);

	/** Frame rotated by the smallest rotation that takes its up vector to NewUp (no twist). */
	UFUNCTION(BlueprintCallable, Category = "Player|Tests")
	static FRotator TransportGravityFrame(const FRotator& Frame, const FVector& NewUp);

	/** World rotation of a view with yaw and pitch relative to a gravity frame. */
	UFUNCTION(BlueprintCallable, Category = "Player|Tests")
	static FRotator ComputeViewRotation(const FRotator& GravityFrame, float Yaw, float Pitch);

	/**
	 * Tests: ticks the mesh's animation with a forced movement state (and optionally forced ground
	 * heights under the feet, cm) and returns component-space locations of pelvis, foot_l, foot_r,
	 * thigh_l, thigh_r, calf_l, calf_r, then the proxy's (pre-update, update, evaluate) counts.
	 */
	UFUNCTION(BlueprintCallable, Category = "Player|Tests")
	TArray<FVector> DebugSampleAnimation(float GroundSpeed, bool bFalling, bool bOverrideGround, float LeftGroundCm, float RightGroundCm, float Seconds);

protected:
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Player|Components")
	TObjectPtr<USpringArmComponent> CameraBoom;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Player|Components")
	TObjectPtr<UCameraComponent> FollowCamera;

	// --- Input ---------------------------------------------------------------------------------

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Player|Input")
	TObjectPtr<UInputMappingContext> CharacterMappingContext;

	/** Axis2D: X right, Y forward. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Player|Input")
	TObjectPtr<UInputAction> MoveAction;

	/** Axis2D, raw mouse movement. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Player|Input")
	TObjectPtr<UInputAction> LookAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Player|Input")
	TObjectPtr<UInputAction> JumpAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Player|Input")
	TObjectPtr<UInputAction> SprintAction;

	/** Shared with the ship: H cycles the debug HUD. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Player|Input")
	TObjectPtr<UInputAction> ToggleHudAction;

	/** Shared with the ship: F boards here, exits there. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Player|Input")
	TObjectPtr<UInputAction> InteractAction;

	// --- Tuning --------------------------------------------------------------------------------

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Player|Movement", meta = (ClampMin = "0.0"))
	float WalkSpeed = 250.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Player|Movement", meta = (ClampMin = "0.0"))
	float SprintSpeed = 550.f;

	/**
	 * Take-off speed of a jump, cm/s. Jump height is v^2 / 2g: 450 gives ~1.7 m under Veyra's
	 * 6 m/s^2 (the engine default 700 would be ~4 m).
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Player|Movement", meta = (ClampMin = "0.0"))
	float JumpVelocity = 450.f;

	/** Degrees of view rotation per mouse count. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Player|Camera", meta = (ClampMin = "0.0"))
	float LookSensitivity = 0.15f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Player|Camera")
	bool bInvertPitch = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Player|Camera", meta = (ClampMin = "-89.0", ClampMax = "0.0"))
	float MinViewPitch = -65.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Player|Camera", meta = (ClampMin = "0.0", ClampMax = "89.0"))
	float MaxViewPitch = 55.f;

	/** How close to a landed ship's hull F boards it, cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Player|Ship", meta = (ClampMin = "50.0"))
	float BoardingRangeCm = 400.f;

	/**
	 * How far the bottom of the capsule may be under the terrain surface before it counts as
	 * fallen through, cm. Collision tiles follow the height field to a few cm; this leaves room.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Player|Movement", meta = (ClampMin = "10.0"))
	float FallThroughToleranceCm = 60.f;

	/** Falling this long without moving means stuck (on a collision seam, inside something). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Player|Movement", meta = (ClampMin = "0.1", Units = "s"))
	float StuckFallingSeconds = 0.6f;

	/** No boarding for this long after the character appeared (it spawns next to the ship). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Player|Ship", meta = (ClampMin = "0.0", Units = "s"))
	float BoardingCooldownSeconds = 0.75f;

private:
	void ResolveInputAssets();
	void HandleMove(const FInputActionValue& Value);
	void HandleMoveCompleted(const FInputActionValue& Value);
	void HandleLook(const FInputActionValue& Value);
	void HandleJump(const FInputActionValue& Value);
	void HandleJumpReleased(const FInputActionValue& Value);
	void HandleSprint(const FInputActionValue& Value);
	void HandleSprintReleased(const FInputActionValue& Value);
	void HandleInteract(const FInputActionValue& Value);
	void HandleToggleHud(const FInputActionValue& Value);

	void UpdateGravity();
	void UpdateView();

	FCelestialEnvironment Environment;
	bool bHasEnvironment = false;
	bool bInGravityVolume = false;

	FVector2D DebugWalkInput = FVector2D::ZeroVector;
	float DebugWalkSeconds = 0.f;

	/** Carried along the planet: Z is up, X is the reference heading for LookYaw. */
	FQuat GravityFrame = FQuat::Identity;
	float LookYaw = 0.f;
	float LookPitch = -10.f;

	FVector2D MoveInput = FVector2D::ZeroVector;
	bool bSprintHeld = false;

	int32 TerrainRecoveries = 0;
	float StuckSeconds = 0.f;
};
