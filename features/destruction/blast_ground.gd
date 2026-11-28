class_name BlastGround
extends Node3D
## Pedaço quadrado de chão que explosão e fogo deformam e queimam: uma malha plana com a altura de
## cada vértice numa textura (cratera) e uma máscara de queimado (grama -> terra -> carvão) com a
## brasa acesa no segundo canal, desenhadas por art/shaders/blast_ground.gdshader. A colisão é um
## HeightMapShape3D de 1 m por célula na camada do mundo, refeito a cada cratera.
## Os pontos da API são do mundo; a altura (y) deles é ignorada.

const GROUND_SHADER: Shader = preload("res://art/shaders/blast_ground.gdshader")
const GRASS_TEXTURE: Texture2D = preload("res://art/town/textures/T_Lawn_BaseColor.png")
const SOIL_TEXTURE: Texture2D = preload("res://art/town/textures/T_FarmSoil_BaseColor.png")
## Máscara de queimado: a partir daqui é terra exposta (não pega fogo) e aqui é carvão.
const SOIL_BURN: float = 0.5
const CHARCOAL_BURN: float = 1.0
## A borda levantada da cratera vai até este múltiplo do raio.
const RIM_REACH: float = 1.6
const RIM_HEIGHT_SHARE: float = 0.22
const ROUGHNESS_SHARE: float = 0.07
## A máscara muda toda hora enquanto o fogo anda: sobe para a GPU no máximo a cada tanto.
const MASK_UPLOAD_SECONDS: float = 0.1
const MASK_CHANNELS: int = 2
const BURN_CHANNEL: int = 0
const HEAT_CHANNEL: int = 1
const CULL_HEIGHT: float = 16.0

## Lado do quadrado, em metros inteiros (a colisão tem uma célula por metro).
@export var size: float = 48.0
@export var vertices_per_meter: int = 4

var _samples_per_side: int
var _heights: PackedFloat32Array
var _mask: PackedByteArray
var _height_texture: ImageTexture
var _mask_texture: ImageTexture
var _collision_shape: HeightMapShape3D
var _is_mask_dirty: bool = false
var _seconds_since_upload: float = 0.0


func _ready() -> void:
	_samples_per_side = roundi(size) * vertices_per_meter + 1
	_heights.resize(_samples_per_side * _samples_per_side)
	_mask.resize(_samples_per_side * _samples_per_side * MASK_CHANNELS)
	_height_texture = ImageTexture.create_from_image(_height_image())
	_mask_texture = ImageTexture.create_from_image(_mask_image())

	_add_mesh()
	_add_collision()
	set_process(false)


func _process(delta: float) -> void:
	_seconds_since_upload += delta

	if _seconds_since_upload < MASK_UPLOAD_SECONDS:
		return

	_mask_texture.update(_mask_image())
	_seconds_since_upload = 0.0
	_is_mask_dirty = false
	set_process(false)


## Cava uma bacia de raio radius e fundura depth, com a borda levantada em volta, e deixa terra
## revolvida (chamuscada no meio) na máscara.
func dig_crater(world_center: Vector3, radius: float, depth: float) -> void:
	var center: Vector2 = _sample_position(world_center)
	var reach: float = radius * RIM_REACH
	var area: Rect2i = _sample_area(center, reach)

	for offset in area.size.x * area.size.y:
		var sample: Vector2i = _sample_in_area(area, offset)
		var index: int = _sample_index(sample)
		var along: float = Vector2(sample).distance_to(center) / (radius * vertices_per_meter)
		var roughness: float = _roughness_at(sample) * (1.0 - smoothstep(1.0, RIM_REACH, along))

		_heights[index] += depth * (_crater_profile(along) + roughness * ROUGHNESS_SHARE)
		_raise_mask(index, BURN_CHANNEL, _crater_burn(along))

	_height_texture.update(_height_image())
	_sync_collision()
	_mark_mask_dirty()


## Queima o chão em volta do ponto até amount (0 grama, 0,5 terra, 1 carvão), mais fraco na borda;
## nunca desfaz o que já estava mais queimado.
func scorch(world_center: Vector3, radius: float, amount: float) -> void:
	_paint(world_center, radius, BURN_CHANNEL, amount, false)


