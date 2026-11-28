class_name BreakablePiece
extends RigidBody3D
## Pedaço do cenário parado no lugar (congelado, colide como parede) até um impacto com mais
## energia do que ele aguenta. Solto, voa com a física, larga quem estava apoiado nele, bate no
## chão com som, dorme parado e some depois de um tempo. Solto, ainda pode ser chutado.

signal broke_free(piece: BreakablePiece)

const FROZEN_LAYERS: int = Destruction.WORLD_LAYER | Destruction.BREAKABLE_LAYER
const LOOSE_LAYERS: int = Destruction.DEBRIS_LAYER | Destruction.BREAKABLE_LAYER
const LOOSE_MASK: int = (
	Destruction.WORLD_LAYER | Destruction.PLAYER_LAYER | Destruction.DEBRIS_LAYER
)
## Velocidade de saída: raiz da energia que sobrou (energia cinética cresce com o quadrado).
const LAUNCH_SPEED_PER_ROOT_ENERGY: float = 0.7
## Quem quebra sempre sai com pelo menos isso: peça que só se solta parece descolar, não quebrar.
const MIN_LAUNCH_SPEED: float = 2.5
const MAX_LAUNCH_SPEED: float = 11.0
## Giro de quem sai voando, em rad/s por m/s de saída.
const SPIN_PER_SPEED: float = 0.6
## Entulho solto que leva outro golpe: empurrado com esta fração da energia que chega.
const LOOSE_PUSH_SHARE: float = 0.5
## Quanto tempo o pedaço solto fica no chão antes de sumir, e quanto leva sumindo.
const LOOSE_SECONDS: float = 30.0
const FADE_SECONDS: float = 0.8
## Batida no chão abaixo disso não faz som.
const KNOCK_SPEED: float = 1.5
## Energia equivalente do som de uma batida, por m/s.
const KNOCK_ENERGY_PER_SPEED: float = 4.0
const KNOCKS_PER_PIECE: int = 2
## Fatia logo acima do pedaço onde procura quem está sentado nele.
const SUPPORT_PROBE_HEIGHT: float = 0.06
const SUPPORT_PROBE_INSET: float = 0.04
## Quanto o casco de um pedaço pré-fraturado encolhe em cada canto.
const HULL_SHRINK: float = 0.008

const BLOCK_SHADER: Shader = preload("res://art/shaders/breakable_block.gdshader")

static var _box_meshes: Dictionary[String, BoxMesh] = {}

@export var substance: Destruction.Substance = Destruction.Substance.WOOD
## Mais firme que o material comum (porta de tábua grossa): multiplica a resistência.
@export var toughness: float = 1.0

var is_loose: bool = false
## Peças pregadas juntas (tábuas de uma porta): quando uma quebra, todas saem com ela.
var linked_pieces: Array[BreakablePiece] = []

var _local_bounds: AABB = AABB(Vector3(-0.5, -0.5, -0.5), Vector3.ONE)
var _knocks_left: int = KNOCKS_PER_PIECE
var _is_fading: bool = false


func _ready() -> void:
	freeze_mode = RigidBody3D.FREEZE_MODE_STATIC
	freeze = true
	collision_layer = FROZEN_LAYERS
	collision_mask = 0


func _exit_tree() -> void:
	if is_loose:
		Destruction.forget_loose(self)


## Caixa pronta (colisão + malha) de um material; malhas da mesma medida e material são a mesma.
static func make_box(
	size: Vector3, piece_substance: Destruction.Substance, material: Material, firmness: float = 1.0
) -> BreakablePiece:
	var piece: BreakablePiece = BreakablePiece.new()
	var collision: CollisionShape3D = CollisionShape3D.new()
	var shape: BoxShape3D = BoxShape3D.new()
	var view: MeshInstance3D = MeshInstance3D.new()

	shape.size = size
	collision.shape = shape
	view.mesh = _shared_box_mesh(size, material)
	piece.substance = piece_substance
	piece.toughness = firmness
	piece.mass = size.x * size.y * size.z * 600.0
	piece.set_bounds(AABB(-size / 2.0, size))
	piece.add_child(collision)
	piece.add_child(view)

	return piece


