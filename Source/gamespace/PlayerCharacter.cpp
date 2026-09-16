// Copyright Epic Games, Inc. All Rights Reserved.

#include "PlayerCharacter.h"

#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "EngineUtils.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/LocalPlayer.h"
#include "Engine/SkeletalMesh.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "InputAction.h"
#include "InputActionValue.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "InputTriggers.h"
#include "SpaceshipPawn.h"
#include "UObject/ConstructorHelpers.h"

DEFINE_LOG_CATEGORY_STATIC(LogPlayerCharacter, Log, All);

namespace PlayerCharacterDefaults
{
	const TCHAR* const MeshPath = TEXT("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple");
	const TCHAR* const MappingContextPath = TEXT("/Game/Input/IMC_Character.IMC_Character");
	const TCHAR* const MoveActionPath = TEXT("/Game/Input/IA_CharMove.IA_CharMove");
	const TCHAR* const LookActionPath = TEXT("/Game/Input/IA_CharLook.IA_CharLook");
	const TCHAR* const JumpActionPath = TEXT("/Game/Input/IA_CharJump.IA_CharJump");
	const TCHAR* const SprintActionPath = TEXT("/Game/Input/IA_CharSprint.IA_CharSprint");
	const TCHAR* const InteractActionPath = TEXT("/Game/Input/IA_Interact.IA_Interact");

	constexpr float CapsuleRadius = 42.f;
	constexpr float CapsuleHalfHeight = 96.f;

	template <typename T>
	T* LoadOptional(const TCHAR* Path)
	{
		return Cast<T>(StaticLoadObject(T::StaticClass(), nullptr, Path, nullptr, LOAD_NoWarn | LOAD_Quiet));
	}
}

APlayerCharacter::APlayerCharacter()
{
	PrimaryActorTick.bCanEverTick = true;
	// Before Character Movement, so this frame's movement already uses this frame's gravity.
	PrimaryActorTick.TickGroup = TG_PrePhysics;

	GetCapsuleComponent()->InitCapsuleSize(PlayerCharacterDefaults::CapsuleRadius, PlayerCharacterDefaults::CapsuleHalfHeight);

	// The character turns towards where it walks; the view is independent (see UpdateView).
	bUseControllerRotationPitch = false;
	bUseControllerRotationYaw = false;
	bUseControllerRotationRoll = false;

	UCharacterMovementComponent* Movement = GetCharacterMovement();
	Movement->bOrientRotationToMovement = true;
	Movement->RotationRate = FRotator(0.f, 540.f, 0.f);
	Movement->MaxWalkSpeed = WalkSpeed;
	Movement->JumpZVelocity = JumpVelocity;
	Movement->AirControl = 0.35f;
	Movement->BrakingDecelerationWalking = 2000.f;
	Movement->BrakingDecelerationFalling = 300.f;

	USkeletalMeshComponent* SkeletalMesh = GetMesh();
	// Mannequin feet at the capsule bottom, facing the capsule's +X (the mesh faces +Y).
	SkeletalMesh->SetRelativeLocationAndRotation(FVector(0.f, 0.f, -PlayerCharacterDefaults::CapsuleHalfHeight), FRotator(0.f, -90.f, 0.f));
	SkeletalMesh->SetAnimationMode(EAnimationMode::AnimationBlueprint);
	SkeletalMesh->SetAnimInstanceClass(UPlayerCharacterAnimInstance::StaticClass());
	static ConstructorHelpers::FObjectFinderOptional<USkeletalMesh> Manny(PlayerCharacterDefaults::MeshPath);
	if (Manny.Get())
	{
		SkeletalMesh->SetSkeletalMeshAsset(Manny.Get());
	}

	CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
	CameraBoom->SetupAttachment(GetCapsuleComponent());
	CameraBoom->TargetArmLength = 380.f;
	CameraBoom->SocketOffset = FVector(0.f, 55.f, 65.f);
	CameraBoom->bUsePawnControlRotation = false;
	// Rotated to the view directly each tick, not with the capsule that turns towards movement.
	CameraBoom->SetUsingAbsoluteRotation(true);
	CameraBoom->bDoCollisionTest = true;
	CameraBoom->ProbeSize = 12.f;
	CameraBoom->bEnableCameraLag = true;
	CameraBoom->CameraLagSpeed = 14.f;
	CameraBoom->CameraLagMaxDistance = 150.f;

	FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FollowCamera"));
	FollowCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
	FollowCamera->bUsePawnControlRotation = false;
	FollowCamera->SetFieldOfView(80.f);
}

