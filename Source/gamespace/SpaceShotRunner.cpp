// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceShotRunner.h"

#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/PlayerController.h"

#include "CelestialBody.h"
#include "DistantBody.h"
#include "Dom/JsonObject.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformFileManager.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "SpaceshipPawn.h"
#include "UnrealClient.h"

DEFINE_LOG_CATEGORY_STATIC(LogSpaceShots, Log, All);

namespace SpaceShotRunnerLocal
{
	/** Seconds to wait for a requested screenshot to appear before moving on. */
	constexpr float FileTimeout = 5.f;

	ACelestialBody* FindBody(const UWorld* World, const FVector& Near)
	{
		ACelestialBody* Best = nullptr;
		double BestDistance = TNumericLimits<double>::Max();
		for (TActorIterator<ACelestialBody> It(World); It; ++It)
		{
			const double Distance = It->GetSurfaceDistance(Near);
			if (Distance < BestDistance)
			{
				BestDistance = Distance;
				Best = *It;
			}
		}
		return Best;
	}
}

void USpaceShotRunner::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	// Started by Tools/Shots.ps1: run the list as soon as there is a ship, then quit.
	FString ListPath;
	if (FParse::Value(FCommandLine::Get(), TEXT("-ShotList="), ListPath))
	{
		FString OutDirectory;
		if (!FParse::Value(FCommandLine::Get(), TEXT("-ShotOut="), OutDirectory))
		{
			OutDirectory = DefaultOutputDirectory();
		}
		RunShotList(ListPath, OutDirectory, true);
	}
}

bool USpaceShotRunner::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

TStatId USpaceShotRunner::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(USpaceShotRunner, STATGROUP_Tickables);
}

FString USpaceShotRunner::DefaultOutputDirectory()
{
	return FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Shots"), TEXT("manual"));
}

