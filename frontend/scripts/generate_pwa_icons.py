"""Generate the PNG icons referenced by the web app manifest.

Run from the repository root with Pillow installed:

    python frontend/scripts/generate_pwa_icons.py

The generated files are committed so production builds do not need Pillow.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

NAVY = "#0b1f3a"
TEAL = "#0f766e"
TEAL_LIGHT = "#5eead4"
WHITE = "#ffffff"
PALE = "#e2e8f0"

OUTPUT = Path(__file__).resolve().parents[1] / "public" / "icons"


def draw_icon(size: int, *, maskable: bool = False) -> Image.Image:
    image = Image.new("RGB", (size, size), NAVY)
    draw = ImageDraw.Draw(image)

    scale = 0.8 if maskable else 1.0
    offset = (size * (1 - scale)) / 2

    def point(x: float, y: float) -> tuple[float, float]:
        return (offset + x * scale, offset + y * scale)

    # Subtle teal ring keeps the mark recognisable at small sizes.
    ring = [point(52, 52), point(460, 460)]
    draw.ellipse(ring, outline=TEAL, width=max(6, int(16 * scale)))

    # Graduation-cap body, then the top diamond, so the silhouette reads well.
    draw.polygon(
        [point(160, 250), point(352, 250), point(352, 352), point(256, 402), point(160, 352)],
        fill=PALE,
    )
    draw.polygon(
        [point(256, 126), point(436, 216), point(256, 306), point(76, 216)],
        fill=WHITE,
    )
    draw.line(
        [point(436, 216), point(436, 332)],
        fill=TEAL_LIGHT,
        width=max(6, int(12 * scale)),
    )
    draw.ellipse(
        [point(416, 330), point(456, 370)],
        fill=TEAL_LIGHT,
    )
    return image


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for size in (192, 512):
        draw_icon(size).save(OUTPUT / f"icon-{size}.png", optimize=True)
    draw_icon(512, maskable=True).save(OUTPUT / "icon-maskable-512.png", optimize=True)
    draw_icon(180).save(OUTPUT / "apple-touch-icon.png", optimize=True)
    print(f"Wrote PWA icons to {OUTPUT}")


if __name__ == "__main__":
    main()
