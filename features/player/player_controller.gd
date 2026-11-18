class_name PlayerController
extends CharacterBody3D
## Personagem do jogador em terceira pessoa: anda relativo à câmera, corpo gira para a direção.
## Soco e chute param o passo e seguem a sequência de UnarmedFighter; depois o corpo fica
## em guarda por um tempo.
## Em build de debug, dois toques no pulo ligam o voo livre (atravessa paredes).

enum Stance { IDLE, WALK, RUN, SPRINT, AIRBORNE, HOVER, FLY, GUARD, ATTACK }

const SPEED_BY_STANCE: Dictionary[Stance, float] = {
	Stance.IDLE: 0.0,
	Stance.WALK: 1.6,
	Stance.RUN: 5.2,
	Stance.SPRINT: 8.2,
	Stance.HOVER: 0.0,
	Stance.FLY: 16.0,
	Stance.GUARD: 0.0,
	Stance.ATTACK: 0.0,
}
const ANIMATION_BY_STANCE: Dictionary[Stance, StringName] = {
	Stance.IDLE: &"ual1/Idle",
	Stance.WALK: &"ual1/Walk",
	Stance.RUN: &"ual1/Sprint",
	Stance.SPRINT: &"ual1/Sprint",
	Stance.AIRBORNE: &"ual1/Jump",
	Stance.HOVER: &"ual1/Swim_Idle",
	Stance.FLY: &"ual1/Swim_Fwd",
	Stance.GUARD: &"combat/Fight_Idle",
}
## A corrida e o sprint usam o mesmo ciclo; o passo acompanha a velocidade.
const ANIMATION_SPEED_BY_STANCE: Dictionary[Stance, float] = {
	Stance.RUN: 0.85,
	Stance.SPRINT: 1.25,
}
const JUMP_START_ANIMATION: StringName = &"ual1/Jump_Start"
const JUMP_LAND_ANIMATION: StringName = &"ual1/Jump_Land"
const ATTACK_BY_ACTION: Dictionary[StringName, UnarmedFighter.Attack] = {
	&"attack_punch": UnarmedFighter.Attack.PUNCH,
	&"attack_kick": UnarmedFighter.Attack.KICK,
}
const FACE_BY_STANCE: Dictionary[Stance, FaceAnimator.Mood] = {
	Stance.GUARD: FaceAnimator.Mood.FOCUSED,
	Stance.ATTACK: FaceAnimator.Mood.FOCUSED,
}
## Golpe entra seco: mistura curta com a pose anterior, senão o braço sai mole.
const ATTACK_BLEND_SECONDS: float = 0.08
## Saindo do descanso o corpo ainda tem de armar a guarda: mistura mais longa para não estalar.
const FIRST_ATTACK_BLEND_SECONDS: float = 0.16
## O esforço aparece no rosto no instante do acerto e some logo.
const STRIKE_FACE_SECONDS: float = 0.22
const GROUND_ACCELERATION: float = 22.0
const AIR_ACCELERATION: float = 6.0
const FLY_ACCELERATION: float = 40.0
const FLY_BOOST: float = 2.5
const TURN_SPEED: float = 12.0
## Pulo curto e firme: ~1,1 m de altura, ~0,6 s no ar; cai mais rápido do que sobe.
const JUMP_VELOCITY: float = 7.0
const RISE_GRAVITY: float = 22.0
const FALL_GRAVITY: float = 30.0
const DOUBLE_TAP_SECONDS: float = 0.3
const MOUSE_SENSITIVITY: float = 0.0025
const PITCH_MIN: float = -1.1
const PITCH_MAX: float = 0.45
## Degrau que o personagem sobe andando, sem pular: meio-fio, soleira, borda do terreiro.
const STEP_HEIGHT: float = 0.2
## Abaixo disto a normal do obstáculo é parede (degrau); acima, rampa que o move_and_slide já sobe.
const STEP_WALL_MAX_NORMAL_Y: float = 0.7
## Antecipação do teste do degrau, para o corpo encostar na borda já levantando.
const STEP_PROBE_SECONDS: float = 0.08

@export var is_input_enabled: bool = true

var is_flying: bool = false

var _stance: Stance = Stance.IDLE
var _takeoff_speed: float = 0.0
var _last_jump_press_seconds: float = -1.0
var _ground_collision_mask: int
var _camera_collision_mask: int

@onready var _model: CharacterModel = $CharacterModel
@onready var _fighter: UnarmedFighter = $UnarmedFighter
@onready var _camera_yaw: Node3D = $CameraYaw
@onready var _camera_pitch: Node3D = $CameraYaw/CameraPitch
@onready var _camera: Camera3D = $CameraYaw/CameraPitch/SpringArm3D/Camera3D
@onready var _spring_arm: SpringArm3D = $CameraYaw/CameraPitch/SpringArm3D
@onready var _avoidance_obstacle: NavigationObstacle3D = $AvoidanceObstacle