bool USpaceShotRunner::ParseShotList(const FString& Json, TArray<FSpaceShot>& OutShots, FString& OutError)
{
	TSharedPtr<FJsonObject> Root;
	const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Json);
	if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
	{
		OutError = TEXT("not valid JSON");
		return false;
	}
	const TArray<TSharedPtr<FJsonValue>>* Entries = nullptr;
	if (!Root->TryGetArrayField(TEXT("shots"), Entries))
	{
		OutError = TEXT("no \"shots\" array");
		return false;
	}
	for (const TSharedPtr<FJsonValue>& Entry : *Entries)
	{
		const TSharedPtr<FJsonObject>* Object = nullptr;
		if (!Entry->TryGetObject(Object))
		{
			continue;
		}
		FSpaceShot Shot;
		Shot.Name = (*Object)->GetStringField(TEXT("name"));
		(*Object)->TryGetStringField(TEXT("camera"), Shot.Camera);
		(*Object)->TryGetStringField(TEXT("facing"), Shot.Facing);
		(*Object)->TryGetStringField(TEXT("mode"), Shot.MasterMode);
		double Number = 0.0;
		if ((*Object)->TryGetNumberField(TEXT("hud"), Number)) { Shot.HudMode = int32(Number); }
		if ((*Object)->TryGetNumberField(TEXT("altitude_m"), Number)) { Shot.AltitudeM = float(Number); }
		if ((*Object)->TryGetNumberField(TEXT("speed_ms"), Number)) { Shot.SpeedMS = float(Number); }
		(*Object)->TryGetStringField(TEXT("quantum"), Shot.QuantumTarget);
		if ((*Object)->TryGetNumberField(TEXT("quantum_progress"), Number)) { Shot.QuantumProgress = float(Number); }
		(*Object)->TryGetBoolField(TEXT("quantum_ready"), Shot.bQuantumReady);
		const TArray<TSharedPtr<FJsonValue>>* DriftValues = nullptr;
		if ((*Object)->TryGetArrayField(TEXT("drift"), DriftValues) && DriftValues->Num() == 3)
		{
			Shot.Drift = FVector((*DriftValues)[0]->AsNumber(), (*DriftValues)[1]->AsNumber(), (*DriftValues)[2]->AsNumber());
			Shot.bHasDrift = true;
		}
		if ((*Object)->TryGetNumberField(TEXT("limiter"), Number)) { Shot.Limiter = float(Number); }
		if ((*Object)->TryGetNumberField(TEXT("settle"), Number)) { Shot.Settle = float(Number); }
		bool bFlag = false;
		if ((*Object)->TryGetBoolField(TEXT("coupled"), bFlag)) { Shot.Coupled = bFlag ? 1 : 0; }
		if ((*Object)->TryGetBoolField(TEXT("gsafe"), bFlag)) { Shot.GSafe = bFlag ? 1 : 0; }
		if ((*Object)->TryGetBoolField(TEXT("comstab"), bFlag)) { Shot.ComStab = bFlag ? 1 : 0; }
		(*Object)->TryGetBoolField(TEXT("boost"), Shot.bBoost);
		(*Object)->TryGetBoolField(TEXT("afterburner"), Shot.bAfterburner);
		if ((*Object)->TryGetBoolField(TEXT("hide_hull"), bFlag)) { Shot.HideHull = bFlag ? 1 : 0; }
		if ((*Object)->TryGetBoolField(TEXT("hide_canopy"), bFlag)) { Shot.HideCanopy = bFlag ? 1 : 0; }
		if ((*Object)->TryGetBoolField(TEXT("gear"), bFlag)) { Shot.Gear = bFlag ? 1 : 0; }
		(*Object)->TryGetBoolField(TEXT("lower_gear"), Shot.bLowerGear);
		if ((*Object)->TryGetBoolField(TEXT("precision"), bFlag)) { Shot.Precision = bFlag ? 1 : 0; }
		if ((*Object)->TryGetNumberField(TEXT("chase_yaw"), Number)) { Shot.ChaseYaw = float(Number); }
		if ((*Object)->TryGetNumberField(TEXT("chase_pitch"), Number)) { Shot.ChasePitch = float(Number); }
		if ((*Object)->TryGetNumberField(TEXT("chase_zoom"), Number)) { Shot.ChaseZoom = float(Number); }
		const TArray<TSharedPtr<FJsonValue>>* Commands = nullptr;
		if ((*Object)->TryGetArrayField(TEXT("console"), Commands))
		{
			for (const TSharedPtr<FJsonValue>& Command : *Commands)
			{
				Shot.Console.Add(Command->AsString());
			}
		}
		const TArray<TSharedPtr<FJsonValue>>* Lights = nullptr;
		if ((*Object)->TryGetArrayField(TEXT("cockpit_light"), Lights) && Lights->Num() == 2)
		{
			Shot.CockpitKeyCd = float((*Lights)[0]->AsNumber());
			Shot.CockpitFillCd = float((*Lights)[1]->AsNumber());
		}
		if ((*Object)->TryGetNumberField(TEXT("display_light"), Number)) { Shot.DisplayLightCd = float(Number); }
		if ((*Object)->TryGetNumberField(TEXT("interior_tint"), Number)) { Shot.InteriorTint = float(Number); }
		const TArray<TSharedPtr<FJsonValue>>* Eye = nullptr;
		if ((*Object)->TryGetArrayField(TEXT("cockpit_eye"), Eye) && Eye->Num() == 3)
		{
			Shot.CockpitEye = FVector((*Eye)[0]->AsNumber(), (*Eye)[1]->AsNumber(), (*Eye)[2]->AsNumber());
		}
		const TArray<TSharedPtr<FJsonValue>>* FreeLoc = nullptr;
		if ((*Object)->TryGetArrayField(TEXT("camera_location"), FreeLoc) && FreeLoc->Num() == 3)
		{
			// Metres in the JSON, centimetres in the engine.
			Shot.CameraLocation = FVector((*FreeLoc)[0]->AsNumber(), (*FreeLoc)[1]->AsNumber(), (*FreeLoc)[2]->AsNumber()) * 100.0;
			Shot.bFreeCamera = true;
		}
		const TArray<TSharedPtr<FJsonValue>>* FreeLook = nullptr;
		if ((*Object)->TryGetArrayField(TEXT("camera_look_at"), FreeLook) && FreeLook->Num() == 3)
		{
			Shot.CameraLookAt = FVector((*FreeLook)[0]->AsNumber(), (*FreeLook)[1]->AsNumber(), (*FreeLook)[2]->AsNumber()) * 100.0;
		}
		if ((*Object)->TryGetNumberField(TEXT("fov"), Number)) { Shot.CameraFov = float(Number); }
		if ((*Object)->TryGetNumberField(TEXT("exposure"), Number)) { Shot.Exposure = float(Number); }
		const TArray<TSharedPtr<FJsonValue>>* Stick = nullptr;
		if ((*Object)->TryGetArrayField(TEXT("stick"), Stick) && Stick->Num() == 2)
		{
			Shot.Stick = FVector2D((*Stick)[0]->AsNumber(), (*Stick)[1]->AsNumber());
		}
		if (Shot.Name.IsEmpty())
		{
			OutError = TEXT("a shot without a name");
			return false;
		}
		OutShots.Add(Shot);
	}
	if (OutShots.Num() == 0)
	{
		OutError = TEXT("no shots in the list");
		return false;
	}
	return true;
}

