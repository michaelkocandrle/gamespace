// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "SpaceFlightHud.generated.h"

class ASpaceshipPawn;
class UBorder;
class UTextBlock;
class UWidgetSwitcher;

/**
 * Something on the cockpit radar, in the ship's own frame (plan view, the nose up). A celestial body
 * is only a bearing on the rim: it is kilometres away and larger than any radar range.
 */
USTRUCT(BlueprintType)
struct GAMESPACE_API FSpaceRadarContact
{
	GENERATED_BODY()

	/** Metres from the ship: X to the right, Y ahead. */
	UPROPERTY(BlueprintReadWrite, Category = "Radar")
	FVector2D Position = FVector2D::ZeroVector;

	/** Metres above (+) or below the ship's wings. */
	UPROPERTY(BlueprintReadWrite, Category = "Radar")
	float HeightM = 0.f;

	/** Metres to it (to the surface for a body). */
	UPROPERTY(BlueprintReadWrite, Category = "Radar")
	float DistanceM = 0.f;

	/** A planet or moon: drawn as a bearing on the rim, whatever the range. */
	UPROPERTY(BlueprintReadWrite, Category = "Radar")
	bool bBody = false;

	/** Name (bodies: their display name). */
	UPROPERTY(BlueprintReadWrite, Category = "Radar")
	FString Label;
};

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

	/** Second line under the master mode: FLIGHT, PREC, SPOOL (cruise charging) or CRUISE. */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	FString SubModeLabel;

	/** Landing gear for the HUD's status rows: UP, DOWN or MOVING. */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	FString GearLabel;

	/** Cruise for the HUD's status rows: OFF, SPOOL, ON or DROP. */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	FString CruiseLabel;

	/** Near a body: altitudes, climb rate, air and the horizon are known. */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	bool bHasEnvironment = false;

	/** Above sea level (the altitude tape) and above the terrain below (R-ALT), metres. */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	float AltitudeAslM = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	float AltitudeAglM = 0.f;

	/** Climb rate, m/s (VSI). */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	float VerticalSpeedMS = 0.f;

	/** Air density relative to sea level, 0..1 (ATMO). */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	float AtmosphereDensity = 0.f;

	/**
	 * Heading (0 north = the body's axis, 90 east), pitch (nose up +) and roll (right wing down +),
	 * degrees, against the local horizon. From the ship's nose; ApplyView replaces them with the view's.
	 */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	float HeadingDeg = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	float PitchDeg = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	float RollDeg = 0.f;

	/** Horizontal field of view the pitch ladder is projected with. */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	float ViewFovDeg = 90.f;

	/** Strafe input, -1..1: X right, Y up (the strafe cross's arrow heads). */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	FVector2D StrafeInput = FVector2D::ZeroVector;

	/** Drift across the nose, -1..1 of 50 m/s: X right, Y up (the strafe cross's dot). */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	FVector2D Drift = FVector2D::ZeroVector;

	/** Turn rate, -1..1 of the ship's top rate: X yaw right, Y pitch up (the gyro's rate line). */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	FVector2D TurnRate = FVector2D::ZeroVector;

	/**
	 * What the thrusters put out, ship-local G (X ahead / retro when negative, Y right, Z up), and what
	 * each direction can do right now: positive = main / right / up, negative = retro / left / down.
	 */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	FVector ThrustG = FVector::ZeroVector;

	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	FVector ThrustCapPositiveG = FVector::ZeroVector;

	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	FVector ThrustCapNegativeG = FVector::ZeroVector;

	/** How hard the engines work, 0..1 (the self status page's engines). */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	float EngineDemand = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	bool bLanded = false;

	/**
	 * The cockpit radar: contacts within RadarRangeM and the bodies' bearings. Filled by the cockpit
	 * displays only (USpaceCockpitDisplays::MakeRadarContacts); the HUD has no radar.
	 */
	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	TArray<FSpaceRadarContact> RadarContacts;

	UPROPERTY(BlueprintReadOnly, Category = "Flight HUD")
	float RadarRangeM = 5000.f;
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

	/** The lowest part of the fill, 0..1 of the gauge, is drawn in ReserveColor (the reference's red reserve). */
	UPROPERTY(BlueprintReadOnly, Category = "Gauge")
	float ReserveZone = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "Gauge")
	FLinearColor ReserveColor = FLinearColor::Red;

	/** More than 0: a column of this many blocks, as the reference's power bars, instead of a tube. */
	UPROPERTY(BlueprintReadOnly, Category = "Gauge")
	int32 Segments = 0;

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

	/** Drawn as the reference's switch badge: a thin outline round the label in the lamp's colour, no square. */
	UPROPERTY(BlueprintReadOnly, Category = "Lamp")
	bool bBadge = false;

	/** Drawn as one of the buttons beside the reference's MFDs (PWR, WPN, ...): a rounded key, filled when lit. */
	UPROPERTY(BlueprintReadOnly, Category = "Lamp")
	bool bButton = false;

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

