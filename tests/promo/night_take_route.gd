class_name NightTakeRoute
extends RefCounted
## Roteiro do plano-sequência (NightTakeDirector): pernas em ordem, sem cortes.
## Pontos no mundo, na altura do piso esperado (o diretor assenta no piso real).
## Catedral: fachada em x = 13, nave a 1,05 m, cripta a -4,75 m; a escada desce de
## x = 49 a x = 40,9 junto à parede sul (z = 11,67), sob o pedestal do santo.
##
## Câmera de cada perna: "orbit" é o ângulo em graus em volta da heroína a partir das costas
## (0 atrás, 90 à direita, 180 de frente), com "distance" e "height" (altura da lente acima do
## piso dela). O diretor passa de uma perna à outra girando em volta dela, sem corte; "rate"
## acelera essa passagem. "camera_at" fixa a lente num ponto do mundo; "lantern" acende a
## lanterna da mão.

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
## Lente baixa na nave lateral, ao lado da coluna (z 8,3 fica fora dela), de lado: a
## heroína, o pedestal correndo e a boca da escada.
const PUSH_CAMERA: Vector3 = Vector3(46.8, NAVE + 1.3, 8.3)
## Na volta o pedestal está aberto (recuado para z 9,4): ela passa rente às velas votivas.
const PASSAGE_TO_DOOR: Array[Vector3] = [
	PUSH_SPOT,
	Vector3(49.6, NAVE, 9.15),
	Vector3(48.0, NAVE, 9.15),
	Vector3(45.2, NAVE, 8.4),
	Vector3(PEW_END_X, NAVE, 7.4),
	Vector3(PEW_END_X, NAVE, 0.0),
	Vector3(13.0, NAVE, 0.0),
	Vector3(10.0, 0.0, 0.0),
	Vector3(6.0, 0.0, 0.0),
]

const LEGS: Array[Dictionary] = [
	{
		"stance": PlayerController.Stance.WALK,
		"path":
		[
			Vector3(-1.0, 0.0, 7.0),
			Vector3(6.0, 0.0, 2.2),
			Vector3(9.0, 0.0, 0.0),
		],
		"orbit": 155.0,
		"distance": 3.2,
		"height": 1.55,
	},
	{
		"stance": PlayerController.Stance.WALK,
		"path": [Vector3(9.0, 0.0, 0.0), Vector3(13.0, NAVE, 0.0), Vector3(19.0, NAVE, 0.0)],
		"rate": 1.6,
		"orbit": 0.0,
		"distance": 3.0,
		"height": 2.0,
	},
	{
		"stance": PlayerController.Stance.RUN,
		"path": [Vector3(19.0, NAVE, 0.0), Vector3(PEW_END_X, NAVE, 0.0)],
		"orbit": 70.0,
		"distance": 3.6,
		"height": 2.3,
	},
	{
		"stance": PlayerController.Stance.RUN,
		"path":
		[Vector3(PEW_END_X, NAVE, 0.0), Vector3(PEW_END_X, NAVE, 7.4), Vector3(45.2, NAVE, 8.4)],
		"orbit": 120.0,
		"distance": 3.4,
		"height": 1.8,
	},
	{
		"stance": PlayerController.Stance.WALK,
		"path": [Vector3(45.2, NAVE, 8.4), PUSH_SPOT],
		"orbit": 150.0,
		"distance": 2.6,
		"height": 1.6,
	},
	{"seconds": 1.2, "face": PEDESTAL, "camera_at": PUSH_CAMERA},
	{
		"seconds": 3.0,
		"action": &"ual1/Push",
		"open_passage": true,
		"face": PEDESTAL,
		"camera_at": PUSH_CAMERA,
	},
	{
		"stance": PlayerController.Stance.WALK,
		"lantern": true,
		"path":
		[
			PUSH_SPOT,
			Vector3(49.5, NAVE, STAIR_Z),
			Vector3(49.0, NAVE, STAIR_Z),
			Vector3(40.9, CRYPT, STAIR_Z),
			Vector3(40.4, CRYPT, STAIR_Z),
		],
		"orbit": 180.0,
		"distance": 2.6,
		"height": 1.1,
		"rate": 2.5,
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
		"orbit": 125.0,
		"distance": 2.8,
		"height": 1.5,
	},
	{"seconds": 3.5, "face": Vector3(43.0, CRYPT, -12.0), "orbit": 25.0, "distance": 2.0},
	{
		"stance": PlayerController.Stance.RUN,
		"path": [Vector3(43.0, CRYPT, -7.0), Vector3(40.0, CRYPT, -3.0), Vector3(40.4, CRYPT, 4.0)],
		"orbit": 180.0,
		"distance": 3.2,
		"height": 1.6,
		"rate": 3.0,
	},
	## Na curva da escada a lente passa para trás dela ainda no salão aberto e sobe atrás:
	## de frente ela ficaria colada na parede do corredor estreito. Perto e baixa, para não
## cortar a laje da nave na boca da escada.
	{
		"stance": PlayerController.Stance.RUN,
		"path":
		[
			Vector3(40.4, CRYPT, 4.0),
			Vector3(40.4, CRYPT, STAIR_Z),
			Vector3(40.9, CRYPT, STAIR_Z),
			Vector3(49.0, NAVE, STAIR_Z),
			Vector3(49.5, NAVE, STAIR_Z),
			PUSH_SPOT,
		],
		"orbit": 0.0,
		"distance": 2.2,
		"height": 1.4,
		"rate": 4.0,
	},
	{
		"stance": PlayerController.Stance.RUN,
		"path": PASSAGE_TO_DOOR,
		"orbit": 180.0,
		"distance": 4.0,
		"height": 1.9,
		"rate": 2.0,
	},
	{"seconds": 1.6, "face": Vector3(0.0, 0.0, -2.0), "orbit": 0.0, "distance": 3.8, "height": 2.0},
	{"seconds": 10.0, "crane": true, "look_up": SWIRL_LOOK},
]

## (segundo do vídeo, hora do dia): fim de tarde na praça, noite fechada quando ela sai.
const TIME_KEYS: Array[Vector2] = [
	Vector2(0.0, 0.47),
	Vector2(14.0, 0.49),
	Vector2(30.0, 0.53),
	Vector2(50.0, 0.68),
	Vector2(200.0, 0.7),
]
