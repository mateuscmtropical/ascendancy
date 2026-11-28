class_name FireGrid
extends Node
## Fogo que anda pela grama de um BlastGround, numa grade de células: cada célula acesa queima por
## alguns segundos, tenta acender as vizinhas (com sorte e cada geração mais fraca, então o fogo
## morre sozinho) e deixa carvão na máscara do chão. Terra exposta e carvão não pegam fogo.
## Visual: brasa na máscara do chão em toda célula acesa e um número fixo de emissores de chama e
## fumaça; faltou emissor, a célula nova toma o da mais antiga (a frente do fogo fica com as
## chamas). advance() move o fogo; o _process só o chama, então teste pode passar o tempo na mão.

signal fire_died

enum CellState { FRESH, BURNING, BURNT }

const FLAME_SHADER: Shader = preload("res://art/shaders/flame.gdshader")
const SMOKE_SHADER: Shader = preload("res://art/shaders/smoke.gdshader")
const MAX_EMITTERS: int = 24
const TICK_SECONDS: float = 0.2
## Acima disto o chão já não é grama: não tem o que queimar.
const FUEL_BURN_LIMIT: float = 0.4
const FRESH_SCORCH: float = 0.3
## O que a célula deixa ao apagar: carvão, com folga para o ruído do shader roer a borda.
const CHARRED_BURN: float = 0.9
const DEAD_VIGOR: float = 0.15
const NEIGHBOR_OFFSETS: Array[Vector2i] = [
	Vector2i(1, 0),
	Vector2i(-1, 0),
	Vector2i(0, 1),
	Vector2i(0, -1),
	Vector2i(1, 1),
	Vector2i(-1, 1),
	Vector2i(1, -1),
	Vector2i(-1, -1),
]
const HEAT_COLORS: PackedColorArray = [
	Color(0.1, 0.004, 0.0),
	Color(0.6, 0.04, 0.004),
	Color(1.0, 0.22, 0.015),
	Color(1.0, 0.5, 0.07),
	Color(1.0, 0.85, 0.42),
]
const HEAT_OFFSETS: PackedFloat32Array = [0.0, 0.22, 0.55, 0.85, 1.0]
const FLAME_FADE: PackedColorArray = [
	Color(1, 1, 1, 0), Color(1, 1, 1, 1), Color(1, 1, 1, 0.85), Color(1, 1, 1, 0)
]
const SMOKE_FADE: PackedColorArray = [
	Color(1, 1, 1, 0), Color(1, 1, 1, 0.7), Color(1, 1, 1, 0.4), Color(1, 1, 1, 0)
]
const FADE_OFFSETS: PackedFloat32Array = [0.0, 0.15, 0.65, 1.0]
const LIGHT_COLOR: Color = Color(1.0, 0.48, 0.14)
const LIGHT_HEIGHT: float = 1.5
const LIGHT_ENERGY_PER_CELL: float = 0.35
const MAX_LIGHT_ENERGY: float = 3.0

@export var ground: BlastGround
@export var cell_size: float = 1.0
## Quanto uma célula queima, em média.
@export var burn_seconds: float = 6.0
## Tempo médio para uma célula acesa de vigor cheio acender uma vizinha.
@export var spread_seconds: float = 1.5
## Vigor que passa para a célula acesa por contágio; abaixo de 1 o fogo morre sozinho.
@export var spread_fade: float = 0.8
## 0 sorteia; outro valor repete o mesmo fogo (teste e rede).
@export var random_seed: int = 0

var _columns: int
var _states: PackedByteArray
var _seconds_left: PackedFloat32Array
var _vigor: PackedFloat32Array
var _burning: Dictionary[int, bool] = {}
var _emitter_by_cell: Dictionary[int, Node3D] = {}
var _free_emitters: Array[Node3D] = []
var _random: RandomNumberGenerator = RandomNumberGenerator.new()
var _seconds_since_tick: float = 0.0
var _light: OmniLight3D
var _flame_mesh: QuadMesh
var _smoke_mesh: QuadMesh
var _flame_process: ParticleProcessMaterial
var _smoke_process: ParticleProcessMaterial


