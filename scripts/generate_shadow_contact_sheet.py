from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from flatshot.core.engine import ShadowEngine
from flatshot.core.models import ShadowSettings


def checker(size: tuple[int, int], a=(238, 238, 238), b=(210, 210, 210), step: int = 24) -> Image.Image:
    img = Image.new("RGB", size, a)
    draw = ImageDraw.Draw(img)
    for y in range(0, size[1], step):
        for x in range(0, size[0], step):
            if ((x // step) + (y // step)) % 2:
                draw.rectangle((x, y, x + step - 1, y + step - 1), fill=b)
    return img


def composite_for_sheet(image: Image.Image, transparent: bool) -> Image.Image:
    if image.mode == "RGBA":
        bg = checker(image.size) if transparent else Image.new("RGB", image.size, (245, 245, 245))
        bg.paste(image, (0, 0), mask=image)
        return bg
    return image.convert("RGB")


def make_fixture(name: str, size=(700, 920)) -> tuple[Image.Image, bool]:
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    w, h = size
    transparent_bg = name.endswith("transparente")

    if name == "alpha limpio":
        draw.rounded_rectangle((190, 190, 510, 660), radius=20, fill=(70, 110, 190, 255))
    elif name == "prenda larga":
        draw.rounded_rectangle((245, 95, 455, 790), radius=28, fill=(38, 54, 70, 245))
        draw.polygon((245, 395, 170, 755, 290, 790), fill=(38, 54, 70, 230))
        draw.polygon((455, 395, 530, 755, 410, 790), fill=(38, 54, 70, 230))
    elif name == "calzado":
        draw.ellipse((150, 455, 535, 660), fill=(35, 35, 38, 250))
        draw.rounded_rectangle((230, 365, 450, 545), radius=35, fill=(55, 65, 82, 245))
        draw.rectangle((125, 585, 555, 660), fill=(20, 20, 20, 230))
    elif name == "percha":
        draw.arc((250, 105, 450, 310), 195, 345, fill=(60, 60, 60, 240), width=12)
        draw.line((350, 205, 205, 365, 495, 365, 350, 205), fill=(55, 55, 55, 230), width=12)
        draw.rounded_rectangle((210, 370, 490, 720), radius=18, fill=(180, 110, 80, 180))
    elif name == "objeto pequeño":
        draw.rounded_rectangle((310, 430, 390, 535), radius=10, fill=(190, 70, 48, 255))
    elif name == "objeto grande":
        draw.rounded_rectangle((95, 85, 605, 835), radius=30, fill=(64, 120, 110, 248))
    elif name == "pegado al borde":
        draw.rounded_rectangle((0, 80, 355, 655), radius=22, fill=(82, 62, 150, 245))
    elif name == "fondo blanco":
        draw.rounded_rectangle((200, 180, 500, 700), radius=18, fill=(225, 225, 218, 255))
        transparent_bg = False
    elif name == "fondo transparente":
        draw.rounded_rectangle((200, 180, 500, 700), radius=18, fill=(65, 130, 205, 220))
        transparent_bg = True
    return img, transparent_bg


def render_pair(
    source: Image.Image,
    transparent: bool,
    target_size: tuple[int, int],
    noise: int,
) -> tuple[Image.Image, Image.Image]:
    common = dict(
        adaptive_zoom=False,
        angle=180,
        distance=28,
        blur=28,
        contact_blur=10,
        opacity=34,
        noise=noise,
        transparent_bg=transparent,
        bg_color=(245, 245, 245),
    )
    legacy = ShadowEngine.aplicar_efectos(
        source,
        ShadowSettings(**common, shadow_engine="legacy"),
        target_size,
    )
    realistic = ShadowEngine.aplicar_efectos(
        source,
        ShadowSettings(**common, shadow_engine="realistic_v2"),
        target_size,
    )
    return composite_for_sheet(legacy, transparent), composite_for_sheet(realistic, transparent)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a legacy/V2 shadow comparison contact sheet.")
    parser.add_argument(
        "--output",
        default=str(ROOT / "artifacts" / "shadow_contact_sheet.png"),
        help="Output PNG path.",
    )
    parser.add_argument("--noise", type=int, default=0, help="Noise value used in both engines.")
    args = parser.parse_args()

    cases = [
        "alpha limpio",
        "prenda larga",
        "calzado",
        "percha",
        "objeto pequeño",
        "objeto grande",
        "pegado al borde",
        "fondo blanco",
        "fondo transparente",
    ]
    target = (320, 420)
    label_h = 34
    gap = 14
    row_h = target[1] + label_h + gap
    sheet_w = target[0] * 2 + gap * 3
    sheet_h = row_h * len(cases) + gap
    sheet = Image.new("RGB", (sheet_w, sheet_h), (248, 248, 248))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    draw.text((gap, 8), "Legacy", fill=(20, 20, 20), font=font)
    draw.text((target[0] + gap * 2, 8), "Realista V2", fill=(20, 20, 20), font=font)

    for row, name in enumerate(cases):
        source, transparent = make_fixture(name)
        legacy, realistic = render_pair(source, transparent, target, max(0, args.noise))
        y = gap + row * row_h + label_h
        draw.text((gap, y - 24), name, fill=(35, 35, 35), font=font)
        sheet.paste(legacy, (gap, y))
        sheet.paste(realistic, (target[0] + gap * 2, y))
        draw.rectangle((gap, y, gap + target[0] - 1, y + target[1] - 1), outline=(210, 210, 210))
        x2 = target[0] + gap * 2
        draw.rectangle((x2, y, x2 + target[0] - 1, y + target[1] - 1), outline=(210, 210, 210))

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
