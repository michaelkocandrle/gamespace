// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "GameFramework/Actor.h"
#include "SpaceEngineering.generated.h"

class UStaticMeshComponent;
class UWidgetComponent;
struct FSpaceHotspot;

/** One power consumer on the engineering screen (SC's power triangle: pips from the power plant into each system). */
struct FSpaceEngSystem
{
	FString Name;
	/** The glyph under its column (USpaceEngineeringScreen draws them): 0 weapons, 1 thrusters, 2 shields, 3 quantum,
	 * 4 life support, 5 radar, 6 cooler. */
	int32 Icon = 0;
	/** 0 core systems, 1 the second core group (life support, radar), 2 coolant. */
	int32 Group = 0;
	int32 MaxPips = 4;
	int32 Pips = 0;
	/** Where SC's amber H marker sits (the pip count at which the system runs hot). */
	int32 HotPips = 3;
	bool bOn = true;
	/** 0 cold .. 1 at its limit (the thin bar beside the column). */
	float Heat = 0.2f;
};

/** A saved allocation (SC's presets: DEFAULT, NEWPRESET_1 ...). */
struct FSpaceEngPreset
{
	FString Name;
	TArray<int32> Pips;
	int32 PowerOut = 10;
	bool bNav = false;
};

/** A component of the 3D view (a box in the ship's wireframe, its connections from the relay). */
struct FSpaceEngComponent
{
	FString Letter;
	FString Name;
	FString Detail;
	FString Value;
	FVector Centre = FVector::ZeroVector;
	FVector Extent = FVector(30.0);
};

/**
 * The engineering terminal's screen (author 7. 10. 2026: "exactly the same MFD control panel as on the references, the
 * same quality" - SC's engineering terminal): the status strip (armor, hull, cooling, life support, hydrogen fuel), the
 * NAV / SCM switch, notifications, the side tabs 3D VIEW / CONFIG / PRESETS; CONFIG is the power board (power sources ->
 * core systems -> coolant, pips, heat bars, H markers, the edit frame with CLEAR ALL / SAVE / SAVE AND APPLY), 3D VIEW
 * the ship's wireframe with its components, connections, filters and an info card, PRESETS the saved allocations.
 * Drawn in its own canvas units (Canvas x Canvas / 2 after the reference's 1750 x 870 inner screen).
 */
UCLASS()
class GAMESPACE_API USpaceEngineeringScreen : public UUserWidget
{
	GENERATED_BODY()

public:
	static constexpr float CanvasW = 1600.f;
	static constexpr float CanvasH = 800.f;
	/** The reference's coordinates (2000 px wide captures) to the canvas. */
	static FVector2D Ref(double X, double Y) { return FVector2D((X - 120.0) * RefScale, (Y - 115.0) * RefScale); }
	static constexpr double RefScale = 1600.0 / 1750.0;

	TWeakObjectPtr<class ASpaceEngineeringTerminal> Terminal;

protected:
	virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
};

/**
 * SC's engineering terminal on a wall: the housing (a kit part's mesh, set by the importer), the live screen in front of
 * its glass, the power model behind it and the controls clicked in interact mode (hold F; SpaceInteraction gathers them).
 */
UCLASS()
class GAMESPACE_API ASpaceEngineeringTerminal : public AActor
{
	GENERATED_BODY()

public:
	ASpaceEngineeringTerminal();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(VisibleAnywhere, Category = "Engineering")
	TObjectPtr<UStaticMeshComponent> Housing;

	UPROPERTY(VisibleAnywhere, Category = "Engineering")
	TObjectPtr<UWidgetComponent> Screen;

	/** The glass's size, cm (the widget is drawn to fill it), and its centre in front of the housing's pivot. */
	UPROPERTY(EditAnywhere, Category = "Engineering")
	FVector2D GlassSizeCm = FVector2D(57.0, 28.5);

	UPROPERTY(EditAnywhere, Category = "Engineering")
	FVector GlassCentreCm = FVector(1.2, 0.0, 0.0);

	/** The ship's name on the watermark (the maker, not SC's). */
	UPROPERTY(EditAnywhere, Category = "Engineering")
	FString MakerName = TEXT("HALCYON");

	// --- the model the screen reads ---------------------------------------------------------------------------------
	TArray<FSpaceEngSystem> Systems;
	TArray<FSpaceEngPreset> Presets;
	TArray<FSpaceEngComponent> Components;
	/** The power plant's output pips (the power sources column) and its size. */
	int32 PowerOut = 10;
	int32 PowerMax = 10;
	bool bNav = false;
	/** 0 3D VIEW, 1 CONFIG, 2 PRESETS. */
	int32 Tab = 1;
	/** The allocation differs from the applied preset: the amber edit frame, EDIT / <name>. */
	bool bEditing = false;
	FString EditName = TEXT("NEWPRESET_1");
	FString CurrentConfig = TEXT("DEFAULT");
	int32 SelectedComponent = 0;
	bool Filters[4] = { false, true, true, true };    // doors, systems, rooms, connections (SC's defaults)
	bool bShowIcons = true;
	/** The 3D view's slow orbit, degrees. */
	float Orbit = 0.f;
	/** A refused click (over the plant's output): the power column flashes red for a moment. */
	float DenyFlash = 0.f;
	FString Notification;
	float NotificationTime = 0.f;

	int32 UsedPips() const;
	float Percent(int32 Header) const;

	// --- controls ----------------------------------------------------------------------------------------------------
	void ClickPip(int32 System, int32 Pip);
	void ClickPowerPip(int32 Pip);
	void ToggleSystem(int32 System);
	void SetNav(bool bInNav);
	void ClearAll();
	void Save(bool bApply);
	void CancelEdit();
	void ApplyPreset(int32 Index);

	/** Every control as a hotspot for interact mode (its place on the glass in the world). */
	void GatherHotspots(TArray<FSpaceHotspot>& Out);

	/** A canvas point on the glass, world space. */
	FVector CanvasToWorld(const FVector2D& Canvas) const;

	/** The 3D view's projection of a ship-space point (cm) into the canvas, from the current orbit. */
	FVector2D Project(const FVector& P) const;

	/** Where the column of system S stands (its centre x on the canvas) and pip K's box. */
	static float ColumnX(int32 System);
	static FBox2D PipBox(float CentreX, int32 Pip);

private:
	void Seed();
	void MarkEdited();
};