func _ready() -> void:
	_ground_collision_mask = collision_mask
	_camera_collision_mask = _spring_arm.collision_mask
	_fighter.move_started.connect(_on_move_started)
	_fighter.strike_reached.connect(_on_strike_reached)


func _unhandled_input(event: InputEvent) -> void:
	var is_mouse_captured: bool = Input.mouse_mode == Input.MOUSE_MODE_CAPTURED

	if not is_input_enabled:
		return

	if event is InputEventMouseButton and event.pressed and not is_mouse_captured:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

		return

	if event.is_action_pressed(&"jump") and not event.is_echo():
		_detect_double_jump_tap()

	_request_attack_from(event)

	if event is InputEventMouseMotion and is_mouse_captured:
		_rotate_camera(event.relative)


func _physics_process(delta: float) -> void:
	var input_vector: Vector2 = _read_move_input()

	_fighter.advance(delta)

	if is_flying:
		_fly(input_vector, delta)

		return

	_walk(input_vector, delta)


func make_camera_current() -> void:
	_camera.make_current()


func set_appearance(body_scene: PackedScene, hair_color: Color) -> void:
	_model.set_body(body_scene, hair_color)


func set_flying(should_fly: bool) -> void:
	is_flying = should_fly
	_fighter.cancel()
	collision_mask = 0 if should_fly else _ground_collision_mask
	_spring_arm.collision_mask = 0 if should_fly else _camera_collision_mask
	velocity = Vector3.ZERO


func _walk(input_vector: Vector2, delta: float) -> void:
	var move_direction: Vector3 = (
		_camera_yaw.global_basis * Vector3(input_vector.x, 0.0, input_vector.y)
	)
	var stance: Stance = _choose_ground_stance(input_vector)
	var is_grounded: bool = is_on_floor()
	var speed: float = SPEED_BY_STANCE[stance] if is_grounded else _takeoff_speed
	var target_velocity: Vector3 = move_direction.normalized() * speed
	var acceleration: float = GROUND_ACCELERATION if is_grounded else AIR_ACCELERATION
	var gravity: float = RISE_GRAVITY if velocity.y > 0.0 else FALL_GRAVITY

	velocity.x = move_toward(velocity.x, target_velocity.x, acceleration * delta)
	velocity.z = move_toward(velocity.z, target_velocity.z, acceleration * delta)
	velocity.y -= gravity * delta

	if is_grounded:
		_takeoff_speed = maxf(SPEED_BY_STANCE[stance], SPEED_BY_STANCE[Stance.RUN])

	if is_grounded and is_input_enabled and Input.is_action_just_pressed(&"jump"):
		velocity.y = JUMP_VELOCITY
		stance = Stance.AIRBORNE

	if stance == Stance.AIRBORNE:
		_fighter.cancel()

	if is_grounded:
		climb_step(Vector3(velocity.x, 0.0, velocity.z) * STEP_PROBE_SECONDS)

	move_and_slide()

	# NPCs desviam do jogador prevendo para onde ele vai.
	_avoidance_obstacle.velocity = Vector3(velocity.x, 0.0, velocity.z)
	_turn_model_toward(move_direction, delta)
	_apply_stance(stance)


## Sobe o corpo até o topo do degrau à frente, se o deslocamento horizontal motion bate numa
## parede baixa (até STEP_HEIGHT) com chão firme em cima. Devolve se subiu.
func climb_step(motion: Vector3) -> bool:
	var step_top: float = _step_top_ahead(motion)

	if step_top <= safe_margin:
		return false

	global_position.y += step_top

	return true


func _step_top_ahead(motion: Vector3) -> float:
	var blocking_hit: KinematicCollision3D = KinematicCollision3D.new()
	var landing_hit: KinematicCollision3D = KinematicCollision3D.new()
	var lift: Vector3 = Vector3.UP * STEP_HEIGHT
	var raised: Transform3D = global_transform.translated(lift)
	var is_blocked_by_wall: bool = (
		motion.length_squared() > 0.000001
		and test_move(global_transform, motion, blocking_hit)
		and blocking_hit.get_normal().y <= STEP_WALL_MAX_NORMAL_Y
	)
	var is_clear_above: bool = (
		is_blocked_by_wall
		and not test_move(global_transform, lift)
		and not test_move(raised, motion)
	)
	var has_firm_landing: bool = (
		is_clear_above
		and test_move(raised.translated(motion), -lift, landing_hit)
		and landing_hit.get_normal().y >= cos(floor_max_angle)
	)

	if not has_firm_landing:
		return 0.0

	return STEP_HEIGHT - landing_hit.get_travel().length()


