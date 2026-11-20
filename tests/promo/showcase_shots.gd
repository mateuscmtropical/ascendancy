class_name ShowcaseShots
extends RefCounted
## Clipes crus do "Ascendancy: a day in" (rolo SHOWCASE a 60 "BPM": "beats" = segundos).
## Um dia inteiro, do amanhecer na fazenda à luta com a Mula à noite, passando por tudo o que a
## cidade tem: fazenda, casa-grande, convento, praça, lojas, catedral, cripta e céu. Cada clipe tem
## 1 s de sobra no começo que a edição corta; a edição (tools_src/cut_showcase_trailer.py) acelera,
## corta na batida e monta a abertura em grade. Gravar a 60 fps (RECORD_FPS=60 tools_src/record.sh).

const DAWN: float = 0.04
const MORNING: float = 0.13
const NOON: float = 0.25
const AFTERNOON: float = 0.37
const NIGHT: float = 0.66
const HUB_VIEWS: String = "res://tests/shots/hub_shots.tscn"
const SHOP_VIEWS: String = "res://tests/shots/shop_shots.tscn"
const FARMHOUSE_VIEWS: String = "res://tests/shots/farmhouse_shots.tscn"
const CRYPT_VIEWS: String = "res://tests/shots/crypt_shots.tscn"
const CRYPT_CLOSED_VIEWS: String = "res://tests/shots/crypt_closed_shots.tscn"
const HERO_SPOT: Vector3 = Vector3(126.0, 0.0, 26.0)
const MULA_SPOT: Vector3 = Vector3(126.0, 0.0, 33.5)
const WATER_WHEEL: Vector3 = Vector3(137.5, 1.7, 32.0)
const MONJOLO: Vector3 = Vector3(131.5, 1.0, 37.9)

## A Mula parada no lugar da luta (sem "mula" no plano ela volta para o pasto).
const MULA_WAITING: Dictionary = {
	"path": [MULA_SPOT, MULA_SPOT + Vector3(0.0, 0.0, -0.01)], "animation": &"Idle"
}

