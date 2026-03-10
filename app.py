"""
Progress Report → Slide Deck Generator

Reads:  doc/Wooyong Park Progress Report .md
Writes: slides.html  (Reveal.js presentation, opens in browser)
"""

import re
import sys
from datetime import datetime
from pathlib import Path

DOC_DIR = Path(__file__).parent / "doc"
OUTPUT_PATH = Path(__file__).parent / "slides.html"


def find_report() -> Path:
    candidates = sorted(DOC_DIR.glob("*.md"))
    if not candidates:
        print(f"ERROR: No .md file found in {DOC_DIR}", file=sys.stderr)
        sys.exit(1)
    if len(candidates) > 1:
        print(f"Multiple .md files found in doc/ — using: {candidates[0].name}", file=sys.stderr)
    return candidates[0]


# ---------------------------------------------------------------------------
# Section extraction
# ---------------------------------------------------------------------------

def read_report() -> str:
    return find_report().read_text(encoding="utf-8")


def extract_section(text: str, heading: str, next_heading: str | None = None) -> str:
    start_marker = f"\n# {heading}"
    start = text.find(start_marker)
    if start == -1:
        return ""
    start += 1
    if next_heading:
        end_marker = f"\n# {next_heading}"
        end = text.find(end_marker, start)
        return text[start:end].strip() if end != -1 else text[start:].strip()
    return text[start:].strip()


# ---------------------------------------------------------------------------
# Milestone parsing
# ---------------------------------------------------------------------------

def parse_due_date(text: str) -> datetime | None:
    """Last date from the last [...] bracket containing dates."""
    for block in reversed(re.findall(r'\[([^\]]+)\]', text)):
        dates = re.findall(r'\d{2}/\d{2}/\d{2}', block)
        if dates:
            try:
                return datetime.strptime(dates[-1], "%m/%d/%y")
            except ValueError:
                continue
    return None


def clean_description(raw: str) -> str:
    s = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', raw)   # [text](url) → text
    s = re.sub(r'\\\[[^\]]*\\\]', '', s)                # \[dates\]
    s = re.sub(r'\[[^\]]*\]', '', s)                    # [dates] / [#issue]
    s = re.sub(r'\\+$', '', s).strip()
    s = re.sub(r'\s+', ' ', s)
    return s


def is_completed(status: str) -> bool:
    low = status.lower().strip()
    return any(low.startswith(k) for k in ("completed", "done", "audit completed"))


def parse_milestones(goals_section: str) -> list[dict]:
    milestones = []
    current_goal = "General"
    lines = goals_section.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        # Goal heading
        g = re.search(r'\*{0,2}Goal:\s*(.+?)(?:\s*\\\[|\s*\*{0,2}$)', line)
        if g:
            current_goal = g.group(1).strip().rstrip("\\").strip()
            i += 1
            continue
        # Milestone line
        m = re.match(r'\s*[\*\-]\s+Milestone:\s*(.+)', line)
        if m:
            raw = m.group(1).strip()
            due = parse_due_date(raw)
            desc = clean_description(raw)
            status = ""
            if i + 1 < len(lines):
                nxt = lines[i + 1].strip()
                sm = re.match(r'[\*\-]?\s*[Ss]tatus:\s*(.+)', nxt)
                if sm:
                    status = sm.group(1).strip()
                    i += 1
            if not is_completed(status):
                milestones.append({
                    "goal": current_goal,
                    "description": desc,
                    "due_date": due,
                    "status": status,
                })
        i += 1
    return milestones


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
# Review parsing (for 20-hour recommendation)
# ---------------------------------------------------------------------------

SKIP_TASKS = {
    "1:1 aleksei", "fb team meeting", "szymon meeting", "meeting with susan",
    "lab weekly meeting", "weekly lab meeting", "rf workshop", "meeting followup",
    "econometrics ii", "econometrics midterm prep", "progress report update",
    "update goals and milestones", "meeting prep(write agenda)",
}


def parse_recent_reviews(reviews_section: str, n: int = 3) -> list[dict]:
    blocks = re.split(r'(?=###\s+(?:Review|Preview)\s+)', reviews_section)
    reviews = []
    for block in blocks:
        h = re.match(r'###\s+(Review|Preview)\s+(\S.*?)$', block, re.MULTILINE)
        if not h:
            continue
        total_m = re.search(r'Total:\s*([\d.]+)', block)
        tasks = []
        for tm in re.finditer(r'^\*\s+(.+?):\s*([\d.]+)h(?:\s*→\s*([\d.]+)h)?', block, re.MULTILINE):
            task = tm.group(1).strip()
            if task.lower() in SKIP_TASKS:
                continue
            planned = float(tm.group(2))
            actual = float(tm.group(3)) if tm.group(3) else planned
            tasks.append((task, planned, actual))
        reviews.append({
            "kind": h.group(1),
            "period": h.group(2).strip(),
            "total_hours": float(total_m.group(1)) if total_m else 0.0,
            "tasks": tasks,
        })
    return [r for r in reviews if r["kind"] == "Review"][:n]


