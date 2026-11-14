extends Node
## Tira um print da cena sem roubar foco: janela fora da tela, espera, salva PNG e fecha.
## Argumentos (depois de --): --shot-out=<caminho.png>
## [--camera=<NomeDaCamera3D>] [--shot-delay=<segundos>]

const OFFSCREEN_POSITION: Vector2i = Vector2i(-20000, -20000)
const OUTPUT_ARGUMENT: String = "--shot-out="
const CAMERA_ARGUMENT: String = "--camera="
const DELAY_ARGUMENT: String = "--shot-delay="
const HEADLESS_DISPLAY: String = "headless"

@export var seconds_before_capture: float = 1.5

var _output_path: String = "user://shot.png"


func _ready() -> void:
	DisplayServer.window_set_position(OFFSCREEN_POSITION)

	_read_arguments()
	_capture_after_warmup()


func _read_arguments() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with(OUTPUT_ARGUMENT):
			_output_path = argument.trim_prefix(OUTPUT_ARGUMENT)

		if argument.begins_with(DELAY_ARGUMENT):
			seconds_before_capture = argument.trim_prefix(DELAY_ARGUMENT).to_float()

		if argument.begins_with(CAMERA_ARGUMENT):
			_make_camera_current.call_deferred(argument.trim_prefix(CAMERA_ARGUMENT))


func _make_camera_current(camera_name: String) -> void:
	var camera: Camera3D = get_parent().find_child(camera_name, true, false) as Camera3D

	camera.make_current()


func _capture_after_warmup() -> void:
	var image: Image

	await get_tree().create_timer(seconds_before_capture).timeout

	# Renderer dummy nunca emite frame_post_draw: no headless só valida que a cena carrega.
	if DisplayServer.get_name() == HEADLESS_DISPLAY:
		print("SHOT skipped (headless)")
		get_tree().quit()

		return

	await RenderingServer.frame_post_draw

	image = get_viewport().get_texture().get_image()
	image.save_png(_output_path)
	print("SHOT ", _output_path, " fps=", Engine.get_frames_per_second())
	get_tree().quit()
