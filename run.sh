#!/usr/bin/env bash
# Spuštění Almanach nástroje. Při prvním běhu doinstaluje balíčky.
cd "$(dirname "$0")"
python3 -m pip install --quiet flask openpyxl reportlab 2>/dev/null
echo "→ http://localhost:5000"
python3 app.py "$@"
