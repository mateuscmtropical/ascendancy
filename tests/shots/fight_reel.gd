extends Node3D
## Demonstração gravável da luta sem arma e do rosto: o jogador de verdade recebe os pedidos de
## golpe de um roteiro, com troca de câmera, câmera lenta e legenda do golpe. Gravar com
## tools_src/record.sh (tempo fixo); fecha sozinha no fim do roteiro.
## [--reel=move] (depois de --) troca o roteiro pelo de golpes andando: o roteiro segura as ações
## de andar do InputMap (estado interno do jogo, nada vai para a janela), com câmeras que seguem.

enum Cue { ATTACK, CAMERA, MOOD, TIME_SCALE, BODY, QUIT, MOVE, JUMP }

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
const WALK_ON: Array[StringName] = [&"move_forward", &"walk"]
const RUN_ON: Array[StringName] = [&"move_forward"]
const SPRINT_ON: Array[StringName] = [&"move_forward", &"sprint"]
const RUN_LEFT: Array[StringName] = [&"move_left"]
const RUN_BACK: Array[StringName] = [&"move_back"]
const STAND: Array[StringName] = []
## Golpes sem parar o passo: soco no tronco, chute voador, arrancada, freada, curva e pulo.
const MOVE_TIMELINE: Array[Dictionary] = [
	{"at": 0.0, "cue": Cue.CAMERA, "value": "TrackSide"},
	{"at": 0.6, "cue": Cue.MOVE, "value": RUN_ON},
	{"at": 1.6, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 1.8, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 2.2, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 2.6, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 4.2, "cue": Cue.ATTACK, "value": KICK},
	{"at": 4.5, "cue": Cue.ATTACK, "value": KICK},
	{"at": 5.2, "cue": Cue.ATTACK, "value": KICK},
	{"at": 7.2, "cue": Cue.MOVE, "value": STAND},
	{"at": 8.2, "cue": Cue.MOVE, "value": WALK_ON},
	{"at": 9.4, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 9.7, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 11.2, "cue": Cue.MOVE, "value": SPRINT_ON},
	{"at": 12.2, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 12.5, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 13.4, "cue": Cue.ATTACK, "value": KICK},
	{"at": 14.8, "cue": Cue.JUMP, "value": null},
	{"at": 15.8, "cue": Cue.MOVE, "value": STAND},
	{"at": 16.8, "cue": Cue.CAMERA, "value": "TrackThree"},
	{"at": 17.0, "cue": Cue.MOVE, "value": RUN_ON},
	{"at": 17.8, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 18.0, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 18.8, "cue": Cue.ATTACK, "value": KICK},
	{"at": 19.1, "cue": Cue.ATTACK, "value": KICK},
	{"at": 20.6, "cue": Cue.MOVE, "value": RUN_LEFT},
	{"at": 21.6, "cue": Cue.MOVE, "value": RUN_BACK},
	{"at": 22.4, "cue": Cue.JUMP, "value": null},
	{"at": 23.4, "cue": Cue.MOVE, "value": STAND},
	{"at": 24.2, "cue": Cue.ATTACK, "value": KICK},
	{"at": 25.6, "cue": Cue.CAMERA, "value": "Chase"},
	{"at": 25.8, "cue": Cue.MOVE, "value": RUN_ON},
	{"at": 26.6, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 26.8, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 27.2, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 28.2, "cue": Cue.ATTACK, "value": KICK},
	{"at": 28.5, "cue": Cue.ATTACK, "value": KICK},
	{"at": 30.0, "cue": Cue.MOVE, "value": RUN_LEFT},
	{"at": 31.0, "cue": Cue.JUMP, "value": null},
	{"at": 32.0, "cue": Cue.MOVE, "value": STAND},
	{"at": 33.2, "cue": Cue.QUIT, "value": null},
]
const TIMELINE_BY_REEL: Dictionary[String, Array] = {
	"fight": TIMELINE,
	"move": MOVE_TIMELINE,
}
const REEL_ARGUMENT: String = "--reel="
const MOVE_ACTIONS: Array[StringName] = [
	&"move_forward", &"move_back", &"move_left", &"move_right", &"walk", &"sprint"
]
## Câmeras que acompanham o jogador: onde ficam em relação a ele.
const TRACK_OFFSETS: Dictionary[String, Vector3] = {
	"TrackSide": Vector3(5.2, 1.1, -0.6),
	"TrackThree": Vector3(3.4, 1.5, -4.2),
}
const TRACK_LOOK_HEIGHT: float = 1.0
const CHASE_CAMERA: String = "Chase"
## Riscas no chão liso, uma por metro, para o olho medir o passo e ver pé patinando.
const STRIPE_COUNT: int = 160
const STRIPE_SIZE: Vector3 = Vector3(40.0, 0.004, 0.05)
const STRIPE_COLOR: Color = Color(0.486, 0.494, 0.596)
const GROUND_STRETCH: float = 8.0
const JUMP_HOLD_SECONDS: float = 0.1
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
	UnarmedFighter.Move.FLYING_FRONT_KICK: "Chute frontal voador",
	UnarmedFighter.Move.FLYING_ROUNDHOUSE_KICK: "Chute circular voador",
	UnarmedFighter.Move.FLYING_SIDE_KICK: "Chute lateral voador",
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
var _timeline: Array = TIMELINE
var _track_cameras: Dictionary[String, Camera3D] = {}
var _face_focus: Vector3 = Vector3(0.0, 1.75, 0.0)
var _cue_players: Dictionary[Cue, Callable] = {
	Cue.ATTACK: _request_attack,
	Cue.CAMERA: _cut_to_camera,
	Cue.MOOD: _show_mood,
	Cue.TIME_SCALE: _set_time_scale,
	Cue.BODY: _change_body,
	Cue.QUIT: _quit,
	Cue.MOVE: _hold_move_actions,
	Cue.JUMP: _jump,
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

	for argument in OS.get_cmdline_user_args():
		if argument.begins_with(REEL_ARGUMENT):
			_set_up_reel(argument.trim_prefix(REEL_ARGUMENT))

	for camera_name in CAMERA_TARGETS:
		var camera: Camera3D = get_node(camera_name) as Camera3D

		camera.look_at(CAMERA_TARGETS[camera_name])


func _process(delta: float) -> void:
	_seconds += delta
	_follow_face(delta)
	_follow_player()

	if _seconds < _timeline[_next_cue].at:
		return

	_cue_players[_timeline[_next_cue].cue].call(_timeline[_next_cue].value)
	_next_cue = mini(_next_cue + 1, _timeline.size() - 1)


## O roteiro andando precisa do controle ligado (é ele que lê as ações seguradas), de chão que
## não acabe e de câmeras que sigam o jogador.
func _set_up_reel(reel_name: String) -> void:
	_timeline = TIMELINE_BY_REEL[reel_name]
	_player.is_input_enabled = true
	($Ground as Node3D).scale = Vector3.ONE * GROUND_STRETCH
	_stripe_ground()

	for camera_name in TRACK_OFFSETS:
		var camera: Camera3D = Camera3D.new()

		camera.fov = 36.0
		add_child(camera)
		_track_cameras[camera_name] = camera


func _stripe_ground() -> void:
	var stripe_mesh: BoxMesh = BoxMesh.new()
	var stripe_material: StandardMaterial3D = StandardMaterial3D.new()

	stripe_material.albedo_color = STRIPE_COLOR
	stripe_mesh.size = STRIPE_SIZE
	stripe_mesh.material = stripe_material

	for index in STRIPE_COUNT:
		var stripe: MeshInstance3D = MeshInstance3D.new()

		stripe.mesh = stripe_mesh
		stripe.position.z = STRIPE_COUNT / 2.0 - index
		add_child(stripe)


func _follow_player() -> void:
	var look_at_point: Vector3 = _player.global_position + Vector3.UP * TRACK_LOOK_HEIGHT

	for camera_name in _track_cameras:
		var camera: Camera3D = _track_cameras[camera_name]

		camera.global_position = _player.global_position + TRACK_OFFSETS[camera_name]
		camera.look_at(look_at_point)


func _hold_move_actions(held_actions: Array[StringName]) -> void:
	for action in MOVE_ACTIONS:
		Input.action_release(action)

	for action in held_actions:
		Input.action_press(action)


func _jump(_value: Variant) -> void:
	Input.action_press(&"jump")
	await get_tree().create_timer(JUMP_HOLD_SECONDS).timeout
	Input.action_release(&"jump")


func _request_attack(attack: UnarmedFighter.Attack) -> void:
	_fighter.request_attack(attack)


func _cut_to_camera(camera_name: String) -> void:
	var camera: Camera3D = _track_cameras.get(camera_name, get_node_or_null(camera_name))

	_caption.text = ""

	if camera_name == CHASE_CAMERA:
		_player.make_camera_current()

		return

	camera.make_current()


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
