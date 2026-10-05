@echo off
echo Starting CHASE servers...

:: Kill anything on ports 3000 and 8000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000 "') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 "') do taskkill /F /PID %%a 2>nul

timeout /t 1 /nobreak >nul

:: Start backend
start "CHASE Backend" cmd /k "cd /d C:\PROJECTS\CHASE\backend && C:\PROJECTS\CHASE\venv\Scripts\python.exe -m uvicorn main:app --port 8000"

:: Wait for backend to start
timeout /t 3 /nobreak >nul

:: Start frontend
start "CHASE Frontend" cmd /k "cd /d C:\PROJECTS\CHASE\frontend && npx vite --port 3000"

echo.
echo Servers starting in separate windows.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
pause