## Peça de um modelo pré-fraturado: a malha vira filha do corpo, no mesmo lugar, e a colisão é o
## casco convexo dela (os pedaços do corte de Voronoi já são convexos).
static func make_from_mesh(
	view: MeshInstance3D, piece_substance: Destruction.Substance, firmness: float = 1.0
) -> BreakablePiece:
	var piece: BreakablePiece = BreakablePiece.new()
	var collision: CollisionShape3D = CollisionShape3D.new()
	var bounds: AABB = view.mesh.get_aabb()

	collision.shape = _shrunk_hull(view.mesh, bounds.get_center())
	piece.transform = view.transform
	piece.substance = piece_substance
	piece.toughness = firmness
	piece.mass = maxf(bounds.size.x * bounds.size.y * bounds.size.z * 600.0, 1.0)
	piece.set_bounds(bounds)
	view.get_parent().remove_child(view)
	view.transform = Transform3D.IDENTITY
	piece.add_child(collision)
	piece.add_child(view)

	return piece


## Casco convexo da malha com cada canto puxado HULL_SHRINK para o centro: pedaços cortados
## encostam exatamente no vizinho, e sem folga o atrito prende quem se solta (tábua no batente).
static func _shrunk_hull(mesh: Mesh, center: Vector3) -> ConvexPolygonShape3D:
	var hull: ConvexPolygonShape3D = mesh.create_convex_shape(true, false)
	var points: PackedVector3Array = hull.points

	for index in points.size():
		points[index] = points[index].move_toward(center, HULL_SHRINK)

	hull.points = points

	return hull


## Material dos blocos e tábuas: cor, quina mais escura e, na madeira, veio ao longo de grain_axis.
static func make_material(
	base_color: Color, edge_color: Color, grain_axis: Vector3 = Vector3.ZERO
) -> ShaderMaterial:
	var material: ShaderMaterial = ShaderMaterial.new()

	material.shader = BLOCK_SHADER
	material.set_shader_parameter(&"base_color", base_color)
	material.set_shader_parameter(&"edge_color", edge_color)

	if not grain_axis.is_zero_approx():
		material.set_shader_parameter(&"grain_axis", grain_axis)
		material.set_shader_parameter(&"grain_strength", 0.55)
		material.set_shader_parameter(&"blotch_strength", 0.06)

	return material


## Caixa do pedaço no espaço dele: dela sai o ponto mais perto de um golpe.
func set_bounds(bounds: AABB) -> void:
	_local_bounds = bounds


func resistance() -> float:
	return Destruction.RESISTANCE_BY_SUBSTANCE[substance] * toughness


## Ponto do pedaço mais perto de point.
func closest_point_to(point: Vector3) -> Vector3:
	var local_point: Vector3 = global_transform.affine_inverse() * point
	var clamped: Vector3 = local_point.clamp(_local_bounds.position, _local_bounds.end)

	return global_transform * clamped


## Energia do impacto que chega neste pedaço (no ponto dele mais perto do golpe).
func energy_from(impact: Impact) -> float:
	var center: Vector3 = global_transform * _local_bounds.get_center()
	var strike_point: Vector3 = impact.nearest_point_to(center)

	return impact.energy_at(closest_point_to(strike_point))


## Solta o pedaço se a energia que chega passa do que ele aguenta; devolve se soltou. Entulho já
## solto só é empurrado.
func take_impact(impact: Impact) -> bool:
	var energy: float = energy_from(impact)
	var center: Vector3 = global_transform * _local_bounds.get_center()
	var push: Vector3 = impact.push_direction_at(center)

	if is_loose:
		_launch(push, energy * LOOSE_PUSH_SHARE)

		return false

	if energy <= resistance():
		return false

	break_free()
	_launch(push, energy - resistance())

	for piece in linked_pieces:
		piece.burst_along(push, energy - resistance())

	return true


## Sai junto de uma peça pregada nela que quebrou, empurrada para o mesmo lado.
func burst_along(push: Vector3, spare_energy: float) -> void:
	if is_loose:
		return

	break_free()
	_launch(push, spare_energy)


## Desprende o pedaço sem empurrão: a física decide se cai ou fica equilibrado.
func break_free() -> void:
	if is_loose:
		return

	is_loose = true
	freeze = false
	collision_layer = LOOSE_LAYERS
	collision_mask = LOOSE_MASK
	contact_monitor = true
	max_contacts_reported = 2
	body_entered.connect(_on_body_entered)
	Destruction.register_loose(self)
	get_tree().create_timer(LOOSE_SECONDS).timeout.connect(fade_out)
	broke_free.emit(self)


