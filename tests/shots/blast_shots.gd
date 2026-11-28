extends Node3D
## Palco da magia de explosão: um BlastGround, câmeras miradas no _ready e um roteiro vindo dos
## argumentos (depois de --), cada um com o instante em segundos:
## [--at=x,z] [--charge=t[,duração]] [--blast=t[,energia]] [--crater=t[,raio,fundura]]
## [--fire=t[,raio]] [--spell=t[,energia,carga]] [--fire-speed=k] [--probe=t] [--record=segundos]
## --spell é a magia inteira: carga, explosão, cratera e fogo na medida da energia. --fire-speed
## acelera só o fogo (para o print do carvão sem esperar). --probe compara a colisão com a altura
## do chão; --record tira o ShotCapture e fecha a cena sozinha (para tools_src/record.sh).

const EFFECT_SCENE: PackedScene = preload("res://features/destruction/explosion_effect.tscn")

const OFFSCREEN_POSITION: Vector2i = Vector2i(-20000, -20000)
const CAMERA_HEIGHTS: Dictionary[String, float] = {
	"BlastWide": 1.0,
	"BlastPlayer": 1.4,
	"BlastClose": 0.3,
	"BlastTop": 0.0,
}
const DEFAULT_CHARGE: PackedFloat64Array = [0.0, 1.6]
const DEFAULT_BLAST: PackedFloat64Array = [0.0, 1500.0]
const DEFAULT_CRATER: PackedFloat64Array = [0.0, 5.0, 1.8]
const DEFAULT_FIRE: PackedFloat64Array = [0.0, 7.0]
const DEFAULT_SPELL: PackedFloat64Array = [0.0, 1500.0, 1.6]
## Cratera e fogo da magia inteira, em múltiplos do raio da bola de fogo.
const CRATER_RADIUS_SHARE: float = 0.75
const CRATER_DEPTH_SHARE: float = 0.28
const FIRE_RADIUS_SHARE: float = 1.25
const PROBE_HEIGHT: float = 20.0

var _center: Vector3 = Vector3.ZERO
var _fire_speed: float = 1.0
var _effect: ExplosionEffect
var _cue_by_argument: Dictionary[String, Callable] = {
	"--at": _set_center,
	"--charge": _schedule.bind(_play_charge, DEFAULT_CHARGE),
	"--blast": _schedule.bind(_play_blast, DEFAULT_BLAST),
	"--crater": _schedule.bind(_dig_crater, DEFAULT_CRATER),
	"--fire": _schedule.bind(_ignite, DEFAULT_FIRE),
	"--spell": _schedule.bind(_cast_spell, DEFAULT_SPELL),
	"--fire-speed": _set_fire_speed,
	"--probe": _schedule.bind(_probe_collision, PackedFloat64Array([0.0])),
	"--record": _record,
}

@onready var _ground: BlastGround = $Ground
@onready var _fire: FireGrid = $Fire


func _ready() -> void:
	_read_arguments()
	_aim_cameras()


func _process(delta: float) -> void:
	_fire.advance(delta * (_fire_speed - 1.0))


func _read_arguments() -> void:
	for argument in OS.get_cmdline_user_args():
		var parts: PackedStringArray = argument.split("=")
		var values: PackedFloat64Array = PackedFloat64Array()

		if parts.size() > 1:
			values = parts[1].split_floats(",")

		if _cue_by_argument.has(parts[0]):
			_cue_by_argument[parts[0]].call(values)


func _aim_cameras() -> void:
	for camera_name in CAMERA_HEIGHTS:
		var camera: Camera3D = get_node(camera_name) as Camera3D

		camera.position += _center
		camera.look_at(_center + Vector3.UP * CAMERA_HEIGHTS[camera_name])


func _set_center(values: PackedFloat64Array) -> void:
	_center = Vector3(values[0], 0.0, values[1])


func _set_fire_speed(values: PackedFloat64Array) -> void:
	_fire_speed = values[0]


## Roda cue no instante values[0] com os valores dados, completados pelos padrões.
func _schedule(values: PackedFloat64Array, cue: Callable, defaults: PackedFloat64Array) -> void:
	var filled: PackedFloat64Array = values + defaults.slice(values.size())

	await get_tree().create_timer(maxf(filled[0], 0.01)).timeout
	await get_tree().physics_frame

	cue.call(filled)


func _play_charge(values: PackedFloat64Array) -> void:
	_add_effect().play_charge(values[1])


func _play_blast(values: PackedFloat64Array) -> void:
	_add_effect().play_blast(values[1])


func _dig_crater(values: PackedFloat64Array) -> void:
	_ground.dig_crater(_center, values[1], values[2])


func _ignite(values: PackedFloat64Array) -> void:
	_fire.ignite(_center, values[1])


## A ordem que o jogo deve seguir: carga, explosão, cratera e só então o fogo na grama em volta.
func _cast_spell(values: PackedFloat64Array) -> void:
	var radius: float = ExplosionEffect.blast_radius_of(values[1])

	_add_effect().play_charge(values[2])

	await get_tree().create_timer(values[2]).timeout

	_add_effect().play_blast(values[1])
	_ground.dig_crater(_center, radius * CRATER_RADIUS_SHARE, radius * CRATER_DEPTH_SHARE)
	_fire.ignite(_center, radius * FIRE_RADIUS_SHARE)


## O efeito do palco: o mesmo nó serve à carga e à explosão; depois que ele some, vem outro.
func _add_effect() -> ExplosionEffect:
	if is_instance_valid(_effect):
		return _effect

	_effect = EFFECT_SCENE.instantiate()
	add_child(_effect)
	_effect.global_position = _center + Vector3.UP * (_ground.height_at(_center) + 0.02)

	return _effect


func _probe_collision(_values: PackedFloat64Array) -> void:
	var offsets: Dictionary[String, Vector3] = {
		"centro": Vector3.ZERO,
		"borda +x": Vector3(DEFAULT_CRATER[1] * 1.15, 0, 0),
		"dentro +z": Vector3(0, 0, DEFAULT_CRATER[1] * 0.5),
		"longe": Vector3(-14, 0, 9),
	}

	for label in offsets:
		var point: Vector3 = _center + offsets[label]
		var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
			point + Vector3.UP * PROBE_HEIGHT, point + Vector3.DOWN * PROBE_HEIGHT, 1
		)
		var hit: Dictionary = get_world_3d().direct_space_state.intersect_ray(query)
		var collision_height: float = hit.get("position", Vector3.INF).y

		print("PROBE ", label, " colisao=", collision_height, " chao=", _ground.height_at(point))


func _record(values: PackedFloat64Array) -> void:
	$ShotCapture.free()
	DisplayServer.window_set_position(OFFSCREEN_POSITION)

	await get_tree().create_timer(values[0]).timeout

	get_tree().quit()
