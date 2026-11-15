class_name ChurchBell
extends AudioStreamPlayer3D
## Sino da catedral: de tempos em tempos bate algumas vezes seguidas. Cada batida soa por cima da
## anterior (max_polyphony), como um sino de verdade que continua vibrando.

@export var first_ring_delay_seconds: float = 8.0
@export var tolls_per_ring: int = 3
@export var seconds_between_tolls: float = 3.2
@export var seconds_between_rings: float = 150.0

var _tolls_left: int = 0
var _timer: Timer = Timer.new()


func _ready() -> void:
	add_child(_timer)
	_timer.timeout.connect(_on_timer_timeout)
	_timer.start(first_ring_delay_seconds)


func _on_timer_timeout() -> void:
	var is_ring_over: bool = _tolls_left == 0

	if is_ring_over:
		_tolls_left = tolls_per_ring

	play()
	_tolls_left -= 1
	_timer.start(seconds_between_rings if _tolls_left == 0 else seconds_between_tolls)
