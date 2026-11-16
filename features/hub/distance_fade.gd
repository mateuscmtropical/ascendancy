class_name DistanceFade
extends Node
## Para de desenhar, longe da câmera, as peças pequenas de um grupo da praça (tufos de grama,
## bancos, vasos, as plantas de cada canteiro da fazenda): cada malha dentro dos filhos de `target`
## cujo nome começa com um de `child_prefixes` ganha visibility_range_end com fade. Lista vazia de
## prefixos pega todos os filhos. Nada é feito por quadro: o corte é do próprio renderizador.

@export var target: NodePath
@export var child_prefixes: PackedStringArray = PackedStringArray()
@export var range_end: float = 60.0
## Faixa (m) em que a peça vai sumindo, em vez de piscar de uma vez.
@export var fade_margin: float = 8.0


func _ready() -> void:
	var group: Node = get_node_or_null(target)

	if group == null:
		return

	for child in group.get_children():
		if not has_wanted_prefix(child.name, child_prefixes):
			continue

		_fade_meshes_of(child)


## Verdadeiro se o nome começa com um dos prefixos (ou se não há prefixo nenhum).
static func has_wanted_prefix(node_name: String, prefixes: PackedStringArray) -> bool:
	if prefixes.is_empty():
		return true

	for prefix in prefixes:
		if node_name.begins_with(prefix):
			return true

	return false


func _fade_meshes_of(node: Node) -> void:
	var meshes: Array[Node] = node.find_children("*", "GeometryInstance3D", true, false)

	if node is GeometryInstance3D:
		meshes.append(node)

	for mesh in meshes:
		_fade_from_afar(mesh as GeometryInstance3D)


func _fade_from_afar(mesh: GeometryInstance3D) -> void:
	mesh.visibility_range_end = range_end
	mesh.visibility_range_end_margin = fade_margin
	mesh.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
