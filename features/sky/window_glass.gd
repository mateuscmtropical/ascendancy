class_name WindowGlass
extends RefCounted
## Troca, na importação dos modelos da cidade, o vidro liso das janelas (material M_TownGlass de
## tools_src/build_town_houses.py) pelo vidro que acende à noite (art/materials/window_glass.tres).

const GLASS_MATERIAL_NAME: String = "M_TownGlass"
const NIGHT_GLASS: Material = preload("res://art/materials/window_glass.tres")


static func light_up_windows(scene: Node) -> void:
	var meshes: Array[Node] = scene.find_children("*", "MeshInstance3D", true, false)

	for mesh_instance in meshes:
		_swap_glass(mesh_instance as MeshInstance3D)


static func _swap_glass(mesh_instance: MeshInstance3D) -> void:
	var mesh: ArrayMesh = mesh_instance.mesh as ArrayMesh

	if mesh == null:
		return

	for surface in mesh.get_surface_count():
		var material: Material = mesh.surface_get_material(surface)

		if material and material.resource_name == GLASS_MATERIAL_NAME:
			mesh.surface_set_material(surface, NIGHT_GLASS)
