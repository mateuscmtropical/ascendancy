extends GutTest

const PREFIXES: PackedStringArray = ["Grass", "Bench"]


func test_matching_prefix_is_wanted() -> void:
	assert_true(DistanceFade.has_wanted_prefix("Grass017", PREFIXES))
	assert_true(DistanceFade.has_wanted_prefix("Bench3", PREFIXES))


func test_other_names_are_left_alone() -> void:
	assert_false(DistanceFade.has_wanted_prefix("OldTree04", PREFIXES))


func test_no_prefix_takes_every_child() -> void:
	assert_true(DistanceFade.has_wanted_prefix("Anything", PackedStringArray()))


func test_meshes_get_a_visibility_range() -> void:
	var group: Node3D = Node3D.new()
	var tuft: MeshInstance3D = MeshInstance3D.new()
	var tree: MeshInstance3D = MeshInstance3D.new()
	var fade: DistanceFade = DistanceFade.new()

	tuft.name = "Grass001"
	tree.name = "OldTree01"
	group.add_child(tuft)
	group.add_child(tree)
	fade.child_prefixes = PackedStringArray(["Grass"])
	fade.range_end = 45.0
	group.add_child(fade)
	fade.target = NodePath("..")
	add_child_autofree(group)

	assert_eq(tuft.visibility_range_end, 45.0)
	assert_eq(tree.visibility_range_end, 0.0)
