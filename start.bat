@echo off
REM AuksionWatch — bir buyruqda hammasi
echo ============================
echo   AuksionWatch
echo ============================
echo.

REM Backend
start "AuksionWatch Backend" cmd /k "cd /d %~dp0 && uvicorn backend.main:app --reload --port 8000"

REM Frontend
start "AuksionWatch Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

REM Telegram bot (faqat bot/.env mavjud bo'lsa)
if exist "%~dp0bot\.env" (
    start "AuksionWatch Bot" cmd /k "cd /d %~dp0bot && python main.py"
    echo Bot: ishga tushdi (bot\.env topildi)
) else (
    echo Bot: o'tkazib yuborildi (bot\.env yo'q — .env.example dan nusxalang)
)

timeout /t 4 >nul
start http://localhost:3000

echo.
echo Backend:  http://localhost:8000/docs
echo Frontend: http://localhost:3000
echo Bot:      Telegram (agar token kiritilgan bo'lsa)
