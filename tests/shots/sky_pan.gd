extends Node3D
## Vídeo do céu noturno: a câmera sai da altura dos olhos na praça e sobe devagar pelo redemoinho de
## estrelas até o astro dourado, com o relógio andando (as estrelas piscam) e a interface escondida.
## Gravar com tools_src/record.sh res://tests/shots/sky_pan.tscn <saida.avi>; a cena fecha sozinha.

const OFFSCREEN_POSITION: Vector2i = Vector2i(-20000, -20000)
const NIGHT_TIME_OF_DAY: float = 0.75
const SETTLE_SECONDS: float = 1.0
const PAN_SECONDS: float = 13.0
const START_ROTATION: Vector3 = Vector3(0.05, 0.45, 0.0)
const END_ROTATION: Vector3 = Vector3(0.85, 1.1, 0.0)

var _elapsed_seconds: float = 0.0

@onready var _camera: Camera3D = $PanCamera
@onready var _day_night: DayNightCycle = $Hub/DayNight


func _ready() -> void:
	DisplayServer.window_set_position(OFFSCREEN_POSITION)
	_day_night.set_time_of_day(NIGHT_TIME_OF_DAY)
	_camera.rotation = START_ROTATION
	_take_over_view.call_deferred()


func _process(delta: float) -> void:
	var pan_progress: float
	var eased_progress: float

	_elapsed_seconds += delta
	pan_progress = clampf((_elapsed_seconds - SETTLE_SECONDS) / PAN_SECONDS, 0.0, 1.0)
	eased_progress = smoothstep(0.0, 1.0, pan_progress)
	_camera.rotation = START_ROTATION.lerp(END_ROTATION, eased_progress)

	if _elapsed_seconds >= SETTLE_SECONDS * 2.0 + PAN_SECONDS:
		get_tree().quit()


## A câmera do jogador e os menus da praça só existem depois do primeiro quadro.
func _take_over_view() -> void:
	var layers: Array[Node] = get_tree().root.find_children("*", "CanvasLayer", true, false)

	_camera.make_current()

	for layer in layers:
		(layer as CanvasLayer).hide()
