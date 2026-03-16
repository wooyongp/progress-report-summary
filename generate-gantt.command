#!/bin/bash
# Double-click this file in Finder to regenerate the Gantt chart and open it.

DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$DIR/.venv"
PYTHON="$VENV/bin/python3.10"
PIP="$VENV/bin/pip"
OUTPUT="$DIR/gantt.html"

# --- Create or recreate .venv if missing or stale (e.g. after moving the folder) ---
if [ ! -d "$VENV" ] || ! "$PYTHON" -c "" 2>/dev/null || ! "$PYTHON" -m pip --version 2>/dev/null >/dev/null; then
  echo "Setting up virtual environment (this only happens once)..."
  rm -rf "$VENV"
  python3.10 -m venv "$VENV"
  if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Could not create virtual environment."
    echo "Make sure Python 3.10 is installed:"
    echo "  Option A: Download from https://www.python.org/downloads/"
    echo "  Option B: Run in Terminal:  brew install python@3.10"
    read -p "Press Enter to close..."
    exit 1
  fi
  echo "Virtual environment created."
fi

# --- Install / update packages from requirements.txt ---
echo "Checking dependencies..."
"$PYTHON" -m pip install -q -r "$DIR/requirements.txt"
if [ $? -ne 0 ]; then
  echo ""
  echo "ERROR: Failed to install required packages."
  read -p "Press Enter to close..."
  exit 1
fi

# --- Generate Gantt chart ---
echo "Generating Gantt chart..."
"$PYTHON" "$DIR/gantt.py"

if [ $? -eq 0 ]; then
  echo "Opening Gantt chart in browser..."
  open "$OUTPUT"
else
  echo ""
  echo "ERROR: Gantt chart generation failed."
  read -p "Press Enter to close..."
fi
