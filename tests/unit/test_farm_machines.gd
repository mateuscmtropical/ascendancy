extends GutTest

const ANGLE_TOLERANCE: float = 0.0001


func test_water_wheel_turns_at_the_set_speed() -> void:
	var angle: float = WaterWheel.angle_after(0.0, 6.0, 1.0)

	assert_almost_eq(angle, TAU / 10.0, ANGLE_TOLERANCE)


func test_water_wheel_angle_wraps_around() -> void:
	var angle: float = WaterWheel.angle_after(TAU - 0.1, 6.0, 1.0)

	assert_between(angle, 0.0, TAU)
	assert_almost_eq(angle, TAU / 10.0 - 0.1, ANGLE_TOLERANCE)


func test_monjolo_rests_down_and_lifts_while_filling() -> void:
	var monjolo: Monjolo = autofree(Monjolo.new())
	var early: float = monjolo.beam_angle_at(monjolo.fill_seconds * 0.25)
	var late: float = monjolo.beam_angle_at(monjolo.fill_seconds * 0.75)

	assert_almost_eq(monjolo.beam_angle_at(0.0), 0.0, ANGLE_TOLERANCE)
	assert_gt(late - early, early, "a subida acelera conforme o cocho enche")
	assert_almost_eq(
		monjolo.beam_angle_at(monjolo.fill_seconds), monjolo.lifted_angle, ANGLE_TOLERANCE
	)


func test_monjolo_falls_back_fast_and_repeats() -> void:
	var monjolo: Monjolo = autofree(Monjolo.new())
	var fall_start: float = monjolo.fill_seconds + monjolo.spill_seconds
	var landed: float = fall_start + monjolo.fall_seconds

	assert_almost_eq(monjolo.beam_angle_at(fall_start), monjolo.lifted_angle, ANGLE_TOLERANCE)
	assert_almost_eq(monjolo.beam_angle_at(landed), 0.0, ANGLE_TOLERANCE)
	assert_lt(monjolo.fall_seconds, monjolo.fill_seconds / 5.0)
	assert_almost_eq(
		monjolo.beam_angle_at(monjolo.cycle_seconds() + 1.0),
		monjolo.beam_angle_at(1.0),
		ANGLE_TOLERANCE
	)
