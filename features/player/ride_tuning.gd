class_name RideTuning
extends RefCounted
## Números da montaria (Mula sem cabeça) usados pelo PlayerController: velocidades por postura,
## animações da mula e do cavaleiro, pulo, voo, turbo de fogo e degrau que ela vence andando.

const SPEED_BY_STANCE: Dictionary[PlayerController.Stance, float] = {
	PlayerController.Stance.IDLE: 0.0,
	PlayerController.Stance.WALK: 4.0,
	PlayerController.Stance.RUN: 16.0,
	PlayerController.Stance.SPRINT: 24.0,
	PlayerController.Stance.AIRBORNE: 16.0,
	PlayerController.Stance.HOVER: 0.0,
	PlayerController.Stance.FLY: 28.0,
}
const MULA_ANIMATION_BY_STANCE: Dictionary[PlayerController.Stance, StringName] = {
	PlayerController.Stance.IDLE: MulaSemCabeca.IDLE_ANIMATION,
	PlayerController.Stance.WALK: MulaSemCabeca.WALK_ANIMATION,
	PlayerController.Stance.RUN: MulaSemCabeca.RUN_ANIMATION,
	PlayerController.Stance.SPRINT: MulaSemCabeca.RUN_ANIMATION,
	PlayerController.Stance.AIRBORNE: MulaSemCabeca.RUN_ANIMATION,
	PlayerController.Stance.HOVER: MulaSemCabeca.WALK_ANIMATION,
	PlayerController.Stance.FLY: MulaSemCabeca.RUN_ANIMATION,
}
const IDLE_ANIMATION: StringName = &"combat/Ride_Idle"
const GALLOP_ANIMATION: StringName = &"combat/Ride_Gallop"
const RIDER_ANIMATION_BY_STANCE: Dictionary[PlayerController.Stance, StringName] = {
	PlayerController.Stance.IDLE: IDLE_ANIMATION,
	PlayerController.Stance.HOVER: IDLE_ANIMATION,
}
## A mula acelera rápido (montaria lendária) e gira devagar.
const ACCELERATION: float = 30.0
const TURN_SPEED: float = 5.0
const CLIMB_SPEED: float = 9.0
const JUMP_VELOCITY: float = 9.0
## Canteiro, banco, meio-fio: a mula passa por cima andando, sem pular.
const STEP_HEIGHT: float = 0.75
## Dois toques no correr: jato de fogo pela traseira que multiplica a velocidade por um tempo.
const TURBO_SPEED_SCALE: float = 1.9
const TURBO_ACCELERATION: float = 70.0
const TURBO_SECONDS: float = 2.5
## O assento do esqueleto fica esta altura acima dos pés do modelo.
const RIDER_SEAT_HEIGHT: float = 0.78
const CAMERA_LIFT: float = 1.0
## Apeando, o jogador desce por este lado da mula (metros, para a esquerda dela).
const DISMOUNT_SIDE_OFFSET: float = 1.3