void APlayerCharacter::BeginPlay()
{
	Super::BeginPlay();
	GetCharacterMovement()->MaxWalkSpeed = WalkSpeed;
	GetCharacterMovement()->JumpZVelocity = JumpVelocity;

	// Gravity before the first movement tick, or the character starts falling along world -Z.
	GravityFrame = GetActorQuat();
	UpdateGravity();
	FaceDirection(GetActorForwardVector());
}

// -------------------------------------------------------------------------------------------
// Gravity and view
// -------------------------------------------------------------------------------------------

float APlayerCharacter::ComputeGravityScale(float GravityCmS2, float WorldGravityZ)
{
	return FMath::Max(0.f, GravityCmS2) / FMath::Max(FMath::Abs(WorldGravityZ), 1.f);
}

FRotator APlayerCharacter::TransportGravityFrame(const FRotator& Frame, const FVector& NewUp)
{
	const FQuat Quat = Frame.Quaternion();
	const FVector Up = NewUp.GetSafeNormal();
	if (Up.IsNearlyZero())
	{
		return Frame;
	}
	return (FQuat::FindBetweenNormals(Quat.GetUpVector(), Up) * Quat).GetNormalized().Rotator();
}

FRotator APlayerCharacter::ComputeViewRotation(const FRotator& Frame, float Yaw, float Pitch)
{
	return (Frame.Quaternion() * FRotator(Pitch, Yaw, 0.f).Quaternion()).Rotator();
}

void APlayerCharacter::UpdateGravity()
{
	ACelestialBody::FindNearest(GetWorld(), GetActorLocation(), &Environment, &bHasEnvironment);
	if (!bHasEnvironment)
	{
		return;
	}
	UCharacterMovementComponent* Movement = GetCharacterMovement();
	Movement->SetGravityDirection(-Environment.Up);
	Movement->GravityScale = ComputeGravityScale(float(Environment.GravityCmS2), GetWorld()->GetGravityZ());

	// Quaternion version of TransportGravityFrame: no rotator round trip every frame.
	GravityFrame = (FQuat::FindBetweenNormals(GravityFrame.GetUpVector(), Environment.Up) * GravityFrame).GetNormalized();
}

void APlayerCharacter::FaceDirection(const FVector& Forward)
{
	const FVector Up = GravityFrame.GetUpVector();
	const FVector Flat = FVector::VectorPlaneProject(Forward, Up).GetSafeNormal();
	if (Flat.IsNearlyZero())
	{
		return;
	}
	// Reset the frame's heading to the direction, so LookYaw = 0 looks along it.
	GravityFrame = FRotationMatrix::MakeFromXZ(Flat, Up).ToQuat();
	LookYaw = 0.f;
	SetActorRotation(GravityFrame);
	UpdateView();
}

void APlayerCharacter::UpdateView()
{
	CameraBoom->SetWorldRotation(GravityFrame * FRotator(LookPitch, LookYaw, 0.f).Quaternion());
	if (AController* PawnController = GetController())
	{
		// Only for systems that read it (audio listener, AI perception); nothing here steers by it.
		PawnController->SetControlRotation(CameraBoom->GetComponentRotation());
	}
}

