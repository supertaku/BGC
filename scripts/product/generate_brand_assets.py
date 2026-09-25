"""Generate simple, project-owned BGC 3D metadata graphics."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "web" / "app"
INK = "#102126"
GOLD = "#e4b76b"
WHITE = "#edf2f1"
MUTED = "#c1cfcb"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    path = Path("C:/Windows/Fonts") / name
    if path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


def draw_grid(draw: ImageDraw.ImageDraw, origin: tuple[int, int], scale: int) -> None:
    x, y = origin
    for dx, dy, w, h in [(0, 0, 4, 7), (5, 1, 3, 4), (9, 0, 5, 9), (2, 8, 5, 3), (8, 10, 6, 3)]:
        draw.rounded_rectangle((x + dx * scale, y + dy * scale, x + (dx + w) * scale, y + (dy + h) * scale), radius=scale, outline=GOLD, width=max(2, scale // 5))


def main() -> None:
    APP.mkdir(parents=True, exist_ok=True)
    icon = Image.new("RGB", (128, 128), INK)
    draw = ImageDraw.Draw(icon)
    draw.rounded_rectangle((13, 13, 115, 115), radius=22, outline=GOLD, width=4)
    draw.text((22, 31), "BGC", fill=WHITE, font=font(31, True))
    draw.text((44, 70), "3D", fill=GOLD, font=font(29, True))
    icon.save(APP / "icon.png", optimize=True)

    image = Image.new("RGB", (1200, 630), INK)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1200, 12), fill=GOLD)
    draw.text((82, 176), "BGC 3D", fill=WHITE, font=font(112, True))
    draw.text((86, 325), "Explore Bonifacio Global City in 3D", fill=MUTED, font=font(38))
    draw.line((86, 440, 670, 440), fill=GOLD, width=3)
    draw_grid(draw, (785, 130), 21)
    image.save(APP / "opengraph-image.png", optimize=True)


if __name__ == "__main__":
    main()
