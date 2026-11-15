extends GutTest

const CYCLE_SECONDS: float = 1440.0
const START: float = 0.18


func test_time_of_day_wraps_every_cycle() -> void:
	var at_start: float = SkyClock.time_of_day(0.0, CYCLE_SECONDS, START)
	var one_cycle_later: float = SkyClock.time_of_day(CYCLE_SECONDS, CYCLE_SECONDS, START)
	var half_cycle_later: float = SkyClock.time_of_day(CYCLE_SECONDS / 2.0, CYCLE_SECONDS, START)

	assert_almost_eq(at_start, START, 0.0001)
	assert_almost_eq(one_cycle_later, START, 0.0001)
	assert_almost_eq(half_cycle_later, START + 0.5, 0.0001)


func test_day_and_night_last_half_a_cycle_each() -> void:
	assert_true(SkyClock.is_daytime(SkyClock.SUNRISE + 0.01))
	assert_true(SkyClock.is_daytime(SkyClock.NOON))
	assert_false(SkyClock.is_daytime(SkyClock.SUNSET + 0.01))
	assert_false(SkyClock.is_daytime(SkyClock.MIDNIGHT))


func test_sun_rises_east_peaks_south_and_sets_west() -> void:
	var sunrise: Vector3 = SkyClock.sun_direction(SkyClock.SUNRISE)
	var noon: Vector3 = SkyClock.sun_direction(SkyClock.NOON)
	var sunset: Vector3 = SkyClock.sun_direction(SkyClock.SUNSET)
	var midnight: Vector3 = SkyClock.sun_direction(SkyClock.MIDNIGHT)

	assert_almost_eq(sunrise.y, 0.0, 0.001, "sun on the horizon at sunrise")
	assert_gt(sunrise.x, 0.9, "sun rises in the east (+X)")
	assert_almost_eq(rad_to_deg(asin(noon.y)), 45.0, 0.5, "noon sun at 45 degrees")
	assert_gt(noon.z, 0.5, "noon sun to the south (+Z)")
	assert_lt(sunset.x, -0.9, "sun sets in the west (-X)")
	assert_lt(midnight.y, -0.5, "sun far below the horizon at midnight")


func test_moon_is_up_at_midnight() -> void:
	assert_gt(SkyClock.moon_direction(SkyClock.MIDNIGHT).y, 0.4)
	assert_lt(SkyClock.moon_direction(SkyClock.NOON).y, 0.0)


func test_day_index_counts_whole_cycles_from_the_first_sunrise() -> void:
	assert_eq(SkyClock.day_index(0.0, CYCLE_SECONDS, START), 0)
	assert_eq(SkyClock.day_index(CYCLE_SECONDS * 0.81, CYCLE_SECONDS, START), 0)
	assert_eq(SkyClock.day_index(CYCLE_SECONDS * 0.83, CYCLE_SECONDS, START), 1)


func test_sky_brightness_follows_the_sun() -> void:
	var noon_amount: float = DayNightCycle.day_amount_for(SkyClock.sun_height(SkyClock.NOON))
	var night_amount: float = DayNightCycle.day_amount_for(SkyClock.sun_height(SkyClock.MIDNIGHT))
	var dusk_glow: float = DayNightCycle.twilight_amount_for(0.02)
	var noon_glow: float = DayNightCycle.twilight_amount_for(0.7)

	assert_almost_eq(noon_amount, 1.0, 0.001)
	assert_almost_eq(night_amount, 0.0, 0.001)
	assert_almost_eq(dusk_glow, 1.0, 0.001)
	assert_almost_eq(noon_glow, 0.0, 0.001)


func test_lamps_light_up_only_when_dark() -> void:
	assert_almost_eq(DayNightCycle.lamp_amount_for(1.0), 0.0, 0.001)
	assert_almost_eq(DayNightCycle.lamp_amount_for(0.0), 1.0, 0.001)
