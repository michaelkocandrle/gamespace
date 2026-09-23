// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceMenuWidget.h"

#include "Kismet/KismetSystemLibrary.h"
#include "SpacePlayerController.h"
#include "SpaceUserSettings.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/SNullWidget.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SSlider.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Layout/SSpacer.h"
#include "Widgets/Layout/SWidgetSwitcher.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "SpaceMenu"

namespace SpaceMenuStyle
{
	const FLinearColor Text(0.90f, 0.93f, 0.97f);
	const FLinearColor Dim(0.55f, 0.62f, 0.70f);
	const FLinearColor Accent(0.40f, 0.78f, 1.00f);
	const FLinearColor Panel(0.010f, 0.015f, 0.030f, 0.82f);
	const FLinearColor Button(0.07f, 0.10f, 0.16f, 0.95f);

	FSlateFontInfo Font(const FName Weight, float Size)
	{
		return FCoreStyle::GetDefaultFontStyle(Weight, Size);
	}

	const FSlateBrush* White()
	{
		return FCoreStyle::Get().GetBrush("WhiteBrush");
	}

	/** 0 means no limit. */
	const int32 FrameLimits[] = { 0, 30, 60, 120, 144, 165, 240 };
	const EWindowMode::Type WindowModes[] = { EWindowMode::WindowedFullscreen, EWindowMode::Fullscreen, EWindowMode::Windowed };
}

void SSpaceMenu::Construct(const FArguments& InArgs)
{
	Owner = InArgs._Owner;
	bTitleScreen = InArgs._TitleScreen;

	UKismetSystemLibrary::GetSupportedFullscreenResolutions(Resolutions);
	if (const USpaceUserSettings* Settings = USpaceUserSettings::Get())
	{
		Resolutions.AddUnique(Settings->GetDesktopResolution());
	}
	Resolutions.RemoveAll([](const FIntPoint& R) { return R.X < 1024 || R.Y < 600; });
	if (Resolutions.Num() == 0)
	{
		Resolutions.Add(FIntPoint(1920, 1080));
	}
	Resolutions.Sort([](const FIntPoint& A, const FIntPoint& B) { return A.X * A.Y < B.X * B.Y; });
	LoadDraft();

	ChildSlot
	[
		SAssignNew(Switcher, SWidgetSwitcher)
		+ SWidgetSwitcher::Slot() [ BuildTitlePage() ]
		+ SWidgetSwitcher::Slot() [ BuildPausePage() ]
		+ SWidgetSwitcher::Slot() [ BuildSettingsPage() ]
		+ SWidgetSwitcher::Slot() [ BuildLoadingPage() ]
	];
	ShowPage(bTitleScreen ? ESpaceMenuPage::Main : ESpaceMenuPage::Pause);
}

void SSpaceMenu::ShowPage(ESpaceMenuPage Page)
{
	if (Page == ESpaceMenuPage::Settings)
	{
		LoadDraft();
	}
	CurrentPage = Page;
	Switcher->SetActiveWidgetIndex(static_cast<int32>(Page));
}

FReply SSpaceMenu::OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent)
{
	const FKey Key = InKeyEvent.GetKey();
	if (Key == EKeys::Escape || Key == EKeys::F10 || Key == EKeys::Gamepad_Special_Right || Key == EKeys::Gamepad_FaceButton_Right)
	{
		if (CurrentPage == ESpaceMenuPage::Settings)
		{
			CloseSettings();
			return FReply::Handled();
		}
		if (CurrentPage == ESpaceMenuPage::Pause)
		{
			if (ASpacePlayerController* Controller = Owner.Get())
			{
				Controller->ResumeGame();
			}
			return FReply::Handled();
		}
	}
	return SCompoundWidget::OnKeyDown(MyGeometry, InKeyEvent);
}

// -------------------------------------------------------------------------------------------
// Pages
// -------------------------------------------------------------------------------------------

