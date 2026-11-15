class_name GroundSurface
extends RefCounted
## Tipo de piso de um colisor, para os passos soarem conforme o chão.
## O import dos modelos (tag_ground_surfaces.gd) grava o tipo como metadado no corpo estático;
## sem metadado o chão é pedra (ruas, calçadas, catedral).

enum Kind { STONE, GRASS, WOOD }

const META_NAME: StringName = &"ground_surface"


static func of(collider: Object) -> Kind:
	if collider == null:
		return Kind.STONE

	return collider.get_meta(META_NAME, Kind.STONE)
