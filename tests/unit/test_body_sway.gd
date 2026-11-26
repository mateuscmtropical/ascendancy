extends GutTest

const STEP_SECONDS: float = 1.0 / 60.0
const FORWARD: Vector2 = Vector2(0.0, 1.0)
const LEFT: Vector2 = Vector2(1.0, 0.0)

var _sway: BodySway


func before_each() -> void:
	_sway = BodySway.new()


func test_speeding_up_leans_forward_and_cruising_stands_back_up() -> void:
	_advance(FORWARD, 0.25)

	assert_gt(_sway.lean.x, 0.05, "leans into the start")
	assert_almost_eq(_sway.lean.y, 0.0, 0.001, "no side lean on a straight line")

	_advance(Vector2.ZERO, 1.5)

	assert_almost_eq(_sway.lean.x, 0.0, 0.003, "upright again at steady speed")


func test_braking_leans_back_and_settles_past_upright() -> void:
	var furthest_forward: float

	_advance(-FORWARD, 0.25)

	assert_lt(_sway.lean.x, -0.05, "leans back against the brake")

	furthest_forward = _advance(Vector2.ZERO, 1.5)

	assert_gt(furthest_forward, 0.002, "swings a little past upright before settling")
	assert_lt(furthest_forward, BodySway.MAX_LEAN * 0.4, "but only a little")


func test_swerving_left_leans_left() -> void:
	_advance(LEFT, 0.25)

	assert_gt(_sway.lean.y, 0.05)


func test_lean_never_passes_much_beyond_the_limit() -> void:
	_advance(Vector2(40.0, 40.0), 1.0)

	assert_lt(_sway.lean.length(), BodySway.MAX_LEAN * 1.3)


func test_landing_from_a_jump_squashes_then_stands_tall_again() -> void:
	var deepest: float = 0.0

	_sway.land(BodySway.HARD_LANDING_SPEED)

	for step in 60:
		_sway.advance(Vector2.ZERO, STEP_SECONDS)
		deepest = minf(deepest, _sway.stretch)

	assert_between(deepest, -0.12, -0.05, "a visible squash, not a pancake")
	assert_almost_eq(_sway.stretch, 0.0, 0.003, "back to full height within a second")


func test_stepping_off_a_kerb_does_not_squash() -> void:
	_sway.land(BodySway.SOFT_LANDING_SPEED)
	_advance(Vector2.ZERO, 0.2)

	assert_almost_eq(_sway.stretch, 0.0, 0.0001)


func test_jumping_stretches_the_body() -> void:
	var tallest: float = 0.0

	_sway.push_off()

	for step in 30:
		_sway.advance(Vector2.ZERO, STEP_SECONDS)
		tallest = maxf(tallest, _sway.stretch)

	assert_between(tallest, 0.02, 0.08)


func test_a_long_frame_does_not_blow_the_springs_up() -> void:
	_sway.land(BodySway.HARD_LANDING_SPEED)

	for step in 20:
		_sway.advance(FORWARD, 0.5)

	assert_lt(absf(_sway.stretch), 0.2)
	assert_lt(_sway.lean.length(), BodySway.MAX_LEAN * 1.5)


func test_reset_stands_the_body_straight() -> void:
	_sway.land(BodySway.HARD_LANDING_SPEED)
	_advance(FORWARD, 0.1)
	_sway.reset()
	_advance(Vector2.ZERO, 0.1)

	assert_eq(_sway.lean, Vector2.ZERO)
	assert_eq(_sway.stretch, 0.0)


## Avança as molas e devolve o ponto mais para a frente a que a inclinação chegou.
func _advance(local_acceleration: Vector2, seconds: float) -> float:
	var furthest_forward: float = -INF

	for step in ceili(seconds / STEP_SECONDS):
		_sway.advance(local_acceleration, STEP_SECONDS)
		furthest_forward = maxf(furthest_forward, _sway.lean.x)

	return furthest_forward
