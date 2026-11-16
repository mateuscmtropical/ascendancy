class_name FpsCounter
extends CanvasLayer
## Quadros por segundo no canto da tela, atualizado algumas vezes por segundo.

const REFRESH_SECONDS: float = 0.25

var _seconds_since_refresh: float = 0.0

@onready var _label: Label = $Label


func _process(delta: float) -> void:
	var frames_per_second: int

	_seconds_since_refresh += delta

	if _seconds_since_refresh < REFRESH_SECONDS:
		return

	_seconds_since_refresh = 0.0
	frames_per_second = roundi(Engine.get_frames_per_second())
	_label.text = "%d FPS" % frames_per_second
