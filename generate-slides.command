#!/bin/bash
# Double-click this file in Finder to regenerate the slides and open them.

DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$DIR/.venv/bin/python3.10"
SLIDES="$DIR/slides.html"

echo "Generating slides..."
"$PYTHON" "$DIR/app.py"

if [ $? -eq 0 ]; then
  echo "Opening slides in browser..."
  open "$SLIDES"
else
  echo "ERROR: slide generation failed."
  read -p "Press Enter to close..."
fi
