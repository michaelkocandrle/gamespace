// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "SpaceInteraction.h"
#include "Widgets/SLeafWidget.h"

class ASpacePlayerController;

/** What the overlay draws this frame, gathered by the player controller (screen positions in viewport pixels). */
struct FSpaceInteractionView
{
	bool bVisible = false;
	bool bInteractMode = false;
	FSpaceInteractTarget Target;
	bool bTargetOnScreen = false;
	FVector2D TargetScreen = FVector2D::ZeroVector;
	TArray<FSpaceHotspot> Hotspots;
	TArray<FVector2D> HotspotScreen;
	TArray<bool> HotspotOnScreen;
	/** Each hotspot's label anchor on screen (its own point when it has none). */
	TArray<FVector2D> HotspotLabelScreen;
	int32 Hovered = INDEX_NONE;
	TArray<FSpaceKeyHint> Keys;
};

/**
 * SC's interaction layer over the game (starcitizenreference/OwnCapture_Gameplay_Notes.md): the prompt by the object
 * ("SEDNOUT [F]"), interact mode's hotspots with the hovered one's label, the context key list at the bottom right,
 * toasts at the top centre and hint cards at the right edge (USpaceNotifications). Drawn in one widget; the
 * controller owns it and hands it the view.
 */
class GAMESPACE_API SSpaceInteractionOverlay : public SLeafWidget
{
public:
	SLATE_BEGIN_ARGS(SSpaceInteractionOverlay) {}
		SLATE_ARGUMENT(TWeakObjectPtr<ASpacePlayerController>, Owner)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

	virtual FVector2D ComputeDesiredSize(float) const override { return FVector2D(1.0, 1.0); }
	virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& Geometry, const FSlateRect& Culling, FSlateWindowElementList& Out,
		int32 Layer, const FWidgetStyle& Style, bool bParentEnabled) const override;

private:
	TWeakObjectPtr<ASpacePlayerController> Owner;
};
