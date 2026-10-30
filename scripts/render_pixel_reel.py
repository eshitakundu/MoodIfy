"""Animate CC0 pixel-art scenes into short clips for the TV wall.

Each scene is built from its layers: they scroll at different speeds (parallax),
and night scenes get rain, twinkling stars or flickering lights. Frames are drawn
at the art's own resolution and scaled up with nearest-neighbour so pixels stay
crisp, then encoded to web/media/clips/clip-NN.mp4 at 512x320.

Sources (all CC0) are listed in web/media/clips/SOURCES.md. The packs themselves
are not in the repo: download them into work/pixel-src/<slug>/ to re-render.

    python scripts/render_pixel_reel.py [scene-name ...]
"""
from __future__ import annotations

import json
import math
import random
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "work" / "pixel-src"
OUT = ROOT / "web" / "media" / "clips"
OUT_W, OUT_H, FPS, SECONDS = 512, 320, 24, 5


@dataclass
class Layer:
    path: str
    speed: float = 0.0          # source pixels per second, positive scrolls left
    y: str = "bottom"           # bottom | top | fill (scale to the view height)
    tile: bool = True
    x: float = 0.0              # start position for untiled sprites
    bob: float = 0.0            # gentle vertical drift, in source pixels


@dataclass
class Scene:
    name: str
    pack: str
    layers: list[Layer]
    height: int                 # view height in source pixels; width follows 16:10
    scale_to: int | None = None  # pre-scale large art to this height (smooth), for hi-res packs
    rain: int = 0               # raindrops per frame at output size
    stars: int = 0              # twinkling stars in the top half
    flicker: float = 0.0        # brightness wobble, 0..0.2
    gif: str | None = None      # play an animated GIF instead of layers
    pan: float = 0.0            # single image larger than the view: 1 = ease across it once
    extra: dict = field(default_factory=dict)


