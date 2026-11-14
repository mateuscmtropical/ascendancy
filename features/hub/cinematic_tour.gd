class_name CinematicTour
extends Node3D
## Passeio de câmera em laço pelos Marker3D filhos, na ordem da cena.

@export var seconds_per_segment: float = 7.0

var _camera: Camera3D


func start_tour() -> void:
	var markers: Array[Marker3D] = _collect_markers()
	var tween: Tween

	_camera = Camera3D.new()
	_camera.fov = 55.0
	add_child(_camera)
	_camera.transform = markers[0].transform
	_camera.make_current()

	tween = create_tween().set_loops()

	for marker in markers.slice(1) + [markers[0]]:
		(
			tween
			. tween_property(_camera, ^"position", marker.position, seconds_per_segment)
			. set_trans(Tween.TRANS_SINE)
			. set_ease(Tween.EASE_IN_OUT)
		)
		(
			tween
			. parallel()
			. tween_property(_camera, ^"quaternion", marker.quaternion, seconds_per_segment)
			. set_trans(Tween.TRANS_SINE)
			. set_ease(Tween.EASE_IN_OUT)
		)


func _collect_markers() -> Array[Marker3D]:
	var markers: Array[Marker3D] = []

	for child in get_children():
		if child is Marker3D:
			markers.append(child)

	return markers
