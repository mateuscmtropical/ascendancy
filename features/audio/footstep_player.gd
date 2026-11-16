class_name FootstepPlayer
extends AudioStreamPlayer3D
## Passos do corpo pai (CharacterBody3D) conforme o piso embaixo dele: cadência que sobe com a
## velocidade, impulso ao pular, pouso ao cair de um pulo, silêncio no ar e parado.
## O filho GroundProbe (RayCast3D para baixo) diz qual colisor está sob os pés.

const STEP_SOUNDS: Dictionary[GroundSurface.Kind, AudioStream] = {
	GroundSurface.Kind.STONE: preload("res://art/audio/step_stone.tres"),
	GroundSurface.Kind.GRASS: preload("res://art/audio/step_grass.tres"),
	GroundSurface.Kind.WOOD: preload("res://art/audio/step_wood.tres"),
	GroundSurface.Kind.DIRT: preload("res://art/audio/step_dirt.tres"),
}
const JUMP_SOUNDS: Dictionary[GroundSurface.Kind, AudioStream] = {
	GroundSurface.Kind.STONE: preload("res://art/audio/jump_stone.tres"),
	GroundSurface.Kind.GRASS: preload("res://art/audio/jump_grass.tres"),
	GroundSurface.Kind.WOOD: preload("res://art/audio/jump_wood.tres"),
	GroundSurface.Kind.DIRT: preload("res://art/audio/jump_dirt.tres"),
}
const LAND_SOUNDS: Dictionary[GroundSurface.Kind, AudioStream] = {
	GroundSurface.Kind.STONE: preload("res://art/audio/land_stone.tres"),
	GroundSurface.Kind.GRASS: preload("res://art/audio/land_grass.tres"),
	GroundSurface.Kind.WOOD: preload("res://art/audio/land_wood.tres"),
	GroundSurface.Kind.DIRT: preload("res://art/audio/land_dirt.tres"),
}
const MIN_STEP_SPEED: float = 0.4
const MIN_STEPS_PER_SECOND: float = 1.8
const MAX_STEPS_PER_SECOND: float = 3.0
const STEPS_PER_SECOND_PER_SPEED: float = 0.17
const BASE_STEPS_PER_SECOND: float = 1.6
## Ao começar a andar o primeiro passo vem logo, não depois de uma passada inteira.
const FIRST_STEP_PROGRESS: float = 0.7
## Descer um meio-fio também tira o pé do chão; só queda mais rápida que isto soa como pouso.
const LANDING_FALL_SPEED: float = 4.0

var _body: CharacterBody3D
var _step_progress: float = FIRST_STEP_PROGRESS
var _was_grounded: bool = true
var _fall_speed: float = 0.0

@onready var _ground_probe: RayCast3D = $GroundProbe


func _ready() -> void:
	_body = get_parent() as CharacterBody3D


func _physics_process(delta: float) -> void:
	var horizontal_speed: float = Vector2(_body.velocity.x, _body.velocity.z).length()
	var is_grounded: bool = _body.is_on_floor()
	var has_landed: bool = is_grounded and not _was_grounded
	var has_jumped: bool = _was_grounded and not is_grounded and _body.velocity.y > 0.0
	var steps_per_second: float = clampf(
		BASE_STEPS_PER_SECOND + STEPS_PER_SECOND_PER_SPEED * horizontal_speed,
		MIN_STEPS_PER_SECOND,
		MAX_STEPS_PER_SECOND
	)

	_was_grounded = is_grounded

	if has_jumped:
		_play_from(JUMP_SOUNDS)

	if has_landed:
		_play_from(LAND_SOUNDS if _fall_speed >= LANDING_FALL_SPEED else STEP_SOUNDS)
		return

	if not is_grounded:
		_fall_speed = -_body.velocity.y
		_step_progress = FIRST_STEP_PROGRESS
		return

	if horizontal_speed < MIN_STEP_SPEED:
		_step_progress = FIRST_STEP_PROGRESS
		return

	_step_progress += steps_per_second * delta

	if _step_progress >= 1.0:
		_play_from(STEP_SOUNDS)


func _play_from(sounds_by_surface: Dictionary[GroundSurface.Kind, AudioStream]) -> void:
	var surface: GroundSurface.Kind = GroundSurface.of(_ground_probe.get_collider())
	var sound: AudioStream = sounds_by_surface[surface]

	_step_progress = 0.0

	# Trocar o stream corta o som que está tocando: só troca quando muda.
	if stream != sound:
		stream = sound

	play()