func _ready() -> void:
	_columns = ceili(ground.size / cell_size)
	_states.resize(_columns * _columns)
	_seconds_left.resize(_columns * _columns)
	_vigor.resize(_columns * _columns)
	_random.seed = random_seed

	if random_seed == 0:
		_random.randomize()

	_build_particle_resources()
	_add_light()
	set_process(false)


func _process(delta: float) -> void:
	advance(delta)


## Acende a grama a até radius do ponto (terra e carvão ficam de fora).
func ignite(world_center: Vector3, radius: float) -> void:
	var center: Vector2 = _cell_position(world_center)
	var reach: Vector2 = Vector2(radius, radius) / cell_size
	var first: Vector2i = Vector2i((center - reach).floor())
	var area: Rect2i = Rect2i(first, Vector2i((center + reach).ceil()) - first + Vector2i.ONE)

	for offset in area.size.x * area.size.y:
		var cell: Vector2i = _cell_in_area(area, offset)

		if (Vector2(cell) + Vector2(0.5, 0.5)).distance_to(center) * cell_size <= radius:
			_light_cell(cell, 1.0)


## Passa seconds de fogo: queima, espalha e apaga em passos de TICK_SECONDS.
func advance(seconds: float) -> void:
	_seconds_since_tick += seconds

	while _seconds_since_tick >= TICK_SECONDS:
		_seconds_since_tick -= TICK_SECONDS
		_burn_one_tick()


func burning_cell_count() -> int:
	return _burning.size()


func is_burning_at(world_point: Vector3) -> bool:
	var cell: Vector2i = Vector2i(_cell_position(world_point).floor())

	return _has_cell(cell) and _states[_cell_index(cell)] == CellState.BURNING


func _burn_one_tick() -> void:
	var centroid: Vector3 = Vector3.ZERO
	var cells: Array = _burning.keys()

	for cell_index: int in cells:
		centroid += _burn_cell(cell_index)

	if _burning.is_empty():
		_light.visible = false
		set_process(false)
		fire_died.emit()

		return

	_light.visible = true
	_light.light_energy = (
		minf(_burning.size() * LIGHT_ENERGY_PER_CELL, MAX_LIGHT_ENERGY)
		* _random.randf_range(0.8, 1.0)
	)
	_light.global_position = centroid / cells.size() + Vector3.UP * LIGHT_HEIGHT


## Um passo de uma célula acesa; devolve o centro dela (para a luz ficar no meio do fogo).
func _burn_cell(cell_index: int) -> Vector3:
	var cell: Vector2i = _cell_from_index(cell_index)
	var spread_chance: float = TICK_SECONDS / spread_seconds * _vigor[cell_index]
	var neighbor: Vector2i = cell + NEIGHBOR_OFFSETS[_random.randi() % NEIGHBOR_OFFSETS.size()]

	_seconds_left[cell_index] -= TICK_SECONDS

	if _random.randf() < spread_chance:
		_light_cell(neighbor, _vigor[cell_index] * spread_fade)

	if _seconds_left[cell_index] <= 0.0:
		_burn_out(cell_index)

	return _cell_center(cell)


func _light_cell(cell: Vector2i, vigor: float) -> void:
	var cell_index: int = _cell_index(cell)
	var center: Vector3

	if not _has_cell(cell) or _states[cell_index] != CellState.FRESH or vigor < DEAD_VIGOR:
		return

	center = _cell_center(cell)

	if ground.burn_at(center) > FUEL_BURN_LIMIT:
		return

	_states[cell_index] = CellState.BURNING
	_seconds_left[cell_index] = burn_seconds * _random.randf_range(0.7, 1.3)
	_vigor[cell_index] = vigor
	_burning[cell_index] = true
	ground.scorch(center, cell_size * 0.9, FRESH_SCORCH)
	ground.heat(center, cell_size * 0.9, 1.0)
	_serve_with_emitter(cell_index, center)
	set_process(true)


