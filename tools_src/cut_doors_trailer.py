"""Cut the "Every door opens somewhere" trailer from the gameplay captures of tests/promo/doors.tscn (60 fps).

The heroine is played for real (tests/promo/doors_director.gd); this script picks a stretch of each clip, joins the
shop entrances with a double-door wipe (ffmpeg xfade vertopen), builds the eight-shop mosaic whose last tile is the
guild, puts the English captions and the end title in IM FELL English (SIL OFL, kept outside the repo), cuts the
Google Flow Music score on its bars (75 BPM, bar = 3.2 s) and encodes one 1080p60 file sized to the target.

Usage: python tools_src/cut_doors_trailer.py <score.wav> <fonts dir> <work dir> <output.mp4> <MB> <capture.avi>=<clip,clip...> ...
Each capture is a recording of tests/promo/doors.tscn with --clips= set to the clips listed after its "=", in that order.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROUTE_FILE = Path(__file__).resolve().parent.parent / "tests" / "promo" / "doors_route.gd"
WIDTH, HEIGHT, FPS = 1920, 1080, 60
MUSIC_CROSSFADE = 0.8
# Trechos da trilha (segundos do arquivo do Flow Music), todos em começo de compasso: abertura e
# passeio, o silêncio da noite, a subida e o fim que se apaga sob o título.
MUSIC_PARTS = ((0.0, 38.816), (67.616, 80.416), (102.816, 122.016), (150.816, 166.816))
# Plano: (clipe, segundo dentro do clipe onde começa, duração na tela, legenda, transição para o próximo).
SHOTS = (
    ("tailor", 0.4, 6.4, "The Tailor’s Arcade", "door"),
    ("smith", 0.4, 3.2, "The Smithy", "door"),
    ("armor", 0.4, 3.2, "The Armoury", "door"),
    ("magic", 0.6, 3.2, "The Cabinet of Curiosities", "door"),
    ("tavern", 4.4, 3.2, "The Tavern", "door"),
    ("alchemy", 0.4, 3.2, "The Apothecary", "door"),
    ("general", 0.4, 3.2, "General Store & Bakery", "cut"),
    ("square", 1.0, 3.2, "The Square", "cut"),
    ("orphanage", 2.4, 3.2, "The Orphanage", "cut"),
    ("saci", 4.6, 3.2, "The Saci", "cut"),
    ("fight", 0.3, 3.2 + 1.0 / FPS, None, "fade"),
    ("cathedral", 1.2, 3.2, "The Cathedral", "cut"),
    ("crypt", 3.2, 2.3, "The Crypt", "cut"),
    ("crypt", 5.95, 4.1, None, "cut"),  # salta o instante em que a lente raspa a boca da escada
    ("stars", 4.0, 2.4, "The Night Sky", "fade"),
    ("mula", 2.4, 9.6, "The Headless Mule", "cut"),
    ("mosaic", 0.0, 8.8, None, "door"),
    ("guild", 0.3, 15.6, "The Adventurers’ Guild", "end"),
)
MOSAIC_TILES = (("tailor", 4.5), ("smith", 5.0), ("armor", 2.2), ("magic", 4.5), ("tavern", 5.5), ("alchemy", 3.0), ("general", 3.5), ("guild", 6.0))
MOSAIC_BEAT = 0.8
TITLE_AT = 7.2
TRANSITION_BY_KIND = {"door": ("vertopen", 0.3), "cut": ("fade", 1.0 / FPS), "fade": ("fadeblack", 0.6), "end": (None, 0.0)}
GRADE = "eq=contrast=1.05:saturation=1.12:gamma=0.98,colorbalance=rm=0.02:bm=-0.03,vignette=PI/6"


def read_clip_lengths() -> dict[str, float]:
    """Seconds of every clip of DoorsRoute, by name."""
    text = ROUTE_FILE.read_text(encoding="utf-8")
    names = re.findall(r'"name": "(\w+)"', text)
    seconds = [float(value) for value in re.findall(r'"seconds": ([\d.]+)', text)]
    return dict(zip(names, seconds))


def clip_sources(captures: list[str]) -> dict[str, tuple[Path, float]]:
    """Clip name -> (capture file, second where the clip starts in it), from "<file>=<clip,clip...>" arguments;
    a clip recorded again in a later capture replaces the earlier take."""
    lengths = read_clip_lengths()
    sources = {}

    for capture in captures:
        path, names = capture.rsplit("=", 1)
        start = 0.0

        for name in names.split(","):
            sources[name] = (Path(path).resolve(), start)
            start += lengths[name]

    return sources


def run(arguments: list) -> None:
    subprocess.run([str(argument) for argument in arguments], check=True)


def caption_filter(caption: str, duration: float, fonts: Path, work: Path, index: int) -> str:
    """Small caption bottom left, fading in after the cut and out before the next."""
    text_file = work / f"caption{index:02d}.txt"
    alpha = f"if(lt(t\\,0.35)\\,0\\,if(lt(t\\,0.75)\\,(t-0.35)/0.4\\,if(gt(t\\,{duration - 0.5:.2f})\\,max(0\\,({duration - 0.1:.2f}-t)/0.4)\\,1)))"

    text_file.write_text(caption, encoding="utf-8")
    return f"drawtext=fontfile='IMFellEnglish-Regular.ttf':textfile='{text_file.name}':fontsize=54:fontcolor=white:alpha={alpha}:shadowcolor=black@0.6:shadowx=2:shadowy=2:x=90:y=h-150"


def title_filter(fonts: Path, start: float) -> str:
    """End title and line, fading in over the last shot."""
    fade = f"if(lt(t\\,{start})\\,0\\,min(1\\,(t-{start})/1.2))"
    title = f"drawtext=fontfile='IMFellEnglishSC.ttf':text='Ascendancy':fontsize=170:fontcolor=white:alpha={fade}:shadowcolor=black@0.7:shadowx=3:shadowy=3:x=(w-text_w)/2:y=h/2-150"
    line = f"drawtext=fontfile='IMFellEnglish-Regular.ttf':text='Every door opens somewhere.':fontsize=56:fontcolor=white:alpha={fade}:shadowcolor=black@0.7:shadowx=2:shadowy=2:x=(w-text_w)/2:y=h/2+60"
    return f"{title},{line}"


def render_shot(index: int, shot: tuple, sources: dict, fonts: Path, work: Path) -> Path:
    """One shot, graded and captioned, long enough to overlap the next one by its transition."""
    name, offset, duration, caption, kind = shot
    length = duration + TRANSITION_BY_KIND[kind][1]
    capture, clip_start = sources[name]
    filters = [GRADE]
    output = work / f"shot{index:02d}.mp4"

    if caption:
        filters.append(caption_filter(caption, TITLE_AT if kind == "end" else length, fonts, work, index))

    if kind == "end":
        filters.append(f"eq=brightness=-0.14*min(1\\,max(0\\,(t-{TITLE_AT})/1.2)):eval=frame")
        filters.append(title_filter(fonts, TITLE_AT))
        filters.append(f"fade=t=out:st={length - 2.0:.2f}:d=2.0")

    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{clip_start + offset:.3f}", "-t", f"{length:.3f}", "-i", capture, "-vf", ",".join(filters), "-r", FPS, "-an", "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-pix_fmt", "yuv420p", output.name])
    return output


def render_mosaic(index: int, shot: tuple, sources: dict, fonts: Path, work: Path) -> Path:
    """The eight shop halls side by side, 4 x 2, one more tile on every beat; the guild comes last."""
    length = shot[2] + TRANSITION_BY_KIND[shot[4]][1]
    tile_width, tile_height = WIDTH // 4, HEIGHT // 2
    inputs = []
    filters = [f"color=c=0x0b0b0e:s={WIDTH}x{HEIGHT}:r={FPS}:d={length:.3f}[base0]"]
    output = work / f"shot{index:02d}.mp4"

    for tile, (name, offset) in enumerate(MOSAIC_TILES):
        capture, clip_start = sources[name]
        appear = tile * MOSAIC_BEAT
        x, y = (tile % 4) * tile_width, (tile // 4) * tile_height
        inputs += ["-ss", f"{max(0.0, clip_start + offset - appear):.3f}", "-t", f"{length:.3f}", "-i", capture]
        filters.append(f"[{tile}:v]{GRADE},crop=ih*{tile_width}/{tile_height}:ih,scale={tile_width - 6}:{tile_height - 6},fps={FPS},format=yuva420p,fade=t=in:st={appear:.2f}:d=0.3:alpha=1[tile{tile}]")
        filters.append(f"[base{tile}][tile{tile}]overlay={x + 3}:{y + 3}:enable='gte(t,{appear:.2f})'[base{tile + 1}]")

    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filters), "-map", f"[base{len(MOSAIC_TILES)}]", "-t", f"{length:.3f}", "-r", FPS, "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-pix_fmt", "yuv420p", output.name])
    return output


def join_shots(shot_files: list[Path], work: Path) -> Path:
    """Chain the shots with each one's transition (xfade at the end of its on-screen time)."""
    inputs = []
    filters = []
    offset = 0.0
    previous = "0:v"
    output = work / "picture.mp4"

    for path in shot_files:
        inputs += ["-i", path.name]

    for index, shot in enumerate(SHOTS[:-1]):
        transition, duration = TRANSITION_BY_KIND[shot[4]]
        offset += shot[2]
        label = f"v{index + 1}"
        filters.append(f"[{previous}][{index + 1}:v]xfade=transition={transition}:duration={duration:.4f}:offset={offset:.4f}[{label}]")
        previous = label

    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filters), "-map", f"[{previous}]", "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-pix_fmt", "yuv420p", output.name])
    return output


