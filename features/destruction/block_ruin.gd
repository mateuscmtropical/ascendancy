class_name BlockRuin
extends Node3D
## Ruína de alvenaria seca montada bloco a bloco: cada bloco é um BreakablePiece de pedra, preso
## até um impacto forte; o que estava apoiado nele cai junto. Paredes em fiadas desencontradas com
## o topo desgastado, vãos com verga, colunas de tambores com viga por cima e porta de tábua.
## A planta vem de PLANS; a mesma planta monta sempre a mesma ruína.

enum Plan { TEMPLE, GATE }

const COURSE_HEIGHT: float = 0.42
const BLOCK_LENGTH: float = 0.9
const WALL_DEPTH: float = 0.6
## Bloco menor que isso numa ponta de fiada vira parte do vizinho.
const MIN_BLOCK_LENGTH: float = 0.3
## Folga entre blocos: encostados, sem se empurrar quando soltam.
const JOINT: float = 0.006
const DRUM_SIZE: Vector3 = Vector3(0.62, 0.5, 0.62)
const PLANK_WIDTH: float = 0.24
const PLANK_THICKNESS: float = 0.08
## Porta de tábua grossa: só um chute voador arrebenta (Destruction, UnarmedFighter.ENERGY_BY_MOVE).
const DOOR_TOUGHNESS: float = 4.7
## Folga da porta sob a verga: a porta não sustenta a verga, então arrombar não a derruba.
const DOOR_CLEARANCE: float = 0.1
## Longe assim a ruína some (fica fora da vista da cidade).
const VISIBLE_DISTANCE: float = 160.0
const STONE_TINTS: Array[Color] = [
	Color("e9dcc6"),
	Color("d8c9b0"),
	Color("cbbba0"),
]
## Quina do bloco: a pedra de sombra fria da paleta, puxada para o tom do bloco.
const STONE_EDGE: Color = Color("a59a8c")
const DOOR_TINT: Color = Color("8b5a3c")
const DOOR_EDGE: Color = Color("5e3b27")
## Parede: de onde a onde (x, z) no chão, fiadas, quantas fiadas o topo perde no máximo e vãos
## (meio ao longo da parede, largura, fiadas de altura, se leva porta).
const PLANS: Dictionary[Plan, Dictionary] = {
	Plan.TEMPLE:
	{
		"walls":
		[
			{
				"from": Vector2(-4.5, -3.0),
				"to": Vector2(4.5, -3.0),
				"courses": 9,
				"ragged": 3,
				"openings": [{"at": 4.5, "width": 1.8, "courses": 5, "door": false}],
			},
			{
				"from": Vector2(-4.8, -2.7),
				"to": Vector2(-4.8, 3.0),
				"courses": 7,
				"ragged": 4,
				"openings": [{"at": 2.7, "width": 0.9, "courses": 3, "door": false}],
			},
			{
				"from": Vector2(4.8, -2.7),
				"to": Vector2(4.8, 3.0),
				"courses": 6,
				"ragged": 4,
				"openings": [],
			},
		],
		"columns": [Vector2(-3.0, 3.6), Vector2(-1.0, 3.6), Vector2(1.0, 3.6), Vector2(3.0, 3.6)],
		"column_drums": 7,
		"beams": [[0, 1], [2, 3]],
	},
	Plan.GATE:
	{
		"walls":
		[
			{
				"from": Vector2(-3.6, 0.0),
				"to": Vector2(3.6, 0.0),
				"courses": 7,
				"ragged": 2,
				"openings": [{"at": 3.6, "width": 1.2, "courses": 5, "door": true}],
			},
		],
		"columns": [],
		"column_drums": 0,
		"beams": [],
	},
}

@export var plan: Plan = Plan.TEMPLE

var _stone_materials: Array[ShaderMaterial] = []
var _door_material: ShaderMaterial


func _ready() -> void:
	var layout: Dictionary = PLANS[plan]
	var walls: Array = layout.walls

	_make_materials()

	for wall_index in walls.size():
		_lay_wall(wall_index, walls[wall_index])

	_raise_columns(layout.columns, layout.column_drums, layout.beams)