func _burn_out(cell_index: int) -> void:
	var center: Vector3 = _cell_center(_cell_from_index(cell_index))

	_states[cell_index] = CellState.BURNT
	_burning.erase(cell_index)
	ground.scorch(center, cell_size * 1.2, CHARRED_BURN)
	ground.heat(center, cell_size * 0.9, -1.0)

	if _emitter_by_cell.has(cell_index):
		_set_emitting(_emitter_by_cell[cell_index], false)
		_free_emitters.append(_emitter_by_cell[cell_index])
		_emitter_by_cell.erase(cell_index)


## Emissor livre ou, se acabaram, o da célula acesa há mais tempo (a primeira do dicionário).
func _serve_with_emitter(cell_index: int, center: Vector3) -> void:
	var emitter: Node3D
	var oldest_cell: int

	if _free_emitters.is_empty() and _emitter_by_cell.size() < MAX_EMITTERS:
		_free_emitters.append(_make_emitter())

	if _free_emitters.is_empty():
		oldest_cell = _emitter_by_cell.keys()[0]
		_free_emitters.append(_emitter_by_cell[oldest_cell])
		_emitter_by_cell.erase(oldest_cell)

	emitter = _free_emitters.pop_back()
	emitter.global_position = center
	_emitter_by_cell[cell_index] = emitter
	_set_emitting(emitter, true)


func _set_emitting(emitter: Node3D, is_emitting: bool) -> void:
	(emitter.get_child(0) as GPUParticles3D).emitting = is_emitting
	(emitter.get_child(1) as GPUParticles3D).emitting = is_emitting


func _make_emitter() -> Node3D:
	var emitter: Node3D = Node3D.new()

	emitter.add_child(_make_particles(_flame_process, _flame_mesh, 10, 0.9))
	emitter.add_child(_make_particles(_smoke_process, _smoke_mesh, 6, 3.2))
	add_child(emitter)

	return emitter


func _make_particles(
	process: ParticleProcessMaterial, mesh: QuadMesh, amount: int, lifetime: float
) -> GPUParticles3D:
	var particles: GPUParticles3D = GPUParticles3D.new()

	particles.process_material = process
	particles.draw_pass_1 = mesh
	particles.amount = amount
	particles.lifetime = lifetime
	particles.emitting = false
	particles.visibility_aabb = AABB(Vector3(-4, -2, -4), Vector3(8, 12, 8))

	return particles


func _add_light() -> void:
	_light = OmniLight3D.new()
	_light.light_color = LIGHT_COLOR
	_light.omni_range = 12.0
	_light.shadow_enabled = false
	_light.visible = false
	add_child(_light)


