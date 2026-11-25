class_name UnarmedFighter
extends Node
## Luta sem arma: encadeia socos e chutes em sequência, guarda o pedido feito cedo demais
## e avisa o instante em que cada golpe acerta. Não toca animação nem lê teclado: quem usa
## pede o ataque, avança o tempo e ouve os sinais.
## Andando, o soco sai só no tronco (as pernas seguem no passo) e o chute vira chute voador;
## parado, o chute prende os pés no chão até a perna voltar.

signal move_started(move: Move)
signal strike_reached(move: Move)
signal move_finished

enum Attack { PUNCH, KICK }
enum Move {
	JAB,
	CROSS,
	HOOK,
	UPPERCUT,
	FRONT_KICK,
	ROUNDHOUSE_KICK,
	SIDE_KICK,
	FLYING_FRONT_KICK,
	FLYING_ROUNDHOUSE_KICK,
	FLYING_SIDE_KICK,
}

const CHAIN_BY_ATTACK: Dictionary[Attack, Array] = {
	Attack.PUNCH: [Move.JAB, Move.CROSS, Move.HOOK, Move.UPPERCUT],
	Attack.KICK: [Move.FRONT_KICK, Move.ROUNDHOUSE_KICK, Move.SIDE_KICK],
}
## O chute de quem vem andando: o corpo todo sai do chão, então não há pé de apoio para escorregar.
const FLYING_BY_KICK: Dictionary[Move, Move] = {
	Move.FRONT_KICK: Move.FLYING_FRONT_KICK,
	Move.ROUNDHOUSE_KICK: Move.FLYING_ROUNDHOUSE_KICK,
	Move.SIDE_KICK: Move.FLYING_SIDE_KICK,
}
const ANIMATION_BY_MOVE: Dictionary[Move, StringName] = {
	Move.JAB: &"ual1/Punch_Jab",
	Move.CROSS: &"ual1/Punch_Cross",
	Move.HOOK: &"combat/Punch_Hook",
	Move.UPPERCUT: &"combat/Punch_Uppercut",
	Move.FRONT_KICK: &"combat/Kick_Front",
	Move.ROUNDHOUSE_KICK: &"combat/Kick_Roundhouse",
	Move.SIDE_KICK: &"combat/Kick_Side",
	Move.FLYING_FRONT_KICK: &"combat/Kick_Front_Flying",
	Move.FLYING_ROUNDHOUSE_KICK: &"combat/Kick_Roundhouse_Flying",
	Move.FLYING_SIDE_KICK: &"combat/Kick_Side_Flying",
}
## Os socos da biblioteca são lentos para um combo; os clipes próprios já saem no tempo certo.
const ANIMATION_SPEED_BY_MOVE: Dictionary[Move, float] = {
	Move.JAB: 1.3,
	Move.CROSS: 1.3,
}
## Tempos em segundos do clipe: quando o golpe acerta, a partir de quando o próximo golpe
## pode cortar a volta à guarda (e as pernas de um chute ficam livres para andar), e quando o
## clipe acaba.
const STRIKE_SECONDS_BY_MOVE: Dictionary[Move, float] = {
	Move.JAB: 0.21,
	Move.CROSS: 0.29,
	Move.HOOK: 0.2,
	Move.UPPERCUT: 0.23,
	Move.FRONT_KICK: 0.36,
	Move.ROUNDHOUSE_KICK: 0.35,
	Move.SIDE_KICK: 0.4,
	Move.FLYING_FRONT_KICK: 0.36,
	Move.FLYING_ROUNDHOUSE_KICK: 0.35,
	Move.FLYING_SIDE_KICK: 0.4,
}
const CHAIN_SECONDS_BY_MOVE: Dictionary[Move, float] = {
	Move.JAB: 0.36,
	Move.CROSS: 0.46,
	Move.HOOK: 0.34,
	Move.UPPERCUT: 0.38,
	Move.FRONT_KICK: 0.56,
	Move.ROUNDHOUSE_KICK: 0.6,
	Move.SIDE_KICK: 0.66,
	# O chute voador só solta as pernas com o pé de volta no chão.
	Move.FLYING_FRONT_KICK: 0.62,
	Move.FLYING_ROUNDHOUSE_KICK: 0.68,
	Move.FLYING_SIDE_KICK: 0.74,
}
const LENGTH_SECONDS_BY_MOVE: Dictionary[Move, float] = {
	Move.JAB: 0.87,
	Move.CROSS: 1.0,
	Move.HOOK: 0.62,
	Move.UPPERCUT: 0.7,
	Move.FRONT_KICK: 0.9,
	Move.ROUNDHOUSE_KICK: 1.0,
	Move.SIDE_KICK: 1.05,
	Move.FLYING_FRONT_KICK: 0.9,
	Move.FLYING_ROUNDHOUSE_KICK: 1.0,
	Move.FLYING_SIDE_KICK: 1.05,
}
## Depois do último golpe o lutador fica este tempo em guarda antes de relaxar.
const GUARD_HOLD_SECONDS: float = 3.0

