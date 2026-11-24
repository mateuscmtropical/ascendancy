class_name FaceAnimator
extends Node
## Rosto vivo de um personagem: pisca sozinho, passeia o olhar e mistura expressões nas
## blend shapes que tools_src/face_shapes.py esculpe na cabeça, nos olhos e nas sobrancelhas.

enum Mood { NEUTRAL, HAPPY, FOCUSED, EFFORT, PAIN, SURPRISED, SAD }

const BLINK_LEFT: StringName = &"blink_l"
const BLINK_RIGHT: StringName = &"blink_r"
const LOOK_LEFT: StringName = &"look_left"
const LOOK_RIGHT: StringName = &"look_right"
const LOOK_UP: StringName = &"look_up"
const LOOK_DOWN: StringName = &"look_down"
const MOUTH_OPEN: StringName = &"mouth_open"
const EXPRESSION_SHAPES: Array[StringName] = [
	&"squint",
	&"eyes_wide",
	&"brow_up",
	&"brow_angry",
	&"brow_sad",
	&"smile",
	&"frown",
	&"mouth_open",
]
const WEIGHTS_BY_EXPRESSION: Dictionary[Mood, Dictionary] = {
	Mood.NEUTRAL: {},
	Mood.HAPPY: {&"smile": 1.0, &"squint": 0.35, &"brow_up": 0.3},
	Mood.FOCUSED: {&"brow_angry": 0.6, &"squint": 0.2, &"frown": 0.25},
	Mood.EFFORT: {&"mouth_open": 0.55, &"brow_angry": 1.0, &"squint": 0.45},
	Mood.PAIN: {&"squint": 1.0, &"brow_sad": 0.7, &"frown": 0.6, &"mouth_open": 0.3},
	Mood.SURPRISED: {&"eyes_wide": 1.0, &"brow_up": 1.0, &"mouth_open": 0.45},
	Mood.SAD: {&"brow_sad": 1.0, &"frown": 0.7},
}
## O rosto leva este tempo para trocar de expressão; golpes pedem troca mais seca.
const EXPRESSION_BLEND_SECONDS: float = 0.16
const BLINK_CLOSE_SECONDS: float = 0.07
const BLINK_OPEN_SECONDS: float = 0.14
const BLINK_PAUSE_MIN_SECONDS: float = 2.2
const BLINK_PAUSE_MAX_SECONDS: float = 5.5
## Às vezes a piscada vem em dupla, como em gente.
const DOUBLE_BLINK_CHANCE: float = 0.18
const DOUBLE_BLINK_PAUSE_SECONDS: float = 0.12
const GAZE_PAUSE_MIN_SECONDS: float = 0.9
const GAZE_PAUSE_MAX_SECONDS: float = 2.8
const GAZE_REACH: Vector2 = Vector2(0.5, 0.3)
## Metade das vezes o olhar volta para a frente em vez de ir para outro canto.
const GAZE_HOME_CHANCE: float = 0.5
const GAZE_SPEED: float = 22.0
## Falando, a boca abre e fecha em sílabas de duração e abertura sorteadas, com pausas.
const SYLLABLE_SECONDS_RANGE: Vector2 = Vector2(0.11, 0.24)
const SYLLABLE_OPEN_RANGE: Vector2 = Vector2(0.15, 0.5)
const SPEECH_PAUSE_CHANCE: float = 0.15

## Expressão de descanso: para onde o rosto volta quando uma expressão passageira acaba.
var resting_expression: Mood = Mood.NEUTRAL
var is_talking: bool = false

var _shape_meshes: Array[MeshInstance3D] = []
var _shape_indices: PackedInt32Array = PackedInt32Array()
var _shape_names: Array[StringName] = []
## Último peso mandado a cada blend shape: repetir o mesmo valor ainda suja a malha no servidor.
var _sent_weights: PackedFloat32Array = PackedFloat32Array()
var _weights: Dictionary[StringName, float] = {}
var _expression: Mood = Mood.NEUTRAL
var _expression_seconds_left: float = 0.0
var _blink_seconds: float = 0.0
var _blink_pause_seconds: float = 0.0
var _gaze: Vector2 = Vector2.ZERO
var _gaze_target: Vector2 = Vector2.ZERO
var _gaze_pause_seconds: float = 0.0
var _syllable_seconds: float = 0.0
var _syllable_length: float = 0.0
var _syllable_open: float = 0.0
var _random: RandomNumberGenerator = RandomNumberGenerator.new()


func _ready() -> void:
	_random.randomize()
	_blink_seconds = BLINK_CLOSE_SECONDS + BLINK_OPEN_SECONDS
	_blink_pause_seconds = _random.randf_range(0.0, BLINK_PAUSE_MAX_SECONDS)
	_gaze_pause_seconds = _random.randf_range(0.0, GAZE_PAUSE_MAX_SECONDS)


func _process(delta: float) -> void:
	advance(delta)


## Liga o rosto às malhas do corpo recém-montado; corpo sem blend shapes deixa o rosto parado.
func bind(skeleton: Skeleton3D) -> void:
	_shape_meshes.clear()
	_shape_indices.clear()
	_shape_names.clear()
	_sent_weights.clear()
	_weights.clear()

	for child in skeleton.get_children():
		if child is MeshInstance3D:
			_bind_mesh(child)

	set_process(not _shape_meshes.is_empty())


## Mostra uma expressão; com hold_seconds ela é passageira e o rosto volta à de descanso.
func show_expression(expression: Mood, hold_seconds: float = 0.0) -> void:
	_expression = expression
	_expression_seconds_left = hold_seconds


func has_shape(shape_name: StringName) -> bool:
	return _weights.has(shape_name)