func _build_particle_resources() -> void:
	var noise: FastNoiseLite = FastNoiseLite.new()
	var noise_texture: NoiseTexture2D = NoiseTexture2D.new()
	var heat_ramp: GradientTexture1D = _gradient_texture(HEAT_OFFSETS, HEAT_COLORS)
	var flame_material: ShaderMaterial = ShaderMaterial.new()
	var smoke_material: ShaderMaterial = ShaderMaterial.new()

	noise.frequency = 0.012
	noise.fractal_octaves = 4
	noise_texture.width = 256
	noise_texture.height = 256
	noise_texture.seamless = true
	noise_texture.noise = noise
	flame_material.shader = FLAME_SHADER
	flame_material.set_shader_parameter(&"noise_texture", noise_texture)
	flame_material.set_shader_parameter(&"heat_ramp", heat_ramp)
	flame_material.set_shader_parameter(&"energy", 0.8)
	smoke_material.shader = SMOKE_SHADER
	smoke_material.set_shader_parameter(&"noise_texture", noise_texture)
	smoke_material.set_shader_parameter(&"smoke_color", Color(0.09, 0.085, 0.09))
	smoke_material.set_shader_parameter(&"density", 0.6)

	_flame_mesh = QuadMesh.new()
	_flame_mesh.size = Vector2(1.0, 1.5)
	_flame_mesh.center_offset = Vector3(0, 0.6, 0)
	_flame_mesh.material = flame_material
	_smoke_mesh = QuadMesh.new()
	_smoke_mesh.material = smoke_material
	_flame_process = _rising_process(Vector2(1.2, 2.1), Vector2(0.3, 1.1), 2.4)
	_flame_process.scale_curve = _curve_texture(
		[Vector2(0, 0.4), Vector2(0.3, 1), Vector2(1, 0.25)]
	)
	_flame_process.color_ramp = _gradient_texture(FADE_OFFSETS, FLAME_FADE)
	_smoke_process = _rising_process(Vector2(1.8, 3.2), Vector2(0.8, 1.6), 0.9)
	_smoke_process.scale_curve = _curve_texture([Vector2(0, 0.35), Vector2(1, 1)])
	_smoke_process.color_ramp = _gradient_texture(FADE_OFFSETS, SMOKE_FADE)


## Partícula que nasce espalhada pela célula e sobe; scale e speed são (mínimo, máximo).
func _rising_process(scale: Vector2, speed: Vector2, lift: float) -> ParticleProcessMaterial:
	var process: ParticleProcessMaterial = ParticleProcessMaterial.new()

	process.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	process.emission_box_extents = Vector3(cell_size * 0.6, 0.05, cell_size * 0.6)
	process.angle_min = -180.0
	process.angle_max = 180.0
	process.direction = Vector3.UP
	process.spread = 25.0
	process.initial_velocity_min = speed.x
	process.initial_velocity_max = speed.y
	process.gravity = Vector3(0, lift, 0)
	process.scale_min = scale.x
	process.scale_max = scale.y

	return process


func _gradient_texture(offsets: PackedFloat32Array, colors: PackedColorArray) -> GradientTexture1D:
	var gradient: Gradient = Gradient.new()
	var texture: GradientTexture1D = GradientTexture1D.new()

	gradient.offsets = offsets
	gradient.colors = colors
	texture.gradient = gradient

	return texture


func _curve_texture(points: Array[Vector2]) -> CurveTexture:
	var curve: Curve = Curve.new()
	var texture: CurveTexture = CurveTexture.new()

	for point in points:
		curve.add_point(point)

	texture.curve = curve

	return texture


## Posição do ponto do mundo na grade (fração de célula, pode cair fora).
func _cell_position(world_point: Vector3) -> Vector2:
	var local: Vector3 = ground.to_local(world_point)

	return (Vector2(local.x, local.z) + Vector2(ground.size, ground.size) / 2.0) / cell_size


## Centro da célula no mundo, na altura do chão.
func _cell_center(cell: Vector2i) -> Vector3:
	var flat: Vector2 = (
		(Vector2(cell) + Vector2(0.5, 0.5)) * cell_size - Vector2(ground.size, ground.size) / 2.0
	)
	var center: Vector3 = ground.to_global(Vector3(flat.x, 0.0, flat.y))

	center.y = ground.height_at(center)

	return center


func _has_cell(cell: Vector2i) -> bool:
	return Rect2i(0, 0, _columns, _columns).has_point(cell)


func _cell_index(cell: Vector2i) -> int:
	return cell.y * _columns + cell.x


@warning_ignore("integer_division")
func _cell_from_index(cell_index: int) -> Vector2i:
	return Vector2i(cell_index % _columns, cell_index / _columns)


@warning_ignore("integer_division")
func _cell_in_area(area: Rect2i, offset: int) -> Vector2i:
	return area.position + Vector2i(offset % area.size.x, offset / area.size.x)