bool USpaceShotRunner::RunShotList(const FString& ListPath, const FString& InOutputDirectory, bool bQuitWhenDone)
{
	FString Json;
	if (!FFileHelper::LoadFileToString(Json, *ListPath))
	{
		UE_LOG(LogSpaceShots, Error, TEXT("SHOTS cannot read %s"), *ListPath);
		return false;
	}
	FString Error;
	TArray<FSpaceShot> Parsed;
	if (!ParseShotList(Json, Parsed, Error))
	{
		UE_LOG(LogSpaceShots, Error, TEXT("SHOTS %s: %s"), *ListPath, *Error);
		return false;
	}
	Shots = MoveTemp(Parsed);
	OutputDirectory = InOutputDirectory;
	bQuitWhenFinished = bQuitWhenDone;
	ShotIndex = 0;
	Timer = 0.f;
	bWaitingForFile = false;
	IPlatformFile::GetPlatformPhysical().CreateDirectoryTree(*OutputDirectory);
	UE_LOG(LogSpaceShots, Display, TEXT("SHOTS %d shot(s) from %s into %s"), Shots.Num(), *ListPath, *OutputDirectory);
	return true;
}

ASpaceshipPawn* USpaceShotRunner::FindShip() const
{
	const UWorld* World = GetWorld();
	const APlayerController* Controller = World ? World->GetFirstPlayerController() : nullptr;
	return Controller ? Cast<ASpaceshipPawn>(Controller->GetPawn()) : nullptr;
}