## Quanto o topo desgastado tira da parede neste ponto: ondula ao longo dela, sem sorteio.
static func ragged_drop(ragged: int, along: float, wall_index: int) -> int:
	var wave: float = 0.5 + 0.5 * sin(along * 1.3 + wall_index * 2.1) * cos(along * 0.55 + 0.7)

	return int(round(ragged * wave))


## Trechos de uma fiada (início e fim ao longo da parede) sem os vãos que cortam essa fiada.
static func course_spans(wall_length: float, course: int, openings: Array) -> Array[Vector2]:
	var spans: Array[Vector2] = [Vector2(0.0, wall_length)]

	for opening in openings:
		var gap: float = _gap_width(opening, course)

		if gap > 0.0:
			spans = _cut_spans(spans, opening.at - gap / 2.0, opening.at + gap / 2.0)

	return spans


## Quanto do vão uma fiada deixa aberto: o vão em si embaixo, o lugar da verga na fiada dela.
static func _gap_width(opening: Dictionary, course: int) -> float:
	if course < opening.courses:
		return opening.width

	if course == opening.courses:
		return opening.width + BLOCK_LENGTH

	return 0.0


## Pontos onde os blocos de um trecho se dividem, desencontrados fiada sim, fiada não.
static func block_breaks(span: Vector2, course: int) -> PackedFloat32Array:
	var breaks: PackedFloat32Array = PackedFloat32Array([span.x])
	var cut: float = ceilf(span.x / BLOCK_LENGTH) * BLOCK_LENGTH + (course % 2) * BLOCK_LENGTH / 2.0

	while cut < span.y - MIN_BLOCK_LENGTH:
		if cut > span.x + MIN_BLOCK_LENGTH:
			breaks.append(cut)

		cut += BLOCK_LENGTH

	breaks.append(span.y)

	return breaks


static func _cut_spans(spans: Array[Vector2], cut_start: float, cut_end: float) -> Array[Vector2]:
	var kept: Array[Vector2] = []

	for span in spans:
		if cut_start > span.x:
			kept.append(Vector2(span.x, minf(span.y, cut_start)))

		if cut_end < span.y:
			kept.append(Vector2(maxf(span.x, cut_end), span.y))

	return kept


func _make_materials() -> void:
	for tint in STONE_TINTS:
		_stone_materials.append(BreakablePiece.make_material(tint, STONE_EDGE))

	_door_material = BreakablePiece.make_material(DOOR_TINT, DOOR_EDGE, Vector3.UP)


func _lay_wall(wall_index: int, wall: Dictionary) -> void:
	var start: Vector2 = wall.from
	var length: float = start.distance_to(wall.to)
	var rows: Array[Dictionary] = []

	for course in int(wall.courses):
		rows.append({"course": course, "spans": course_spans(length, course, wall.openings)})

	for row in rows:
		_lay_course(wall_index, wall, row.course, row.spans)

	for opening in wall.openings:
		_set_lintel(wall, opening)


func _lay_course(wall_index: int, wall: Dictionary, course: int, spans: Array[Vector2]) -> void:
	var breaks: PackedFloat32Array = PackedFloat32Array()

	for span in spans:
		breaks = block_breaks(span, course)
		_lay_blocks(wall_index, wall, course, breaks)


func _lay_blocks(
	wall_index: int, wall: Dictionary, course: int, breaks: PackedFloat32Array
) -> void:
	var courses: int = wall.courses

	for index in breaks.size() - 1:
		var block_start: float = breaks[index]
		var block_end: float = breaks[index + 1]
		var middle: float = (block_start + block_end) / 2.0
		var is_standing: bool = course < courses - ragged_drop(wall.ragged, middle, wall_index)

		if is_standing:
			_place_wall_block(wall, middle, block_end - block_start, course, wall_index + index)


func _place_wall_block(
	wall: Dictionary, along: float, length: float, course: int, tint: int
) -> void:
	var size: Vector3 = Vector3(length - JOINT, COURSE_HEIGHT - JOINT, WALL_DEPTH)
	var height: float = course * COURSE_HEIGHT + COURSE_HEIGHT / 2.0

	_place_on_wall(wall, along, height, size, Destruction.Substance.STONE, _stone_of(tint + course))