void APlayerCharacter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	UpdateGravity();

	UCharacterMovementComponent* Movement = GetCharacterMovement();
	Movement->MaxWalkSpeed = bSprintHeld ? SprintSpeed : WalkSpeed;
	Movement->JumpZVelocity = JumpVelocity;

	if (!MoveInput.IsNearlyZero())
	{
		// Relative to where the camera looks, flattened onto the local ground.
		const FQuat Heading = GravityFrame * FRotator(0.f, LookYaw, 0.f).Quaternion();
		AddMovementInput(Heading.GetForwardVector(), float(MoveInput.Y));
		AddMovementInput(Heading.GetRightVector(), float(MoveInput.X));
	}

	UpdateView();
}

// -------------------------------------------------------------------------------------------
// Input
// -------------------------------------------------------------------------------------------

void APlayerCharacter::ResolveInputAssets()
{
	using namespace PlayerCharacterDefaults;
	if (!CharacterMappingContext) { CharacterMappingContext = LoadOptional<UInputMappingContext>(MappingContextPath); }
	if (!MoveAction) { MoveAction = LoadOptional<UInputAction>(MoveActionPath); }
	if (!LookAction) { LookAction = LoadOptional<UInputAction>(LookActionPath); }
	if (!JumpAction) { JumpAction = LoadOptional<UInputAction>(JumpActionPath); }
	if (!SprintAction) { SprintAction = LoadOptional<UInputAction>(SprintActionPath); }
	if (!InteractAction) { InteractAction = LoadOptional<UInputAction>(InteractActionPath); }

	if (CharacterMappingContext && MoveAction && LookAction && JumpAction && SprintAction && InteractAction)
	{
		return;
	}

	// Same fallback as the ship: flyable - here walkable - without the assets.
	UE_LOG(LogPlayerCharacter, Warning, TEXT("%s builds its input procedurally; run Tools/Assets/add_character_input.py."), *GetName());
	auto Make = [this](const TCHAR* Name, EInputActionValueType Type)
	{
		UInputAction* Action = NewObject<UInputAction>(this, FName(Name));
		Action->ValueType = Type;
		return Action;
	};
	MoveAction = Make(TEXT("IA_CharMove_Runtime"), EInputActionValueType::Axis2D);
	MoveAction->AccumulationBehavior = EInputActionAccumulationBehavior::Cumulative;
	LookAction = Make(TEXT("IA_CharLook_Runtime"), EInputActionValueType::Axis2D);
	JumpAction = Make(TEXT("IA_CharJump_Runtime"), EInputActionValueType::Boolean);
	SprintAction = Make(TEXT("IA_CharSprint_Runtime"), EInputActionValueType::Boolean);
	InteractAction = Make(TEXT("IA_Interact_Runtime"), EInputActionValueType::Boolean);
	InteractAction->Triggers.Add(NewObject<UInputTriggerPressed>(InteractAction));

	UInputMappingContext* Context = NewObject<UInputMappingContext>(this, FName(TEXT("IMC_Character_Runtime")));
	auto MapMove = [Context, this](const FKey& Key, bool bSwizzle, bool bNegate)
	{
		FEnhancedActionKeyMapping& Mapping = Context->MapKey(MoveAction, Key);
		if (bSwizzle)
		{
			Mapping.Modifiers.Add(NewObject<UInputModifierSwizzleAxis>(Context));
		}
		if (bNegate)
		{
			Mapping.Modifiers.Add(NewObject<UInputModifierNegate>(Context));
		}
	};
	MapMove(EKeys::W, true, false);
	MapMove(EKeys::S, true, true);
	MapMove(EKeys::D, false, false);
	MapMove(EKeys::A, false, true);
	Context->MapKey(LookAction, EKeys::Mouse2D);
	Context->MapKey(JumpAction, EKeys::SpaceBar);
	Context->MapKey(SprintAction, EKeys::LeftShift);
	Context->MapKey(InteractAction, EKeys::F);
	CharacterMappingContext = Context;
}

void APlayerCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);
	ResolveInputAssets();

	if (UEnhancedInputComponent* Input = Cast<UEnhancedInputComponent>(PlayerInputComponent))
	{
		Input->BindAction(MoveAction, ETriggerEvent::Triggered, this, &APlayerCharacter::HandleMove);
		Input->BindAction(MoveAction, ETriggerEvent::Completed, this, &APlayerCharacter::HandleMoveCompleted);
		Input->BindAction(LookAction, ETriggerEvent::Triggered, this, &APlayerCharacter::HandleLook);
		Input->BindAction(JumpAction, ETriggerEvent::Started, this, &APlayerCharacter::HandleJump);
		Input->BindAction(JumpAction, ETriggerEvent::Completed, this, &APlayerCharacter::HandleJumpReleased);
		Input->BindAction(SprintAction, ETriggerEvent::Triggered, this, &APlayerCharacter::HandleSprint);
		Input->BindAction(SprintAction, ETriggerEvent::Completed, this, &APlayerCharacter::HandleSprintReleased);
		Input->BindAction(InteractAction, ETriggerEvent::Started, this, &APlayerCharacter::HandleInteract);
	}

	const APlayerController* PlayerController = Cast<APlayerController>(GetController());
	if (UEnhancedInputLocalPlayerSubsystem* Subsystem = PlayerController
		? ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(PlayerController->GetLocalPlayer()) : nullptr)
	{
		Subsystem->AddMappingContext(CharacterMappingContext, 0);
	}
}

void APlayerCharacter::UnPossessed()
{
	// The ship's contexts must not see WASD / mouse routed to a character that is gone, and the
	// character's must not stay active in the ship: the controller is still set at this point.
	if (const APlayerController* PlayerController = Cast<APlayerController>(GetController()))
	{
		if (UEnhancedInputLocalPlayerSubsystem* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(PlayerController->GetLocalPlayer()))
		{
			Subsystem->RemoveMappingContext(CharacterMappingContext);
		}
	}
	MoveInput = FVector2D::ZeroVector;
	bSprintHeld = false;
	Super::UnPossessed();
}

void APlayerCharacter::HandleMove(const FInputActionValue& Value)
{
	MoveInput = Value.Get<FVector2D>();
}

void APlayerCharacter::HandleMoveCompleted(const FInputActionValue& /*Value*/)
{
	MoveInput = FVector2D::ZeroVector;
}

void APlayerCharacter::HandleLook(const FInputActionValue& Value)
{
	const FVector2D Delta = Value.Get<FVector2D>() * LookSensitivity;
	LookYaw = FRotator::NormalizeAxis(LookYaw + float(Delta.X));
	LookPitch = FMath::Clamp(LookPitch + float(Delta.Y) * (bInvertPitch ? -1.f : 1.f), MinViewPitch, MaxViewPitch);
}

void APlayerCharacter::HandleJump(const FInputActionValue& /*Value*/)
{
	Jump();
}

void APlayerCharacter::HandleJumpReleased(const FInputActionValue& /*Value*/)
{
	StopJumping();
}

void APlayerCharacter::HandleSprint(const FInputActionValue& /*Value*/)
{
	bSprintHeld = true;
}

void APlayerCharacter::HandleSprintReleased(const FInputActionValue& /*Value*/)
{
	bSprintHeld = false;
}

void APlayerCharacter::HandleInteract(const FInputActionValue& /*Value*/)
{
	TryBoardShip();
}

// -------------------------------------------------------------------------------------------
// Ship
// -------------------------------------------------------------------------------------------

ASpaceshipPawn* APlayerCharacter::FindBoardableShip(double& OutDistanceCm) const
{
	ASpaceshipPawn* Best = nullptr;
	OutDistanceCm = TNumericLimits<double>::Max();
	for (TActorIterator<ASpaceshipPawn> It(GetWorld()); It; ++It)
	{
		if (!It->IsLanded() || It->IsPlayerControlled())
		{
			continue;
		}
		const double Distance = It->GetDistanceToHull(GetActorLocation());
		if (Distance <= BoardingRangeCm && Distance < OutDistanceCm)
		{
			OutDistanceCm = Distance;
			Best = *It;
		}
	}
	return Best;
}

