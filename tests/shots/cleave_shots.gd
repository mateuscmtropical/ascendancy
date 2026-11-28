extends Node3D
## Palco da magia de corte: chão BlastGround, o morro pré-cortado (FracturedBuilding com a base
## quase inquebrável), um boneco no lugar de quem lança e um roteiro vindo dos argumentos
## (depois de --), os instantes em segundos:
## [--caster=x,z] [--aim=x,z] [--cleave=t[,energia,comprimento]] [--effect=t[,energia,comprimento]]
## [--strike=t[,energia,comprimento]] [--slide=t[,velocidade,graus]] [--linked] [--camera=Nome]
## [--record=segundos]
## --cleave é a magia inteira (efeito + Impact em linha); --effect e --strike são as metades.
## --linked prega as fatias do topo umas nas outras (sai tudo junto de qualquer lado). --slide é
## experiência só do palco: solta o topo e empurra cada fatia de lado (para fora da linha; com
## graus, todas para o mesmo lado, girado a partir da direção do corte), para medir o empurrão
## que faz escorregar. --record tira o ShotCapture e fecha a cena sozinha (para tools_src/record.sh,
## que não escolhe câmera: usar --camera).

const EFFECT_SCENE: PackedScene = preload("res://features/destruction/cleave_effect.tscn")
const HILL_MODEL: PackedScene = preload("res://art/destruction/sliced_hill.gltf")

const OFFSCREEN_POSITION: Vector2i = Vector2i(-20000, -20000)
## Altura do corte acima dos pés de quem lança e raio do alcance, como no jogo.
const CUT_HEIGHT: float = 1.4
const CUT_RADIUS: float = 0.7
const BASE_TOUGHNESS: float = 50.0
const DEFAULT_CLEAVE: PackedFloat64Array = [0.0, 1500.0, 25.0]
const DEFAULT_SLIDE: PackedFloat64Array = [0.0, 7.0, NAN]
const FIGURE_HEIGHT: float = 0.875
const CAMERA_TARGET: Vector3 = Vector3(0, 2.2, 0)

var _caster: Vector3 = Vector3(0, 0, 13.5)
var _aim: Vector3 = Vector3.ZERO
var _hill: FracturedBuilding = FracturedBuilding.new()
var _cue_by_argument: Dictionary[String, Callable] = {
	"--caster": _set_caster,
	"--aim": _set_aim,
	"--cleave": _schedule.bind(_cast_cleave, DEFAULT_CLEAVE),
	"--effect": _schedule.bind(_play_effect, DEFAULT_CLEAVE),
	"--strike": _schedule.bind(_strike, DEFAULT_CLEAVE),
	"--slide": _schedule.bind(_slide_cap, DEFAULT_SLIDE),
	"--linked": _link_cap,
	"--camera": _pick_camera,
	"--record": _record,
}

@onready var _figure: MeshInstance3D = $Figure
@onready var _player_camera: Camera3D = $CleavePlayer


func _ready() -> void:
	_hill.model = HILL_MODEL
	_hill.toughness_by_section = {"Base": BASE_TOUGHNESS}
	_hill.linked_sections = PackedStringArray()
	_read_arguments()
	add_child(_hill)
	_place_caster()


func _read_arguments() -> void:
	for argument in OS.get_cmdline_user_args():
		var parts: PackedStringArray = argument.split("=")

		if _cue_by_argument.has(parts[0]):
			_cue_by_argument[parts[0]].call("=".join(parts.slice(1)))


## O boneco e a câmera do jogador (atrás e acima do ombro dele) seguem o lançador; as outras
## câmeras olham o morro.
func _place_caster() -> void:
	var forward: Vector3 = _cut_direction()

	_figure.position = _caster + Vector3.UP * FIGURE_HEIGHT
	_player_camera.position = _caster - forward * 4.0 + forward.cross(Vector3.UP) * 0.8
	_player_camera.position.y = 2.3
	_player_camera.look_at(_caster + forward * 12.0 + Vector3.UP * CUT_HEIGHT)

	for camera_name: String in ["CleaveWide", "CleaveSide", "CleaveFront", "CleaveTop"]:
		(get_node(camera_name) as Camera3D).look_at(CAMERA_TARGET)


func _cut_direction() -> Vector3:
	return (_aim - _caster).normalized()


func _cut_origin() -> Vector3:
	return _caster + Vector3.UP * CUT_HEIGHT


func _set_caster(text: String) -> void:
	var values: PackedFloat64Array = text.split_floats(",")

	_caster = Vector3(values[0], 0.0, values[1])


func _set_aim(text: String) -> void:
	var values: PackedFloat64Array = text.split_floats(",")

	_aim = Vector3(values[0], 0.0, values[1])


func _link_cap(_text: String) -> void:
	_hill.linked_sections = PackedStringArray(["Cap"])


func _pick_camera(text: String) -> void:
	(get_node(text) as Camera3D).current = true


## Roda cue no instante do primeiro valor, com os valores dados completados pelos padrões.
func _schedule(text: String, cue: Callable, defaults: PackedFloat64Array) -> void:
	var values: PackedFloat64Array = text.split_floats(",", false)
	var filled: PackedFloat64Array = values + defaults.slice(values.size())

	await get_tree().create_timer(maxf(filled[0], 0.01)).timeout
	await get_tree().physics_frame

	cue.call(filled)


func _cast_cleave(values: PackedFloat64Array) -> void:
	_play_effect(values)
	_strike(values)


func _play_effect(values: PackedFloat64Array) -> void:
	var effect: CleaveEffect = EFFECT_SCENE.instantiate()

	add_child(effect)
	effect.play(_cut_origin(), _cut_direction(), values[2], values[1])


func _strike(values: PackedFloat64Array) -> void:
	var impact: Impact = Impact.new(
		_cut_origin(), _cut_direction(), CUT_RADIUS, values[1], values[2]
	)
	var broken: int = Destruction.strike(impact, self)

	print("CLEAVE soltou ", broken, " pedaços; soltos na cena: ", Destruction.loose_piece_count())


## Experiência: solta todas as fatias do topo sem o Impact e dá a cada uma só um empurrão
## horizontal, sem giro: para fora da linha do corte ou, com graus, todas no mesmo rumo.
func _slide_cap(values: PackedFloat64Array) -> void:
	var holder: Node = _hill.find_child("Pieces_Cap", true, false)
	var forward: Vector3 = _cut_direction()

	for piece: BreakablePiece in holder.find_children("", "BreakablePiece", false, false):
		var offset: Vector3 = piece.global_position - _cut_origin()
		var sideways: Vector3 = offset - forward * offset.dot(forward)

		sideways.y = 0.0

		if not is_nan(values[2]):
			sideways = forward.rotated(Vector3.UP, deg_to_rad(values[2]))

		piece.break_free()
		piece.apply_central_impulse(sideways.normalized() * values[1] * piece.mass)


func _record(text: String) -> void:
	$ShotCapture.free()
	DisplayServer.window_set_position(OFFSCREEN_POSITION)

	await get_tree().create_timer(text.to_float()).timeout

	get_tree().quit()