L = Layer
SCENES = [
    Scene("future-alley", "future-city-27", [L("future_city_27.png", 0, "top", tile=False)],
          height=160, pan=1, rain=70, flicker=0.06),
    Scene("neon-sign-city", "neon-city-0", [], height=94, gif="neon_city_0.gif"),
    Scene("rooftops", "city-parallax-pixel-art", [
        L("City/BG.png", 0, "fill"), L("City/Background 1.png", 4, "fill"), L("City/Middle.png", 10, "fill"),
        L("City/Foreground.png", 20, "fill")], height=135, stars=25),
    Scene("cyber-street", "warped-city-2", [
        L("cyberpunk city 2 files/Environment/background/back.png", 2, "fill"),
        L("cyberpunk city 2 files/Environment/background/middle.png", 7, "fill"),
        L("cyberpunk city 2 files/Environment/background/front.png", 16, "fill")], height=160, rain=55, flicker=0.05),
    Scene("dusk-skyline", "skyline-background", [
        L("Background_City_Skyline/Layers/Background_City_Skyline_Atmosfere_02.png", 0, "fill"),
        L("Background_City_Skyline/Layers/Background_City_Skyline_Cloud_02.png", 3, "fill"),
        L("Background_City_Skyline/Layers/Background_City_Skyline_Back_02.png", 6, "fill"),
        L("Background_City_Skyline/Layers/Background_City_Skyline_Front_02.png", 12, "fill")], height=170),
    Scene("night-ocean", "warped-ocean-view", [
        L("Ocean View Files/Layers/Night/Back.png", 2, "fill"),
        L("Ocean View Files/Layers/Night/Clouds.png", 6, "fill"),
        L("Ocean View Files/Layers/Night/Middle.png", 12, "fill")], height=240, stars=50),
    Scene("miami-drive", "warped-miami-synth", [
        L("Miami-synth-files/Layers/back.png", 0, "fill"), L("Miami-synth-files/Layers/sun.png", 0, "fill"),
        L("Miami-synth-files/Layers/buildings.png", 8, "fill"), L("Miami-synth-files/Layers/palms.png", 18, "fill"),
        L("Miami-synth-files/Layers/highway.png", 60, "fill")], height=240),
    Scene("four-colour-night", "parallax-city-night-4-colors", [
        L("CityBackground/sCitySky.png", 0, "fill"), L("CityBackground/sCityFar.png", 4, "fill"),
        L("CityBackground/sCityMid.png", 9, "fill"), L("CityBackground/sCityClose.png", 18, "fill")],
          height=144, rain=40),
    Scene("night-city-pan", "pixel-night-city", [L("fondo.png", 0, "top", tile=False)],
          height=300, pan=1, stars=30, flicker=0.04),
    Scene("seaview", "background-seaview-parallax", [
        L("seaview_background/seaview_sky.png", 0, "fill"), L("seaview_background/seaview_clouds.png", 10, "fill"),
        L("seaview_background/seaview_sea.png", 4, "fill"), L("seaview_background/seaview_hills.png", 8, "fill"),
        L("seaview_background/seaview_foreground.png", 16, "fill")], height=320, scale_to=320),
    Scene("warped-city", "warped-city", [
        L("warped city files/demo/assets/environment/bg-1.png", 2, "fill"),
        L("warped city files/demo/assets/environment/bg-2.png", 7, "fill"),
        L("warped city files/demo/assets/environment/bg-3.png", 16, "fill")], height=224, rain=60, flicker=0.05),
    Scene("magic-cliffs", "magic-cliffs-environment", [
        L("Magic-Cliffs-Environment/PNG/sky.png", 0, "fill"), L("Magic-Cliffs-Environment/PNG/clouds.png", 6, "top"),
        L("Magic-Cliffs-Environment/PNG/sea.png", 10, "bottom"),
        L("Magic-Cliffs-Environment/PNG/far-grounds.png", 14, "bottom")], height=240),
    Scene("deep-space", "space-background-3", [
        L("space_background_pack/layers/parallax-space-backgound.png", 0, "fill"),
        L("space_background_pack/layers/parallax-space-stars.png", 4, "fill"),
        L("space_background_pack/layers/parallax-space-far-planets.png", 8, "fill"),
        L("space_background_pack/layers/parallax-space-ring-planet.png", 12, "top", tile=False, x=150, bob=3),
        L("space_background_pack/layers/parallax-space-big-planet.png", 6, "top", tile=False, x=40, bob=2)],
          height=160, stars=30),
    Scene("industrial", "industrial-parallax-background", [
        L("parallax-industrial-pack/layers/skill-desc_0003_bg.png", 0, "fill"),
        L("parallax-industrial-pack/layers/skill-desc_0002_far-buildings.png", 5, "bottom"),
        L("parallax-industrial-pack/layers/skill-desc_0001_buildings.png", 11, "bottom"),
        L("parallax-industrial-pack/layers/skill-desc_0000_foreground.png", 22, "bottom")], height=160, flicker=0.05),
    Scene("mountain-dusk", "mountain-at-dusk-background", [
        L("parallax_mountain_pack/layers/parallax-mountain-bg.png", 0, "fill"),
        L("parallax_mountain_pack/layers/parallax-mountain-montain-far.png", 3, "fill"),
        L("parallax_mountain_pack/layers/parallax-mountain-mountains.png", 7, "fill"),
        L("parallax_mountain_pack/layers/parallax-mountain-trees.png", 14, "fill"),
        L("parallax_mountain_pack/layers/parallax-mountain-foreground-trees.png", 24, "fill")], height=160),
]


def load(scene: Scene, layer: Layer) -> Image.Image:
    image = Image.open(SRC / scene.pack / layer.path).convert("RGBA")
    if scene.scale_to and image.height != scene.scale_to:
        image = image.resize((round(image.width * scene.scale_to / image.height), scene.scale_to), Image.LANCZOS)
    if layer.y == "fill" and image.height != scene.height:
        image = image.resize((max(1, round(image.width * scene.height / image.height)), scene.height), Image.NEAREST)
    return image


def paste(frame: Image.Image, image: Image.Image, x: int, y: int) -> None:
    """alpha_composite needs a non-negative destination, so clip the source instead."""
    frame.alpha_composite(image, (max(x, 0), max(y, 0)), (max(-x, 0), max(-y, 0)))


def draw_layer(frame: Image.Image, image: Image.Image, layer: Layer, t: float) -> None:
    view_w, view_h = frame.size
    top = view_h - image.height if layer.y == "bottom" else 0
    top += round(math.sin(t * 1.3) * layer.bob)
    if not layer.tile:
        paste(frame, image, round(layer.x - layer.speed * t), top)
        return
    x = -(int(layer.speed * t) % image.width)
    while x < view_w:
        paste(frame, image, x, top)
        x += image.width


