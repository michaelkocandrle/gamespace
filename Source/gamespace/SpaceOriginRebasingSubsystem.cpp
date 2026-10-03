// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceOriginRebasingSubsystem.h"

#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "Misc/CoreDelegates.h"
#include "CelestialBody.h"
#include "SpaceGameMode.h"
#include "SpaceshipPawn.h"

DEFINE_LOG_CATEGORY_STATIC(LogSpaceOrigin, Log, All);

namespace SpaceOrigin
{
	constexpr double CmPerKm = 100000.0;

	/** The running game mode's settings, or the class defaults outside ASpaceGameMode. */
	const ASpaceGameMode* Settings(const UWorld* World)
	{
		const ASpaceGameMode* Mode = World ? Cast<ASpaceGameMode>(World->GetAuthGameMode()) : nullptr;
		return Mode ? Mode : GetDefault<ASpaceGameMode>();
	}

	APawn* PlayerPawn(const UWorld* World)
	{
		const APlayerController* PC = World ? World->GetFirstPlayerController() : nullptr;
		return PC ? PC->GetPawn() : nullptr;
	}

	FVector Absolute(const UWorld* World, const FVector& WorldLocation)
	{
		return FVector(World->OriginLocation) + WorldLocation;
	}
}

// -------------------------------------------------------------------------------------------
// Lifecycle
// -------------------------------------------------------------------------------------------

void USpaceOriginRebasingSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	PreOffsetHandle = FCoreDelegates::PreWorldOriginOffset.AddUObject(this, &USpaceOriginRebasingSubsystem::OnPreWorldOriginOffset);
	PostOffsetHandle = FCoreDelegates::PostWorldOriginOffset.AddUObject(this, &USpaceOriginRebasingSubsystem::OnPostWorldOriginOffset);
}

void USpaceOriginRebasingSubsystem::Deinitialize()
{
	FCoreDelegates::PreWorldOriginOffset.Remove(PreOffsetHandle);
	FCoreDelegates::PostWorldOriginOffset.Remove(PostOffsetHandle);
	Super::Deinitialize();
}

bool USpaceOriginRebasingSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	// Shifting an editor world would move the level being edited.
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

TStatId USpaceOriginRebasingSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(USpaceOriginRebasingSubsystem, STATGROUP_Tickables);
}

// -------------------------------------------------------------------------------------------
// Rebasing
// -------------------------------------------------------------------------------------------

void USpaceOriginRebasingSubsystem::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	// A request is applied at the start of the next world tick; don't stack another on top.
	if (!IsEnabled() || bRequestPending)
	{
		return;
	}

	const APawn* Pawn = GetLocalPlayerPawn();
	if (Pawn && Pawn->GetActorLocation().SizeSquared() > FMath::Square(GetRebaseDistanceCm()))
	{
		RequestOriginAt(Pawn->GetActorLocation());
	}
}

bool USpaceOriginRebasingSubsystem::RebaseNow()
{
	const APawn* Pawn = GetLocalPlayerPawn();
	return Pawn && RequestOriginAt(Pawn->GetActorLocation());
}

bool USpaceOriginRebasingSubsystem::RequestOriginAt(const FVector& WorldLocation)
{
	UWorld* World = GetWorld();
	const FIntVector Current = World->OriginLocation;

	// The origin is stored in int32 centimetres: compute in 64 bits and refuse what won't fit.
	const int64 X = int64(Current.X) + FMath::RoundToInt64(WorldLocation.X);
	const int64 Y = int64(Current.Y) + FMath::RoundToInt64(WorldLocation.Y);
	const int64 Z = int64(Current.Z) + FMath::RoundToInt64(WorldLocation.Z);
	const int64 Limit = MAX_int32;
	if (FMath::Abs(X) > Limit || FMath::Abs(Y) > Limit || FMath::Abs(Z) > Limit)
	{
		if (!bOutOfRange)
		{
			UE_LOG(LogSpaceOrigin, Warning,
				TEXT("Player is beyond +/-%.0f km of absolute zero; the world origin cannot follow (FIntVector limit). ")
				TEXT("Continuing without rebasing - positions stay double precision."), Limit / SpaceOrigin::CmPerKm);
		}
		bOutOfRange = true;
		return false;
	}
	bOutOfRange = false;

	const FIntVector NewOrigin{ static_cast<int32>(X), static_cast<int32>(Y), static_cast<int32>(Z) };
	if (NewOrigin == Current)
	{
		return false;
	}

	World->RequestNewWorldOrigin(NewOrigin);
	bRequestPending = true;
	return true;
}

