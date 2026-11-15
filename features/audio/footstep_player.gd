class_name FootstepPlayer
extends AudioStreamPlayer3D
## Passos do corpo pai (CharacterBody3D): cadência que sobe com a velocidade, um passo ao pousar,
## silêncio no ar e parado. O stream é um AudioStreamRandomizer com as variações do passo.

const MIN_STEP_SPEED: float = 0.4
const MIN_STEPS_PER_SECOND: float = 1.8
const MAX_STEPS_PER_SECOND: float = 3.0
const STEPS_PER_SECOND_PER_SPEED: float = 0.17
const BASE_STEPS_PER_SECOND: float = 1.6
## Ao começar a andar o primeiro passo vem logo, não depois de uma passada inteira.
const FIRST_STEP_PROGRESS: float = 0.7

var _body: CharacterBody3D
var _step_progress: float = FIRST_STEP_PROGRESS
var _was_grounded: bool = true


func _ready() -> void:
	_body = get_parent() as CharacterBody3D


func _physics_process(delta: float) -> void:
	var horizontal_speed: float = Vector2(_body.velocity.x, _body.velocity.z).length()
	var is_grounded: bool = _body.is_on_floor()
	var has_landed: bool = is_grounded and not _was_grounded
	var steps_per_second: float = clampf(
		BASE_STEPS_PER_SECOND + STEPS_PER_SECOND_PER_SPEED * horizontal_speed,
		MIN_STEPS_PER_SECOND,
		MAX_STEPS_PER_SECOND
	)

	_was_grounded = is_grounded

	if has_landed:
		_step()
		return

	if not is_grounded or horizontal_speed < MIN_STEP_SPEED:
		_step_progress = FIRST_STEP_PROGRESS
		return

	_step_progress += steps_per_second * delta

	if _step_progress >= 1.0:
		_step()


func _step() -> void:
	_step_progress = 0.0
	play()
