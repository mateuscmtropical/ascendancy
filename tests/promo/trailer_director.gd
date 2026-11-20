class_name TrailerDirector
extends Node
## Vídeos cortados na batida da trilha: planos longos e abertos, câmera estável e um ator (ou a
## Mula sem cabeça) andando por caminhos marcados. Os planos estão em trailer_shots.gd (trailer, 124
## BPM) e full_shots.gd (vídeo completo, 120 BPM). Passo e velocidade vêm do controle do jogador,
## então o pé não desliza. Plano com "time" usa o relógio do céu (dia, pôr do sol, noite); os
## demais usam o sol fixo do trailer. Textos opcionais ("title", "subtitle", "caption") vão para os
## rótulos da cena, se ela os tiver. Conferir com trailer_check.tscn ou full_check.tscn e gravar com
## tools_src/record.sh. Argumentos (depois de --): --from-shot=N --to-shot=M. NAMED: shot_views.gd.

enum Reel { TRAILER, COMPLETE, MARKETING, SHOWCASE }

const OFFSCREEN_POSITION: Vector2i = Vector2i(-20000, -20000)
## MARKETING: 60 "batidas" por minuto, então "beats" é a duração do clipe em segundos (a edição e a
## trilha ficam em tools_src/cut_marketing_trailer.py).
const BPM_BY_REEL: Dictionary[Reel, float] = {
	Reel.TRAILER: 124.0, Reel.COMPLETE: 120.0, Reel.MARKETING: 60.0, Reel.SHOWCASE: 60.0
}
const SHOTS_BY_REEL: Dictionary[Reel, Array] = {
	Reel.TRAILER: TrailerShots.SHOTS,
	Reel.COMPLETE: FullShots.SHOTS,
	Reel.MARKETING: MarketingShots.SHOTS,
	Reel.SHOWCASE: ShowcaseShots.SHOTS,
}
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
const FORCED_EVENT_BY_NAME: Dictionary[String, DayNightCycle.ForcedEvent] = {
	"": DayNightCycle.ForcedEvent.NONE,
	"shower": DayNightCycle.ForcedEvent.NONE,
	"solar": DayNightCycle.ForcedEvent.SOLAR_ECLIPSE,
	"lunar": DayNightCycle.ForcedEvent.LUNAR_ECLIPSE,
}
const FROM_SHOT_ARGUMENT: String = "--from-shot="
const TO_SHOT_ARGUMENT: String = "--to-shot="
const IDLE_ANIMATION: StringName = &"ual1/Idle"
const MULA_NODE_NAME: String = "MulaSemCabeca"
const GROUND_PROBE_UP: float = 2.0
const GROUND_PROBE_DOWN: float = 4.0
const WORLD_COLLISION_MASK: int = 1
const FLASH_ENERGY: float = 9.0
const FLASH_SECONDS: float = 0.6
## Os moradores desviam do ator como desviam do jogador (avoidance da navmesh).
const ACTOR_AVOIDANCE_RADIUS: float = 0.5
const FADE_IN_SECONDS: float = 0.8
const FADE_OUT_SECONDS: float = 2.0
## Plano com "dip" começa preto, espera o céu assentar e clareia; o plano antes dele escurece.
const DIP_HOLD_SECONDS: float = 0.5
const DIP_IN_SECONDS: float = 0.6
const DIP_OUT_SECONDS: float = 0.3
const TEXT_FADE_SECONDS: float = 0.4
const TEXT_DELAY_SECONDS: float = 0.3

@export var reel: Reel = Reel.TRAILER
@export var hub: Hub
@export var camera: Camera3D
@export var sun: DirectionalLight3D
@export var title_label: Label
@export var subtitle_label: Label
@export var caption_label: Label
@export var fade_rect: ColorRect

var actor: CharacterModel
var mula: MulaSemCabeca
var shot_index: int = -1
var shots: Array[Dictionary] = []

