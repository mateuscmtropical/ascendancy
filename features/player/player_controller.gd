class_name PlayerController
extends CharacterBody3D
## Personagem do jogador em terceira pessoa: anda relativo à câmera, corpo gira para a direção.

enum Stance { IDLE, WALK, JOG, SPRINT, AIRBORNE }

const SPEED_BY_STANCE: Dictionary[Stance, float] = {
	Stance.IDLE: 0.0,
	Stance.WALK: 1.6,
	Stance.JOG: 3.9,
	Stance.SPRINT: 6.4,
	Stance.AIRBORNE: 3.9,
}
const ANIMATION_BY_STANCE: Dictionary[Stance, StringName] = {
	Stance.IDLE: &"ual1/Idle",
	Stance.WALK: &"ual1/Walk",
	Stance.JOG: &"ual1/Jog_Fwd",
	Stance.SPRINT: &"ual1/Sprint",
	Stance.AIRBORNE: &"ual1/Jump",
}
const GROUND_ACCELERATION: float = 18.0
const AIR_ACCELERATION: float = 4.0
const TURN_SPEED: float = 12.0
const JUMP_VELOCITY: float = 4.6
const MOUSE_SENSITIVITY: float = 0.0025
const PITCH_MIN: float = -1.1
const PITCH_MAX: float = 0.45

@export var is_input_enabled: bool = true

var _stance: Stance = Stance.IDLE
var _gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")

@onready var _model: CharacterModel = $CharacterModel
@onready var _camera_yaw: Node3D = $CameraYaw
@onready var _camera_pitch: Node3D = $CameraYaw/CameraPitch
@onready var _camera: Camera3D = $CameraYaw/CameraPitch/SpringArm3D/Camera3D
@onready var _avoidance_obstacle: NavigationObstacle3D = $AvoidanceObstacle


func _unhandled_input(event: InputEvent) -> void:
	var is_mouse_captured: bool = Input.mouse_mode == Input.MOUSE_MODE_CAPTURED

	if not is_input_enabled:
		return

	if event is InputEventMouseButton and event.pressed and not is_mouse_captured:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

		return

	if event.is_action_pressed(&"release_mouse"):
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

		return

	if event is InputEventMouseMotion and is_mouse_captured:
		_rotate_camera(event.relative)


func _physics_process(delta: float) -> void:
	var input_vector: Vector2 = _read_move_input()
	var move_direction: Vector3 = (
		_camera_yaw.global_basis * Vector3(input_vector.x, 0.0, input_vector.y)
	)
	var stance: Stance = _choose_stance(input_vector)
	var target_velocity: Vector3 = move_direction.normalized() * SPEED_BY_STANCE[stance]
	var acceleration: float = GROUND_ACCELERATION if is_on_floor() else AIR_ACCELERATION

	velocity.x = move_toward(velocity.x, target_velocity.x, acceleration * delta)
	velocity.z = move_toward(velocity.z, target_velocity.z, acceleration * delta)
	velocity.y -= _gravity * delta

	if is_on_floor() and is_input_enabled and Input.is_action_just_pressed(&"jump"):
		velocity.y = JUMP_VELOCITY

	move_and_slide()

	# NPCs desviam do jogador prevendo para onde ele vai.
	_avoidance_obstacle.velocity = Vector3(velocity.x, 0.0, velocity.z)
	_turn_model_toward(move_direction, delta)
	_apply_stance(stance)


func make_camera_current() -> void:
	_camera.make_current()


func set_appearance(body_scene: PackedScene, hair_color: Color) -> void:
	_model.set_body(body_scene, hair_color)


func _read_move_input() -> Vector2:
	if not is_input_enabled:
		return Vector2.ZERO

	return Input.get_vector(&"move_left", &"move_right", &"move_forward", &"move_back")


func _choose_stance(input_vector: Vector2) -> Stance:
	if not is_on_floor():
		return Stance.AIRBORNE

	if input_vector.is_zero_approx():
		return Stance.IDLE

	if Input.is_action_pressed(&"sprint"):
		return Stance.SPRINT

	if Input.is_action_pressed(&"walk"):
		return Stance.WALK

	return Stance.JOG


func _apply_stance(stance: Stance) -> void:
	if stance == _stance:
		return

	_stance = stance
	_model.play_animation(ANIMATION_BY_STANCE[stance])


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
