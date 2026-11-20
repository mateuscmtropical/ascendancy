extends Node3D
## Folha de prints de luta e de rosto: congela um clipe num instante e põe uma expressão no rosto.
## Argumentos (depois de --): [--character=male|female|villager_male|villager_female|saci]
## [--animation=<biblioteca/clipe>] [--seconds=<instante do clipe>]
## [--mood=<nome de FaceAnimator.Mood>] [--blink] fecha os olhos.
## Câmeras: FightSide, FightThree, FightFront, FaceClose (segue a cabeça).

const BLINK_ARGUMENT: String = "--blink"
const BODY_BY_CHARACTER: Dictionary[String, PackedScene] = {
	"male": preload("res://art/characters/adventurer_male.gltf"),
	"female": preload("res://art/characters/adventurer_female.gltf"),
	"villager_male": preload("res://art/characters/villager_male.gltf"),
	"villager_female": preload("res://art/characters/villager_female.gltf"),
	"saci": preload("res://art/characters/saci.gltf"),
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

var _animation_name: StringName = &"ual1/Idle"
var _pose_seconds: float = 0.0
var _mood: FaceAnimator.Mood = FaceAnimator.Mood.NEUTRAL
var _is_blinking: bool = false
var _argument_readers: Dictionary[String, Callable] = {
	"--character": _read_character,
	"--animation": _read_animation,
	"--seconds": _read_seconds,
	"--mood": _read_mood,
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
	_freeze_body()
	_freeze_face()
	_aim_face_camera()


func _read_character(character: String) -> void:
	_fighter.set_body(BODY_BY_CHARACTER[character], HAIR_COLOR)


func _read_animation(animation_name: String) -> void:
	_animation_name = StringName(animation_name)


func _read_seconds(seconds: String) -> void:
	_pose_seconds = seconds.to_float()


func _read_mood(mood_name: String) -> void:
	_mood = FaceAnimator.Mood[mood_name.to_upper()]


func _freeze_body() -> void:
	var player: AnimationPlayer = _fighter.get_node("AnimationPlayer") as AnimationPlayer

	player.play(_animation_name, 0.0)
	player.seek(_pose_seconds, true)
	player.speed_scale = 0.0


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
