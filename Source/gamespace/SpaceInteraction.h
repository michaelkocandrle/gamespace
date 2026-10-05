// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"

class APawn;

/** What a tap on F does here, and where: SC's prompt by the object ("SIT [F]", "OPEN [F]"). */
struct FSpaceInteractTarget
{
	/** SC's door prompt: the label set vertically along the door's edge beside the key. */
	bool bVertical = false;
	bool bValid = false;
	/** False: the action exists but cannot be done now (the ramp in flight); the prompt says why instead. */
	bool bAvailable = true;
	FText Label;
	FVector WorldLocation = FVector::ZeroVector;
};

/** A thing to click in interact mode (hold F): SC's cursor on physical screens and buttons. */
struct FSpaceHotspot
{
	FText Label;
	FVector WorldLocation = FVector::ZeroVector;
	/** Left click (true) or right click (false). */
	TFunction<void(bool bPrimary)> Use;
	/** What the right click does, if anything (shown under the label). */
	FText SecondaryLabel;
	/** Where the label goes instead of just above the control (a control on a display: over its frame, so the label
	 * never covers the page). */
	bool bLabelAnchor = false;
	FVector LabelWorldLocation = FVector::ZeroVector;
	/** The control's size, cm: the highlight frames it (SC lights the control itself, no marker dot). */
	float SizeCm = 6.f;
};

/** One line of SC's context key list at the bottom right: "ACTION [key]". */
struct FSpaceKeyHint
{
	FText Action;
	FString Key;
};

/**
 * Interaction after Star Citizen (step 1 after the author's own captures, 4. 10. 2026): a tap on F does the default
 * action of the target shown by its object, holding F turns on interact mode with a cursor and clickable hotspots,
 * and a list at the bottom right says which keys do what right now. These gather it for the pawn being played; the
 * player controller drives F and the cursor, the interaction overlay draws it.
 */
namespace SpaceInteraction
{
	/** The tap target and the interact-mode hotspots for this pawn. */
	GAMESPACE_API void Gather(APawn* Pawn, FSpaceInteractTarget& OutTarget, TArray<FSpaceHotspot>& OutHotspots);

	/** The key list for this pawn and state. */
	GAMESPACE_API void KeyHints(APawn* Pawn, bool bInteractMode, const FSpaceInteractTarget& Target, TArray<FSpaceKeyHint>& Out);

	/** A tap on F: the default action (sit, get up, step outside, board, get out). */
	GAMESPACE_API void Interact(APawn* Pawn);
}
