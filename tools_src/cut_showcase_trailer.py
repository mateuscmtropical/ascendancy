"""Cut the action showcase trailer from the raw capture of tests/promo/showcase.tscn (60 fps) with ffmpeg.

Technique (new for this trailer): 3x3 grid hook that lights up tile by tile on the beat, fast beat-locked cuts
with sped-up gameplay, speed ramps on the hits (fast, then slow motion at impact), blurred whip transitions centred
on the act cuts, Bebas Neue location tags, full 16:9 frame, and the narration ducking a frenetic 160 BPM score that
is spliced on two phrase starts so its big hits land on the drop into the farm and on nightfall.

Usage: python tools_src/cut_showcase_trailer.py <raw.avi> <score> <narration> <fonts dir> <work dir> <output.mp4> [MB]
The fonts dir needs BebasNeue-Regular.ttf (SIL OFL; kept outside the repo).
"""

import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SHOTS_FILE = Path(__file__).resolve().parent.parent / "tests" / "promo" / "showcase_shots.gd"
WIDTH, HEIGHT, FPS = 1920, 1080, 30
SETTLE = 1.0  # cada clipe cru tem 1 s de sobra no começo
BEAT = 60.0 / 160.0  # trilha a 160 BPM
WHIP = BEAT * 0.75  # transição borrada entre atos, centrada no corte
LEAD = WHIP / 2
TAG_SECONDS = 6 * BEAT
FONT = "BebasNeue-Regular.ttf"
LOOK = "eq=contrast=1.06:saturation=1.18,unsharp=5:5:0.6"
# Trilha: SCORE_A_BEATS batidas a partir de SCORE_A (a pancada de 60.06 s cai no fim da grade) e o resto a partir
# de SCORE_B (a volta forte depois do respiro), que cai no começo da noite. Os dois pontos são começo de frase.
SCORE_A = 54.0624
SCORE_B = 156.0624
SCORE_A_BEATS = 112
# Grade: (clipe, casa da grade 0..8); uma peça acende por batida, nesta ordem
GRID_TILES = [(0, 0), (10, 4), (15, 8), (22, 2), (27, 6), (30, 1), (24, 7), (31, 3), (33, 5)]
GRID_BEATS = 16

# Atos: (etiqueta, [(clipe, batidas, velocidade, início no clipe depois da sobra), ...])
ACTS = [
    ("THE FARM", [(0, 4, 1.5, 0.0), (1, 4, 1.5, 0.0), (2, 3, 1.5, 0.0), (3, 3, 1.5, 0.0), (4, 4, 1.5, 0.0),
                  (5, 2, 2.0, 0.0), (6, 2, 2.0, 0.0), (7, 2, 2.0, 0.0)]),
    ("THE CONVENT", [(8, 4, 1.5, 0.0), (9, 3, 1.5, 0.0), (10, 3, 1.5, 0.0), (11, 3, 1.5, 0.0), (12, 2, 2.0, 0.0),
                     (13, 3, 1.5, 0.0), (14, 4, 1.4, 0.0)]),
    ("THE TOWN", [(15, 6, 1.0, 0.0), (16, 3, 1.5, 0.0), (17, 2, 2.0, 0.0), (18, 2, 2.0, 0.0), (19, 2, 2.0, 0.0),
                  (20, 3, 1.5, 0.0)]),
    ("THE CATHEDRAL", [(21, 4, 1.3, 0.0), (22, 3, 1.5, 0.0), (23, 3, 1.5, 0.0), (24, 4, 3.5, 0.0)]),
    ("THE CRYPT", [(25, 6, 1.2, -0.6), (26, 3, 1.5, 0.0), (27, 3, 1.5, 0.0), (28, 3, 1.5, 0.0), (29, 3, 1.5, 0.0)]),
    ("NIGHTFALL", [(30, 5, 1.4, 0.0), (31, 6, 1.0, 0.2), (32, 7, 1.0, 0.0), (33, 2, 1.2, 0.0), (33, 5, 0.4, 0.9),
                   (34, 4, 1.0, -0.9), (35, 2, 1.2, -0.9), (35, 5, 0.35, 0.0)]),
    ("", [(36, 24, 0.6, 0.0)]),
]
# Título: (texto, tamanho, cor, y, segundo em que entra)
TITLE_TEXTS = [
    ("ASCENDANCY", 230, "FFFFFF", "(h-text_h)/2", 1.0),
]
# Narração: (início e fim na faixa da voz, ato em que entra (None = grade), atraso em batidas)
VOICE_LINES = [
    ((0.00, 3.60), None, 4),  # One town. Every corner alive.
    ((3.75, 5.30), 0, 2),  # Fields at dawn.
    ((5.40, 8.35), 1, 2),  # Halls full of children learning magic.
    ((8.45, 10.60), 2, 3),  # Streets that never sleep.
    ((10.62, 14.95), 3, 2),  # But under the cathedral... there's a stair that shouldn't be there.
    ((15.05, 18.45), 5, 1),  # And when night falls... the legends ride.
    ((18.65, 20.10), 5, 16),  # Pick up your sword.
    ((20.25, 21.60), 6, 3),  # Ascendancy.
]