void USpaceOriginRebasingSubsystem::OnPreWorldOriginOffset(UWorld* InWorld, FIntVector /*PreviousOrigin*/, FIntVector /*NewOrigin*/)
{
	if (InWorld == GetWorld())
	{
		OffsetStartSeconds = FPlatformTime::Seconds();
	}
}

void USpaceOriginRebasingSubsystem::OnPostWorldOriginOffset(UWorld* InWorld, FIntVector PreviousOrigin, FIntVector NewOrigin)
{
	if (InWorld != GetWorld())
	{
		return;
	}

	bRequestPending = false;
	++RebaseCount;
	LastRebaseMilliseconds = (FPlatformTime::Seconds() - OffsetStartSeconds) * 1000.0;
	LastShiftCm = FVector(NewOrigin - PreviousOrigin);
	LastRebaseRealTime = InWorld->GetRealTimeSeconds();

	if (SpaceOrigin::Settings(InWorld)->bLogRebases)
	{
		UE_LOG(LogSpaceOrigin, Log, TEXT("Rebase #%d: origin shifted by (%.3f, %.3f, %.3f) km to (%.3f, %.3f, %.3f) km in %.2f ms"),
			RebaseCount,
			LastShiftCm.X / SpaceOrigin::CmPerKm, LastShiftCm.Y / SpaceOrigin::CmPerKm, LastShiftCm.Z / SpaceOrigin::CmPerKm,
			NewOrigin.X / SpaceOrigin::CmPerKm, NewOrigin.Y / SpaceOrigin::CmPerKm, NewOrigin.Z / SpaceOrigin::CmPerKm,
			LastRebaseMilliseconds);
	}
}

// -------------------------------------------------------------------------------------------
// Queries
// -------------------------------------------------------------------------------------------

FIntVector USpaceOriginRebasingSubsystem::GetOriginLocation() const
{
	return GetWorld()->OriginLocation;
}

FVector USpaceOriginRebasingSubsystem::ToAbsolute(const FVector& WorldLocation) const
{
	return SpaceOrigin::Absolute(GetWorld(), WorldLocation);
}

FVector USpaceOriginRebasingSubsystem::ToWorld(const FVector& AbsoluteLocation) const
{
	return AbsoluteLocation - FVector(GetWorld()->OriginLocation);
}

bool USpaceOriginRebasingSubsystem::IsEnabled() const
{
	return SpaceOrigin::Settings(GetWorld())->bEnableOriginRebasing;
}

double USpaceOriginRebasingSubsystem::GetRebaseDistanceCm() const
{
	return SpaceOrigin::Settings(GetWorld())->RebaseDistanceKm * SpaceOrigin::CmPerKm;
}

double USpaceOriginRebasingSubsystem::GetSecondsSinceLastRebase() const
{
	return LastRebaseRealTime < 0.0 ? -1.0 : GetWorld()->GetRealTimeSeconds() - LastRebaseRealTime;
}

APawn* USpaceOriginRebasingSubsystem::GetLocalPlayerPawn() const
{
	return SpaceOrigin::PlayerPawn(GetWorld());
}

// -------------------------------------------------------------------------------------------
// Console commands (open the console in PIE with the key under Esc)
// -------------------------------------------------------------------------------------------

