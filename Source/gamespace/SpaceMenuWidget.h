// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"

class ASpacePlayerController;
class SWidgetSwitcher;

enum class ESpaceMenuPage : uint8
{
	Main,
	Pause,
	Settings,
	Loading
};

/**
 * The game's menus as one Slate widget: title screen (Play / Settings / Quit), pause menu
 * (Resume / Settings / Main menu / Quit) and the settings page. Plain C++, no UMG assets, so it
 * builds and cooks without anything authored in the editor. A prototype look: dark panels, big
 * type, keyboard and mouse.
 *
 * Owned and shown by ASpacePlayerController; every action goes back to it.
 */
class GAMESPACE_API SSpaceMenu : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SSpaceMenu) {}
		SLATE_ARGUMENT(TWeakObjectPtr<ASpacePlayerController>, Owner)
		/** Title screen (true) or in-game pause menu (false). */
		SLATE_ARGUMENT(bool, TitleScreen)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

	void ShowPage(ESpaceMenuPage Page);
	ESpaceMenuPage GetPage() const { return CurrentPage; }

	virtual bool SupportsKeyboardFocus() const override { return true; }
	virtual FReply OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent) override;

private:
	/** Working copy of the settings page; written to USpaceUserSettings by Apply. */
	struct FDraft
	{
		int32 WindowMode = 0;
		int32 Resolution = 0;
		int32 Quality = 2;
		float ResolutionScale = 100.f;
		bool bVSync = false;
		int32 FrameLimit = 0;
		float MasterVolume = 0.8f;
		float EffectsVolume = 1.f;
		float MusicVolume = 0.7f;
		float MouseSensitivity = 1.f;
		bool bInvertPitch = false;
		int32 HudMode = 1;
		bool bShowFps = false;
	};

	TSharedRef<SWidget> BuildTitlePage();
	TSharedRef<SWidget> BuildPausePage();
	TSharedRef<SWidget> BuildSettingsPage();
	TSharedRef<SWidget> BuildLoadingPage();

	TSharedRef<SWidget> MakeButton(const FText& Label, TFunction<void()> OnClick, float FontSize = 26.f);
	TSharedRef<SWidget> MakeSection(const FText& Title);
	TSharedRef<SWidget> MakeChoiceRow(const FText& Label, TFunction<int32()> GetIndex, TFunction<void(int32)> SetIndex, TFunction<int32()> Count, TFunction<FText(int32)> Describe);
	TSharedRef<SWidget> MakeToggleRow(const FText& Label, bool* Value);
	TSharedRef<SWidget> MakeSliderRow(const FText& Label, float* Value, float Min, float Max, TFunction<FText(float)> Describe, bool bPreviewVolume = false);

	void LoadDraft();
	void ApplyDraft();
	void CloseSettings();
	void Hovered();

	TWeakObjectPtr<ASpacePlayerController> Owner;
	bool bTitleScreen = true;
	ESpaceMenuPage CurrentPage = ESpaceMenuPage::Main;
	TSharedPtr<SWidgetSwitcher> Switcher;
	FDraft Draft;
	TArray<FIntPoint> Resolutions;
	/** "Applied" feedback on the settings page. */
	double AppliedTime = -100.0;
};
