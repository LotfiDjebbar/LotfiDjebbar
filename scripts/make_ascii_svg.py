"""Convert source-prepped.png into a self-typing monochrome ASCII SVG.

Each row wipes in left-to-right via a CSS clip-path keyframe animation,
staggered top to bottom with per-row animation-delay. Prints once and
freezes (no looping). CSS keyframes (rather than SMIL) keep the element
count low and render reliably via GitHub's <img>-embedded SVG pipeline.

Usage: python scripts/make_ascii_svg.py
"""
from PIL import Image

RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense); leading space clears bg to nothing
COLS = 100
FONT_ASPECT = 0.55  # monospace cell width / height, used to derive row count
FONT_SIZE = 8
CELL_W = FONT_SIZE * 0.6
CELL_H = FONT_SIZE * 1.0
ROW_STAGGER = 0.045  # seconds between each row's wipe starting
WIPE_DUR = 0.28  # seconds for one row's left-to-right wipe

FILL_LIGHT = "#24292f"
FILL_DARK = "#c9d1d9"


def image_to_grid(path: str, cols: int = COLS) -> list[str]:
    img = Image.open(path).convert("L")
    rows = max(1, round(cols * (img.height / img.width) * FONT_ASPECT))
    img = img.resize((cols, rows), Image.LANCZOS)

    ramp_len = len(RAMP)
    lines = []
    for y in range(rows):
        chars = []
        for x in range(cols):
            brightness = img.getpixel((x, y))  # 0 dark .. 255 bright
            idx = int((255 - brightness) / 255 * (ramp_len - 1))
            chars.append(RAMP[idx])
        lines.append("".join(chars))
    return lines


def escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(lines: list[str], out_path: str = "avi-ascii.svg") -> None:
    cols = max(len(line) for line in lines)
    width = cols * CELL_W
    height = len(lines) * CELL_H
    total_duration = len(lines) * ROW_STAGGER + WIPE_DUR

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.1f} {height:.1f}" '
        f'width="{width:.1f}" height="{height:.1f}" font-family="ui-monospace, SFMono-Regular, '
        f'Consolas, \'Liberation Mono\', Menlo, monospace">'
    )
    parts.append(
        "<style>"
        f".ink{{fill:{FILL_LIGHT};}}"
        f"@media (prefers-color-scheme: dark){{.ink{{fill:{FILL_DARK};}}}}"
        f".row{{clip-path:inset(0 {width:.1f}px 0 0);"
        f"animation:wipe {WIPE_DUR:.3f}s cubic-bezier(.25,.1,.25,1) forwards;}}"
        f"@keyframes wipe{{to{{clip-path:inset(0 0px 0 0);}}}}"
        "</style>"
    )

    for i, line in enumerate(lines):
        y = i * CELL_H
        begin = i * ROW_STAGGER
        text_y = y + CELL_H * 0.85
        parts.append(f'<g class="row ink" style="animation-delay:{begin:.3f}s">')
        parts.append(
            f'<text x="0" y="{text_y:.1f}" font-size="{FONT_SIZE}" xml:space="preserve">'
            f"{escape(line)}</text>"
        )
        parts.append("</g>")

    parts.append("</svg>")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("".join(parts))
    print(f"wrote {out_path} ({cols}x{len(lines)} chars, ~{total_duration:.1f}s animation)")


if __name__ == "__main__":
    grid = image_to_grid("source-prepped.png")
    build_svg(grid)
