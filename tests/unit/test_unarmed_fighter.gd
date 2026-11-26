extends GutTest

const PLAYER_SCENE: PackedScene = preload("res://features/player/player.tscn")
const MODEL_SCENE: PackedScene = preload("res://features/player/character_model.tscn")
const STEP_SECONDS: float = 1.0 / 60.0

var _fighter: UnarmedFighter
var _started_moves: Array[UnarmedFighter.Move] = []
var _struck_moves: Array[UnarmedFighter.Move] = []


func before_each() -> void:
	_started_moves.clear()
	_struck_moves.clear()
	_fighter = UnarmedFighter.new()
	_fighter.move_started.connect(_started_moves.append)
	_fighter.strike_reached.connect(_struck_moves.append)
	add_child_autofree(_fighter)


func test_single_punch_strikes_once_and_returns_to_guard() -> void:
	_fighter.request_attack(UnarmedFighter.Attack.PUNCH)

	assert_true(_fighter.is_attacking())

	_advance(1.0)

	assert_eq(_started_moves, [UnarmedFighter.Move.JAB])
	assert_eq(_struck_moves, [UnarmedFighter.Move.JAB])
	assert_false(_fighter.is_attacking(), "jab over within a second")
	assert_true(_fighter.is_on_guard(), "still on guard right after the blow")

	_advance(UnarmedFighter.GUARD_HOLD_SECONDS)

	assert_false(_fighter.is_on_guard(), "relaxed after the guard time")


func test_swing_sounds_once_per_blow_just_before_it_lands() -> void:
	var swung_attacks: Array[UnarmedFighter.Attack] = []
	var jab_strike: float = UnarmedFighter.STRIKE_SECONDS_BY_MOVE[UnarmedFighter.Move.JAB]

	_fighter.swing_started.connect(swung_attacks.append)
	_fighter.request_attack(UnarmedFighter.Attack.PUNCH)
	_advance((jab_strike - UnarmedFighter.SWING_LEAD_SECONDS) / 1.3 - 0.03)

	assert_eq(swung_attacks.size(), 0, "silent while the fist is still loading")

	_advance(0.05)

	assert_eq(swung_attacks, [UnarmedFighter.Attack.PUNCH])
	assert_eq(_struck_moves.size(), 0, "the air sounds before the blow lands")

	_advance(1.0)
	_fighter.request_attack(UnarmedFighter.Attack.KICK)
	_advance(1.2)

	assert_eq(swung_attacks, [UnarmedFighter.Attack.PUNCH, UnarmedFighter.Attack.KICK])


func test_player_swing_is_heard_when_punching() -> void:
	var player: PlayerController = _spawn_player()
	var swings: AudioStreamPlayer3D = player.get_node("Swings")

	await wait_physics_frames(10)
	_press(&"attack_punch")
	await wait_physics_frames(10)

	assert_eq(swings.stream, PlayerController.SWING_SOUND_BY_ATTACK[UnarmedFighter.Attack.PUNCH])
	assert_true(swings.playing, "the punch cuts the air")


func test_punches_asked_early_chain_through_the_combo() -> void:
	_fighter.request_attack(UnarmedFighter.Attack.PUNCH)

	for blow in 3:
		_advance(0.1)
		_fighter.request_attack(UnarmedFighter.Attack.PUNCH)
		_advance(0.5)

	assert_eq(
		_started_moves,
		[
			UnarmedFighter.Move.JAB,
			UnarmedFighter.Move.CROSS,
			UnarmedFighter.Move.HOOK,
			UnarmedFighter.Move.UPPERCUT,
		]
	)


func test_chained_blow_waits_for_the_strike_of_the_current_one() -> void:
	_fighter.request_attack(UnarmedFighter.Attack.KICK)
	_fighter.request_attack(UnarmedFighter.Attack.KICK)
	_advance(UnarmedFighter.STRIKE_SECONDS_BY_MOVE[UnarmedFighter.Move.FRONT_KICK] - 0.05)

	assert_eq(_started_moves.size(), 1, "second kick still waiting")

	_advance(0.4)

	assert_eq(_struck_moves, [UnarmedFighter.Move.FRONT_KICK], "first kick landed before the cut")
	assert_eq(_started_moves.back(), UnarmedFighter.Move.ROUNDHOUSE_KICK)


