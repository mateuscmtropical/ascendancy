class_name DoorsRoute
extends RefCounted
## Clipes do vídeo "Every door opens somewhere" (DoorsDirector), na ordem de gravação; a edição
## escolhe a ordem de montagem. Cada clipe: "start" (teleporte), "path" (pontos que ela segue),
## "stance" (walk | sprint; sem ele corre), "time" (hora do céu), "seconds" (duração exata),
## câmera "side" (graus fora das costas), "sweep" (olhar em volta ao chegar: graus para cada
## lado, segundos de um lado ao outro), "orbit" (graus/s parada), "pitch" e "pitch_hold"
## (radianos, positivo olha para cima; "pitch_rate" é a pressa do olhar), "events" (teclas:
## {"at", "press", "hold"}) e "waits"
## (índice do ponto -> segundo do clipe antes do qual ela espera parada, ex.: a pedra abrir).
## Lojas: fachadas em z = -68,3, portas no meio do lote, menos a guilda (porta a 3,2 m do meio).

const DAY: float = 0.14
const GOLDEN: float = 0.43
const NIGHT: float = 0.62
const SHOP_STREET_Z: float = -64.0
const SHOP_INSIDE_Z: float = -75.0
const NAVE: float = 1.05
const CRYPT: float = -4.75
const STAIR_Z: float = 11.67
const PUSH_SPOT: Vector3 = Vector3(49.6, NAVE, 9.95)