/** What a USpaceHudSymbol draws. */
UENUM(BlueprintType)
enum class ESpaceHudSymbol : uint8
{
	/** Master mode: a ring with bars in it. */
	ModeIcon,
	/** Dotted cross with arrow heads, lit in the direction of the strafe input; a dot for the drift. */
	Strafe,
	/** Cross with a small ring at each end and the turn rate as a line from the middle. */
	Gyro,
	/** G-Safe: a shield with a G. */
	Shield,
	/** A small open ring (beside the afterburner percentage). */
	Ring,
	/** The nose reticle: four short ticks round a dot. */
	Reticle,
	/** A plus (beside the speed limiter). */
	Plus,
	/** A polyline through Points: the thin brackets beside the reference's text blocks. */
	Line,
	/** An MFD's glass: deep blue gradient, faint grid, darker edges, a soft reflection, a thin inner rim. */
	MfdGlass,
};

/** One of the Star Citizen HUD's drawn symbols (see ESpaceHudSymbol). */
UCLASS()
class GAMESPACE_API USpaceHudSymbol : public UUserWidget
{
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintReadOnly, Category = "Symbol")
	ESpaceHudSymbol Symbol = ESpaceHudSymbol::Line;

	UPROPERTY(BlueprintReadOnly, Category = "Symbol")
	FLinearColor Color = FLinearColor::White;

	/** Strafe arrow heads, the gyro's rate line. */
	UPROPERTY(BlueprintReadOnly, Category = "Symbol")
	FLinearColor Accent = FLinearColor::Red;

	/** Strafe: input; gyro: turn rate. -1..1, X right, Y up. */
	UPROPERTY(BlueprintReadOnly, Category = "Symbol")
	FVector2D Value = FVector2D::ZeroVector;

	/** Strafe: drift. -1..1, X right, Y up. */
	UPROPERTY(BlueprintReadOnly, Category = "Symbol")
	FVector2D Value2 = FVector2D::ZeroVector;

	/** Line: the points as fractions of the widget's size. */
	UPROPERTY(BlueprintReadOnly, Category = "Symbol")
	TArray<FVector2D> Points;

	UPROPERTY(BlueprintReadOnly, Category = "Symbol")
	float Thickness = 1.2f;

protected:
	virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
};

/**
 * A scale moving under a fixed mark: the heading tape (horizontal, labels above the ticks, the value
 * under a caret, wraps at 360) or the altitude tape (vertical, labels right of the ticks, the value in
 * a box at the mark).
 */
UCLASS()
class GAMESPACE_API USpaceHudTape : public UUserWidget
{
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintReadOnly, Category = "Tape")
	bool bVertical = false;

	UPROPERTY(BlueprintReadOnly, Category = "Tape")
	bool bWrap360 = false;

	UPROPERTY(BlueprintReadOnly, Category = "Tape")
	float Value = 0.f;

	/** Units shown over the tape's length. */
	UPROPERTY(BlueprintReadOnly, Category = "Tape")
	float Span = 70.f;

	/** Labelled tick every MajorStep units, MinorPerMajor ticks between. */
	UPROPERTY(BlueprintReadOnly, Category = "Tape")
	float MajorStep = 20.f;

	UPROPERTY(BlueprintReadOnly, Category = "Tape")
	int32 MinorPerMajor = 4;

	/** Labels and the value print Value x LabelScale with LabelDecimals decimals. */
	UPROPERTY(BlueprintReadOnly, Category = "Tape")
	float LabelScale = 1.f;

	UPROPERTY(BlueprintReadOnly, Category = "Tape")
	int32 LabelDecimals = 0;

	/** The mark along the tape, 0..1 (vertical: from the top). */
	UPROPERTY(BlueprintReadOnly, Category = "Tape")
	float MarkAt = 0.5f;

	UPROPERTY(BlueprintReadOnly, Category = "Tape")
	FLinearColor Color = FLinearColor::White;

	/** The text a value prints as (labels and the mark). */
	UFUNCTION(BlueprintCallable, Category = "Tape")
	FString Format(float InValue) const;

