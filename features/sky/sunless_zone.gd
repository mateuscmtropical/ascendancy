class_name SunlessZone
extends Node3D
## Volume onde a luz do sol não chega (a cripta, debaixo da terra). Com a câmera aqui dentro o
## DayNightCycle apaga a luz direcional: lá embaixo ela só iluminaria o piso por engano e a sombra
## dela redesenharia a cidade inteira lá em cima a cada quadro.

const GROUP: StringName = &"sunless_zones"

## Caixa no espaço deste nó.
@export var box: AABB = AABB()


func _enter_tree() -> void:
	add_to_group(GROUP)


func contains(point: Vector3) -> bool:
	var local_point: Vector3 = global_transform.affine_inverse() * point

	return box.has_point(local_point)
