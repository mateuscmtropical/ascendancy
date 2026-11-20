extends GutTest

const MULA_SCENE: PackedScene = preload("res://features/mobs/mula_sem_cabeca.tscn")
const HOOF_COUNT: int = 4
const WITHERS_HEIGHT: float = 1.7
const HEIGHT_TOLERANCE: float = 0.75

var _mula: MulaSemCabeca


func before_each() -> void:
	_mula = MULA_SCENE.instantiate() as MulaSemCabeca
	add_child_autofree(_mula)


func test_every_fire_marker_gets_its_fire() -> void:
	var markers: Array[Node] = _mula.find_children(
		MulaSemCabeca.FIRE_MARKER_PATTERN, "Node3D", true, false
	)

	assert_gt(markers.size(), 0, "the model brings fire markers")

	for marker in markers:
		var flames: Array[Node] = marker.find_children("*", "GPUParticles3D", true, false)

		assert_gt(flames.size(), 0, "%s burns" % marker.name)


func test_fire_is_drawn_in_metres() -> void:
	var blazes: Array[Node] = _mula.find_children("Blaze", "GPUParticles3D", true, false)
	var blaze: GPUParticles3D = blazes[0] as GPUParticles3D

	var body_scale: Vector3 = (_mula.get_node("Model") as Node3D).scale

	assert_almost_eq(blaze.global_basis.get_scale(), body_scale, Vector3.ONE * 0.01)


func test_each_hoof_burns() -> void:
	var hoof_markers: Array[Node] = _mula.find_children("FireHoof*", "Node3D", true, false)

	assert_eq(hoof_markers.size(), HOOF_COUNT)


func test_stump_stands_above_the_withers() -> void:
	var stump: Node3D = _mula.find_child("FireStump", true, false) as Node3D
	var body_scale: float = (_mula.get_node("Model") as Node3D).scale.y

	assert_gt(stump.global_position.y, WITHERS_HEIGHT * body_scale)
	assert_lt(stump.global_position.y, (WITHERS_HEIGHT + HEIGHT_TOLERANCE) * body_scale)


func test_veins_use_the_pulsing_material() -> void:
	var veins: MeshInstance3D = _mula.find_child("MulaVeins", true, false) as MeshInstance3D

	assert_eq(veins.material_override, _mula.vein_material)


func test_flames_use_the_ribbon_material() -> void:
	var flames: MeshInstance3D = _mula.find_child("MulaFlames", true, false) as MeshInstance3D

	assert_eq(flames.material_override, _mula.flame_ribbon_material)


func test_fire_goes_out_when_the_mula_dies() -> void:
	var blazes: Array[Node] = _mula.find_children("Blaze", "GPUParticles3D", true, false)
	var blaze: GPUParticles3D = blazes[0] as GPUParticles3D

	_mula.play_animation(MulaSemCabeca.DEATH_ANIMATION)
	await wait_seconds(MulaSemCabeca.BURN_FADE_SECONDS + 0.3)

	assert_false(blaze.emitting, "the stump blaze stops")
	assert_almost_eq(_mula.get_burn(), 0.0, 0.01)


func test_fire_comes_back_with_the_next_animation() -> void:
	var blazes: Array[Node] = _mula.find_children("Blaze", "GPUParticles3D", true, false)
	var blaze: GPUParticles3D = blazes[0] as GPUParticles3D

	_mula.play_animation(MulaSemCabeca.DEATH_ANIMATION)
	_mula.play_animation(MulaSemCabeca.IDLE_ANIMATION)
	await wait_seconds(MulaSemCabeca.BURN_FADE_SECONDS + 0.3)

	assert_true(blaze.emitting, "the stump blaze burns again")
	assert_almost_eq(_mula.get_burn(), 1.0, 0.01)


func test_gaits_loop_and_strikes_do_not() -> void:
	var player: AnimationPlayer = (
		_mula.find_child("AnimationPlayer", true, false) as AnimationPlayer
	)
	var run: Animation = player.get_animation(MulaSemCabeca.RUN_ANIMATION)
	var death: Animation = player.get_animation(MulaSemCabeca.DEATH_ANIMATION)

	assert_eq(run.loop_mode, Animation.LOOP_LINEAR)
	assert_eq(death.loop_mode, Animation.LOOP_NONE)


func test_play_animation_switches_the_clip() -> void:
	var player: AnimationPlayer = (
		_mula.find_child("AnimationPlayer", true, false) as AnimationPlayer
	)

	_mula.play_animation(MulaSemCabeca.ATTACK_ANIMATION)

	assert_eq(player.current_animation, String(MulaSemCabeca.ATTACK_ANIMATION))


func test_animation_steps_every_frame_up_close() -> void:
	assert_eq(MulaSemCabeca.animation_step_for(10.0, true), 0.0)


func test_animation_steps_sparser_far_away() -> void:
	var middle_step: float = MulaSemCabeca.animation_step_for(45.0, true)
	var far_step: float = MulaSemCabeca.animation_step_for(150.0, true)

	assert_gt(middle_step, 0.0)
	assert_gt(far_step, middle_step)
	assert_lt(far_step, INF)


func test_animation_stops_off_screen() -> void:
	assert_eq(MulaSemCabeca.animation_step_for(10.0, false), INF)


func test_fire_shows_only_near_and_on_screen() -> void:
	assert_true(MulaSemCabeca.should_show_fire(40.0, true))
	assert_false(MulaSemCabeca.should_show_fire(MulaSemCabeca.FIRE_DETAIL_DISTANCE + 1.0, true))
	assert_false(MulaSemCabeca.should_show_fire(40.0, false))
