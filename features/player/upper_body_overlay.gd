class_name UpperBodyOverlay
extends SkeletonModifier3D
## Toca um clipe só da cintura para cima, por cima da animação que o esqueleto já recebeu: o soco
## sai com as pernas ainda no passo. Filho do Skeleton3D; parado não custa nada (fica inativo).
## O tronco fica quase onde o clipe o põe, não onde o quadril do passo o levaria: correndo
## inclinado, o soco continua indo para a frente e não para o chão.

const FIRST_BONE: StringName = &"spine_01"
## Ossos de baixo que carregam o tronco: dizem como o quadril está no clipe e no corpo.
const CARRIER_BONES: Array[StringName] = [&"root", &"pelvis"]
## Quanto o tronco segue o clipe (1) em vez do quadril que está andando (0). Um resto do balanço
## do passo fica, senão o tronco parece pregado no ar.
const UPRIGHT_SHARE: float = 0.75
## Caminho das trilhas de osso nas bibliotecas, a partir do corpo.
const TRACK_PREFIX: String = "Armature/Skeleton3D:"

## Ossos de cima e, no fim da lista, os de CARRIER_BONES (lidos do clipe, nunca escritos).
var _bones: PackedInt32Array = PackedInt32Array()
var _upper_count: int = 0
var _rest_turns: Array[Quaternion] = []
## Pose que o clipe anterior deixou, de onde o clipe novo parte sem estalo.
var _previous_turns: Array[Quaternion] = []
var _shown_turns: Array[Quaternion] = []
var _tracks_by_clip: Dictionary[Animation, PackedInt32Array] = {}
var _clip: Animation
var _tracks: PackedInt32Array = PackedInt32Array()
var _seconds: float = 0.0
var _speed: float = 1.0
var _blend_seconds: float = 0.1
var _blend_progress: float = 1.0
var _target_influence: float = 0.0


func _ready() -> void:
	active = false
	influence = 0.0


func _skeleton_changed(_old_skeleton: Skeleton3D, new_skeleton: Skeleton3D) -> void:
	if new_skeleton != null:
		_list_upper_bones(new_skeleton)


func _process_modification_with_delta(delta: float) -> void:
	var skeleton: Skeleton3D = get_skeleton()
	var fade_step: float = delta / _blend_seconds

	_seconds += delta * _speed
	_blend_progress = minf(_blend_progress + fade_step, 1.0)
	influence = move_toward(influence, _target_influence, fade_step)

	_shown_turns[0] = _previous_turns[0].slerp(_first_turn(skeleton), _blend_progress)
	skeleton.set_bone_pose_rotation(_bones[0], _shown_turns[0])

	for index in range(1, _upper_count):
		var turn: Quaternion = _previous_turns[index].slerp(_clip_turn(index), _blend_progress)

		_shown_turns[index] = turn
		skeleton.set_bone_pose_rotation(_bones[index], turn)

	if influence <= 0.0 and _target_influence <= 0.0:
		active = false


## Começa o clipe do zero; se outro ainda está tocando, parte da pose dele.
func play(clip: Animation, speed: float, blend_seconds: float) -> void:
	var is_cutting_in: bool = active and influence > 0.0

	if is_cutting_in:
		_previous_turns.assign(_shown_turns)

	_clip = clip
	_tracks = _tracks_of(clip)
	_seconds = 0.0
	_speed = speed
	_blend_seconds = blend_seconds
	_blend_progress = 0.0 if is_cutting_in else 1.0
	_target_influence = 1.0
	active = true


## Devolve o tronco e os braços à animação de baixo, sem tranco.
func stop(blend_seconds: float) -> void:
	_blend_seconds = blend_seconds
	_target_influence = 0.0


## Giro do primeiro osso do tronco que o deixa perto de onde o clipe o põe no espaço do corpo,
## descontando a diferença entre o quadril do clipe e o quadril que está andando.
func _first_turn(skeleton: Skeleton3D) -> Quaternion:
	var clip_hips: Quaternion = _clip_turn(_upper_count) * _clip_turn(_upper_count + 1)
	var body_hips_pose: Transform3D = skeleton.get_bone_global_pose(_bones[_upper_count + 1])
	var body_hips: Quaternion = body_hips_pose.basis.get_rotation_quaternion()
	var clip_first: Quaternion = _clip_turn(0)
	var level_first: Quaternion = body_hips.inverse() * clip_hips * clip_first

	return clip_first.slerp(level_first, UPRIGHT_SHARE)


func _clip_turn(index: int) -> Quaternion:
	var track: int = _tracks[index]

	# Osso que o clipe não move (trilha parada some na importação) fica na pose de descanso.
	if track < 0:
		return _rest_turns[index]

	return _clip.rotation_track_interpolate(track, _seconds)


## Ossos de spine_01 para cima (o primeiro da lista é ele: no esqueleto o pai sempre vem antes
## do filho), mais os que carregam o tronco.
func _list_upper_bones(skeleton: Skeleton3D) -> void:
	var is_upper: Dictionary[int, bool] = {}

	_bones.clear()
	_rest_turns.clear()

	for bone in skeleton.get_bone_count():
		var is_first: bool = skeleton.get_bone_name(bone) == FIRST_BONE

		if is_first or is_upper.has(skeleton.get_bone_parent(bone)):
			is_upper[bone] = true
			_bones.append(bone)

	_upper_count = _bones.size()

	for bone_name in CARRIER_BONES:
		_bones.append(skeleton.find_bone(bone_name))

	for bone in _bones:
		_rest_turns.append(skeleton.get_bone_rest(bone).basis.get_rotation_quaternion())

	_previous_turns.assign(_rest_turns)
	_shown_turns.assign(_rest_turns)
	_tracks_by_clip.clear()


## Trilha de rotação de cada osso de cima neste clipe (-1 = sem trilha), achada uma vez por clipe.
func _tracks_of(clip: Animation) -> PackedInt32Array:
	var skeleton: Skeleton3D = get_skeleton()
	var tracks: PackedInt32Array = _tracks_by_clip.get(clip, PackedInt32Array())

	if not tracks.is_empty():
		return tracks

	for bone in _bones:
		var path: NodePath = NodePath(TRACK_PREFIX + skeleton.get_bone_name(bone))

		tracks.append(clip.find_track(path, Animation.TYPE_ROTATION_3D))

	_tracks_by_clip[clip] = tracks

	return tracks