var _has_finished: bool = false
var _shot_started_seconds: float = 0.0
var _elapsed_seconds: float = 0.0
var _actor_ground_height: float = 0.0
var _mula_ground_height: float = 0.0
var _has_reached_path_end: bool = false
var _first_shot: int = 0
var _last_shot: int = 0
var _selected_choice: int = -1
var _flash_light: OmniLight3D
var _actor_obstacle: NavigationObstacle3D
var _day_night: DayNightCycle
var _mula_home: Transform3D
var _is_mula_moved: bool = false
var _text_tween: Tween
var _fade_tween: Tween
var _views: ShotViews = ShotViews.new()
var _camera_updaters: Dictionary[TrailerShots.CameraKind, Callable] = {
	TrailerShots.CameraKind.DOLLY: _update_dolly_camera,
	TrailerShots.CameraKind.FOLLOW: _update_follow_camera,
	TrailerShots.CameraKind.WATCH: _update_watch_camera,
	TrailerShots.CameraKind.ORBIT: _update_orbit_camera,
	TrailerShots.CameraKind.SELECT: _update_select_camera,
	TrailerShots.CameraKind.NAMED: _update_named_camera,
}


func _ready() -> void:
	DisplayServer.window_set_position(OFFSCREEN_POSITION)
	hub.show_scenery()

	shots.assign(SHOTS_BY_REEL[reel])
	_last_shot = shots.size() - 1

	for argument in OS.get_cmdline_user_args():
		if argument.begins_with(FROM_SHOT_ARGUMENT):
			_first_shot = argument.trim_prefix(FROM_SHOT_ARGUMENT).to_int()

		if argument.begins_with(TO_SHOT_ARGUMENT):
			_last_shot = mini(_last_shot, argument.trim_prefix(TO_SHOT_ARGUMENT).to_int())

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

	_day_night = hub.get_node("DayNight") as DayNightCycle
	mula = hub.find_child(MULA_NODE_NAME, true, false) as MulaSemCabeca
	_mula_home = mula.global_transform

	camera.make_current()

	_start_shot(_first_shot)


func _process(delta: float) -> void:
	var shot: Dictionary
	var shot_seconds: float

	_elapsed_seconds += delta

	if _elapsed_seconds - _shot_started_seconds >= _shot_length(shot_index):
		_advance_shot()

	if _has_finished:
		return

	shot = shots[shot_index]
	shot_seconds = _elapsed_seconds - _shot_started_seconds
	_update_actor(shot, shot_seconds)
	_update_mula(shot, shot_seconds)
	_camera_updaters[shot["camera"]].call(shot, shot_seconds / _shot_length(shot_index))
	_update_flash(shot, shot_seconds)
	_update_time_lapse(shot)


## Plano com "time_to": o céu anda de "time" até "time_to" ao longo do plano (pôr do sol acelerado).
func _update_time_lapse(shot: Dictionary) -> void:
	if not shot.has("time_to"):
		return

	hub.set_time_of_day(lerpf(shot["time"], shot["time_to"], shot_progress()))


## Quanto do plano atual já passou, de 0 a 1.
func shot_progress() -> float:
	return (_elapsed_seconds - _shot_started_seconds) / _shot_length(shot_index)


## Cortes presos à grade de batidas: o início do plano é a soma das batidas anteriores, não o quadro
## em que o corte foi notado, então os cortes não escorregam da música ao longo do vídeo.
func _advance_shot() -> void:
	var next_index: int = shot_index + 1

	_shot_started_seconds += _shot_length(shot_index)

	if next_index > _last_shot:
		_has_finished = true
		get_tree().quit()

		return

	_start_shot(next_index)


func _shot_length(index: int) -> float:
	return shots[index]["beats"] * 60.0 / BPM_BY_REEL[reel]


func _start_shot(index: int) -> void:
	var shot: Dictionary = shots[index]

	shot_index = index
	camera.fov = shot.get("fov", camera.fov)
	_flash_light.light_energy = 0.0
	_has_reached_path_end = false
	_place_actor(shot.get("actor", {}))
	_place_mula(shot.get("mula", {}))
	_set_sun(shot)
	_show_texts(shot, _shot_length(index))

	_plan_fades(index)

	if shot["camera"] == TrailerShots.CameraKind.SELECT:
		hub.open_character_select()
		_selected_choice = -1

		return

	hub.show_scenery()
	camera.make_current()
	_camera_updaters[shot["camera"]].call(shot, 0.0)

	if shot.get("event", "") == "shower":
		hub.start_meteor_shower()

	_views.open_passage_if_asked(shot, hub)