namespace SpaceOrigin
{
	void TeleportTo(UWorld* World, APawn* Pawn, const FVector& WorldLocation)
	{
		// Teleport keeps the velocity; the rebasing subsystem notices the distance next tick.
		Pawn->SetActorLocation(WorldLocation, false, nullptr, ETeleportType::TeleportPhysics);
		if (ASpaceshipPawn* Ship = Cast<ASpaceshipPawn>(Pawn))
		{
			Ship->SnapCameraToShip();
		}
		const FVector Abs = Absolute(World, WorldLocation);
		UE_LOG(LogSpaceOrigin, Log, TEXT("Teleported to absolute (%.3f, %.3f, %.3f) km"),
			Abs.X / CmPerKm, Abs.Y / CmPerKm, Abs.Z / CmPerKm);
	}

	static FAutoConsoleCommandWithWorldAndArgs TeleportForwardCommand(
		TEXT("space.TeleportForwardKm"),
		TEXT("space.TeleportForwardKm <km>: moves the player ship along its nose. Negative goes backwards."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			APawn* Pawn = PlayerPawn(World);
			if (!Pawn || Args.Num() < 1)
			{
				UE_LOG(LogSpaceOrigin, Warning, TEXT("usage: space.TeleportForwardKm <km> (needs a player pawn)"));
				return;
			}
			const double Km = FCString::Atod(*Args[0]);
			TeleportTo(World, Pawn, Pawn->GetActorLocation() + Pawn->GetActorForwardVector() * Km * CmPerKm);
		}));

	/**
	 * Moves the player's ship over the nearest ground whose slope (under the pads, 150 cm, and over the ship's length,
	 * 800 cm) lies in [MinDeg, MaxDeg], at the same height over it and level; with a yaw, the nose that far right of
	 * straight uphill. Rings of samples 100 m apart, nearest first. A slope (MinDeg > 0) must also be one plane:
	 * the normals at 150, 800 and 1100 cm within 2 degrees of each other.
	 */
	void MoveShipToSlope(UWorld* World, const TCHAR* Command, double MinDeg, double MaxDeg, TOptional<double> YawFromUphillDeg, double SearchKm)
	{
		APawn* Pawn = PlayerPawn(World);
		const ACelestialBody* Body = Pawn ? ACelestialBody::FindNearest(World, Pawn->GetActorLocation()) : nullptr;
		if (!Body)
		{
			UE_LOG(LogSpaceOrigin, Warning, TEXT("%s: needs a player pawn near a body"), Command);
			return;
		}
		const double SearchCm = SearchKm * CmPerKm;
		const FVector Centre = Body->GetActorLocation();
		const FVector Here = Pawn->GetActorLocation();
		const double Radius = (Here - Centre).Size();
		const FVector Up = (Here - Centre).GetSafeNormal();
		const double Height = Body->GetSurfaceDistance(Here);
		FVector T1 = FVector::VectorPlaneProject(Pawn->GetActorForwardVector(), Up).GetSafeNormal();
		FVector T2 = FVector::CrossProduct(Up, T1);
		if (T1.IsNearlyZero())
		{
			// the nose straight up or down (before a shot levels the ship): any two directions along the ground
			Up.FindBestAxisVectors(T1, T2);
		}
		// rings of samples 100 m apart, nearest first; the flattest one seen if none is flat enough
		constexpr double StepCm = 10000.0;
		double BestSlope = 90.0, BestRing = 0.0;
		int32 Samples = 0, Failed = 0;
		FVector BestSurface = FVector::ZeroVector, BestUp = Up;
		for (double Ring = 0.0; Ring <= SearchCm; Ring += StepCm)
		{
			const int32 Count = Ring <= 0.0 ? 1 : FMath::Max(6, int32(2.0 * PI * Ring / StepCm));
			for (int32 I = 0; I < Count; ++I)
			{
				const double A = 2.0 * PI * I / Count;
				const FVector Probe = Centre + ((Here + (T1 * FMath::Cos(A) + T2 * FMath::Sin(A)) * Ring) - Centre).GetSafeNormal() * Radius;
				// flat under the landing probe's footprint (150 cm) and over the ship's length (800 cm)
				FVector Surface, Normal, Wide;
				const FVector ProbeUp = (Probe - Centre).GetSafeNormal();
				++Samples;
				if (!Body->GetSurfaceFrame(Probe, 800.0, Surface, Wide) || !Body->GetSurfaceFrame(Probe, 150.0, Surface, Normal))
				{
					++Failed;
					continue;
				}
				auto SlopeOf = [&ProbeUp](const FVector& N) { return FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(FVector::DotProduct(N, ProbeUp), -1.0, 1.0))); };
				const double Slope = FMath::Max(SlopeOf(Normal), SlopeOf(Wide));
				const double Gentlest = FMath::Min(SlopeOf(Normal), SlopeOf(Wide));
				if (Slope < BestSlope)
				{
					BestSlope = Slope;
					BestRing = Ring;
					BestSurface = Surface;
					BestUp = ProbeUp;
				}
				if (Slope > MaxDeg || Gentlest < MinDeg)
				{
					continue;
				}
				if (MinDeg > 0.0)
				{
					// A slope, not a hollow or a ridge: one plane under the pads, over the ship's length and beyond
					// its ends (11 m), so the shot shows the slope and not the terrain's bumps.
					FVector Far, FarNormal;
					if (!Body->GetSurfaceFrame(Probe, 1100.0, Far, FarNormal)
						|| FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(FarNormal | Normal, -1.0, 1.0))) > 2.0
						|| FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(Wide | Normal, -1.0, 1.0))) > 2.0)
					{
						continue;
					}
				}
				FVector Forward = FVector::VectorPlaneProject(Pawn->GetActorForwardVector(), ProbeUp).GetSafeNormal();
				Forward = Forward.IsNearlyZero() ? FVector::VectorPlaneProject(T1, ProbeUp).GetSafeNormal() : Forward;
				const FVector Uphill = FVector::VectorPlaneProject(-Wide, ProbeUp).GetSafeNormal();
				if (YawFromUphillDeg.IsSet() && !Uphill.IsNearlyZero())
				{
					// Turning right about up: the nose YawFromUphillDeg right of straight up the slope.
					Forward = Uphill.RotateAngleAxis(YawFromUphillDeg.GetValue(), ProbeUp);
				}
				TeleportTo(World, Pawn, Surface + ProbeUp * Height);
				Pawn->SetActorRotation(FRotationMatrix::MakeFromXZ(Forward, ProbeUp).ToQuat(), ETeleportType::TeleportPhysics);
				UE_LOG(LogSpaceOrigin, Display, TEXT("%s: %.0f m away, slope %.1f-%.1f deg"), Command, Ring / 100.0, Gentlest, Slope);
				return;
			}
		}
		UE_LOG(LogSpaceOrigin, Warning, TEXT("%s: no slope of %.1f-%.1f deg within %.1f km, the flattest %.1f deg %.0f m away (%d samples, %d failed)"),
			Command, MinDeg, MaxDeg, SearchCm / CmPerKm, BestSlope, BestRing / 100.0, Samples, Failed);
		if (MinDeg <= 0.0 && BestSlope < 20.0)
		{
			FVector Forward = FVector::VectorPlaneProject(Pawn->GetActorForwardVector(), BestUp).GetSafeNormal();
			Forward = Forward.IsNearlyZero() ? FVector::VectorPlaneProject(T1, BestUp).GetSafeNormal() : Forward;
			TeleportTo(World, Pawn, BestSurface + BestUp * Height);
			Pawn->SetActorRotation(FRotationMatrix::MakeFromXZ(Forward, BestUp).ToQuat(), ETeleportType::TeleportPhysics);
		}
	}

	static FAutoConsoleCommandWithWorldAndArgs FlatSpotCommand(
		TEXT("space.FlatSpot"),
		TEXT("space.FlatSpot [max slope deg = 5] [search km = 3]: moves the player's ship over the nearest ground flatter than that, at the same height over it and level - for landing shots (walking the ship needs it landed)."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			const double MaxDeg = Args.Num() > 0 ? FCString::Atod(*Args[0]) : 5.0;
			const double SearchKm = Args.Num() > 1 ? FCString::Atod(*Args[1]) : 3.0;
			MoveShipToSlope(World, TEXT("space.FlatSpot"), 0.0, MaxDeg, TOptional<double>(), SearchKm);
		}));

	static FAutoConsoleCommandWithWorldAndArgs SlopeSpotCommand(
		TEXT("space.SlopeSpot"),
		TEXT("space.SlopeSpot <min deg> <max deg> [yaw deg = 0] [search km = 3]: moves the player's ship over the nearest ground with a slope in that range (under the pads and over the ship's length), at the same height over it and level, the nose yaw degrees right of straight uphill - for landing-on-a-slope shots."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			if (Args.Num() < 2)
			{
				UE_LOG(LogSpaceOrigin, Warning, TEXT("usage: space.SlopeSpot <min deg> <max deg> [yaw deg] [search km]"));
				return;
			}
			const double Yaw = Args.Num() > 2 ? FCString::Atod(*Args[2]) : 0.0;
			const double SearchKm = Args.Num() > 3 ? FCString::Atod(*Args[3]) : 3.0;
			MoveShipToSlope(World, TEXT("space.SlopeSpot"), FCString::Atod(*Args[0]), FCString::Atod(*Args[1]), Yaw, SearchKm);
		}));

	static FAutoConsoleCommandWithWorldAndArgs TeleportAbsoluteCommand(
		TEXT("space.TeleportAbsoluteKm"),
		TEXT("space.TeleportAbsoluteKm <x> <y> <z>: moves the player ship to an absolute position in km, independent of rebasing."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			APawn* Pawn = PlayerPawn(World);
			if (!Pawn || Args.Num() < 3)
			{
				UE_LOG(LogSpaceOrigin, Warning, TEXT("usage: space.TeleportAbsoluteKm <x> <y> <z> (needs a player pawn)"));
				return;
			}
			const FVector Abs(FCString::Atod(*Args[0]), FCString::Atod(*Args[1]), FCString::Atod(*Args[2]));
			TeleportTo(World, Pawn, Abs * CmPerKm - FVector(World->OriginLocation));
		}));

	static FAutoConsoleCommandWithWorld RebaseNowCommand(
		TEXT("space.RebaseNow"),
		TEXT("space.RebaseNow: moves the world origin to the player ship on the next tick, whatever the distance."),
		FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World)
		{
			USpaceOriginRebasingSubsystem* Rebasing = World ? World->GetSubsystem<USpaceOriginRebasingSubsystem>() : nullptr;
			if (!Rebasing || !Rebasing->RebaseNow())
			{
				UE_LOG(LogSpaceOrigin, Warning, TEXT("space.RebaseNow: nothing to do (not in a game world, no pawn, already at the origin, or out of range)"));
			}
		}));

	static FAutoConsoleCommandWithWorld PrintOriginCommand(
		TEXT("space.PrintOrigin"),
		TEXT("space.PrintOrigin: logs the world origin and the player ship position."),
		FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World)
		{
			if (!World)
			{
				return;
			}
			const FVector Origin(World->OriginLocation);
			UE_LOG(LogSpaceOrigin, Log, TEXT("Origin (%.3f, %.3f, %.3f) km"), Origin.X / CmPerKm, Origin.Y / CmPerKm, Origin.Z / CmPerKm);
			if (const APawn* Pawn = PlayerPawn(World))
			{
				const FVector Loc = Pawn->GetActorLocation();
				const FVector Abs = Absolute(World, Loc);
				UE_LOG(LogSpaceOrigin, Log, TEXT("Ship %.3f km from origin, absolute (%.3f, %.3f, %.3f) km"),
					Loc.Size() / CmPerKm, Abs.X / CmPerKm, Abs.Y / CmPerKm, Abs.Z / CmPerKm);
			}
		}));
}
