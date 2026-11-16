extends Node3D
## Folha de prints da Mula sem cabeça: aponta cada câmera para o seu alvo e escolhe a animação
## pela câmera pedida na linha de comando (--camera=<nome>) ou direto (--animation=<nome>).

const CAMERA_ARGUMENT: String = "--camera="
const ANIMATION_ARGUMENT: String = "--animation="
const CAMERA_TARGETS: Dictionary[String, Vector3] = {
	"MulaThreeQuarter": Vector3(0.0, 1.35, 0.0),
	"MulaSide": Vector3(0.0, 1.3, 0.0),
	"MulaBack": Vector3(0.0, 1.25, 0.0),
	"MulaNeck": Vector3(0.0, 1.8, 0.95),
	"MulaHooves": Vector3(0.1, 0.3, 0.6),
	"MulaRun": Vector3(0.0, 1.25, 0.0),
	"MulaScale": Vector3(0.0, 1.2, 1.0),
	"MulaFootprints": Vector3(0.0, 0.5, -0.6),
}
const ANIMATION_BY_CAMERA: Dictionary[String, StringName] = {
	"MulaRun": MulaSemCabeca.RUN_ANIMATION,
	"MulaThreeQuarter": MulaSemCabeca.RUN_ANIMATION,
	"MulaFootprints": MulaSemCabeca.WALK_ANIMATION,
}
## Câmeras que param a animação num quadro (segundos).
const POSE_SECONDS_BY_CAMERA: Dictionary[String, float] = {
	"MulaThreeQuarter": 0.3,
}
## Câmeras em que a mula anda para a frente (m/s), para as pegadas de lava ficarem no chão.
const WALK_SPEED_BY_CAMERA: Dictionary[String, float] = {
	"MulaFootprints": 1.3,
}
const WALK_START: float = -3.2

var _walk_speed: float = 0.0

@onready var _mula: MulaSemCabeca = $Mula


func _ready() -> void:
	for camera_name in CAMERA_TARGETS:
		var camera: Camera3D = get_node(camera_name) as Camera3D

		camera.look_at(CAMERA_TARGETS[camera_name])

	for argument in OS.get_cmdline_user_args():
		if argument.begins_with(CAMERA_ARGUMENT):
			_play_animation_of_camera(argument.trim_prefix(CAMERA_ARGUMENT))

		if argument.begins_with(ANIMATION_ARGUMENT):
			_mula.play_animation(StringName(argument.trim_prefix(ANIMATION_ARGUMENT)))


func _process(delta: float) -> void:
	_mula.position.z += _walk_speed * delta


func _play_animation_of_camera(camera_name: String) -> void:
	var animation_name: StringName = ANIMATION_BY_CAMERA.get(
		camera_name, MulaSemCabeca.IDLE_ANIMATION
	)

	_mula.play_animation(animation_name)

	if WALK_SPEED_BY_CAMERA.has(camera_name):
		_walk_speed = WALK_SPEED_BY_CAMERA[camera_name]
		_mula.position.z = WALK_START

	if POSE_SECONDS_BY_CAMERA.has(camera_name):
		_freeze_pose_at(animation_name, POSE_SECONDS_BY_CAMERA[camera_name])


## Congela a animação num quadro: pose de ataque para a conferência com a folha de conceito.
func _freeze_pose_at(animation_name: StringName, seconds: float) -> void:
	var player: AnimationPlayer = (
		_mula.find_child("AnimationPlayer", true, false) as AnimationPlayer
	)

	player.play(animation_name, 0.0)
	player.seek(seconds, true)
	player.speed_scale = 0.0