## Hora e evento do céu quando o plano pede ("time"); senão o sol fixo do clima pedido.
func _set_sun(shot: Dictionary) -> void:
	var mood: TrailerShots.SunMood = shot.get("sun", TrailerShots.SunMood.DAY)

	if not shot.has("time"):
		sun.rotation = SUN_ROTATION_BY_MOOD[mood]
		sun.light_color = SUN_COLOR_BY_MOOD[mood]

		return

	_day_night.forced_event = FORCED_EVENT_BY_NAME[shot.get("event", "")]
	hub.set_time_of_day(shot["time"])


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

	if actor_spec.get("weapon", false):
		HeroSword.arm(actor)

	_actor_obstacle.avoidance_enabled = true
	_actor_ground_height = path[0].y
	actor.global_position = path[0]

	if action.is_empty():
		_play_stance(stance)

		return

	actor.play_animation_then(action, IDLE_ANIMATION)


## A Mula do plano sai do pasto para o ponto inicial do caminho; sem pedido, volta para casa parada.
func _place_mula(mula_spec: Dictionary) -> void:
	var path: Array = mula_spec.get("path", [])

	if path.is_empty():
		_send_mula_home()

		return

	_is_mula_moved = true
	_mula_ground_height = path[0].y
	mula.global_position = path[0]
	mula.global_rotation.y = atan2(path[1].x - path[0].x, path[1].z - path[0].z)
	mula.play_animation(mula_spec.get("animation", MulaSemCabeca.IDLE_ANIMATION))


func _send_mula_home() -> void:
	if not _is_mula_moved:
		return

	_is_mula_moved = false
	mula.global_transform = _mula_home
	mula.play_animation(MulaSemCabeca.IDLE_ANIMATION)


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

	flat_position = PathWalk.point_along(path, travel)
	heading = PathWalk.heading_along(path, travel)
	walking_direction = heading.normalized()

	if actor_spec.has("face"):
		heading = actor_spec["face"] - flat_position

	if travel >= PathWalk.path_length(path) and not _has_reached_path_end:
		_has_reached_path_end = true
		_play_stance(PlayerController.Stance.IDLE)

	_actor_ground_height = _probe_ground(flat_position, _actor_ground_height)
	actor.global_position = Vector3(flat_position.x, _actor_ground_height, flat_position.z)
	actor.global_rotation.y = atan2(heading.x, heading.z)
	_actor_obstacle.velocity = (
		Vector3.ZERO if _has_reached_path_end else walking_direction * speed
	)


func _update_mula(shot: Dictionary, shot_seconds: float) -> void:
	var mula_spec: Dictionary = shot.get("mula", {})
	var path: Array = mula_spec.get("path", [])
	var travel: float = mula_spec.get("speed", 0.0) * shot_seconds
	var flat_position: Vector3
	var heading: Vector3

	if path.is_empty():
		return

	flat_position = PathWalk.point_along(path, travel)
	heading = PathWalk.heading_along(path, travel)
	_mula_ground_height = _probe_ground(flat_position, _mula_ground_height)
	mula.global_position = Vector3(flat_position.x, _mula_ground_height, flat_position.z)
	mula.global_rotation.y = atan2(heading.x, heading.z)


func _probe_ground(flat_position: Vector3, last_height: float) -> float:
	var space: PhysicsDirectSpaceState3D = camera.get_world_3d().direct_space_state
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		Vector3(flat_position.x, last_height + GROUND_PROBE_UP, flat_position.z),
		Vector3(flat_position.x, last_height - GROUND_PROBE_DOWN, flat_position.z),
		WORLD_COLLISION_MASK
	)
	var hit: Dictionary = space.intersect_ray(query)

	return hit["position"].y if hit else last_height


## Quem a câmera de seguir/observar acompanha: um nó do hub ("subject"), a Mula do plano ou o ator.
func _subject_of(shot: Dictionary) -> Node3D:
	if shot.has("subject"):
		return hub.get_node(shot["subject"]) as Node3D

	return mula if shot.has("mula") else actor


func _update_dolly_camera(shot: Dictionary, progress: float) -> void:
	var eased: float = smoothstep(0.0, 1.0, progress)
	var eye: Vector3 = shot["eye_from"].lerp(shot["eye_to"], eased)
	var target: Vector3 = shot["look_from"].lerp(shot["look_to"], eased)

	camera.look_at_from_position(eye, target)


func _update_follow_camera(shot: Dictionary, _progress: float) -> void:
	var subject: Node3D = _subject_of(shot)
	var subject_basis: Basis = subject.global_basis.orthonormalized()
	var eye: Vector3 = subject.global_position + subject_basis * shot["offset"]
	var target: Vector3 = subject.global_position + subject_basis * shot["look_offset"]

	camera.look_at_from_position(eye, target)


