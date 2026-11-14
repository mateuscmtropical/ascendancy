class_name WalkingNpc
extends CharacterBody3D
## Morador da praça: percorre uma rota em laço pela navmesh, desviando de objetos e de outras
## pessoas (avoidance), ou fica parado numa animação servindo de obstáculo para quem passa.

enum Activity { PATROL, STAND }
enum PatrolState { WALKING, PAUSED }

const CHARACTER_MODEL_SCENE: PackedScene = preload("res://features/player/character_model.tscn")
const WALK_ANIMATION: StringName = &"ual1/Walk"
const TURN_SPEED: float = 6.0

@export var body_scene: PackedScene
@export var hair_color: Color = Color("4a3426")
@export var activity: Activity = Activity.PATROL
@export var idle_animation: StringName = &"ual1/Idle"
@export var route: PackedVector3Array = PackedVector3Array()
@export var walk_speed: float = 1.3
@export var pause_seconds: float = 3.0
@export var animation_offset_seconds: float = 0.0

var _model: CharacterModel
var _patrol_state: PatrolState = PatrolState.WALKING
var _target_index: int = 0
var _pause_left: float = 0.0
## Subida por metro andado até o próximo ponto do caminho (escadas e rampas da navmesh).
var _climb_per_meter: float = 0.0
var _patrol_steps: Dictionary[PatrolState, Callable] = {
	PatrolState.WALKING: _walk_toward_target,
	PatrolState.PAUSED: _wait_at_target,
}

@onready var _navigation_agent: NavigationAgent3D = $NavigationAgent3D
@onready var _obstacle: NavigationObstacle3D = $NavigationObstacle3D


func _ready() -> void:
	var is_walking: bool = activity == Activity.PATROL and route.size() > 1

	_model = CHARACTER_MODEL_SCENE.instantiate()
	_model.body_scene = body_scene
	_model.hair_color = hair_color
	_model.start_animation = WALK_ANIMATION if is_walking else idle_animation
	_model.start_offset_seconds = animation_offset_seconds
	add_child(_model)

	_navigation_agent.avoidance_enabled = is_walking
	_obstacle.avoidance_enabled = not is_walking
	set_physics_process(is_walking)

	if not is_walking:
		return

	global_position = route[0]
	_target_index = 1
	_navigation_agent.max_speed = walk_speed
	_navigation_agent.target_position = route[_target_index]
	_navigation_agent.velocity_computed.connect(_move_with_safe_velocity)


func _physics_process(delta: float) -> void:
	var patrol_step: Callable = _patrol_steps[_patrol_state]

	patrol_step.call(delta)


static func next_route_index(current_index: int, route_size: int) -> int:
	return (current_index + 1) % route_size


func _walk_toward_target(_delta: float) -> void:
	var next_point: Vector3
	var direction: Vector3
	var horizontal_distance: float

	if _navigation_agent.is_navigation_finished():
		_arrive_at_target()

		return

	next_point = _navigation_agent.get_next_path_position()
	direction = next_point - global_position
	horizontal_distance = Vector2(direction.x, direction.z).length()
	_climb_per_meter = direction.y / horizontal_distance if horizontal_distance > 0.05 else 0.0
	direction.y = 0.0
	_navigation_agent.velocity = direction.normalized() * walk_speed


## Chamado pelo avoidance com a velocidade que não bate em ninguém.
func _move_with_safe_velocity(safe_velocity: Vector3) -> void:
	var delta: float = get_physics_process_delta_time()
	var horizontal_speed: float = Vector2(safe_velocity.x, safe_velocity.z).length()

	if _patrol_state == PatrolState.PAUSED:
		return

	velocity = Vector3(safe_velocity.x, horizontal_speed * _climb_per_meter, safe_velocity.z)
	move_and_slide()

	if velocity.length() < 0.05:
		return

	rotation.y = lerp_angle(rotation.y, atan2(velocity.x, velocity.z), TURN_SPEED * delta)


func _arrive_at_target() -> void:
	_patrol_state = PatrolState.PAUSED
	_pause_left = pause_seconds
	_target_index = next_route_index(_target_index, route.size())
	_navigation_agent.velocity = Vector3.ZERO

	if pause_seconds > 0.0:
		_model.play_animation(idle_animation)


func _wait_at_target(delta: float) -> void:
	_pause_left -= delta
	_navigation_agent.velocity = Vector3.ZERO

	if _pause_left > 0.0:
		return

	_patrol_state = PatrolState.WALKING
	_navigation_agent.target_position = route[_target_index]
	_model.play_animation(WALK_ANIMATION)
