class_name BodySway
extends RefCounted
## Peso do corpo por cima das animações: inclina para onde acelera (arranca para a frente, freia
## para trás, deita na curva) e amassa no pouso, estica no pulo. Molas com pouca folga, para o
## corpo passar um tanto do ponto e assentar em vez de parar seco. Só enfeite: não mexe na física.

## Inclinação (rad) com o corpo na aceleração cheia do chão.
const MAX_LEAN: float = 0.17
const LEAN_STIFFNESS: float = 320.0
const LEAN_DAMPING: float = 18.0
const STRETCH_STIFFNESS: float = 900.0
const STRETCH_DAMPING: float = 26.0
## Empurrão na mola da altura (por segundo): pulo estica ~4%, pouso de pulo cheio amassa ~7%.
const JUMP_STRETCH_KICK: float = 3.0
const LAND_SQUASH_KICK: float = 5.6
## Queda mais lenta que a primeira (degrau, meio-fio) não amassa; da segunda em diante amassa tudo.
const SOFT_LANDING_SPEED: float = 2.5
const HARD_LANDING_SPEED: float = 8.0
## Quadro mais longo que isto (engasgo) avança as molas só este tanto, senão elas estouram.
const MAX_STEP_SECONDS: float = 1.0 / 30.0

## x = para a frente, y = para a esquerda do corpo, em rad.
var lean: Vector2 = Vector2.ZERO
## Quanto a altura do corpo passa de 1 (negativo = amassado).
var stretch: float = 0.0

var _lean_velocity: Vector2 = Vector2.ZERO
var _stretch_velocity: float = 0.0


## local_acceleration: aceleração horizontal no espaço do corpo (x = esquerda, y = frente), como
## fração da aceleração cheia do chão.
func advance(local_acceleration: Vector2, delta: float) -> void:
	var step: float = minf(delta, MAX_STEP_SECONDS)
	var lean_target: Vector2 = (
		Vector2(local_acceleration.y, local_acceleration.x).limit_length(1.0) * MAX_LEAN
	)
	var lean_pull: Vector2 = (lean_target - lean) * LEAN_STIFFNESS - _lean_velocity * LEAN_DAMPING
	var stretch_pull: float = -stretch * STRETCH_STIFFNESS - _stretch_velocity * STRETCH_DAMPING

	_lean_velocity += lean_pull * step
	lean += _lean_velocity * step
	_stretch_velocity += stretch_pull * step
	stretch += _stretch_velocity * step


func push_off() -> void:
	_stretch_velocity += JUMP_STRETCH_KICK


func land(fall_speed: float) -> void:
	var impact: float = inverse_lerp(SOFT_LANDING_SPEED, HARD_LANDING_SPEED, fall_speed)

	_stretch_velocity -= LAND_SQUASH_KICK * clampf(impact, 0.0, 1.0)


func reset() -> void:
	lean = Vector2.ZERO
	stretch = 0.0
	_lean_velocity = Vector2.ZERO
	_stretch_velocity = 0.0
