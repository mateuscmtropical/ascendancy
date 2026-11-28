extends GutTest

const PLAYER_SCENE: PackedScene = preload("res://features/player/player.tscn")
const COTTAGE: PackedScene = preload("res://art/destruction/cottage.gltf")
const BLOCK_SIZE: Vector3 = Vector3(0.8, 0.4, 0.5)
const PUNCH: UnarmedFighter.Attack = UnarmedFighter.Attack.PUNCH
const KICK: UnarmedFighter.Attack = UnarmedFighter.Attack.KICK

var _material: StandardMaterial3D = StandardMaterial3D.new()
var _stage: Node3D


func before_each() -> void:
	_stage = Node3D.new()
	add_child_autofree(_stage)


func test_energy_is_full_at_the_blow_and_gone_past_its_reach() -> void:
	var impact: Impact = Impact.new(Vector3.ZERO, Vector3.FORWARD, 2.0, 100.0)

	assert_eq(impact.energy_at(Vector3.ZERO), 100.0)
	assert_gt(impact.energy_at(Vector3(0.5, 0, 0)), impact.energy_at(Vector3(1.5, 0, 0)))
	assert_eq(impact.energy_at(Vector3(2.5, 0, 0)), 0.0, "nothing past the radius")


func test_a_cut_carries_its_energy_along_the_whole_line() -> void:
	var cut: Impact = Impact.new(Vector3.ZERO, Vector3.RIGHT, 0.5, 100.0, 10.0)

	assert_eq(cut.energy_at(Vector3(7.0, 0, 0)), 100.0)
	assert_eq(cut.energy_at(Vector3(11.0, 0, 0)), 0.0, "past the end of the line")
	assert_almost_eq(cut.push_direction_at(Vector3(5, 1, 1)).z, 1.0, 0.01, "flat, out of the cut")


func test_what_a_cut_frees_slides_off_flat_without_spinning() -> void:
	var slice: BreakablePiece = _piece_at(Vector3(3, 1.6, 0.3), Destruction.Substance.EARTH)
	var punch: BreakablePiece = _piece_at(Vector3(3, 1.6, 6.3), Destruction.Substance.EARTH)

	await _settle()
	Destruction.strike(Impact.new(Vector3(0, 1.4, 0), Vector3.RIGHT, 0.7, 3000.0, 6.0), _stage)
	Destruction.strike(Impact.new(Vector3(3, 1.4, 6.0), Vector3.BACK, 0.7, 3000.0), _stage)
	await get_tree().physics_frame

	assert_true(slice.is_loose)
	assert_almost_eq(slice.angular_velocity.length(), 0.0, 0.01, "a cut slice does not tumble")
	assert_lt(slice.linear_velocity.length(), BreakablePiece.MAX_SLIDE_SPEED + 0.01)
	assert_gt(slice.linear_velocity.z, absf(slice.linear_velocity.y) * 3.0, "pushed sideways")
	assert_gt(punch.angular_velocity.length(), 1.0, "a round blow still sends it spinning")


func test_punch_breaks_wood_but_not_stone() -> void:
	var plank: BreakablePiece = _piece_at(Vector3(0, 1.35, 1.0), Destruction.Substance.WOOD)
	var block: BreakablePiece = _piece_at(Vector3(4, 1.35, 1.0), Destruction.Substance.STONE)
	var jab: float = UnarmedFighter.ENERGY_BY_MOVE[UnarmedFighter.Move.JAB]

	await _settle()
	Destruction.strike(Impact.new(Vector3(0, 1.35, 0.75), Vector3.BACK, 0.45, jab), _stage)
	Destruction.strike(Impact.new(Vector3(4, 1.35, 0.75), Vector3.BACK, 0.45, jab * 3.0), _stage)

	assert_true(plank.is_loose, "jab cracks the board")
	assert_false(block.is_loose, "even three jabs' worth leaves stone standing")


func test_stronger_blow_breaks_more_and_throws_harder() -> void:
	var weak_count: int = await _pieces_broken_by(300.0)
	var weak_speed: float
	var strong_count: int

	await get_tree().physics_frame
	weak_speed = _fastest_loose_speed()
	_clear_stage()
	strong_count = await _pieces_broken_by(3000.0)
	await get_tree().physics_frame

	assert_gt(strong_count, weak_count)
	assert_gt(_fastest_loose_speed(), weak_speed)


