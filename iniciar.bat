@echo off
title VaccineTransport IoT — Iniciando servicos...
color 0A

echo ============================================
echo  VaccineTransport IoT — Startup
echo ============================================
echo.

:: ── 1. MySQL ──────────────────────────────────
echo [1/3] Iniciando MySQL...
taskkill /F /IM mysqld.exe >nul 2>&1
start "" /B "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe" --datadir="C:/Users/guilh/mysql-data" --port=3306
timeout /t 6 /nobreak >nul

:: Verifica se subiu
netstat -an | find ":3306" | find "LISTENING" >nul
if %errorlevel%==0 (
    echo [OK] MySQL rodando na porta 3306
) else (
    echo [ERRO] MySQL nao iniciou. Verifique o datadir.
    pause
    exit /b 1
)

:: ── 2. Mosquitto ──────────────────────────────
echo.
echo [2/3] Iniciando Mosquitto TLS...
taskkill /F /IM mosquitto.exe >nul 2>&1
timeout /t 1 /nobreak >nul
start "" /B "C:\Program Files\mosquitto\mosquitto.exe" -c "C:\Users\guilh\Desktop\vaccine-transport-iot\source\broker\mosquitto-tls.conf"
timeout /t 3 /nobreak >nul

netstat -an | find ":8883" | find "LISTENING" >nul
if %errorlevel%==0 (
    echo [OK] Mosquitto rodando na porta 8883 ^(TLS^)
) else (
    echo [ERRO] Mosquitto nao iniciou. Verifique mosquitto-tls.conf.
    pause
    exit /b 1
)

:: ── 3. Flask ──────────────────────────────────
echo.
echo [3/3] Iniciando Flask...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 1 /nobreak >nul
start "" /B /D "C:\Users\guilh\Desktop\vaccine-transport-iot\source\app" "C:\Users\guilh\Desktop\vaccine-transport-iot\source\venv\Scripts\python.exe" "C:\Users\guilh\Desktop\vaccine-transport-iot\source\app\app.py"
timeout /t 5 /nobreak >nul

netstat -an | find ":5000" | find "LISTENING" >nul
if %errorlevel%==0 (
    echo [OK] Flask rodando na porta 5000
) else (
    echo [ERRO] Flask nao iniciou. Verifique app.py.
    pause
    exit /b 1
)

:: ── Pronto ────────────────────────────────────
echo.
echo ============================================
echo  Todos os servicos estao rodando!
echo  Dashboard: https://10.0.0.175:5000
echo ============================================
echo.
echo Pressione qualquer tecla para fechar esta janela.
echo Os servicos continuarao rodando em background.
pause >nul