func weight_of(shape_name: StringName) -> float:
	return _weights.get(shape_name, 0.0)


func blink_now() -> void:
	_blink_seconds = 0.0


## Longe da câmera o rosto não passa de uns pixels: volta ao neutro de olhos abertos e para de
## animar até chegar perto de novo.
func set_detailed(is_detailed: bool) -> void:
	if _shape_meshes.is_empty() or is_detailed == is_processing():
		return

	set_process(is_detailed)

	if is_detailed:
		return

	for shape_name in _weights:
		_weights[shape_name] = 0.0

	_gaze = Vector2.ZERO
	_gaze_target = Vector2.ZERO
	_apply_weights()


## Um passo do rosto; o _process chama a cada quadro e os testes chamam com o tempo que quiserem.
func advance(delta: float) -> void:
	_advance_expression(delta)
	_advance_talk(delta)
	_advance_blink(delta)
	_advance_gaze(delta)
	_apply_weights()


func _bind_mesh(mesh_instance: MeshInstance3D) -> void:
	for shape_index in mesh_instance.get_blend_shape_count():
		var shape_name: StringName = mesh_instance.mesh.get_blend_shape_name(shape_index)

		_shape_meshes.append(mesh_instance)
		_shape_indices.append(shape_index)
		_shape_names.append(shape_name)
		_sent_weights.append(mesh_instance.get_blend_shape_value(shape_index))
		_weights[shape_name] = 0.0


func _advance_expression(delta: float) -> void:
	var step: float = delta / EXPRESSION_BLEND_SECONDS
	var targets: Dictionary = WEIGHTS_BY_EXPRESSION[_expression]

	for shape_name in EXPRESSION_SHAPES:
		var target: float = targets.get(shape_name, 0.0)

		_weights[shape_name] = move_toward(_weights.get(shape_name, 0.0), target, step)

	if _expression == resting_expression:
		return

	if _expression_seconds_left <= 0.0:
		return

	_expression_seconds_left -= delta

	if _expression_seconds_left <= 0.0:
		_expression = resting_expression


func _advance_talk(delta: float) -> void:
	var chatter: float

	if not is_talking:
		return

	_syllable_seconds += delta

	if _syllable_seconds >= _syllable_length:
		_start_syllable()

	chatter = _syllable_open * sin(PI * _syllable_seconds / _syllable_length)
	_weights[MOUTH_OPEN] = maxf(_weights.get(MOUTH_OPEN, 0.0), chatter)


func _start_syllable() -> void:
	var is_pause: bool = _random.randf() < SPEECH_PAUSE_CHANCE

	_syllable_seconds = 0.0
	_syllable_length = _random.randf_range(SYLLABLE_SECONDS_RANGE.x, SYLLABLE_SECONDS_RANGE.y)
	_syllable_open = (
		0.0 if is_pause else _random.randf_range(SYLLABLE_OPEN_RANGE.x, SYLLABLE_OPEN_RANGE.y)
	)


func _advance_blink(delta: float) -> void:
	var closed: float = _blink_closure(_blink_seconds)

	_weights[BLINK_LEFT] = closed
	_weights[BLINK_RIGHT] = closed

	if _blink_seconds < BLINK_CLOSE_SECONDS + BLINK_OPEN_SECONDS:
		_blink_seconds += delta
		return

	_blink_pause_seconds -= delta

	if _blink_pause_seconds > 0.0:
		return

	var is_double: bool = _random.randf() < DOUBLE_BLINK_CHANCE
	var long_pause: float = _random.randf_range(BLINK_PAUSE_MIN_SECONDS, BLINK_PAUSE_MAX_SECONDS)

	_blink_pause_seconds = DOUBLE_BLINK_PAUSE_SECONDS if is_double else long_pause
	_blink_seconds = 0.0


## Pálpebra fecha depressa e abre mais devagar; 1 é olho fechado.
func _blink_closure(blink_seconds: float) -> float:
	if blink_seconds < BLINK_CLOSE_SECONDS:
		return blink_seconds / BLINK_CLOSE_SECONDS

	var opening: float = (blink_seconds - BLINK_CLOSE_SECONDS) / BLINK_OPEN_SECONDS

	return 1.0 - smoothstep(0.0, 1.0, opening)


func _advance_gaze(delta: float) -> void:
	_gaze = _gaze.lerp(_gaze_target, minf(1.0, GAZE_SPEED * delta))
	_weights[LOOK_LEFT] = maxf(_gaze.x, 0.0)
	_weights[LOOK_RIGHT] = maxf(-_gaze.x, 0.0)
	_weights[LOOK_UP] = maxf(_gaze.y, 0.0)
	_weights[LOOK_DOWN] = maxf(-_gaze.y, 0.0)
	_gaze_pause_seconds -= delta

	if _gaze_pause_seconds > 0.0:
		return

	var is_going_home: bool = _random.randf() < GAZE_HOME_CHANCE
	var wander: Vector2 = (
		Vector2(_random.randf_range(-1.0, 1.0), _random.randf_range(-1.0, 1.0)) * GAZE_REACH
	)

	_gaze_target = Vector2.ZERO if is_going_home else wander
	_gaze_pause_seconds = _random.randf_range(GAZE_PAUSE_MIN_SECONDS, GAZE_PAUSE_MAX_SECONDS)


func _apply_weights() -> void:
	for shape in _shape_meshes.size():
		var weight: float = _weights[_shape_names[shape]]

		if weight == _sent_weights[shape]:
			continue

		_sent_weights[shape] = weight
		_shape_meshes[shape].set_blend_shape_value(_shape_indices[shape], weight)