func test_what_rested_on_a_broken_block_comes_down_with_it() -> void:
	var bottom: BreakablePiece = _piece_at(Vector3(0, 0.2, 0), Destruction.Substance.STONE)
	var middle: BreakablePiece = _piece_at(Vector3(0, 0.6, 0), Destruction.Substance.STONE)
	var top: BreakablePiece = _piece_at(Vector3(0.3, 1.0, 0), Destruction.Substance.STONE)
	var beside: BreakablePiece = _piece_at(Vector3(2.0, 0.2, 0), Destruction.Substance.STONE)

	await _settle()
	# Raio curto: o golpe só alcança o bloco de baixo; os de cima caem por perder o apoio.
	Destruction.strike(Impact.new(Vector3(0, 0.2, -0.3), Vector3.BACK, 0.22, 600.0), _stage)

	assert_true(bottom.is_loose)
	assert_lt(
		middle.energy_from(Impact.new(Vector3(0, 0.2, -0.3), Vector3.BACK, 0.22, 600.0)), 200.0
	)
	assert_true(middle.is_loose, "sat on the broken block")
	assert_true(top.is_loose, "sat on the block that fell")
	assert_false(beside.is_loose, "nothing to do with it")


func test_a_block_still_resting_on_another_support_stays() -> void:
	var left: BreakablePiece = _piece_at(Vector3(-0.45, 0.2, 0), Destruction.Substance.STONE)
	var right: BreakablePiece = _piece_at(Vector3(0.45, 0.2, 0), Destruction.Substance.STONE)
	var bridge: BreakablePiece = _piece_at(Vector3(0, 0.6, 0), Destruction.Substance.STONE)

	await _settle()
	Destruction.strike(Impact.new(Vector3(-0.45, 0.2, -0.3), Vector3.BACK, 0.22, 600.0), _stage)

	assert_true(left.is_loose)
	assert_false(right.is_loose)
	assert_false(bridge.is_loose, "still sits on the right block")


func test_standing_kick_bounces_off_the_door_and_flying_kick_bursts_it() -> void:
	var gate: BlockRuin = BlockRuin.new()
	var door: Array[BreakablePiece]
	var fighter: UnarmedFighter = UnarmedFighter.new()
	var aim: Vector3 = Vector3(0, 0, -1.0)

	gate.plan = BlockRuin.Plan.GATE
	_stage.add_child(gate)
	_stage.add_child(fighter)
	door = _wooden_pieces(gate)
	await _settle()

	fighter.request_attack(KICK)
	Destruction.strike(fighter.impact_of(UnarmedFighter.Move.SIDE_KICK, aim, Vector3.BACK), _stage)

	assert_eq(_loose_count(door), 0, "the strongest standing kick does not break the door")

	Destruction.strike(
		fighter.impact_of(UnarmedFighter.Move.FLYING_FRONT_KICK, aim, Vector3.BACK), _stage
	)

	assert_eq(_loose_count(door), door.size(), "the weakest flying kick bursts the whole door")


func test_no_two_blocks_of_a_ruin_overlap() -> void:
	var temple: BlockRuin = BlockRuin.new()
	var gate: BlockRuin = BlockRuin.new()
	var query: PhysicsShapeQueryParameters3D = PhysicsShapeQueryParameters3D.new()
	var overlaps: int = 0

	gate.plan = BlockRuin.Plan.GATE
	gate.position = Vector3(20, 0, 0)
	_stage.add_child(temple)
	_stage.add_child(gate)
	await _settle()

	# Encolhida um pouco: blocos encostados não contam, só os que entram um no outro.
	for piece in _stage.find_children("*", "BreakablePiece", true, false):
		var body: BreakablePiece = piece
		var shape: BoxShape3D = (body.get_child(0) as CollisionShape3D).shape.duplicate()

		shape.size -= Vector3.ONE * 0.02
		query.shape = shape
		query.transform = body.global_transform
		query.exclude = [body.get_rid()]
		query.collision_mask = Destruction.BREAKABLE_LAYER
		overlaps += body.get_world_3d().direct_space_state.intersect_shape(query).size()

	assert_eq(overlaps, 0, "overlapping blocks would burst apart when freed")


func test_cottage_stands_whole_until_a_blow_breaks_a_section() -> void:
	var cottage: FracturedBuilding = FracturedBuilding.new()
	var front_wall: Node3D
	var back_wall: Node3D
	var kick: float = UnarmedFighter.ENERGY_BY_MOVE[UnarmedFighter.Move.FLYING_SIDE_KICK]

	cottage.model = COTTAGE
	_stage.add_child(cottage)
	front_wall = cottage.find_child("Section_PLASTER_FrontWall", true, false)
	back_wall = cottage.find_child("Section_PLASTER_BackWall", true, false)
	await _settle()

	assert_eq(cottage.find_children("*", "BreakablePiece", true, false).size(), 142)
	Destruction.strike(Impact.new(Vector3(1.2, 1.4, 2.3), Vector3.FORWARD, 0.55, kick), _stage)
	assert_true(_whole_of(front_wall).visible, "a kick does not break plaster")

	Destruction.strike(Impact.new(Vector3(1.2, 1.4, 2.6), Vector3.FORWARD, 1.5, 900.0), _stage)
	assert_false(_whole_of(front_wall).visible, "the broken wall shows its pieces")
	assert_true(_whole_of(back_wall).visible, "the far wall stays one mesh")


