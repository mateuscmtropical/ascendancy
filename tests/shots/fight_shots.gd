extends Node3D
## Folha de prints de luta e de rosto: congela um clipe num instante e põe uma expressão no rosto.
## Argumentos (depois de --): [--character=male|female|villager_male|villager_female|saci|
## couple_him|couple_her]
## [--animation=<biblioteca/clipe>] [--seconds=<instante do clipe>]
## [--mood=<nome de FaceAnimator.Mood>] [--blink] fecha os olhos.
## [--strip=<quantos> --until=<instante final>] põe o clipe em fila, um corpo por instante de
## --seconds a --until, visto de lado por uma câmera sem perspectiva ([--strip-view=front]
## vê de frente).
## Câmeras: FightSide, FightThree, FightFront, FaceClose (segue a cabeça).

const BLINK_ARGUMENT: String = "--blink"
const MODEL_SCENE: PackedScene = preload("res://features/player/character_model.tscn")
const BODY_BY_CHARACTER: Dictionary[String, PackedScene] = {
	"male": preload("res://art/characters/adventurer_male.gltf"),
	"female": preload("res://art/characters/adventurer_female.gltf"),
	"villager_male": preload("res://art/characters/villager_male.gltf"),
	"villager_female": preload("res://art/characters/villager_female.gltf"),
	"saci": preload("res://art/characters/saci.gltf"),
	"couple_him": preload("res://art/characters/couple_him.gltf"),
	"couple_her": preload("res://art/characters/couple_her.gltf"),
}
const HAIR_COLOR: Color = Color(0.29, 0.204, 0.149)
const CAMERA_TARGETS: Dictionary[String, Vector3] = {
	"FightSide": Vector3(0.0, 1.0, 0.35),
	"FightThree": Vector3(0.0, 1.0, 0.25),
	"FightFront": Vector3(0.0, 1.0, 0.0),
}
const HEAD_BONE: StringName = &"Head"
## O osso fica na base do crânio; os olhos estão este tanto acima e à frente.
const FACE_FROM_HEAD_BONE: Vector3 = Vector3(0.0, 0.11, 0.06)
const FACE_CAMERA_OFFSET: Vector3 = Vector3(0.22, 0.03, 0.8)
## Tempo para o rosto assentar na expressão antes de ser congelado.
const FACE_SETTLE_SECONDS: float = 1.0
## Distância entre os corpos da fila: cabe um chute esticado sem tocar o vizinho.
const STRIP_SPACING: float = 1.7
const STRIP_CAMERA_DISTANCE: float = 12.0
const STRIP_MARGIN: float = 1.2
const STRIP_MIN_HEIGHT: float = 2.6
const STRIP_LABEL_HEIGHT: float = 2.15
## Para onde a fila cresce e de onde a câmera olha, por vista.
const STRIP_STEP_BY_VIEW: Dictionary[String, Vector3] = {
	"side": Vector3(0.0, 0.0, -1.0),
	"front": Vector3(1.0, 0.0, 0.0),
}
const STRIP_EYE_BY_VIEW: Dictionary[String, Vector3] = {
	"side": Vector3(1.0, 0.0, 0.0),
	"front": Vector3(0.0, 0.0, 1.0),
}

var _animation_name: StringName = &"ual1/Idle"
var _pose_seconds: float = 0.0
var _mood: FaceAnimator.Mood = FaceAnimator.Mood.NEUTRAL
var _is_blinking: bool = false
var _body_scene: PackedScene = BODY_BY_CHARACTER["male"]
var _strip_count: int = 1
var _strip_until_seconds: float = 0.0
var _strip_view: String = "side"
var _argument_readers: Dictionary[String, Callable] = {
	"--character": _read_character,
	"--animation": _read_animation,
	"--seconds": _read_seconds,
	"--mood": _read_mood,
	"--strip": _read_strip_count,
	"--until": _read_until_seconds,
	"--strip-view": _read_strip_view,
}

@onready var _fighter: CharacterModel = $Fighter
@onready var _face_camera: Camera3D = $FaceClose


