class_name ShotViews
extends RefCounted
## Câmera NAMED do TrailerDirector: reaproveita uma câmera de print ("view": [cena de tests/shots,
## nome da Camera3D]), lida sem instanciar a praça (só posição, rotação e fov do nó), e anda "push"
## metros para a frente e gira "pan" graus ao longo do plano. Plano com "open_passage" abre a
## passagem secreta da catedral no começo.

const VIEW_PROPERTIES: Array[StringName] = [&"transform", &"position", &"rotation", &"fov"]
const PASSAGE_NODE_NAME: String = "CryptMonument"

var _transforms: Dictionary[String, Transform3D] = {}
var _fovs: Dictionary[String, float] = {}


func camera_transform(shot: Dictionary, progress: float) -> Transform3D:
	var view: Transform3D = _transforms[_load(shot["view"])]
	var eased: float = smoothstep(0.0, 1.0, progress)
	var turn: Basis = Basis(Vector3.UP, deg_to_rad(shot.get("pan", 0.0) * eased))
	var view_basis: Basis = turn * view.basis

	return Transform3D(view_basis, view.origin - view_basis.z * shot.get("push", 0.0) * eased)


func fov_of(view_spec: Array) -> float:
	var key: String = _load(view_spec)

	return _fovs[key]


func open_passage_if_asked(shot: Dictionary, hub: Hub) -> void:
	var passage: SecretPassage

	if not shot.get("open_passage", false):
		return

	passage = hub.find_child(PASSAGE_NODE_NAME, true, false) as SecretPassage

	if not passage.is_open:
		passage.toggle()


func _load(view_spec: Array) -> String:
	var key: String = "%s:%s" % view_spec
	var state: SceneState
	var view: Camera3D

	if _transforms.has(key):
		return key

	state = (load(view_spec[0]) as PackedScene).get_state()
	view = Camera3D.new()

	for node_index in state.get_node_count():
		if state.get_node_name(node_index) == StringName(view_spec[1]):
			_copy_view_properties(state, node_index, view)

	_transforms[key] = view.transform
	_fovs[key] = view.fov
	view.free()

	return key


func _copy_view_properties(state: SceneState, node_index: int, view: Camera3D) -> void:
	for property_index in state.get_node_property_count(node_index):
		var property: StringName = state.get_node_property_name(node_index, property_index)

		if property in VIEW_PROPERTIES:
			view.set(property, state.get_node_property_value(node_index, property_index))