## Acende (amount > 0) ou apaga (amount < 0) a brasa do chão em volta do ponto.
func heat(world_center: Vector3, radius: float, amount: float) -> void:
	_paint(world_center, radius, HEAT_CHANNEL, amount, true)


## Quanto o ponto está queimado, 0 a 1 (0 também fora do chão).
func burn_at(world_point: Vector3) -> float:
	var sample: Vector2i = Vector2i(_sample_position(world_point).round())

	if not _has_sample(sample):
		return 0.0

	return _mask[_sample_index(sample) * MASK_CHANNELS + BURN_CHANNEL] / 255.0


## Põe a amostra mais perto do ponto exatamente em amount.
func set_burn(world_point: Vector3, amount: float) -> void:
	var sample: Vector2i = Vector2i(_sample_position(world_point).round())

	if not _has_sample(sample):
		return

	_mask[_sample_index(sample) * MASK_CHANNELS + BURN_CHANNEL] = _to_byte(amount)
	_mark_mask_dirty()


## Altura do chão (y do mundo) embaixo do ponto.
func height_at(world_point: Vector3) -> float:
	var position_in_samples: Vector2 = _sample_position(world_point)
	var limit: float = _samples_per_side - 1.001
	var clamped: Vector2 = position_in_samples.clamp(Vector2.ZERO, Vector2(limit, limit))
	var corner: Vector2i = Vector2i(clamped.floor())
	var blend: Vector2 = clamped - Vector2(corner)
	var index: int = _sample_index(corner)
	var near: float = lerpf(_heights[index], _heights[index + 1], blend.x)
	var far_index: int = index + _samples_per_side
	var far: float = lerpf(_heights[far_index], _heights[far_index + 1], blend.x)

	return global_position.y + lerpf(near, far, blend.y)


## O ponto cai dentro do quadrado?
func covers(world_point: Vector3) -> bool:
	return _has_sample(Vector2i(_sample_position(world_point).round()))


func _add_mesh() -> void:
	var mesh: PlaneMesh = PlaneMesh.new()
	var material: ShaderMaterial = ShaderMaterial.new()
	var instance: MeshInstance3D = MeshInstance3D.new()
	var half: float = size / 2.0

	material.shader = GROUND_SHADER
	material.set_shader_parameter(&"height_texture", _height_texture)
	material.set_shader_parameter(&"mask_texture", _mask_texture)
	material.set_shader_parameter(&"grass_texture", GRASS_TEXTURE)
	material.set_shader_parameter(&"soil_texture", SOIL_TEXTURE)
	material.set_shader_parameter(&"sample_count", float(_samples_per_side))
	material.set_shader_parameter(&"meters_per_sample", 1.0 / vertices_per_meter)
	mesh.size = Vector2(size, size)
	mesh.subdivide_width = _samples_per_side - 2
	mesh.subdivide_depth = _samples_per_side - 2
	mesh.material = material
	instance.name = "Surface"
	instance.mesh = mesh
	instance.custom_aabb = AABB(
		Vector3(-half, -CULL_HEIGHT / 2.0, -half), Vector3(size, CULL_HEIGHT, size)
	)
	add_child(instance)


func _add_collision() -> void:
	var body: StaticBody3D = StaticBody3D.new()
	var shape_node: CollisionShape3D = CollisionShape3D.new()
	var cells_per_side: int = roundi(size) + 1

	_collision_shape = HeightMapShape3D.new()
	_collision_shape.map_width = cells_per_side
	_collision_shape.map_depth = cells_per_side
	shape_node.shape = _collision_shape
	body.name = "Body"
	body.collision_layer = Destruction.WORLD_LAYER
	body.collision_mask = 0
	body.add_child(shape_node)
	add_child(body)
	_sync_collision()


@warning_ignore("integer_division")
func _sync_collision() -> void:
	var cells_per_side: int = _collision_shape.map_width
	var cell_heights: PackedFloat32Array = PackedFloat32Array()

	cell_heights.resize(cells_per_side * cells_per_side)

	for cell_index in cell_heights.size():
		var cell: Vector2i = Vector2i(cell_index % cells_per_side, cell_index / cells_per_side)

		cell_heights[cell_index] = _heights[_sample_index(cell * vertices_per_meter)]

	_collision_shape.map_data = cell_heights


