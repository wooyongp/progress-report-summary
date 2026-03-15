# Progress Report Slide Generator

Turns your Markdown progress report into a browser-based slide deck showing upcoming milestones by urgency and a recommended work plan.

---

## Before you start (one-time setup)

You need **Python 3.10** installed on your Mac. You only do this once.

**Check if it's already installed** — open Terminal and run:
```
python3.10 --version
```
- If you see `Python 3.10.x` → you're ready, skip to [Using the app](#using-the-app).
- If you see an error → install Python 3.10:
  - **Option A:** Download from [python.org](https://www.python.org/downloads/)
  - **Option B:** If you have Homebrew: `brew install python@3.10`

Everything else (the virtual environment, packages) is set up **automatically** the first time you double-click the launcher.

---

## Using the app

1. Put your progress report `.md` file inside the `doc/` folder.
2. **Double-click `generate-slides.command`** in Finder.
   - The first time, it will set up the environment automatically — this takes a few seconds.
   - A Terminal window will open, generate the slides, then close.
3. `slides.html` opens in your browser automatically.
4. Navigate slides with the **arrow keys** or on-screen arrows.

> **If macOS blocks the file on first run:** right-click `generate-slides.command` → Open → Open. You only need to do this once.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Double-click does nothing | Right-click → Open → Open (one-time Gatekeeper bypass) |
| `python3.10: command not found` | Install Python 3.10 — see [Before you start](#before-you-start-one-time-setup) |
| Slides open but look unstyled | You need an internet connection the first time (Reveal.js loads from CDN) |
| A milestone is missing | Check it doesn't have `Status: completed`, `done`, or `audit completed` |
| Wrong section parsed | Headings must be exactly `# Goals/Milestones` and `# Previews/Reviews` |

---

## Progress report format

Your `.md` file must contain two top-level sections:

### `# Goals/Milestones`

```markdown
**Goal: <goal title> [due date]**

* Milestone: <description> [MM/DD/YY]
  * Status: <free text>
```

- Milestones with `Status: completed`, `done`, or `audit completed` are excluded from slides.
- Due dates are parsed from the last `[MM/DD/YY]` bracket on the milestone line.
- Multiple dates in one bracket (e.g. `[01/15/26→02/06/26]`) use the **last** date.

### `# Previews/Reviews`

```markdown
### Review <period label>
* <Task name>: 2h → 1.5h
Total: 20
```

Used to calculate the average hours per period and identify tasks that are repeatedly pushed back.

---

## What each file is for

```
progress-report/
├── doc/                        ← place your .md file here
├── .venv/                      ← Python virtual environment (auto-created on first run)
├── app.py                      ← slide generation logic
├── generate-slides.command     ← double-click this to run
├── slides.html                 ← generated output (overwritten each run)
├── requirements.txt            ← package list (currently no external packages needed)
└── SETUP.md                    ← detailed setup guide
```

---

## Requirements

- macOS (the double-click launcher is macOS-only; `app.py` runs anywhere with Python)
- Python 3.10
- Internet connection the first time slides are opened (Reveal.js CDN; cached after that)
