"""
Progress Report → Gantt Chart Generator

Reads:  doc/<report>.md
Writes: gantt.html  (SVG-based Gantt chart, opens in browser)

Each milestone bar spans from (deadline − 3 days) to deadline.
"""

import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Reuse parsing helpers from app.py
sys.path.insert(0, str(Path(__file__).parent))
from app import find_report, extract_section, parse_milestones

OUTPUT_PATH = Path(__file__).parent / "gantt.html"

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------

ROW_H       = 32        # px per milestone row
ROW_PAD     = 4         # px padding inside row
LABEL_W     = 380       # px for the left label column
CHART_W     = 900       # px for the chart area
HEADER_H    = 60        # px for date axis header
FOOTER_H    = 20
FONT        = "system-ui, 'Segoe UI', sans-serif"

COLORS = {
    "overdue":      ("#fca5a5", "#b91c1c"),   # bg, text/border
    "this_week":    ("#fed7aa", "#c2410c"),
    "next_2_weeks": ("#fef08a", "#854d0e"),
    "this_month":   ("#bbf7d0", "#065f46"),
    "later":        ("#bfdbfe", "#1e40af"),
}


def bucket(ms: dict, today: datetime) -> str:
    if not ms["due_date"]:
        return "undated"
    days = (ms["due_date"] - today).days
    if days < 0:
        return "overdue"
    if days <= 7:
        return "this_week"
    if days <= 14:
        return "next_2_weeks"
    if days <= 30:
        return "this_month"
    return "later"


# ---------------------------------------------------------------------------
# SVG helpers
# ---------------------------------------------------------------------------

def esc(s: str) -> str:
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;"))


def date_range(milestones: list[dict], today: datetime):
    dates = [m["due_date"] for m in milestones if m["due_date"]]
    if not dates:
        return today - timedelta(days=7), today + timedelta(days=30)
    earliest = min(dates) - timedelta(days=5)
    latest   = max(dates) + timedelta(days=5)
    # always include today
    earliest = min(earliest, today - timedelta(days=3))
    latest   = max(latest, today + timedelta(days=3))
    return earliest, latest


def x_pos(d: datetime, start: datetime, span_days: int) -> float:
    return LABEL_W + (d - start).days / span_days * CHART_W


def build_svg(milestones: list[dict], today: datetime) -> str:
    dated = [m for m in milestones if m["due_date"]]
    dated.sort(key=lambda m: m["due_date"])

    if not dated:
        return "<p>No milestones with due dates found.</p>"

    start_date, end_date = date_range(dated, today)
    span_days = max((end_date - start_date).days, 1)

    total_w = LABEL_W + CHART_W
    total_h = HEADER_H + len(dated) * ROW_H + FOOTER_H

    lines = []
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{total_w}" height="{total_h}" '
        f'font-family="{FONT}" font-size="12">'
    )

    # ── Background ──────────────────────────────────────────────────────────
    lines.append(f'<rect width="{total_w}" height="{total_h}" fill="#fafafa"/>')

    # ── Month/week grid lines ────────────────────────────────────────────────
    d = start_date.replace(day=1) + timedelta(days=32)
    d = d.replace(day=1)
    while d < end_date:
        x = x_pos(d, start_date, span_days)
        lines.append(
            f'<line x1="{x:.1f}" y1="{HEADER_H}" '
            f'x2="{x:.1f}" y2="{total_h - FOOTER_H}" '
            f'stroke="#e5e7eb" stroke-width="1"/>'
        )
        lines.append(
            f'<text x="{x:.1f}" y="14" text-anchor="middle" '
            f'fill="#9ca3af" font-size="10">{d.strftime("%b %Y")}</text>'
        )
        # next month
        d = (d.replace(day=1) + timedelta(days=32)).replace(day=1)

    # week ticks
    d = start_date
    while d <= end_date:
        if d.weekday() == 0:  # Monday
            x = x_pos(d, start_date, span_days)
            lines.append(
                f'<line x1="{x:.1f}" y1="{HEADER_H - 10}" '
                f'x2="{x:.1f}" y2="{total_h - FOOTER_H}" '
                f'stroke="#f3f4f6" stroke-width="1"/>'
            )
        d += timedelta(days=1)

    # ── Header date axis ────────────────────────────────────────────────────
    lines.append(
        f'<rect x="0" y="0" width="{total_w}" height="{HEADER_H}" fill="#1a1a2e"/>'
    )
    lines.append(
        f'<text x="{LABEL_W // 2}" y="38" text-anchor="middle" '
        f'fill="white" font-weight="600" font-size="13">Milestone</text>'
    )

    # date labels every 2 days
    d = start_date
    while d <= end_date:
        x = x_pos(d, start_date, span_days)
        if x >= LABEL_W:
            lines.append(
                f'<text x="{x:.1f}" y="38" text-anchor="middle" '
                f'fill="#cbd5e1" font-size="10">{d.strftime("%m/%d")}</text>'
            )
        d += timedelta(days=2)

    # ── Row backgrounds (zebra) ──────────────────────────────────────────────
    for i in range(len(dated)):
        y = HEADER_H + i * ROW_H
        fill = "#ffffff" if i % 2 == 0 else "#f9fafb"
        lines.append(
            f'<rect x="0" y="{y}" width="{total_w}" height="{ROW_H}" fill="{fill}"/>'
        )

    # ── Milestone bars ────────────────────────────────────────────────────────
    for i, m in enumerate(dated):
        b = bucket(m, today)
        bg, border = COLORS.get(b, ("#e5e7eb", "#6b7280"))
        y = HEADER_H + i * ROW_H

        bar_end   = m["due_date"]
        bar_start = bar_end - timedelta(days=3)

        x1 = max(x_pos(bar_start, start_date, span_days), LABEL_W)
        x2 = max(x_pos(bar_end,   start_date, span_days), LABEL_W)
        bar_w = max(x2 - x1, 4)

        bar_y = y + ROW_PAD
        bar_h = ROW_H - ROW_PAD * 2

        # label on left
        label = m["description"]
        max_chars = 55
        if len(label) > max_chars:
            label = label[:max_chars - 1] + "…"
        lines.append(
            f'<text x="{LABEL_W - 8}" y="{y + ROW_H // 2 + 4}" '
            f'text-anchor="end" fill="#374151" font-size="11">{esc(label)}</text>'
        )

        # goal tag
        goal_short = m["goal"][:25] + ("…" if len(m["goal"]) > 25 else "")
        lines.append(
            f'<text x="6" y="{y + ROW_H // 2 - 3}" '
            f'fill="#6366f1" font-size="9" font-weight="600">{esc(goal_short)}</text>'
        )

        # bar
        lines.append(
            f'<rect x="{x1:.1f}" y="{bar_y}" width="{bar_w:.1f}" height="{bar_h}" '
            f'rx="4" fill="{bg}" stroke="{border}" stroke-width="1.5"/>'
        )

        # due date label inside / beside bar
        due_label = m["due_date"].strftime("%m/%d")
        label_x = x2 + 4
        lines.append(
            f'<text x="{label_x:.1f}" y="{y + ROW_H // 2 + 4}" '
            f'fill="{border}" font-size="10" font-weight="600">{due_label}</text>'
        )

        # row separator
        lines.append(
            f'<line x1="0" y1="{y + ROW_H}" x2="{total_w}" y2="{y + ROW_H}" '
            f'stroke="#e5e7eb" stroke-width="0.5"/>'
        )

    # ── Today line ────────────────────────────────────────────────────────────
    tx = x_pos(today, start_date, span_days)
    if LABEL_W <= tx <= LABEL_W + CHART_W:
        lines.append(
            f'<line x1="{tx:.1f}" y1="{HEADER_H}" '
            f'x2="{tx:.1f}" y2="{total_h - FOOTER_H}" '
            f'stroke="#ef4444" stroke-width="2" stroke-dasharray="6,3"/>'
        )
        lines.append(
            f'<text x="{tx + 4:.1f}" y="{HEADER_H + 14}" '
            f'fill="#ef4444" font-size="10" font-weight="700">Today</text>'
        )

    # ── Left column border ────────────────────────────────────────────────────
    lines.append(
        f'<line x1="{LABEL_W}" y1="0" x2="{LABEL_W}" y2="{total_h}" '
        f'stroke="#d1d5db" stroke-width="1.5"/>'
    )

    lines.append("</svg>")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# HTML wrapper