## Quem usa diz se o lutador está andando; vale para o próximo golpe que começar.
var is_on_the_move: bool = false

var _is_attacking: bool = false
var _attack: Attack = Attack.PUNCH
var _move: Move = Move.JAB
var _move_seconds: float = 0.0
var _has_struck: bool = false
var _chain_step: int = 0
var _has_pending_attack: bool = false
var _pending_attack: Attack = Attack.PUNCH
var _guard_seconds_left: float = 0.0


func is_attacking() -> bool:
	return _is_attacking


## Em guarda: no meio de um golpe ou há pouco tempo do último.
func is_on_guard() -> bool:
	return _is_attacking or _guard_seconds_left > 0.0


## Chute ainda sem a perna de volta: o clipe é dono do corpo inteiro.
func is_committed() -> bool:
	var is_leg_back: bool = _move_seconds >= CHAIN_SECONDS_BY_MOVE[_move]

	return _is_attacking and _attack == Attack.KICK and not is_leg_back


## Chute dado parado, com o pé de apoio no chão: andar agora arrastaria esse pé.
func holds_feet() -> bool:
	return is_committed() and FLYING_BY_KICK.has(_move)


## Onde o golpe atual está no próprio clipe, em segundos.
func move_seconds() -> float:
	return _move_seconds


func current_move() -> Move:
	return _move


func animation_of(move: Move) -> StringName:
	return ANIMATION_BY_MOVE[move]


func animation_speed_of(move: Move) -> float:
	return ANIMATION_SPEED_BY_MOVE.get(move, 1.0)


## Pede um ataque. Parado, começa já; no meio de um golpe fica guardado e entra na sequência
## assim que o golpe atual permitir.
func request_attack(attack: Attack) -> void:
	if _is_attacking:
		_has_pending_attack = true
		_pending_attack = attack

		return

	_chain_step = 0
	_start_move(attack)


## Interrompe o golpe (pulo, queda, dano) sem passar pelos sinais de acerto.
func cancel() -> void:
	if not _is_attacking:
		return

	_is_attacking = false
	_has_pending_attack = false
	move_finished.emit()


func advance(delta: float) -> void:
	if not _is_attacking:
		_guard_seconds_left = maxf(_guard_seconds_left - delta, 0.0)

		return

	_move_seconds += delta * animation_speed_of(_move)

	if not _has_struck and _move_seconds >= STRIKE_SECONDS_BY_MOVE[_move]:
		_has_struck = true
		strike_reached.emit(_move)

	if _has_pending_attack and _move_seconds >= CHAIN_SECONDS_BY_MOVE[_move]:
		_chain_step += 1
		_start_move(_pending_attack)

		return

	if _move_seconds >= LENGTH_SECONDS_BY_MOVE[_move]:
		_is_attacking = false
		move_finished.emit()


func _start_move(attack: Attack) -> void:
	var chain: Array = CHAIN_BY_ATTACK[attack]
	var standing_move: Move = chain[_chain_step % chain.size()]

	_attack = attack
	_move = FLYING_BY_KICK.get(standing_move, standing_move) if is_on_the_move else standing_move
	_move_seconds = 0.0
	_has_struck = false
	_has_pending_attack = false
	_is_attacking = true
	_guard_seconds_left = GUARD_HOLD_SECONDS
	move_started.emit(_move)
