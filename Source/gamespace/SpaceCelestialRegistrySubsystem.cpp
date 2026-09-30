// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceCelestialRegistrySubsystem.h"

#include "CelestialBody.h"
#include "DistantBody.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"

namespace SpaceCelestialRegistry
{
	/** Registers once; the same actor can re-register its components (editor moves, construction scripts). */
	template <typename TBody>
	void Add(TArray<TWeakObjectPtr<TBody>>& Bodies, TBody* Body)
	{
		if (Body && !Body->IsTemplate() && !Bodies.Contains(TWeakObjectPtr<TBody>(Body)))
		{
			Bodies.Emplace(Body);
		}
	}

	template <typename TBody>
	void Remove(TArray<TWeakObjectPtr<TBody>>& Bodies, TBody* Body)
	{
		Bodies.Remove(TWeakObjectPtr<TBody>(Body));
	}

	/** Live bodies of this world only; drops the destroyed ones on the way (keeps the order). */
	template <typename TBody>
	void Visit(TArray<TWeakObjectPtr<TBody>>& Bodies, const UWorld* World, TFunctionRef<void(TBody&)> Function)
	{
		Bodies.RemoveAll([](const TWeakObjectPtr<TBody>& Body) { return !IsValid(Body.Get()); });
		// Function may register or unregister bodies (a spawn in a callback); walk a copy.
		const TArray<TWeakObjectPtr<TBody>> Snapshot = Bodies;
		for (const TWeakObjectPtr<TBody>& Weak : Snapshot)
		{
			TBody* Body = Weak.Get();
			if (IsValid(Body) && Body->GetWorld() == World && !Body->IsActorBeingDestroyed())
			{
				Function(*Body);
			}
		}
	}
}

USpaceCelestialRegistrySubsystem* USpaceCelestialRegistrySubsystem::Get(const UWorld* World)
{
	return World ? World->GetSubsystem<USpaceCelestialRegistrySubsystem>() : nullptr;
}

void USpaceCelestialRegistrySubsystem::Register(ACelestialBody* Body)
{
	SpaceCelestialRegistry::Add(CelestialBodies, Body);
}

void USpaceCelestialRegistrySubsystem::Unregister(ACelestialBody* Body)
{
	SpaceCelestialRegistry::Remove(CelestialBodies, Body);
}

void USpaceCelestialRegistrySubsystem::Register(ADistantBody* Body)
{
	SpaceCelestialRegistry::Add(DistantBodies, Body);
}

void USpaceCelestialRegistrySubsystem::Unregister(ADistantBody* Body)
{
	SpaceCelestialRegistry::Remove(DistantBodies, Body);
}

void USpaceCelestialRegistrySubsystem::SeedOnce()
{
	if (bSeeded)
	{
		return;
	}
	bSeeded = true;
	if (const UWorld* World = GetWorld())
	{
		for (TActorIterator<ACelestialBody> It(World); It; ++It)
		{
			SpaceCelestialRegistry::Add(CelestialBodies, *It);
		}
		for (TActorIterator<ADistantBody> It(World); It; ++It)
		{
			SpaceCelestialRegistry::Add(DistantBodies, *It);
		}
	}
}

void USpaceCelestialRegistrySubsystem::ForEachCelestialBody(TFunctionRef<void(ACelestialBody&)> Callback)
{
	SeedOnce();
	SpaceCelestialRegistry::Visit<ACelestialBody>(CelestialBodies, GetWorld(), Callback);
}

void USpaceCelestialRegistrySubsystem::ForEachDistantBody(TFunctionRef<void(ADistantBody&)> Callback)
{
	SeedOnce();
	SpaceCelestialRegistry::Visit<ADistantBody>(DistantBodies, GetWorld(), Callback);
}

ACelestialBody* USpaceCelestialRegistrySubsystem::FindNearestCelestialBody(const FVector& Location)
{
	ACelestialBody* Nearest = nullptr;
	double NearestDistance = TNumericLimits<double>::Max();
	ForEachCelestialBody([&](ACelestialBody& Body)
	{
		const double Distance = Body.GetSurfaceDistance(Location);
		if (Distance < NearestDistance)
		{
			NearestDistance = Distance;
			Nearest = &Body;
		}
	});
	return Nearest;
}

int32 USpaceCelestialRegistrySubsystem::DebugCountRegisteredBodies(const UObject* WorldContextObject, bool bDistant)
{
	const UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::LogAndReturnNull) : nullptr;
	USpaceCelestialRegistrySubsystem* Registry = Get(World);
	if (!Registry)
	{
		return -1;
	}
	int32 Count = 0;
	if (bDistant)
	{
		Registry->ForEachDistantBody([&Count](ADistantBody&) { ++Count; });
	}
	else
	{
		Registry->ForEachCelestialBody([&Count](ACelestialBody&) { ++Count; });
	}
	return Count;
}

void USpaceCelestialRegistrySubsystem::Deinitialize()
{
	CelestialBodies.Reset();
	DistantBodies.Reset();
	bSeeded = false;
	Super::Deinitialize();
}
