// Copyright Epic Games, Inc. All Rights Reserved.

#include "SpaceHoloRadarComponent.h"

#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "SpaceFlightHud.h"
#include "SpaceshipPawn.h"
#include "UObject/ConstructorHelpers.h"

namespace HoloRadarDefaults
{
	const TCHAR* DiscMaterial = TEXT("/Game/Ships/Shared/Materials/M_Ship_HoloRadar.M_Ship_HoloRadar");
	const TCHAR* BlipMaterial = TEXT("/Game/Ships/Shared/Materials/M_Ship_HoloBlip.M_Ship_HoloBlip");
	const FName Socket(TEXT("Control_radar"));
	// the engine's basic shapes: the plane is 100 x 100 cm, the sphere 100 cm across, the cylinder and the cone
	// 100 cm across and 100 cm tall about their centre
	constexpr float ShapeCm = 100.f;
}

USpaceHoloRadarComponent::USpaceHoloRadarComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = true;
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Plane(TEXT("/Engine/BasicShapes/Plane.Plane"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cylinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cone(TEXT("/Engine/BasicShapes/Cone.Cone"));
	PlaneMesh = Plane.Object;
	SphereMesh = Sphere.Object;
	CylinderMesh = Cylinder.Object;
	ConeMesh = Cone.Object;
}

UStaticMeshComponent* USpaceHoloRadarComponent::MakePiece(UStaticMesh* Mesh, UMaterialInterface* Material, FName Name)
{
	UStaticMeshComponent* Piece = NewObject<UStaticMeshComponent>(GetOwner(), Name);
	Piece->SetStaticMesh(Mesh);
	Piece->SetMobility(EComponentMobility::Movable);
	Piece->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Piece->SetCastShadow(false);
	Piece->SetupAttachment(this);
	if (Material)
	{
		Piece->SetMaterial(0, Material);
	}
	Piece->RegisterComponent();
	Piece->SetVisibility(false);
	return Piece;
}

void USpaceHoloRadarComponent::BeginPlay()
{
	Super::BeginPlay();
	ASpaceshipPawn* Owner = Cast<ASpaceshipPawn>(GetOwner());
	UStaticMeshComponent* Hull = Owner ? Owner->GetHullMesh() : nullptr;
	if (!Hull || !Hull->DoesSocketExist(HoloRadarDefaults::Socket))
	{
		SetComponentTickEnabled(false);
		return;
	}
	Ship = Owner;
	bHasRadar = true;
	// on the emitter, square to the ship (the socket's own rotation is whatever Blender's empty had)
	AttachToComponent(Hull, FAttachmentTransformRules::SnapToTargetNotIncludingScale, HoloRadarDefaults::Socket);
	SetRelativeRotation(FRotator::ZeroRotator);
	SetWorldRotation(Hull->GetComponentRotation());
	AddLocalRotation(FRotator(TiltDeg, 0.f, 0.f));           // the nose side up: the disc faces the seat behind it

	UMaterialInterface* DiscMaterial = LoadObject<UMaterialInterface>(nullptr, HoloRadarDefaults::DiscMaterial);
	UMaterialInterface* BlipMaterial = LoadObject<UMaterialInterface>(nullptr, HoloRadarDefaults::BlipMaterial);
	const float S = 1.f / HoloRadarDefaults::ShapeCm;

	UStaticMeshComponent* Disc = MakePiece(PlaneMesh, DiscMaterial, TEXT("HoloRadarDisc"));
	Disc->SetRelativeLocation(FVector(0.f, 0.f, DiscHeightCm));
	Disc->SetRelativeScale3D(FVector(2.f * RadiusCm * S, 2.f * RadiusCm * S, 1.f));
	Pieces.Add(Disc);

	// the ship itself in the middle: a small cone along the nose
	UMaterialInstanceDynamic* Own = BlipMaterial ? UMaterialInstanceDynamic::Create(BlipMaterial, this) : nullptr;
	if (Own)
	{
		Own->SetVectorParameterValue(TEXT("Colour"), FLinearColor(0.85f, 0.95f, 1.f));
		Own->SetScalarParameterValue(TEXT("Intensity"), 6.f);
	}
	UStaticMeshComponent* Self = MakePiece(ConeMesh, Own, TEXT("HoloRadarSelf"));
	Self->SetRelativeLocation(FVector(0.f, 0.f, DiscHeightCm + 0.4f));
	Self->SetRelativeRotation(FRotator(-90.f, 0.f, 0.f));
	Self->SetRelativeScale3D(FVector(0.9f * S, 0.9f * S, 1.6f * S));
	Pieces.Add(Self);

	// the emitter's beam up to the disc: a faint column
	UMaterialInstanceDynamic* Beam = BlipMaterial ? UMaterialInstanceDynamic::Create(BlipMaterial, this) : nullptr;
	if (Beam)
	{
		Beam->SetVectorParameterValue(TEXT("Colour"), ContactColour);
		Beam->SetScalarParameterValue(TEXT("Intensity"), 0.25f);
	}
	UStaticMeshComponent* Column = MakePiece(CylinderMesh, Beam, TEXT("HoloRadarBeam"));
	Column->SetRelativeLocation(FVector(0.f, 0.f, DiscHeightCm * 0.5f));
	Column->SetRelativeScale3D(FVector(1.2f * S, 1.2f * S, DiscHeightCm * S));
	Pieces.Add(Column);

	UMaterialInstanceDynamic* StalkMaterial = BlipMaterial ? UMaterialInstanceDynamic::Create(BlipMaterial, this) : nullptr;
	if (StalkMaterial)
	{
		StalkMaterial->SetVectorParameterValue(TEXT("Colour"), ContactColour);
		StalkMaterial->SetScalarParameterValue(TEXT("Intensity"), 1.5f);
	}
	for (int32 i = 0; i < MaxBlips; ++i)
	{
		UMaterialInstanceDynamic* M = BlipMaterial ? UMaterialInstanceDynamic::Create(BlipMaterial, this) : nullptr;
		BlipMaterials.Add(M);
		Blips.Add(MakePiece(SphereMesh, M, FName(*FString::Printf(TEXT("HoloRadarBlip%d"), i))));
		Stalks.Add(MakePiece(CylinderMesh, StalkMaterial, FName(*FString::Printf(TEXT("HoloRadarStalk%d"), i))));
	}
	UpdateContacts();
	ApplyVisibility();
}

void USpaceHoloRadarComponent::SetRadarOn(bool bOn)
{
	bRadarOn = bOn;
	ApplyVisibility();
}

void USpaceHoloRadarComponent::ApplyVisibility()
{
	const ASpaceshipPawn* Live = Ship.Get();
	const bool bShow = bHasRadar && bRadarOn && Live && Live->IsPowered();
	bShown = bShow;
	for (UStaticMeshComponent* Piece : Pieces)
	{
		Piece->SetVisibility(bShow);
	}
	for (int32 i = 0; i < Blips.Num(); ++i)
	{
		Blips[i]->SetVisibility(bShow && i < ActiveBlips);
		Stalks[i]->SetVisibility(bShow && i < ActiveBlips);
	}
}

void USpaceHoloRadarComponent::UpdateContacts()
{
	const ASpaceshipPawn* Live = Ship.Get();
	if (!Live)
	{
		return;
	}
	const TArray<FSpaceRadarContact> Contacts = USpaceCockpitDisplays::MakeRadarContacts(Live, RangeM, MaxBlips);
	const float S = 1.f / HoloRadarDefaults::ShapeCm;
	const float PerM = RadiusCm / FMath::Max(RangeM, 1.f);
	ActiveBlips = FMath::Min(Contacts.Num(), MaxBlips);
	for (int32 i = 0; i < ActiveBlips; ++i)
	{
		const FSpaceRadarContact& C = Contacts[i];
		// ship frame: X ahead, Y right, Z up; the contact: Position X right, Y ahead (m)
		FVector P(C.Position.Y * PerM, C.Position.X * PerM, C.HeightM * PerM);
		float Size = 0.7f;
		FLinearColor Colour = ContactColour;
		if (C.bBody)
		{
			// a body: a bearing on the rim, level with the disc
			const FVector2D Flat = FVector2D(P.X, P.Y).GetSafeNormal() * RadiusCm;
			P = FVector(Flat.X, Flat.Y, 0.f);
			Size = 1.1f;
			Colour = BodyColour;
		}
		else
		{
			const FVector2D Flat(P.X, P.Y);
			if (Flat.Size() > RadiusCm)
			{
				const FVector2D In = Flat.GetSafeNormal() * RadiusCm;
				P.X = In.X;
				P.Y = In.Y;
			}
			P.Z = FMath::Clamp(P.Z, -DiscHeightCm * 0.9f, RadiusCm * 0.7f);
		}
		Blips[i]->SetRelativeLocation(FVector(P.X, P.Y, DiscHeightCm + P.Z));
		Blips[i]->SetRelativeScale3D(FVector(Size * S));
		if (UMaterialInstanceDynamic* M = BlipMaterials[i])
		{
			M->SetVectorParameterValue(TEXT("Colour"), Colour);
			M->SetScalarParameterValue(TEXT("Intensity"), C.bBody ? 5.f : 8.f);
		}
		// the stalk from the disc to the point (none for a body on the rim)
		const float H = FMath::Abs(P.Z);
		Stalks[i]->SetRelativeLocation(FVector(P.X, P.Y, DiscHeightCm + P.Z * 0.5f));
		Stalks[i]->SetRelativeScale3D(FVector(0.12f * S, 0.12f * S, FMath::Max(H, 0.01f) * S));
	}
	if (bShown)
	{
		ApplyVisibility();          // the number of points may have changed
	}
}

void USpaceHoloRadarComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	const ASpaceshipPawn* Live = Ship.Get();
	if (!Live)
	{
		return;
	}
	SinceUpdate += DeltaTime;
	if (bShown && SinceUpdate >= 1.f / FMath::Max(UpdateHz, 0.1f))
	{
		SinceUpdate = 0.f;
		UpdateContacts();
	}
	const bool bWant = bHasRadar && bRadarOn && Live->IsPowered();
	if (bWant != bShown)
	{
		ApplyVisibility();
	}
}
