class_name TrailerShots
extends RefCounted
## Planos do trailer em ordem: duração em batidas, câmera, sol e ator (ver TrailerDirector).
## Ator: "stance" do PlayerController (velocidade e passo do jogo); "action" toca uma vez e para.

enum CameraKind { DOLLY, FOLLOW, WATCH, ORBIT, SELECT, NAMED }
enum SunMood { DAY, GOLDEN }

const SHOTS: Array[Dictionary] = [
	{  # o largo do chafariz se abrindo, aproximação lenta
		"beats": 16,
		"camera": CameraKind.DOLLY,
		"eye_from": Vector3(-23.0, 2.2, 12.0),
		"eye_to": Vector3(-24.4, 1.8, 7.8),
		"look_from": Vector3(-34.0, 2.6, 0.0),
		"look_to": Vector3(-34.0, 2.4, 0.0),
		"fov": 52.0,
	},
	{  # aventureira caminha para a catedral, câmera atrás dela
		"beats": 12,
		"camera": CameraKind.FOLLOW,
		"offset": Vector3(-1.2, 2.1, -3.4),
		"look_offset": Vector3(0.0, 4.2, 8.0),
		"fov": 55.0,
		"actor":
		{
			"body": "female",
			"path": [Vector3(-11.3, 0.2, 2.2), Vector3(-2.0, 0.2, 2.2)],
			"stance": PlayerController.Stance.WALK,
		},
	},
	{  # nave com os feixes dos vitrais, avançando para o altar
		"beats": 12,
		"camera": CameraKind.DOLLY,
		"eye_from": Vector3(19.0, 2.65, 0.0),
		"eye_to": Vector3(27.0, 2.7, 0.0),
		"look_from": Vector3(56.0, 5.0, 0.0),
		"look_to": Vector3(56.0, 4.8, 0.0),
		"fov": 58.0,
	},
	{  # altar e crucifixo, aproximação suave
		"beats": 8,
		"camera": CameraKind.DOLLY,
		"eye_from": Vector3(35.5, 2.7, 3.0),
		"eye_to": Vector3(38.5, 2.7, 2.2),
		"look_from": Vector3(58.4, 6.4, 0.0),
		"look_to": Vector3(58.4, 6.6, 0.0),
		"fov": 36.0,
	},
	{  # aventureira pelo calçadão, câmera de lado
		"beats": 8,
		"camera": CameraKind.FOLLOW,
		"offset": Vector3(-3.8, 1.5, 0.4),
		"look_offset": Vector3(0.0, 1.2, 0.8),
		"fov": 52.0,
		"actor":
		{
			"body": "female",
			"path": [Vector3(1.6, 0.2, 18.0), Vector3(1.6, 0.2, 26.0)],
			"stance": PlayerController.Stance.WALK,
		},
	},
	{  # entra na ferraria pela porta, câmera atrás do ombro
		"beats": 8,
		"camera": CameraKind.FOLLOW,
		"offset": Vector3(0.45, 1.65, -2.1),
		"look_offset": Vector3(0.0, 1.45, 4.0),
		"fov": 62.0,
		"actor":
		{
			"body": "male",
			"path": [Vector3(-69.5, 0.2, -18.4), Vector3(-76.5, 0.2, -18.4)],
			"stance": PlayerController.Stance.WALK,
		},
	},
	{  # lojista na forja
		"beats": 8,
		"camera": CameraKind.DOLLY,
		"eye_from": Vector3(-77.0, 1.6, -18.2),
		"eye_to": Vector3(-79.4, 1.55, -18.5),
		"look_from": Vector3(-84.5, 1.55, -18.6),
		"look_to": Vector3(-84.5, 1.5, -18.6),
		"fov": 55.0,
	},
	{  # corrida pelo calçadão passando rente à câmera (ápice da música)
		"beats": 8,
		"camera": CameraKind.WATCH,
		"eye_from": Vector3(-1.2, 1.0, 16.5),
		"eye_to": Vector3(-1.2, 1.0, 16.5),
		"look_offset": Vector3(0.0, 1.1, 0.0),
		"fov": 55.0,
		"actor":
		{
			"body": "male",
			"path": [Vector3(1.6, 0.2, 32.0), Vector3(1.6, 0.2, 9.0)],
			"stance": PlayerController.Stance.RUN,
		},
	},
	{  # magia no calçadão, catedral ao fundo
		"beats": 4,
		"camera": CameraKind.WATCH,
		"eye_from": Vector3(-0.8, 1.0, -3.8),
		"eye_to": Vector3(-0.5, 1.0, -3.5),
		"look_offset": Vector3(0.0, 1.5, 0.0),
		"fov": 55.0,
		"actor":
		{
			"body": "male",
			"path": [Vector3(2.6, 0.2, -1.6)],
			"action": &"ual1/Spell_Simple_Shoot",
			"face": Vector3(-1.0, 0.0, -4.5),
		},
		"flash": [0.55, Vector3(1.9, 1.4, -2.2)],
	},
	{  # mercado no calçadão, gente passando
		"beats": 16,
		"camera": CameraKind.DOLLY,
		"eye_from": Vector3(0.5, 1.7, 47.0),
		"eye_to": Vector3(0.5, 1.7, 43.6),
		"look_from": Vector3(0.5, 1.5, 20.0),
		"look_to": Vector3(0.5, 1.5, 20.0),
		"fov": 55.0,
	},
	{  # rua das lojas
		"beats": 12,
		"camera": CameraKind.DOLLY,
		"eye_from": Vector3(-65.3, 1.7, -31.0),
		"eye_to": Vector3(-65.6, 1.7, -27.5),
		"look_from": Vector3(-70.0, 2.4, -5.4),
		"look_to": Vector3(-70.5, 2.4, -5.4),
		"fov": 55.0,
	},
	{  # coreto ao entardecer
		"beats": 16,
		"camera": CameraKind.DOLLY,
		"eye_from": Vector3(-32.5, 1.7, -20.8),
		"eye_to": Vector3(-35.0, 1.7, -19.4),
		"look_from": Vector3(-46.0, 2.8, -13.0),
		"look_to": Vector3(-46.0, 2.8, -13.0),
		"fov": 50.0,
		"sun": SunMood.GOLDEN,
	},
	{  # chafariz e catedral ao entardecer, o título entra por cima na montagem
		"beats": 20,
		"camera": CameraKind.DOLLY,
		"eye_from": Vector3(-52.0, 1.7, 3.0),
		"eye_to": Vector3(-48.5, 1.75, 2.4),
		"look_from": Vector3(13.0, 7.0, 0.0),
		"look_to": Vector3(13.0, 7.5, 0.0),
		"fov": 45.0,
		"sun": SunMood.GOLDEN,
	},
]
