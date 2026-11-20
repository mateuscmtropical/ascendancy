extends GutTest

const CAMERA_INSIDE: Vector3 = Vector3(0.0, -2.0, 0.0)
const CAMERA_OUTSIDE: Vector3 = Vector3(0.0, 1.6, 0.0)

var _cycle: DayNightCycle
var _sun: DirectionalLight3D
var _camera: Camera3D


func before_each() -> void:
	var zone: SunlessZone = SunlessZone.new()

	_sun = DirectionalLight3D.new()
	_camera = Camera3D.new()
	_cycle = DayNightCycle.new()
	_cycle.sun = _sun
	_cycle.time_scale = 0.0
	_cycle.start_time_of_day = 0.25
	zone.box = AABB(Vector3(-5.0, -5.0, -5.0), Vector3(10.0, 4.5, 10.0))
	add_child_autofree(zone)
	add_child_autofree(_sun)
	add_child_autofree(_camera)
	_camera.make_current()
	add_child_autofree(_cycle)


func test_sun_shines_with_the_camera_above_ground() -> void:
	_camera.global_position = CAMERA_OUTSIDE
	_cycle.apply_sky()

	assert_true(_sun.visible)


func test_sun_goes_out_with_the_camera_in_the_crypt() -> void:
	_camera.global_position = CAMERA_INSIDE
	_cycle.apply_sky()

	assert_false(_sun.visible)
