extends GutTest

const HOUSE_MODEL: PackedScene = preload("res://art/town/houses/sobrado_w10_0.gltf")
const NIGHT_GLASS: Material = preload("res://art/materials/window_glass.tres")


func test_house_windows_use_the_glass_that_lights_up_at_night() -> void:
	var house: Node = HOUSE_MODEL.instantiate()
	var materials: Array[Material] = _surface_materials(house)
	var is_plain_glass: Callable = func(material: Material) -> bool:
		return material.resource_name == WindowGlass.GLASS_MATERIAL_NAME
	var has_plain_glass: bool = materials.any(is_plain_glass)

	house.free()

	assert_true(materials.has(NIGHT_GLASS), "imported windows wear the night glass")
	assert_false(has_plain_glass, "no plain glass left")


func _surface_materials(scene: Node) -> Array[Material]:
	var materials: Array[Material] = []
	var meshes: Array[Node] = scene.find_children("*", "MeshInstance3D", true, false)

	for mesh_instance in meshes:
		materials.append_array(_materials_of((mesh_instance as MeshInstance3D).mesh))

	return materials


func _materials_of(mesh: Mesh) -> Array[Material]:
	var materials: Array[Material] = []

	for surface in mesh.get_surface_count():
		materials.append(mesh.surface_get_material(surface))

	return materials
