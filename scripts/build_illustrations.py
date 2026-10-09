"""Write the NaviCare illustrations into assets/.

These are small original drawings, sized for GitHub and Streamlit.
Run from the repo root: python scripts/build_illustrations.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets"

TEAL = (21, 132, 119)
NAVY = (39, 80, 106)
CORAL = (233, 130, 104)
CREAM = (255, 253, 249)
MINT = (229, 246, 240)
WHITE = (255, 255, 255)
SKIN = (243, 213, 196)
SKIN_DEEP = (224, 184, 160)


def gradient(
    size: tuple[int, int], start: tuple[int, int, int], end: tuple[int, int, int]
) -> Image.Image:
    width, height = size
    image = Image.new("RGB", size, start)
    draw = ImageDraw.Draw(image)
    for y in range(height):
        mix = y / max(height - 1, 1)
        color = tuple(
            int(start[channel] + (end[channel] - start[channel]) * mix)
            for channel in range(3)
        )
        draw.line([(0, y), (width, y)], fill=color)
    return image


def blob(
    base: Image.Image,
    center: tuple[int, int],
    radius: int,
    color: tuple[int, int, int],
    alpha: int,
) -> None:
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    x, y = center
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*color, alpha))
    composed = Image.alpha_composite(base.convert("RGBA"), overlay)
    base.paste(composed.convert("RGB"))


def person(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    scale: float,
    cloth: tuple[int, int, int],
    skin: tuple[int, int, int] = SKIN,
) -> None:
    head = int(54 * scale)
    body_w = int(92 * scale)
    body_h = int(150 * scale)
    head_top = y
    draw.ellipse((x - head, head_top, x + head, head_top + head * 2), fill=skin)
    body_top = head_top + int(head * 1.7)
    draw.rounded_rectangle(
        (x - body_w // 2, body_top, x + body_w // 2, body_top + body_h),
        radius=int(36 * scale),
        fill=cloth,
    )


def save_logo() -> None:
    size = 256
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 8, size - 8, size - 8), radius=56, fill=(*TEAL, 255))
    draw.line(
        [(52, 176), (96, 124), (132, 156), (196, 76)],
        fill=(*WHITE, 255),
        width=16,
        joint="curve",
    )
    draw.ellipse((176, 52, 220, 96), fill=(*CORAL, 255))
    draw.ellipse((190, 66, 206, 82), fill=(*WHITE, 255))
    image.save(ASSET_DIR / "navicare_logo_mark.png", optimize=True)


def save_hero() -> None:
    image = gradient((1400, 860), (223, 246, 238), (255, 240, 231))
    blob(image, (1120, 150), 240, CORAL, 70)
    blob(image, (220, 720), 280, TEAL, 50)
    blob(image, (760, 120), 140, NAVY, 28)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((150, 660, 1250, 760), radius=70, fill=WHITE)
    draw.arc((180, 530, 1220, 860), 200, 340, fill=TEAL, width=8)
    person(draw, 400, 250, 1.15, TEAL)
    person(draw, 700, 330, 0.82, CORAL, SKIN_DEEP)
    person(draw, 1000, 230, 1.22, NAVY)
    image.save(ASSET_DIR / "navicare_hero.png", optimize=True)


def save_scheme() -> None:
    image = gradient((1400, 900), CREAM, MINT)
    blob(image, (160, 140), 160, TEAL, 40)
    blob(image, (1240, 760), 200, CORAL, 45)
    draw = ImageDraw.Draw(image)
    cards = [
        (140, 200, 480, 760, TEAL),
        (530, 280, 870, 760, NAVY),
        (920, 360, 1260, 760, CORAL),
    ]
    for left, top, right, bottom, color in cards:
        draw.rounded_rectangle((left, top, right, bottom), radius=36, fill=WHITE)
        draw.rectangle((left, top, right, top + 16), fill=color)
        draw.rounded_rectangle(
            (left + 40, top + 80, right - 70, top + 132), radius=14, fill=color
        )
        draw.rounded_rectangle(
            (left + 40, top + 170, right - 110, top + 206), radius=10, fill=MINT
        )
        draw.rounded_rectangle(
            (left + 40, top + 230, right - 160, top + 266),
            radius=10,
            fill=(232, 239, 236),
        )
    draw.rounded_rectangle((620, 48, 780, 188), radius=36, fill=TEAL)
    draw.line([(700, 84), (700, 152)], fill=WHITE, width=12)
    draw.line([(666, 118), (734, 118)], fill=WHITE, width=12)
    image.save(ASSET_DIR / "navicare_scheme.png", optimize=True)


def save_conversation() -> None:
    image = gradient((1400, 900), (255, 248, 244), (230, 244, 250))
    blob(image, (200, 160), 180, CORAL, 40)
    blob(image, (1180, 150), 160, TEAL, 45)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((160, 700, 1240, 800), radius=60, fill=WHITE)
    person(draw, 420, 360, 1.15, TEAL)
    person(draw, 980, 360, 1.15, NAVY)
    draw.rounded_rectangle((180, 80, 620, 250), radius=32, fill=WHITE)
    draw.polygon([(320, 250), (400, 250), (360, 310)], fill=WHITE)
    draw.rounded_rectangle((220, 120, 500, 152), radius=10, fill=MINT)
    draw.rounded_rectangle((220, 176, 440, 208), radius=10, fill=(232, 239, 236))
    draw.rounded_rectangle((780, 110, 1220, 290), radius=32, fill=WHITE)
    draw.polygon([(980, 290), (1060, 290), (1020, 350)], fill=WHITE)
    draw.rounded_rectangle((820, 154, 1120, 186), radius=10, fill=(255, 230, 222))
    draw.rounded_rectangle((820, 210, 1040, 242), radius=10, fill=(232, 239, 236))
    image.save(ASSET_DIR / "navicare_conversation.png", optimize=True)


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    save_logo()
    save_hero()
    save_scheme()
    save_conversation()
    for path in sorted(ASSET_DIR.glob("navicare_*.png")):
        print(f"{path.name}: {path.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
