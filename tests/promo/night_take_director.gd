class_name NightTakeDirector
extends Node
## Plano-sequência "Uma noite em Ascendancy", sem cortes: a câmera de jogo segue a heroína
## da praça no fim da tarde até a cripta e de volta, já de noite, e sobe para o céu no fim.
## Pernas em NightTakeRoute.LEGS; hora do dia em NightTakeRoute.TIME_KEYS.

const OFFSCREEN_POSITION: Vector2i = Vector2i(-20000, -20000)
const CHARACTER_SCENE: PackedScene = preload("res://features/player/character_model.tscn")
const BODY_SCENE: PackedScene = preload("res://art/characters/adventurer_female.gltf")
const HAIR_COLOR: Color = Color(0.62, 0.36, 0.2)
const PASSAGE_NODE_NAME: String = "CryptMonument"
const PLAYER_LAYER: int = 2
const WORLD_COLLISION_MASK: int = 1
const GROUND_PROBE_UP: float = 1.2
const GROUND_PROBE_DOWN: float = 2.4
const ACTOR_AVOIDANCE_RADIUS: float = 0.5
const HEAD_HEIGHT: float = 1.55
const CAMERA_WALL_MARGIN: float = 0.25
const CAMERA_FOLLOW_RATE: float = 3.0
const CAMERA_TURN_RATE: float = 2.2
const ZOOM_RATE: float = 1.5
const LOOK_AHEAD: float = 2.0
const CRANE_RISE: float = 2.5
const END_HOLD_SECONDS: float = 3.0

@export var hub: Hub
@export var camera: Camera3D

var actor: CharacterModel

var _legs: Array[Dictionary] = []
var _leg_starts: Array[float] = []
var _leg_index: int = -1
var _elapsed_seconds: float = 0.0
var _total_seconds: float = 0.0
var _ground_height: float = 0.0
var _heading: Vector3 = Vector3.LEFT
var _camera_distance: float = 4.0
var _camera_height: float = 1.9
var _crane_from: Transform3D
var _passage: SecretPassage
var _presence: AnimatableBody3D
var _obstacle: NavigationObstacle3D


func _ready() -> void:
	DisplayServer.window_set_position(OFFSCREEN_POSITION)
	hub.show_scenery()

	_legs.assign(NightTakeRoute.LEGS.duplicate(true))
	while NavigationServer3D.map_get_iteration_id(camera.get_world_3d().navigation_map) == 0:
		await get_tree().physics_frame

	_route_legs_on_navmesh()
	_measure_legs()
	_passage = hub.find_child(PASSAGE_NODE_NAME, true, false) as SecretPassage

	actor = CHARACTER_SCENE.instantiate()
	add_child(actor)
	actor.set_body(BODY_SCENE, HAIR_COLOR)
	_add_presence()
	_heading = PathWalk.heading_along(_legs[0]["path"], 0.0).normalized()
	_update_actor(_legs[0])

	camera.make_current()
	_start_leg(0)
	_place_camera_behind()


func _process(delta: float) -> void:
	var leg: Dictionary

	if _leg_index < 0:
		return

	_elapsed_seconds += delta

	if _elapsed_seconds >= _total_seconds + END_HOLD_SECONDS:
		get_tree().quit()

		return

	while _leg_index < _legs.size() - 1 and _elapsed_seconds >= _leg_starts[_leg_index + 1]:
		_start_leg(_leg_index + 1)

	leg = _legs[_leg_index]
	hub.set_time_of_day(_time_of_day_at(_elapsed_seconds))
	_update_actor(leg)
	_update_camera(leg, delta)


## Pernas com "navigate": o caminho vira a rota da navmesh dos NPCs entre as pontas,
## então a heroína contorna bancos e canteiros como um jogador faria.
func _route_legs_on_navmesh() -> void:
	var map: RID = camera.get_world_3d().navigation_map

	for leg in _legs:
		if not leg.get("navigate", false):
			continue

		var route: PackedVector3Array = NavigationServer3D.map_get_path(
			map, leg["path"][0], leg["path"][-1], true
		)

		if route.size() >= 2:
			leg["path"] = Array(route)


