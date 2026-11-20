class_name AnisotropicTextures
extends RefCounted
## Na importação dos modelos da cidade, os materiais com mipmap passam a filtrar anisotrópico:
## chão, calçadas e fachadas vistas de lado continuam nítidos ao longe sem o viés de mipmap
## negativo, que obrigava a GPU a ler a textura inteira a cada pixel distante. Material sem mipmap
## (folhagem com alpha scissor) fica como está.

const MIPMAPPED_FILTERS: Dictionary[BaseMaterial3D.TextureFilter, BaseMaterial3D.TextureFilter] = {
	BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS:
	BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC,
	BaseMaterial3D.TEXTURE_FILTER_NEAREST_WITH_MIPMAPS:
	BaseMaterial3D.TEXTURE_FILTER_NEAREST_WITH_MIPMAPS_ANISOTROPIC,
}


static func apply_to(scene: Node) -> void:
	var meshes: Array[Node] = scene.find_children("*", "MeshInstance3D", true, false)

	for mesh_instance in meshes:
		_apply_to_mesh((mesh_instance as MeshInstance3D).mesh)


static func _apply_to_mesh(mesh: Mesh) -> void:
	if mesh == null:
		return

	for surface in mesh.get_surface_count():
		var material: BaseMaterial3D = mesh.surface_get_material(surface) as BaseMaterial3D

		if material and MIPMAPPED_FILTERS.has(material.texture_filter):
			material.texture_filter = MIPMAPPED_FILTERS[material.texture_filter]
