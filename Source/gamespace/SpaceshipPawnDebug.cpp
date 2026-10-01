// Copyright Epic Games, Inc. All Rights Reserved.

// ASpaceshipPawn's test and shot API: the Debug* functions the headless tests (Tools/Tests), the shot runner and
// tuning sessions call, and the space.* console commands. Split out of SpaceshipPawn.cpp so the runtime code and the
// test hooks are read apart (Docs/Reviews/2026-09-30_spaceshippawn_split_plan.md, step 9); same class, same
// UFUNCTIONs, so Python and the HUD see no difference.

#include "SpaceshipPawn.h"

#include "Camera/CameraComponent.h"
#include "CockpitDisplayComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/SpringArmComponent.h"
#include "HAL/IConsoleManager.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "SpaceshipLog.h"

namespace
{
	/** space.DashboardFocus 1 / 0: holds the dashboard focus of every ship (shots, testing). */
	FAutoConsoleCommandWithWorldAndArgs DashboardFocusCommand(
		TEXT("space.DashboardFocus"),
		TEXT("space.DashboardFocus 1|0: lean in to the dashboard's displays (Z or the middle mouse button in the game)."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			const bool bOn = Args.Num() == 0 || FCString::Atoi(*Args[0]) != 0;
			for (TActorIterator<ASpaceshipPawn> It(World); It; ++It)
			{
				It->SetDashboardFocus(bOn);
			}
		}));

	/** Material parameters of every ship here, live: space.ShipMat <Parameter> <Value>. */
	FAutoConsoleCommandWithWorldAndArgs ShipMaterialCommand(
		TEXT("space.ShipMat"),
		TEXT("space.ShipMat <Parameter> <Value>: set a scalar on every material of the ship (DetailNormalStrength, DetailTileCm, RoughnessScale...). Not saved."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			if (Args.Num() < 2)
			{
				UE_LOG(LogTemp, Display, TEXT("space.ShipMat <Parameter> <Value>"));
				return;
			}
			int32 Changed = 0;
			for (TActorIterator<ASpaceshipPawn> It(World); It; ++It)
			{
				Changed += It->DebugSetMaterialScalar(FName(*Args[0]), FCString::Atof(*Args[1]));
			}
			UE_LOG(LogTemp, Display, TEXT("space.ShipMat %s = %s on %d materials"), *Args[0], *Args[1], Changed);
		}));

	/** The same for a colour: space.ShipMatColor <Parameter> <R> <G> <B>. */
	FAutoConsoleCommandWithWorldAndArgs ShipMaterialColorCommand(
		TEXT("space.ShipMatColor"),
		TEXT("space.ShipMatColor <Parameter> <R> <G> <B>: set a colour on every material of the ship (BaseColorTint...). Not saved."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			if (Args.Num() < 4)
			{
				UE_LOG(LogTemp, Display, TEXT("space.ShipMatColor <Parameter> <R> <G> <B>"));
				return;
			}
			const FLinearColor Colour(FCString::Atof(*Args[1]), FCString::Atof(*Args[2]), FCString::Atof(*Args[3]), 1.f);
			int32 Changed = 0;
			for (TActorIterator<ASpaceshipPawn> It(World); It; ++It)
			{
				Changed += It->DebugSetMaterialColor(FName(*Args[0]), Colour);
			}
			UE_LOG(LogTemp, Display, TEXT("space.ShipMatColor %s on %d materials"), *Args[0], Changed);
		}));

	/**
	 * space.Drift <forward> <right> <up>: sets the ship's velocity in its own axes, m/s. For shots of
	 * the HUD in states the shot runner cannot fly into - sliding sideways, going backwards - where
	 * the flight path marker is the whole point. The flight computer takes over again immediately in
	 * coupled flight, so pair it with decoupled.
	 */
	FAutoConsoleCommandWithWorldAndArgs DriftCommand(
		TEXT("space.Drift"),
		TEXT("space.Drift <forward> <right> <up>: set the ship's velocity in its own axes, m/s."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			const FVector Local(Args.Num() > 0 ? FCString::Atof(*Args[0]) * 100.f : 0.f,
				Args.Num() > 1 ? FCString::Atof(*Args[1]) * 100.f : 0.f,
				Args.Num() > 2 ? FCString::Atof(*Args[2]) * 100.f : 0.f);
			for (TActorIterator<ASpaceshipPawn> It(World); It; ++It)
			{
				It->DebugSetLinearVelocity(It->GetActorQuat().RotateVector(Local));
			}
			UE_LOG(LogTemp, Display, TEXT("space.Drift %.0f %.0f %.0f m/s (ship axes)"),
				Local.X / 100.f, Local.Y / 100.f, Local.Z / 100.f);
		}));

	/** space.Quantum <name> [progress]: jump at once (shots, testing a destination without flying to it). */
	FAutoConsoleCommandWithWorldAndArgs QuantumCommand(
		TEXT("space.Quantum"),
		TEXT("space.Quantum <destination name> [0..1 of the way]: quantum jump at once, no spool. space.Quantum ready: spool and calibration full."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			for (TActorIterator<ASpaceshipPawn> It(World); It; ++It)
			{
				if (Args.Num() > 0 && Args[0].Equals(TEXT("ready"), ESearchCase::IgnoreCase))
				{
					It->DebugFinishQuantumCharge();
				}
				else
				{
					It->DebugEngageQuantum(Args.Num() > 0 ? Args[0] : FString(), Args.Num() > 1 ? FCString::Atof(*Args[1]) : 0.f);
				}
			}
		}));

	/** space.Vtol 1 / 0: VTOL on every ship here, for shots that should not depend on a key. */
	FAutoConsoleCommandWithWorldAndArgs VtolCommand(
		TEXT("space.Vtol"),
		TEXT("space.Vtol 1|0: VTOL (G in the game). SCM only."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			const bool bOn = Args.Num() == 0 || FCString::Atoi(*Args[0]) != 0;
			for (TActorIterator<ASpaceshipPawn> It(World); It; ++It)
			{
				It->SetVtol(bOn);
			}
		}));

	/** space.CockpitPitch <deg>: the cockpit view's rest pitch (comparison shots of the framing). */
	FAutoConsoleCommandWithWorldAndArgs CockpitPitchCommand(
		TEXT("space.CockpitPitch"),
		TEXT("space.CockpitPitch <degrees>: tilt the cockpit view at rest (negative looks down)."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			for (TActorIterator<ASpaceshipPawn> It(World); It; ++It)
			{
				It->SetCockpitViewPitch(Args.Num() > 0 ? FCString::Atof(*Args[0]) : 0.f);
			}
		}));
}


