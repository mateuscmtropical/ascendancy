extends GutTest

const PEN: Rect2 = Rect2(78.5, 5.5, 20.0, 21.0)
const WANDER_SEED: int = 4242
const PICKS: int = 50
const TRUNK: Vector3 = Vector3(88.5, 15.5, 0.7)
const CLEARANCE: float = 1.0


func test_wander_targets_stay_inside_the_pen() -> void:
	var generator: RandomNumberGenerator = RandomNumberGenerator.new()
	var from: Vector2 = PEN.get_center()

	generator.seed = WANDER_SEED

	for pick in PICKS:
		from = FarmAnimal.pick_wander_target(PEN, from, generator)

		assert_true(PEN.has_point(from), "target %s inside the pen" % from)


func test_same_seed_gives_the_same_walk() -> void:
	var first: Array[Vector2] = _wander_path(WANDER_SEED)
	var second: Array[Vector2] = _wander_path(WANDER_SEED)
	var other: Array[Vector2] = _wander_path(WANDER_SEED + 1)

	assert_eq(first, second)
	assert_ne(first, other)


func test_wander_target_is_a_real_walk_away() -> void:
	var generator: RandomNumberGenerator = RandomNumberGenerator.new()
	var from: Vector2 = PEN.get_center()
	var target: Vector2

	generator.seed = WANDER_SEED
	target = FarmAnimal.pick_wander_target(PEN, from, generator)

	assert_gte(target.distance_to(from), FarmAnimal.MIN_WANDER_DISTANCE)


func test_wander_paths_keep_clear_of_trunks() -> void:
	var generator: RandomNumberGenerator = RandomNumberGenerator.new()
	var trunks: PackedVector3Array = PackedVector3Array([TRUNK])
	var from: Vector2 = Vector2(80.0, 7.0)
	var target: Vector2

	generator.seed = WANDER_SEED

	for pick in PICKS:
		target = FarmAnimal.pick_wander_target(PEN, from, generator, trunks, CLEARANCE)

		assert_true(
			FarmAnimal.is_path_clear(from, target, trunks, CLEARANCE),
			"walk %s -> %s clear of the trunk" % [from, target]
		)
		from = target


func test_path_through_a_trunk_is_blocked() -> void:
	var trunks: PackedVector3Array = PackedVector3Array([TRUNK])
	var west: Vector2 = Vector2(TRUNK.x - 5.0, TRUNK.y)
	var east: Vector2 = Vector2(TRUNK.x + 5.0, TRUNK.y)
	var north_east: Vector2 = Vector2(TRUNK.x + 5.0, TRUNK.y - 4.0)
	var north_west: Vector2 = Vector2(TRUNK.x - 5.0, TRUNK.y - 4.0)

	assert_false(FarmAnimal.is_path_clear(west, east, trunks, CLEARANCE))
	assert_true(FarmAnimal.is_path_clear(north_west, north_east, trunks, CLEARANCE))


func test_swing_radius_reaches_the_corners_of_the_body() -> void:
	var cow_body: Vector3 = Vector3(0.9, 1.4, 2.2)
	var corner: Vector2 = Vector2(cow_body.x, cow_body.z) / 2.0
	var reach: float = FarmAnimal.swing_radius(cow_body)

	assert_almost_eq(reach, corner.length(), 0.001)
	assert_gt(reach, cow_body.z / 2.0, "turning in place sweeps past half the length")


func test_step_never_overshoots_the_target() -> void:
	var target: Vector2 = Vector2(3.0, 0.0)
	var halfway: Vector2 = FarmAnimal.step_toward(Vector2.ZERO, target, 1.5)
	var arrived: Vector2 = FarmAnimal.step_toward(halfway, target, 10.0)

	assert_almost_eq(halfway.x, 1.5, 0.001)
	assert_eq(arrived, target)


func test_cruise_speed_slows_down_near_the_target() -> void:
	var far: float = FarmAnimal.cruise_speed(0.5, 10.0)
	var near: float = FarmAnimal.cruise_speed(0.5, 0.1)

	assert_almost_eq(far, 0.5, 0.001)
	assert_almost_eq(near, 0.5 * FarmAnimal.MIN_SPEED_SHARE, 0.001)


func test_heading_angle_faces_the_target() -> void:
	var toward_plus_z: float = FarmAnimal.heading_angle(Vector2.ZERO, Vector2(0.0, 3.0))
	var toward_plus_x: float = FarmAnimal.heading_angle(Vector2.ZERO, Vector2(3.0, 0.0))

	assert_almost_eq(toward_plus_z, 0.0, 0.001)
	assert_almost_eq(toward_plus_x, PI / 2.0, 0.001)


func _wander_path(wander_seed: int) -> Array[Vector2]:
	var generator: RandomNumberGenerator = RandomNumberGenerator.new()
	var path: Array[Vector2] = []
	var from: Vector2 = PEN.get_center()

	generator.seed = wander_seed

	for pick in 5:
		from = FarmAnimal.pick_wander_target(PEN, from, generator)
		path.append(from)

	return path