## Solta os pedaços ainda presos sentados neste que ficaram sem nenhum outro apoio e os devolve.
func release_pieces_on_top(world: World3D) -> Array[BreakablePiece]:
	var released: Array[BreakablePiece] = []

	for piece in _frozen_pieces_in_slab(world, _local_bounds.end.y + SUPPORT_PROBE_HEIGHT / 2.0):
		if not piece.rests_on_frozen_piece(world):
			piece.break_free()
			released.append(piece)

	return released


## Se ainda tem algum pedaço preso logo embaixo (verga apoiada na outra ponta, telhado na outra
## parede): aí fica; só cai o que perdeu todo o apoio.
func rests_on_frozen_piece(world: World3D) -> bool:
	var below: float = _local_bounds.position.y - SUPPORT_PROBE_HEIGHT / 2.0

	return not _frozen_pieces_in_slab(world, below).is_empty()


## Pedaços presos que tocam uma fatia fina na altura height (no espaço do pedaço), do tamanho da
## base dele.
func _frozen_pieces_in_slab(world: World3D, height: float) -> Array[BreakablePiece]:
	var query: PhysicsShapeQueryParameters3D = PhysicsShapeQueryParameters3D.new()
	var probe: BoxShape3D = BoxShape3D.new()
	var center: Vector3 = _local_bounds.get_center()
	var found: Array[BreakablePiece] = []
	var hits: Array[Dictionary]

	probe.size = Vector3(
		maxf(_local_bounds.size.x - SUPPORT_PROBE_INSET * 2.0, 0.01),
		SUPPORT_PROBE_HEIGHT,
		maxf(_local_bounds.size.z - SUPPORT_PROBE_INSET * 2.0, 0.01)
	)
	query.shape = probe
	query.transform = (
		global_transform * Transform3D(Basis.IDENTITY, Vector3(center.x, height, center.z))
	)
	query.collision_mask = Destruction.BREAKABLE_LAYER
	query.exclude = [get_rid()]
	hits = world.direct_space_state.intersect_shape(query, Destruction.MAX_QUERY_RESULTS)

	for hit in hits:
		var piece: BreakablePiece = hit.collider as BreakablePiece

		if piece != null and not piece.is_loose:
			found.append(piece)

	return found


## Some encolhendo (sem colidir) e sai da cena.
func fade_out() -> void:
	var tween: Tween

	if _is_fading:
		return

	_is_fading = true
	collision_layer = 0
	collision_mask = 0
	tween = create_tween().set_parallel()

	# Só a malha encolhe: forma de colisão com escala zero é inválida no Jolt.
	for child in get_children():
		if child is VisualInstance3D:
			tween.tween_property(child, "scale", Vector3.ONE * 0.01, FADE_SECONDS)

	tween.chain().tween_callback(queue_free)


func _launch(direction: Vector3, spare_energy: float) -> void:
	var root_energy: float = sqrt(maxf(spare_energy, 0.0))
	var speed: float = minf(
		MIN_LAUNCH_SPEED + root_energy * LAUNCH_SPEED_PER_ROOT_ENERGY, MAX_LAUNCH_SPEED
	)
	# Tomba para a frente, para onde vai: porta arrombada cai para dentro, não volta no batente.
	var spin_axis: Vector3 = Vector3.UP.cross(direction)

	if spin_axis.length_squared() < 0.0001:
		spin_axis = Vector3.RIGHT

	sleeping = false
	apply_central_impulse(direction * speed * mass)
	angular_velocity += spin_axis.normalized() * speed * SPIN_PER_SPEED


func _on_body_entered(_body: Node) -> void:
	var speed: float = linear_velocity.length()

	if _knocks_left <= 0 or speed < KNOCK_SPEED:
		return

	_knocks_left -= 1
	Destruction.play_knock(substance, global_position, speed * KNOCK_ENERGY_PER_SPEED, self)


static func _shared_box_mesh(size: Vector3, material: Material) -> BoxMesh:
	var key: String = "%s|%d" % [size, material.get_instance_id()]
	var mesh: BoxMesh = _box_meshes.get(key)

	if mesh != null:
		return mesh

	mesh = BoxMesh.new()
	mesh.size = size
	mesh.material = material
	_box_meshes[key] = mesh

	return mesh