void ASpaceshipPawn::DebugConfigureCockpit(const FVector& EyeLocation, bool bHideHull, bool bHideCanopy)
{
	if (!EyeLocation.IsNearlyZero())
	{
		CockpitCamera->SetRelativeLocation(EyeLocation);
		// UpdateCameraEffects puts the camera back on its base location (plus shake) every frame, so
		// the base has to move too or the new eye lasts exactly one frame.
		CockpitCameraBaseLocation = EyeLocation;
	}
	bHideHullInCockpit = bHideHull;
	bHideCanopyInCockpit = bHideCanopy;
	if (CockpitFrameRoot)
	{
		// The placeholder cockpit is built around the eye; it moves with it.
		CockpitFrameRoot->SetRelativeLocation(CockpitCameraBaseLocation);
	}
	// So do the cockpit lights, or a shot from another eye would be lit differently.
	PlaceCockpitLights();
	SetCockpitView(bCockpitView);
}

void ASpaceshipPawn::DebugSetCockpitLighting(float KeyCd, float FillCd, float DisplayCd, float InteriorTint)
{
	if (KeyCd >= 0.f)
	{
		CockpitLightIntensityCd = KeyCd;
	}
	if (FillCd >= 0.f)
	{
		CockpitFillIntensityCd = FillCd;
	}
	PlaceCockpitLights();
	if (DisplayCd >= 0.f && CockpitDisplays)
	{
		CockpitDisplays->SetDisplayLightIntensity(DisplayCd);
	}
	if (InteriorTint >= 0.f)
	{
		TArray<UStaticMeshComponent*> Meshes;
		GetComponents(Meshes);
		for (UStaticMeshComponent* Mesh : Meshes)
		{
			if (Mesh->GetName() == TEXT("Interior") && Mesh->GetNumMaterials() > 0)
			{
				UMaterialInstanceDynamic* Dynamic = Mesh->CreateDynamicMaterialInstance(0);
				// The imported instance's own tint times the multiplier, so 1 is the ship as imported.
				FLinearColor Tint = FLinearColor::White;
				if (Dynamic->Parent)
				{
					Dynamic->Parent->GetVectorParameterValue(TEXT("BaseColorTint"), Tint);
				}
				Tint = Tint * InteriorTint;
				Tint.A = 1.f;
				Dynamic->SetVectorParameterValue(TEXT("BaseColorTint"), Tint);
			}
		}
	}
}