func test_combo_restarts_after_a_pause() -> void:
	_fighter.request_attack(UnarmedFighter.Attack.PUNCH)
	_advance(0.1)
	_fighter.request_attack(UnarmedFighter.Attack.KICK)
	_advance(2.0)
	_fighter.request_attack(UnarmedFighter.Attack.KICK)

	assert_eq(
		_started_moves,
		[
			UnarmedFighter.Move.JAB,
			UnarmedFighter.Move.ROUNDHOUSE_KICK,
			UnarmedFighter.Move.FRONT_KICK,
		]
	)


func test_every_move_has_its_clip_and_timings_in_order() -> void:
	var model: CharacterModel = MODEL_SCENE.instantiate()
	var animation_player: AnimationPlayer

	add_child_autofree(model)
	animation_player = model.get_node("AnimationPlayer")

	for move: UnarmedFighter.Move in UnarmedFighter.Move.values():
		_assert_move_is_playable(move, animation_player)


func test_kick_on_the_move_is_a_flying_kick_that_never_holds_the_feet() -> void:
	_fighter.is_on_the_move = true
	_fighter.request_attack(UnarmedFighter.Attack.KICK)

	assert_eq(_started_moves, [UnarmedFighter.Move.FLYING_FRONT_KICK])
	assert_true(_fighter.is_committed(), "the kick owns the whole body")
	assert_false(_fighter.holds_feet(), "but the body keeps travelling")

	_advance(UnarmedFighter.CHAIN_SECONDS_BY_MOVE[UnarmedFighter.Move.FLYING_FRONT_KICK])

	assert_false(_fighter.is_committed(), "legs free once the foot is back down")
	assert_eq(_struck_moves, [UnarmedFighter.Move.FLYING_FRONT_KICK])


func test_standing_kick_holds_the_feet_until_the_leg_is_back() -> void:
	_fighter.request_attack(UnarmedFighter.Attack.KICK)

	assert_true(_fighter.holds_feet())

	_advance(UnarmedFighter.CHAIN_SECONDS_BY_MOVE[UnarmedFighter.Move.FRONT_KICK])

	assert_false(_fighter.holds_feet())
	assert_true(_fighter.is_attacking(), "still coming back to the guard")


func test_punch_never_commits_the_legs() -> void:
	_fighter.request_attack(UnarmedFighter.Attack.PUNCH)

	assert_false(_fighter.is_committed())
	assert_false(_fighter.holds_feet())


func test_standing_punch_plays_the_jab_on_the_whole_body() -> void:
	var player: PlayerController = _spawn_player()
	var animation_player: AnimationPlayer = player.get_node("CharacterModel/AnimationPlayer")

	await wait_physics_frames(10)
	_press(&"attack_punch")
	await wait_physics_frames(12)

	assert_eq(String(animation_player.current_animation), "ual1/Punch_Jab")

	await wait_physics_frames(60)

	assert_eq(
		String(animation_player.current_animation), "combat/Fight_Idle", "guard after the blow"
	)


func test_punch_on_the_move_keeps_the_step_and_throws_with_the_trunk() -> void:
	var player: PlayerController = _spawn_player()
	var animation_player: AnimationPlayer = player.get_node("CharacterModel/AnimationPlayer")
	var fighter: UnarmedFighter = player.get_node("UnarmedFighter")
	var skeleton: Skeleton3D = player.get_node("CharacterModel/Body/Armature/Skeleton3D")
	var hand: BoneAttachment3D = _attach_to_bone(skeleton, "hand_l")
	var chest: BoneAttachment3D = _attach_to_bone(skeleton, "spine_03")
	var start: Vector3
	var jog_reach: float
	var punch_reach: float

	Input.action_press(&"move_forward")
	await wait_physics_frames(40)
	jog_reach = hand.global_position.distance_to(chest.global_position)
	start = player.global_position
	_press(&"attack_punch")
	await wait_physics_frames(13)
	punch_reach = hand.global_position.distance_to(chest.global_position)

	assert_true(fighter.is_attacking())
	assert_eq(String(animation_player.current_animation), "combat/Run", "legs keep the step")
	assert_gt(player.global_position.distance_to(start), 0.9, "the blow does not brake the run")
	assert_gt(punch_reach, jog_reach + 0.15, "the jab reaches out over the jog")

	Input.action_release(&"move_forward")
	await wait_physics_frames(3)

	assert_eq(
		String(animation_player.current_animation),
		"ual1/Punch_Jab",
		"stopping mid-blow hands the whole body to the clip"
	)
	assert_gt(animation_player.current_animation_position, 0.2, "from where the blow already is")


