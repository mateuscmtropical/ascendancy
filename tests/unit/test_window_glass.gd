extends GutTest

const HOUSE_MODEL: PackedScene = preload("res://art/town/houses/sobrado_w10_0.gltf")
const SHOP_MODEL: PackedScene = preload("res://art/town/shops/shop_smith.gltf")
const SHOP_INTERIOR_MODEL: PackedScene = preload("res://art/town/shops/shop_magic_interior.gltf")
const FURNITURE_GLASS_NAME: String = "M_TownVitrine"


func test_house_windows_use_the_glass_that_lights_up_at_night() -> void:
	var materials: Array[Material] = _imported_materials(HOUSE_MODEL)
	var has_plain_glass: bool = _has_material_named(materials, WindowGlass.GLASS_MATERIAL_NAME)

	assert_true(materials.has(WindowGlass.NIGHT_GLASS), "imported windows wear the night glass")
	assert_false(has_plain_glass, "no plain glass left")


func test_shop_windows_use_the_shopfront_glass_that_lights_up_at_night() -> void:
	var materials: Array[Material] = _imported_materials(SHOP_MODEL)
	var has_plain_shopfront: bool = _has_material_named(
		materials, WindowGlass.SHOPFRONT_MATERIAL_NAME
	)

	assert_true(materials.has(WindowGlass.SHOPFRONT_GLASS), "shop windows wear the shopfront glass")
	assert_false(has_plain_shopfront, "no plain shopfront glass left")


func test_glass_of_the_furniture_stays_plain() -> void:
	var materials: Array[Material] = _imported_materials(SHOP_INTERIOR_MODEL)
	var has_furniture_glass: bool = _has_material_named(materials, FURNITURE_GLASS_NAME)

	assert_true(has_furniture_glass, "glass cases and flasks keep their own glass")
	assert_false(materials.has(WindowGlass.SHOPFRONT_GLASS), "furniture glass does not glow")


func _imported_materials(model: PackedScene) -> Array[Material]:
	var scene: Node = model.instantiate()
	var materials: Array[Material] = _surface_materials(scene)

	scene.free()

	return materials


func _has_material_named(materials: Array[Material], material_name: String) -> bool:
	var is_named: Callable = func(material: Material) -> bool:
		return material != null and material.resource_name == material_name

	return materials.any(is_named)


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
