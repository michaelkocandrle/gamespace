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

	/** Landing gear down and locked (SC-2a). */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	bool bGearDown = false;

	/** Gear on its way down or up. */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	bool bGearMoving = false;

	/** Low over the ground with the gear up: touchdown is blocked until it comes down. */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	bool bGearWarning = false;

	/** Precision mode switched on (gear or P). */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	bool bPrecisionOn = false;

	/** Precision mode in effect (on, and in SCM). */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	bool bPrecisionActive = false;
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

	/** What is drawn: eases towards Value, so a jump in speed springs rather than snaps. */
	UPROPERTY(BlueprintReadOnly, Category = "Gauge")
	float Display = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "Gauge")
	float DisplayReverse = 0.f;

	/** Breathing of the halo, 0..1, driven by the HUD's clock. */
	UPROPERTY(BlueprintReadOnly, Category = "Gauge")
	float Pulse = 1.f;

	/** One step of the easing. Driven by the HUD so tests can step it without Slate. */
	void Advance(float DeltaSeconds);

protected:
	virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
};

/**
 * A panel outline in the Star Citizen style: thin lines with cut corners around a barely tinted
 * fill, drawn by the widget itself (UMG borders can only do square or rounded corners).
 */
UCLASS()
class GAMESPACE_API USpaceHudPanel : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Corner cut, pixels. */
	UPROPERTY(BlueprintReadOnly, Category = "Panel")
	float Chamfer = 10.f;

	UPROPERTY(BlueprintReadOnly, Category = "Panel")
	FLinearColor LineColor = FLinearColor::White;

	/** Fill behind the content. 0 by default: the reference frames groups with brackets over the bare view. */
	UPROPERTY(BlueprintReadOnly, Category = "Panel")
	float FillAlpha = 0.f;

	/** Halo strength around the lines, 0..1. */
	UPROPERTY(BlueprintReadOnly, Category = "Panel")
	float Glow = 0.5f;

protected:
	virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
};

/** A status lamp: a small glowing square that fades in and out and flashes when it changes. */
UCLASS()
class GAMESPACE_API USpaceHudLamp : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Where the lamp is heading: 1 lit, 0 dark. */
	UPROPERTY(BlueprintReadOnly, Category = "Lamp")
	float Target = 0.f;

	/** What is drawn, easing towards Target. */
	UPROPERTY(BlueprintReadOnly, Category = "Lamp")
	float Intensity = 0.f;

	/** Extra brightness right after a change, decaying. */
	UPROPERTY(BlueprintReadOnly, Category = "Lamp")
	float Flash = 0.f;

	/** Breathing of the halo while lit, 0..1, driven by the HUD's clock. */
	UPROPERTY(BlueprintReadOnly, Category = "Lamp")
	float Pulse = 1.f;

	UPROPERTY(BlueprintReadOnly, Category = "Lamp")
	FLinearColor Color = FLinearColor::White;

	/** Largest size of the state square, pixels: 6 on the HUD, bigger on the cockpit displays, which are seen small. */
	UPROPERTY(BlueprintReadOnly, Category = "Lamp")
	float SquareMax = 6.f;

	/** Sets where the lamp should go; a change starts a short flash. */
	void SetTarget(bool bLit, const FLinearColor& InColor);

	/** One animation step. Driven by the HUD so tests can step it without Slate. */
	void Advance(float DeltaSeconds);

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
 * - Left of centre: status lamps (SCM/NAV, CPLD, GSAF, CSTB, BOOST, GEAR, PREC) beside the vertical speed
 *   gauge (fill = speed along the nose, marker = speed limiter, red reverse zone at the bottom), speed and
 *   limit as small numbers under it, and the G meter tied to it. Compact and a little above the middle,
 *   so it stays above the cockpit's dashboard.
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

	/** Tests: whether the status lamp (CPLD, GSAF, CSTB, BOOST, MODE, GEAR, PREC) is lit, and its colour. */
	UFUNCTION(BlueprintCallable, Category = "Flight HUD|Tests")
	bool DebugIsLampLit(FName Lamp, FLinearColor& OutColor) const;

	/** Tests: a text widget, for its font. */
	UFUNCTION(BlueprintCallable, Category = "Flight HUD|Tests")
	UTextBlock* DebugGetTextWidget(FName TextName) const;

	/** Tests: a status lamp, for its animation state. */
	UFUNCTION(BlueprintCallable, Category = "Flight HUD|Tests")
	USpaceHudLamp* DebugGetLamp(FName Lamp) const;

	/** Tests: runs the HUD's animations for this long, without Slate. */
	UFUNCTION(BlueprintCallable, Category = "Flight HUD|Tests")
	void DebugAdvance(float Seconds);

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

	/** Builds the widget tree. The widgets' names are what ApplyState drives, whatever the layout. */
	virtual void BuildTree();
	/** Monospace (the engine's DroidSansMono), letter-spaced and outlined: a technical, readable look. */
	UTextBlock* MakeText(const FName Name, float Size, int32 LetterSpacing = 60, const FName Weight = TEXT("Mono"));

	UPROPERTY(Transient)
	TMap<FName, TObjectPtr<USpaceHudLamp>> Lamps;

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

/**
 * The cockpit's two dashboard displays: the flight HUD's instruments (same widgets, same names, so
 * USpaceFlightHud::ApplyState drives them) laid out for two screens side by side on one canvas of
 * 2 x DisplaySize. Left, FLIGHT: master mode, speed gauge, speed and limiter, G meter. Right, SYSTEMS:
 * the switch lamps (CPLD, GSAF, CSTB, BOOST, GEAR, PREC) and the boost and afterburner gauges.
 *
 * Big type and thick lines: a display is ~30 cm wide ~1.2 m from the eye, so the 512 px of one screen
 * shrink to ~200 on a 1600 px wide view. Never added to the viewport: UCockpitDisplayComponent draws it
 * into a render target and feeds it the ship's state.
 */
UCLASS()
class GAMESPACE_API USpaceCockpitDisplays : public USpaceFlightHud
{
	GENERATED_BODY()

public:
	/** One display, pixels (the render target is two of them side by side). */
	static constexpr float DisplayWidth = 512.f;
	static constexpr float DisplayHeight = 448.f;

protected:
	/** Driven by UCockpitDisplayComponent, not by a player: nothing to do per Slate tick. */
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
	virtual void BuildTree() override;
};