TSharedRef<SWidget> SSpaceMenu::BuildTitlePage()
{
	using namespace SpaceMenuStyle;
	return SNew(SOverlay)
		+ SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Fill)
		[
			SNew(SBox).WidthOverride(620.f)
			[
				SNew(SBorder)
				.BorderImage(White())
				.BorderBackgroundColor(FLinearColor(0.f, 0.f, 0.f, 0.55f))
				.Padding(FMargin(72.f, 0.f))
				[
					SNew(SVerticalBox)
					+ SVerticalBox::Slot().FillHeight(1.f) [ SNew(SSpacer) ]
					+ SVerticalBox::Slot().AutoHeight()
					[
						SNew(STextBlock).Text(LOCTEXT("Title", "GAMESPACE")).Font(Font("Bold", 64.f)).ColorAndOpacity(Text)
					]
					+ SVerticalBox::Slot().AutoHeight().Padding(FMargin(6.f, 0.f, 0.f, 56.f))
					[
						SNew(STextBlock).Text(LOCTEXT("Subtitle", "prototyp  ·  Veyra")).Font(Font("Regular", 20.f)).ColorAndOpacity(Accent)
					]
					+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f)
					[
						MakeButton(LOCTEXT("Play", "HRÁT"), [this]()
						{
							ShowPage(ESpaceMenuPage::Loading);
							if (ASpacePlayerController* Controller = Owner.Get())
							{
								Controller->StartGame();
							}
						}, 30.f)
					]
					+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f)
					[
						MakeButton(LOCTEXT("Settings", "NASTAVENÍ"), [this]() { ShowPage(ESpaceMenuPage::Settings); }, 30.f)
					]
					+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f)
					[
						MakeButton(LOCTEXT("Quit", "KONEC"), [this]()
						{
							if (ASpacePlayerController* Controller = Owner.Get())
							{
								Controller->QuitGame();
							}
						}, 30.f)
					]
					+ SVerticalBox::Slot().FillHeight(1.2f) [ SNew(SSpacer) ]
					+ SVerticalBox::Slot().AutoHeight().Padding(FMargin(6.f, 0.f, 0.f, 40.f))
					[
						SNew(STextBlock)
						.Text(LOCTEXT("TitleHint", "Ve hře: Escape menu  ·  H HUD  ·  J cruise  ·  V flight assist  ·  C kokpit"))
						.Font(Font("Regular", 13.f))
						.ColorAndOpacity(Dim)
						.AutoWrapText(true)
					]
				]
			]
		];
}

TSharedRef<SWidget> SSpaceMenu::BuildPausePage()
{
	using namespace SpaceMenuStyle;
	return SNew(SOverlay)
		+ SOverlay::Slot()
		[
			SNew(SImage).Image(White()).ColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, 0.55f))
		]
		+ SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center)
		[
			SNew(SBox).WidthOverride(520.f)
			[
				SNew(SBorder)
				.BorderImage(White())
				.BorderBackgroundColor(Panel)
				.Padding(FMargin(48.f, 40.f))
				[
					SNew(SVerticalBox)
					+ SVerticalBox::Slot().AutoHeight().Padding(FMargin(0.f, 0.f, 0.f, 28.f))
					[
						SNew(STextBlock).Text(LOCTEXT("Paused", "PAUZA")).Font(Font("Bold", 44.f)).ColorAndOpacity(Text)
					]
					+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 5.f)
					[
						MakeButton(LOCTEXT("Resume", "POKRAČOVAT"), [this]()
						{
							if (ASpacePlayerController* Controller = Owner.Get())
							{
								Controller->ResumeGame();
							}
						})
					]
					+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 5.f)
					[
						// Walk the Steadfast interior, or back (the same as I). Only where there is one.
						Owner.IsValid() && Owner->HasInterior()
							? MakeButton(Owner->IsWalkingInterior() ? LOCTEXT("InteriorBack", "ZPĚT (I)")
							                                         : LOCTEXT("Interior", "INTERIÉR STEADFASTU (I)"), [this]()
							{
								if (ASpacePlayerController* Controller = Owner.Get())
								{
									Controller->ResumeGame();
									Controller->ToggleInterior();
								}
							})
							: SNullWidget::NullWidget
					]
					+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 5.f)
					[
						MakeButton(LOCTEXT("PauseSettings", "NASTAVENÍ"), [this]() { ShowPage(ESpaceMenuPage::Settings); })
					]
					+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 5.f)
					[
						MakeButton(LOCTEXT("MainMenu", "HLAVNÍ MENU"), [this]()
						{
							ShowPage(ESpaceMenuPage::Loading);
							if (ASpacePlayerController* Controller = Owner.Get())
							{
								Controller->GoToMainMenu();
							}
						})
					]
					+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 5.f)
					[
						MakeButton(LOCTEXT("PauseQuit", "UKONČIT HRU"), [this]()
						{
							if (ASpacePlayerController* Controller = Owner.Get())
							{
								Controller->QuitGame();
							}
						})
					]
				]
			]
		];
}

