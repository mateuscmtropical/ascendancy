class_name ShadowlessGroup
extends Node3D
## Turns off sun shadow casting for the meshes under target (this node by default).
## Used on scenery whose shadow never lands where the player can see it (far backdrop, flat ground),
## so the shadow pass skips those draw calls. With mesh_names set, only the meshes with one of
## those names (trailing digits ignored) lose their shadow.

@export var target: NodePath = ^"."
@export var mesh_names: PackedStringArray = []


func _ready() -> void:
	var root: Node = get_node(target)
	var meshes: Array[Node] = root.find_children("*", "GeometryInstance3D", true, false)

	for mesh in meshes:
		if is_shadowless(mesh.name):
			(mesh as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


func is_shadowless(mesh_name: String) -> bool:
	return mesh_names.is_empty() or mesh_name.rstrip("0123456789") in mesh_names
