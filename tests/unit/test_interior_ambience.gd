extends GutTest

var _day_night: DayNightCycle
var _probe: ReflectionProbe


func before_each() -> void:
	var world_environment: WorldEnvironment = WorldEnvironment.new()

	world_environment.environment = Environment.new()
	_probe = ReflectionProbe.new()
	_probe.add_to_group(DayNightCycle.INTERIOR_AMBIENCE_GROUP)
	_day_night = DayNightCycle.new()
	_day_night.world_environment = world_environment
	_day_night.time_scale = 0.0

	add_child_autofree(world_environment)
	add_child_autofree(_probe)
	add_child_autofree(_day_night)


func test_interior_probe_stays_off_in_daylight() -> void:
	_day_night.set_time_of_day(0.25)

	assert_false(_probe.visible)


func test_interior_probe_lights_the_hall_at_midnight() -> void:
	_day_night.set_time_of_day(0.75)

	assert_true(_probe.visible)
	assert_true(_probe.ambient_color.is_equal_approx(DayNightCycle.INTERIOR_NIGHT_AMBIENT))
	assert_almost_eq(
		_probe.ambient_color_energy, DayNightCycle.INTERIOR_NIGHT_AMBIENT_ENERGY, 0.001
	)
