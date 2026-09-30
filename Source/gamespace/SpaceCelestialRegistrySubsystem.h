// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "SpaceCelestialRegistrySubsystem.generated.h"

class ACelestialBody;
class ADistantBody;

/**
 * The bodies of one world - the terrain planets (ACelestialBody) and the backdrop bodies (ADistantBody) - kept in
 * a list instead of walking every actor. Asked every frame by the ship (environment, quantum target and
 * obstruction), the character and the sky (ACelestialBody::FindNearest), by origin rebasing, and five times a
 * second by the cockpit radar (audit v1, 30. 9. 2026).
 *
 * Bodies register when their components register and leave when they unregister (Post(Un)RegisterAllComponents),
 * which covers spawning, level loading and streaming in game, PIE and editor worlds - the headless tests spawn
 * bodies in the editor world. The first query also walks the world once, for bodies whose components registered
 * before this subsystem existed. Entries are weak: a destroyed body drops out on the next query.
 *
 * World types without subsystems (editor previews, inactive worlds) have no registry; callers fall back to
 * walking the world there.
 *
 * Only the bodies: ships, characters and other radar contacts are not registered yet (design of a general
 * registry for ships and targets: Docs/Reviews/2026-09-30_registry_design.md).
 */
UCLASS()
class GAMESPACE_API USpaceCelestialRegistrySubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	/** The registry of World, or null where the world type has no subsystems. */
	static USpaceCelestialRegistrySubsystem* Get(const UWorld* World);

	void Register(ACelestialBody* Body);
	void Unregister(ACelestialBody* Body);
	void Register(ADistantBody* Body);
	void Unregister(ADistantBody* Body);

	/** Every live terrain body, in registration order. */
	void ForEachCelestialBody(TFunctionRef<void(ACelestialBody&)> Visit);

	/** Every live backdrop body, in registration order. */
	void ForEachDistantBody(TFunctionRef<void(ADistantBody&)> Visit);

	/** The terrain body whose surface is nearest to Location, or null. */
	ACelestialBody* FindNearestCelestialBody(const FVector& Location);

	/** For tests: how many live bodies the registry of WorldContextObject's world holds (-1 without a registry). */
	UFUNCTION(BlueprintCallable, Category = "Celestial Registry", meta = (WorldContext = "WorldContextObject"))
	static int32 DebugCountRegisteredBodies(const UObject* WorldContextObject, bool bDistant);

	virtual void Deinitialize() override;

private:
	/** One walk of the world for bodies that registered before the subsystem existed. */
	void SeedOnce();

	TArray<TWeakObjectPtr<ACelestialBody>> CelestialBodies;
	TArray<TWeakObjectPtr<ADistantBody>> DistantBodies;
	bool bSeeded = false;
};
