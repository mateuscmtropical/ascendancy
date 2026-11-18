extends Node3D
## Demonstração gravável da luta sem arma e do rosto: o jogador de verdade (controle desligado)
## recebe os pedidos de golpe de um roteiro, com troca de câmera, câmera lenta e legenda do
## golpe. Gravar com tools_src/record.sh (tempo fixo); fecha sozinha no fim do roteiro.

enum Cue { ATTACK, CAMERA, MOOD, TIME_SCALE, BODY, QUIT }

const OFFSCREEN_POSITION: Vector2i = Vector2i(-20000, -20000)
const PUNCH: UnarmedFighter.Attack = UnarmedFighter.Attack.PUNCH
const KICK: UnarmedFighter.Attack = UnarmedFighter.Attack.KICK
const FEMALE_BODY: PackedScene = preload("res://art/characters/adventurer_female.gltf")
const FEMALE_HAIR: Color = Color(0.62, 0.36, 0.2)
const MOOD_SECONDS: float = 1.1
## O jogador nasce no ar e pousa: o roteiro só começa depois do pouso.
const LEAD_IN_SECONDS: float = 1.2
## Tempos em segundos de jogo (a câmera lenta estica o tempo real, não o roteiro).
const TIMELINE: Array[Dictionary] = [
	{"at": 0.0, "cue": Cue.CAMERA, "value": "ReelThree"},
	{"at": 0.8, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 1.0, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 1.4, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 1.8, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 3.6, "cue": Cue.ATTACK, "value": KICK},
	{"at": 3.9, "cue": Cue.ATTACK, "value": KICK},
	{"at": 4.6, "cue": Cue.ATTACK, "value": KICK},
	{"at": 6.6, "cue": Cue.CAMERA, "value": "ReelSide"},
	{"at": 7.0, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 7.2, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 7.6, "cue": Cue.ATTACK, "value": KICK},
	{"at": 9.4, "cue": Cue.TIME_SCALE, "value": 0.3},
	{"at": 9.5, "cue": Cue.ATTACK, "value": KICK},
	{"at": 9.8, "cue": Cue.ATTACK, "value": KICK},
	{"at": 11.3, "cue": Cue.TIME_SCALE, "value": 1.0},
	{"at": 11.6, "cue": Cue.CAMERA, "value": "ReelFront"},
	{"at": 11.9, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 12.1, "cue": Cue.ATTACK, "value": KICK},
	{"at": 12.6, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 13.0, "cue": Cue.ATTACK, "value": KICK},
	{"at": 17.1, "cue": Cue.CAMERA, "value": "ReelFace"},
	{"at": 18.2, "cue": Cue.MOOD, "value": FaceAnimator.Mood.HAPPY},
	{"at": 19.6, "cue": Cue.MOOD, "value": FaceAnimator.Mood.SURPRISED},
	{"at": 21.0, "cue": Cue.MOOD, "value": FaceAnimator.Mood.SAD},
	{"at": 22.4, "cue": Cue.MOOD, "value": FaceAnimator.Mood.PAIN},
	{"at": 23.8, "cue": Cue.MOOD, "value": FaceAnimator.Mood.EFFORT},
	{"at": 25.4, "cue": Cue.BODY, "value": FEMALE_BODY},
	{"at": 28.0, "cue": Cue.MOOD, "value": FaceAnimator.Mood.HAPPY},
	{"at": 29.4, "cue": Cue.MOOD, "value": FaceAnimator.Mood.SURPRISED},
	{"at": 30.8, "cue": Cue.MOOD, "value": FaceAnimator.Mood.EFFORT},
	{"at": 32.2, "cue": Cue.CAMERA, "value": "ReelThree"},
	{"at": 32.6, "cue": Cue.ATTACK, "value": KICK},
	{"at": 32.9, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 33.3, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 33.7, "cue": Cue.ATTACK, "value": KICK},
	{"at": 36.0, "cue": Cue.QUIT, "value": null},
]
const CAMERA_TARGETS: Dictionary[String, Vector3] = {
	"ReelThree": Vector3(0.0, 1.0, 0.3),
	"ReelSide": Vector3(0.0, 1.0, 0.35),
	"ReelFront": Vector3(0.0, 1.0, 0.0),
}
const MOVE_NAMES: Dictionary[UnarmedFighter.Move, String] = {
	UnarmedFighter.Move.JAB: "Jab",
	UnarmedFighter.Move.CROSS: "Direto",
	UnarmedFighter.Move.HOOK: "Gancho",
	UnarmedFighter.Move.UPPERCUT: "Uppercut",
	UnarmedFighter.Move.FRONT_KICK: "Chute frontal",
	UnarmedFighter.Move.ROUNDHOUSE_KICK: "Chute circular",
	UnarmedFighter.Move.SIDE_KICK: "Chute lateral",
}
const MOOD_NAMES: Dictionary[FaceAnimator.Mood, String] = {
	FaceAnimator.Mood.HAPPY: "Feliz",
	FaceAnimator.Mood.SURPRISED: "Surpresa",
	FaceAnimator.Mood.SAD: "Triste",
	FaceAnimator.Mood.PAIN: "Dor",
	FaceAnimator.Mood.EFFORT: "Esforço",
}
const HEAD_BONE: StringName = &"Head"
const FACE_FROM_HEAD_BONE: Vector3 = Vector3(0.0, 0.11, 0.06)
const FACE_CAMERA_OFFSET: Vector3 = Vector3(0.2, -0.16, 0.8)
const FACE_FOLLOW_SPEED: float = 3.0

