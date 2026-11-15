extends GutTest

const WORLD_SEED: int = 1
const OTHER_SEED: int = 2
const CYCLE_SECONDS: float = 1440.0
const SLOTS: int = 4000
const DAYS: int = 600
const MIN_END_HEIGHT: float = 0.13


func test_sub_seed_is_stable_and_spreads() -> void:
	var parts: Array[int] = [WORLD_SEED, SkyEvents.Layer.METEOR, 17]
	var next_parts: Array[int] = [WORLD_SEED, SkyEvents.Layer.METEOR, 18]

	assert_eq(SkyEvents.sub_seed(parts), SkyEvents.sub_seed(parts))
	assert_ne(SkyEvents.sub_seed(parts), SkyEvents.sub_seed(next_parts))
	assert_between(SkyEvents.sub_seed(parts), 0, 0xFFFFFFFF)


func test_same_seed_draws_the_same_meteors() -> void:
	var first: Array = _meteor_signature(WORLD_SEED)
	var second: Array = _meteor_signature(WORLD_SEED)
	var other: Array = _meteor_signature(OTHER_SEED)

	assert_eq(first, second)
	assert_ne(first, other)


func test_meteors_are_occasional_and_rarer_by_day() -> void:
	var night_count: int = _meteor_count(false)
	var day_count: int = _meteor_count(true)

	assert_between(night_count, int(SLOTS * 0.08), int(SLOTS * 0.3), "night: one now and then")
	assert_lt(day_count, night_count / 2, "daytime meteors are much rarer")
	assert_gt(day_count, 0, "but they do happen")


func test_meteor_showers_bring_several_at_once() -> void:
	var largest: int = 0

	for slot in SLOTS:
		largest = maxi(largest, SkyEvents.meteors_in_slot(WORLD_SEED, slot, false).size())

	assert_gte(largest, SkyEvents.SHOWER_COUNT.x, "at least one shower in a long night sky")


func test_meteors_stay_in_the_sky_and_never_fall_on_the_map() -> void:
	for meteor in _night_meteors(WORLD_SEED, SLOTS):
		assert_gt(meteor.start_direction.y, MIN_END_HEIGHT, "starts high")
		assert_gt(meteor.end_direction.y, MIN_END_HEIGHT, "ends above the horizon")


func test_forced_shower_is_a_real_shower() -> void:
	var shower: Array[SkyMeteor] = SkyEvents.meteor_shower_at(WORLD_SEED, 10.0, false)

	assert_gte(shower.size(), SkyEvents.SHOWER_COUNT.x)
	assert_true(shower.any(func(meteor: SkyMeteor) -> bool: return meteor.is_visible_at(11.0)))


func test_eclipses_are_rare_and_deterministic() -> void:
	var eclipses: Array[SkyEclipse] = _eclipses(WORLD_SEED)
	var again: Array[SkyEclipse] = _eclipses(WORLD_SEED)

	assert_between(eclipses.size(), int(DAYS * 0.03), int(DAYS * 0.12))
	assert_eq(eclipses.size(), again.size())
	assert_eq(eclipses[0].start_offset, again[0].start_offset)


func test_solar_eclipse_by_day_lunar_by_night() -> void:
	for eclipse in _eclipses(WORLD_SEED):
		var start: float = eclipse.start_offset / CYCLE_SECONDS
		var end: float = (eclipse.start_offset + eclipse.duration) / CYCLE_SECONDS
		var is_solar: bool = eclipse.kind == SkyEclipse.Kind.SOLAR

		assert_eq(SkyClock.is_daytime(start), is_solar, "starts in the right half of the day")
		assert_eq(SkyClock.is_daytime(end), is_solar, "ends in the right half of the day")
		assert_between(eclipse.duration, 60.0, 120.0, "lasts one or two minutes")


func test_eclipse_coverage_ramps_in_and_out() -> void:
	var eclipse: SkyEclipse = SkyEclipse.new(SkyEclipse.Kind.SOLAR, 100.0, 80.0)

	assert_eq(eclipse.coverage_at(99.0), 0.0)
	assert_almost_eq(eclipse.coverage_at(140.0), 1.0, 0.001)
	assert_between(eclipse.coverage_at(105.0), 0.0, 0.6)
	assert_eq(eclipse.coverage_at(181.0), 0.0)


func _meteor_signature(world_seed: int) -> Array:
	var meteors: Array[SkyMeteor] = _night_meteors(world_seed, 400)

	return meteors.map(
		func(meteor: SkyMeteor) -> Array:
			return [snappedf(meteor.start_seconds, 0.001), meteor.end_direction]
	)


func _night_meteors(world_seed: int, slot_count: int) -> Array[SkyMeteor]:
	var meteors: Array[SkyMeteor] = []

	for slot in slot_count:
		meteors.append_array(SkyEvents.meteors_in_slot(world_seed, slot, false))

	return meteors


func _meteor_count(is_daytime: bool) -> int:
	var count: int = 0

	for slot in SLOTS:
		count += SkyEvents.meteors_in_slot(WORLD_SEED, slot, is_daytime).size()

	return count


func _eclipses(world_seed: int) -> Array[SkyEclipse]:
	var eclipses: Array[SkyEclipse] = []

	for day in DAYS:
		var eclipse: SkyEclipse = SkyEvents.eclipse_of_day(world_seed, day, CYCLE_SECONDS)

		if eclipse:
			eclipses.append(eclipse)

	return eclipses
