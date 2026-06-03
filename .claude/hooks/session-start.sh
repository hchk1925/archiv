#!/bin/bash
# SessionStart hook — hokejový almanach: instalace závislostí + rychlý smoke test.
# Ne-fatální (neblokuje sezení při chybě). Jen pro web/remote prostředí.
set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

# 1) Python závislosti používané skripty (openpyxl/flask/pandas/pdfminer + cffi)
pip install --quiet --disable-pip-version-check -r requirements.txt 2>/dev/null \
  || pip install --quiet --disable-pip-version-check openpyxl flask pandas pdfminer.six cffi 2>/dev/null \
  || true

# 2) Smoke test integrity: postav DB a vypiš stručný health (ne-fatální)
if python3 build_db.py >/dev/null 2>&1; then
  python3 health.py 2>/dev/null | grep -E "Sezóny|rozbit" | sed 's/^/[almanach] /' || true
else
  echo "[almanach] smoke test přeskočen (build_db neproběhl)"
fi
exit 0
