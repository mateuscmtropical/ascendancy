extends GutTest

const GROUND_MODEL: PackedScene = preload("res://art/town/ground.gltf")


func test_lawn_beds_are_grass() -> void:
	var ground: Node = GROUND_MODEL.instantiate()
	var bed: Node = ground.find_child("Bed0", true, false)
	var surface: GroundSurface.Kind = GroundSurface.of(bed)

	ground.free()

	assert_eq(surface, GroundSurface.Kind.GRASS)


func test_untagged_ground_is_stone() -> void:
	var ground: Node = GROUND_MODEL.instantiate()
	var street_block: Node = ground.find_child("Roundabout", true, false)
	var surface: GroundSurface.Kind = GroundSurface.of(street_block)

	ground.free()

	assert_eq(surface, GroundSurface.Kind.STONE)
	assert_eq(GroundSurface.of(null), GroundSurface.Kind.STONE)