const SHOTS: Array[Dictionary] = [
	{  # 0 roda d'água ao amanhecer
		"beats": 3.5,
		"camera": TrailerShots.CameraKind.DOLLY,
		"time": DAWN,
		"eye_from": WATER_WHEEL + Vector3(-6.0, 0.6, -5.0),
		"eye_to": WATER_WHEEL + Vector3(-4.5, 0.4, -3.5),
		"look_from": WATER_WHEEL,
		"look_to": WATER_WHEEL + Vector3(0.0, -0.2, 0.0),
		"fov": 50.0,
	},
	{  # 1 monjolo batendo
		"beats": 3.5,
		"camera": TrailerShots.CameraKind.DOLLY,
		"time": DAWN,
		"eye_from": MONJOLO + Vector3(-4.0, 0.6, -3.0),
		"eye_to": MONJOLO + Vector3(-3.0, 0.4, -2.2),
		"look_from": MONJOLO,
		"look_to": MONJOLO,
		"fov": 50.0,
	},
	{  # 2 pasto com os bichos
		"beats": 3.0,
		"camera": TrailerShots.CameraKind.NAMED,
		"time": MORNING,
		"view": [HUB_VIEWS, "PastureEye"],
		"push": 0.6,
	},
	{  # 3 chiqueiro
		"beats": 3.0,
		"camera": TrailerShots.CameraKind.NAMED,
		"time": MORNING,
		"view": [HUB_VIEWS, "PigstyEye"],
		"push": 1.5,
	},
	{  # 4 carroça na estrada
		"beats": 3.5,
		"camera": TrailerShots.CameraKind.FOLLOW,
		"time": MORNING,
		"subject": "Carriages/Carriage1",
		"offset": Vector3(-4.5, 1.6, 3.0),
		"look_offset": Vector3(0.0, 1.2, 1.5),
		"fov": 55.0,
	},
	{  # 5 cozinha da casa-grande
		"beats": 3.0,
		"camera": TrailerShots.CameraKind.NAMED,
		"time": MORNING,
		"view": [FARMHOUSE_VIEWS, "Cozinha"],
		"push": 1.0,
	},
	{  # 6 tulha com o monte de café
		"beats": 3.0,
		"camera": TrailerShots.CameraKind.NAMED,
		"time": MORNING,
		"view": [FARMHOUSE_VIEWS, "TulhaMound"],
		"push": 1.0,
	},
	{  # 7 quarto das meninas na fazenda
		"beats": 3.0,
		"camera": TrailerShots.CameraKind.NAMED,
		"time": MORNING,
		"view": [FARMHOUSE_VIEWS, "MeninasFundo"],
		"push": 0.8,
	},
	{  # 8 escadaria imperial do convento
		"beats": 3.5,
		"camera": TrailerShots.CameraKind.NAMED,
		"time": MORNING,
		"view": [SHOP_VIEWS, "VestibuleStair"],
		"push": 2.0,
	},
	{  # 9 sala de aula
		"beats": 3.0,
		"camera": TrailerShots.CameraKind.NAMED,
		"time": MORNING,
		"view": [SHOP_VIEWS, "SchoolClass2Front"],
		"push": 1.5,
	},
	{  # 10 sala de prática de magia
		"beats": 3.0,
		"camera": TrailerShots.CameraKind.NAMED,
		"time": MORNING,
		"view": [SHOP_VIEWS, "SchoolMagicFar"],
		"push": 2.0,
		"pan": 8.0,
	},
	{  # 11 sala de armas
		"beats": 3.0,
		"camera": TrailerShots.CameraKind.NAMED,
		"time": MORNING,
		"view": [SHOP_VIEWS, "SchoolSalleFar"],
		"push": 2.0,
	},
	{  # 12 berçário
		"beats": 3.0,
		"camera": TrailerShots.CameraKind.NAMED,
		"time": MORNING,
		"view": [SHOP_VIEWS, "ReadingNursery"],
		"push": 1.0,
	},
	{  # 13 refeitório das crianças
		"beats": 3.0,
		"camera": TrailerShots.CameraKind.NAMED,
		"time": MORNING,
		"view": [SHOP_VIEWS, "LibraryRefFar"],
		"push": 2.0,
	},
	{  # 14 capela do convento
		"beats": 3.5,
		"camera": TrailerShots.CameraKind.NAMED,
		"time": MORNING,
		"view": [SHOP_VIEWS, "SeminaryChapelNave"],
		"push": 2.5,
	},
	{  # 15 heroína em disparada pelo calçadão, vindo para a lente
		"beats": 4.0,
		"camera": TrailerShots.CameraKind.FOLLOW,
		"time": NOON,
		"offset": Vector3(0.9, 1.1, 3.4),
		"look_offset": Vector3(0.0, 1.3, 0.0),
		"fov": 55.0,
		"actor":
		{
			"body": "female",
			"weapon": true,
			"path": [Vector3(1.6, 0.2, 42.0), Vector3(1.6, 0.2, 14.0)],
			"stance": PlayerController.Stance.SPRINT,
		},
	},
	{  # 16 chafariz e moradores
		"beats": 3.0,
		"camera": TrailerShots.CameraKind.NAMED,
		"time": NOON,
		"view": [HUB_VIEWS, "FountainEye"],
		"push": 2.0,
	},
	{  # 17 taverna
		"beats": 3.0,
		"camera": TrailerShots.CameraKind.NAMED,
		"time": NOON,
		"view": [SHOP_VIEWS, "TavernInside"],
		"push": 2.0,
	},
	{  # 18 ferraria
		"beats": 3.0,
		"camera": TrailerShots.CameraKind.NAMED,
		"time": NOON,
		"view": [SHOP_VIEWS, "SmithInside"],
		"push": 1.5,
	},
	{  # 19 loja de magia
		"beats": 3.0,
		"camera": TrailerShots.CameraKind.NAMED,
		"time": NOON,
		"view": [SHOP_VIEWS, "MagicInside"],
		"push": 1.5,
	},
	{  # 20 guilda
		"beats": 3.0,
		"camera": TrailerShots.CameraKind.NAMED,
		"time": NOON,
		"view": [SHOP_VIEWS, "GuildInside"],
		"push": 1.5,
	},
	{  # 21 fachada da catedral à tarde
		"beats": 3.0,
		"camera": TrailerShots.CameraKind.NAMED,
		"time": AFTERNOON,
		"view": [HUB_VIEWS, "FacadeFar"],
		"push": 3.0,
	},
	{  # 22 nave da catedral
		"beats": 3.0,
		"camera": TrailerShots.CameraKind.NAMED,
		"time": AFTERNOON,
		"view": [HUB_VIEWS, "NaveEye"],
		"push": 3.0,
	},
	{  # 23 altar-mor sob a cúpula
		"beats": 3.0,
		"camera": TrailerShots.CameraKind.NAMED,
		"time": AFTERNOON,
		"view": [HUB_VIEWS, "AltarEye"],
		"push": 0.8,
	},
	{  # 24 o dia vira noite sobre o casarão (acelerado na edição)
		"beats": 7.0,
		"camera": TrailerShots.CameraKind.NAMED,
		"time": 0.44,
		"time_to": 0.64,
		"view": [HUB_VIEWS, "CasaraoAerial"],
		"push": 2.0,
	},
	{  # 25 o pedestal do santo desliza e abre a escada
		"beats": 4.0,
		"camera": TrailerShots.CameraKind.NAMED,
		"time": NIGHT,
		"view": [CRYPT_CLOSED_VIEWS, "MonumentAisle"],
		"open_passage": true,
		"push": 0.6,
	},
	{  # 26 escada da cripta
		"beats": 3.0,
		"camera": TrailerShots.CameraKind.NAMED,
		"time": NIGHT,
		"view": [CRYPT_VIEWS, "StairTop"],
		"push": 2.0,
	},
	{  # 27 ossuário
		"beats": 3.0,
		"camera": TrailerShots.CameraKind.NAMED,
		"time": NIGHT,
		"view": [CRYPT_VIEWS, "CatacombOssuary"],
		"push": 1.5,
	},
	{  # 28 altar dos santos na cripta
		"beats": 3.0,
		"camera": TrailerShots.CameraKind.NAMED,
		"time": NIGHT,
		"view": [CRYPT_VIEWS, "SaintsAltar"],
		"push": 1.5,
	},
	{  # 29 gabinete do mago com o círculo mágico
		"beats": 3.0,
		"camera": TrailerShots.CameraKind.NAMED,
		"time": NIGHT,
		"view": [CRYPT_VIEWS, "CabinetCircle"],
		"push": 1.0,
	},
	{  # 30 chuva de meteoros sobre o campo
		"beats": 4.0,
		"camera": TrailerShots.CameraKind.NAMED,
		"time": 0.7,
		"event": "shower",
		"view": [HUB_VIEWS, "SkySwirl"],
		"pan": -6.0,
	},
	{  # 31 a Mula galopa, câmera correndo do lado
		"beats": 3.5,
		"camera": TrailerShots.CameraKind.FOLLOW,
		"time": NIGHT,
		"subject": "MulaSemCabeca",
		"offset": Vector3(6.5, 1.2, 2.5),
		"look_offset": Vector3(0.0, 1.4, -0.5),
		"fov": 50.0,
		"mula":
		{
			"path": [Vector3(125.5, 0.0, 52.0), Vector3(126.0, 0.0, 34.0)],
			"speed": 6.4,
			"animation": &"Run",
		},
	},
	{  # 32 a heroína encara a Mula que ataca, câmera baixa girando
		"beats": 4.0,
		"camera": TrailerShots.CameraKind.ORBIT,
		"time": NIGHT,
		"center": (HERO_SPOT + MULA_SPOT) * 0.5,
		"angle_from": 150.0,
		"angle_to": 205.0,
		"radius_from": 6.5,
		"radius_to": 5.5,
		"height_from": 0.6,
		"height_to": 1.0,
		"look_height": 1.5,
		"fov": 50.0,
		"actor":
		{
			"body": "female",
			"weapon": true,
			"path": [HERO_SPOT, HERO_SPOT + Vector3(0.0, 0.0, 0.01)],
			"face": MULA_SPOT,
			"action": &"ual1/Sword_Idle",
		},
		"mula":
		{
			"path": [MULA_SPOT, MULA_SPOT + Vector3(0.0, 0.0, -0.01)],
			"animation": &"Attack",
		},
	},
	{  # 33 golpe pesado da heroína, clarão no impacto
		"beats": 3.2,
		"camera": TrailerShots.CameraKind.DOLLY,
		"time": NIGHT,
		"eye_from": Vector3(124.6, 1.5, 22.6),
		"eye_to": Vector3(124.9, 1.4, 23.2),
		"look_from": Vector3(126.4, 1.3, 30.0),
		"look_to": Vector3(126.4, 1.3, 30.0),
		"fov": 50.0,
		"flash": [2.0, Vector3(126.0, 1.4, 27.5)],
		"mula": MULA_WAITING,
		"actor":
		{
			"body": "female",
			"weapon": true,
			"path": [HERO_SPOT, HERO_SPOT + Vector3(0.0, 0.0, 0.01)],
			"face": MULA_SPOT,
			"action": &"ual2/Sword_Heavy_Combo",
		},
	},
	{  # 34 a heroína rola de lado, esquivando
		"beats": 2.6,
		"camera": TrailerShots.CameraKind.DOLLY,
		"time": NIGHT,
		"eye_from": Vector3(129.0, 1.1, 26.5),
		"eye_to": Vector3(128.6, 1.0, 26.3),
		"look_from": Vector3(126.0, 1.1, 26.5),
		"look_to": Vector3(126.0, 1.1, 26.5),
		"fov": 48.0,
		"mula": MULA_WAITING,
		"actor":
		{
			"body": "female",
			"weapon": true,
			"path": [HERO_SPOT, HERO_SPOT + Vector3(0.0, 0.0, 0.01)],
			"face": HERO_SPOT + Vector3(-4.0, 0.0, 0.0),
			"action": &"ual1/Roll",
		},
	},
	{  # 35 investida da heroína contra a lente
		"beats": 2.6,
		"camera": TrailerShots.CameraKind.DOLLY,
		"time": NIGHT,
		"eye_from": Vector3(126.0, 1.0, 30.5),
		"eye_to": Vector3(126.0, 1.0, 30.8),
		"look_from": Vector3(126.0, 1.2, 26.0),
		"look_to": Vector3(126.0, 1.2, 26.0),
		"fov": 50.0,
		"flash": [1.5, Vector3(126.0, 1.4, 28.0)],
		"mula": MULA_WAITING,
		"actor":
		{
			"body": "female",
			"weapon": true,
			"path": [HERO_SPOT, HERO_SPOT + Vector3(0.0, 0.0, 0.01)],
			"face": MULA_SPOT,
			"action": &"ual2/Sword_Dash",
		},
	},
	{  # 36 fundo do título: a cidade acesa vista do alto, de noite
		"beats": 7.0,
		"camera": TrailerShots.CameraKind.ORBIT,
		"time": NIGHT,
		"center": Vector3(-10.0, 0.0, 0.0),
		"angle_from": 120.0,
		"angle_to": 140.0,
		"radius_from": 95.0,
		"radius_to": 85.0,
		"height_from": 45.0,
		"height_to": 38.0,
		"look_height": 0.0,
		"fov": 55.0,
	},
]
