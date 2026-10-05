// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "SpaceDoorPanel.generated.h"

/**
 * The holographic touch panel beside a ship's door (author 5. 10. 2026: SC's door panel, a hologram opened in interact
 * mode): an emitter line at its foot, a frame of light with corner marks, the door's number, a lock / arrows glyph and
 * its state - amber shut, azure open. Shown in the world by a UWidgetComponent (UShipBoardingComponent).
 */
UCLASS()
class GAMESPACE_API USpaceDoorPanel : public UUserWidget
{
	GENERATED_BODY()

public:
	/** 0 shut .. 1 open (the leaf's travel). */
	float Open = 0.f;
	/** Where the leaf is heading. */
	bool bOpening = false;
	/** The cursor is on it in interact mode (brighter). */
	bool bHovered = false;
	int32 DoorNumber = 0;

protected:
	virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
};