void USpaceShotRunner::ApplyShot(const FSpaceShot& Shot, ASpaceshipPawn& Ship)
{
	for (const FString& Command : Shot.Console)
	{
		UE_LOG(LogSpaceShots, Display, TEXT("SHOTS console: %s"), *Command);
		GEngine->Exec(Ship.GetWorld(), *Command);
	}
	UWorld* World = GetWorld();
	if (Shot.HudMode >= 0)
	{
		if (IConsoleVariable* Hud = IConsoleManager::Get().FindConsoleVariable(TEXT("space.Hud")))
		{
			Hud->Set(Shot.HudMode, ECVF_SetByConsole);
		}
	}

	// Place the ship at a height over the nearest body, pointing where the shot asks.
	if (Shot.AltitudeM >= 0.f)
	{
		// A ship landed by the previous shot would stay glued to the ground.
		Ship.DebugForceLanded(false);
		if (const ACelestialBody* Body = SpaceShotRunnerLocal::FindBody(World, Ship.GetActorLocation()))
		{
			const FVector Centre = Body->GetActorLocation();
			FVector Up = (Ship.GetActorLocation() - Centre).GetSafeNormal();
			if (Up.IsNearlyZero())
			{
				Up = FVector::UpVector;
			}
			// Keep where the ship is over the body and only change how high it flies.
			const double CurrentAltitude = Body->GetSurfaceDistance(Ship.GetActorLocation());
			const FVector Location = Ship.GetActorLocation() + Up * (Shot.AltitudeM * 100.0 - CurrentAltitude);
			const FVector Tangent = FVector::VectorPlaneProject(Ship.GetActorForwardVector(), Up).GetSafeNormal();
			FVector Forward = Tangent.IsNearlyZero() ? FVector::CrossProduct(Up, FVector::RightVector).GetSafeNormal() : Tangent;
			if (Shot.Facing.Equals(TEXT("planet"), ESearchCase::IgnoreCase))
			{
				Forward = -Up;
			}
			else if (Shot.Facing.Equals(TEXT("away"), ESearchCase::IgnoreCase))
			{
				Forward = Up;
			}
			Ship.SetActorLocationAndRotation(Location, FRotationMatrix::MakeFromXZ(Forward, Up).ToQuat(), false, nullptr, ETeleportType::TeleportPhysics);
			Ship.SnapCameraToShip();
		}
	}

	// "facing": "body:Orun" - the nose on a body by its display name (the quantum drive picks what the nose is on).
	if (Shot.Facing.StartsWith(TEXT("body:"), ESearchCase::IgnoreCase))
	{
		const FString Name = Shot.Facing.Mid(5);
		const AActor* Found = nullptr;
		for (TActorIterator<ACelestialBody> It(World); It && !Found; ++It)
		{
			Found = It->GetDisplayName().ToString().Equals(Name, ESearchCase::IgnoreCase) ? *It : nullptr;
		}
		for (TActorIterator<ADistantBody> It(World); It && !Found; ++It)
		{
			Found = It->GetDisplayName().ToString().Equals(Name, ESearchCase::IgnoreCase) ? *It : nullptr;
		}
		if (Found)
		{
			const FVector Forward = (Found->GetActorLocation() - Ship.GetActorLocation()).GetSafeNormal();
			Ship.SetActorRotation(FRotationMatrix::MakeFromXZ(Forward, Ship.GetActorUpVector()).ToQuat(), ETeleportType::TeleportPhysics);
			Ship.SnapCameraToShip();
		}
		else
		{
			UE_LOG(LogSpaceShots, Warning, TEXT("SHOTS no body called %s"), *Name);
		}
	}

	if (!Shot.MasterMode.IsEmpty())
	{
		Ship.RequestMasterMode(Shot.MasterMode.Equals(TEXT("NAV"), ESearchCase::IgnoreCase) ? EMasterMode::NAV : EMasterMode::SCM);
		Ship.DebugFinishMasterModeSwitch();
	}
	if (Shot.Limiter >= 0.f)
	{
		Ship.SetSpeedLimiter(Shot.Limiter);
	}
	if (Shot.Coupled >= 0)
	{
		Ship.SetFlightAssist(Shot.Coupled != 0);
	}
	if (Shot.GSafe >= 0)
	{
		Ship.SetGSafe(Shot.GSafe != 0);
	}
	if (Shot.ComStab >= 0)
	{
		Ship.SetComStab(Shot.ComStab != 0);
	}
	if (Shot.Gear >= 0)
	{
		Ship.DebugSetGearInstant(Shot.Gear != 0);
	}
	if (Shot.bLowerGear)
	{
		Ship.DebugSetGearInstant(false);
		Ship.SetGearDown(true);
	}
	if (Shot.Precision >= 0)
	{
		Ship.SetPrecisionMode(Shot.Precision != 0);
	}
	Ship.DebugSetChaseView(Shot.ChaseYaw, Shot.ChasePitch, Shot.ChaseZoom);
	Ship.SetBoostHeld(Shot.bBoost);
	Ship.SetAfterburnerHeld(Shot.bAfterburner);
	Ship.DebugSetMouseStick(Shot.Stick);
	Ship.DebugSetLinearVelocity(Shot.bHasDrift
		? Ship.GetActorQuat().RotateVector(Shot.Drift * 100.f)
		: Ship.GetActorForwardVector() * (Shot.SpeedMS * 100.f));
	if (!Shot.QuantumTarget.IsEmpty())
	{
		Ship.DebugEngageQuantum(Shot.QuantumTarget, Shot.QuantumProgress);
	}
	if (Shot.bQuantumReady)
	{
		Ship.DebugFinishQuantumCharge();
	}
	if (!Shot.CockpitEye.IsNearlyZero() || Shot.HideHull >= 0 || Shot.HideCanopy >= 0)
	{
		Ship.DebugConfigureCockpit(Shot.CockpitEye, Shot.HideHull > 0, Shot.HideCanopy != 0);
	}
	if (Shot.CockpitKeyCd >= 0.f || Shot.CockpitFillCd >= 0.f || Shot.DisplayLightCd >= 0.f || Shot.InteriorTint >= 0.f)
	{
		Ship.DebugSetCockpitLighting(Shot.CockpitKeyCd, Shot.CockpitFillCd, Shot.DisplayLightCd, Shot.InteriorTint);
	}
	Ship.SetCockpitView(Shot.Camera.Equals(TEXT("cockpit"), ESearchCase::IgnoreCase));
	ApplyFreeCamera(Shot, Ship);
}

