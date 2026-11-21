extends GutTest


func _mesh(mesh_name: String, parent: Node) -> MeshInstance3D:
	var mesh: MeshInstance3D = MeshInstance3D.new()

	mesh.name = mesh_name
	parent.add_child(mesh)

	return mesh


func test_only_named_meshes_lose_their_shadow() -> void:
	var scenery: Node3D = Node3D.new()
	var group: ShadowlessGroup = ShadowlessGroup.new()
	var lawn: MeshInstance3D = _mesh("GroundLawn", scenery)
	var hedge: MeshInstance3D = _mesh("GroundHedge", scenery)
	var countryside: MeshInstance3D = _mesh("Countryside2", scenery)

	add_child_autofree(scenery)
	group.target = NodePath("..")
	group.mesh_names = PackedStringArray(["GroundLawn", "Countryside"])
	scenery.add_child(group)

	assert_eq(lawn.cast_shadow, GeometryInstance3D.SHADOW_CASTING_SETTING_OFF)
	assert_eq(countryside.cast_shadow, GeometryInstance3D.SHADOW_CASTING_SETTING_OFF)
	assert_eq(
		hedge.cast_shadow, GeometryInstance3D.SHADOW_CASTING_SETTING_ON, "hedges keep their shade"
	)


func test_without_names_every_mesh_loses_its_shadow() -> void:
	var group: ShadowlessGroup = ShadowlessGroup.new()
	var pine: MeshInstance3D = _mesh("Pine", group)

	add_child_autofree(group)

	assert_eq(pine.cast_shadow, GeometryInstance3D.SHADOW_CASTING_SETTING_OFF)