def cut_score(score: Path, work: Path) -> Path:
    """The score cut on its bars, each part crossfaded into the next over one beat, faded out at the end."""
    inputs = []
    filters = []
    previous = "a0"
    total = sum(end - start for start, end in MUSIC_PARTS) - (len(MUSIC_PARTS) - 1) * MUSIC_CROSSFADE
    output = work / "score.wav"

    for index, (start, end) in enumerate(MUSIC_PARTS):
        inputs += ["-ss", f"{start:.3f}", "-t", f"{end - start:.3f}", "-i", score]
        filters.append(f"[{index}:a]anull[a{index}]")

    for index in range(1, len(MUSIC_PARTS)):
        label = f"m{index}"
        filters.append(f"[{previous}][a{index}]acrossfade=d={MUSIC_CROSSFADE}:c1=tri:c2=tri[{label}]")
        previous = label

    filters.append(f"[{previous}]afade=t=out:st={total - 3.0:.2f}:d=3.0,alimiter=limit=0.89[out]")
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[out]", output.name])
    return output


def encode(picture: Path, music: Path, output: Path, megabytes: float, work: Path) -> None:
    """Two-pass H.264 + AAC sized to the target, fast start for the web."""
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", picture.name], capture_output=True, text=True, check=True)
    duration = float(probe.stdout.strip())
    video_kbps = int(megabytes * 8192 / duration - 192)
    common = ["-i", picture.name, "-i", music.name, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-b:v", f"{video_kbps}k", "-pix_fmt", "yuv420p", "-shortest"]

    run(["ffmpeg", "-v", "error", "-y", *common, "-pass", "1", "-passlogfile", "pass", "-an", "-f", "mp4", "NUL"])
    run(["ffmpeg", "-v", "error", "-y", *common, "-pass", "2", "-passlogfile", "pass", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", output])


def main() -> None:
    score, fonts, work, output = (Path(argument).resolve() for argument in sys.argv[1:5])
    megabytes = float(sys.argv[5])
    sources = clip_sources(sys.argv[6:])
    renderers = {"mosaic": render_mosaic}

    work.mkdir(parents=True, exist_ok=True)
    os.chdir(work)  # ffmpeg filter options take bare file names here (no drive colon to escape)

    for font_file in fonts.glob("*.ttf"):
        shutil.copy(font_file, work / font_file.name)

    shot_files = [renderers.get(shot[0], render_shot)(index, shot, sources, fonts, work) for index, shot in enumerate(SHOTS)]
    encode(join_shots(shot_files, work), cut_score(score, work), output, megabytes, work)


if __name__ == "__main__":
    main()
