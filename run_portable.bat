
@echo off
setlocal
if not exist .venv (
  py -3 -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
set FC_DB_PATH=%cd%\data\fluxo.db
set FC_UPLOAD_DIR=%cd%\data\uploads
if not exist data mkdir data
if not exist data\uploads mkdir data\uploads
python launcher.py
