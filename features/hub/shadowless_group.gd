class_name ShadowlessGroup
extends Node3D
## Turns off sun shadow casting for every mesh under this node.
## Used on scenery whose shadow never lands where the player can see it,
## so the shadow pass skips those draw calls.


func _ready() -> void:
	var meshes: Array[Node] = find_children("*", "GeometryInstance3D", true, false)

	for mesh in meshes:
		(mesh as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