var _seconds: float = -LEAD_IN_SECONDS
var _next_cue: int = 0
var _face_focus: Vector3 = Vector3(0.0, 1.75, 0.0)
var _cue_players: Dictionary[Cue, Callable] = {
	Cue.ATTACK: _request_attack,
	Cue.CAMERA: _cut_to_camera,
	Cue.MOOD: _show_mood,
	Cue.TIME_SCALE: _set_time_scale,
	Cue.BODY: _change_body,
	Cue.QUIT: _quit,
}

@onready var _player: PlayerController = $Player
@onready var _fighter: UnarmedFighter = $Player/UnarmedFighter
@onready var _model: CharacterModel = $Player/CharacterModel
@onready var _face_camera: Camera3D = $ReelFace
@onready var _caption: Label = $Interface/Caption


func _ready() -> void:
	DisplayServer.window_set_position(OFFSCREEN_POSITION)
	_player.is_input_enabled = false
	_fighter.move_started.connect(_caption_move)

	for camera_name in CAMERA_TARGETS:
		var camera: Camera3D = get_node(camera_name) as Camera3D

		camera.look_at(CAMERA_TARGETS[camera_name])


func _process(delta: float) -> void:
	_seconds += delta
	_follow_face(delta)

	if _seconds < TIMELINE[_next_cue].at:
		return

	_cue_players[TIMELINE[_next_cue].cue].call(TIMELINE[_next_cue].value)
	_next_cue = mini(_next_cue + 1, TIMELINE.size() - 1)


func _request_attack(attack: UnarmedFighter.Attack) -> void:
	_fighter.request_attack(attack)


func _cut_to_camera(camera_name: String) -> void:
	(get_node(camera_name) as Camera3D).make_current()
	_caption.text = ""


func _show_mood(mood: FaceAnimator.Mood) -> void:
	_model.show_expression(mood, MOOD_SECONDS)
	_caption.text = MOOD_NAMES[mood]


func _set_time_scale(time_scale: float) -> void:
	Engine.time_scale = time_scale


func _change_body(body_scene: PackedScene) -> void:
	_player.set_appearance(body_scene, FEMALE_HAIR)
	_caption.text = ""


func _quit(_value: Variant) -> void:
	get_tree().quit()


func _caption_move(move: UnarmedFighter.Move) -> void:
	_caption.text = MOVE_NAMES[move]


func _follow_face(delta: float) -> void:
	var skeleton: Skeleton3D = _model.get_node("Body/Armature/Skeleton3D") as Skeleton3D
	var head_pose: Transform3D = skeleton.get_bone_global_pose(skeleton.find_bone(HEAD_BONE))
	var face_position: Vector3 = skeleton.global_transform * head_pose.origin + FACE_FROM_HEAD_BONE

	# A câmera acompanha a cabeça com atraso: colada nela, o balanço do corpo sumiria da imagem.
	_face_focus = _face_focus.lerp(face_position, minf(1.0, FACE_FOLLOW_SPEED * delta))
	_face_camera.global_position = _face_focus + FACE_CAMERA_OFFSET
	_face_camera.look_at(_face_focus)
