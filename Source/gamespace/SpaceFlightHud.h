// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "SpaceFlightHud.generated.h"

class ASpaceshipPawn;
class UBorder;
class UTextBlock;

/**
 * Everything the flight HUD shows, read from the ship in one place. The widgets only display this,
 * so what they show can be checked headless without drawing anything.
 */
USTRUCT(BlueprintType)
struct GAMESPACE_API FSpaceFlightHudState
{
	GENERATED_BODY()

	/** A ship is flown and the HUD is not hidden (H). */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	bool bVisible = false;

	/** "SCM" or "NAV": the mode in force, or the one being switched to. */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	FString ModeLabel;

	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	bool bNav = false;

	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	bool bModeSwitching = false;

	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	float ModeSwitchProgress = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	bool bCoupled = false;

	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	bool bSpaceBrake = false;

	/** G-Safe switched on (K). */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	bool bGSafeOn = false;

	/** G-Safe on and not suspended by boost. */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	bool bGSafeActive = false;

	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	bool bComStab = false;

	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	bool bBoostActive = false;

	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	bool bBoostLocked = false;

	/** 0..1. */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	float BoostEnergy = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	bool bAfterburnerActive = false;

	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	bool bAfterburnerLocked = false;

	/** SCM: the afterburner can be used in this master mode. */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	bool bAfterburnerAvailable = false;

	/** 0..1. */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	float AfterburnerFuel = 0.f;

	/** Speed along the flight path, cm/s. */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	float SpeedCmS = 0.f;

	/** Speed along the nose, cm/s; negative flying backwards. */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	float ForwardSpeedCmS = 0.f;

	/** Speed limit in force (limiter, afterburner), cm/s. */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	float SpeedLimitCmS = 0.f;

	/** What the full speed gauge stands for: the mode's top speed, raised while the afterburner is in. */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	float GaugeScaleCmS = 1.f;

	/** Forward speed on the gauge's positive part, 0..1 (the gauge's upper part). */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	float SpeedFraction = 0.f;

	/** Backward speed on the gauge's reverse zone, 0..1. */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	float ReverseFraction = 0.f;

	/** The limiter's mark on the gauge, 0..1 of the positive part. */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	float LimiterFraction = 1.f;

	/** Faster than the limiter allows (braking down to it). */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	bool bOverLimit = false;

	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	float GForce = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	float GSafeMaxG = 7.f;

	/** The mouse virtual joystick is shown (flying, not free looking, not landed, not the old spring stick). */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	bool bShowVirtualJoystick = false;

	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	FVector2D Stick = FVector2D::ZeroVector;

	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	float Deadzone = 0.f;
};

/**
 * A thin line gauge drawn by the widget itself: frame, ticks, a fill from a zero line, an optional
 * reverse zone below it and a marker. Vertical (speed, boost, afterburner) or horizontal (G load).
 */
UCLASS()
class GAMESPACE_API USpaceHudGauge : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Filled part above the zero line, 0..1. */
	UPROPERTY(BlueprintReadOnly, Category = "Gauge")
	float Value = 0.f;

	/** Filled part of the reverse zone below the zero line, 0..1. */
	UPROPERTY(BlueprintReadOnly, Category = "Gauge")
	float ReverseValue = 0.f;

	/** Share of the length taken by the reverse zone (0: none, the gauge starts at its end). */
	UPROPERTY(BlueprintReadOnly, Category = "Gauge")
	float ReverseZone = 0.f;

	/** Marker position above the zero line, 0..1; negative: no marker. */
	UPROPERTY(BlueprintReadOnly, Category = "Gauge")
	float Marker = -1.f;

	UPROPERTY(BlueprintReadOnly, Category = "Gauge")
	FLinearColor FillColor = FLinearColor::Green;

	UPROPERTY(BlueprintReadOnly, Category = "Gauge")
	FLinearColor MarkerColor = FLinearColor::White;

	/** Frame and ticks drawn fainter (system unavailable). */
	UPROPERTY(BlueprintReadOnly, Category = "Gauge")
	bool bDim = false;

	UPROPERTY(BlueprintReadOnly, Category = "Gauge")
	bool bHorizontal = false;

	UPROPERTY(BlueprintReadOnly, Category = "Gauge")
	int32 Ticks = 10;

protected:
	virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
};

