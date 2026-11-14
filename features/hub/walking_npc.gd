class_name WalkingNpc
extends Node3D
## Morador da praça: percorre uma rota em laço parando em cada ponto, ou fica parado numa animação.

enum Activity { PATROL, STAND }
enum PatrolState { WALKING, PAUSED }

const CHARACTER_MODEL_SCENE: PackedScene = preload("res://features/player/character_model.tscn")
const WALK_ANIMATION: StringName = &"ual1/Walk"
const ARRIVAL_DISTANCE: float = 0.15
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
var _patrol_steps: Dictionary[PatrolState, Callable] = {
	PatrolState.WALKING: _walk_toward_target,
	PatrolState.PAUSED: _wait_at_target,
}


func _ready() -> void:
	var starts_walking: bool = activity == Activity.PATROL and route.size() > 1

	_model = CHARACTER_MODEL_SCENE.instantiate()
	_model.body_scene = body_scene
	_model.hair_color = hair_color
	_model.start_animation = WALK_ANIMATION if starts_walking else idle_animation
	_model.start_offset_seconds = animation_offset_seconds
	add_child(_model)

	set_process(starts_walking)

	if starts_walking:
		global_position = route[0]
		_target_index = 1


func _process(delta: float) -> void:
	var patrol_step: Callable = _patrol_steps[_patrol_state]

	patrol_step.call(delta)


static func next_route_index(current_index: int, route_size: int) -> int:
	return (current_index + 1) % route_size


func _walk_toward_target(delta: float) -> void:
	var target: Vector3 = route[_target_index]
	var to_target: Vector3 = target - global_position

	to_target.y = 0.0

	if to_target.length() <= ARRIVAL_DISTANCE:
		_arrive_at_target()

		return

	global_position += to_target.normalized() * minf(walk_speed * delta, to_target.length())
	rotation.y = lerp_angle(rotation.y, atan2(to_target.x, to_target.z), TURN_SPEED * delta)


func _arrive_at_target() -> void:
	_patrol_state = PatrolState.PAUSED
	_pause_left = pause_seconds
	_target_index = next_route_index(_target_index, route.size())
	_model.play_animation(idle_animation)


func _wait_at_target(delta: float) -> void:
	_pause_left -= delta

	if _pause_left > 0.0:
		return

	_patrol_state = PatrolState.WALKING
	_model.play_animation(WALK_ANIMATION)