func _paint(
	world_center: Vector3, radius: float, channel: int, amount: float, is_added: bool
) -> void:
	var center: Vector2 = _sample_position(world_center)
	var area: Rect2i = _sample_area(center, radius)

	for offset in area.size.x * area.size.y:
		var sample: Vector2i = _sample_in_area(area, offset)
		var index: int = _sample_index(sample)
		var along: float = Vector2(sample).distance_to(center) / (radius * vertices_per_meter)
		var strength: float = amount * (1.0 - smoothstep(0.55, 1.0, along))

		if is_added:
			_add_to_mask(index, channel, strength)
		else:
			_raise_mask(index, channel, strength)

	_mark_mask_dirty()


## Perfil da cratera em frações da fundura: bacia até o raio (along = 1), borda levantada em volta.
func _crater_profile(along: float) -> float:
	var bowl: float = -pow(maxf(1.0 - along * along, 0.0), 2.0)
	var rim_along: float = clampf((along - 0.7) / (RIM_REACH - 0.7), 0.0, 1.0)
	var rim: float = RIM_HEIGHT_SHARE * pow(sin(PI * rim_along), 2.0)

	return bowl + rim


## Queimado que a cratera deixa: chamuscado no meio, terra revolvida até passar a borda.
func _crater_burn(along: float) -> float:
	var charred: float = lerpf(0.9, SOIL_BURN + 0.05, smoothstep(0.15, 0.9, along))

	return charred * (1.0 - smoothstep(1.25, RIM_REACH, along))


## -1 a 1, fixo por amostra: torrões no fundo e na borda em vez de uma tigela lisa.
func _roughness_at(sample: Vector2i) -> float:
	var coarse: Vector2 = Vector2(sample) / (vertices_per_meter * 0.9)

	return sin(coarse.x * 2.3 + sin(coarse.y * 1.7) * 2.0) * cos(coarse.y * 2.9 + coarse.x * 0.6)


func _raise_mask(index: int, channel: int, amount: float) -> void:
	var byte_index: int = index * MASK_CHANNELS + channel

	_mask[byte_index] = maxi(_mask[byte_index], _to_byte(amount))


func _add_to_mask(index: int, channel: int, amount: float) -> void:
	var byte_index: int = index * MASK_CHANNELS + channel

	_mask[byte_index] = clampi(_mask[byte_index] + roundi(amount * 255.0), 0, 255)


func _mark_mask_dirty() -> void:
	if _is_mask_dirty:
		return

	_is_mask_dirty = true
	set_process(true)


## Posição do ponto do mundo na grade de amostras (fração de amostra, pode cair fora).
func _sample_position(world_point: Vector3) -> Vector2:
	var local: Vector3 = to_local(world_point)

	return (Vector2(local.x, local.z) + Vector2(size, size) / 2.0) * vertices_per_meter


## Amostras a até reach metros do centro, sem a fileira da borda (que fica na altura zero para
## emendar com o chão em volta).
func _sample_area(center: Vector2, reach: float) -> Rect2i:
	var reach_in_samples: Vector2 = Vector2(reach, reach) * vertices_per_meter
	var first: Vector2i = Vector2i((center - reach_in_samples).floor())
	var last: Vector2i = Vector2i((center + reach_in_samples).ceil())
	var inside: Rect2i = Rect2i(1, 1, _samples_per_side - 2, _samples_per_side - 2)

	return Rect2i(first, last - first + Vector2i.ONE).intersection(inside)


@warning_ignore("integer_division")
func _sample_in_area(area: Rect2i, offset: int) -> Vector2i:
	return area.position + Vector2i(offset % area.size.x, offset / area.size.x)


func _sample_index(sample: Vector2i) -> int:
	return sample.y * _samples_per_side + sample.x


func _has_sample(sample: Vector2i) -> bool:
	return Rect2i(0, 0, _samples_per_side, _samples_per_side).has_point(sample)


func _to_byte(amount: float) -> int:
	return clampi(roundi(amount * 255.0), 0, 255)


func _height_image() -> Image:
	return Image.create_from_data(
		_samples_per_side, _samples_per_side, false, Image.FORMAT_RF, _heights.to_byte_array()
	)


func _mask_image() -> Image:
	return Image.create_from_data(
		_samples_per_side, _samples_per_side, false, Image.FORMAT_RG8, _mask
	)
