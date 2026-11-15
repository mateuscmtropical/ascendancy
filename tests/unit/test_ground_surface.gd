extends GutTest

const GROUND_MODEL: PackedScene = preload("res://art/town/ground.gltf")
const FARM_YARD_MODEL: PackedScene = preload("res://art/town/farm/farm_yard.gltf")
const FARM_FIELDS_MODEL: PackedScene = preload("res://art/town/farm/farm_fields.gltf")


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


func test_farm_yard_lane_and_fields_are_dirt() -> void:
	var yard: Node = FARM_YARD_MODEL.instantiate()
	var fields: Node = FARM_FIELDS_MODEL.instantiate()
	var yard_surface: GroundSurface.Kind = GroundSurface.of(yard.find_child("Yard*", true, false))
	var lane_surface: GroundSurface.Kind = GroundSurface.of(yard.find_child("Path*", true, false))
	var pasture_surface: GroundSurface.Kind = GroundSurface.of(yard.find_child("Bed*", true, false))
	var field_surface: GroundSurface.Kind = GroundSurface.of(
		fields.find_child("Field*", true, false)
	)

	yard.free()
	fields.free()

	assert_eq(yard_surface, GroundSurface.Kind.DIRT)
	assert_eq(lane_surface, GroundSurface.Kind.DIRT)
	assert_eq(pasture_surface, GroundSurface.Kind.GRASS)
	assert_eq(field_surface, GroundSurface.Kind.DIRT)
