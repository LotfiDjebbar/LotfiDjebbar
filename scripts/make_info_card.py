"""Hand-authored neofetch-style info card SVG.

A title bar plus colored key/value rows that fade + slide in on a short
stagger, like they're printing next to the ASCII portrait. Prints once
and freezes (no looping).

Set STATIC=1 to emit a frozen frame (all rows already visible) for local
Quick Look previews.

Usage: python scripts/make_info_card.py
"""
import os

USERNAME = "lotfi@LotfiDjebbar"

ROWS = [
    ("Now", "AI Engineer (Alternance) @ CETELEX Technology"),
    ("Prev", "5th-yr eng. student, Data Science & AI, ENP Alger"),
    ("Stack", "Python, PyTorch, LangChain, CrewAI"),
    ("", "Ollama, pgvector, PostgreSQL"),
    ("Highlights", "Darija Transformer from scratch -- 79.4% acc"),
    ("", "Prod RAG agent @ CETELEX -- 100% exec, P50 30ms"),
    ("", "Seeking MSc abroad in AI/NLP, Fall 2027"),
]

WIDTH = 580
PAD_X = 22
PAD_TOP = 44
LINE_H = 26
FONT_SIZE = 13
KEY_COLOR = "#39d353"  # github-green accent for keys, reads fine on light/dark
RULE_COLOR_LIGHT = "#d0d7de"
RULE_COLOR_DARK = "#30363d"
BG_LIGHT = "#f6f8fa"
BG_DARK = "#0d1117"
TEXT_LIGHT = "#24292f"
TEXT_DARK = "#c9d1d9"
TITLE_LIGHT = "#57606a"
TITLE_DARK = "#8b949e"

ROW_STAGGER = 0.12
FADE_DUR = 0.35

STATIC = os.environ.get("STATIC") == "1"


def escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(out_path: str = "info-card.svg") -> None:
    height = PAD_TOP + LINE_H * len(ROWS) + 20

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" '
        f'width="{WIDTH}" height="{height}" font-family="ui-monospace, SFMono-Regular, '
        f'Consolas, \'Liberation Mono\', Menlo, monospace">'
    )
    parts.append(
        "<style>"
        f".bg{{fill:{BG_LIGHT};stroke:{RULE_COLOR_LIGHT};}}"
        f".rule{{stroke:{RULE_COLOR_LIGHT};}}"
        f".title{{fill:{TITLE_LIGHT};}}"
        f".val{{fill:{TEXT_LIGHT};}}"
        f".key{{fill:{KEY_COLOR};font-weight:600;}}"
        f".dot{{fill:{RULE_COLOR_LIGHT};}}"
        "@media (prefers-color-scheme: dark){"
        f".bg{{fill:{BG_DARK};stroke:{RULE_COLOR_DARK};}}"
        f".rule{{stroke:{RULE_COLOR_DARK};}}"
        f".title{{fill:{TITLE_DARK};}}"
        f".val{{fill:{TEXT_DARK};}}"
        f".dot{{fill:{RULE_COLOR_DARK};}}"
        "}"
        "</style>"
    )

    parts.append(
        f'<rect class="bg" x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" '
        f'rx="10" stroke-width="1"/>'
    )

    # mac-style title dots
    for i, color in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{20 + i * 16}" cy="18" r="5" fill="{color}"/>')

    parts.append(
        f'<text class="title" x="{PAD_X}" y="{PAD_TOP - 14}" font-size="12">{escape(USERNAME)}</text>'
    )
    parts.append(
        f'<line class="rule" x1="{PAD_X}" y1="{PAD_TOP - 6}" x2="{WIDTH - PAD_X}" y2="{PAD_TOP - 6}" '
        f'stroke-width="1"/>'
    )

    key_x = PAD_X
    val_x = PAD_X + 118

    for i, (key, val) in enumerate(ROWS):
        y = PAD_TOP + i * LINE_H + LINE_H * 0.65
        begin = i * ROW_STAGGER

        group_attrs = "" if STATIC else f' transform="translate(-8,0)" opacity="0"'
        parts.append(f'<g{group_attrs}>')

        if key:
            parts.append(
                f'<text class="key" x="{key_x}" y="{y:.1f}" font-size="{FONT_SIZE}">'
                f"{escape(key)}:</text>"
            )
        parts.append(
            f'<text class="val" x="{val_x}" y="{y:.1f}" font-size="{FONT_SIZE}">'
            f"{escape(val)}</text>"
        )

        if not STATIC:
            parts.append(
                f'<animate attributeName="opacity" from="0" to="1" begin="{begin:.3f}s" '
                f'dur="{FADE_DUR:.3f}s" fill="freeze"/>'
            )
            parts.append(
                f'<animateTransform attributeName="transform" type="translate" '
                f'from="-8,0" to="0,0" begin="{begin:.3f}s" dur="{FADE_DUR:.3f}s" '
                f'fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1"/>'
            )
        parts.append("</g>")

    parts.append("</svg>")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("".join(parts))
    print(f"wrote {out_path} ({WIDTH}x{height}, {len(ROWS)} rows, static={STATIC})")


if __name__ == "__main__":
    build_svg()
