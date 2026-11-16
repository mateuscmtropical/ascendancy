class_name DayNightCycle
extends Node
## Dia e noite da cidade: gira o sol (e de noite a lua) na mesma luz direcional, muda cor e
## energia dela, a luz ambiente, a névoa, a exposição e o céu (art/shaders/sky.gdshader), acende
## os postes ao anoitecer e passa ao céu as estrelas cadentes e os eclipses sorteados por
## SkyEvents. Tudo sai de um número só, o tempo de jogo: quem tem o mesmo tempo e a mesma semente
## vê o mesmo céu.
##
## Iluminação: a cidade não tem GI assado por hora do dia. Quem acompanha o ciclo é a luz
## direcional, a luz ambiente vinda do céu (radiância do Sky, refeita conforme o shader muda), a
## névoa e a exposição; as luzes locais (postes, lojas) são fixas e só os postes apagam de dia.
##
## Argumentos (depois de --): --time-of-day=0.8 congela o relógio nessa hora (prints);
## --sky-event=shower|solar|lunar força um evento para conferir o visual.

enum ForcedEvent { NONE, METEOR_SHOWER, SOLAR_ECLIPSE, LUNAR_ECLIPSE }

const NIGHT_LIGHTS_GROUP: StringName = &"night_lights"
const BASE_ENERGY_META: StringName = &"day_night_base_energy"
const TIME_ARGUMENT: String = "--time-of-day="
const EVENT_ARGUMENT: String = "--sky-event="
const EVENT_BY_NAME: Dictionary[String, ForcedEvent] = {
	"shower": ForcedEvent.METEOR_SHOWER,
	"solar": ForcedEvent.SOLAR_ECLIPSE,
	"lunar": ForcedEvent.LUNAR_ECLIPSE,
}
const FORCED_ECLIPSE: Dictionary[ForcedEvent, Vector2] = {
	ForcedEvent.SOLAR_ECLIPSE: Vector2(1.0, 0.0),
	ForcedEvent.LUNAR_ECLIPSE: Vector2(0.0, 1.0),
}
const METEOR_SLOTS: int = 8
const FROZEN_SHOWER_SECONDS: float = 0.5
const SUN_ENERGY: float = 1.35
const MOON_ENERGY: float = 0.16
const NOON_SUN_COLOR: Color = Color(1.0, 0.902, 0.769)
const LOW_SUN_COLOR: Color = Color(1.0, 0.6, 0.36)
const MOON_LIGHT_COLOR: Color = Color(0.62, 0.72, 0.95)
const BLOOD_MOON_COLOR: Color = Color(0.85, 0.4, 0.3)
const DAY_AMBIENT: Color = Color(0.663, 0.784, 0.941)
const TWILIGHT_AMBIENT: Color = Color(0.85, 0.62, 0.55)
const NIGHT_AMBIENT: Color = Color(0.16, 0.2, 0.34)
const DAY_FOG: Color = Color(0.78, 0.87, 0.95)
const TWILIGHT_FOG: Color = Color(0.93, 0.68, 0.52)
const NIGHT_FOG: Color = Color(0.05, 0.07, 0.12)
const DAY_EXPOSURE: float = 0.95
const NIGHT_EXPOSURE: float = 1.35
const NIGHT_AMBIENT_ENERGY: float = 0.45
## Postes acendem quando o céu escurece abaixo disto e chegam ao máximo na noite fechada.
const LAMPS_ON_DAY_AMOUNT: Vector2 = Vector2(0.15, 0.45)
## Estrela que começou na fatia anterior ainda pode estar riscando o céu.
const SLOT_LOOKBACK: int = 1

@export var sun: DirectionalLight3D
@export var world_environment: WorldEnvironment
## Ciclo inteiro em minutos de jogo: metade dia claro, metade noite (pedido: 10 a 15 min cada).
@export var cycle_minutes: float = 24.0
## Hora em que o jogo começa (0 nascer, 0,25 meio-dia, 0,5 pôr do sol, 0,75 meia-noite).
@export_range(0.0, 1.0) var start_time_of_day: float = 0.18
@export var world_seed: int = 1
@export var time_scale: float = 1.0
@export var forced_event: ForcedEvent = ForcedEvent.NONE

