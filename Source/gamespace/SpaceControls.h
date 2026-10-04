// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "SpaceControls.generated.h"

/** Where a control works: in a ship, on foot, or everywhere. */
enum class ESpaceControlMode : uint8
{
	Flight,
	OnFoot,
	Global
};

/** What a control is about; the keybinding page colours it by this (after SC's categories). */
enum class ESpaceControlCategory : uint8
{
	Movement,
	Systems,
	Landing,
	Camera,
	Navigation,
	Interaction,
	Interface,
	Count
};

/** One control as the keybinding page shows it. */
struct FSpaceControl
{
	ESpaceControlMode Mode = ESpaceControlMode::Flight;
	/** The key (an FKey name: "W", "SpaceBar", "LeftMouseButton", "MouseWheelAxis", "Mouse2D"). */
	FName Key;
	/** Held with Alt (the code reads Alt itself: Alt + wheel zooms, Alt + F1 goes back on the MFD). */
	bool bAlt = false;
	/** What it does, in Czech; a line break where the key cap needs one. */
	FText Label;
	ESpaceControlCategory Category = ESpaceControlCategory::Interface;
	/** The input action it is mapped to in /Game/Input (empty when the code maps it), for the test against the assets. */
	FName Action;
};

/**
 * The game's controls in one table, for the settings page's KLÁVESY tab (SC's KEYBINDINGS: a picture of the keyboard
 * and the mouse with every bound key). The keys themselves live in the mapping contexts in /Game/Input and in the code
 * that adds runtime ones (the controller's global keys, the ship's fallbacks); Tools/Tests/test_menu_settings.py checks
 * this table against IMC_Spaceship and IMC_Character, so it cannot drift from them.
 */
struct GAMESPACE_API FSpaceControls
{
	static const TArray<FSpaceControl>& Get();
	static FLinearColor CategoryColor(ESpaceControlCategory Category);
	static FText CategoryName(ESpaceControlCategory Category);
};

/** Tests: the controls table as text. */
UCLASS()
class GAMESPACE_API USpaceControlsLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/** One line per control: "<mode>|<key>|<alt 0/1>|<action>|<label>" with mode flight / onfoot / global. */
	UFUNCTION(BlueprintCallable, Category = "Spaceship|Tests")
	static TArray<FString> DescribeControls();
};