TSharedRef<SWidget> SSpaceMenu::BuildLoadingPage()
{
	using namespace SpaceMenuStyle;
	return SNew(SOverlay)
		+ SOverlay::Slot()
		[
			SNew(SImage).Image(White()).ColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, 0.85f))
		]
		+ SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center)
		[
			SNew(STextBlock).Text(LOCTEXT("Loading", "NAČÍTÁNÍ…")).Font(Font("Bold", 36.f)).ColorAndOpacity(Text)
		];
}

TSharedRef<SWidget> SSpaceMenu::BuildSettingsPage()
{
	using namespace SpaceMenuStyle;

	auto Percent = [](float Value) { return FText::FromString(FString::Printf(TEXT("%d %%"), FMath::RoundToInt32(Value * 100.f))); };

	TSharedRef<SVerticalBox> Rows = SNew(SVerticalBox);
	auto Add = [&Rows](const TSharedRef<SWidget>& Row) { Rows->AddSlot().AutoHeight().Padding(0.f, 4.f)[ Row ]; };

	Add(MakeSection(LOCTEXT("Graphics", "GRAFIKA")));
	Add(MakeChoiceRow(LOCTEXT("WindowMode", "Režim zobrazení"),
		[this]() { return Draft.WindowMode; }, [this](int32 I) { Draft.WindowMode = I; }, []() { return 3; },
		[](int32 I)
		{
			return I == 0 ? LOCTEXT("Borderless", "Celá obrazovka (bez rámečku)")
				: I == 1 ? LOCTEXT("Exclusive", "Celá obrazovka (exkluzivní)") : LOCTEXT("Windowed", "V okně");
		}));
	Add(MakeChoiceRow(LOCTEXT("Resolution", "Rozlišení"),
		[this]() { return Draft.Resolution; }, [this](int32 I) { Draft.Resolution = I; }, [this]() { return Resolutions.Num(); },
		[this](int32 I)
		{
			if (Draft.WindowMode == 0)
			{
				return LOCTEXT("DesktopResolution", "podle monitoru");
			}
			const FIntPoint R = Resolutions.IsValidIndex(I) ? Resolutions[I] : FIntPoint::ZeroValue;
			return FText::FromString(FString::Printf(TEXT("%d × %d"), R.X, R.Y));
		}));
	Add(MakeChoiceRow(LOCTEXT("Quality", "Kvalita grafiky"),
		[this]() { return Draft.Quality; }, [this](int32 I) { Draft.Quality = I; }, []() { return 5; },
		[](int32 I)
		{
			static const FText Names[] = { LOCTEXT("Low", "Nízká"), LOCTEXT("Medium", "Střední"), LOCTEXT("High", "Vysoká"),
				LOCTEXT("Epic", "Epická"), LOCTEXT("Cinematic", "Filmová") };
			return Names[FMath::Clamp(I, 0, 4)];
		}));
	Add(MakeSliderRow(LOCTEXT("ResolutionScale", "Rozlišení vykreslování (TSR)"), &Draft.ResolutionScale, 50.f, 100.f,
		[](float V) { return FText::FromString(FString::Printf(TEXT("%d %%"), FMath::RoundToInt32(V))); }));
	Add(MakeToggleRow(LOCTEXT("VSync", "Vertikální synchronizace"), &Draft.bVSync));
	Add(MakeChoiceRow(LOCTEXT("FrameLimit", "Limit snímků"),
		[this]() { return Draft.FrameLimit; }, [this](int32 I) { Draft.FrameLimit = I; }, []() { return int32(UE_ARRAY_COUNT(FrameLimits)); },
		[](int32 I)
		{
			return FrameLimits[I] == 0 ? LOCTEXT("NoLimit", "Bez limitu") : FText::FromString(FString::Printf(TEXT("%d FPS"), FrameLimits[I]));
		}));

	Add(MakeSection(LOCTEXT("Audio", "ZVUK")));
	Add(MakeSliderRow(LOCTEXT("MasterVolume", "Celková hlasitost"), &Draft.MasterVolume, 0.f, 1.f, Percent, true));
	Add(MakeSliderRow(LOCTEXT("EffectsVolume", "Efekty a motory"), &Draft.EffectsVolume, 0.f, 1.f, Percent, true));
	Add(MakeSliderRow(LOCTEXT("MusicVolume", "Hudba a ambient"), &Draft.MusicVolume, 0.f, 1.f, Percent, true));

	Add(MakeSection(LOCTEXT("Controls", "OVLÁDÁNÍ")));
	Add(MakeSliderRow(LOCTEXT("Sensitivity", "Citlivost myši"), &Draft.MouseSensitivity, 0.25f, 3.f,
		[](float V) { return FText::FromString(FString::Printf(TEXT("× %.2f"), V)); }));
	Add(MakeToggleRow(LOCTEXT("InvertPitch", "Obrácené klopení lodi (myš nahoru = nos dolů)"), &Draft.bInvertPitch));

	Add(MakeSection(LOCTEXT("Game", "HRA")));
	Add(MakeChoiceRow(LOCTEXT("Hud", "HUD (klávesa H)"),
		[this]() { return Draft.HudMode; }, [this](int32 I) { Draft.HudMode = I; }, []() { return 4; },
		[](int32 I)
		{
			return I == 0 ? LOCTEXT("HudOff", "Skrytý") : I == 1 ? LOCTEXT("HudFlight", "Jen letový HUD")
				: I == 2 ? LOCTEXT("HudCompact", "S textem") : LOCTEXT("HudFull", "S plným textem");
		}));
	Add(MakeToggleRow(LOCTEXT("ShowFps", "Zobrazit FPS"), &Draft.bShowFps));

	return SNew(SOverlay)
		+ SOverlay::Slot()
		[
			SNew(SImage).Image(White()).ColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, 0.5f))
		]
		+ SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center).Padding(40.f)
		[
			SNew(SBox).WidthOverride(1000.f).MaxDesiredHeight(920.f)
			[
				SNew(SBorder)
				.BorderImage(White())
				.BorderBackgroundColor(Panel)
				.Padding(FMargin(48.f, 36.f))
				[
					SNew(SVerticalBox)
					+ SVerticalBox::Slot().AutoHeight().Padding(FMargin(0.f, 0.f, 0.f, 16.f))
					[
						SNew(STextBlock).Text(LOCTEXT("SettingsTitle", "NASTAVENÍ")).Font(Font("Bold", 40.f)).ColorAndOpacity(Text)
					]
					+ SVerticalBox::Slot().FillHeight(1.f)
					[
						SNew(SScrollBox) + SScrollBox::Slot().Padding(FMargin(0.f, 0.f, 16.f, 0.f)) [ Rows ]
					]
					+ SVerticalBox::Slot().AutoHeight().Padding(FMargin(0.f, 24.f, 0.f, 0.f))
					[
						SNew(SHorizontalBox)
						+ SHorizontalBox::Slot().FillWidth(1.f).VAlign(VAlign_Center)
						[
							SNew(STextBlock)
							.Text_Lambda([this]()
							{
								return FPlatformTime::Seconds() - AppliedTime < 2.5
									? LOCTEXT("Applied", "Uloženo.")
									: LOCTEXT("SettingsHint", "Escape: zpět bez uložení");
							})
							.Font(Font("Regular", 15.f))
							.ColorAndOpacity(Dim)
						]
						+ SHorizontalBox::Slot().AutoWidth().Padding(8.f, 0.f)
						[
							MakeButton(LOCTEXT("Apply", "POUŽÍT"), [this]() { ApplyDraft(); }, 22.f)
						]
						+ SHorizontalBox::Slot().AutoWidth().Padding(8.f, 0.f)
						[
							MakeButton(LOCTEXT("Back", "ZPĚT"), [this]() { CloseSettings(); }, 22.f)
						]
					]
				]
			]
		];
}

