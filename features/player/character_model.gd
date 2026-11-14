class_name CharacterModel
extends Node3D
## Visual de um personagem: corpo montado (art/characters) + animações UAL no mesmo esqueleto.

const HAIR_MATERIAL_PREFIX: String = "MI_Hair"
# Cartões de cabelo têm dupla face; rugosidade baixa reflete o céu como mechas cinza-azuladas.
const HAIR_ROUGHNESS: float = 1.0
const SKELETON_PATH: NodePath = ^"Armature/Skeleton3D"
const BODY_NODE_NAME: StringName = &"Body"
const ANIMATION_BLEND_SECONDS: float = 0.2

@export var body_scene: PackedScene
@export var hair_color: Color = Color("4a3426")
@export var start_animation: StringName = &"ual1/Idle"
@export var start_offset_seconds: float = 0.0

var _current_animation: StringName

@onready var _animation_player: AnimationPlayer = $AnimationPlayer


func _ready() -> void:
	_current_animation = start_animation

	if body_scene:
		_build_body()


func set_body(new_body_scene: PackedScene, new_hair_color: Color) -> void:
	var old_body: Node = get_node_or_null(NodePath(BODY_NODE_NAME))

	body_scene = new_body_scene
	hair_color = new_hair_color

	if old_body:
		remove_child(old_body)
		old_body.queue_free()

	_build_body()


func play_animation(animation_name: StringName) -> void:
	_current_animation = animation_name
	_animation_player.play(animation_name, ANIMATION_BLEND_SECONDS)


func _build_body() -> void:
	var body: Node3D = body_scene.instantiate()

	body.name = BODY_NODE_NAME
	add_child(body)

	_tint_hair(body.get_node(SKELETON_PATH))
	_animation_player.clear_caches()
	_animation_player.play(_current_animation)
	_animation_player.seek(start_offset_seconds, true)


func _tint_hair(skeleton: Skeleton3D) -> void:
	var hair_meshes: Array[MeshInstance3D] = []

	for child in skeleton.get_children():
		if child is MeshInstance3D and _is_hair_mesh(child):
			hair_meshes.append(child)

	for hair_mesh in hair_meshes:
		var tinted_material: StandardMaterial3D = hair_mesh.mesh.surface_get_material(0).duplicate()

		tinted_material.albedo_color = hair_color
		tinted_material.roughness = HAIR_ROUGHNESS
		hair_mesh.set_surface_override_material(0, tinted_material)


func _is_hair_mesh(mesh_instance: MeshInstance3D) -> bool:
	var material: Material = mesh_instance.mesh.surface_get_material(0)

	return material.resource_name.begins_with(HAIR_MATERIAL_PREFIX)
