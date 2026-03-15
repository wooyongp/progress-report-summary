#!/bin/bash
# Double-click this file in Finder to regenerate the slides and open them.

DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$DIR/.venv"
PYTHON="$VENV/bin/python3.10"
PIP="$VENV/bin/pip"
SLIDES="$DIR/slides.html"

# --- First-time setup: create .venv if missing ---
if [ ! -d "$VENV" ]; then
  echo "First-time setup: creating virtual environment..."
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
"$PIP" install -q -r "$DIR/requirements.txt"
if [ $? -ne 0 ]; then
  echo ""
  echo "ERROR: Failed to install required packages."
  read -p "Press Enter to close..."
  exit 1
fi

# --- Generate slides ---
echo "Generating slides..."
"$PYTHON" "$DIR/app.py"

if [ $? -eq 0 ]; then
  echo "Opening slides in browser..."
  open "$SLIDES"
else
  echo ""
  echo "ERROR: Slide generation failed."
  read -p "Press Enter to close..."
fi
