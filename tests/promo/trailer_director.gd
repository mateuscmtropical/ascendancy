class_name TrailerDirector
extends Node
## Trailer cortado na batida da trilha (124 BPM): planos longos e abertos, câmera estável e um ator
## andando por caminhos marcados (planos em trailer_shots.gd). Passo e velocidade vêm do próprio
## controle do jogador, então o pé não desliza. Sem texto na imagem: letterbox, título e música
## entram na montagem. Conferir com trailer_check.tscn e gravar com tools_src/record.sh.

const OFFSCREEN_POSITION: Vector2i = Vector2i(-20000, -20000)
const BEAT_SECONDS: float = 60.0 / 124.0
const CHARACTER_SCENE: PackedScene = preload("res://features/player/character_model.tscn")
const BODY_BY_NAME: Dictionary[String, PackedScene] = {
	"male": preload("res://art/characters/adventurer_male.gltf"),
	"female": preload("res://art/characters/adventurer_female.gltf"),
}
const HAIR_BY_NAME: Dictionary[String, Color] = {
	"male": Color(0.29, 0.2, 0.15),
	"female": Color(0.62, 0.36, 0.2),
}
const SUN_ROTATION_BY_MOOD: Dictionary[TrailerShots.SunMood, Vector3] = {
	TrailerShots.SunMood.DAY: Vector3(-0.78, 1.248, 0.0),
	TrailerShots.SunMood.GOLDEN: Vector3(-0.22, 1.9, 0.0),
}
const SUN_COLOR_BY_MOOD: Dictionary[TrailerShots.SunMood, Color] = {
	TrailerShots.SunMood.DAY: Color(1.0, 0.902, 0.769),
	TrailerShots.SunMood.GOLDEN: Color(1.0, 0.68, 0.42),
}
const IDLE_ANIMATION: StringName = &"ual1/Idle"
const GROUND_PROBE_UP: float = 2.0
const GROUND_PROBE_DOWN: float = 4.0
const WORLD_COLLISION_MASK: int = 1
const FLASH_ENERGY: float = 9.0
const FLASH_SECONDS: float = 0.6
## Os moradores desviam do ator como desviam do jogador (avoidance da navmesh).
const ACTOR_AVOIDANCE_RADIUS: float = 0.5

@export var hub: Hub
@export var camera: Camera3D
@export var sun: DirectionalLight3D

var actor: CharacterModel
var shot_index: int = -1

var _has_finished: bool = false
var _shot_started_seconds: float = 0.0
var _elapsed_seconds: float = 0.0
var _actor_ground_height: float = 0.0
var _has_reached_path_end: bool = false
var _flash_light: OmniLight3D
var _actor_obstacle: NavigationObstacle3D
var _camera_updaters: Dictionary[TrailerShots.CameraKind, Callable] = {
	TrailerShots.CameraKind.DOLLY: _update_dolly_camera,
	TrailerShots.CameraKind.FOLLOW: _update_follow_camera,
	TrailerShots.CameraKind.WATCH: _update_watch_camera,
}


func _ready() -> void:
	DisplayServer.window_set_position(OFFSCREEN_POSITION)
	hub.show_scenery()

	actor = CHARACTER_SCENE.instantiate()
	actor.hide()
	add_child(actor)

	_actor_obstacle = NavigationObstacle3D.new()
	_actor_obstacle.radius = ACTOR_AVOIDANCE_RADIUS
	_actor_obstacle.avoidance_enabled = true
	actor.add_child(_actor_obstacle)

	_flash_light = OmniLight3D.new()
	_flash_light.light_color = Color(0.55, 0.8, 1.0)
	_flash_light.omni_range = 7.0
	_flash_light.light_energy = 0.0
	add_child(_flash_light)

	camera.make_current()

	_start_shot(0)


func _process(delta: float) -> void:
	var shot: Dictionary
	var shot_seconds: float

	_elapsed_seconds += delta

	if _elapsed_seconds - _shot_started_seconds >= _shot_length(shot_index):
		_advance_shot()

	if _has_finished:
		return

	shot = TrailerShots.SHOTS[shot_index]
	shot_seconds = _elapsed_seconds - _shot_started_seconds
	_update_actor(shot, shot_seconds)
	_camera_updaters[shot["camera"]].call(shot, shot_seconds / _shot_length(shot_index))
	_update_flash(shot, shot_seconds)


## Cortes presos à grade de batidas: o início do plano é a soma das batidas anteriores, não o quadro
## em que o corte foi notado, então os cortes não escorregam da música ao longo do trailer.
func _advance_shot() -> void:
	var next_index: int = shot_index + 1

	_shot_started_seconds += _shot_length(shot_index)

	if next_index >= TrailerShots.SHOTS.size():
		_has_finished = true
		get_tree().quit()

		return

	_start_shot(next_index)


func _shot_length(index: int) -> float:
	return TrailerShots.SHOTS[index]["beats"] * BEAT_SECONDS


func _start_shot(index: int) -> void:
	var shot: Dictionary = TrailerShots.SHOTS[index]
	var mood: TrailerShots.SunMood = shot.get("sun", TrailerShots.SunMood.DAY)

	shot_index = index
	camera.fov = shot["fov"]
	sun.rotation = SUN_ROTATION_BY_MOOD[mood]
	sun.light_color = SUN_COLOR_BY_MOOD[mood]
	_flash_light.light_energy = 0.0
	_has_reached_path_end = false
	_place_actor(shot.get("actor", {}))