protected:
	virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
};

/**
 * The pitch ladder over the whole view: two horizon strokes and a bracket every 5 degrees with its
 * number, rolled with the view and projected with its field of view, so the lines sit on the real
 * horizon and on the real 5-degree lines.
 */
UCLASS()
class GAMESPACE_API USpaceHudLadder : public UUserWidget
{
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintReadOnly, Category = "Ladder")
	float PitchDeg = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "Ladder")
	float RollDeg = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "Ladder")
	float FovDeg = 90.f;

	UPROPERTY(BlueprintReadOnly, Category = "Ladder")
	FLinearColor Color = FLinearColor::White;

	/** Where the line for PitchLineDeg is drawn, relative to the view's centre (pixels of a view this wide). */
	UFUNCTION(BlueprintCallable, Category = "Ladder")
	static FVector2D LineCentre(float PitchLineDeg, float InPitchDeg, float InRollDeg, float InFovDeg, float ViewWidth);

protected:
	virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
};

/**
 * The cockpit radar, after the disc in the middle of the reference's dashboard (Docs/UI/Screenshot
 * 2026-09-17 201854.png): a plan view in the ship's frame with the nose up - range rings, a cross,
 * the own ship in the middle, contacts as diamonds with a stalk for their height, and the bodies'
 * bearings as marks on the rim with their initial.
 */
UCLASS()
class GAMESPACE_API USpaceHudRadar : public UUserWidget
{
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintReadOnly, Category = "Radar")
	TArray<FSpaceRadarContact> Contacts;

	UPROPERTY(BlueprintReadOnly, Category = "Radar")
	float RangeM = 5000.f;

	UPROPERTY(BlueprintReadOnly, Category = "Radar")
	FLinearColor Color = FLinearColor::White;

	/** Contacts. */
	UPROPERTY(BlueprintReadOnly, Category = "Radar")
	FLinearColor Accent = FLinearColor::White;

	/** Where a contact is drawn, as a fraction of the disc's radius from its centre (X right, Y up); length over 1: off the disc. */
	UFUNCTION(BlueprintCallable, Category = "Radar")
	static FVector2D PlotPosition(const FSpaceRadarContact& Contact, float InRangeM);

protected:
	virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
};

/**
 * The self status page, after the reference's (Docs/UI/Screenshot 2026-09-17 194942.png): the ship
 * seen from above as a hologram - its collision hulls' outlines, the engines glowing with the thrust,
 * the landing gear lit when down. Only what the game has: no shields, no hull damage.
 */
UCLASS()
class GAMESPACE_API USpaceHudShipStatus : public UUserWidget
{
	GENERATED_BODY()

public:
	/** The hulls from above, metres: X right, Y ahead (each a convex outline). */
	TArray<TArray<FVector2D>> Outlines;

	/** Engines and gear legs from above, metres. */
	UPROPERTY(BlueprintReadOnly, Category = "Ship Status")
	TArray<FVector2D> Engines;

	UPROPERTY(BlueprintReadOnly, Category = "Ship Status")
	TArray<FVector2D> Gear;

