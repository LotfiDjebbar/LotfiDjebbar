"""Scrape the public GitHub contribution calendar -- no token, no GraphQL API.

GitHub serves the calendar as public HTML at
https://github.com/users/<username>/contributions (the same fragment the
profile page itself uses). Parses day cells + their tooltip text and writes
data/contributions.json with raw days plus derived stats.

Usage: python scripts/fetch_contributions.py [username]
"""
import json
import re
import sys
from collections import defaultdict
from datetime import date

import requests
from bs4 import BeautifulSoup

USERNAME = "LotfiDjebbar"
URL = "https://github.com/users/{username}/contributions"


def fetch_html(username: str) -> str:
    resp = requests.get(
        URL.format(username=username),
        headers={"User-Agent": "Mozilla/5.0 (profile-readme-bot)"},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.text


def parse(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    tooltip_by_id: dict[str, str] = {}
    for tip in soup.select("tool-tip"):
        target = tip.get("for")
        if target:
            tooltip_by_id[target] = tip.get_text(strip=True)

    days = []
    for cell in soup.select("td.ContributionCalendar-day[data-date]"):
        d = cell["data-date"]
        level = int(cell.get("data-level", 0))
        cell_id = cell.get("id", "")
        tooltip = tooltip_by_id.get(cell_id, "")
        m = re.match(r"(\d+)\s+contributions?", tooltip)
        count = int(m.group(1)) if m else 0
        days.append({"date": d, "level": level, "count": count})

    days.sort(key=lambda d: d["date"])

    header = soup.select_one("#js-contribution-activity-description")
    total_text = header.get_text(strip=True) if header else ""
    m = re.match(r"([\d,]+)", total_text)
    total_from_header = int(m.group(1).replace(",", "")) if m else sum(d["count"] for d in days)

    return {"days": days, "total_from_header": total_from_header}


def compute_stats(days: list[dict], total_from_header: int) -> dict:
    total = sum(d["count"] for d in days)

    longest = current = 0
    for d in days:
        if d["count"] > 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0

    # current streak counted back from the most recent day with data
    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    best_day = max(days, key=lambda d: d["count"], default=None)

    monthly = defaultdict(int)
    for d in days:
        month = d["date"][:7]  # YYYY-MM
        monthly[month] += d["count"]

    return {
        "total_contributions": total_from_header or total,
        "longest_streak": longest,
        "current_streak": current_streak,
        "best_day": best_day,
        "monthly_totals": dict(sorted(monthly.items())),
    }


def main() -> None:
    username = sys.argv[1] if len(sys.argv) > 1 else USERNAME
    html = fetch_html(username)
    parsed = parse(html)
    stats = compute_stats(parsed["days"], parsed["total_from_header"])

    out = {
        "username": username,
        "generated": date.today().isoformat(),
        "days": parsed["days"],
        "stats": stats,
    }

    with open("data/contributions.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"wrote data/contributions.json ({len(parsed['days'])} days, {stats['total_contributions']} contributions)")


if __name__ == "__main__":
    main()
