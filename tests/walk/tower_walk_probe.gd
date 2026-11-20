extends Node
## Teste de caminhada das torres da catedral (headless): o corpo do jogador de verdade (mesma
## cápsula, climb_step e move_and_slide do PlayerController) anda pelo caminho gravado no sidecar
## art/town/cathedral_towers.json, da nave até o tablado do sótão e de volta, e depois até a sala
## do relógio, nas duas torres. Só a posição inicial é posta à mão; falha se travar, cair ou
## chegar a um ponto na altura errada.
## Uso: Godot --headless --fixed-fps 60 --path . res://tests/walk/tower_walk_probe.tscn

const HUB_SCENE: PackedScene = preload("res://features/hub/hub.tscn")
const SIDECAR_PATH: String = "res://art/town/cathedral_towers.json"
const TOWER_TAGS: PackedStringArray = ["L", "R"]
const WALK_SPEED: float = 3.0
const GRAVITY: float = 30.0
const REACH_DISTANCE: float = 0.25
const HEIGHT_TOLERANCE: float = 0.45
const STALL_SECONDS: float = 3.0
const PROGRESS_EPSILON: float = 0.05
const FALL_TOLERANCE: float = 1.0
const SETTLE_FRAMES: int = 30

var _player: PlayerController
var _towers: Node3D
var _paths: Dictionary = {}
var _tower_index: int = 0
var _waypoints: Array[Vector3] = []
var _waypoint_index: int = 0
var _best_distance: float = INF
var _stall_seconds: float = 0.0
var _lowest_allowed: float = -INF
var _settle_frames: int = 0


func _ready() -> void:
	var hub: Node = HUB_SCENE.instantiate()
	var sidecar_text: String = FileAccess.get_file_as_string(SIDECAR_PATH)

	add_child(hub)
	_player = hub.get_node("Player")
	_player.set_physics_process(false)
	_towers = hub.get_node("Buildings/CathedralTowers")
	_paths = JSON.parse_string(sidecar_text)["stair_paths"]
	_start_tower()


func _physics_process(delta: float) -> void:
	var target: Vector3
	var offset: Vector3
	var distance: float

	if _settle_frames > 0:
		_settle_frames -= 1
		return

	target = _waypoints[_waypoint_index]
	offset = Vector3(
		target.x - _player.global_position.x, 0.0, target.z - _player.global_position.z
	)
	distance = offset.length()

	if distance < REACH_DISTANCE:
		_arrive(target)
		return

	_check_progress(distance, delta)
	_step_toward(offset.normalized(), delta)


func _start_tower() -> void:
	var tag: String = TOWER_TAGS[_tower_index]
	var points: Array = _paths[tag]

	_waypoints.clear()

	for point in points:
		_waypoints.append(_towers.global_transform * Vector3(point[0], point[1], point[2]))

	_player.global_position = _waypoints[0] + Vector3.UP * 0.05
	_player.velocity = Vector3.ZERO
	_waypoint_index = 1
	_lowest_allowed = _waypoints[0].y - FALL_TOLERANCE
	_reset_progress()
	_settle_frames = SETTLE_FRAMES
	print("WALK tower %s: %d waypoints" % [tag, _waypoints.size()])


func _arrive(target: Vector3) -> void:
	var height_error: float = absf(_player.global_position.y - target.y)

	if height_error > HEIGHT_TOLERANCE:
		_fail(
			(
				"waypoint %d at height %.2f, body at %.2f"
				% [_waypoint_index, target.y, _player.global_position.y]
			)
		)
		return

	_lowest_allowed = minf(target.y, _player.global_position.y) - FALL_TOLERANCE
	_waypoint_index += 1
	_reset_progress()

	if _waypoint_index < _waypoints.size():
		return

	print(
		(
			"WALK tower %s reached the clock room at %.2f m"
			% [TOWER_TAGS[_tower_index], _player.global_position.y]
		)
	)
	_tower_index += 1

	if _tower_index < TOWER_TAGS.size():
		_start_tower()
		return

	print("WALK OK")
	get_tree().quit(0)


func _check_progress(distance: float, delta: float) -> void:
	if _player.global_position.y < _lowest_allowed:
		_fail("fell to %.2f going to waypoint %d" % [_player.global_position.y, _waypoint_index])
		return

	if distance < _best_distance - PROGRESS_EPSILON:
		_best_distance = distance
		_stall_seconds = 0.0
		return

	_stall_seconds += delta

	if _stall_seconds > STALL_SECONDS:
		_fail(
			(
				"stuck at %s, %.2f m from waypoint %d %s"
				% [_player.global_position, distance, _waypoint_index, _waypoints[_waypoint_index]]
			)
		)


func _step_toward(direction: Vector3, delta: float) -> void:
	var horizontal: Vector3 = direction * WALK_SPEED

	_player.velocity.x = horizontal.x
	_player.velocity.z = horizontal.z
	_player.velocity.y -= GRAVITY * delta

	if _player.is_on_floor():
		_player.climb_step(horizontal * PlayerController.STEP_PROBE_SECONDS)

	_player.move_and_slide()


func _reset_progress() -> void:
	_best_distance = INF
	_stall_seconds = 0.0


func _fail(reason: String) -> void:
	print("WALK FAIL tower %s: %s" % [TOWER_TAGS[_tower_index], reason])
	set_physics_process(false)
	get_tree().quit(1)
