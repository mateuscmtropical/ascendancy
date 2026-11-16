class_name SkyMeteor
extends RefCounted
## Uma estrela cadente: risca o céu de `start_direction` a `end_direction` (direções unitárias a
## partir do observador, sempre acima do horizonte) entre `start_seconds` e o fim da duração.

## Fração do caminho que a cauda ocupa atrás da cabeça.
const TAIL_SHARE: float = 0.45

var start_seconds: float = 0.0
var duration: float = 1.0
var start_direction: Vector3 = Vector3.UP
var end_direction: Vector3 = Vector3.UP
var brightness: float = 1.0


func _init(
	start: float, seconds: float, from_direction: Vector3, to_direction: Vector3, glow: float
) -> void:
	start_seconds = start
	duration = seconds
	start_direction = from_direction
	end_direction = to_direction
	brightness = glow


## Progresso em [0, 1] no instante; fora disso a estrela não está no céu.
func progress_at(game_seconds: float) -> float:
	return (game_seconds - start_seconds) / duration


func is_visible_at(game_seconds: float) -> bool:
	var progress: float = progress_at(game_seconds)

	return progress >= 0.0 and progress <= 1.0


func head_at(game_seconds: float) -> Vector3:
	var progress: float = clampf(progress_at(game_seconds), 0.0, 1.0)

	return start_direction.slerp(end_direction, progress)


func tail_at(game_seconds: float) -> Vector3:
	var progress: float = clampf(progress_at(game_seconds) - TAIL_SHARE, 0.0, 1.0)

	return start_direction.slerp(end_direction, progress)


## Acende rápido, apaga no fim do risco.
func glow_at(game_seconds: float) -> float:
	var progress: float = progress_at(game_seconds)

	return brightness * smoothstep(0.0, 0.12, progress) * (1.0 - smoothstep(0.7, 1.0, progress))
