class_name MulaMount
extends Area3D
## Montaria da Mula: com o jogador perto, E monta (ele passa a guiar a mula pelo chão e pelo ar)
## e E de novo apeia. Montado, o aviso some: a mula vai junto e a área também. Chamada de longe
## (summon_to), ela voa num arco por cima de tudo e pousa ao lado de quem chamou.

const PROMPT_TEXT: String = "E: montar na mula"
const GROUP: StringName = &"mounts"
const SUMMON_SPEED: float = 32.0
## Altura do arco do voo de chamada, por metro de distância (com mínimo e máximo).
const SUMMON_ARC_PER_METER: float = 0.25
const SUMMON_ARC_LIMITS: Vector2 = Vector2(6.0, 40.0)
## Pousa a este tanto de quem chamou, ao lado e um pouco à frente.
const SUMMON_LANDING_OFFSET: Vector3 = Vector3(1.8, 0.0, 1.2)
const SUMMON_TURN_SPEED: float = 6.0

var _player_near: PlayerController
var _rider: PlayerController
var _flight_start: Vector3
var _flight_target: Vector3
var _flight_arc: float = 0.0
var _flight_progress: float = 1.0
var _flight_length: float = 0.0

@onready var _mula: MulaSemCabeca = get_parent() as MulaSemCabeca
@onready var _prompt: Label3D = $Prompt


func _enter_tree() -> void:
	add_to_group(GROUP)


func _ready() -> void:
	set_physics_process(false)
	_prompt.text = PROMPT_TEXT
	body_entered.connect(_on_body_entered)
	body_exited.connect(_on_body_exited)
	_refresh_prompt()


func _unhandled_input(event: InputEvent) -> void:
	var player: PlayerController = _rider if _rider != null else _player_near

	if player == null or not event.is_action_pressed(&"interact") or is_flying_to_caller():
		return

	get_viewport().set_input_as_handled()
	toggle_ride(player)


## Monta o jogador na mula ou, se ele já está montado, apeia.
func toggle_ride(player: PlayerController) -> void:
	if _rider != null:
		_rider.dismount()
		_rider = null
		_refresh_prompt()

		return

	_rider = player
	player.ride(_mula)
	_refresh_prompt()


func is_ridden() -> bool:
	return _rider != null


## Chamada: de onde estiver, a mula voa até ao lado de quem chamou.
func summon_to(caller: Node3D) -> void:
	var side: Vector3 = caller.global_basis * SUMMON_LANDING_OFFSET

	if _rider != null:
		return

	_flight_start = _mula.global_position
	_flight_target = caller.global_position + Vector3(side.x, 0.0, side.z)
	_flight_length = maxf(_flight_start.distance_to(_flight_target), 0.01)
	_flight_arc = clampf(
		_flight_length * SUMMON_ARC_PER_METER, SUMMON_ARC_LIMITS.x, SUMMON_ARC_LIMITS.y
	)
	_flight_progress = 0.0
	_mula.is_airborne = true
	_mula.play_animation(MulaSemCabeca.RUN_ANIMATION)
	set_physics_process(true)


func is_flying_to_caller() -> bool:
	return _flight_progress < 1.0


func _physics_process(delta: float) -> void:
	var previous: Vector3 = _mula.global_position
	var heading: Vector3
	var next_position: Vector3

	_flight_progress = minf(_flight_progress + SUMMON_SPEED * delta / _flight_length, 1.0)
	next_position = summon_flight_point(
		_flight_start, _flight_target, _flight_arc, _flight_progress
	)
	heading = next_position - previous
	_mula.global_position = next_position

	if Vector2(heading.x, heading.z).length() > 0.001:
		_mula.global_rotation.y = lerp_angle(
			_mula.global_rotation.y, atan2(heading.x, heading.z), SUMMON_TURN_SPEED * delta
		)

	if _flight_progress < 1.0:
		return

	_mula.is_airborne = false
	_mula.play_animation(MulaSemCabeca.IDLE_ANIMATION)
	set_physics_process(false)


## Ponto do voo de chamada: reta do começo ao alvo com um arco (seno) por cima.
static func summon_flight_point(
	start: Vector3, target: Vector3, arc: float, progress: float
) -> Vector3:
	return start.lerp(target, progress) + Vector3.UP * arc * sin(progress * PI)


func _on_body_entered(body: Node3D) -> void:
	if body is PlayerController:
		_player_near = body as PlayerController
		_refresh_prompt()


func _on_body_exited(body: Node3D) -> void:
	if body == _player_near:
		_player_near = null
		_refresh_prompt()


func _refresh_prompt() -> void:
	_prompt.visible = _player_near != null and _rider == null
