class_name LavaMarks
extends Node3D
## Marcas de lava que a Mula deixa no chão: pegadas em brasa com chaminhas e pingos, que esfriam
## e somem. Dois MultiMesh de tamanho fixo (mancha no chão e chama em pé) dividem as vagas de um
## LavaMarkPool; cada instância leva a hora em que nasceu e os shaders esfriam sozinhos, então
## nada é alocado nem percorrido por quadro. Fica solto no mundo (não anda com a mula).

const NOW_PARAMETER: StringName = &"now_seconds"
const COOLING_PARAMETER: StringName = &"cooling_seconds"
const GROUND_LIFT: float = 0.012

@export var cooling_seconds: float = 5.0
@export var stain_material: ShaderMaterial
@export var flame_material: ShaderMaterial

var _now_seconds: float = 0.0
var _pool: LavaMarkPool

@onready var _stains: MultiMesh = ($Stains as MultiMeshInstance3D).multimesh
@onready var _flames: MultiMesh = ($Flames as MultiMeshInstance3D).multimesh


func _ready() -> void:
	var unborn: Color = Color(LavaMarkPool.NEVER, 0.0, 0.0, 0.0)

	top_level = true
	global_transform = Transform3D.IDENTITY
	_pool = LavaMarkPool.new(_stains.instance_count)
	stain_material.set_shader_parameter(COOLING_PARAMETER, cooling_seconds)
	flame_material.set_shader_parameter(COOLING_PARAMETER, cooling_seconds)

	for slot in _pool.get_capacity():
		_stains.set_instance_custom_data(slot, unborn)
		_flames.set_instance_custom_data(slot, unborn)


func _process(delta: float) -> void:
	_now_seconds += delta

	stain_material.set_shader_parameter(NOW_PARAMETER, _now_seconds)
	flame_material.set_shader_parameter(NOW_PARAMETER, _now_seconds)


func count_hot_marks() -> int:
	return _pool.count_hot_marks(_now_seconds, cooling_seconds)


## Nova marca de `size` metros no ponto do chão, virada para `heading` (radianos em Y).
## `flame_share` é a altura da chaminha em relação ao tamanho (0 = sem chama, como nos pingos)
## e `horseshoe` escolhe a forma: 1 ferradura, 0 mancha.
func stamp(
	ground_position: Vector3, size: float, heading: float, flame_share: float, horseshoe: float
) -> void:
	var slot: int = _pool.claim_slot(_now_seconds)
	var birth: Color = Color(_now_seconds, randf(), horseshoe, 0.0)
	var turned: Basis = Basis(Vector3.UP, heading).scaled(Vector3.ONE * size)
	var standing: Basis = Basis.IDENTITY.scaled(Vector3.ONE * size * flame_share)
	var lifted_position: Vector3 = ground_position + Vector3.UP * GROUND_LIFT

	_stains.set_instance_transform(slot, Transform3D(turned, lifted_position))
	_stains.set_instance_custom_data(slot, birth)
	_flames.set_instance_transform(slot, Transform3D(standing, lifted_position))
	_flames.set_instance_custom_data(slot, birth)
