extends GutTest

const MODEL_SCENE: PackedScene = preload("res://features/player/character_model.tscn")
const BODY_SCENES: Array[PackedScene] = [
	preload("res://art/characters/adventurer_male.gltf"),
	preload("res://art/characters/adventurer_female.gltf"),
	preload("res://art/characters/villager_male.gltf"),
	preload("res://art/characters/villager_female.gltf"),
]
const FACE_SHAPES: Array[StringName] = [
	&"blink_l",
	&"blink_r",
	&"squint",
	&"eyes_wide",
	&"brow_up",
	&"brow_angry",
	&"brow_sad",
	&"smile",
	&"frown",
	&"mouth_open",
	&"look_left",
	&"look_right",
	&"look_up",
	&"look_down",
]
const STEP_SECONDS: float = 1.0 / 60.0

var _face: FaceAnimator


func before_each() -> void:
	_face = _spawn_face(BODY_SCENES[0])


func test_every_character_has_every_face_shape() -> void:
	for body_scene in BODY_SCENES:
		var face: FaceAnimator = _spawn_face(body_scene)

		_assert_face_has_all_shapes(face, body_scene.resource_path)


func test_blink_closes_both_eyes_then_opens_them() -> void:
	_face.blink_now()
	_advance(FaceAnimator.BLINK_CLOSE_SECONDS)

	assert_gt(_face.weight_of(&"blink_l"), 0.9, "left eye closed at the end of the closing time")
	assert_gt(_face.weight_of(&"blink_r"), 0.9, "right eye closed at the end of the closing time")

	_advance(FaceAnimator.BLINK_OPEN_SECONDS + 2.0 * STEP_SECONDS)

	assert_lt(_face.weight_of(&"blink_l"), 0.05, "eye open again")


func test_face_blinks_by_itself() -> void:
	var blink_peak: float = 0.0

	for step in int(2.0 * FaceAnimator.BLINK_PAUSE_MAX_SECONDS / STEP_SECONDS):
		_face.advance(STEP_SECONDS)
		blink_peak = maxf(blink_peak, _face.weight_of(&"blink_l"))

	assert_gt(blink_peak, 0.9, "a blink happened within two of the longest pauses")


func test_expression_blends_in_and_passing_one_returns_to_rest() -> void:
	_face.show_expression(FaceAnimator.Mood.HAPPY, 0.5)
	_advance(STEP_SECONDS)

	assert_between(_face.weight_of(&"smile"), 0.01, 0.5, "smile is blended in, not snapped")

	_advance(FaceAnimator.EXPRESSION_BLEND_SECONDS)

	assert_almost_eq(_face.weight_of(&"smile"), 1.0, 0.01, "smile reached")

	_advance(0.5 + 2.0 * FaceAnimator.EXPRESSION_BLEND_SECONDS)

	assert_almost_eq(_face.weight_of(&"smile"), 0.0, 0.01, "back to the resting face")


func test_talking_moves_the_mouth_and_silence_closes_it() -> void:
	var widest_mouth: float = 0.0

	_face.is_talking = true

	for step in ceili(1.0 / STEP_SECONDS):
		_face.advance(STEP_SECONDS)
		widest_mouth = maxf(widest_mouth, _face.weight_of(&"mouth_open"))

	assert_gt(widest_mouth, 0.1, "the mouth opened while talking")

	_face.is_talking = false
	_advance(2.0 * FaceAnimator.EXPRESSION_BLEND_SECONDS)

	assert_almost_eq(_face.weight_of(&"mouth_open"), 0.0, 0.01, "closed again in silence")


func test_weights_reach_the_meshes() -> void:
	var head: MeshInstance3D = _face.get_parent().get_node("Body/Armature/Skeleton3D/Head_Skin")
	var smile_index: int = head.find_blend_shape_by_name(&"smile")

	_face.show_expression(FaceAnimator.Mood.HAPPY)
	_advance(2.0 * FaceAnimator.EXPRESSION_BLEND_SECONDS)

	assert_almost_eq(head.get_blend_shape_value(smile_index), 1.0, 0.01)


func test_far_face_rests_neutral_and_stops() -> void:
	var head: MeshInstance3D = _face.get_parent().get_node("Body/Armature/Skeleton3D/Head_Skin")
	var smile_index: int = head.find_blend_shape_by_name(&"smile")

	_face.show_expression(FaceAnimator.Mood.HAPPY)
	_advance(2.0 * FaceAnimator.EXPRESSION_BLEND_SECONDS)
	_face.set_detailed(false)

	assert_false(_face.is_processing(), "far face stops animating")
	assert_eq(head.get_blend_shape_value(smile_index), 0.0, "far face back to neutral")

	_face.set_detailed(true)

	assert_true(_face.is_processing(), "near face animates again")


func _spawn_face(body_scene: PackedScene) -> FaceAnimator:
	var model: CharacterModel = MODEL_SCENE.instantiate()

	model.body_scene = body_scene
	add_child_autofree(model)

	return model.get_node("FaceAnimator")


func _assert_face_has_all_shapes(face: FaceAnimator, label: String) -> void:
	for shape_name in FACE_SHAPES:
		assert_true(face.has_shape(shape_name), "%s has %s" % [label, shape_name])


func _advance(seconds: float) -> void:
	for step in ceili(seconds / STEP_SECONDS):
		_face.advance(STEP_SECONDS)
