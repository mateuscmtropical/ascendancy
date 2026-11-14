class_name PromoDirector
extends Node
## Roteiro do vídeo promocional: voos de câmera com legenda, escolha de personagem e jogo.
## Gravar com tools_src/record.sh (Movie Maker, tempo fixo); fecha o jogo ao terminar.

enum ShotKind { FLY, CHARACTER_SELECT, GAMEPLAY }

const OFFSCREEN_POSITION: Vector2i = Vector2i(-20000, -20000)
const FADE_SECONDS: float = 0.5
const TEXT_FADE_SECONDS: float = 0.8
const SHOTS: Array[Dictionary] = [
	{
		"kind": ShotKind.FLY,
		"seconds": 7.5,
		"title": "ASCENDANCY",
		"subtitle": "Uma aventura de fantasia em terceira pessoa",
		"eye_from": Vector3(0, 26, 62),
		"eye_to": Vector3(0, 15, 40),
		"look_from": Vector3(0, 8, -20),
		"look_to": Vector3(0, 7, -26),
	},
	{
		"kind": ShotKind.FLY,
		"seconds": 6.0,
		"caption": "Uma catedral no coração da cidade",
		"eye_from": Vector3(-5, 1.7, -6),
		"eye_to": Vector3(4, 1.7, -8),
		"look_from": Vector3(0, 9, -34),
		"look_to": Vector3(0, 14, -34),
	},
	{
		"kind": ShotKind.FLY,
		"seconds": 6.0,
		"caption": "Fontes, flores e praças de pedra",
		"eye_from": Vector3(-12, 3.2, 6),
		"eye_to": Vector3(-3, 3.2, 12.5),
		"look_from": Vector3(0, 2, 0),
		"look_to": Vector3(0, 2, 0),
	},
	{
		"kind": ShotKind.FLY,
		"seconds": 5.0,
		"caption": "Moradores com rotina própria",
		"eye_from": Vector3(15.5, 1.7, 13.5),
		"eye_to": Vector3(14.8, 1.7, 12.5),
		"look_from": Vector3(5, 1.3, 9),
		"look_to": Vector3(4, 1.3, 8),
	},
	{
		"kind": ShotKind.FLY,
		"seconds": 5.0,
		"caption": "Mercado na esquina da praça",
		"eye_from": Vector3(4, 1.7, 18),
		"eye_to": Vector3(7, 1.7, 17),
		"look_from": Vector3(16, 1.2, 24),
		"look_to": Vector3(17, 1.2, 26),
	},
	{
		"kind": ShotKind.FLY,
		"seconds": 5.0,
		"caption": "Um banco à sombra para descansar",
		"eye_from": Vector3(-14.2, 1.45, -10.2),
		"eye_to": Vector3(-14.8, 1.35, -9.4),
		"look_from": Vector3(-19, 0.8, -8),
		"look_to": Vector3(-19, 0.8, -8),
	},
	{
		"kind": ShotKind.CHARACTER_SELECT,
		"seconds": 6.0,
		"caption": "Aventureiro ou aventureira",
	},
	{
		"kind": ShotKind.GAMEPLAY,
		"seconds": 8.0,
		"caption": "Explore a praça em terceira pessoa",
		"jog_seconds": 2.6,
		"sprint_seconds": 1.6,
	},
	{
		"kind": ShotKind.FLY,
		"seconds": 7.5,
		"title": "ASCENDANCY",
		"subtitle": "Em desenvolvimento · feito em Godot 4",
		"eye_from": Vector3(0, 8, 24),
		"eye_to": Vector3(0, 26, 58),
		"look_from": Vector3(0, 5, -12),
		"look_to": Vector3(0, 8, -26),
	},
]

@export var hub: Hub
@export var camera: Camera3D
@export var title_label: Label
@export var subtitle_label: Label
@export var caption_label: Label
@export var fade_rect: ColorRect


func _ready() -> void:
	DisplayServer.window_set_position(OFFSCREEN_POSITION)

	_play_reel.call_deferred()


func _play_reel() -> void:
	hub.show_scenery()

	for shot in SHOTS:
		_fade_through_black(shot.seconds)
		_show_texts(shot)

		match shot.kind:
			ShotKind.FLY:
				await _fly_camera(shot)
			ShotKind.CHARACTER_SELECT:
				await _show_character_select(shot)
			ShotKind.GAMEPLAY:
				await _play_as_adventuress(shot)

	get_tree().quit()


func _fly_camera(shot: Dictionary) -> void:
	var tween: Tween = create_tween()

	hub.show_scenery()
	camera.make_current()
	_place_camera(0.0, shot)

	(
		tween
		. tween_method(_place_camera.bind(shot), 0.0, 1.0, shot.seconds)
		. set_trans(Tween.TRANS_SINE)
		. set_ease(Tween.EASE_IN_OUT)
	)

	await tween.finished


func _place_camera(progress: float, shot: Dictionary) -> void:
	var eye: Vector3 = shot.eye_from.lerp(shot.eye_to, progress)
	var target: Vector3 = shot.look_from.lerp(shot.look_to, progress)

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
		tween.tween_property(text_label, ^"modulate:a", 1.0, TEXT_FADE_SECONDS).set_delay(0.4)
