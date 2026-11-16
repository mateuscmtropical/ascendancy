extends GutTest

const INWARD: Vector3 = Vector3(0.0, 0.0, -1.0)


func test_sun_outside_the_window_shines_in() -> void:
	var light_travel: Vector3 = Vector3(0.0, -0.6, -0.8)

	assert_almost_eq(SunThroughGlass.entry_strength(light_travel, INWARD), 1.0, 0.001)


func test_sun_on_the_other_side_gives_no_light() -> void:
	var light_travel: Vector3 = Vector3(0.0, -0.6, 0.8)

	assert_eq(SunThroughGlass.entry_strength(light_travel, INWARD), 0.0)


func test_grazing_sun_gives_no_light() -> void:
	var light_travel: Vector3 = Vector3(1.0, -0.2, -0.01)

	assert_eq(SunThroughGlass.entry_strength(light_travel, INWARD), 0.0)
