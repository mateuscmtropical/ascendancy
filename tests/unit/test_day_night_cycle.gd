extends GutTest

const SUN: Vector3 = Vector3(0.0, 0.7071, 0.7071)
const AMOUNTS: Vector4 = Vector4(1.0, 0.0, 0.0, 0.0)


func test_first_sky_state_is_always_sent() -> void:
	assert_true(DayNightCycle.is_sky_change_visible(Vector3.ZERO, SUN, -Vector4.ONE, AMOUNTS))


func test_tiny_sun_motion_does_not_refresh_the_sky() -> void:
	var nudged: Vector3 = SUN.rotated(Vector3.RIGHT, DayNightCycle.SKY_REFRESH_ANGLE * 0.5)

	assert_false(DayNightCycle.is_sky_change_visible(SUN, nudged, AMOUNTS, AMOUNTS))


func test_visible_sun_motion_refreshes_the_sky() -> void:
	var moved: Vector3 = SUN.rotated(Vector3.RIGHT, DayNightCycle.SKY_REFRESH_ANGLE * 2.0)

	assert_true(DayNightCycle.is_sky_change_visible(SUN, moved, AMOUNTS, AMOUNTS))


func test_eclipse_start_refreshes_the_sky() -> void:
	var eclipsed: Vector4 = AMOUNTS + Vector4(0.0, 0.0, DayNightCycle.SKY_REFRESH_AMOUNT * 2.0, 0.0)

	assert_true(DayNightCycle.is_sky_change_visible(SUN, SUN, AMOUNTS, eclipsed))
