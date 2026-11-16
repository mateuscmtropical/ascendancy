class_name WindowGlass
extends RefCounted
## Troca, na importação dos modelos da cidade, os vidros lisos que o Blender exporta pelos que
## acendem à noite: M_TownGlass (janelas das casas e janelas altas, tools_src/build_town_houses.py)
## vira art/materials/window_glass.tres, e M_TownShopfront (vitrines das lojas grandes,
## tools_src/build_market_shops.py) vira art/materials/shopfront_glass.tres. O vidro dos móveis
## (M_TownVitrine: estojos, frascos) fica como está. As janelas da fazenda (M_FarmGlass,
## tools_src/build_farm.py) acendem todas juntas: o sorteio por vidraça deixava a casa em xadrez.
## A lanterna das carroças (M_FarmLantern) é vidro fosco de dia e acende à noite.

const GLASS_MATERIAL_NAME: String = "M_TownGlass"
const SHOPFRONT_MATERIAL_NAME: String = "M_TownShopfront"
const FARM_GLASS_MATERIAL_NAME: String = "M_FarmGlass"
const LANTERN_MATERIAL_NAME: String = "M_FarmLantern"
const NIGHT_GLASS: Material = preload("res://art/materials/window_glass.tres")
const SHOPFRONT_GLASS: Material = preload("res://art/materials/shopfront_glass.tres")
const FARM_GLASS: Material = preload("res://art/materials/farm_window_glass.tres")
const LANTERN_GLASS: Material = preload("res://art/materials/lantern_glass.tres")
const NIGHT_MATERIAL_BY_NAME: Dictionary[String, Material] = {
	GLASS_MATERIAL_NAME: NIGHT_GLASS,
	SHOPFRONT_MATERIAL_NAME: SHOPFRONT_GLASS,
	FARM_GLASS_MATERIAL_NAME: FARM_GLASS,
	LANTERN_MATERIAL_NAME: LANTERN_GLASS,
}


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

		if material == null or not NIGHT_MATERIAL_BY_NAME.has(material.resource_name):
			continue

		mesh.surface_set_material(surface, NIGHT_MATERIAL_BY_NAME[material.resource_name])