var game_seconds: float = 0.0
## Direção que aponta para o sol agora e a força da luz dele (0 de noite, menor no eclipse);
## lidas pelos vitrais da catedral (SunThroughGlass).
var sun_direction_now: Vector3 = Vector3.UP
var sunlight: float = 1.0

var _sky_material: ShaderMaterial
var _meteors_by_slot: Dictionary[int, Array] = {}
var _eclipses_by_day: Dictionary[int, SkyEclipse] = {}
var _forced_meteors: Array[SkyMeteor] = []
var _meteor_heads: PackedVector4Array = PackedVector4Array()
var _meteor_tails: PackedVector4Array = PackedVector4Array()
var _lamp_amount: float = -1.0


func _ready() -> void:
	var arguments: PackedStringArray = OS.get_cmdline_user_args()

	_meteor_heads.resize(METEOR_SLOTS)
	_meteor_tails.resize(METEOR_SLOTS)
	_read_arguments(arguments)

	if world_environment and world_environment.environment.sky:
		_sky_material = world_environment.environment.sky.sky_material as ShaderMaterial

	if forced_event == ForcedEvent.METEOR_SHOWER:
		_start_shower_next_frame()

	apply_sky()


func _process(delta: float) -> void:
	game_seconds += delta * time_scale
	apply_sky()


func cycle_seconds() -> float:
	return cycle_minutes * 60.0


func time_of_day() -> float:
	return SkyClock.time_of_day(game_seconds, cycle_seconds(), start_time_of_day)


## Pula o relógio para uma hora do dia (mantém o dia corrente).
func set_time_of_day(day_time: float) -> void:
	var day: int = SkyClock.day_index(game_seconds, cycle_seconds(), start_time_of_day)

	game_seconds = (day + day_time - start_time_of_day) * cycle_seconds()
	apply_sky()


## Solta agora uma chuva de meteoros saindo do céu à frente da câmera (vídeo, print). Com o relógio
## parado os riscos saem quase juntos, para aparecerem todos na mesma imagem.
func start_meteor_shower() -> void:
	var is_day: bool = SkyClock.is_daytime(time_of_day())
	var is_frozen: bool = is_zero_approx(time_scale)
	var spread: float = FROZEN_SHOWER_SECONDS if is_frozen else SkyEvents.SHOWER_SECONDS
	var start: float = game_seconds - spread if is_frozen else game_seconds
	var camera: Camera3D = get_viewport().get_camera_3d()
	var looking: Vector3 = -camera.global_basis.z if camera else Vector3.ZERO
	var radiant: Vector3 = (
		Vector3(looking.x, maxf(looking.y, 0.8), looking.z) if camera else looking
	)

	_forced_meteors = SkyEvents.meteor_shower_at(world_seed, start, is_day, spread, radiant)


## Quanto o céu está claro (0 noite fechada, 1 dia) para a altura do sol.
static func day_amount_for(sun_height: float) -> float:
	return smoothstep(-0.12, 0.1, sun_height)


## Quanto do laranja do nascer/pôr do sol aparece: máximo com o sol rente ao horizonte.
static func twilight_amount_for(sun_height: float) -> float:
	return clampf(1.0 - absf(sun_height - 0.02) / 0.22, 0.0, 1.0)


## Fração da energia dos postes: zero de dia, cheia de noite.
static func lamp_amount_for(day_amount: float) -> float:
	return 1.0 - smoothstep(LAMPS_ON_DAY_AMOUNT.x, LAMPS_ON_DAY_AMOUNT.y, day_amount)