func _fly(input_vector: Vector2, delta: float) -> void:
	var look_direction: Vector3 = (
		_camera_pitch.global_basis * Vector3(input_vector.x, 0.0, input_vector.y)
	)
	var climb: float = _read_climb_input()
	var stance: Stance = Stance.FLY if input_vector.length() > 0.0 or climb != 0.0 else Stance.HOVER
	var boost: float = FLY_BOOST if Input.is_action_pressed(&"sprint") else 1.0
	var target_velocity: Vector3 = (
		(look_direction + Vector3.UP * climb).limit_length(1.0)
		* SPEED_BY_STANCE[Stance.FLY]
		* boost
	)

	velocity = velocity.move_toward(target_velocity, FLY_ACCELERATION * boost * delta)
	move_and_slide()

	_avoidance_obstacle.velocity = Vector3.ZERO
	_turn_model_toward(Vector3(look_direction.x, 0.0, look_direction.z), delta)
	_apply_stance(stance)


func _read_move_input() -> Vector2:
	if not is_input_enabled:
		return Vector2.ZERO

	return Input.get_vector(&"move_left", &"move_right", &"move_forward", &"move_back")


func _read_climb_input() -> float:
	var climb_up: float = 1.0 if Input.is_action_pressed(&"jump") else 0.0
	var climb_down: float = 1.0 if Input.is_action_pressed(&"walk") else 0.0

	if not is_input_enabled:
		return 0.0

	return climb_up - climb_down


func _detect_double_jump_tap() -> void:
	var now_seconds: float = Time.get_ticks_msec() / 1000.0
	var is_double_tap: bool = now_seconds - _last_jump_press_seconds < DOUBLE_TAP_SECONDS

	_last_jump_press_seconds = now_seconds

	if not OS.is_debug_build() or not is_double_tap:
		return

	_last_jump_press_seconds = -1.0
	set_flying(not is_flying)


func _request_attack_from(event: InputEvent) -> void:
	var can_attack: bool = is_on_floor() and not is_flying

	if not can_attack or event.is_echo():
		return

	for action in ATTACK_BY_ACTION:
		if event.is_action_pressed(action):
			_fighter.request_attack(ATTACK_BY_ACTION[action])


func _on_move_started(move: UnarmedFighter.Move) -> void:
	var animation: StringName = _fighter.animation_of(move)
	var animation_speed: float = _fighter.animation_speed_of(move)
	var is_guard_up: bool = _stance == Stance.GUARD or _stance == Stance.ATTACK
	var blend_seconds: float = ATTACK_BLEND_SECONDS if is_guard_up else FIRST_ATTACK_BLEND_SECONDS

	_model.play_animation(animation, animation_speed, blend_seconds)


func _on_strike_reached(_move: UnarmedFighter.Move) -> void:
	_model.show_expression(FaceAnimator.Mood.EFFORT, STRIKE_FACE_SECONDS)


func _choose_ground_stance(input_vector: Vector2) -> Stance:
	if not is_on_floor():
		return Stance.AIRBORNE

	if _fighter.is_attacking():
		return Stance.ATTACK

	if input_vector.is_zero_approx():
		return Stance.GUARD if _fighter.is_on_guard() else Stance.IDLE

	if Input.is_action_pressed(&"sprint"):
		return Stance.SPRINT

	if Input.is_action_pressed(&"walk"):
		return Stance.WALK

	return Stance.RUN


func _apply_stance(stance: Stance) -> void:
	var was_airborne: bool = _stance == Stance.AIRBORNE
	var animation_speed: float = ANIMATION_SPEED_BY_STANCE.get(stance, 1.0)

	if stance == _stance:
		return

	_stance = stance
	_model.rest_expression(FACE_BY_STANCE.get(stance, FaceAnimator.Mood.NEUTRAL))

	# O golpe já está tocando: quem escolhe a animação dele é o UnarmedFighter.
	if stance == Stance.ATTACK:
		return

	if stance == Stance.AIRBORNE and velocity.y > 0.0:
		_model.play_animation_then(JUMP_START_ANIMATION, ANIMATION_BY_STANCE[stance])

		return

	if was_airborne and stance == Stance.IDLE:
		_model.play_animation_then(JUMP_LAND_ANIMATION, ANIMATION_BY_STANCE[stance])

		return

	_model.play_animation(ANIMATION_BY_STANCE[stance], animation_speed)


func _turn_model_toward(direction: Vector3, delta: float) -> void:
	var target_yaw: float

	if direction.length_squared() < 0.01:
		return

	target_yaw = atan2(direction.x, direction.z)
	_model.global_rotation.y = lerp_angle(_model.global_rotation.y, target_yaw, TURN_SPEED * delta)


func _rotate_camera(mouse_delta: Vector2) -> void:
	_camera_yaw.rotation.y -= mouse_delta.x * MOUSE_SENSITIVITY
	_camera_pitch.rotation.x = clampf(
		_camera_pitch.rotation.x - mouse_delta.y * MOUSE_SENSITIVITY, PITCH_MIN, PITCH_MAX
	)