bool APlayerCharacter::TryBoardShip()
{
	// The pilot appears within boarding range of the ship it left: one F press must not undo it.
	if (GetGameTimeSinceCreation() < BoardingCooldownSeconds)
	{
		return false;
	}
	double Distance = 0.0;
	ASpaceshipPawn* Ship = FindBoardableShip(Distance);
	APlayerController* PlayerController = Cast<APlayerController>(GetController());
	if (!Ship || !PlayerController)
	{
		return false;
	}
	UE_LOG(LogPlayerCharacter, Log, TEXT("%s boards %s (%.0f cm from the hull)"), *GetName(), *Ship->GetName(), Distance);
	PlayerController->Possess(Ship);
	Ship->OnBoarded();
	Destroy();
	return true;
}

FFootIKState APlayerCharacter::GetFootIKState() const
{
	const UPlayerCharacterAnimInstance* Anim = Cast<UPlayerCharacterAnimInstance>(GetMesh()->GetAnimInstance());
	return Anim ? Anim->GetFootIKState() : FFootIKState();
}

// -------------------------------------------------------------------------------------------
// Tests
// -------------------------------------------------------------------------------------------

TArray<FVector> APlayerCharacter::DebugSampleAnimation(float GroundSpeed, bool bFalling, bool bOverrideGround, float LeftGroundCm, float RightGroundCm, float Seconds)
{
	TArray<FVector> Result;
	USkeletalMeshComponent* SkeletalMesh = GetMesh();
	// Editor worlds (tests) do not tick animation unless asked to.
	SkeletalMesh->SetUpdateAnimationInEditor(true);
	if (!SkeletalMesh->GetAnimInstance())
	{
		SkeletalMesh->InitAnim(true);
	}
	UPlayerCharacterAnimInstance* Anim = Cast<UPlayerCharacterAnimInstance>(SkeletalMesh->GetAnimInstance());
	if (!Anim)
	{
		return Result;
	}
	Anim->SetDebugOverride(true, GroundSpeed, bFalling, bOverrideGround, LeftGroundCm, RightGroundCm);
	const float Step = 1.f / 30.f;
	for (float Time = 0.f; Time < Seconds; Time += Step)
	{
		// The proxy runs its native Update once per engine frame (GFrameCounter). A commandlet
		// never advances frames, so step it here as a game would.
		++GFrameCounter;
		SkeletalMesh->TickAnimation(Step, false);
		SkeletalMesh->RefreshBoneTransforms();
	}
	for (const TCHAR* Bone : { TEXT("pelvis"), TEXT("foot_l"), TEXT("foot_r"), TEXT("thigh_l"), TEXT("thigh_r"), TEXT("calf_l"), TEXT("calf_r") })
	{
		const int32 Index = SkeletalMesh->GetBoneIndex(FName(Bone));
		Result.Add(Index == INDEX_NONE ? FVector(TNumericLimits<float>::Max()) : SkeletalMesh->GetBoneTransform(Index, FTransform::Identity).GetLocation());
	}
	Anim->SetDebugOverride(false, 0.f, false, false, 0.f, 0.f);
	// One more update so the counters include the last evaluation.
	++GFrameCounter;
	SkeletalMesh->TickAnimation(Step, false);
	const FIntVector Counters = Anim->GetProxyCounters();
	Result.Add(FVector(Counters));
	UE_LOG(LogPlayerCharacter, Log, TEXT("DebugSampleAnimation: anim %s, mesh %s, render data %d, required bones %d, pre-update %d, update %d, evaluate %d"),
		*GetNameSafe(Anim), *GetNameSafe(SkeletalMesh->GetSkeletalMeshAsset()), SkeletalMesh->GetSkeletalMeshRenderData() != nullptr,
		SkeletalMesh->RequiredBones.Num(), Counters.X, Counters.Y, Counters.Z);
	return Result;
}
