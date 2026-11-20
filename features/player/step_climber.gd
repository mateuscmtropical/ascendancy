class_name StepClimber
extends RefCounted
## Degrau que um CharacterBody3D sobe andando, sem pular: meio-fio, soleira, borda do terreiro.

const STEP_HEIGHT: float = 0.2
## Abaixo disto a normal do obstáculo é parede (degrau); acima, rampa que o move_and_slide já sobe.
const STEP_WALL_MAX_NORMAL_Y: float = 0.7


## Quanto o corpo tem de subir para o topo do degrau à frente, se o deslocamento horizontal motion
## bate numa parede baixa (até step_height) com chão firme em cima; 0 se não há degrau.
static func step_top_ahead(
	body: CharacterBody3D, motion: Vector3, step_height: float = STEP_HEIGHT
) -> float:
	var blocking_hit: KinematicCollision3D = KinematicCollision3D.new()
	var landing_hit: KinematicCollision3D = KinematicCollision3D.new()
	var lift: Vector3 = Vector3.UP * step_height
	var standing: Transform3D = body.global_transform
	var raised: Transform3D = standing.translated(lift)
	var is_blocked_by_wall: bool = (
		motion.length_squared() > 0.000001
		and body.test_move(standing, motion, blocking_hit)
		and blocking_hit.get_normal().y <= STEP_WALL_MAX_NORMAL_Y
	)
	var is_clear_above: bool = (
		is_blocked_by_wall
		and not body.test_move(standing, lift)
		and not body.test_move(raised, motion)
	)
	var has_firm_landing: bool = (
		is_clear_above
		and body.test_move(raised.translated(motion), -lift, landing_hit)
		and landing_hit.get_normal().y >= cos(body.floor_max_angle)
	)

	if not has_firm_landing:
		return 0.0

	return step_height - landing_hit.get_travel().length()