func _place_actor(actor_spec: Dictionary) -> void:
	var body_name: String = actor_spec.get("body", "")
	var path: Array = actor_spec.get("path", [])
	var stance: PlayerController.Stance = actor_spec.get("stance", PlayerController.Stance.IDLE)
	var action: StringName = actor_spec.get("action", &"")

	if body_name.is_empty():
		actor.hide()
		_actor_obstacle.avoidance_enabled = false

		return

	actor.set_body(BODY_BY_NAME[body_name], HAIR_BY_NAME[body_name])
	actor.show()
	_actor_obstacle.avoidance_enabled = true
	_actor_ground_height = path[0].y
	actor.global_position = path[0]

	if action.is_empty():
		_play_stance(stance)

		return

	actor.play_animation_then(action, IDLE_ANIMATION)


func _play_stance(stance: PlayerController.Stance) -> void:
	var animation_name: StringName = PlayerController.ANIMATION_BY_STANCE[stance]
	var animation_speed: float = PlayerController.ANIMATION_SPEED_BY_STANCE.get(stance, 1.0)

	actor.play_animation(animation_name, animation_speed)


func _update_actor(shot: Dictionary, shot_seconds: float) -> void:
	var actor_spec: Dictionary = shot.get("actor", {})
	var path: Array = actor_spec.get("path", [])
	var stance: PlayerController.Stance = actor_spec.get("stance", PlayerController.Stance.IDLE)
	var speed: float = PlayerController.SPEED_BY_STANCE[stance]
	var travel: float = speed * shot_seconds
	var flat_position: Vector3
	var heading: Vector3
	var walking_direction: Vector3

	if path.is_empty():
		return

	flat_position = _point_along(path, travel)
	heading = _heading_along(path, travel)
	walking_direction = heading.normalized()

	if actor_spec.has("face"):
		heading = actor_spec["face"] - flat_position

	if travel >= _path_length(path) and not _has_reached_path_end:
		_has_reached_path_end = true
		_play_stance(PlayerController.Stance.IDLE)

	_actor_ground_height = _probe_ground(flat_position, _actor_ground_height)
	actor.global_position = Vector3(flat_position.x, _actor_ground_height, flat_position.z)
	actor.global_rotation.y = atan2(heading.x, heading.z)
	_actor_obstacle.velocity = (
		Vector3.ZERO if _has_reached_path_end else walking_direction * speed
	)


func _path_length(path: Array) -> float:
	var length: float = 0.0

	for index in path.size() - 1:
		length += path[index].distance_to(path[index + 1])

	return length


func _point_along(path: Array, travel: float) -> Vector3:
	var remaining: float = travel

	for index in path.size() - 1:
		var segment: Vector3 = path[index + 1] - path[index]

		if remaining <= segment.length():
			return path[index] + segment.normalized() * remaining

		remaining -= segment.length()

	return path[-1]


func _heading_along(path: Array, travel: float) -> Vector3:
	var remaining: float = travel

	if path.size() < 2:
		return Vector3.BACK

	for index in path.size() - 1:
		var segment: Vector3 = path[index + 1] - path[index]

		if remaining <= segment.length() or index == path.size() - 2:
			return Vector3(segment.x, 0.0, segment.z)

		remaining -= segment.length()

	return Vector3.BACK


func _probe_ground(flat_position: Vector3, last_height: float) -> float:
	var space: PhysicsDirectSpaceState3D = camera.get_world_3d().direct_space_state
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		Vector3(flat_position.x, last_height + GROUND_PROBE_UP, flat_position.z),
		Vector3(flat_position.x, last_height - GROUND_PROBE_DOWN, flat_position.z),
		WORLD_COLLISION_MASK
	)
	var hit: Dictionary = space.intersect_ray(query)

	return hit["position"].y if hit else last_height


func _update_dolly_camera(shot: Dictionary, progress: float) -> void:
	var eased: float = smoothstep(0.0, 1.0, progress)
	var eye: Vector3 = shot["eye_from"].lerp(shot["eye_to"], eased)
	var target: Vector3 = shot["look_from"].lerp(shot["look_to"], eased)

	camera.look_at_from_position(eye, target)


func _update_follow_camera(shot: Dictionary, _progress: float) -> void:
	var actor_basis: Basis = actor.global_basis.orthonormalized()
	var eye: Vector3 = actor.global_position + actor_basis * shot["offset"]
	var target: Vector3 = actor.global_position + actor_basis * shot["look_offset"]

	camera.look_at_from_position(eye, target)


func _update_watch_camera(shot: Dictionary, progress: float) -> void:
	var eased: float = smoothstep(0.0, 1.0, progress)
	var eye: Vector3 = shot["eye_from"].lerp(shot["eye_to"], eased)
	var target: Vector3 = actor.global_position + shot["look_offset"]

	camera.look_at_from_position(eye, target)


func _update_flash(shot: Dictionary, shot_seconds: float) -> void:
	var flash: Array = shot.get("flash", [])
	var since_flash: float

	if flash.is_empty():
		return

	since_flash = shot_seconds - flash[0]
	_flash_light.global_position = flash[1]
	_flash_light.light_energy = (
		FLASH_ENERGY * clampf(1.0 - absf(since_flash) / FLASH_SECONDS, 0.0, 1.0)
	)
