// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceNotifications.h"

#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "HAL/PlatformTime.h"
#include "SpaceUserSettings.h"

namespace SpaceNotificationsLocal
{
	/** On screen at once: SC stacks a couple; more would cover the view. */
	constexpr int32 MaxToasts = 3;
	constexpr int32 MaxHints = 2;
}

USpaceNotifications* USpaceNotifications::Get(const UObject* WorldContext)
{
	const UWorld* World = WorldContext ? WorldContext->GetWorld() : nullptr;
	const UGameInstance* Instance = World ? World->GetGameInstance() : nullptr;
	return Instance ? Instance->GetSubsystem<USpaceNotifications>() : nullptr;
}

double USpaceNotifications::Now()
{
	return FPlatformTime::Seconds();
}

void USpaceNotifications::Prune(TArray<FEntry>& Entries)
{
	const double Time = Now();
	Entries.RemoveAll([Time](const FEntry& Entry) { return Time - Entry.StartSeconds > Entry.Seconds; });
}

void USpaceNotifications::Toast(const FText& Text, float Seconds)
{
	Prune(Toasts);
	if (Toasts.Num() >= SpaceNotificationsLocal::MaxToasts)
	{
		Toasts.RemoveAt(0);
	}
	FEntry Entry;
	Entry.Title = Text;
	Entry.StartSeconds = Now();
	Entry.Seconds = Seconds;
	Toasts.Add(Entry);
}

bool USpaceNotifications::Hint(FName Id, const FText& Title, const FText& Body, float Seconds)
{
	const USpaceUserSettings* Settings = USpaceUserSettings::Get();
	if (Shown.Contains(Id) || (Settings && !Settings->bShowHints))
	{
		return false;
	}
	Shown.Add(Id);
	Prune(Hints);
	if (Hints.Num() >= SpaceNotificationsLocal::MaxHints)
	{
		Hints.RemoveAt(0);
	}
	FEntry Entry;
	Entry.Title = Title;
	Entry.Body = Body;
	Entry.StartSeconds = Now();
	Entry.Seconds = Seconds;
	Hints.Add(Entry);
	return true;
}

void USpaceNotifications::DebugHint(const FString& Title, const FString& Body)
{
	FEntry Entry;
	Entry.Title = FText::FromString(Title);
	Entry.Body = FText::FromString(Body);
	Entry.StartSeconds = Now();
	Entry.Seconds = 14.f;
	Hints.Add(Entry);
}

const TArray<USpaceNotifications::FEntry>& USpaceNotifications::GetToasts()
{
	Prune(Toasts);
	return Toasts;
}

const TArray<USpaceNotifications::FEntry>& USpaceNotifications::GetHints()
{
	Prune(Hints);
	return Hints;
}