## Duração de cada perna: caminho / velocidade, ou "seconds" nas paradas e no guindaste.
func _measure_legs() -> void:
	var start: float = 0.0

	for leg in _legs:
		_leg_starts.append(start)
		start += _leg_length(leg)

	_total_seconds = start
	print("NIGHT_TAKE legs=", _leg_starts, " total=", _total_seconds)


func _leg_length(leg: Dictionary) -> float:
	var path: Array = leg.get("path", [])
	var speed: float = PlayerController.SPEED_BY_STANCE[leg.get(
		"stance", PlayerController.Stance.IDLE
	)]

	if path.size() < 2 or is_zero_approx(speed):
		return leg.get("seconds", 0.0)

	return PathWalk.path_length(path) / speed


func _start_leg(index: int) -> void:
	var leg: Dictionary = _legs[index]
	var stance: PlayerController.Stance = leg.get("stance", PlayerController.Stance.IDLE)
	var action: StringName = leg.get("action", &"")

	_leg_index = index

	if leg.get("crane", false):
		_crane_from = camera.global_transform

	if leg.get("open_passage", false) and not _passage.is_open:
		_passage.toggle()

	if action.is_empty():
		actor.play_animation(
			PlayerController.ANIMATION_BY_STANCE[stance],
			PlayerController.ANIMATION_SPEED_BY_STANCE.get(stance, 1.0)
		)

		return

	actor.play_animation(action)


func _leg_progress() -> float:
	var length: float = maxf(_leg_length(_legs[_leg_index]), 0.001)

	return clampf((_elapsed_seconds - _leg_starts[_leg_index]) / length, 0.0, 1.0)


func _update_actor(leg: Dictionary) -> void:
	var path: Array = leg.get("path", [])
	var point: Vector3

	if path.size() < 2:
		if leg.has("face"):
			_turn_towards(_flat(leg["face"] - actor.global_position), 0.08)
			actor.global_rotation.y = atan2(_heading.x, _heading.z)

		return

	point = PathWalk.point_along(path, _leg_progress() * PathWalk.path_length(path))
	_turn_towards(PathWalk.heading_along(path, _leg_progress() * PathWalk.path_length(path)), 0.15)
	_ground_height = _probe_ground(point)
	actor.global_position = Vector3(point.x, _ground_height, point.z)
	actor.global_rotation.y = atan2(_heading.x, _heading.z)
	_obstacle.velocity = _heading * PlayerController.SPEED_BY_STANCE[leg["stance"]]


## O caminho já traz a altura aproximada; o raio só assenta o pé no piso de verdade.
func _probe_ground(point: Vector3) -> float:
	var space: PhysicsDirectSpaceState3D = camera.get_world_3d().direct_space_state
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		point + Vector3.UP * GROUND_PROBE_UP,
		point + Vector3.DOWN * GROUND_PROBE_DOWN,
		WORLD_COLLISION_MASK
	)
	var hit: Dictionary

	query.exclude = [_presence.get_rid()]
	hit = space.intersect_ray(query)

	return hit["position"].y if hit else point.y