// -------------------------------------------------------------------------------------------
// Building blocks
// -------------------------------------------------------------------------------------------

TSharedRef<SWidget> SSpaceMenu::MakeButton(const FText& Label, TFunction<void()> OnClick, float FontSize)
{
	using namespace SpaceMenuStyle;
	return SNew(SButton)
		.ButtonColorAndOpacity(Button)
		.ContentPadding(FMargin(26.f, 10.f))
		.HAlign(HAlign_Left)
		.OnHovered_Lambda([this]() { Hovered(); })
		.OnClicked_Lambda([this, OnClick]()
		{
			if (ASpacePlayerController* Controller = Owner.Get())
			{
				Controller->PlayUiSound(true);
			}
			OnClick();
			return FReply::Handled();
		})
		[
			SNew(STextBlock).Text(Label).Font(Font("Bold", FontSize)).ColorAndOpacity(Text)
		];
}

TSharedRef<SWidget> SSpaceMenu::MakeSection(const FText& Title)
{
	using namespace SpaceMenuStyle;
	return SNew(SBox).Padding(FMargin(0.f, 18.f, 0.f, 4.f))
		[
			SNew(STextBlock).Text(Title).Font(Font("Bold", 17.f)).ColorAndOpacity(Accent)
		];
}

TSharedRef<SWidget> SSpaceMenu::MakeChoiceRow(const FText& Label, TFunction<int32()> GetIndex, TFunction<void(int32)> SetIndex,
	TFunction<int32()> Count, TFunction<FText(int32)> Describe)
{
	using namespace SpaceMenuStyle;
	auto Step = [this, GetIndex, SetIndex, Count](int32 Direction)
	{
		const int32 N = FMath::Max(Count(), 1);
		SetIndex((GetIndex() + Direction + N) % N);
		if (ASpacePlayerController* Controller = Owner.Get())
		{
			Controller->PlayUiSound(false);
		}
		return FReply::Handled();
	};
	auto Arrow = [Step](const TCHAR* Glyph, int32 Direction) -> TSharedRef<SWidget>
	{
		return SNew(SButton)
			.ButtonColorAndOpacity(SpaceMenuStyle::Button)
			.ContentPadding(FMargin(14.f, 2.f))
			.OnClicked_Lambda([Step, Direction]() { return Step(Direction); })
			[
				SNew(STextBlock).Text(FText::FromString(Glyph)).Font(SpaceMenuStyle::Font("Bold", 18.f)).ColorAndOpacity(SpaceMenuStyle::Text)
			];
	};
	return SNew(SHorizontalBox)
		+ SHorizontalBox::Slot().FillWidth(0.48f).VAlign(VAlign_Center)
		[
			SNew(STextBlock).Text(Label).Font(Font("Regular", 18.f)).ColorAndOpacity(Text)
		]
		+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center) [ Arrow(TEXT("<"), -1) ]
		+ SHorizontalBox::Slot().FillWidth(0.52f).VAlign(VAlign_Center).HAlign(HAlign_Center)
		[
			SNew(STextBlock).Text_Lambda([GetIndex, Describe]() { return Describe(GetIndex()); }).Font(Font("Bold", 18.f)).ColorAndOpacity(Accent)
		]
		+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center) [ Arrow(TEXT(">"), 1) ];
}