def build_recommendation(milestones: list[dict], reviews: list[dict], today: datetime) -> list[dict]:
    """Return a list of {task, hours, reason} dicts for the recommended plan."""
    recs = []

    # In-progress / currently active
    in_prog = [m for m in milestones if m["status"] and
               any(k in m["status"].lower() for k in ("writing", "planning", "currently", "in progress"))]
    for m in in_prog[:3]:
        days = (m["due_date"] - today).days if m["due_date"] else None
        tag = f"due in {days}d" if days is not None and days >= 0 else ("OVERDUE" if days is not None else "no date")
        recs.append({"task": m["description"][:80], "hours": 2.0,
                     "reason": f"Currently in progress — {tag}"})

    # Overdue
    overdue = [m for m in milestones if m["due_date"] and (m["due_date"] - today).days < 0
               and not any(r["task"] == m["description"][:80] for r in recs)]
    for m in sorted(overdue, key=lambda x: x["due_date"])[:3]:
        recs.append({"task": m["description"][:80], "hours": 1.5,
                     "reason": f"Overdue ({m['due_date'].strftime('%m/%d/%y')})"})

    # Due within 14 days (not already listed)
    seen = {r["task"] for r in recs}
    urgent = [m for m in milestones if m["due_date"] and 0 <= (m["due_date"] - today).days <= 14
              and m["description"][:80] not in seen]
    for m in sorted(urgent, key=lambda x: x["due_date"])[:3]:
        days = (m["due_date"] - today).days
        recs.append({"task": m["description"][:80], "hours": 1.5,
                     "reason": f"Due in {days}d ({m['due_date'].strftime('%m/%d/%y')})"})

    # Recurring pushed-back tasks from reviews
    counts: dict[str, int] = {}
    for rev in reviews:
        for task, _, _ in rev["tasks"]:
            counts[task.lower()] = counts.get(task.lower(), 0) + 1
    recurring = sorted([(t, c) for t, c in counts.items() if c >= 2], key=lambda x: -x[1])
    seen2 = {r["task"].lower() for r in recs}
    for task, cnt in recurring[:2]:
        if task not in seen2:
            recs.append({"task": task.title()[:80], "hours": 1.0,
                         "reason": f"Pushed back in {cnt} of last {len(reviews)} reviews — time-box it"})

    return recs


# ---------------------------------------------------------------------------
# HTML / Reveal.js generation
# ---------------------------------------------------------------------------

def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def milestone_row(m: dict, today: datetime) -> str:
    due = m["due_date"].strftime("%m/%d/%y") if m["due_date"] else "—"
    days = (m["due_date"] - today).days if m["due_date"] else None

    if days is None:
        badge = '<span class="badge gray">no date</span>'
    elif days < 0:
        badge = f'<span class="badge red">OVERDUE {abs(days)}d</span>'
    elif days == 0:
        badge = '<span class="badge red">TODAY</span>'
    elif days <= 7:
        badge = f'<span class="badge orange">in {days}d</span>'
    else:
        badge = f'<span class="badge green">in {days}d</span>'

    status_html = f'<div class="status">{esc(m["status"][:120])}</div>' if m["status"] else ""
    goal_short = esc(m["goal"][:55]) + ("…" if len(m["goal"]) > 55 else "")

    return f"""
      <tr>
        <td class="due">{esc(due)}</td>
        <td class="badge-cell">{badge}</td>
        <td>
          <div class="goal-tag">{goal_short}</div>
          <div class="ms-desc">{esc(m["description"][:100])}</div>
          {status_html}
        </td>
      </tr>"""


def build_milestone_slides(milestones: list[dict], today: datetime) -> str:
    buckets = {
        "overdue":     ("🔴 Overdue",           []),
        "this_week":   ("🟠 Due This Week",      []),
        "next_2_weeks":("🟡 Due in Next 2 Weeks",[]),
        "this_month":  ("🟢 Due This Month",     []),
        "later":       ("📅 Later",              []),
        "undated":     ("⬜ No Due Date",        []),
    }
    for m in milestones:
        buckets[bucket(m, today)][1].append(m)

    slides = ""
    for key, (label, items) in buckets.items():
        if not items:
            continue
        rows = "".join(milestone_row(m, today) for m in items)
        slides += f"""
    <section>
      <h2>{label}</h2>
      <table class="ms-table">
        <thead><tr><th>Due</th><th></th><th>Milestone</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </section>"""
    return slides