	/** 0..1. */
	UPROPERTY(BlueprintReadOnly, Category = "Ship Status")
	float EngineDemand = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "Ship Status")
	FLinearColor EngineColor = FLinearColor::White;

	/** The gear legs' colour; transparent alpha: not drawn (up). */
	UPROPERTY(BlueprintReadOnly, Category = "Ship Status")
	FLinearColor GearColor = FLinearColor::Transparent;

	UPROPERTY(BlueprintReadOnly, Category = "Ship Status")
	FLinearColor Color = FLinearColor::White;

	/** Tests: how many hull outlines the page draws. */
	UFUNCTION(BlueprintCallable, Category = "Ship Status|Tests")
	int32 GetOutlineCount() const { return Outlines.Num(); }

	/** Reads the ship's shape: hull outlines from its collision, engines and gear from its sockets. */
	UFUNCTION(BlueprintCallable, Category = "Ship Status")
	void SetShip(const AActor* Ship);

protected:
	virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
};

/**
 * The flight HUD in UMG, laid out after the current Star Citizen HUD (Docs/UI/Screenshot 2026-09-17
 * 201854.png, measured at 1080p from the middle of the screen). SC-1c's version followed an older
 * reference (Docs/UI/SC_ThrottleHUD_VisualReference.md); the lines below describe that one where the
 * new layout does not say otherwise:
 * - left: master mode icon with SCM/NAV over the sub-mode, switch badges (CSTB, CPLD, PREC, BOOST),
 *   the strafe cross, the tall speed tube with the limiter handle and a +, speed and m/s under it, and
 *   BOOST / LIMIT rows under a bracket;
 * - middle: heading tape, pitch ladder, nose reticle, the mouse virtual joystick;
 * - right: afterburner tube (red reserve) with its percentage, the altitude tape in km, the gyro
 *   (turn rate) with the G-Safe shield, G and the G-Safe limit, GEAR / CRUISE rows at the top and
 *   R-ALT / VSI / ATMO at the bottom.
 * Heading, ladder and altitudes only near a body. What SC shows and this game has no system for yet
 * (fuel, countermeasures, weapons) is left out rather than faked.
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

	/** Heading, pitch and roll of the view instead of the ship's nose, and the view's field of view:
	 * the HUD is drawn over the view, so its horizon has to be the view's. */
	UFUNCTION(BlueprintCallable, Category = "Flight HUD")
	static FSpaceFlightHudState ApplyView(const FSpaceFlightHudState& State, const ASpaceshipPawn* Ship, FRotator ViewRotation, float FovDeg);

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

	/** Tests: a drawn symbol, tape or the ladder by widget name. */
	UFUNCTION(BlueprintCallable, Category = "Flight HUD|Tests")
	UWidget* DebugGetPart(FName PartName) const { return Parts.FindRef(PartName); }

	/** Tests: whether a widget is shown (not collapsed or hidden). */
	UFUNCTION(BlueprintCallable, Category = "Flight HUD|Tests")
	bool DebugIsShown(FName WidgetName) const;

	/** Share of the speed gauge's length below zero, for flying backwards. */
	static constexpr float SpeedReverseZone = 0.12f;

	/** Full length of the G meter, G. */
	static constexpr float GMeterRangeG = 12.f;

protected:
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	/** Makes the lines the drawn parts queued while painting, grouped by layer and thickness: Slate runs
	 * this after the children. See SpaceHudStyle::PaintLine. */
	virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;

	/** Builds the widget tree. The widgets' names are what ApplyState drives, whatever the layout. */
	virtual void BuildTree();

	/** The state as this layout shows it (the cockpit displays steady their figures); the HUD shows it as is. */
	virtual FSpaceFlightHudState SteadyState(const FSpaceFlightHudState& State) { return State; }
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

	/** Symbols, tapes and the ladder by name. */
	UPROPERTY(Transient)
	TMap<FName, TObjectPtr<UWidget>> Parts;

	UPROPERTY(Transient)
	TObjectPtr<UWidget> VirtualJoystickBox;

	TMap<FName, bool> LampLit;
	TMap<FName, FLinearColor> LampColors;
	float Time = 0.f;
};

