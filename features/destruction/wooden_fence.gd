class_name WoodenFence
extends Node3D
## Cerca de mourão e travessas ao longo de +X: cada peça é um BreakablePiece de madeira. Um chute
## arranca a travessa; o mourão, mais grosso, aguenta mais.

const POST_SIZE: Vector3 = Vector3(0.14, 1.15, 0.14)
const RAIL_SIZE: Vector3 = Vector3(2.0, 0.12, 0.05)
const RAIL_HEIGHTS: Array[float] = [0.4, 0.85]
const POST_TOUGHNESS: float = 2.2
const VISIBLE_DISTANCE: float = 120.0
const TINT: Color = Color("a9794c")
const EDGE: Color = Color("6b4a32")

## Quantos vãos de travessa a cerca tem.
@export var bays: int = 4


func _ready() -> void:
	var post_material: ShaderMaterial = BreakablePiece.make_material(TINT, EDGE, Vector3.UP)
	var rail_material: ShaderMaterial = BreakablePiece.make_material(TINT, EDGE, Vector3.RIGHT)

	for post_index in bays + 1:
		var post: BreakablePiece = _make_piece(POST_SIZE, post_material)

		post.toughness = POST_TOUGHNESS
		post.position = Vector3(post_index * RAIL_SIZE.x, POST_SIZE.y / 2.0, 0.0)

	for rail_index in bays * RAIL_HEIGHTS.size():
		var bay: int = rail_index / RAIL_HEIGHTS.size()
		var rail: BreakablePiece = _make_piece(RAIL_SIZE, rail_material)

		rail.position = Vector3(
			(bay + 0.5) * RAIL_SIZE.x,
			RAIL_HEIGHTS[rail_index % RAIL_HEIGHTS.size()],
			(POST_SIZE.z + RAIL_SIZE.z) / 2.0
		)


func _make_piece(size: Vector3, material: Material) -> BreakablePiece:
	var piece: BreakablePiece = BreakablePiece.make_box(size, Destruction.Substance.WOOD, material)
	var view: MeshInstance3D = piece.get_child(1) as MeshInstance3D

	view.visibility_range_end = VISIBLE_DISTANCE
	add_child(piece)

	return piece