/** The mouse virtual joystick: rim (full turn rate), dead zone and the cursor. */
UCLASS()
class GAMESPACE_API USpaceHudVirtualJoystick : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Cursor inside the unit circle, X right, Y up. */
	UPROPERTY(BlueprintReadOnly, Category = "Virtual Joystick")
	FVector2D Stick = FVector2D::ZeroVector;

	/** Dead zone radius as a fraction of the rim. */
	UPROPERTY(BlueprintReadOnly, Category = "Virtual Joystick")
	float Deadzone = 0.06f;

protected:
	virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
};

/**
 * SC-1c flight HUD in UMG, after Docs/UI/SC_ThrottleHUD_VisualReference.md: thin, translucent cyan
 * lines around the middle of the screen instead of panels.
 *
 * - Left of centre: status lamps (SCM/NAV, CPLD, GSAF, CSTB, BOOST), the vertical speed gauge
 *   (fill = speed along the nose, marker = speed limiter, red reverse zone at the bottom), speed and
 *   limit as small numbers under it, and the G meter tied to it.
 * - Right of centre: boost energy and afterburner fuel gauges in the same style.
 * - Centre: the mouse virtual joystick.
 *
 * Built entirely in C++ (no widget Blueprint asset): the widget tree is constructed in Initialize.
 * ASpaceDebugHUD adds it to the viewport; it follows the controlled ship every tick and hides with
 * H (space.Hud 0) or when no ship is flown. The rest of the debug readout stays text until SC-3.
 */
UCLASS()
class GAMESPACE_API USpaceFlightHud : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual bool Initialize() override;

	/** What the HUD shows for this ship (null: nothing, not visible). The widgets display exactly this. */
	UFUNCTION(BlueprintCallable, Category = "Flight HUD")
	static FSpaceFlightHudState MakeState(const ASpaceshipPawn* Ship, int32 HudMode);

	/** Pushes a state into the widgets. Called every tick; public for tests. */
	UFUNCTION(BlueprintCallable, Category = "Flight HUD")
	void ApplyState(const FSpaceFlightHudState& State);

	/** Tests: builds the widget tree if Initialize has not (no player needed). */
	UFUNCTION(BlueprintCallable, Category = "Flight HUD|Tests")
	void DebugInitialize() { Initialize(); }

	/** Tests: names of every widget in the tree. */
	UFUNCTION(BlueprintCallable, Category = "Flight HUD|Tests")
	TArray<FString> DebugGetWidgetNames() const;

	/** Tests: whether the status lamp (CPLD, GSAF, CSTB, BOOST, MODE) is lit, and its colour. */
	UFUNCTION(BlueprintCallable, Category = "Flight HUD|Tests")
	bool DebugIsLampLit(FName Lamp, FLinearColor& OutColor) const;

	/** Tests: the text of a text widget (ModeText, SpeedText, LimitText, GText, BoostText, AfterburnerText). */
	UFUNCTION(BlueprintCallable, Category = "Flight HUD|Tests")
	FString DebugGetText(FName TextName) const;

	/** Tests: a gauge (SpeedGauge, GGauge, BoostGauge, AfterburnerGauge). */
	UFUNCTION(BlueprintCallable, Category = "Flight HUD|Tests")
	USpaceHudGauge* DebugGetGauge(FName GaugeName) const;

	UFUNCTION(BlueprintCallable, Category = "Flight HUD|Tests")
	USpaceHudVirtualJoystick* DebugGetVirtualJoystick() const { return VirtualJoystick; }

	/** Share of the speed gauge's length below zero, for flying backwards. */
	static constexpr float SpeedReverseZone = 0.12f;

	/** Full length of the G meter, G. */
	static constexpr float GMeterRangeG = 12.f;

protected:
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

private:
	void BuildTree();
	UTextBlock* MakeText(const FName Name, float Size, const FName Weight = TEXT("Bold"));

	UPROPERTY(Transient)
	TMap<FName, TObjectPtr<UBorder>> Lamps;

	UPROPERTY(Transient)
	TMap<FName, TObjectPtr<UTextBlock>> LampLabels;

	UPROPERTY(Transient)
	TMap<FName, TObjectPtr<UTextBlock>> Texts;

	UPROPERTY(Transient)
	TMap<FName, TObjectPtr<USpaceHudGauge>> Gauges;

	UPROPERTY(Transient)
	TObjectPtr<USpaceHudVirtualJoystick> VirtualJoystick;

	UPROPERTY(Transient)
	TObjectPtr<UWidget> VirtualJoystickBox;

	TMap<FName, bool> LampLit;
	float Time = 0.f;
};
