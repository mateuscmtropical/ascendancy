class_name WoodenCrate
extends Node3D
## Caixote de tábuas pregadas: cada tábua é um BreakablePiece de madeira. Um soco racha a tábua
## que leva o golpe, um chute abre a caixa; a tampa cai para dentro quando perde o apoio.

const SIZE: float = 0.9
const PLANKS_PER_FACE: int = 2
const THICKNESS: float = 0.05
const JOINT: float = 0.01
const VISIBLE_DISTANCE: float = 120.0
const TINT: Color = Color("b48a58")
const EDGE: Color = Color("7a5438")
## Faces da caixa: lado de fora (normal), eixo ao longo das tábuas e se a face vai de ponta a ponta
## (frente, trás, tampo e fundo cobrem as quinas; as laterais cabem entre elas).
const FACES: Array[Dictionary] = [
	{"normal": Vector3.BACK, "along": Vector3.RIGHT, "full": true},
	{"normal": Vector3.FORWARD, "along": Vector3.RIGHT, "full": true},
	{"normal": Vector3.RIGHT, "along": Vector3.FORWARD, "full": false},
	{"normal": Vector3.LEFT, "along": Vector3.FORWARD, "full": false},
	{"normal": Vector3.UP, "along": Vector3.RIGHT, "full": true},
	{"normal": Vector3.DOWN, "along": Vector3.RIGHT, "full": true},
]


func _ready() -> void:
	var material_by_axis: Dictionary[Vector3, ShaderMaterial] = {
		Vector3.RIGHT: BreakablePiece.make_material(TINT, EDGE, Vector3.RIGHT),
		Vector3.FORWARD: BreakablePiece.make_material(TINT, EDGE, Vector3.BACK),
	}

	for plank_index in FACES.size() * PLANKS_PER_FACE:
		var face: Dictionary = FACES[plank_index / PLANKS_PER_FACE]

		_nail_plank(face, plank_index % PLANKS_PER_FACE, material_by_axis[face.along])


## Uma tábua da face: deitada ao longo de along, lado a lado com as outras na terceira direção.
func _nail_plank(face: Dictionary, slot: int, material: Material) -> void:
	var normal: Vector3 = face.normal
	var along: Vector3 = face.along
	var across: Vector3 = normal.cross(along).abs()
	var inner: float = SIZE - THICKNESS * 2.0
	var length: float = SIZE if face.full else inner
	var width: float = inner / PLANKS_PER_FACE if normal.y == 0.0 else SIZE / PLANKS_PER_FACE
	var offset: float = (slot + 0.5) * width - (inner if normal.y == 0.0 else SIZE) / 2.0
	var size: Vector3 = along.abs() * length + across * (width - JOINT) + normal.abs() * THICKNESS
	var piece: BreakablePiece = BreakablePiece.make_box(size, Destruction.Substance.WOOD, material)
	var view: MeshInstance3D = piece.get_child(1) as MeshInstance3D

	piece.position = (Vector3.UP * SIZE / 2.0 + normal * (SIZE - THICKNESS) / 2.0 + across * offset)
	view.visibility_range_end = VISIBLE_DISTANCE
	add_child(piece)