def render_frames(scene: Scene):
    rng = random.Random(scene.name)
    total = FPS * SECONDS
    if scene.gif:
        gif = Image.open(SRC / scene.pack / scene.gif)
        frames = []
        for i in range(gif.n_frames):
            gif.seek(i)
            frames.append(gif.convert("RGBA"))
        crop_h = round(frames[0].width / 1.6)
        top = (frames[0].height - crop_h) // 2
        for n in range(total):
            yield frames[n % len(frames)].crop((0, top, frames[0].width, top + crop_h))
        return
    layers = [(layer, load(scene, layer)) for layer in scene.layers]
    view_h = scene.height if not scene.scale_to else scene.scale_to
    view_w = round(view_h * 1.6)
    stars = [(rng.random(), rng.random() * 0.5, rng.random() * 6.28) for _ in range(scene.stars)]
    for n in range(total):
        t = n / FPS
        frame = Image.new("RGBA", (view_w, view_h), (8, 8, 16, 255))
        for layer, image in layers:
            if scene.pan and not layer.tile:
                span_x = max(0, image.width - view_w)
                span_y = max(0, image.height - view_h)
                p = (math.sin(t / SECONDS * math.pi - math.pi / 2) + 1) / 2
                paste(frame, image, -round(span_x * p), -round(span_y * p))
            else:
                draw_layer(frame, image, layer, t)
        if stars:
            draw = ImageDraw.Draw(frame)
            for sx, sy, phase in stars:
                glow = (math.sin(t * 3 + phase) + 1) / 2
                if glow > 0.55:
                    level = int(150 + 105 * glow)
                    draw.point((int(sx * view_w), int(sy * view_h)), fill=(level, level, 255, 255))
        if scene.flicker:
            dip = 1 - scene.flicker * (0.5 + 0.5 * math.sin(t * 9)) * (1 if rng.random() > 0.15 else 2)
            frame = ImageEnhance.Brightness(frame).enhance(dip)
        yield frame


def add_rain(frame: Image.Image, n: int, count: int, rng_seed: str) -> Image.Image:
    rng = random.Random(rng_seed)
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    drops = [(rng.random() * OUT_W * 1.3, rng.random() * OUT_H, 9 + rng.random() * 9) for _ in range(count)]
    for x0, y0, speed in drops:
        y = (y0 + n * speed) % (OUT_H + 20) - 20
        x = x0 - (y - y0) * 0.25 - OUT_W * 0.15
        draw.line((x, y, x - 3, y + 11), fill=(170, 190, 230, 110), width=1)
    return Image.alpha_composite(frame, overlay)


def render(scene: Scene, index: int) -> Path:
    out = OUT / f"clip-{index:02d}.mp4"
    ffmpeg = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OUT_W}x{OUT_H}",
         "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "28", "-g", "6",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    for n, frame in enumerate(render_frames(scene)):
        # cover-crop to 16:10, then scale up with hard pixel edges
        w, h = frame.size
        if w / h > 1.6:
            cw = round(h * 1.6); frame = frame.crop(((w - cw) // 2, 0, (w - cw) // 2 + cw, h))
        elif w / h < 1.6:
            ch = round(w / 1.6); frame = frame.crop((0, (h - ch) // 2, w, (h - ch) // 2 + ch))
        frame = frame.resize((OUT_W, OUT_H), Image.NEAREST)
        if scene.rain:
            frame = add_rain(frame, n, scene.rain, scene.name)
        ffmpeg.stdin.write(frame.convert("RGB").tobytes())
    ffmpeg.stdin.close()
    ffmpeg.wait()
    return out


def build_reel() -> None:
    """Join every clip into media/reel.mp4 with a segment index the page cuts between.

    The clips share one encoding, so they are concatenated without re-encoding."""
    clips = sorted(OUT.glob("clip-*.mp4"))
    listing = OUT / "reel.txt"
    listing.write_text("".join(f"file '{clip.name}'\n" for clip in clips), encoding="utf-8")
    reel = OUT.parent / "reel.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-c", "copy", "-movflags", "+faststart", str(reel)], check=True)
    listing.unlink()
    segments = [{"start": round(i * SECONDS, 3), "duration": SECONDS} for i in range(len(clips))]
    (OUT.parent / "reel.json").write_text(json.dumps({"duration": len(clips) * SECONDS, "segments": segments}),
                                          encoding="utf-8")
    print(f"reel.mp4: {len(clips)} clips, {reel.stat().st_size // 1024} KB")


def main(names: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for index, scene in enumerate(SCENES, start=1):
        if names and scene.name not in names:
            continue
        print(f"clip-{index:02d}  {scene.name}  ->", render(scene, index).name)
    build_reel()


if __name__ == "__main__":
    main(sys.argv[1:])