func test_kick_on_the_move_flies_and_then_hands_the_legs_back() -> void:
	var player: PlayerController = _spawn_player()
	var animation_player: AnimationPlayer = player.get_node("CharacterModel/AnimationPlayer")
	var start: Vector3

	Input.action_press(&"move_forward")
	await wait_physics_frames(40)
	start = player.global_position
	_press(&"attack_kick")
	await wait_physics_frames(20)

	assert_eq(String(animation_player.current_animation), "combat/Kick_Front_Flying")
	assert_gt(player.global_position.distance_to(start), 1.4, "the kick travels with the run")

	await wait_physics_frames(25)

	assert_eq(String(animation_player.current_animation), "combat/Run", "back to the step")
	Input.action_release(&"move_forward")


func test_standing_kick_holds_the_step_until_the_leg_is_back() -> void:
	var player: PlayerController = _spawn_player()
	var start: Vector3

	await wait_physics_frames(10)
	start = player.global_position
	_press(&"attack_kick")
	await wait_physics_frames(3)
	Input.action_press(&"move_forward")
	await wait_physics_frames(22)

	assert_lt(player.global_position.distance_to(start), 0.05, "support foot stays planted")

	await wait_physics_frames(40)
	Input.action_release(&"move_forward")

	assert_gt(player.global_position.distance_to(start), 1.0, "free to walk after the kick")


func test_player_jump_cancels_the_blow() -> void:
	var player: PlayerController = _spawn_player()
	var fighter: UnarmedFighter = player.get_node("UnarmedFighter")

	await wait_physics_frames(10)
	_press(&"attack_kick")
	await wait_physics_frames(6)

	assert_true(fighter.is_attacking())

	Input.action_press(&"jump")
	await wait_physics_frames(3)
	Input.action_release(&"jump")

	assert_false(fighter.is_attacking())


## Segue o osso já com a camada do tronco aplicada (a pose lida direto do esqueleto é a de
## antes dos modificadores).
func _attach_to_bone(skeleton: Skeleton3D, bone_name: String) -> BoneAttachment3D:
	var attachment: BoneAttachment3D = BoneAttachment3D.new()

	attachment.bone_name = bone_name
	skeleton.add_child(attachment)

	return attachment


func _advance(seconds: float) -> void:
	for step in ceili(seconds / STEP_SECONDS):
		_fighter.advance(STEP_SECONDS)


func _assert_move_is_playable(move: UnarmedFighter.Move, animation_player: AnimationPlayer) -> void:
	var animation_name: StringName = UnarmedFighter.ANIMATION_BY_MOVE[move]
	var strike: float = UnarmedFighter.STRIKE_SECONDS_BY_MOVE[move]
	var chain: float = UnarmedFighter.CHAIN_SECONDS_BY_MOVE[move]
	var length: float = UnarmedFighter.LENGTH_SECONDS_BY_MOVE[move]

	assert_true(animation_player.has_animation(animation_name), "%s exists" % animation_name)
	assert_true(
		strike < chain and chain < length, "%s: strike, then chain, then end" % animation_name
	)

	if animation_player.has_animation(animation_name):
		assert_almost_eq(animation_player.get_animation(animation_name).length, length, 0.05)


func _spawn_player() -> PlayerController:
	var floor_body: StaticBody3D = StaticBody3D.new()
	var floor_shape: CollisionShape3D = CollisionShape3D.new()
	var player: PlayerController = PLAYER_SCENE.instantiate()

	floor_shape.shape = WorldBoundaryShape3D.new()
	floor_body.add_child(floor_shape)
	add_child_autofree(floor_body)
	add_child_autofree(player)

	return player


func _press(action: StringName) -> void:
	var event: InputEventAction = InputEventAction.new()

	event.action = action
	event.pressed = true
	Input.parse_input_event(event)
