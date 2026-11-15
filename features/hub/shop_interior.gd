class_name ShopInterior
extends Node3D
## Furniture and goods of one shop. Nothing in here casts sun shadows (the hall is
## roofed) and every mesh stops being drawn beyond visible_distance, so the full
## interiors of the market cost nothing from across the square.

const HYSTERESIS_MARGIN: float = 6.0

@export var visible_distance: float = 60.0


func _ready() -> void:
	var meshes: Array[Node] = find_children("*", "GeometryInstance3D", true, false)

	for mesh in meshes:
		_hide_from_afar(mesh as GeometryInstance3D)


func _hide_from_afar(mesh: GeometryInstance3D) -> void:
	mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mesh.visibility_range_end = visible_distance
	mesh.visibility_range_end_margin = HYSTERESIS_MARGIN
