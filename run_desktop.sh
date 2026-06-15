#!/usr/bin/env bash
cd "$(dirname "$0")"
python3 -m pip install --quiet flask openpyxl reportlab 2>/dev/null
python3 desktop.py
