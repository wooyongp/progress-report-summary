# Progress Report Slide Generator

Converts a Markdown progress report into a browser-based slide deck (Reveal.js) showing upcoming milestones by urgency and a recommended work plan for the next period.

## How it works

1. Reads a `.md` file from the `doc/` folder
2. Parses `# Goals/Milestones` for incomplete milestones and their due dates
3. Parses `# Previews/Reviews` for recent time-tracking data
4. Generates `slides.html` — a Reveal.js presentation that opens in your browser

### Slides produced

| Slide | Content |
|---|---|
| Overdue / This Week / Next 2 Weeks / This Month / Later | Milestone tables grouped by urgency, colour-coded by days remaining |
| Recommended Plan | Suggested hours per task, derived from in-progress items, overdue deadlines, and recurring pushed-back tasks |

## Requirements

- **macOS** (the `.command` launcher is macOS-only; `app.py` runs anywhere with Python)
- **Python 3.10** — no third-party packages needed (stdlib only)
- Internet connection for the first browser open (Reveal.js loads from CDN; cached after that)

## Quickstart

```
# 1. Put your progress report in doc/
cp "My Progress Report.md" doc/

# 2. Double-click generate-slides.command in Finder
#    — or run from Terminal:
.venv/bin/python3.10 app.py

# 3. slides.html opens in your browser automatically
```

> If macOS blocks `generate-slides.command` on first run: right-click → Open → Open.

## Progress report format

The `.md` file must contain two top-level sections:

### `# Goals/Milestones`

```markdown
**Goal: <goal title> [due date]**

* Milestone: <description> [MM/DD/YY]
  * Status: <free text>
```

- Milestones with `Status: completed`, `done`, or `audit completed` are **excluded** from slides.
- Due dates are parsed from the last `[MM/DD/YY]` in any `[...]` bracket on the milestone line.
- Multiple dates in one bracket (e.g. `[01/15/26→02/06/26]`) use the **last** date.

### `# Previews/Reviews`

```markdown
### Review <period label>
* <Task name>: 2h → 1.5h
Total: 20
```

Used to calculate the average hours per period and identify tasks that are repeatedly pushed back.

## Project structure

```
progress-report/
├── doc/                        ← place your .md file here
├── .venv/                      ← Python virtual environment (stdlib only)
├── app.py                      ← slide generation logic
├── generate-slides.command     ← double-click launcher (macOS)
├── slides.html                 ← generated output (overwritten each run)
├── requirements.txt            ← no external packages
└── SETUP.md                    ← first-time setup instructions
```

## Recreating the virtual environment

If `.venv` is missing:

```bash
python3.10 -m venv .venv
```

No `pip install` needed — the app uses only the Python standard library.

## Troubleshooting

| Problem | Fix |
|---|---|
| Double-click does nothing | Right-click → Open → Open (one-time Gatekeeper bypass) |
| `python3.10: command not found` | Install Python 3.10 via [python.org](https://www.python.org/downloads/) or `brew install python@3.10` |
| `.venv` missing | Run `python3.10 -m venv .venv` in this folder |
| Slides look unstyled | Need internet on first load (Reveal.js CDN) |
| Milestone not appearing | Check it doesn't have `Status: completed/done/audit completed` |
| Wrong section parsed | Ensure headings are exactly `# Goals/Milestones` and `# Previews/Reviews` |