int32 ASpaceshipPawn::DebugSetMaterialScalar(FName Parameter, float Value)
{
	int32 Changed = 0;
	TInlineComponentArray<UMeshComponent*> Meshes(this);
	for (UMeshComponent* Mesh : Meshes)
	{
		for (int32 Slot = 0; Slot < Mesh->GetNumMaterials(); ++Slot)
		{
			UMaterialInstanceDynamic* Dynamic = Cast<UMaterialInstanceDynamic>(Mesh->GetMaterial(Slot));
			if (!Dynamic)
			{
				Dynamic = Mesh->CreateDynamicMaterialInstance(Slot);
			}
			if (Dynamic)
			{
				Dynamic->SetScalarParameterValue(Parameter, Value);
				++Changed;
			}
		}
	}
	return Changed;
}

int32 ASpaceshipPawn::DebugSetMaterialColor(FName Parameter, FLinearColor Value)
{
	int32 Changed = 0;
	TInlineComponentArray<UMeshComponent*> Meshes(this);
	for (UMeshComponent* Mesh : Meshes)
	{
		for (int32 Slot = 0; Slot < Mesh->GetNumMaterials(); ++Slot)
		{
			UMaterialInstanceDynamic* Dynamic = Cast<UMaterialInstanceDynamic>(Mesh->GetMaterial(Slot));
			if (!Dynamic)
			{
				Dynamic = Mesh->CreateDynamicMaterialInstance(Slot);
			}
			if (Dynamic)
			{
				Dynamic->SetVectorParameterValue(Parameter, Value);
				++Changed;
			}
		}
	}
	return Changed;
}

void ASpaceshipPawn::DebugAdvanceDashboardFocus(float Seconds)
{
	for (float Left = Seconds; Left > 0.f; Left -= 1.f / 60.f)
	{
		UpdateFreeLook(FMath::Min(Left, 1.f / 60.f));
	}
}

TArray<FVector> ASpaceshipPawn::DebugSimulateFreeLook(const TArray<FVector>& Frames)
{
	const float Step = 1.f / 60.f;
	TArray<FVector> Result;
	for (const FVector& Frame : Frames)
	{
		SetFreeLookHeld(Frame.Z > 0.5);
		MouseLookDelta += FVector2D(Frame.X, Frame.Y);
		UpdateFreeLook(Step);
		UpdateAngularMotion(Step);
		Result.Add(FVector(FreeLookAngles.X, FreeLookAngles.Y, bFreeLookHeld ? 1.0 : 0.0));
		const FRotator Rotation = GetActorRotation();
		Result.Add(FVector(Rotation.Pitch, Rotation.Yaw, Rotation.Roll));
	}
	return Result;
}

FVector ASpaceshipPawn::DebugStepFlight(float DeltaSeconds, float Thrust, float Strafe, float Lift, bool bBoost)
{
	ThrustInput = Thrust;
	StrafeInput = Strafe;
	LiftInput = Lift;
	Systems->SetBoostHeld(bBoost);
	StepFlight(DeltaSeconds);
	return LinearVelocity;
}

