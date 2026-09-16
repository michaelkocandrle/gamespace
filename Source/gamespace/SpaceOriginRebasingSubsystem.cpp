// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceOriginRebasingSubsystem.h"

#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "Misc/CoreDelegates.h"
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
