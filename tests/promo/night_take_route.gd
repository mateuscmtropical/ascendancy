class_name NightTakeRoute
extends RefCounted
## Roteiro do plano-sequência (NightTakeDirector): pernas em ordem, sem cortes.
## Pontos no mundo, na altura do piso esperado (o diretor assenta no piso real).
## Catedral: fachada em x = 13, nave a 1,05 m, cripta a -4,75 m; a escada desce de
## x = 49 a x = 40,9 junto à parede sul (z = 11,67), sob o pedestal do santo.

const STAIR_Z: float = 11.67
const NAVE: float = 1.05
const CRYPT: float = -4.75
## Espiral do céu: ao norte, ~54° acima da heroína parada no adro.
const SWIRL_LOOK: Vector3 = Vector3(6.0, 11.0, -8.0)
## Bancos: a nave tem corredor central (z = 0) e acaba antes da escada do coro (x = 43,6); a
## heroína cruza entre os dois e passa ao corredor lateral (z de 7 a 8,8) até a passagem.
const PEW_END_X: float = 42.8
## Entre o genuflexório do altar lateral (x >= 49,8) e o pedestal (x <= 49), de frente para ele.
const PUSH_SPOT: Vector3 = Vector3(49.6, NAVE, 9.95)
const PEDESTAL: Vector3 = Vector3(47.3, NAVE, 12.4)
## Câmera de lado, na nave lateral: atrás dela fica a coluna do altar.
const PUSH_CAMERA: Vector3 = Vector3(46.4, NAVE + 1.6, 8.0)
const AISLE_TO_PASSAGE: Array[Vector3] = [
	Vector3(PEW_END_X, NAVE, 0.0),
	Vector3(PEW_END_X, NAVE, 7.4),
	Vector3(45.2, NAVE, 8.4),
	PUSH_SPOT,
]
## Na volta o pedestal está aberto (recuado para z 9,4): ela passa rente às velas votivas.
const PASSAGE_TO_DOOR: Array[Vector3] = [
	PUSH_SPOT,
	Vector3(49.6, NAVE, 9.15),
	Vector3(48.0, NAVE, 9.15),
	Vector3(45.2, NAVE, 8.4),
	Vector3(PEW_END_X, NAVE, 7.4),
	Vector3(PEW_END_X, NAVE, 0.0),
	Vector3(16.0, NAVE, 0.0),
]

const LEGS: Array[Dictionary] = [
	{
		"stance": PlayerController.Stance.RUN,
		"navigate": true,
		"path":
		[
			Vector3(-30.0, 0.0, 14.0),
			Vector3(-8.0, 0.0, 14.0),
			Vector3(8.0, 0.0, 4.0),
			Vector3(10.0, 0.0, 0.0)
		],
		"camera_distance": 4.5,
		"camera_height": 2.1,
	},
	{
		"stance": PlayerController.Stance.WALK,
		"path": [Vector3(10.0, 0.0, 0.0), Vector3(13.0, NAVE, 0.0), Vector3(16.0, NAVE, 0.0)],
		"camera_distance": 3.6,
	},
	{
		"stance": PlayerController.Stance.RUN,
		"path": [Vector3(16.0, NAVE, 0.0), Vector3(PEW_END_X, NAVE, 0.0)],
		"camera_distance": 3.6,
	},
	{
		"stance": PlayerController.Stance.WALK,
		"path": AISLE_TO_PASSAGE,
		"camera_distance": 3.0,
	},
	{"seconds": 1.0, "face": PEDESTAL, "camera_at": PUSH_CAMERA},
	{
		"seconds": 3.0,
		"action": &"ual1/Push",
		"open_passage": true,
		"face": PEDESTAL,
		"camera_at": PUSH_CAMERA,
	},
	{
		"stance": PlayerController.Stance.WALK,
		"path":
		[
			PUSH_SPOT,
			Vector3(49.5, NAVE, STAIR_Z),
			Vector3(49.0, NAVE, STAIR_Z),
			Vector3(40.9, CRYPT, STAIR_Z),
			Vector3(40.4, CRYPT, STAIR_Z),
		],
		"camera_distance": 2.4,
		"camera_height": 1.6,
	},
	{
		"stance": PlayerController.Stance.WALK,
		"path":
		[
			Vector3(40.4, CRYPT, STAIR_Z),
			Vector3(40.4, CRYPT, 4.0),
			Vector3(40.0, CRYPT, -3.0),
			Vector3(43.0, CRYPT, -7.0)
		],
		"camera_distance": 2.6,
		"camera_height": 1.7,
	},
	{
		"seconds": 3.5,
		"face": Vector3(43.0, CRYPT, -12.0),
		"camera_distance": 2.2,
		"camera_height": 1.5
	},
	{
		"stance": PlayerController.Stance.RUN,
		"path":
		[
			Vector3(43.0, CRYPT, -7.0),
			Vector3(40.0, CRYPT, -3.0),
			Vector3(40.4, CRYPT, 4.0),
			Vector3(40.4, CRYPT, STAIR_Z),
			Vector3(40.9, CRYPT, STAIR_Z),
			Vector3(49.0, NAVE, STAIR_Z),
			Vector3(49.5, NAVE, STAIR_Z),
			PUSH_SPOT,
		],
		"camera_distance": 3.0,
		"camera_height": 1.8,
	},
	{
		"stance": PlayerController.Stance.RUN,
		"path": PASSAGE_TO_DOOR,
		"camera_distance": 3.4,
		"camera_height": 1.9,
	},
	{
		"stance": PlayerController.Stance.WALK,
		"path":
		[
			Vector3(16.0, NAVE, 0.0),
			Vector3(13.0, NAVE, 0.0),
			Vector3(10.0, 0.0, 0.0),
			Vector3(6.0, 0.0, 0.0)
		],
		"camera_distance": 3.8,
		"camera_height": 2.0,
	},
	{"seconds": 1.2, "face": Vector3(0.0, 0.0, -2.0), "camera_distance": 3.8, "camera_height": 2.0},
	{"seconds": 11.0, "crane": true, "look_up": SWIRL_LOOK},
]

## (segundo do vídeo, hora do dia): o céu escurece enquanto ela está na cripta.
const TIME_KEYS: Array[Vector2] = [
	Vector2(0.0, 0.44),
	Vector2(25.5, 0.49),
	Vector2(35.3, 0.53),
	Vector2(58.4, 0.68),
	Vector2(200.0, 0.7),
]
