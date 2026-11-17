class_name HeroSword
extends RefCounted
## Espada do vídeo de marketing (art/props/hero_sword.gltf, tools_src/build_hero_sword.py) presa
## na mão direita do personagem. O corpo é refeito a cada plano, então a espada vai junto com ele.

const SWORD_SCENE: PackedScene = preload("res://art/props/hero_sword.gltf")
const SWORD_BONE: StringName = &"hand_r"
## Cabo do gltf (origem no meio do cabo, lâmina em +Y) encaixado na palma da mão direita.
const SWORD_GRIP_ROTATION: Vector3 = Vector3(0.0, 0.0, -PI / 2.0)
const SWORD_GRIP_OFFSET: Vector3 = Vector3(0.0, 0.09, 0.03)
const SKELETON_PATH_IN_ACTOR: NodePath = ^"Body/Armature/Skeleton3D"


static func arm(actor: Node3D) -> void:
	var skeleton: Skeleton3D = actor.get_node(SKELETON_PATH_IN_ACTOR) as Skeleton3D
	var attachment: BoneAttachment3D = BoneAttachment3D.new()
	var sword: Node3D = SWORD_SCENE.instantiate()

	attachment.bone_name = SWORD_BONE
	skeleton.add_child(attachment)
	sword.rotation = SWORD_GRIP_ROTATION
	sword.position = SWORD_GRIP_OFFSET
	attachment.add_child(sword)
