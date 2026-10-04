// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "UObject/StrongObjectPtr.h"

class ASpacePlayerController;
class SWidgetSwitcher;
class UTexture2D;
struct FSlateBrush;

enum class ESpaceMenuPage : uint8
{
	Main,
	Pause,
	Settings,
	Loading
};

/** The settings page's tabs, in the order they are shown. */
enum class ESpaceSettingsTab : uint8
{
	Game,
	Graphics,
	Audio,
	Controls,
	Count
};

/**
 * The game's menus as one Slate widget: title screen, pause menu, settings and the loading page. Plain C++, no UMG
 * assets, so it builds and cooks without anything authored in the editor.
 *
 * The look follows Star Citizen 4.10's main menu and OPTIONS MENU as closely as we can (the author's own capture,
 * starcitizenreference/MenuSettings_OwnCapture_Notes.md, 4. 10. 2026): hard boxes with a thin outline and a cut
 * bottom-right corner, a squarish face (Oxanium, the free face nearest SC's that has Czech letters), an image card to
 * play from, a full-screen black settings page with tabs across the top, a row highlight under the mouse, arrow
 * selectors that go round, drop-down boxes and sliders with a white block thumb. Settings take effect at
 * once, as in SC; RESET puts the current tab back to its defaults. The title screen keeps our live 3D background.
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
	void ShowTab(ESpaceSettingsTab Tab);

	virtual bool SupportsKeyboardFocus() const override { return true; }
	virtual FReply OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent) override;

private:
	/** The settings as the page shows them; every change is written straight to USpaceUserSettings (Commit). */
	struct FDraft
	{
		int32 WindowMode = 0;
		int32 Resolution = 0;
		int32 Quality = 3;
		float ResolutionScale = 75.f;
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
	TSharedRef<SWidget> BuildPlayCard();
	TSharedRef<SWidget> BuildTabRows(ESpaceSettingsTab Tab);

	/** A box button (dark translucent fill, thin outline, cut corner) with its label in capitals. */
	TSharedRef<SWidget> MakeButton(const FText& Label, TFunction<void()> OnClick, float Width, bool bFilled = true);
	TSharedRef<SWidget> MakeTab(ESpaceSettingsTab Tab, const FText& Label);
	/** Label, the control in its 402-wide column, and an optional widget right of it (a slider's value). */
	TSharedRef<SWidget> MakeRow(const FText& Label, const TSharedRef<SWidget>& Control, const TSharedPtr<SWidget>& After = nullptr);
	/** ‹ value ›: steps round Count() values, both arrows always lit (as SC's two-value rows). */
	TSharedRef<SWidget> MakeSelectorRow(const FText& Label, TFunction<int32()> GetIndex, TFunction<void(int32)> SetIndex,
		TFunction<int32()> Count, TFunction<FText(int32)> Describe);
	TSharedRef<SWidget> MakeToggleRow(const FText& Label, bool* Value);
	/** A box with › and the value; a click opens the list of values under it. */
	TSharedRef<SWidget> MakeDropdownRow(const FText& Label, TFunction<int32()> GetIndex, TFunction<void(int32)> SetIndex,
		TFunction<int32()> Count, TFunction<FText(int32)> Describe);
	/** Dark track, white block thumb, the value beside it. Applied when the drag ends (volumes preview as it moves). */
	TSharedRef<SWidget> MakeSliderRow(const FText& Label, float* Value, float Min, float Max, TFunction<FText(float)> Describe,
		bool bPreviewVolume = false);

	void LoadDraft();
	/** Writes the draft to the settings, applies and saves them. */
	void Commit();
	/** RESET: the current tab back to its defaults. */
	void ResetTab();
	void CloseSettings();
	void Hovered();
	void Clicked();

	TWeakObjectPtr<ASpacePlayerController> Owner;
	bool bTitleScreen = true;
	ESpaceMenuPage CurrentPage = ESpaceMenuPage::Main;
	ESpaceSettingsTab CurrentTab = ESpaceSettingsTab::Graphics;
	TSharedPtr<SWidgetSwitcher> Switcher;
	TSharedPtr<SWidgetSwitcher> TabSwitcher;
	FDraft Draft;
	TArray<FIntPoint> Resolutions;

	/** The play card's picture (Content/UI/Menu/card_play.jpg, read from the file like the fonts). */
	TStrongObjectPtr<UTexture2D> CardTexture;
	TSharedPtr<FSlateBrush> CardBrush;
};
