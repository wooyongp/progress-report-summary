# Progress Report Slide Generator — Setup Guide

This app reads your progress report and generates a browser-based slide deck
with upcoming milestones and a recommended work plan.

---

## What you need before using this app

### 1. macOS
The double-click launcher (`generate-slides.command`) is macOS-only.

### 2. Python 3.10
Check if it's installed by opening Terminal and running:
```
python3.10 --version
```
If you see `Python 3.10.x`, you're set.
If not, install it via [python.org](https://www.python.org/downloads/) or Homebrew:
```
brew install python@3.10
```

### 3. The `.venv` virtual environment
A `.venv` folder must exist inside this project folder.
It is already created if you cloned this repo as-is.

If it's missing (e.g. after re-downloading), recreate it by opening Terminal,
navigating to this folder, and running:
```
cd /path/to/progress-report
python3.10 -m venv .venv
```
No packages need to be installed — the app uses Python's standard library only.

### 4. An internet connection (first time only)
The slides use [Reveal.js](https://revealjs.com/) loaded from a CDN.
The first time you open `slides.html` you need internet access so your browser
can download the Reveal.js files. After that, your browser caches them and
slides work offline.

---

## How to use

1. Place your progress report `.md` file inside the `doc/` folder.
   Any filename works — the app picks up whichever `.md` file is there.
2. Double-click **`generate-slides.command`** in Finder.
   - A Terminal window will open briefly, generate the slides, then close.
3. Your browser opens `slides.html` automatically.
4. Navigate slides with **arrow keys** or the on-screen arrows.

> **Tip:** If macOS blocks the `.command` file the first time, right-click it →
> "Open" → "Open" to allow it. You only need to do this once.

---

## File overview

```
progress-report/
├── doc/
│   └── Wooyong Park Progress Report .md   ← your source file (edit this)
├── .venv/                                 ← Python virtual environment
├── app.py                                 ← slide generation logic
├── generate-slides.command                ← double-click to run
├── slides.html                            ← generated output (auto-overwritten)
├── requirements.txt                       ← no external packages needed
└── SETUP.md                               ← this file
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Double-click does nothing | Right-click → Open → Open (one-time Gatekeeper bypass) |
| "python3.10: command not found" | Install Python 3.10 (see step 2 above) |
| `.venv` missing | Run `python3.10 -m venv .venv` in this folder |
| Slides open but look unstyled | You need internet for the first load (Reveal.js CDN) |
| Wrong milestones shown | Check that completed milestones in the .md have `Status: completed` |