## Verga por cima do vão (um bloco só, apoiado dos dois lados) e porta de tábuas se houver.
func _set_lintel(wall: Dictionary, opening: Dictionary) -> void:
	var length: float = opening.width + BLOCK_LENGTH
	var height: float = opening.courses * COURSE_HEIGHT + COURSE_HEIGHT / 2.0
	var size: Vector3 = Vector3(length - JOINT, COURSE_HEIGHT - JOINT, WALL_DEPTH)
	var is_under_top: bool = opening.courses < wall.courses

	if is_under_top:
		_place_on_wall(wall, opening.at, height, size, Destruction.Substance.STONE, _stone_of(0))

	if opening.door:
		_hang_door(wall, opening)


func _hang_door(wall: Dictionary, opening: Dictionary) -> void:
	var plank_count: int = int(floor(opening.width / PLANK_WIDTH))
	var door_height: float = opening.courses * COURSE_HEIGHT - DOOR_CLEARANCE
	var size: Vector3 = Vector3(PLANK_WIDTH - JOINT, door_height, PLANK_THICKNESS)
	var first: float = opening.at - (plank_count - 1) * PLANK_WIDTH / 2.0
	var planks: Array[BreakablePiece] = []

	for index in plank_count:
		var plank: BreakablePiece = _place_on_wall(
			wall,
			first + index * PLANK_WIDTH,
			door_height / 2.0,
			size,
			Destruction.Substance.WOOD,
			_door_material
		)

		plank.toughness = DOOR_TOUGHNESS
		plank.linked_pieces = planks
		planks.append(plank)


func _place_on_wall(
	wall: Dictionary,
	along: float,
	height: float,
	size: Vector3,
	substance: Destruction.Substance,
	material: Material
) -> BreakablePiece:
	var start: Vector2 = wall.from
	var direction: Vector2 = (wall.to - start).normalized()
	var spot: Vector2 = start + direction * along
	var piece: BreakablePiece = BreakablePiece.make_box(size, substance, material)

	piece.position = Vector3(spot.x, height, spot.y)
	piece.rotation.y = -direction.angle()
	_add_piece(piece)

	return piece


func _raise_columns(columns: Array, drums: int, beams: Array) -> void:
	for drum_index in columns.size() * drums:
		var column_index: int = drum_index / drums
		var drum: int = drum_index % drums
		var spot: Vector2 = columns[column_index]
		var piece: BreakablePiece = BreakablePiece.make_box(
			DRUM_SIZE - Vector3.ONE * JOINT,
			Destruction.Substance.STONE,
			_stone_of(column_index + drum)
		)

		piece.position = Vector3(spot.x, drum * DRUM_SIZE.y + DRUM_SIZE.y / 2.0, spot.y)
		_add_piece(piece)

	for beam in beams:
		_span_beam(columns[beam[0]], columns[beam[1]], drums)


func _span_beam(from: Vector2, to: Vector2, drums: int) -> void:
	var length: float = from.distance_to(to) + DRUM_SIZE.x
	var size: Vector3 = Vector3(length, COURSE_HEIGHT, DRUM_SIZE.z + 0.1)
	var middle: Vector2 = (from + to) / 2.0
	var piece: BreakablePiece = BreakablePiece.make_box(
		size, Destruction.Substance.STONE, _stone_of(1)
	)

	piece.position = Vector3(middle.x, drums * DRUM_SIZE.y + COURSE_HEIGHT / 2.0, middle.y)
	piece.rotation.y = -(to - from).angle()
	_add_piece(piece)


func _add_piece(piece: BreakablePiece) -> void:
	var view: MeshInstance3D = piece.get_child(1) as MeshInstance3D

	view.visibility_range_end = VISIBLE_DISTANCE
	add_child(piece)


func _stone_of(index: int) -> ShaderMaterial:
	return _stone_materials[posmod(index, _stone_materials.size())]