def clip_starts() -> list:
    """Start of every clip in the raw capture: the running sum of the "beats" (seconds) of showcase_shots.gd."""
    starts = [0.0]

    for length in clip_lengths()[:-1]:
        starts.append(starts[-1] + length)

    return starts


def clip_lengths() -> list:
    return [float(value) for value in re.findall(r'"beats":\s*([0-9.]+)', SHOTS_FILE.read_text(encoding="utf-8"))]


def act_beats() -> list:
    """Nominal length in beats of every piece of the montage: the grid, then each act."""
    return [GRID_BEATS] + [sum(shot[1] for shot in shots) for _, shots in ACTS]


def piece_starts() -> list:
    starts = [0.0]

    for beats in act_beats()[:-1]:
        starts.append(starts[-1] + beats * BEAT)

    return starts


def check() -> None:
    """Every shot must fit in its clip after the settle second, counting the whip lead and tail."""
    lengths = clip_lengths()
    problems = []

    assert sum(act_beats()[:-2]) == SCORE_A_BEATS, act_beats()

    for act_index, (_, shots) in enumerate(ACTS):
        for shot_index, (clip, beats, speed, offset) in enumerate(shots):
            lead, tail = whip_margins(act_index, shot_index)
            begin = SETTLE + offset - lead * speed
            end = SETTLE + offset + (beats * BEAT + tail) * speed

            if begin < 0.0 or end > lengths[clip]:
                problems.append(f"act {act_index} shot {shot_index} clip {clip}: {begin:.2f}..{end:.2f} of {lengths[clip]}")

    assert not problems, "\n".join(problems)


def whip_margins(act_index: int, shot_index: int) -> tuple:
    """Extra seconds before the first shot and after the last shot of an act, eaten by the whip transitions."""
    lead = LEAD if shot_index == 0 else 0.0
    tail = LEAD if shot_index == len(ACTS[act_index][1]) - 1 and act_index < len(ACTS) - 1 else 0.0

    return lead, tail


def run(command: list, work: Path) -> None:
    subprocess.run(["ffmpeg", "-y", "-v", "error", *command], cwd=work, check=True)