void USpaceShotRunner::ApplyFreeCamera(const FSpaceShot& Shot, ASpaceshipPawn& Ship)
{
	APlayerController* Controller = Ship.GetWorld() ? Ship.GetWorld()->GetFirstPlayerController() : nullptr;
	if (!Controller)
	{
		return;
	}
	const bool bFree = Shot.bFreeCamera || Shot.Camera.Equals(TEXT("free"), ESearchCase::IgnoreCase);
	if (!bFree)
	{
		if (FreeCamera.IsValid())
		{
			// Back to the ship's own cameras for the shots that follow.
			Controller->SetViewTarget(&Ship);
			FreeCamera->Destroy();
			FreeCamera = nullptr;
		}
		return;
	}
	if (!FreeCamera.IsValid())
	{
		FreeCamera = Ship.GetWorld()->SpawnActor<ACameraActor>(ACameraActor::StaticClass());
	}
	if (!FreeCamera.IsValid())
	{
		return;
	}
	const FVector Look = Shot.CameraLookAt.IsNearlyZero() ? Ship.GetActorLocation() : Shot.CameraLookAt;
	FreeCamera->SetActorLocation(Shot.CameraLocation);
	FreeCamera->SetActorRotation((Look - Shot.CameraLocation).GetSafeNormal().Rotation());
	UCameraComponent* Camera = FreeCamera->GetCameraComponent();
	if (Shot.CameraFov > 0.f)
	{
		Camera->SetFieldOfView(Shot.CameraFov);
	}
	// Auto exposure quietly undoes whatever a shot is meant to measure: darken the material, and
	// the eye simply opens wider. A shot that says "exposure" pins it, the way the ship's own
	// camera does; without it the camera keeps adapting, as every earlier preset expects.
	FPostProcessSettings& Post = Camera->PostProcessSettings;
	const bool bPinned = Shot.Exposure > 0.f;
	Post.bOverride_AutoExposureMinBrightness = bPinned;
	Post.bOverride_AutoExposureMaxBrightness = bPinned;
	if (bPinned)
	{
		Post.AutoExposureMinBrightness = Shot.Exposure;
		Post.AutoExposureMaxBrightness = Shot.Exposure;
	}
	Controller->SetViewTarget(FreeCamera.Get());
}