func _update_camera(leg: Dictionary, delta: float) -> void:
	var head: Vector3 = actor.global_position + Vector3.UP * HEAD_HEIGHT
	var wanted: Vector3
	var look_target: Vector3
	var rate: float = leg.get("camera_rate", 1.0)

	if leg.get("crane", false):
		_update_crane(leg, head)

		return

	_camera_distance = lerpf(_camera_distance, leg.get("camera_distance", 4.0), delta * ZOOM_RATE)
	_camera_height = lerpf(_camera_height, leg.get("camera_height", 1.9), delta * ZOOM_RATE)
	wanted = head - _heading * _camera_distance + Vector3.UP * (_camera_height - HEAD_HEIGHT)
	wanted = _keep_off_walls(head, wanted)
	look_target = head + _heading * LOOK_AHEAD

	if leg.has("camera_at"):
		wanted = leg["camera_at"]
		look_target = head

	# A câmera chega atrasada: na curva ela varre por fora, então o ponto já suavizado
	# também é puxado para fora da parede, senão o quadro fica dentro da pedra.
	camera.global_position = _keep_off_walls(
		head, camera.global_position.lerp(wanted, minf(1.0, delta * CAMERA_FOLLOW_RATE * rate))
	)
	camera.global_transform = camera.global_transform.interpolate_with(
		camera.global_transform.looking_at(look_target), minf(1.0, delta * CAMERA_TURN_RATE * rate)
	)


## No fim a câmera sobe por trás da heroína e inclina até "look_up", no céu.
func _update_crane(leg: Dictionary, head: Vector3) -> void:
	var eased: float = smoothstep(0.0, 1.0, _leg_progress())
	var risen: Vector3 = _crane_from.origin + Vector3.UP * CRANE_RISE * eased
	var target: Transform3D = Transform3D(_crane_from.basis, risen).looking_at(leg["look_up"])
	var start: Transform3D = Transform3D(_crane_from.basis, risen).looking_at(head)

	camera.global_transform = start.interpolate_with(target, eased)


## Parede ou coluna entre a cabeça e a câmera: puxa a câmera para o ponto livre.
func _keep_off_walls(head: Vector3, wanted: Vector3) -> Vector3:
	var space: PhysicsDirectSpaceState3D = camera.get_world_3d().direct_space_state
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		head, wanted, WORLD_COLLISION_MASK
	)
	var hit: Dictionary

	query.exclude = [_presence.get_rid()]
	hit = space.intersect_ray(query)

	if not hit:
		return wanted

	return hit["position"] + (head - wanted).normalized() * CAMERA_WALL_MARGIN


func _place_camera_behind() -> void:
	var head: Vector3 = actor.global_position + Vector3.UP * HEAD_HEIGHT

	camera.global_position = (
		head - _heading * _camera_distance + Vector3.UP * (_camera_height - HEAD_HEIGHT)
	)
	camera.look_at(head + _heading * LOOK_AHEAD)


func _time_of_day_at(seconds: float) -> float:
	var keys: Array = NightTakeRoute.TIME_KEYS

	for index in keys.size() - 1:
		if seconds <= keys[index + 1].x:
			return lerpf(
				keys[index].y,
				keys[index + 1].y,
				inverse_lerp(keys[index].x, keys[index + 1].x, seconds)
			)

	return keys[-1].y


## Corpo na camada do jogador: a passagem secreta vê a heroína chegar e mostra o "E" como no jogo.
func _add_presence() -> void:
	var shape: CollisionShape3D = CollisionShape3D.new()
	var capsule: CapsuleShape3D = CapsuleShape3D.new()

	capsule.radius = 0.35
	capsule.height = 1.7
	shape.shape = capsule
	shape.position.y = 0.85

	_presence = AnimatableBody3D.new()
	_presence.collision_layer = PLAYER_LAYER
	_presence.collision_mask = 0
	_presence.sync_to_physics = false
	_presence.add_child(shape)
	actor.add_child(_presence)

	_obstacle = NavigationObstacle3D.new()
	_obstacle.radius = ACTOR_AVOIDANCE_RADIUS
	_obstacle.avoidance_enabled = true
	actor.add_child(_obstacle)


## Gira o rumo pelo ângulo no plano: slerp de vetores quase opostos dá eixo torto na curva.
func _turn_towards(direction: Vector3, weight: float) -> void:
	var yaw: float = lerp_angle(
		atan2(_heading.x, _heading.z), atan2(direction.x, direction.z), weight
	)

	_heading = Vector3(sin(yaw), 0.0, cos(yaw))


func _flat(vector: Vector3) -> Vector3:
	return Vector3(vector.x, 0.0, vector.z)
