// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "SpaceNotifications.generated.h"

/**
 * SC's two kinds of message (starcitizenreference/OwnCapture_Gameplay_Notes.md): a toast, a dark pill at the top centre
 * for an event ("Hangar Request Completed", joining the ship's channel), and a hint card at the right edge that
 * explains a mechanic the first time it matters (QUANTUM DRIVE - SPOOLING, PLAYER TEMPERATURE). The interaction
 * overlay draws them; anything can push one. Hints show once per run and only with the Rozhraní - tipy setting on.
 */
UCLASS()
class GAMESPACE_API USpaceNotifications : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	struct FEntry
	{
		FText Title;
		FText Body;
		double StartSeconds = 0.0;
		float Seconds = 5.f;
	};

	static USpaceNotifications* Get(const UObject* WorldContext);

	/** A toast at the top centre for Seconds. */
	void Toast(const FText& Text, float Seconds = 5.f);

	/** A hint card at the right edge, once per run per Id; false when it was shown before or hints are off. */
	bool Hint(FName Id, const FText& Title, const FText& Body, float Seconds = 14.f);

	/** The toasts and hint cards still on screen (expired ones are dropped). */
	const TArray<FEntry>& GetToasts();
	const TArray<FEntry>& GetHints();

	/** Tests: push a toast or a hint (the hint ignores the once-per-run rule and the setting). */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Tests")
	void DebugToast(const FString& Text) { Toast(FText::FromString(Text)); }
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Tests")
	void DebugHint(const FString& Title, const FString& Body);
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Tests")
	int32 DebugCountToasts() { return GetToasts().Num(); }
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Tests")
	int32 DebugCountHints() { return GetHints().Num(); }
	/** Tests: whether a hint id was already shown this run. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Tests")
	bool DebugWasHintShown(FName Id) const { return Shown.Contains(Id); }

private:
	static double Now();
	static void Prune(TArray<FEntry>& Entries);

	TArray<FEntry> Toasts;
	TArray<FEntry> Hints;
	TSet<FName> Shown;
};
