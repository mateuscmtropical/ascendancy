class_name SkyEvents
extends RefCounted
## Sorteio dos eventos raros do céu com sub-seed determinística (regra de determinismo do projeto):
## cada fatia de tempo e cada dia têm a semente própria, hash(world_seed, camada, índice), sem RNG
## compartilhado. Quem tem a mesma semente de mundo e o mesmo relógio vê as mesmas estrelas
## cadentes e os mesmos eclipses, no single-player e no multiplayer.

enum Layer { METEOR = 1, SHOWER = 2, ECLIPSE = 3 }

## Fatia de tempo sorteada de uma vez; uma estrela cadente começa dentro da fatia dela.
const SLOT_SECONDS: float = 20.0
const METEOR_CHANCE: Dictionary[bool, float] = {false: 0.14, true: 0.035}
const SHOWER_CHANCE: Dictionary[bool, float] = {false: 0.012, true: 0.004}
const METEOR_BRIGHTNESS: Dictionary[bool, Vector2] = {
	false: Vector2(0.8, 1.6),
	true: Vector2(0.25, 0.45),
}
const SHOWER_COUNT: Vector2i = Vector2i(5, 9)
const SHOWER_SECONDS: float = 6.0
const METEOR_SECONDS: Vector2 = Vector2(0.6, 1.4)
const METEOR_ARC_DEGREES: Vector2 = Vector2(12.0, 28.0)
const START_ELEVATION_DEGREES: Vector2 = Vector2(30.0, 72.0)
## Nenhum risco desce abaixo disto: a estrela some no céu, nunca cai no mapa.
const MIN_END_ELEVATION_DEGREES: float = 8.0
const SHOWER_SPREAD_DEGREES: Vector2 = Vector2(4.0, 16.0)
const ECLIPSE_CHANCE: float = 0.07
const ECLIPSE_SECONDS: Vector2 = Vector2(60.0, 120.0)
## Início do eclipse em fração do ciclo: o solar perto do meio-dia, o lunar perto da meia-noite.
const ECLIPSE_START: Dictionary[SkyEclipse.Kind, Vector2] = {
	SkyEclipse.Kind.SOLAR: Vector2(0.12, 0.34),
	SkyEclipse.Kind.LUNAR: Vector2(0.62, 0.84),
}
const HASH_PRIME: int = 16777619
const HASH_OFFSET: int = 2166136261
const HASH_MASK: int = 0xFFFFFFFF
const HASH_AVALANCHE: int = 0x45D9F3B


## Semente de 32 bits de uma lista de inteiros (FNV-1a byte a byte + avalanche), igual em toda
## plataforma: não depende do hash() do motor.
static func sub_seed(parts: Array[int]) -> int:
	var mixed: int = HASH_OFFSET

	for part in parts:
		mixed = _mix_word(mixed, part & HASH_MASK)

	mixed = ((mixed ^ (mixed >> 16)) * HASH_AVALANCHE) & HASH_MASK
	mixed = ((mixed ^ (mixed >> 16)) * HASH_AVALANCHE) & HASH_MASK

	return mixed ^ (mixed >> 16)


static func slot_of(game_seconds: float) -> int:
	return floori(game_seconds / SLOT_SECONDS)


## Estrelas cadentes que começam na fatia `slot` (de dia são mais raras e fracas): nenhuma, uma,
## ou de vez em quando uma chuva de várias saindo do mesmo ponto em poucos segundos.
static func meteors_in_slot(world_seed: int, slot: int, is_daytime: bool) -> Array[SkyMeteor]:
	var single: RandomNumberGenerator = _generator(world_seed, Layer.METEOR, slot)
	var shower: RandomNumberGenerator = _generator(world_seed, Layer.SHOWER, slot)
	var slot_start: float = slot * SLOT_SECONDS
	var meteors: Array[SkyMeteor] = []

	if shower.randf() < SHOWER_CHANCE[is_daytime]:
		meteors.append_array(
			_meteor_shower(
				shower,
				slot_start,
				is_daytime,
				SLOT_SECONDS - SHOWER_SECONDS,
				SHOWER_SECONDS,
				_random_radiant(shower)
			)
		)

	if single.randf() < METEOR_CHANCE[is_daytime]:
		meteors.append(_single_meteor(single, slot_start, is_daytime))

	return meteors


## Chuva de meteoros que começa em `start_seconds`: usada para forçar o evento em prints.
static func meteor_shower_at(
	world_seed: int,
	start_seconds: float,
	is_daytime: bool,
	spread_seconds: float = SHOWER_SECONDS,
	radiant: Vector3 = Vector3.ZERO,
) -> Array[SkyMeteor]:
	var generator: RandomNumberGenerator = _generator(world_seed, Layer.SHOWER, -1)
	var shower_radiant: Vector3 = radiant.normalized() if radiant else _random_radiant(generator)

	return _meteor_shower(generator, start_seconds, is_daytime, 0.0, spread_seconds, shower_radiant)