const CLIPS: Array[Dictionary] = [
	{
		"name": "tailor",
		"time": DAY,
		"start": Vector3(-22.0, 0.0, -63.0),
		"direct": true,
		"path":
		[Vector3(-18.6, 0.0, -66.9), Vector3(-16.0, 0.0, -68.0), Vector3(-16.0, 0.0, -73.5)],
		"sweep": Vector2(40.0, 3.0),
		"pitch": -0.08,
		"pitch_hold": 0.05,
		"seconds": 8.0,
	},
	{
		"name": "smith",
		"time": DAY,
		"start": Vector3(-94.4, 0.0, SHOP_STREET_Z),
		"path": [Vector3(-94.4, 0.0, SHOP_INSIDE_Z)],
		"direct": true,
		"sweep": Vector2(40.0, 3.0),
		"pitch_hold": 0.12,
		"seconds": 7.5,
	},
	{
		"name": "armor",
		"time": DAY,
		"start": Vector3(-52.0, 0.0, SHOP_STREET_Z),
		"path": [Vector3(-52.0, 0.0, -73.6)],
		"direct": true,
		"sweep": Vector2(40.0, 3.0),
		"pitch_hold": 0.22,
		"seconds": 7.5,
	},
	{
		"name": "magic",
		"time": DAY,
		"start": Vector3(-34.0, 0.0, SHOP_STREET_Z),
		"path": [Vector3(-34.0, 0.0, -74.0)],
		"direct": true,
		"sweep": Vector2(40.0, 3.0),
		"pitch_hold": 0.55,
		"seconds": 7.5,
	},
	{
		"name": "tavern",
		"time": DAY,
		"start": Vector3(16.0, 0.0, SHOP_STREET_Z),
		"path":
		[
			Vector3(16.0, 0.0, -70.2),
			Vector3(16.0, 0.0, -79.0),
			Vector3(13.0, 0.0, -79.0),
			Vector3(10.5, 0.0, -77.5),
		],
		"direct": true,
		"sweep": Vector2(40.0, 3.0),
		"pitch_hold": 0.1,
		"seconds": 7.5,
	},
	{
		"name": "alchemy",
		"time": DAY,
		"start": Vector3(34.0, 0.0, SHOP_STREET_Z),
		"path": [Vector3(34.0, 0.0, SHOP_INSIDE_Z)],
		"direct": true,
		"sweep": Vector2(40.0, 3.0),
		"pitch_hold": 0.2,
		"seconds": 7.5,
	},
	{
		"name": "general",
		"time": DAY,
		"start": Vector3(48.4, 0.0, SHOP_STREET_Z),
		"path": [Vector3(48.4, 0.0, SHOP_INSIDE_Z)],
		"direct": true,
		"sweep": Vector2(40.0, 3.0),
		"pitch_hold": 0.1,
		"seconds": 7.5,
	},
	{
		"name": "guild",
		"time": DAY,
		"start": Vector3(83.8, 0.0, SHOP_STREET_Z),
		"path": [Vector3(83.8, 0.0, -74.6)],
		"direct": true,
		"sweep": Vector2(35.0, 5.0),
		"pitch_hold": 0.22,
		"seconds": 17.0,
	},
	{
		"name": "square",
		"time": DAY,
		"start": Vector3(-24.0, 0.0, 9.0),
		"watch": "BenchCoupleHim",
		"near": Vector3(1.2, 0.0, 6.5),
		"seconds": 7.0,
	},
	{
		"name": "orphanage",
		"time": DAY,
		"start": Vector3(-60.0, 0.0, 0.0),
		"path": [Vector3(-71.0, 0.0, 0.0), Vector3(-82.0, 0.0, 0.0)],
		"sweep": Vector2(40.0, 3.0),
		"pitch_hold": 0.15,
		"seconds": 7.0,
	},
	{
		"name": "cathedral",
		"time": GOLDEN,
		"start": Vector3(4.0, 0.0, 0.0),
		"path": [Vector3(9.0, 0.0, 0.0), Vector3(13.0, NAVE, 0.0), Vector3(32.0, NAVE, 0.0)],
		"pitch": -0.05,
		"pitch_hold": 0.3,
		"seconds": 7.5,
	},
	{
		"name": "crypt",
		"time": GOLDEN,
		"start": Vector3(42.8, NAVE, 6.0),
		"path":
		[
			Vector3(42.8, NAVE, 7.4),
			Vector3(45.2, NAVE, 8.4),
			PUSH_SPOT,
			Vector3(49.5, NAVE, STAIR_Z),
			Vector3(49.0, NAVE, STAIR_Z),
			Vector3(40.9, CRYPT, STAIR_Z),
			Vector3(40.4, CRYPT, STAIR_Z),
			Vector3(40.4, CRYPT, 4.0),
			Vector3(40.0, CRYPT, -3.0),
		],
		"events": [{"at": 2.2, "press": &"interact"}],
		"waits": {3: 5.2},
		"direct": true,
		"seconds": 11.0,
	},
	{
		"name": "stars",
		"time": NIGHT,
		"start": Vector3(4.0, 0.0, 4.0),
		"path": [Vector3(4.0, 0.0, -2.0)],
		"stance": "walk",
		"pitch": 0.0,
		"pitch_hold": 1.32,
		"orbit": 8.0,
		"seconds": 8.0,
	},
	{
		"name": "fight",
		"time": GOLDEN,
		"start": Vector3(-26.0, 0.0, -6.0),
		"path": [],
		"side": 120.0,
		"orbit": 10.0,
		"events":
		[
			{"at": 0.4, "press": &"attack_punch"},
			{"at": 1.0, "press": &"attack_punch"},
			{"at": 1.6, "press": &"attack_kick"},
			{"at": 2.6, "press": &"attack_punch"},
			{"at": 3.2, "press": &"attack_kick"},
		],
		"seconds": 5.0,
	},
	{
		"name": "saci",
		"time": DAY,
		"start": Vector3(76.0, 0.0, 5.0),
		"near": Vector3(-7.0, 0.0, 0.0),
		"stance": "walk",
		"watch": "Saci",
		"side": -12.0,
		"seconds": 8.0,
	},
	{
		"name": "mula",
		"time": NIGHT,
		"start": Vector3(-8.0, 0.0, -61.0),
		"path": [Vector3(-8.0, 0.0, -61.0), Vector3(70.0, 0.0, -61.0)],
		"events": [{"at": 0.3, "press": &"summon_mount"}, {"at": 5.4, "press": &"interact"}],
		"waits": {1: 6.0},
		"direct": true,
		"seconds": 15.0,
	},
]
