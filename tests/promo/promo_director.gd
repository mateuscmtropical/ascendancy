class_name PromoDirector
extends Node
## Roteiro do vídeo promocional: voos de drone, órbitas e gruas pela cidade, escolha de personagem
## e jogo. Gravar com tools_src/record.sh (Movie Maker, tempo fixo); fecha o jogo ao terminar.

enum ShotKind { FLY, ORBIT, CHARACTER_SELECT, GAMEPLAY }

const OFFSCREEN_POSITION: Vector2i = Vector2i(-20000, -20000)
const FADE_SECONDS: float = 0.3
const TEXT_FADE_SECONDS: float = 0.5
const SHOTS: Array[Dictionary] = [
	{
		"kind": ShotKind.ORBIT,
		"seconds": 7.0,
		"title": "ASCENDANCY",
		"subtitle": "Uma aventura de fantasia em terceira pessoa",
		"center": Vector3(0, 0, -4),
		"angle_from": 200.0,
		"angle_to": 245.0,
		"radius_from": 150.0,
		"radius_to": 135.0,
		"height_from": 70.0,
		"height_to": 52.0,
		"look_height": 0.0,
	},
	{
		"kind": ShotKind.FLY,
		"seconds": 4.5,
		"caption": "Uma cidade inteira para explorar",
		"eye_from": Vector3(-80, 30, 40),
		"eye_to": Vector3(-47, 6, 12),
		"look_from": Vector3(-34, 1, 0),
		"look_to": Vector3(-34, 2, 0),
	},
	{
		"kind": ShotKind.ORBIT,
		"seconds": 5.0,
		"caption": "Chafariz no coração da praça",
		"center": Vector3(-34, 0, 0),
		"angle_from": 290.0,
		"angle_to": 375.0,
		"radius_from": 13.5,
		"radius_to": 12.5,
		"height_from": 3.6,
		"height_to": 2.6,
		"look_height": 2.0,
	},
	{
		"kind": ShotKind.FLY,
		"seconds": 4.5,
		"caption": "Coreto com música ao vivo",
		"eye_from": Vector3(-39, 1.6, -21),
		"eye_to": Vector3(-39, 7.5, -23),
		"look_from": Vector3(-50, 2.4, -12),
		"look_to": Vector3(-50, 3.2, -12),
	},
	{
		"kind": ShotKind.FLY,
		"seconds": 4.5,
		"caption": "Feira no calçadão entre as duas praças",
		"eye_from": Vector3(0.4, 3.4, 46),
		"eye_to": Vector3(0.4, 3.0, 10),
		"look_from": Vector3(0, 2, 0),
		"look_to": Vector3(18, 9, 0),
	},
	{
		"kind": ShotKind.FLY,
		"seconds": 5.0,
		"caption": "A catedral no alto da praça",
		"eye_from": Vector3(-6, 1.2, -14),
		"eye_to": Vector3(2, 10, -10),
		"look_from": Vector3(18, 8, 0),
		"look_to": Vector3(18, 20, 0),
	},
	{
		"kind": ShotKind.ORBIT,
		"seconds": 5.0,
		"center": Vector3(18, 0, 0),
		"angle_from": 145.0,
		"angle_to": 215.0,
		"radius_from": 30.0,
		"radius_to": 27.0,
		"height_from": 24.0,
		"height_to": 33.0,
		"look_height": 22.0,
	},
	{
		"kind": ShotKind.FLY,
		"seconds": 5.5,
		"caption": "Portas abertas: entre e explore",
		"eye_from": Vector3(6, 2.6, -1.3),
		"eye_to": Vector3(32, 2.6, -1.3),
		"look_from": Vector3(50, 3.5, -1),
		"look_to": Vector3(54, 4, 0),
	},
	{
		"kind": ShotKind.FLY,
		"seconds": 4.5,
		"caption": "Arcos, vitrais e colunas douradas",
		"eye_from": Vector3(40, 4.5, 2.5),
		"eye_to": Vector3(44, 3.2, -2.5),
		"look_from": Vector3(55, 5, 0),
		"look_to": Vector3(55, 5, 0),
	},
	{
		"kind": ShotKind.FLY,
		"seconds": 4.5,
		"caption": "Avenida arborizada com rotatória",
		"eye_from": Vector3(-95, 4, -50),
		"eye_to": Vector3(-40, 3, -50),
		"look_from": Vector3(-20, 3, -57),
		"look_to": Vector3(10, 3, -57),
	},
	{
		"kind": ShotKind.FLY,
		"seconds": 4.5,
		"caption": "Quarteirões de casarões ao redor",
		"eye_from": Vector3(60, 24, 80),
		"eye_to": Vector3(92, 18, 22),
		"look_from": Vector3(40, 0, 30),
		"look_to": Vector3(30, 2, 0),
	},
	{
		"kind": ShotKind.CHARACTER_SELECT,
		"seconds": 5.0,
		"caption": "Aventureiro ou aventureira",
	},
	{
		"kind": ShotKind.GAMEPLAY,
		"seconds": 8.0,
		"caption": "Explore a cidade em terceira pessoa",
		"jog_seconds": 3.0,
		"sprint_seconds": 3.5,
	},
	{
		"kind": ShotKind.ORBIT,
		"seconds": 7.0,
		"title": "ASCENDANCY",
		"subtitle": "Em desenvolvimento · feito em Godot 4",
		"center": Vector3(0, 0, 0),
		"angle_from": 160.0,
		"angle_to": 200.0,
		"radius_from": 60.0,
		"radius_to": 125.0,
		"height_from": 15.0,
		"height_to": 60.0,
		"look_height": 5.0,
	},
]

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

	for shot in SHOTS:
		var shot_player: Callable = _shot_players[shot.kind]

		_fade_through_black(shot.seconds)
		_show_texts(shot)
		await shot_player.call(shot)

	get_tree().quit()


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

	# Diagonal pelo gramado: caminho livre de arbustos e árvores a partir do coreto.
	hub.start_playing(CharacterSelect.Choice.FEMALE)
	Input.action_press(&"move_forward")
	Input.action_press(&"move_left")
	await get_tree().create_timer(shot.jog_seconds).timeout

	Input.action_press(&"sprint")
	await get_tree().create_timer(shot.sprint_seconds).timeout

	Input.action_release(&"sprint")
	Input.action_release(&"move_forward")
	Input.action_release(&"move_left")
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
