@tool
extends EditorScenePostImport
## Script de import dos modelos da cidade: marca o piso de cada corpo estático pelo nome que o
## gerador do Blender deu ao colisor (Bed3-colonly vira o corpo Bed3, piso de grama), põe os
## colisores CameraStop* (beirais, toldos, coreto, escada da torre) na camada que só o braço da
## câmera enxerga e troca o vidro das janelas pelo que acende à noite (WindowGlass); texturas
## com mipmap filtram anisotrópico (AnisotropicTextures).

## Por caminho: no --import headless a classe nova ainda não está no cache de class_name.
const ANISOTROPIC_TEXTURES: GDScript = preload("res://features/hub/anisotropic_textures.gd")
const CAMERA_STOP_PREFIX: String = "CameraStop"
## Camada 4 ("camera"): o SpringArm do jogador colide com ela; jogador, NPC e navmesh não.
const CAMERA_LAYER: int = 1 << 3
const SURFACE_BY_COLLIDER_NAME: Dictionary[String, GroundSurface.Kind] = {
	"Bed": GroundSurface.Kind.GRASS,
	"Hedge": GroundSurface.Kind.GRASS,
	"WoodFloor": GroundSurface.Kind.WOOD,
	"Field": GroundSurface.Kind.DIRT,
	"Yard": GroundSurface.Kind.DIRT,
	"Path": GroundSurface.Kind.DIRT,
}


func _post_import(scene: Node) -> Object:
	var bodies: Array[Node] = scene.find_children("*", "StaticBody3D", true, false)

	for body in bodies:
		var collider_name: String = String(body.name).rstrip("0123456789")

		if collider_name.begins_with(CAMERA_STOP_PREFIX):
			_make_camera_only(body as CollisionObject3D)
			continue

		if not SURFACE_BY_COLLIDER_NAME.has(collider_name):
			continue

		body.set_meta(GroundSurface.META_NAME, SURFACE_BY_COLLIDER_NAME[collider_name])

	WindowGlass.light_up_windows(scene)
	ANISOTROPIC_TEXTURES.apply_to(scene)

	return scene


func _make_camera_only(body: CollisionObject3D) -> void:
	body.collision_layer = CAMERA_LAYER
	body.collision_mask = 0