void USpaceShotRunner::TakeSingleShot(const FString& Name)
{
	const FString Directory = OutputDirectory.IsEmpty() ? DefaultOutputDirectory() : OutputDirectory;
	IPlatformFile::GetPlatformPhysical().CreateDirectoryTree(*Directory);
	const FString File = FPaths::Combine(Directory, FString::Printf(TEXT("%02d_%s.png"), ManualShotCount++,
		Name.IsEmpty() ? TEXT("shot") : *Name));
	// With the UI: the flight HUD is usually the point of the picture.
	FScreenshotRequest::RequestScreenshot(File, true, false);
	UE_LOG(LogSpaceShots, Display, TEXT("SHOTS wrote %s"), *File);
}

void USpaceShotRunner::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
	if (ShotIndex == INDEX_NONE || !Shots.IsValidIndex(ShotIndex))
	{
		return;
	}
	ASpaceshipPawn* Ship = FindShip();
	if (!Ship)
	{
		return;  // still loading the level / spawning the pawn
	}

	if (bWaitingForFile)
	{
		Timer += DeltaTime;
		if (IPlatformFile::GetPlatformPhysical().FileExists(*PendingFile) || Timer > SpaceShotRunnerLocal::FileTimeout)
		{
			UE_LOG(LogSpaceShots, Display, TEXT("SHOTS %s %s"), *PendingFile,
				IPlatformFile::GetPlatformPhysical().FileExists(*PendingFile) ? TEXT("saved") : TEXT("MISSING (timed out)"));
			bWaitingForFile = false;
			Timer = 0.f;
			++ShotIndex;
			if (!Shots.IsValidIndex(ShotIndex))
			{
				UE_LOG(LogSpaceShots, Display, TEXT("SHOTS done, %d picture(s) in %s"), Shots.Num(), *OutputDirectory);
				if (bQuitWhenFinished)
				{
					FPlatformMisc::RequestExit(false);
				}
				ShotIndex = INDEX_NONE;
			}
			else
			{
				ApplyShot(Shots[ShotIndex], *Ship);
			}
		}
		return;
	}

	// First frame of this shot: set it up, then let it settle before the picture.
	if (Timer == 0.f)
	{
		ApplyShot(Shots[ShotIndex], *Ship);
	}
	Timer += DeltaTime;
	// Keep held inputs alive while it settles (boost and the afterburner are "held" states).
	Ship->SetBoostHeld(Shots[ShotIndex].bBoost);
	Ship->SetAfterburnerHeld(Shots[ShotIndex].bAfterburner);
	Ship->DebugSetMouseStick(Shots[ShotIndex].Stick);
	if (Timer >= Shots[ShotIndex].Settle)
	{
		PendingFile = FPaths::Combine(OutputDirectory, FString::Printf(TEXT("%02d_%s.png"), ShotIndex, *Shots[ShotIndex].Name));
		FScreenshotRequest::RequestScreenshot(PendingFile, true, false);
		bWaitingForFile = true;
		Timer = 0.f;
	}
}

namespace
{
	USpaceShotRunner* RunnerFor(UWorld* World)
	{
		return World ? World->GetSubsystem<USpaceShotRunner>() : nullptr;
	}

	FAutoConsoleCommandWithWorldAndArgs ShotCommand(
		TEXT("space.Shot"),
		TEXT("Saves a picture of the current view to Saved/Shots (space.Shot [name])."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			if (USpaceShotRunner* Runner = RunnerFor(World))
			{
				Runner->TakeSingleShot(Args.Num() > 0 ? Args[0] : FString());
			}
		}));

	FAutoConsoleCommandWithWorldAndArgs ShotsCommand(
		TEXT("space.Shots"),
		TEXT("Runs a shot list from here (space.Shots <path to a Tools/Shots/*.json>)."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			USpaceShotRunner* Runner = RunnerFor(World);
			if (Runner && Args.Num() > 0)
			{
				Runner->RunShotList(Args[0], Args.Num() > 1 ? Args[1] : USpaceShotRunner::DefaultOutputDirectory(), false);
			}
		}));
}
