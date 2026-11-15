@tool
extends EditorScenePostImport
## Script de import dos modelos da cidade: marca o piso de cada corpo estático pelo nome que o
## gerador do Blender deu ao colisor (Bed3-colonly vira o corpo Bed3, piso de grama) e troca o
## vidro das janelas pelo que acende à noite (WindowGlass).

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

		if not SURFACE_BY_COLLIDER_NAME.has(collider_name):
			continue

		body.set_meta(GroundSurface.META_NAME, SURFACE_BY_COLLIDER_NAME[collider_name])

	WindowGlass.light_up_windows(scene)

	return scene
