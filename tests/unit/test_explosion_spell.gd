extends GutTest

var _stage: Node3D


func before_each() -> void:
	_stage = Node3D.new()
	add_child_autofree(_stage)


func test_longer_charge_means_more_energy_up_to_the_cap() -> void:
	var tap: float = ExplosionSpell.energy_for(0.0)
	var half: float = ExplosionSpell.energy_for(ExplosionSpell.FULL_CHARGE_SECONDS / 2.0)
	var full: float = ExplosionSpell.energy_for(ExplosionSpell.FULL_CHARGE_SECONDS)

	assert_eq(tap, ExplosionSpell.MIN_ENERGY)
	assert_between(half, tap, full)
	assert_eq(full, ExplosionSpell.MAX_ENERGY)
	assert_eq(ExplosionSpell.energy_for(10.0), full, "holding longer adds nothing")


func test_stronger_spell_reaches_farther() -> void:
	var weak: float = ExplosionSpell.radius_for(ExplosionSpell.MIN_ENERGY)
	var strong: float = ExplosionSpell.radius_for(ExplosionSpell.MAX_ENERGY)

	assert_gt(strong, weak * 1.5)


func test_a_tap_fizzles_without_a_blast() -> void:
	var spell: ExplosionSpell = _spell()
	var blasts: Array[Impact] = []

	spell.blasted.connect(func(impact: Impact) -> void: blasts.append(impact))
	await wait_physics_frames(2)
	spell.begin_charge()
	await wait_physics_frames(3)
	spell.release()
	await wait_seconds(ExplosionSpell.HUSH_SECONDS + 0.2)

	assert_eq(blasts.size(), 0)


func test_full_charge_blasts_after_a_hush_and_breaks_stone() -> void:
	var spell: ExplosionSpell = _spell()
	var ruin: BlockRuin = BlockRuin.new()
	var blasts: Array[Impact] = []

	ruin.position = Vector3(0, 0, ExplosionSpell.CAST_DISTANCE + 3.0)
	_stage.add_child(ruin)
	spell.blasted.connect(func(impact: Impact) -> void: blasts.append(impact))
	await wait_physics_frames(2)
	spell.begin_charge()
	spell.charge_seconds = ExplosionSpell.FULL_CHARGE_SECONDS
	spell.release()

	assert_eq(blasts.size(), 0, "the boom waits for the hush")

	await wait_seconds(ExplosionSpell.HUSH_SECONDS + 0.1)

	assert_eq(blasts.size(), 1)
	assert_eq(blasts[0].energy, ExplosionSpell.MAX_ENERGY)
	assert_gt(_loose_count(ruin), 10, "a full blast tears the ruin apart")


func test_blast_digs_a_crater_and_lights_a_fire_that_burns_out_to_charcoal() -> void:
	var spell: ExplosionSpell = _spell()
	var ground: BlastGround = BlastGround.new()
	var fire: FireGrid = FireGrid.new()
	var target: Vector3 = Vector3(0, 0, ExplosionSpell.CAST_DISTANCE)
	var aside: Vector3 = target + Vector3(5.5, 0, 0)

	ground.add_to_group(&"blast_ground")
	fire.add_to_group(&"fire_grid")
	fire.ground = ground
	fire.random_seed = 7
	_stage.add_child(ground)
	_stage.add_child(fire)
	await wait_physics_frames(2)
	spell.begin_charge()
	spell.charge_seconds = ExplosionSpell.FULL_CHARGE_SECONDS / 2.0
	spell.release()
	await wait_seconds(ExplosionSpell.HUSH_SECONDS + 0.1)

	assert_lt(ground.height_at(target), -0.5, "a crater where it fell")
	assert_gt(fire.burning_cell_count(), 0, "the grass caught fire")

	fire.advance(120.0)

	assert_eq(fire.burning_cell_count(), 0, "the fire dies on its own")
	assert_gt(ground.burn_at(aside), FireGrid.FUEL_BURN_LIMIT, "burnt grass left around the crater")


func _spell() -> ExplosionSpell:
	var floor_body: StaticBody3D = StaticBody3D.new()
	var floor_shape: CollisionShape3D = CollisionShape3D.new()
	var body: Node3D = Node3D.new()
	var spell: ExplosionSpell = ExplosionSpell.new()

	floor_shape.shape = WorldBoundaryShape3D.new()
	floor_body.add_child(floor_shape)
	_stage.add_child(floor_body)
	_stage.add_child(body)
	spell.aim_from = body
	_stage.add_child(spell)

	return spell


func _loose_count(holder: Node) -> int:
	var pieces: Array[Node] = holder.find_children("*", "BreakablePiece", true, false)

	return pieces.filter(func(piece: BreakablePiece) -> bool: return piece.is_loose).size()