## Eclipse do dia `day` (contado do início do mundo), ou null na grande maioria dos dias.
static func eclipse_of_day(world_seed: int, day: int, cycle_seconds: float) -> SkyEclipse:
	var generator: RandomNumberGenerator = _generator(world_seed, Layer.ECLIPSE, day)
	var kind: SkyEclipse.Kind = SkyEclipse.Kind.SOLAR
	var start_window: Vector2

	if generator.randf() >= ECLIPSE_CHANCE:
		return null

	kind = SkyEclipse.Kind.SOLAR if generator.randf() < 0.5 else SkyEclipse.Kind.LUNAR
	start_window = ECLIPSE_START[kind]

	return SkyEclipse.new(
		kind,
		generator.randf_range(start_window.x, start_window.y) * cycle_seconds,
		generator.randf_range(ECLIPSE_SECONDS.x, ECLIPSE_SECONDS.y)
	)


static func _generator(world_seed: int, layer: Layer, index: int) -> RandomNumberGenerator:
	var generator: RandomNumberGenerator = RandomNumberGenerator.new()
	var parts: Array[int] = [world_seed, layer, index]

	generator.seed = sub_seed(parts)

	return generator


## Os quatro bytes de uma palavra de 32 bits, do menos significativo para o mais.
static func _mix_word(mixed: int, word: int) -> int:
	var result: int = mixed

	result = ((result ^ (word & 0xFF)) * HASH_PRIME) & HASH_MASK
	result = ((result ^ ((word >> 8) & 0xFF)) * HASH_PRIME) & HASH_MASK
	result = ((result ^ ((word >> 16) & 0xFF)) * HASH_PRIME) & HASH_MASK
	result = ((result ^ ((word >> 24) & 0xFF)) * HASH_PRIME) & HASH_MASK

	return result


static func _single_meteor(
	generator: RandomNumberGenerator, slot_start: float, is_daytime: bool
) -> SkyMeteor:
	var start_direction: Vector3 = _sky_direction(
		generator.randf_range(0.0, TAU),
		deg_to_rad(generator.randf_range(START_ELEVATION_DEGREES.x, START_ELEVATION_DEGREES.y))
	)
	var travel: Vector3 = _travel_direction(start_direction, generator.randf_range(0.0, TAU))

	return _meteor_along(
		generator,
		slot_start + generator.randf() * SLOT_SECONDS,
		start_direction,
		travel,
		is_daytime
	)


## Vários riscos saindo do mesmo ponto (radiante) ao longo de `spread_seconds`, a chuva começando
## entre `window_start` e `window_start + start_window`.
static func _meteor_shower(
	generator: RandomNumberGenerator,
	window_start: float,
	is_daytime: bool,
	start_window: float,
	spread_seconds: float,
	radiant: Vector3
) -> Array[SkyMeteor]:
	var count: int = generator.randi_range(SHOWER_COUNT.x, SHOWER_COUNT.y)
	var shower_start: float = window_start + generator.randf() * start_window
	var meteors: Array[SkyMeteor] = []

	for meteor_index in count:
		var outward: float = generator.randf_range(0.0, TAU)
		var spread: float = deg_to_rad(
			generator.randf_range(SHOWER_SPREAD_DEGREES.x, SHOWER_SPREAD_DEGREES.y)
		)
		var travel: Vector3 = _travel_direction(radiant, outward)
		var start_direction: Vector3 = radiant.rotated(radiant.cross(travel).normalized(), spread)
		var start: float = shower_start + generator.randf() * spread_seconds

		meteors.append(_meteor_along(generator, start, start_direction, travel, is_daytime))

	return meteors


static func _random_radiant(generator: RandomNumberGenerator) -> Vector3:
	return _sky_direction(
		generator.randf_range(0.0, TAU), deg_to_rad(generator.randf_range(45.0, 75.0))
	)


## Risco que sai de `start_direction` andando para `travel`, encurtado até terminar acima do
## horizonte mínimo.
static func _meteor_along(
	generator: RandomNumberGenerator,
	start: float,
	start_direction: Vector3,
	travel: Vector3,
	is_daytime: bool
) -> SkyMeteor:
	var axis: Vector3 = start_direction.cross(travel).normalized()
	var arc: float = deg_to_rad(generator.randf_range(METEOR_ARC_DEGREES.x, METEOR_ARC_DEGREES.y))
	var lowest: float = sin(deg_to_rad(MIN_END_ELEVATION_DEGREES))
	var brightness_range: Vector2 = METEOR_BRIGHTNESS[is_daytime]
	var end_direction: Vector3 = start_direction.rotated(axis, arc)

	while end_direction.y < lowest and arc > 0.01:
		arc *= 0.5
		end_direction = start_direction.rotated(axis, arc)

	return SkyMeteor.new(
		start,
		generator.randf_range(METEOR_SECONDS.x, METEOR_SECONDS.y),
		start_direction,
		end_direction,
		generator.randf_range(brightness_range.x, brightness_range.y)
	)


static func _sky_direction(azimuth: float, elevation: float) -> Vector3:
	return Vector3(cos(azimuth) * cos(elevation), sin(elevation), sin(azimuth) * cos(elevation))


## Direção tangente ao céu em `direction`, girada `angle` em volta dela; puxa um pouco para baixo,
## como as estrelas cadentes de verdade parecem cair.
static func _travel_direction(direction: Vector3, angle: float) -> Vector3:
	var east: Vector3 = Vector3.UP.cross(direction).normalized()
	var north: Vector3 = direction.cross(east).normalized()
	var tangent: Vector3 = east * cos(angle) + north * sin(angle)

	return (tangent - north * 0.35).normalized()
