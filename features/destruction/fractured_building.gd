class_name FracturedBuilding
extends Node3D
## Prédio ou muro pré-fraturado (gerado por tools_src/build_destructibles.py): cada seção
## `Section_<SUBSTÂNCIA>_<Nome>` traz a malha inteira `Whole_<Nome>` e os pedaços
## `Pieces_<Nome>/Piece_*`. Inteira, a seção desenha só a malha única; os pedaços já existem
## congelados, só com colisão. Quando o primeiro pedaço da seção quebra, a malha inteira some e
## os pedaços aparecem no lugar dela.

const SECTION_PREFIX: String = "Section_"
const VISIBLE_DISTANCE: float = 160.0

## Modelo glTF pré-fraturado.
@export var model: PackedScene
## Seção mais firme que o material comum (nome da seção -> multiplicador da resistência): porta
## de tábua grossa e alicerce, que só uma magia forte arranca.
@export var toughness_by_section: Dictionary[String, float] = {"Door": 4.7, "Plinth": 3.0}
## Seções pregadas inteiras (porta): quando um pedaço quebra, todos saem com ele.
@export var linked_sections: PackedStringArray = ["Door"]


func _ready() -> void:
	var building: Node3D = model.instantiate()

	add_child(building)

	for section in building.get_children():
		if section.name.begins_with(SECTION_PREFIX):
			_prepare_section(section)


func _prepare_section(section: Node3D) -> void:
	var parts: PackedStringArray = section.name.trim_prefix(SECTION_PREFIX).split("_", true, 1)
	var substance: Destruction.Substance = Destruction.Substance[parts[0]]
	var section_name: String = parts[1]
	var whole: MeshInstance3D = section.get_node("Whole_" + section_name)
	var holder: Node3D = section.get_node("Pieces_" + section_name)
	var firmness: float = toughness_by_section.get(section_name, 1.0)
	var pieces: Array[BreakablePiece] = []

	whole.visibility_range_end = VISIBLE_DISTANCE

	for view in holder.get_children():
		var piece: BreakablePiece = BreakablePiece.make_from_mesh(view, substance, firmness)

		(view as MeshInstance3D).visibility_range_end = VISIBLE_DISTANCE
		view.visible = false
		holder.add_child(piece)
		piece.broke_free.connect(_on_piece_broke_free.bind(whole, pieces), CONNECT_ONE_SHOT)
		pieces.append(piece)

	if section_name in linked_sections:
		for piece in pieces:
			piece.linked_pieces = pieces


## Primeiro pedaço da seção que se solta: troca a malha inteira pelos pedaços.
func _on_piece_broke_free(
	_piece: BreakablePiece, whole: MeshInstance3D, pieces: Array[BreakablePiece]
) -> void:
	if not whole.visible:
		return

	whole.visible = false

	for piece in pieces:
		piece.get_child(1).visible = true
