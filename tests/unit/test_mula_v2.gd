extends "res://tests/unit/test_mula_sem_cabeca.gd"
## Mesmos testes da mula sem cabeça, rodando sobre a versão 2 (porte de touro).

const MULA_V2_SCENE: PackedScene = preload("res://features/mobs/mula_v2.tscn")


func _mula_scene() -> PackedScene:
	return MULA_V2_SCENE
