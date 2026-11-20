extends GutTest

const SQUARE_ROUTE: PackedVector3Array = [
	Vector3(0.0, 0.0, 0.0),
	Vector3(10.0, 0.0, 0.0),
	Vector3(10.0, 0.0, 10.0),
	Vector3(0.0, 0.0, 10.0),
]


func test_route_length_closes_the_loop() -> void:
	assert_almost_eq(Carriage.route_length(SQUARE_ROUTE), 40.0, 0.001)


func test_point_along_walks_the_segments_in_order() -> void:
	var on_first: Vector3 = Carriage.point_along(SQUARE_ROUTE, 4.0)
	var on_second: Vector3 = Carriage.point_along(SQUARE_ROUTE, 15.0)
	var on_closing: Vector3 = Carriage.point_along(SQUARE_ROUTE, 35.0)

	assert_almost_eq(on_first.distance_to(Vector3(4.0, 0.0, 0.0)), 0.0, 0.001)
	assert_almost_eq(on_second.distance_to(Vector3(10.0, 0.0, 5.0)), 0.0, 0.001)
	assert_almost_eq(on_closing.distance_to(Vector3(0.0, 0.0, 5.0)), 0.0, 0.001)


func test_point_along_wraps_around_laps() -> void:
	var first_lap: Vector3 = Carriage.point_along(SQUARE_ROUTE, 7.0)
	var third_lap: Vector3 = Carriage.point_along(SQUARE_ROUTE, 87.0)
	var backwards: Vector3 = Carriage.point_along(SQUARE_ROUTE, -33.0)

	assert_almost_eq(first_lap.distance_to(third_lap), 0.0, 0.001)
	assert_almost_eq(first_lap.distance_to(backwards), 0.0, 0.001)


func test_wheels_roll_with_the_distance_travelled() -> void:
	var carriage: Carriage = _build_moving_carriage()
	var wheel: MeshInstance3D = carriage.find_child("WheelL", true, false) as MeshInstance3D
	var radius: float = wheel.get_aabb().size.y / 2.0

	await wait_physics_frames(30)

	assert_almost_eq(wheel.rotation.x, fposmod(carriage.get_travelled() / radius, TAU), 0.001)
	assert_gt(wheel.rotation.x, 0.0)


func test_horse_walks_in_step_with_the_carriage() -> void:
	var carriage: Carriage = _build_moving_carriage()
	var animation_player: AnimationPlayer = (
		carriage.find_child("AnimationPlayer", true, false) as AnimationPlayer
	)

	assert_eq(animation_player.current_animation, String(Carriage.WALK_ANIMATION))
	assert_almost_eq(
		animation_player.speed_scale, carriage.speed / Carriage.HORSE_STRIDE_SPEED, 0.001
	)
	assert_eq(
		animation_player.get_animation(Carriage.WALK_ANIMATION).loop_mode, Animation.LOOP_LINEAR
	)


func _build_moving_carriage() -> Carriage:
	var carriage: Carriage = Carriage.new()

	carriage.wagon_scene = load("res://art/town/farm/farm_wagon.gltf")
	carriage.horse_scene = load("res://art/town/farm/animals/horse_harness.gltf")
	carriage.route = SQUARE_ROUTE
	add_child_autofree(carriage)

	return carriage
