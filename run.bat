@echo off
cd /d "%~dp0"
python -m pip install --quiet flask openpyxl reportlab
echo Otevri http://localhost:5000
python app.py %*
