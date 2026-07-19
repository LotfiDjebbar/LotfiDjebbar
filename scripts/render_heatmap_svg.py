"""Render data/contributions.json as the classic 53-week x 7-day calendar
of rounded, colored boxes, using GitHub's own green ramp.

Reveals once with a diagonal, line-after-line slide-down (CSS keyframes
that play on load, then freeze -- no looping), plus a Less->More legend
and a stats footer. Output: contrib-heatmap.svg.

Usage: python scripts/render_heatmap_svg.py
"""
import json
from datetime import date, datetime

PALETTE_LIGHT = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]
PALETTE_DARK = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

CELL = 11
GAP = 3
STEP = CELL + GAP
LEFT_PAD = 28  # room for day-of-week labels
TOP_PAD = 20  # room for month labels
LEGEND_H = 22
FOOTER_H = 22

STAGGER = 0.012  # seconds between each diagonal step
CELL_DUR = 0.35

TEXT_LIGHT = "#57606a"
TEXT_DARK = "#8b949e"

MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DOW_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}  # Monday=0 .. Sunday=6, sparse labels like GitHub


def load_data(path: str = "data/contributions.json") -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_weeks(days: list[dict]) -> list[list[dict | None]]:
    parsed = [dict(d, dt=datetime.strptime(d["date"], "%Y-%m-%d").date()) for d in days]
    parsed.sort(key=lambda d: d["dt"])

    first = parsed[0]["dt"]
    # pad the front so the grid starts on a Sunday, like GitHub's calendar
    lead_gap = (first.weekday() + 1) % 7  # weekday(): Mon=0..Sun=6 -> convert to Sun=0..Sat=6
    padded: list[dict | None] = [None] * lead_gap + parsed

    weeks: list[list[dict | None]] = []
    for i in range(0, len(padded), 7):
        week = padded[i : i + 7]
        week += [None] * (7 - len(week))
        weeks.append(week)
    return weeks


def escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(data: dict, out_path: str = "contrib-heatmap.svg") -> None:
    weeks = build_weeks(data["days"])
    n_weeks = len(weeks)

    width = LEFT_PAD + n_weeks * STEP + 10
    grid_h = 7 * STEP
    height = TOP_PAD + grid_h + LEGEND_H + FOOTER_H

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" font-family="ui-monospace, SFMono-Regular, '
        f'Consolas, \'Liberation Mono\', Menlo, monospace">'
    )

    style_parts = [".cell{animation:reveal " + f"{CELL_DUR:.2f}s cubic-bezier(.25,.1,.25,1) forwards;" + "opacity:0;transform-origin:center;}"]
    style_parts.append("@keyframes reveal{0%{opacity:0;transform:translate(-6px,-6px) scale(.4);}100%{opacity:1;transform:translate(0,0) scale(1);}}")
    for lvl in range(5):
        style_parts.append(f".lvl{lvl}{{fill:{PALETTE_LIGHT[lvl]};}}")
    style_parts.append(f".lbl{{fill:{TEXT_LIGHT};}}")
    style_parts.append(
        "@media (prefers-color-scheme: dark){"
        + "".join(f".lvl{lvl}{{fill:{PALETTE_DARK[lvl]};}}" for lvl in range(5))
        + f".lbl{{fill:{TEXT_DARK};}}"
        + "}"
    )
    parts.append("<style>" + "".join(style_parts) + "</style>")

    # month labels: place a label above the first week column that starts a new month
    seen_months: set[tuple[int, int]] = set()
    for wi, week in enumerate(weeks):
        for day in week:
            if day is None:
                continue
            dt: date = day["dt"]
            key = (dt.year, dt.month)
            if dt.day <= 7 and key not in seen_months:
                seen_months.add(key)
                x = LEFT_PAD + wi * STEP
                parts.append(f'<text class="lbl" x="{x}" y="{TOP_PAD - 7}" font-size="10">{MONTH_ABBR[dt.month - 1]}</text>')
            break

    # day-of-week labels (Sun=row0 .. Sat=row6)
    for row, label in DOW_LABELS.items():
        y = TOP_PAD + row * STEP + CELL * 0.85
        parts.append(f'<text class="lbl" x="0" y="{y:.1f}" font-size="9">{label}</text>')

    # grid cells, diagonal stagger: delay grows with (week + day-row)
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            if day is None:
                continue
            x = LEFT_PAD + wi * STEP
            y = TOP_PAD + di * STEP
            level = day["level"]
            delay = (wi + di) * STAGGER
            title = f"{day['count']} contribution{'s' if day['count'] != 1 else ''} on {day['date']}"
            parts.append(
                f'<rect class="cell lvl{level}" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'rx="2" style="animation-delay:{delay:.3f}s"><title>{escape(title)}</title></rect>'
            )

    # legend: Less -> More
    legend_y = TOP_PAD + grid_h + 14
    legend_x = LEFT_PAD + max(0, n_weeks * STEP - 150)
    parts.append(f'<text class="lbl" x="{legend_x}" y="{legend_y}" font-size="10">Less</text>')
    for i in range(5):
        lx = legend_x + 32 + i * (CELL + 3)
        parts.append(f'<rect class="lvl{i}" x="{lx}" y="{legend_y - 9}" width="{CELL}" height="{CELL}" rx="2"/>')
    parts.append(f'<text class="lbl" x="{legend_x + 32 + 5 * (CELL + 3) + 4}" y="{legend_y}" font-size="10">More</text>')

    # stats footer
    stats = data["stats"]
    footer = (
        f"{stats['total_contributions']} contributions in the last year -- "
        f"longest streak {stats['longest_streak']}d -- current streak {stats['current_streak']}d"
    )
    footer_y = TOP_PAD + grid_h + LEGEND_H + 16
    parts.append(f'<text class="lbl" x="{LEFT_PAD}" y="{footer_y}" font-size="11">{escape(footer)}</text>')

    parts.append("</svg>")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("".join(parts))
    print(f"wrote {out_path} ({width}x{height}, {n_weeks} weeks)")


if __name__ == "__main__":
    build_svg(load_data())
