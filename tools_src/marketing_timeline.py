"""Edit decision list of the marketing trailer, shared by the cut (cut_marketing_trailer.py) and the score
(compose_marketing_music.py) so every hit lands on its cut.

Each segment: start and length in output seconds; clip = index into tests/promo/marketing_shots.gd (None = black);
src = seconds into that clip (each clip carries 1 s of pre-roll); speed < 1 = slow motion from the 60 fps capture;
grade = colour preset; texts = (text, style, in, out) relative to the segment; flash/shake = moments relative to the
segment; zoom = (scale at start, scale at end) punch-in. CUES are the score's events in output seconds.
"""

DURATION = 72.0
BEAT = 0.5  # 120 BPM

ACT_OPEN, ACT_CITY, ACT_DUSK, ACT_NIGHT, ACT_FIGHT, ACT_TITLE = 0.0, 13.0, 35.0, 41.0, 47.5, 59.0
DROP = 19.0
FINAL_BOOM = 58.0


def segment(start: float, length: float, clip: int = None, src: float = 1.0, speed: float = 1.0, grade: str = "day", texts: tuple = (), flash: tuple = (), shake: tuple = (), zoom: tuple = (1.0, 1.04)) -> dict:
    return dict(start=start, length=length, clip=clip, src=src, speed=speed, grade=grade, texts=texts, flash=flash, shake=shake, zoom=zoom)


SEGMENTS = [
    # frio de abertura: a lenda
    segment(0.0, 3.0, texts=(("DIZEM QUE, NAS NOITES DE LUA DE SANGUE,", "card", 0.4, 2.8),)),
    segment(3.0, 5.0, clip=0, grade="night", zoom=(1.0, 1.08)),
    segment(8.0, 2.0, texts=(("ALGO GALOPA PELOS CAMPOS.", "card", 0.2, 1.9),)),
    segment(10.0, 1.5, clip=1, grade="fire", shake=(0.0,), zoom=(1.12, 1.2)),
    segment(11.5, 1.5),
    # a cidade
    segment(13.0, 6.0, clip=2, grade="dawn", texts=(("ANTES DA NOITE, HÁ UMA CIDADE INTEIRA.", "card", 1.0, 5.6),), zoom=(1.0, 1.05)),
    segment(19.0, 2.0, clip=3, flash=(0.0,), zoom=(1.0, 1.06)),
    segment(21.0, 1.0, clip=4),
    segment(22.0, 1.0, clip=5),
    segment(23.0, 2.0, clip=6, src=1.3, texts=(("EXPLORE", "word", 0.0, 1.5),)),
    segment(25.0, 1.0, clip=7),
    segment(26.0, 1.0, clip=8),
    segment(27.0, 1.0, clip=9, texts=(("NEGOCIE", "word", 0.0, 1.0),)),
    segment(28.0, 1.0, clip=10),
    segment(29.0, 1.0, clip=11),
    segment(30.0, 1.0, clip=12),
    segment(31.0, 1.0, clip=13, texts=(("VIVA", "word", 0.0, 1.0),)),
    segment(32.0, 1.0, clip=14),
    segment(33.0, 2.0, clip=15, zoom=(1.0, 1.08)),
    # o dia vira noite
    segment(35.0, 6.0, clip=16, speed=7.0 / 6.0, grade="dusk", texts=(("MAS QUANDO A LUA SANGRA...", "card", 2.0, 5.7),), zoom=(1.0, 1.06)),
    segment(41.0, 0.5),
    segment(41.5, 3.0, clip=17, grade="night", zoom=(1.0, 1.05)),
    segment(44.5, 3.0, clip=18, grade="night", zoom=(1.0, 1.06)),
    # a luta
    segment(47.5, 3.0, clip=19, src=1.0, speed=0.5, grade="fire", shake=(0.0, 2.6), zoom=(1.0, 1.1)),
    segment(50.5, 1.0, clip=20, src=1.0, grade="night", shake=(0.0,)),
    segment(51.5, 1.5, clip=21, src=1.2, grade="fire", shake=(0.0, 0.8)),
    segment(53.0, 1.5, clip=22, src=1.5, grade="night", flash=(0.5,), shake=(0.5,)),
    segment(54.5, 1.0, clip=23, src=1.1, grade="night", flash=(0.4,), shake=(0.4,)),
    segment(55.5, 1.5, clip=24, src=1.0, grade="fire", zoom=(1.0, 1.12)),
    segment(57.0, 0.25, clip=1, src=1.5, grade="fire", flash=(0.0,)),
    segment(57.25, 0.25, clip=22, src=2.4, grade="night", flash=(0.0,)),
    segment(57.5, 0.25, clip=21, src=2.0, grade="fire", flash=(0.0,)),
    segment(57.75, 0.25, clip=19, src=2.6, grade="fire", flash=(0.0,)),
    segment(58.0, 1.0),
    # título e fim
    segment(59.0, 7.0, clip=25, grade="title", texts=(("ASCENDANCY", "title", 0.6, 6.7), ("ENFRENTE AS LENDAS.  SUBA ANDAR POR ANDAR.", "sub", 2.6, 6.7)), zoom=(1.0, 1.04)),
    segment(66.0, 6.0, clip=26, grade="dawn", texts=(("SOZINHO OU COM AMIGOS", "card", 0.3, 2.8), ("EM BREVE", "title_small", 3.0, 6.0)), zoom=(1.0, 1.03)),
]

# trilha: momentos (segundos de saída) de cada efeito
CUES = {
    "bell_toll": (0.3, 5.0, 69.0),
    "hooves": ((8.0, 10.0), (45.0, 47.5)),
    "braam": (10.0, 47.5),
    "boom": (10.0, 47.5, FINAL_BOOM),
    "riser": ((35.5, 41.0), (16.5, 19.0)),
    "heartbeat": (41.5, 47.5),
    "taiko": tuple(50.5 + index * BEAT for index in range(15)),
    "hit": (19.0, 23.0, 27.0, 31.0, 50.5, 51.5, 53.0, 54.5, 55.5, 57.0, 57.25, 57.5, 57.75),
    "whoosh": (20.9, 24.9, 28.9, 32.9, 35.0, 41.4, 50.3, 58.9),
    "fire": ((10.0, 11.5), (47.5, 58.0)),
}


def check() -> None:
    """Segments tile the whole duration with no gap or overlap."""
    ends = [entry["start"] + entry["length"] for entry in SEGMENTS]
    starts = [entry["start"] for entry in SEGMENTS]

    assert starts[0] == 0.0 and abs(ends[-1] - DURATION) < 1e-6, (starts[0], ends[-1])
    assert all(abs(end - start) < 1e-6 for end, start in zip(ends, starts[1:])), [(end, start) for end, start in zip(ends, starts[1:]) if abs(end - start) > 1e-6]


if __name__ == "__main__":
    check()
    print(f"OK {len(SEGMENTS)} segments, {DURATION} s")
