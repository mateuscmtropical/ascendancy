extends GutTest

const AHEAD: float = 8.0
const HILL: PackedScene = preload("res://art/destruction/sliced_hill.gltf")
const SLASH_WAIT_SECONDS: float = 0.6

var _stage: Node3D


func before_each() -> void:
	_stage = Node3D.new()
	add_child_autofree(_stage)


func test_longer_charge_cuts_harder_and_farther() -> void:
	var tap: float = CleaveSpell.energy_for(0.0)
	var full: float = CleaveSpell.energy_for(CleaveSpell.FULL_CHARGE_SECONDS)

	assert_eq(tap, CleaveSpell.MIN_ENERGY)
	assert_eq(full, CleaveSpell.MAX_ENERGY)
	assert_eq(CleaveSpell.energy_for(10.0), full, "holding longer adds nothing")
	assert_gt(CleaveSpell.length_for(full), CleaveSpell.length_for(tap) * 1.3)


func test_a_tap_fizzles_without_a_cut() -> void:
	var spell: CleaveSpell = _spell()
	var cuts: Array[Impact] = []

	spell.cut.connect(func(impact: Impact) -> void: cuts.append(impact))
	await wait_physics_frames(2)
	spell.begin_charge()
	await wait_physics_frames(3)
	spell.release()
	await wait_seconds(SLASH_WAIT_SECONDS)

	assert_eq(cuts.size(), 0)


func test_full_cut_slices_a_wall_at_chest_height_and_spares_the_bottom_course() -> void:
	var spell: CleaveSpell = _spell()
	var ruin: BlockRuin = BlockRuin.new()
	var cuts: Array[Impact] = []
	var bottom_course: Array[Node]

	# Parede do portão de lado, para a lâmina cruzar pedra e não o vão da porta.
	ruin.plan = BlockRuin.Plan.GATE
	ruin.position = Vector3(-2.0, 0, AHEAD)
	_stage.add_child(ruin)
	spell.cut.connect(func(impact: Impact) -> void: cuts.append(impact))
	await wait_physics_frames(2)
	bottom_course = _low_pieces(_pieces(ruin, false))
	spell.begin_charge()
	spell.charge_seconds = CleaveSpell.FULL_CHARGE_SECONDS
	spell.release()
	await wait_seconds(SLASH_WAIT_SECONDS)

	assert_eq(cuts.size(), CleaveSpell.SEGMENTS, "the blow arrives in steps along the blade")
	assert_gt(_pieces(ruin, true).size(), 3, "the cut breaks the wall it crosses")
	assert_gt(bottom_course.size(), 0)
	assert_false(
		bottom_course.any(func(piece: BreakablePiece) -> bool: return piece.is_loose),
		"the bottom course is below the blade"
	)


func test_the_blade_is_thin_and_misses_what_is_beside_it() -> void:
	var spell: CleaveSpell = _spell()
	var crate: WoodenCrate = WoodenCrate.new()

	crate.position = Vector3(2.5, 0, AHEAD)
	_stage.add_child(crate)
	await wait_physics_frames(2)
	spell.begin_charge()
	spell.charge_seconds = CleaveSpell.FULL_CHARGE_SECONDS
	spell.release()
	await wait_seconds(SLASH_WAIT_SECONDS)

	assert_eq(_pieces(crate, true).size(), 0, "a crate off the line stays whole")


func test_cutting_along_the_hill_frees_the_whole_top_and_keeps_the_base() -> void:
	var spell: CleaveSpell = _spell()
	var hill: FracturedBuilding = FracturedBuilding.new()

	hill.model = HILL
	hill.toughness_by_section = {"Base": 50.0}
	hill.linked_sections = ["Cap"]
	hill.rotation.y = PI
	hill.position = Vector3(0, 0, 13.0)
	_stage.add_child(hill)
	await wait_physics_frames(2)
	spell.begin_charge()
	spell.charge_seconds = CleaveSpell.FULL_CHARGE_SECONDS
	spell.release()
	await wait_seconds(SLASH_WAIT_SECONDS)

	var cap: Node = hill.find_child("Section_EARTH_Cap*", true, false)

	assert_gt(_pieces(cap, true).size(), 10, "the top is cut loose")
	assert_eq(_pieces(cap, false).size(), 0, "all of it, slice by slice")
	assert_eq(_pieces(hill.find_child("Section_EARTH_Base*", true, false), true).size(), 0)


func _spell() -> CleaveSpell:
	var body: Node3D = Node3D.new()
	var spell: CleaveSpell = CleaveSpell.new()

	_stage.add_child(body)
	spell.aim_from = body
	_stage.add_child(spell)

	return spell


func _pieces(holder: Node, loose: bool) -> Array[Node]:
	var pieces: Array[Node] = holder.find_children("*", "BreakablePiece", true, false)

	return pieces.filter(func(piece: BreakablePiece) -> bool: return piece.is_loose == loose)


func _low_pieces(pieces: Array[Node]) -> Array[Node]:
	return pieces.filter(
		func(piece: BreakablePiece) -> bool:
			return piece.global_position.y < BlockRuin.COURSE_HEIGHT
	)
