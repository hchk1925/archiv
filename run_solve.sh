#!/usr/bin/env bash
cd "$(dirname "$0")"
python3 -m pip install --quiet openpyxl 2>/dev/null
python3 solve_flags_gui.py