func apply_sky() -> void:
	var day_time: float = time_of_day()
	var sun_direction: Vector3 = SkyClock.sun_direction(day_time)
	var moon_direction: Vector3 = SkyClock.moon_direction(day_time)
	var day_amount: float = day_amount_for(sun_direction.y)
	var twilight_amount: float = twilight_amount_for(sun_direction.y)
	var eclipse: Vector2 = _eclipse_coverage()

	_light_with_sun_or_moon(sun_direction, moon_direction, eclipse)
	_tint_environment(day_amount, twilight_amount, eclipse.x)
	_switch_night_lights(day_amount * (1.0 - 0.8 * eclipse.x))
	_fill_meteor_slots()

	if _sky_material == null:
		return

	_sky_material.set_shader_parameter(&"sun_direction", sun_direction)
	_sky_material.set_shader_parameter(&"moon_direction", moon_direction)
	_sky_material.set_shader_parameter(&"day_amount", day_amount)
	_sky_material.set_shader_parameter(&"twilight_amount", twilight_amount)
	_sky_material.set_shader_parameter(&"cloud_time", game_seconds)
	_sky_material.set_shader_parameter(&"solar_eclipse", eclipse.x)
	_sky_material.set_shader_parameter(&"lunar_eclipse", eclipse.y)
	_sky_material.set_shader_parameter(&"meteor_heads", _meteor_heads)
	_sky_material.set_shader_parameter(&"meteor_tails", _meteor_tails)


## Cobertura do eclipse solar (x) e lunar (y) agora: sorteado por dia, ou forçado por argumento.
func _eclipse_coverage() -> Vector2:
	var day: int = SkyClock.day_index(game_seconds, cycle_seconds(), start_time_of_day)
	var seconds_into_day: float = (
		(start_time_of_day + game_seconds / cycle_seconds() - day) * cycle_seconds()
	)
	var eclipse: SkyEclipse
	var coverage: float

	if FORCED_ECLIPSE.has(forced_event):
		return FORCED_ECLIPSE[forced_event]

	if not _eclipses_by_day.has(day):
		_eclipses_by_day[day] = SkyEvents.eclipse_of_day(world_seed, day, cycle_seconds())

	eclipse = _eclipses_by_day[day]

	if eclipse == null:
		return Vector2.ZERO

	coverage = eclipse.coverage_at(seconds_into_day)

	return (
		Vector2(coverage, 0.0) if eclipse.kind == SkyEclipse.Kind.SOLAR else Vector2(0.0, coverage)
	)


## A mesma luz direcional é o sol de dia e a lua de noite; troca de astro com o sol no horizonte,
## quando a energia dos dois está perto de zero.
func _light_with_sun_or_moon(
	sun_direction: Vector3, moon_direction: Vector3, eclipse: Vector2
) -> void:
	var is_sun_up: bool = sun_direction.y > -0.03
	var source_direction: Vector3 = sun_direction if is_sun_up else moon_direction
	var sun_strength: float = smoothstep(-0.03, 0.18, sun_direction.y) * (1.0 - 0.85 * eclipse.x)
	var moon_strength: float = smoothstep(0.0, 0.25, moon_direction.y) * (1.0 - 0.5 * eclipse.y)
	var sun_tint: Color = LOW_SUN_COLOR.lerp(NOON_SUN_COLOR, smoothstep(0.02, 0.4, sun_direction.y))
	var moon_tint: Color = MOON_LIGHT_COLOR.lerp(BLOOD_MOON_COLOR, eclipse.y)

	sun_direction_now = sun_direction
	sunlight = sun_strength

	if sun == null:
		return

	sun.light_color = sun_tint if is_sun_up else moon_tint
	sun.light_energy = SUN_ENERGY * sun_strength if is_sun_up else MOON_ENERGY * moon_strength
	sun.visible = sun.light_energy > 0.001

	if source_direction.y <= 0.0:
		return

	sun.global_basis = Basis.looking_at(-source_direction, Vector3.UP)


func _tint_environment(day_amount: float, twilight_amount: float, solar_eclipse: float) -> void:
	var environment: Environment = world_environment.environment if world_environment else null
	var ambient: Color = NIGHT_AMBIENT.lerp(DAY_AMBIENT, day_amount)
	var fog: Color = NIGHT_FOG.lerp(DAY_FOG, day_amount)
	var darkening: float = 1.0 - 0.6 * solar_eclipse

	if environment == null:
		return

	environment.ambient_light_color = ambient.lerp(TWILIGHT_AMBIENT, twilight_amount * 0.45)
	environment.ambient_light_energy = lerpf(NIGHT_AMBIENT_ENERGY, 1.0, day_amount) * darkening
	environment.fog_light_color = fog.lerp(TWILIGHT_FOG, twilight_amount * 0.6) * darkening
	environment.tonemap_exposure = lerpf(NIGHT_EXPOSURE, DAY_EXPOSURE, day_amount)


