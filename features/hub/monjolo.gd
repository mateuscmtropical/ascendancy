class_name Monjolo
extends Node3D
## Braço do monjolo: a bica enche o cocho devagar e o peso da água vai erguendo o pilão; cheio, o
## cocho despeja, o braço volta de uma vez e o pilão cai no pilão de toco. O nó gira em volta do
## eixo Z local (o pino entre as forquilhas); ângulo positivo ergue o pilão.

@export var lifted_angle: float = 0.38
@export var fill_seconds: float = 4.5
@export var spill_seconds: float = 0.6
@export var fall_seconds: float = 0.35
@export var rest_seconds: float = 0.9

var _cycle_time: float = 0.0


func _process(delta: float) -> void:
	_cycle_time = fposmod(_cycle_time + delta, cycle_seconds())
	rotation.z = beam_angle_at(_cycle_time)


## Duração de uma batida inteira: enche, despeja, cai e descansa.
func cycle_seconds() -> float:
	return fill_seconds + spill_seconds + fall_seconds + rest_seconds


## Ângulo do braço num instante do ciclo. Enchendo, sobe cada vez mais rápido (a água pesa mais);
## despejando, fica no alto; caindo, desce acelerado como coisa solta; descansando, fica no fundo.
func beam_angle_at(cycle_time: float) -> float:
	var time: float = fposmod(cycle_time, cycle_seconds())
	var fall_start: float = fill_seconds + spill_seconds

	if time < fill_seconds:
		return lifted_angle * (1.0 - cos(time / fill_seconds * PI / 2.0))

	if time < fall_start:
		return lifted_angle

	if time < fall_start + fall_seconds:
		var fallen: float = (time - fall_start) / fall_seconds

		return lifted_angle * (1.0 - fallen * fallen)

	return 0.0