func test_cottage_door_bursts_only_to_a_flying_kick() -> void:
	var cottage: FracturedBuilding = FracturedBuilding.new()
	var fighter: UnarmedFighter = UnarmedFighter.new()
	var door: Array[BreakablePiece]
	var aim: Vector3 = Vector3(-1.0, 0, 2.7)

	cottage.model = COTTAGE
	_stage.add_child(cottage)
	_stage.add_child(fighter)
	door = _wooden_pieces(cottage.find_child("Section_WOOD_Door", true, false))
	await _settle()

	Destruction.strike(
		fighter.impact_of(UnarmedFighter.Move.SIDE_KICK, aim, Vector3.FORWARD), _stage
	)
	assert_eq(_loose_count(door), 0)
	Destruction.strike(
		fighter.impact_of(UnarmedFighter.Move.FLYING_FRONT_KICK, aim, Vector3.FORWARD), _stage
	)
	assert_eq(_loose_count(door), door.size())


func test_loose_pieces_never_pass_the_cap() -> void:
	var extra: int = 5

	for index in Destruction.MAX_LOOSE_PIECES + extra:
		var piece: BreakablePiece = _piece_at(
			Vector3(0, 50.0 + index, 0), Destruction.Substance.WOOD
		)

		piece.break_free()

	assert_eq(Destruction.loose_piece_count(), Destruction.MAX_LOOSE_PIECES)


func test_player_punch_breaks_the_crate_in_front() -> void:
	var player: PlayerController = _spawn_player()
	var crate: WoodenCrate = WoodenCrate.new()
	var planks: Array[BreakablePiece]

	# Em cima de outro caixote: o soco sai na altura do peito.
	crate.position = Vector3(0, 0.6, 0.85)
	_stage.add_child(crate)
	planks = _wooden_pieces(crate)
	await _settle()

	_press(&"attack_punch")
	await _run_physics(0.5)

	assert_gt(_loose_count(planks), 0, "the jab lands on the crate in front of the body")


func _pieces_broken_by(energy: float) -> int:
	var ruin: BlockRuin = BlockRuin.new()

	_stage.add_child(ruin)
	await _settle()

	return Destruction.strike(
		Impact.new(Vector3(0, 1.0, -3.0), Vector3.FORWARD, 3.0, energy), _stage
	)


func _whole_of(section: Node3D) -> MeshInstance3D:
	return section.find_child("Whole_*", false, false) as MeshInstance3D


func _fastest_loose_speed() -> float:
	var fastest: float = 0.0

	for piece in _stage.find_children("*", "BreakablePiece", true, false):
		fastest = maxf(fastest, (piece as BreakablePiece).linear_velocity.length())

	return fastest


func _clear_stage() -> void:
	_stage.queue_free()
	_stage = Node3D.new()
	add_child_autofree(_stage)


func _piece_at(spot: Vector3, substance: Destruction.Substance) -> BreakablePiece:
	var piece: BreakablePiece = BreakablePiece.make_box(BLOCK_SIZE, substance, _material)

	piece.position = spot
	_stage.add_child(piece)

	return piece


func _wooden_pieces(holder: Node) -> Array[BreakablePiece]:
	var planks: Array[BreakablePiece] = []

	for piece in holder.find_children("*", "BreakablePiece", true, false):
		if (piece as BreakablePiece).substance == Destruction.Substance.WOOD:
			planks.append(piece)

	return planks


func _loose_count(pieces: Array[BreakablePiece]) -> int:
	return pieces.filter(func(piece: BreakablePiece) -> bool: return piece.is_loose).size()


## Corpos recém-postos só entram na consulta do espaço físico depois de um passo de física.
func _settle() -> void:
	await get_tree().physics_frame
	await get_tree().physics_frame


func _run_physics(seconds: float) -> void:
	for frame in int(seconds * Engine.physics_ticks_per_second):
		await get_tree().physics_frame


func _spawn_player() -> PlayerController:
	var floor_body: StaticBody3D = StaticBody3D.new()
	var floor_shape: CollisionShape3D = CollisionShape3D.new()
	var player: PlayerController = PLAYER_SCENE.instantiate()

	floor_shape.shape = WorldBoundaryShape3D.new()
	floor_body.add_child(floor_shape)
	_stage.add_child(floor_body)
	_stage.add_child(player)

	return player


func _press(action: StringName) -> void:
	var event: InputEventAction = InputEventAction.new()

	event.action = action
	event.pressed = true
	Input.parse_input_event(event)