## Postes e demais luzes do grupo night_lights (a energia original é guardada na primeira vez) e
## o brilho das janelas (global night_glow, art/shaders/window_glass.gdshader).
func _switch_night_lights(day_amount: float) -> void:
	var lamp_amount: float = lamp_amount_for(day_amount)

	if is_equal_approx(lamp_amount, _lamp_amount):
		return

	_lamp_amount = lamp_amount
	RenderingServer.global_shader_parameter_set(&"night_glow", lamp_amount)

	for node in get_tree().get_nodes_in_group(NIGHT_LIGHTS_GROUP):
		var night_light: Light3D = node as Light3D

		if not night_light.has_meta(BASE_ENERGY_META):
			night_light.set_meta(BASE_ENERGY_META, night_light.light_energy)

		night_light.light_energy = night_light.get_meta(BASE_ENERGY_META) * lamp_amount
		night_light.visible = lamp_amount > 0.01


## Até METEOR_SLOTS estrelas cadentes no céu agora, das fatias atual e anterior.
func _fill_meteor_slots() -> void:
	var slot: int = SkyEvents.slot_of(game_seconds)
	var visible_meteors: Array[SkyMeteor] = _forced_meteors.filter(
		func(meteor: SkyMeteor) -> bool: return meteor.is_visible_at(game_seconds)
	)

	for recent_slot in range(slot - SLOT_LOOKBACK, slot + 1):
		visible_meteors.append_array(
			_meteors_of_slot(recent_slot).filter(
				func(meteor: SkyMeteor) -> bool: return meteor.is_visible_at(game_seconds)
			)
		)

	for slot_index in METEOR_SLOTS:
		var meteor: SkyMeteor = (
			visible_meteors[slot_index] if slot_index < visible_meteors.size() else null
		)

		_meteor_heads[slot_index] = _meteor_vector(meteor, true)
		_meteor_tails[slot_index] = _meteor_vector(meteor, false)

	_forget_old_slots(slot)


func _meteors_of_slot(slot: int) -> Array[SkyMeteor]:
	var slot_time: float = slot * SkyEvents.SLOT_SECONDS
	var is_day: bool = SkyClock.is_daytime(
		SkyClock.time_of_day(slot_time, cycle_seconds(), start_time_of_day)
	)
	var meteors: Array[SkyMeteor] = []

	if not _meteors_by_slot.has(slot):
		_meteors_by_slot[slot] = SkyEvents.meteors_in_slot(world_seed, slot, is_day)

	meteors.assign(_meteors_by_slot[slot])

	return meteors


func _forget_old_slots(slot: int) -> void:
	for cached_slot in _meteors_by_slot.keys():
		if cached_slot < slot - SLOT_LOOKBACK:
			_meteors_by_slot.erase(cached_slot)


func _meteor_vector(meteor: SkyMeteor, is_head: bool) -> Vector4:
	var direction: Vector3

	if meteor == null:
		return Vector4(0.0, 1.0, 0.0, 0.0)

	direction = meteor.head_at(game_seconds) if is_head else meteor.tail_at(game_seconds)

	return Vector4(direction.x, direction.y, direction.z, meteor.glow_at(game_seconds))


## A câmera do print ou do vídeo só fica atual depois do primeiro quadro da cena.
func _start_shower_next_frame() -> void:
	await get_tree().process_frame

	start_meteor_shower()


func _read_arguments(arguments: PackedStringArray) -> void:
	for argument in arguments:
		if argument.begins_with(TIME_ARGUMENT):
			time_scale = 0.0
			set_time_of_day(argument.trim_prefix(TIME_ARGUMENT).to_float())

		if argument.begins_with(EVENT_ARGUMENT):
			forced_event = EVENT_BY_NAME.get(argument.trim_prefix(EVENT_ARGUMENT), ForcedEvent.NONE)
