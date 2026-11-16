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
