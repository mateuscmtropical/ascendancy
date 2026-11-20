extends Node3D
## Conferência dos bichos da fazenda: cada um toca a própria animação (`--animation=Walk`,
## padrão) em laço, e as câmeras com a meta `look_at` apontam para o alvo antes do print.

const ANIMATION_ARGUMENT: String = "--animation="
const DEFAULT_ANIMATION: StringName = &"WalkSlow"
const LOOK_AT_META: StringName = &"look_at"


func _ready() -> void:
	var animation_name: StringName = _read_animation_name()

	for player: AnimationPlayer in find_children("*", "AnimationPlayer", true, false):
		_play_looped(player, animation_name)

	for camera: Camera3D in find_children("*", "Camera3D", false, false):
		camera.look_at(camera.get_meta(LOOK_AT_META, Vector3.ZERO))


func _read_animation_name() -> StringName:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with(ANIMATION_ARGUMENT):
			return StringName(argument.trim_prefix(ANIMATION_ARGUMENT))

	return DEFAULT_ANIMATION


func _play_looped(player: AnimationPlayer, animation_name: StringName) -> void:
	if not player.has_animation(animation_name):
		return

	player.get_animation(animation_name).loop_mode = Animation.LOOP_LINEAR
	player.play(animation_name)