/**
 * The cockpit's dashboard displays: the flight HUD's instruments (same widgets, same names, so
 * USpaceFlightHud::ApplyState drives them) laid out on one canvas, in the style of the reference's
 * MFDs (deep blue glass, a title over a rule, a page bar at the bottom). Left, FLIGHT: speed, limiter,
 * G and the sub-mode large, the master mode pill, and bars for speed, boost, afterburner and G like the
 * reference's power page. Right, SYSTEMS: a list like its contacts page - COUPLED, G-SAFE, COMSTAB,
 * BOOST, PRECISION and GEAR each with its switch pill, CRUISE with its state. In the middle column
 * of the dashboard, two small screens one over the other: RADAR (the reference's centre radar) and
 * SELF STATUS (the ship from above).
 *
 * Canvas: left 0..560, right 560..1120, the centre column 1120..1330 (radar over 0..259, self status
 * under it) - the same pixels per centimetre on every screen, and each screen the shape of its glass.
 * Tools/Blender/build_ai_ship.py maps each screen's quad to its rectangle (texture_rect in the recipe).
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
	/** The glass is ~29 x 25 cm: the same shape, so nothing is stretched. */
	static constexpr float DisplayWidth = 560.f;
	static constexpr float DisplayHeight = 490.f;

	/** The centre column's two screens: ~11 x 13.5 and ~11 x 12 cm of glass at the big displays' density. */
	static constexpr float CentreWidth = 210.f;
	static constexpr float CentreTopHeight = 259.f;

	/** The whole canvas (the render target's layout size). */
	static constexpr float CanvasWidth = 2.f * DisplayWidth + CentreWidth;
	static constexpr float CanvasHeight = DisplayHeight;

	/**
	 * A screen's rectangle on the canvas, by the name of its socket (Display_<name>): left, right,
	 * centre_top, centre_bottom. Empty for an unknown name.
	 */
	static FBox2D ScreenRect(const FString& Name);

	/** Tests: ScreenRect as (min X, min Y, max X, max Y); zeros for an unknown name. */
	UFUNCTION(BlueprintCallable, Category = "Cockpit Displays|Tests")
	static FVector4 DebugGetScreenRect(const FString& Name);

	/**
	 * What the radar shows around the ship: pawns and static meshes (asteroids, stations) within RangeM,
	 * nearest first and at most MaxContacts, and every celestial or distant body as a bearing.
	 */
	UFUNCTION(BlueprintCallable, Category = "Cockpit Displays")
	static TArray<FSpaceRadarContact> MakeRadarContacts(const ASpaceshipPawn* Ship, float RangeM, int32 MaxContacts = 24);

	/** What the displays show for this ship: the HUD's state with the radar's contacts. */
	UFUNCTION(BlueprintCallable, Category = "Cockpit Displays")
	static FSpaceFlightHudState MakeDisplayState(const ASpaceshipPawn* Ship, float RadarRangeM);

	/** Reads the ship's shape for the self status page. */
	void SetShip(const AActor* Ship);

	/** Shows or hides the centre column's screens (space.CockpitCentre). */
	void SetCentreColumn(bool bOn);

	/**
	 * MFD pages, as the reference's MFDs page with the keys beside them. Left (0): FLIGHT, THRUSTERS,
	 * NAVIGATION; right (1): STATUS, CONTACTS, SELF STATUS - only what the game has data for (no weapons,
	 * shields, power or cooling pages until those systems exist).
	 */
	static constexpr int32 PageCount = 3;

	/** The page titles of a display (0 left, 1 right). */
	static const TArray<FString>& PageTitles(int32 Display);

	/** Shows these pages (wrapped into 0..PageCount-1); the title and the page tab follow. */
	UFUNCTION(BlueprintCallable, Category = "Cockpit Displays")
	void SetPages(int32 LeftPage, int32 RightPage);

	/** Tests: the page a display shows. */
	UFUNCTION(BlueprintCallable, Category = "Cockpit Displays|Tests")
	int32 DebugGetPage(int32 Display) const;

	/**
	 * A figure as the display shows it: while it changes fast between two updates it is shown in
	 * Step-sized steps (the speed in tens of m/s while accelerating), and exactly once it settles. A
	 * number rewritten digit by digit is what temporal AA blended into two values over each other.
	 */
	float Steady(FName Figure, float Value, float Step, float FastChange);

protected:
	/** Driven by UCockpitDisplayComponent, not by a player: nothing to do per Slate tick. */
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
	virtual void BuildTree() override;

	virtual FSpaceFlightHudState SteadyState(const FSpaceFlightHudState& State) override;

private:
	TMap<FName, float> LastFigures;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UWidgetSwitcher>> PageSwitchers;
};
