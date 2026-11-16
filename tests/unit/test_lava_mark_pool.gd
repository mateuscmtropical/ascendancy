extends GutTest

const CAPACITY: int = 4
const COOLING_SECONDS: float = 5.0


func test_new_pool_has_no_hot_marks() -> void:
	var pool: LavaMarkPool = LavaMarkPool.new(CAPACITY)

	assert_eq(pool.count_hot_marks(0.0, COOLING_SECONDS), 0)


func test_mark_cools_in_a_straight_line_and_goes_out() -> void:
	var pool: LavaMarkPool = LavaMarkPool.new(CAPACITY)
	var slot: int = pool.claim_slot(10.0)

	assert_almost_eq(pool.get_heat(slot, 10.0, COOLING_SECONDS), 1.0, 0.001, "fresh")
	assert_almost_eq(pool.get_heat(slot, 12.5, COOLING_SECONDS), 0.5, 0.001, "half way")
	assert_eq(pool.get_heat(slot, 15.0, COOLING_SECONDS), 0.0, "cold at the cooling time")
	assert_eq(pool.get_heat(slot, 60.0, COOLING_SECONDS), 0.0, "stays cold")


func test_slots_are_handed_out_in_a_ring() -> void:
	var pool: LavaMarkPool = LavaMarkPool.new(CAPACITY)
	var claimed: Array[int] = []

	for step in CAPACITY + 2:
		claimed.append(pool.claim_slot(float(step)))

	assert_eq(claimed, [0, 1, 2, 3, 0, 1], "the oldest slot is reused, never a new one")


func test_reused_slot_is_hot_again() -> void:
	var pool: LavaMarkPool = LavaMarkPool.new(1)
	var slot: int = pool.claim_slot(0.0)

	assert_eq(pool.get_heat(slot, 20.0, COOLING_SECONDS), 0.0)

	slot = pool.claim_slot(20.0)

	assert_eq(pool.get_heat(slot, 20.0, COOLING_SECONDS), 1.0)


func test_hot_marks_never_pass_the_capacity() -> void:
	var pool: LavaMarkPool = LavaMarkPool.new(CAPACITY)

	for step in CAPACITY * 3:
		pool.claim_slot(1.0)

	assert_eq(pool.count_hot_marks(1.0, COOLING_SECONDS), CAPACITY)
	assert_eq(pool.count_hot_marks(1.0 + COOLING_SECONDS, COOLING_SECONDS), 0)
