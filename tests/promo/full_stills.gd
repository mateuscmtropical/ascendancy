extends Node
## Salva quadros de conferência do vídeo completo: em cada plano, um quadro em cada ponto de
## STILL_PROGRESS. Rodar com janela fora da tela (como tools_src/shot.sh) e --fixed-fps 30; combina
## com --from-shot/--to-shot do TrailerDirector. Argumento (depois de --): --stills-dir=<pasta>

const DIRECTORY_ARGUMENT: String = "--stills-dir="
const STILL_PROGRESS: Array[float] = [0.2, 0.5, 0.9]

@export var director: TrailerDirector

var _directory: String = "user://stills"
var _next_still: int = 0
var _last_shot: int = -1


func _ready() -> void:
	process_priority = 100

	for argument in OS.get_cmdline_user_args():
		if argument.begins_with(DIRECTORY_ARGUMENT):
			_directory = argument.trim_prefix(DIRECTORY_ARGUMENT)

	DirAccess.make_dir_recursive_absolute(_directory)


func _process(_delta: float) -> void:
	if director.shot_index != _last_shot:
		_last_shot = director.shot_index
		_next_still = 0

	if _next_still >= STILL_PROGRESS.size():
		return

	if director.shot_progress() < STILL_PROGRESS[_next_still]:
		return

	_save_still(_last_shot, _next_still)
	_next_still += 1


func _save_still(shot: int, still: int) -> void:
	var path: String = "%s/s%02d_%d.png" % [_directory, shot, still]

	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(path)
