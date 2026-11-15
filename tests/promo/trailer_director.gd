class_name TrailerDirector
extends Node
## Trailer cortado na batida da trilha (124 BPM): planos na altura dos olhos, câmera de mão,
## foco raso e um ator andando por caminhos marcados (planos em trailer_shots.gd). Sem texto na
## imagem: letterbox, título e música entram na montagem. Gravar com tools_src/record.sh.

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
const GROUND_PROBE_UP: float = 2.0
const GROUND_PROBE_DOWN: float = 4.0
const WORLD_COLLISION_MASK: int = 1
const SHAKE_FREQUENCY: float = 0.35
const FLASH_ENERGY: float = 9.0
const FLASH_SECONDS: float = 0.6

@export var hub: Hub
@export var camera: Camera3D
@export var sun: DirectionalLight3D

var _shot_index: int = -1
var _has_finished: bool = false
var _shot_started_seconds: float = 0.0
var _elapsed_seconds: float = 0.0
var _actor: CharacterModel
var _actor_ground_height: float = 0.0
var _is_hopping: bool = false
var _flash_light: OmniLight3D
var _shake_noise: FastNoiseLite = FastNoiseLite.new()
var _camera_attributes: CameraAttributesPractical = CameraAttributesPractical.new()
var _camera_updaters: Dictionary[TrailerShots.CameraKind, Callable] = {
	TrailerShots.CameraKind.DOLLY: _update_dolly_camera,
	TrailerShots.CameraKind.FOLLOW: _update_follow_camera,
	TrailerShots.CameraKind.WATCH: _update_watch_camera,
}


func _ready() -> void:
	DisplayServer.window_set_position(OFFSCREEN_POSITION)
	hub.show_scenery()

	_actor = CHARACTER_SCENE.instantiate()
	_actor.hide()
	add_child(_actor)

	_flash_light = OmniLight3D.new()
	_flash_light.light_color = Color(0.55, 0.8, 1.0)
	_flash_light.omni_range = 7.0
	_flash_light.light_energy = 0.0
	add_child(_flash_light)

	_shake_noise.frequency = SHAKE_FREQUENCY
	_camera_attributes.dof_blur_amount = 0.08
	camera.attributes = _camera_attributes
	camera.make_current()

	_start_shot(0)


func _process(delta: float) -> void:
	var shot: Dictionary
	var shot_seconds: float
	var shot_length: float

	_elapsed_seconds += delta

	if _elapsed_seconds - _shot_started_seconds >= _shot_length(_shot_index):
		_advance_shot()

	if _has_finished:
		return

	shot = TrailerShots.SHOTS[_shot_index]
	shot_seconds = _elapsed_seconds - _shot_started_seconds
	shot_length = _shot_length(_shot_index)
	_update_actor(shot, shot_seconds)
	_camera_updaters[shot["camera"]].call(shot, shot_seconds / shot_length)
	_apply_focus(shot, shot_seconds / shot_length)
	_apply_shake(shot)
	_update_flash(shot, shot_seconds)


## Cortes presos à grade de batidas: o início do plano é a soma das batidas anteriores, não o quadro
## em que o corte foi notado, então os cortes não escorregam da música ao longo do trailer.
func _advance_shot() -> void:
	var next_index: int = _shot_index + 1

	_shot_started_seconds += _shot_length(_shot_index)

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

	_shot_index = index
	camera.fov = shot["fov"]
	sun.rotation = SUN_ROTATION_BY_MOOD[mood]
	sun.light_color = SUN_COLOR_BY_MOOD[mood]
	_flash_light.light_energy = 0.0
	_is_hopping = false
	_place_actor(shot.get("actor", {}))


func _place_actor(actor_spec: Dictionary) -> void:
	var body_name: String = actor_spec.get("body", "")
	var path: Array = actor_spec.get("path", [])

	if body_name.is_empty():
		_actor.hide()

		return

	_actor.set_body(BODY_BY_NAME[body_name], HAIR_BY_NAME[body_name])
	_actor.play_animation(actor_spec["animation"], actor_spec.get("animation_speed", 1.0))
	_actor.show()
	_actor_ground_height = path[0].y
	_actor.global_position = path[0]


func _update_actor(shot: Dictionary, shot_seconds: float) -> void:
	var actor_spec: Dictionary = shot.get("actor", {})
	var path: Array = actor_spec.get("path", [])
	var travel: float = actor_spec.get("speed", 0.0) * shot_seconds
	var flat_position: Vector3
	var heading: Vector3

	if path.is_empty():
		return

	flat_position = _point_along(path, travel)
	heading = _heading_along(path, travel)

	if actor_spec.has("face"):
		heading = actor_spec["face"] - flat_position

	_actor_ground_height = _probe_ground(flat_position, _actor_ground_height)
	_actor.global_position = Vector3(flat_position.x, _actor_ground_height, flat_position.z)
	_actor.global_position.y += _hop_height(actor_spec, shot_seconds)
	_actor.global_rotation.y = atan2(heading.x, heading.z)


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


func _hop_height(actor_spec: Dictionary, shot_seconds: float) -> float:
	var hop: Array = actor_spec.get("hop", [])
	var progress: float

	if hop.is_empty():
		return 0.0

	progress = (shot_seconds - hop[0]) / hop[1]

	if progress < 0.0:
		return 0.0

	if progress > 1.0:
		_land_from_hop(actor_spec)

		return 0.0

	if not _is_hopping:
		_is_hopping = true
		_actor.play_animation(actor_spec["hop_animation"])

	return 4.0 * hop[2] * progress * (1.0 - progress)


func _land_from_hop(actor_spec: Dictionary) -> void:
	if not _is_hopping:
		return

	_is_hopping = false
	_actor.play_animation(actor_spec["animation"], actor_spec.get("animation_speed", 1.0))


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
	var actor_basis: Basis = _actor.global_basis.orthonormalized()
	var eye: Vector3 = _actor.global_position + actor_basis * shot["offset"]
	var target: Vector3 = _actor.global_position + actor_basis * shot["look_offset"]

	camera.look_at_from_position(eye, target)


func _update_watch_camera(shot: Dictionary, progress: float) -> void:
	var eased: float = smoothstep(0.0, 1.0, progress)
	var eye: Vector3 = shot["eye_from"].lerp(shot["eye_to"], eased)
	var target: Vector3 = _actor.global_position + shot["look_offset"]

	camera.look_at_from_position(eye, target)


func _apply_focus(shot: Dictionary, progress: float) -> void:
	var eased: float = smoothstep(0.0, 1.0, progress)
	var focus: float = lerpf(shot["focus_from"], shot["focus_to"], eased)

	_camera_attributes.dof_blur_far_enabled = true
	_camera_attributes.dof_blur_far_distance = focus * 1.4
	_camera_attributes.dof_blur_far_transition = focus * 1.2
	_camera_attributes.dof_blur_near_enabled = focus < 8.0
	_camera_attributes.dof_blur_near_distance = focus * 0.55
	_camera_attributes.dof_blur_near_transition = focus * 0.4


func _apply_shake(shot: Dictionary) -> void:
	var amplitude: float = deg_to_rad(shot["shake"])
	var noise_time: float = _elapsed_seconds * 100.0

	camera.rotate_object_local(Vector3.UP, amplitude * _shake_noise.get_noise_1d(noise_time))
	camera.rotate_object_local(
		Vector3.RIGHT, amplitude * _shake_noise.get_noise_1d(noise_time + 500.0)
	)


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