TSharedRef<SWidget> SSpaceMenu::MakeToggleRow(const FText& Label, bool* Value)
{
	return MakeChoiceRow(Label, [Value]() { return *Value ? 1 : 0; }, [Value](int32 I) { *Value = I != 0; }, []() { return 2; },
		[](int32 I) { return I ? LOCTEXT("ToggleOn", "Zapnuto") : LOCTEXT("ToggleOff", "Vypnuto"); });
}

TSharedRef<SWidget> SSpaceMenu::MakeSliderRow(const FText& Label, float* Value, float Min, float Max, TFunction<FText(float)> Describe, bool bPreviewVolume)
{
	using namespace SpaceMenuStyle;
	return SNew(SHorizontalBox)
		+ SHorizontalBox::Slot().FillWidth(0.48f).VAlign(VAlign_Center)
		[
			SNew(STextBlock).Text(Label).Font(Font("Regular", 18.f)).ColorAndOpacity(Text)
		]
		+ SHorizontalBox::Slot().FillWidth(0.40f).VAlign(VAlign_Center).Padding(8.f, 6.f)
		[
			SNew(SSlider)
			.MinValue(Min)
			.MaxValue(Max)
			.Value_Lambda([Value]() { return *Value; })
			.OnValueChanged_Lambda([this, Value, bPreviewVolume](float NewValue)
			{
				*Value = NewValue;
				if (bPreviewVolume)
				{
					if (ASpacePlayerController* Controller = Owner.Get())
					{
						Controller->PreviewVolumes(Draft.MasterVolume, Draft.EffectsVolume, Draft.MusicVolume);
					}
				}
			})
		]
		+ SHorizontalBox::Slot().FillWidth(0.12f).VAlign(VAlign_Center).HAlign(HAlign_Right)
		[
			SNew(STextBlock).Text_Lambda([Value, Describe]() { return Describe(*Value); }).Font(Font("Bold", 18.f)).ColorAndOpacity(Accent)
		];
}

