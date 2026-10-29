@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "GITHUB_URL=https://github.com/Dannilool/analise-irrigacao"
echo.
echo  Sistema de Analise de Irrigacao - API FastAPI
echo  Dashboard:  http://127.0.0.1:8000
echo  Swagger:    http://127.0.0.1:8000/docs
echo.
echo  Pressione Ctrl+C para encerrar.
echo.
python -m uvicorn app:app --host 127.0.0.1 --port 8000
pause