def encode_args() -> list:
    return ["-r", str(FPS), "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "12", "-pix_fmt", "yuv420p"]


def source_args(raw: Path, starts: list, clip: int, offset: float, seconds: float) -> list:
    return ["-ss", f"{starts[clip] + SETTLE + offset:.4f}", "-t", f"{seconds:.4f}", "-i", str(raw)]


def render_shot(raw: Path, starts: list, work: Path, name: str, shot: tuple, lead: float, tail: float) -> Path:
    clip, beats, speed, offset = shot
    length = beats * BEAT + lead + tail
    filters = f"setpts=(PTS-STARTPTS)/{speed},fps={FPS},{LOOK}"
    output = work / f"{name}.mp4"

    run([*source_args(raw, starts, clip, offset - lead * speed, length * speed + 0.1), "-vf", filters,
         "-frames:v", str(round(length * FPS)), *encode_args(), output.name], work)

    return output


def render_grid(raw: Path, starts: list, work: Path) -> Path:
    """3x3 wall of clips from every part of the game; one tile lights up per beat and plays from that moment."""
    length = GRID_BEATS * BEAT + LEAD
    inputs = []
    tiles = []
    order = {}

    for index, (clip, cell) in enumerate(GRID_TILES):
        appear = index * BEAT
        order[cell] = index
        inputs += source_args(raw, starts, clip, 0.0, length)
        tiles.append(f"[{index}:v]setpts=PTS-STARTPTS,fps={FPS},scale=636:356,pad=640:360:2:2:color=0x0A0A0A,"
                     f"tpad=start_duration={appear:.3f}:start_mode=clone:stop_mode=clone:stop_duration={length:.3f},"
                     f"fade=t=in:st={appear:.3f}:d=0.05,trim=duration={length:.3f}[t{index}]")

    layout = "|".join(f"{(cell % 3) * 640}_{(cell // 3) * 360}" for cell in range(9))
    stack = "".join(f"[t{order[cell]}]" for cell in range(9))
    graph = ";".join(tiles) + f";{stack}xstack=inputs=9:layout={layout},{LOOK}"
    output = work / "grid.mp4"
    run([*inputs, "-filter_complex", graph, "-frames:v", str(round(length * FPS)), *encode_args(), output.name], work)

    return output


def tag_filter(text: str, work: Path, name: str) -> str:
    """Location tag lower left, right after the whip: a gold bar, the word slides in, both leave together."""
    text_file = work / f"{name}.txt"
    text_file.write_text(text, encoding="utf-8")
    local = f"(t-{LEAD:.3f})"
    alpha = (f"if(lt({local},0),0,if(lt({local},0.12),{local}/0.12,"
             f"if(lt({local},{TAG_SECONDS - 0.25:.3f}),1,max(0,({TAG_SECONDS:.3f}-{local})/0.25))))")
    bar = f"drawbox=x=96:y=880:w=12:h=110:color=0xE8C46A:t=fill:enable='between({local},0,{TAG_SECONDS:.3f})'"
    word = (f"drawtext=fontfile=fonts/{FONT}:textfile={text_file.name}:fontsize=112:fontcolor=white"
            f":x='130+40*(1-min(1,max(0,{local})/0.2))':y=884:shadowcolor=black@0.6:shadowx=0:shadowy=4:alpha='{alpha}'")

    return f"{bar},{word}"


def title_filter(work: Path) -> str:
    length = act_beats()[-1] * BEAT + LEAD
    filters = ["eq=brightness=-0.08:saturation=0.85"]

    for index, (text, size, color, y, start) in enumerate(TITLE_TEXTS):
        text_file = work / f"title{index}.txt"
        text_file.write_text(text, encoding="utf-8")
        enter = start + LEAD
        grow = f"{size}*(1+0.25*max(0,1-(t-{enter:.3f})/0.3))"
        filters.append(f"drawtext=fontfile=fonts/{FONT}:textfile={text_file.name}:fontsize='{grow}':fontcolor=0x{color}"
                       f":x=(w-text_w)/2:y={y}:shadowcolor=black@0.7:shadowx=0:shadowy=5:enable='gte(t,{enter:.3f})'")

    filters.append(f"fade=t=out:st={length - 1.5:.3f}:d=1.5")

    return ",".join(filters)


def render_act(raw: Path, starts: list, work: Path, act_index: int, pool: ThreadPoolExecutor) -> Path:
    label, shots = ACTS[act_index]
    is_last = act_index == len(ACTS) - 1
    jobs = [(f"act{act_index}_{shot_index:02d}", shot, *whip_margins(act_index, shot_index)) for shot_index, shot in enumerate(shots)]
    parts = list(pool.map(lambda job: render_shot(raw, starts, work, *job), jobs))
    joined = work / f"act{act_index}_joined.mp4"
    output = work / f"act{act_index}.mp4"
    look = title_filter(work) if is_last else tag_filter(label, work, f"tag{act_index}")

    (work / f"act{act_index}.txt").write_text("".join(f"file '{part.name}'\n" for part in parts), encoding="utf-8")
    run(["-f", "concat", "-safe", "0", "-i", f"act{act_index}.txt", "-c", "copy", joined.name], work)
    run(["-i", joined.name, "-vf", look, *encode_args(), output.name], work)

    return output


def whip_chain(pieces: list, starts: list, work: Path) -> Path:
    """Joins the pieces with a blurred horizontal whip (xfade hblur) centred on each nominal cut, so the cuts stay
    on the beat: every piece but the first carries LEAD extra seconds before its start, every piece but the last
    LEAD extra seconds after its end."""
    inputs = []
    graph = []
    current = "[0:v]"

    for piece in pieces:
        inputs += ["-i", piece.name]

    for index in range(1, len(pieces)):
        graph.append(f"{current}[{index}:v]xfade=transition=hblur:duration={WHIP:.4f}:offset={starts[index] - LEAD:.4f}[x{index}]")
        current = f"[x{index}]"

    output = work / "montage.mp4"
    run([*inputs, "-filter_complex", ";".join(graph), "-map", current, *encode_args(), output.name], work)

    return output


def mix_audio(score: Path, voice: Path, starts: list, duration: float, work: Path) -> Path:
    """Score spliced on two phrase starts, narration lines placed on their acts, the score ducking under the voice."""
    inputs = ["-i", str(score)]
    lines = []
    a_end = SCORE_A + SCORE_A_BEATS * BEAT

    for index, ((start, end), act, delay_beats) in enumerate(VOICE_LINES):
        at = (0.0 if act is None else starts[act + 1]) + delay_beats * BEAT
        inputs += ["-i", str(voice)]
        lines.append(f"[{index + 1}:a]atrim={start}:{end},asetpts=PTS-STARTPTS,afade=t=in:d=0.03,"
                     f"afade=t=out:st={end - start - 0.06:.3f}:d=0.06,adelay={int(at * 1000)}|{int(at * 1000)}[v{index}]")

    count = len(VOICE_LINES)
    graph = f"[0:a]asplit=2[sa][sb];[sa]atrim={SCORE_A:.4f}:{a_end + 0.015:.4f},asetpts=PTS-STARTPTS[a]"
    graph += f";[sb]atrim={SCORE_B - 0.015:.4f},asetpts=PTS-STARTPTS[b];[a][b]acrossfade=d=0.03,atrim=0:{duration:.3f}"
    graph += f",afade=t=out:st={duration - 2.0:.3f}:d=2.0,volume=0.7[music];" + ";".join(lines)
    graph += ";" + "".join(f"[v{index}]" for index in range(count))
    graph += f"amix=inputs={count}:normalize=0,volume=1.4,apad=whole_dur={duration:.3f},asplit=2[voice][key]"
    graph += ";[music][key]sidechaincompress=threshold=0.02:ratio=8:attack=10:release=400[ducked]"
    graph += ";[ducked][voice]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1.0:LRA=11[out]"
    output = work / "mix.wav"
    run([*inputs, "-filter_complex", graph, "-map", "[out]", "-ar", "48000", output.name], work)

    return output


def finish(montage: Path, mix: Path, duration: float, work: Path, output: Path, megabytes: float) -> None:
    audio_kbps = 256
    video_kbps = int(megabytes * 8 * 1024 / duration - audio_kbps)
    encode = ["-c:v", "libx264", "-preset", "slow", "-b:v", f"{video_kbps}k", "-maxrate", f"{int(video_kbps * 1.6)}k",
              "-bufsize", f"{video_kbps * 2}k", "-pix_fmt", "yuv420p"]

    run(["-i", montage.name, *encode, "-pass", "1", "-an", "-t", f"{duration:.3f}", "-f", "mp4", "NUL"], work)
    run(["-i", montage.name, "-i", mix.name, *encode, "-pass", "2", "-c:a", "aac", "-b:a", f"{audio_kbps}k",
         "-t", f"{duration:.3f}", "-movflags", "+faststart", str(output)], work)


def main() -> None:
    raw, score, voice, fonts, work, output = (Path(argument).resolve() for argument in sys.argv[1:7])
    megabytes = float(sys.argv[7]) if len(sys.argv) > 7 else 88.0
    starts = clip_starts()
    piece_start_times = piece_starts()
    duration = sum(act_beats()) * BEAT

    check()
    work.mkdir(parents=True, exist_ok=True)

    if not (work / "fonts").exists():
        shutil.copytree(fonts, work / "fonts")

    with ThreadPoolExecutor(max_workers=6) as pool:
        pieces = [render_grid(raw, starts, work)] + [render_act(raw, starts, work, index, pool) for index in range(len(ACTS))]

    montage = whip_chain(pieces, piece_start_times, work)
    mix = mix_audio(score, voice, piece_start_times, duration, work)
    finish(montage, mix, duration, work, output, megabytes)
    print(f"CUT {output} {duration:.1f}s pieces at {[round(start, 2) for start in piece_start_times]}")


if __name__ == "__main__":
    main()