// -------------------------------------------------------------------------------------------
// Settings
// -------------------------------------------------------------------------------------------

void SSpaceMenu::LoadDraft()
{
	const USpaceUserSettings* Settings = USpaceUserSettings::Get();
	if (!Settings)
	{
		return;
	}
	const EWindowMode::Type Mode = Settings->GetFullscreenMode();
	Draft.WindowMode = Mode == EWindowMode::WindowedFullscreen ? 0 : Mode == EWindowMode::Fullscreen ? 1 : 2;

	const FIntPoint Current = Settings->GetScreenResolution();
	Draft.Resolution = Resolutions.Num() - 1;
	for (int32 Index = 0; Index < Resolutions.Num(); ++Index)
	{
		if (Resolutions[Index] == Current)
		{
			Draft.Resolution = Index;
		}
	}

	// Not GetOverallScalabilityLevel(): that is -1 whenever the resolution scale is not the preset's
	// default, which made this row show High and the next apply save High over the player's choice.
	Draft.Quality = Settings->GetGraphicsQualityLevel();
	float Normalized = 1.f;
	float Scale = 100.f;
	float MinScale = 50.f;
	float MaxScale = 100.f;
	Settings->GetResolutionScaleInformationEx(Normalized, Scale, MinScale, MaxScale);
	Draft.ResolutionScale = FMath::Clamp(Scale, 50.f, 100.f);
	Draft.bVSync = Settings->IsVSyncEnabled();

	const float Limit = Settings->GetFrameRateLimit();
	Draft.FrameLimit = 0;
	for (int32 Index = 1; Index < UE_ARRAY_COUNT(SpaceMenuStyle::FrameLimits); ++Index)
	{
		if (FMath::IsNearlyEqual(Limit, float(SpaceMenuStyle::FrameLimits[Index]), 0.5f))
		{
			Draft.FrameLimit = Index;
		}
	}

	Draft.MasterVolume = Settings->MasterVolume;
	Draft.EffectsVolume = Settings->EffectsVolume;
	Draft.MusicVolume = Settings->MusicVolume;
	Draft.MouseSensitivity = Settings->MouseSensitivity;
	Draft.bInvertPitch = Settings->bInvertShipPitch;
	Draft.HudMode = FMath::Clamp(Settings->HudMode, 0, 3);
	Draft.bShowFps = Settings->bShowFps;
}

