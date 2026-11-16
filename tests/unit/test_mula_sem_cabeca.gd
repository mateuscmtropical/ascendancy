extends GutTest

const MULA_SCENE: PackedScene = preload("res://features/mobs/mula_sem_cabeca.tscn")
const HOOF_COUNT: int = 4
const WITHERS_HEIGHT: float = 1.7
const HEIGHT_TOLERANCE: float = 0.35

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

	assert_almost_eq(blaze.global_basis.get_scale(), Vector3.ONE, Vector3.ONE * 0.01)


func test_each_hoof_burns() -> void:
	var hoof_markers: Array[Node] = _mula.find_children("FireHoof*", "Node3D", true, false)

	assert_eq(hoof_markers.size(), HOOF_COUNT)


func test_stump_stands_above_the_withers() -> void:
	var stump: Node3D = _mula.find_child("FireStump", true, false) as Node3D

	assert_gt(stump.global_position.y, WITHERS_HEIGHT)
	assert_lt(stump.global_position.y, WITHERS_HEIGHT + HEIGHT_TOLERANCE)


func test_veins_use_the_pulsing_material() -> void:
	var veins: MeshInstance3D = _mula.find_child("MulaVeins", true, false) as MeshInstance3D

	assert_eq(veins.material_override, _mula.vein_material)


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