func _update_watch_camera(shot: Dictionary, progress: float) -> void:
	var eased: float = smoothstep(0.0, 1.0, progress)
	var eye: Vector3 = shot["eye_from"].lerp(shot["eye_to"], eased)
	var target: Vector3 = _subject_of(shot).global_position + shot["look_offset"]

	camera.look_at_from_position(eye, target)


func _update_orbit_camera(shot: Dictionary, progress: float) -> void:
	var eased: float = smoothstep(0.0, 1.0, progress)
	var angle: float = deg_to_rad(lerpf(shot["angle_from"], shot["angle_to"], eased))
	var radius: float = lerpf(shot["radius_from"], shot["radius_to"], eased)
	var height: float = lerpf(shot["height_from"], shot["height_to"], eased)
	var eye: Vector3 = shot["center"] + Vector3(cos(angle) * radius, height, sin(angle) * radius)
	var target: Vector3 = shot["center"] + Vector3(0.0, shot["look_height"], 0.0)

	camera.look_at_from_position(eye, target)


func _update_named_camera(shot: Dictionary, progress: float) -> void:
	camera.global_transform = _views.camera_transform(shot, progress)
	camera.fov = shot.get("fov", _views.fov_of(shot["view"]))


## A câmera é a da escolha de personagem do jogo; metade do plano em cada aventureiro.
func _update_select_camera(_shot: Dictionary, progress: float) -> void:
	var choice: CharacterSelect.Choice = (
		CharacterSelect.Choice.MALE if progress < 0.5 else CharacterSelect.Choice.FEMALE
	)

	if choice == _selected_choice:
		return

	_selected_choice = choice
	hub.preview_choice(choice)


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


func _show_texts(shot: Dictionary, shot_seconds: float) -> void:
	var text_labels: Dictionary[Label, String] = {}
	var hold_seconds: float = shot_seconds - TEXT_DELAY_SECONDS - TEXT_FADE_SECONDS * 2.0

	if _text_tween:
		_text_tween.kill()

	if title_label == null:
		return

	text_labels[title_label] = shot.get("title", "")
	text_labels[subtitle_label] = shot.get("subtitle", "")
	text_labels[caption_label] = shot.get("caption", "")
	_text_tween = create_tween().set_parallel()

	for text_label in text_labels:
		text_label.text = text_labels[text_label]
		text_label.modulate.a = 0.0
		_text_tween.tween_property(text_label, ^"modulate:a", 1.0, TEXT_FADE_SECONDS).set_delay(
			TEXT_DELAY_SECONDS
		)
		_text_tween.tween_property(text_label, ^"modulate:a", 0.0, TEXT_FADE_SECONDS).set_delay(
			TEXT_DELAY_SECONDS + TEXT_FADE_SECONDS + hold_seconds
		)


## Abre o plano saindo do preto (primeiro plano, ou "dip") e fecha no preto antes de um "dip" e no
## fim do vídeo.
func _plan_fades(index: int) -> void:
	var opens_dark: bool = index == _first_shot or shots[index].get("dip", false)
	var closes_for_dip: bool = index < _last_shot and shots[index + 1].get("dip", false)
	var closing_seconds: float = FADE_OUT_SECONDS if index == _last_shot else DIP_OUT_SECONDS
	var opened_seconds: float = 0.0

	if fade_rect == null:
		return

	if _fade_tween:
		_fade_tween.kill()

	fade_rect.modulate.a = 1.0 if opens_dark else 0.0

	if not (opens_dark or index == _last_shot or closes_for_dip):
		return

	_fade_tween = create_tween()

	if opens_dark:
		opened_seconds = (
			DIP_HOLD_SECONDS + (FADE_IN_SECONDS if index == _first_shot else DIP_IN_SECONDS)
		)
		_fade_tween.tween_interval(DIP_HOLD_SECONDS)
		_fade_tween.tween_property(fade_rect, ^"modulate:a", 0.0, opened_seconds - DIP_HOLD_SECONDS)

	if index == _last_shot or closes_for_dip:
		_fade_tween.tween_interval(_shot_length(index) - opened_seconds - closing_seconds)
		_fade_tween.tween_property(fade_rect, ^"modulate:a", 1.0, closing_seconds)