FVector ASpaceshipPawn::DebugStepFlightInput(float DeltaSeconds, const FVector& LinearInput, const FVector& RotationInput, bool bBoost)
{
	ThrustInput = float(LinearInput.X);
	StrafeInput = float(LinearInput.Y);
	LiftInput = float(LinearInput.Z);
	RollInput = float(RotationInput.X);
	LookInput = FVector2D(RotationInput.Z, RotationInput.Y);
	Systems->SetBoostHeld(bBoost);
	StepFlight(DeltaSeconds);
	return LinearVelocity;
}

bool ASpaceshipPawn::DebugEngageQuantum(const FString& TargetName, float TravelFraction)
{
	AActor* Picked = Quantum->FindDestination(TargetName, GetActorLocation(), GetActorForwardVector());
	if (!Picked)
	{
		UE_LOG(LogSpaceship, Warning, TEXT("%s: no quantum destination '%s'"), *GetName(), *TargetName);
		return false;
	}
	Systems->ForceMasterMode(EMasterMode::NAV);
	Quantum->SetTarget(Picked);
	Quantum->UpdateTarget(GetActorLocation(), GetActorForwardVector(), GetQuantumRules());
	const FVector Direction = (Quantum->GetTargetCentre() - GetActorLocation()).GetSafeNormal();
	SetActorRotation(FRotationMatrix::MakeFromXZ(Direction, GetActorUpVector()).ToQuat());
	BeginQuantumJump();
	if (TravelFraction > 0.f)
	{
		const double Skip = Quantum->GetJumpLengthCm() * FMath::Clamp(double(TravelFraction), 0.0, 0.95);
		SetActorLocation(GetActorLocation() + Direction * Skip);
		Quantum->SkipTravel(Skip);
	}
	LinearVelocity = Direction * ComputeQuantumSpeed(Quantum->GetTargetDistanceCm(), double(QuantumMaxSpeedKmS) * 100000.0, 0.f);
	// Shots part-way through a jump start past the acceleration ramp; at 0 the ramp plays out.
	Quantum->SetTravelSeconds(TravelFraction > 0.f ? QuantumRampSeconds + 1.f : 0.f);
	if (TravelFraction <= 0.f)
	{
		LinearVelocity = Direction * double(QuantumExitSpeed);
	}
	Presentation->SetQuantumBlend(TravelFraction > 0.f ? 1.f : 0.f);
	return true;
}

void ASpaceshipPawn::DebugStepGear(float DeltaSeconds)
{
	UpdateGear(DeltaSeconds);
}

void ASpaceshipPawn::DebugSetGearInstant(bool bDown)
{
	if (!bDown && Landing->IsLanded())
	{
		return;
	}
	Landing->SetGearInstant(bDown);
	PoseGearLegs();
}

void ASpaceshipPawn::DebugSetChaseView(float YawDeg, float PitchDeg, float Zoom)
{
	if (Zoom > 0.f)
	{
		CameraZoom = CameraZoomTarget = Zoom;
	}
	if (FMath::IsNearlyZero(YawDeg) && FMath::IsNearlyZero(PitchDeg))
	{
		SetFreeLookHeld(false);
		FreeLookAngles = FreeLookTarget = FVector2D::ZeroVector;
	}
	else
	{
		SetFreeLookHeld(true);
		FreeLookAngles = FreeLookTarget = FVector2D(YawDeg, PitchDeg);
	}
	const FRotator Offset(float(FreeLookAngles.Y), float(FreeLookAngles.X), 0.f);
	CameraBoom->SetRelativeRotation(Offset);
	CockpitCamera->SetRelativeRotation(Offset);
	SnapCameraToShip();
}

void ASpaceshipPawn::DebugForceLanded(bool bLanded)
{
	if (bLanded && Landing->GetState() != ELandingState::Landed)
	{
		EnterLanded();
	}
	else if (!bLanded && Landing->GetState() == ELandingState::Landed)
	{
		ExitLanded();
	}
}
