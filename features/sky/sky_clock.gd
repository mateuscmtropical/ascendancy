class_name SkyClock
extends RefCounted
## Relógio do céu: converte o tempo de jogo (segundos desde o início do mundo) em hora do dia,
## dia corrente e direções do sol e da lua. Funções puras: o servidor e os clientes calculam o
## mesmo céu a partir do mesmo tempo.
##
## Hora do dia em [0, 1): 0 = nascer do sol, 0,25 = meio-dia, 0,5 = pôr do sol, 0,75 = meia-noite.
## O dia claro e a noite duram cada um metade do ciclo.

const SUNRISE: float = 0.0
const NOON: float = 0.25
const SUNSET: float = 0.5
const MIDNIGHT: float = 0.75
## Inclinação do caminho do sol: ao meio-dia ele fica a 90° - 45° = 45° de altura, ao sul (+Z).
const PATH_TILT_DEGREES: float = 45.0
## A lua anda a meia volta do sol, um pouco fora do plano dele para não nascer junto do pôr do sol.
const MOON_LAG: float = 0.5
const MOON_TILT_DEGREES: float = 35.0


## Hora do dia em [0, 1) para um ciclo de `cycle_seconds` que começou em `start_time_of_day`.
static func time_of_day(
	game_seconds: float, cycle_seconds: float, start_time_of_day: float
) -> float:
	return fposmod(start_time_of_day + game_seconds / cycle_seconds, 1.0)


## Número do dia (0, 1, 2...) do instante; o primeiro dia começa no nascer do sol antes do início.
static func day_index(game_seconds: float, cycle_seconds: float, start_time_of_day: float) -> int:
	return floori(start_time_of_day + game_seconds / cycle_seconds)


static func is_daytime(day_time: float) -> bool:
	return fposmod(day_time, 1.0) < SUNSET


## Direção que aponta para o sol: nasce a leste (+X), passa ao sul (+Z) e se põe a oeste (-X).
static func sun_direction(day_time: float) -> Vector3:
	return _orbit_direction(day_time * TAU, PATH_TILT_DEGREES)


## Direção que aponta para a lua: do lado oposto do sol, em órbita inclinada à parte.
static func moon_direction(day_time: float) -> Vector3:
	return _orbit_direction((day_time + MOON_LAG) * TAU, MOON_TILT_DEGREES)


## Seno da altura do sol: 1 no zênite, 0 no horizonte, negativo de noite.
static func sun_height(day_time: float) -> float:
	return sun_direction(day_time).y


static func _orbit_direction(angle: float, tilt_degrees: float) -> Vector3:
	var tilt: float = deg_to_rad(tilt_degrees)

	return Vector3(cos(angle), sin(angle) * cos(tilt), sin(angle) * sin(tilt)).normalized()