func _ready() -> void:
	for camera_name in CAMERA_TARGETS:
		var camera: Camera3D = get_node(camera_name) as Camera3D

		camera.look_at(CAMERA_TARGETS[camera_name])

	for argument in OS.get_cmdline_user_args():
		var reader: Callable = _argument_readers.get(argument.get_slice("=", 0), Callable())

		if reader.is_valid():
			reader.call(argument.get_slice("=", 1))

	_is_blinking = OS.get_cmdline_user_args().has(BLINK_ARGUMENT)
	_freeze_body(_fighter, _pose_seconds)
	_freeze_face()
	_aim_face_camera()

	if _strip_count > 1:
		_line_up_strip()


func _read_character(character: String) -> void:
	_body_scene = BODY_BY_CHARACTER[character]
	_fighter.set_body(_body_scene, HAIR_COLOR)


func _read_animation(animation_name: String) -> void:
	_animation_name = StringName(animation_name)


func _read_seconds(seconds: String) -> void:
	_pose_seconds = seconds.to_float()


func _read_mood(mood_name: String) -> void:
	_mood = FaceAnimator.Mood[mood_name.to_upper()]


func _read_strip_count(count: String) -> void:
	_strip_count = count.to_int()


func _read_until_seconds(seconds: String) -> void:
	_strip_until_seconds = seconds.to_float()


func _read_strip_view(view: String) -> void:
	_strip_view = view


func _freeze_body(fighter: CharacterModel, seconds: float) -> void:
	var player: AnimationPlayer = fighter.get_node("AnimationPlayer") as AnimationPlayer

	player.play(_animation_name, 0.0)
	player.seek(seconds, true)
	player.speed_scale = 0.0


## O primeiro corpo da fila é o da cena; os outros nascem ao lado, cada um no seu instante.
func _line_up_strip() -> void:
	var step: Vector3 = STRIP_STEP_BY_VIEW[_strip_view] * STRIP_SPACING
	var span_seconds: float = _strip_until_seconds - _pose_seconds

	_label_instant(Vector3.ZERO, _pose_seconds)

	for index in range(1, _strip_count):
		var fighter: CharacterModel = MODEL_SCENE.instantiate()
		var seconds: float = _pose_seconds + span_seconds * index / (_strip_count - 1)

		fighter.body_scene = _body_scene
		fighter.hair_color = HAIR_COLOR
		fighter.position = step * index
		add_child(fighter)
		_freeze_body(fighter, seconds)
		_label_instant(fighter.position, seconds)

	_frame_strip(step * (_strip_count - 1))


func _label_instant(at: Vector3, seconds: float) -> void:
	var label: Label3D = Label3D.new()

	label.text = "%.2f" % seconds
	label.position = at + Vector3.UP * STRIP_LABEL_HEIGHT
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.pixel_size = 0.004
	add_child(label)


func _frame_strip(last_position: Vector3) -> void:
	var camera: Camera3D = Camera3D.new()
	var width: float = last_position.length() + 2.0 * STRIP_MARGIN
	var height: float = maxf(width * 9.0 / 16.0, STRIP_MIN_HEIGHT)
	var middle: Vector3 = last_position / 2.0 + Vector3.UP * (height / 2.0 - 0.15)

	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = height
	add_child(camera)
	camera.global_position = middle + STRIP_EYE_BY_VIEW[_strip_view] * STRIP_CAMERA_DISTANCE
	camera.look_at(middle)
	camera.make_current()


func _freeze_face() -> void:
	var face: FaceAnimator = _fighter.get_node("FaceAnimator") as FaceAnimator

	face.set_process(false)
	face.show_expression(_mood)
	face.advance(FACE_SETTLE_SECONDS)

	if not _is_blinking:
		return

	face.blink_now()
	face.advance(FaceAnimator.BLINK_CLOSE_SECONDS)
	face.advance(0.0)


func _aim_face_camera() -> void:
	var skeleton: Skeleton3D = _fighter.get_node("Body/Armature/Skeleton3D") as Skeleton3D
	var head_pose: Transform3D = skeleton.get_bone_global_pose(skeleton.find_bone(HEAD_BONE))
	var face_position: Vector3 = skeleton.global_transform * head_pose.origin + FACE_FROM_HEAD_BONE

	_face_camera.global_position = face_position + FACE_CAMERA_OFFSET
	_face_camera.look_at(face_position)