def build_rec_slide(recs: list[dict], reviews: list[dict], today: datetime) -> str:
    avg_total = round(sum(r["total_hours"] for r in reviews) / len(reviews)) if reviews else 20
    fb_budget = round(avg_total * 0.75)
    other_budget = avg_total - fb_budget

    rows = ""
    total_h = 0.0
    for r in recs:
        total_h += r["hours"]
        rows += f"""
        <tr>
          <td class="h-cell">{r['hours']:.0f}h</td>
          <td><div class="ms-desc">{esc(r['task'])}</div>
              <div class="reason">{esc(r['reason'])}</div></td>
        </tr>"""

    other_rows = f"""
        <tr><td class="h-cell">2h</td><td><div class="ms-desc">ECON271 / coursework</div></td></tr>
        <tr><td class="h-cell">1h</td><td><div class="ms-desc">Lab meeting / workshops</div></td></tr>
        <tr><td class="h-cell">0.5h</td><td><div class="ms-desc">Progress report update</div></td></tr>"""

    return f"""
    <section>
      <h2>📋 Recommended Next {avg_total}-Hour Plan</h2>
      <p style="font-size:0.55em;margin-bottom:0.6em;opacity:0.7">
        Based on your recent average of {avg_total}h/period &nbsp;|&nbsp;
        FB Misinfo ~{fb_budget}h &nbsp;·&nbsp; Other ~{other_budget}h
      </p>
      <table class="ms-table">
        <thead><tr><th style="width:3em"></th><th>FB Misinfo tasks</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <table class="ms-table" style="margin-top:0.8em">
        <thead><tr><th style="width:3em"></th><th>Other</th></tr></thead>
        <tbody>{other_rows}</tbody>
      </table>
    </section>"""


def render_html(milestone_slides: str, rec_slide: str, today: datetime) -> str:
    date_str = today.strftime("%B %d, %Y")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Progress Report — {date_str}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reset.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/theme/simple.css">
<style>
  :root {{ --r-heading-font: 'Segoe UI', system-ui, sans-serif;
           --r-main-font: 'Segoe UI', system-ui, sans-serif; }}
  .reveal h1 {{ font-size:1.6em; }}
  .reveal h2 {{ font-size:1.1em; margin-bottom:0.5em; color:#1a1a2e; }}
  .reveal section {{ text-align:left; }}
  .ms-table {{ width:100%; border-collapse:collapse; font-size:0.5em; }}
  .ms-table th {{ background:#1a1a2e; color:#fff; padding:4px 8px; font-size:1em; }}
  .ms-table td {{ padding:4px 8px; border-bottom:1px solid #eee; vertical-align:top; }}
  .ms-table tr:hover td {{ background:#f5f5f5; }}
  .due {{ white-space:nowrap; color:#555; font-size:0.95em; }}
  .badge-cell {{ white-space:nowrap; }}
  .badge {{ padding:2px 6px; border-radius:4px; font-size:0.9em; font-weight:600; }}
  .badge.red {{ background:#fee2e2; color:#b91c1c; }}
  .badge.orange {{ background:#ffedd5; color:#c2410c; }}
  .badge.green {{ background:#d1fae5; color:#065f46; }}
  .badge.gray {{ background:#f3f4f6; color:#6b7280; }}
  .goal-tag {{ font-size:0.85em; color:#6366f1; font-weight:600; }}
  .ms-desc {{ font-weight:500; }}
  .status {{ font-size:0.9em; color:#6b7280; font-style:italic; margin-top:2px; }}
  .reason {{ font-size:0.9em; color:#6b7280; font-style:italic; margin-top:2px; }}
  .h-cell {{ font-weight:700; color:#1a1a2e; white-space:nowrap; font-size:1.1em; }}
</style>
</head>
<body>
<div class="reveal">
  <div class="slides">

    <section>
      <h1>📊 Progress Report</h1>
      <h3 style="color:#6366f1">Wooyong Park</h3>
      <p style="color:#888">{date_str}</p>
      <p style="font-size:0.5em;margin-top:2em;color:#aaa">
        Use arrow keys or click the arrows to navigate
      </p>
    </section>

    <section>
      <h2>📌 Upcoming Milestones</h2>
      <p style="font-size:0.55em;color:#888">Use → to step through by urgency group</p>
    </section>

    {milestone_slides}

    {rec_slide}

  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
<script>
  Reveal.initialize({{
    hash: true,
    controls: true,
    progress: true,
    center: false,
    transition: 'slide',
    width: 1100,
    height: 700,
  }});
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    report = read_report()
    goals_section = extract_section(report, "Goals/Milestones", "Career")
    reviews_section = extract_section(report, "Previews/Reviews")

    if not goals_section:
        print("ERROR: Could not find '# Goals/Milestones' section.", file=sys.stderr)
        sys.exit(1)

    today = datetime.today()
    milestones = parse_milestones(goals_section)
    reviews = parse_recent_reviews(reviews_section, n=3)
    recs = build_recommendation(milestones, reviews, today)

    milestone_slides = build_milestone_slides(milestones, today)
    rec_slide = build_rec_slide(recs, reviews, today)
    html = render_html(milestone_slides, rec_slide, today)

    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"Slides written to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