void SSpaceMenu::ApplyDraft()
{
	USpaceUserSettings* Settings = USpaceUserSettings::Get();
	if (!Settings)
	{
		return;
	}
	Settings->SetFullscreenMode(SpaceMenuStyle::WindowModes[FMath::Clamp(Draft.WindowMode, 0, 2)]);
	// Borderless always covers the whole monitor.
	Settings->SetScreenResolution(Draft.WindowMode == 0 || !Resolutions.IsValidIndex(Draft.Resolution)
		? Settings->GetDesktopResolution() : Resolutions[Draft.Resolution]);
	Settings->SetOverallScalabilityLevel(Draft.Quality);
	Settings->SetResolutionScaleValueEx(Draft.ResolutionScale);
	Settings->SetVSyncEnabled(Draft.bVSync);
	Settings->SetFrameRateLimit(float(SpaceMenuStyle::FrameLimits[FMath::Clamp(Draft.FrameLimit, 0, int32(UE_ARRAY_COUNT(SpaceMenuStyle::FrameLimits)) - 1)]));

	Settings->MasterVolume = Draft.MasterVolume;
	Settings->EffectsVolume = Draft.EffectsVolume;
	Settings->MusicVolume = Draft.MusicVolume;
	Settings->MouseSensitivity = Draft.MouseSensitivity;
	Settings->bInvertShipPitch = Draft.bInvertPitch;
	Settings->HudMode = Draft.HudMode;
	Settings->bShowFps = Draft.bShowFps;

	// Applies the video mode and scalability and saves GameUserSettings.ini.
	Settings->ApplySettings(false);
	if (ASpacePlayerController* Controller = Owner.Get())
	{
		Settings->ApplyGameSettings(Controller->GetWorld());
		Controller->PreviewVolumes(Settings->MasterVolume, Settings->EffectsVolume, Settings->MusicVolume);
	}
	AppliedTime = FPlatformTime::Seconds();
}

void SSpaceMenu::CloseSettings()
{
	// Unapplied changes are dropped; undo the volume preview.
	if (const USpaceUserSettings* Settings = USpaceUserSettings::Get())
	{
		if (ASpacePlayerController* Controller = Owner.Get())
		{
			Controller->PreviewVolumes(Settings->MasterVolume, Settings->EffectsVolume, Settings->MusicVolume);
		}
	}
	ShowPage(bTitleScreen ? ESpaceMenuPage::Main : ESpaceMenuPage::Pause);
}

void SSpaceMenu::Hovered()
{
	if (ASpacePlayerController* Controller = Owner.Get())
	{
		Controller->PlayUiSound(false);
	}
}

#undef LOCTEXT_NAMESPACE
