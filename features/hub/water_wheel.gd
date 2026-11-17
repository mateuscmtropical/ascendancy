class_name WaterWheel
extends Node3D
## Roda d'água do moinho da fazenda: gira sem parar em volta do próprio eixo X, empurrada pela água
## que cai da calha logo depois do topo (o topo anda para o lado da queda). A origem do modelo é o
## eixo, então o giro não tira a roda do lugar.

@export var turns_per_minute: float = 6.0


func _process(delta: float) -> void:
	rotation.x = angle_after(rotation.x, turns_per_minute, delta)


## Ângulo da roda depois de `delta` segundos, sempre entre 0 e TAU.
static func angle_after(angle: float, turns_per_minute: float, delta: float) -> float:
	var step: float = TAU * turns_per_minute / 60.0 * delta

	return fposmod(angle + step, TAU)