# ---------------------------------------------------------------------------

def render_html(svg: str, today: datetime) -> str:
    date_str = today.strftime("%B %d, %Y")
    legend_items = [
        ("overdue",      "#fca5a5", "#b91c1c", "Overdue"),
        ("this_week",    "#fed7aa", "#c2410c", "Due this week"),
        ("next_2_weeks", "#fef08a", "#854d0e", "Due in next 2 weeks"),
        ("this_month",   "#bbf7d0", "#065f46", "Due this month"),
        ("later",        "#bfdbfe", "#1e40af", "Later"),
    ]
    legend_html = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:4px;margin-right:16px">'
        f'<span style="display:inline-block;width:14px;height:14px;border-radius:3px;'
        f'background:{bg};border:1.5px solid {border}"></span>'
        f'<span style="font-size:13px;color:#374151">{label}</span></span>'
        for _, bg, border, label in legend_items
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Milestone Gantt — {date_str}</title>
<style>
  body {{ margin: 0; padding: 24px; background: #f3f4f6;
          font-family: system-ui, 'Segoe UI', sans-serif; }}
  h1   {{ font-size: 1.4rem; color: #1a1a2e; margin-bottom: 4px; }}
  .sub {{ font-size: 0.85rem; color: #6b7280; margin-bottom: 16px; }}
  .legend {{ margin-bottom: 16px; display: flex; flex-wrap: wrap; gap: 4px; }}
  .card {{ background: white; border-radius: 12px; padding: 16px;
           box-shadow: 0 1px 4px rgba(0,0,0,.08); overflow-x: auto; }}
  .note {{ font-size: 11px; color: #9ca3af; margin-top: 10px; }}
</style>
</head>
<body>
  <h1>📅 Milestone Gantt Chart</h1>
  <p class="sub">Wooyong Park &nbsp;·&nbsp; Generated {date_str} &nbsp;·&nbsp;
     Each bar spans 3 days ending on the deadline</p>
  <div class="legend">{legend_html}</div>
  <div class="card">
    {svg}
    <p class="note">
      Milestones without a due date are not shown. &nbsp;
      Completed milestones are excluded.
    </p>
  </div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    report = find_report().read_text(encoding="utf-8")
    goals_section = extract_section(report, "Goals/Milestones", "Career")

    if not goals_section:
        print("ERROR: Could not find '# Goals/Milestones' section.", file=sys.stderr)
        sys.exit(1)

    today = datetime.today()
    milestones = parse_milestones(goals_section)

    svg = build_svg(milestones, today)
    html = render_html(svg, today)

    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"Gantt chart written to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
