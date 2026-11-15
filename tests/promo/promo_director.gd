class_name PromoDirector
extends Node
## Diretor dos vídeos: toca o roteiro escolhido pelo export reel (tests/promo/promo_shots.gd) com
## voos, órbitas, escolha de personagem e jogo. Gravar com tools_src/record.sh (Movie Maker,
## tempo fixo); fecha o jogo ao terminar.

enum ShotKind { FLY, ORBIT, CHARACTER_SELECT, GAMEPLAY }
enum Reel { PROMO, DRONE }

const OFFSCREEN_POSITION: Vector2i = Vector2i(-20000, -20000)
const FADE_SECONDS: float = 0.3
const TEXT_FADE_SECONDS: float = 0.5
const SHOTS_BY_REEL: Dictionary[Reel, Array] = {
	Reel.PROMO: PromoShots.PROMO,
	Reel.DRONE: PromoShots.DRONE,
}

@export var reel: Reel = Reel.PROMO
@export var hub: Hub
@export var camera: Camera3D
@export var title_label: Label
@export var subtitle_label: Label
@export var caption_label: Label
@export var fade_rect: ColorRect

var _shot_players: Dictionary[ShotKind, Callable] = {
	ShotKind.FLY: _fly_camera,
	ShotKind.ORBIT: _orbit_camera,
	ShotKind.CHARACTER_SELECT: _show_character_select,
	ShotKind.GAMEPLAY: _play_as_adventuress,
}


func _ready() -> void:
	DisplayServer.window_set_position(OFFSCREEN_POSITION)

	_play_reel.call_deferred()


func _play_reel() -> void:
	hub.show_scenery()

	for shot in SHOTS_BY_REEL[reel]:
		var shot_player: Callable = _shot_players[shot.kind]

		_set_the_sky(shot)
		_fade_through_black(shot.seconds)
		_show_texts(shot)
		await shot_player.call(shot)

	get_tree().quit()


## Hora do dia e chuva de meteoros pedidas pela tomada (o relógio segue andando depois).
func _set_the_sky(shot: Dictionary) -> void:
	if shot.has("time_of_day"):
		hub.set_time_of_day(shot.time_of_day)

	if shot.get("meteor_shower", false):
		hub.start_meteor_shower()


func _fly_camera(shot: Dictionary) -> void:
	await _move_camera(_place_flying_camera.bind(shot), shot.seconds)


func _orbit_camera(shot: Dictionary) -> void:
	await _move_camera(_place_orbiting_camera.bind(shot), shot.seconds)


func _move_camera(place_camera: Callable, seconds: float) -> void:
	var tween: Tween = create_tween()

	hub.show_scenery()
	camera.make_current()
	place_camera.call(0.0)

	tween.tween_method(place_camera, 0.0, 1.0, seconds).set_trans(Tween.TRANS_SINE).set_ease(
		Tween.EASE_IN_OUT
	)

	await tween.finished


func _place_flying_camera(progress: float, shot: Dictionary) -> void:
	var eye: Vector3 = shot.eye_from.lerp(shot.eye_to, progress)
	var target: Vector3 = shot.look_from.lerp(shot.look_to, progress)

	camera.look_at_from_position(eye, target)


func _place_orbiting_camera(progress: float, shot: Dictionary) -> void:
	var angle: float = deg_to_rad(lerpf(shot.angle_from, shot.angle_to, progress))
	var radius: float = lerpf(shot.radius_from, shot.radius_to, progress)
	var height: float = lerpf(shot.height_from, shot.height_to, progress)
	var eye: Vector3 = shot.center + Vector3(cos(angle) * radius, height, sin(angle) * radius)
	var target: Vector3 = shot.center + Vector3(0, shot.look_height, 0)

	camera.look_at_from_position(eye, target)


func _show_character_select(shot: Dictionary) -> void:
	var half_seconds: float = shot.seconds / 2.0

	hub.open_character_select()
	hub.preview_choice(CharacterSelect.Choice.MALE)
	await get_tree().create_timer(half_seconds).timeout

	hub.preview_choice(CharacterSelect.Choice.FEMALE)
	await get_tree().create_timer(half_seconds).timeout


func _play_as_adventuress(shot: Dictionary) -> void:
	var standing_seconds: float = shot.seconds - shot.jog_seconds - shot.sprint_seconds

	# Reto do pé da escada do coreto rumo à catedral: caminho livre de arbustos e árvores.
	hub.start_playing(CharacterSelect.Choice.FEMALE)
	Input.action_press(&"move_forward")
	await get_tree().create_timer(shot.jog_seconds).timeout

	Input.action_press(&"sprint")
	await get_tree().create_timer(shot.sprint_seconds).timeout

	Input.action_release(&"sprint")
	Input.action_release(&"move_forward")
	await get_tree().create_timer(standing_seconds).timeout


func _fade_through_black(shot_seconds: float) -> void:
	var tween: Tween = create_tween()

	fade_rect.modulate.a = 1.0
	tween.tween_property(fade_rect, ^"modulate:a", 0.0, FADE_SECONDS)
	tween.tween_interval(shot_seconds - FADE_SECONDS * 2.0)
	tween.tween_property(fade_rect, ^"modulate:a", 1.0, FADE_SECONDS)


func _show_texts(shot: Dictionary) -> void:
	var tween: Tween = create_tween().set_parallel()
	var text_labels: Array[Label] = [title_label, subtitle_label, caption_label]

	title_label.text = shot.get("title", "")
	subtitle_label.text = shot.get("subtitle", "")
	caption_label.text = shot.get("caption", "")

	for text_label in text_labels:
		text_label.modulate.a = 0.0
		tween.tween_property(text_label, ^"modulate:a", 1.0, TEXT_FADE_SECONDS).set_delay(0.3)
